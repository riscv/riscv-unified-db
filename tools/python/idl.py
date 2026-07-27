# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""IDL (Instruction Description Language) interpreter for RISC-V assembly semantics.

This module compiles and evaluates IDL function bodies that describe the encode/decode
semantics of RISC-V instructions.
"""

import contextlib
import functools
import re
import subprocess
import tempfile
from pathlib import Path

from ruamel.yaml import YAML


class IdlExecutionError(Exception):
    pass


class _IdlReturn(Exception):
    def __init__(self, value):
        self.value = value


_REPO_ROOT = Path(__file__).resolve().parents[2]
_IDLC = _REPO_ROOT / "bin" / "idlc"


@functools.cache
def _compile_idl_function_body(idl):
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".idl", delete_on_close=False
    ) as idl_file:
        idl_file.write(idl)
        idl_path = idl_file.name
        idl_file.close()

        result = subprocess.run(
            [
                str(_IDLC),
                "compile",
                "--format",
                "yaml",
                "--root",
                "function_body",
                idl_path,
            ],
            cwd=_REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise IdlExecutionError(f"IDL compile failed: {details}")

    yaml = YAML(typ="safe")
    return yaml.load(result.stdout)


def _trunc_div(lhs, rhs):
    if rhs == 0:
        raise IdlExecutionError("division by zero")
    sign = -1 if (lhs < 0) ^ (rhs < 0) else 1
    return sign * (abs(lhs) // abs(rhs))


def _operand_key(node, env):
    if isinstance(node, dict) and node.get("kind") == "id":
        return node["name"]
    return _eval_idl_expr(node, env)


def _operand_offset_value(operand_name, env):
    for operand_def in env.get("operand_defs") or []:
        if operand_def.get("name") != operand_name:
            continue
        offset_def = operand_def.get("offset")
        if isinstance(offset_def, dict):
            offset_name = offset_def.get("name")
            if offset_name in env["operands"]:
                return env["operands"][offset_name]

    raise IdlExecutionError(f"no offset value found for operand '{operand_name}'")


def _format_idl_message(message, env):
    def replace_operand(match):
        key = match.group(1)
        return str(env["operands"].get(key, "??"))

    def replace_var(match):
        key = match.group(1)
        return str(env["vars"].get(key, "??"))

    message = re.sub(r"\$\{operands\[([A-Za-z_][A-Za-z0-9_]*)\]\}", replace_operand, message)
    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", replace_var, message)


def _eval_idl_funcall(node, env):
    func = node["func"]
    args = [_eval_idl_expr(arg, env) for arg in node.get("args", [])]

    if func == "reg2creg":
        if len(args) != 1:
            raise IdlExecutionError("reg2creg expects one argument")
        return args[0] - 8
    if func == "creg2reg":
        if len(args) != 1:
            raise IdlExecutionError("creg2reg expects one argument")
        return args[0] + 8
    if func == "xlen":
        if args:
            raise IdlExecutionError("xlen expects no arguments")
        return env["xlen"]
    if func == "raise":
        message = args[0] if args else "IDL raised"
        if isinstance(message, str):
            message = _format_idl_message(message, env)
        raise IdlExecutionError(str(message))

    raise IdlExecutionError(f"unsupported IDL function '{func}'")


def _eval_idl_binary(node, env):
    op = node["op"]

    if op == "||":
        return bool(_eval_idl_expr(node["lhs"], env)) or bool(_eval_idl_expr(node["rhs"], env))
    if op == "&&":
        return bool(_eval_idl_expr(node["lhs"], env)) and bool(_eval_idl_expr(node["rhs"], env))

    lhs = _eval_idl_expr(node["lhs"], env)
    rhs = _eval_idl_expr(node["rhs"], env)

    # operands could be strings or ints; IDL constants appear as strings;
    # coerce to common type if possible
    if isinstance(lhs, int):
        with contextlib.suppress(ValueError):
            rhs = int(rhs)
    elif isinstance(rhs, int):
        with contextlib.suppress(ValueError):
            lhs = int(lhs)

    if op == "==":
        return lhs == rhs
    if op == "!=":
        return lhs != rhs
    if op == "<":
        return lhs < rhs
    if op == "<=":
        return lhs <= rhs
    if op == ">":
        return lhs > rhs
    if op == ">=":
        return lhs >= rhs
    if op == "+":
        return lhs + rhs
    if op == "-":
        return lhs - rhs
    if op == "*":
        return lhs * rhs
    if op == "/":
        return _trunc_div(lhs, rhs)
    if op == "%":
        return lhs % rhs
    if op == "<<":
        return lhs << rhs
    if op == ">>":
        return lhs >> rhs
    if op == "&":
        return lhs & rhs
    if op == "|":
        return lhs | rhs
    if op == "^":
        return lhs ^ rhs

    raise IdlExecutionError(f"unsupported IDL binary operator '{op}'")


def _eval_idl_expr(node, env):
    if not isinstance(node, dict):
        return node

    kind = node.get("kind")

    if kind == "bits_literal":
        return int(node["value"])
    if kind == "string_literal":
        return node["text"]
    if kind == "id":
        name = node["name"]
        if name in env["vars"]:
            return env["vars"][name]
        raise IdlExecutionError(f"unknown IDL identifier '{name}'")
    if kind == "paren_expr":
        return _eval_idl_expr(node["expr"], env)
    if kind == "array_access":
        array = node["array"]
        if (
            isinstance(array, dict)
            and array.get("kind") == "id"
            and array.get("name") == "operands"
        ):
            return env["operands"].get(_operand_key(node["index"], env), "??")
        array_value = _eval_idl_expr(array, env)
        return array_value[_eval_idl_expr(node["index"], env)]
    if kind == "operand_offset_access":
        return _operand_offset_value(node["operand_name"], env)
    if kind == "funcall_expr":
        return _eval_idl_funcall(node, env)
    if kind == "binary_operator_expr":
        return _eval_idl_binary(node, env)
    if kind == "unary_operator_expr":
        op = node["op"]
        value = _eval_idl_expr(node["expr"], env)
        if op == "-":
            return -value
        if op == "+":
            return value
        if op == "!":
            return not bool(value)
        if op == "~":
            return ~value
        raise IdlExecutionError(f"unsupported IDL unary operator '{op}'")
    if kind == "ternary_operator_expr":
        branch = "true_expression" if _eval_idl_expr(node["condition"], env) else "false_expression"
        return _eval_idl_expr(node[branch], env)
    if kind == "var_decl_init":
        value = _eval_idl_expr(node["value"], env)
        env["vars"][node["name"]["name"]] = value
        return value
    if kind == "var_assignment":
        value = _eval_idl_expr(node["value"], env)
        var = node["var"]
        if var.get("kind") != "id":
            raise IdlExecutionError("unsupported assignment target")
        env["vars"][var["name"]] = value
        return value
    if kind == "return_expr":
        exprs = node.get("exprs", [])
        if len(exprs) == 0:
            raise _IdlReturn(None)
        if len(exprs) == 1:
            raise _IdlReturn(_eval_idl_expr(exprs[0], env))
        raise _IdlReturn(tuple(_eval_idl_expr(expr, env) for expr in exprs))

    raise IdlExecutionError(f"unsupported IDL expression kind '{kind}'")


def _exec_idl_body(node, env):
    if not isinstance(node, dict):
        raise IdlExecutionError("invalid IDL body")

    kind = node.get("kind")
    if kind not in ("function_body", "if_body"):
        raise IdlExecutionError(f"unsupported IDL body kind '{kind}'")

    for stmt in node.get("stmts", []):
        _exec_idl_stmt(stmt, env)


def _exec_idl_if(node, env):
    if _eval_idl_expr(node["condition"], env):
        _exec_idl_body(node["taken_body"], env)
        return

    for else_if in node.get("else_ifs", []) or []:
        if _eval_idl_expr(else_if["condition"], env):
            _exec_idl_body(else_if["body"], env)
            return

    else_body = node.get("else")
    if else_body:
        _exec_idl_body(else_body, env)


def _exec_idl_stmt(node, env):
    if not isinstance(node, dict):
        raise IdlExecutionError("invalid IDL statement")

    kind = node.get("kind")
    if kind == "stmt":
        _eval_idl_expr(node["expr"], env)
        return
    if kind == "if_stmt":
        _exec_idl_if(node, env)
        return

    raise IdlExecutionError(f"unsupported IDL statement kind '{kind}'")


def execute(idl, xlen, *, variables=None, operands=None, instruction_operands=None):
    """Compile and evaluate an IDL function body.

    Args:
        idl: IDL source string describing the function body.
        xlen: XLEN value (32 or 64) for the target architecture.
        variables: Optional mapping of variable names to initial values (used for
            decode expressions).
        operands: Optional mapping of operand names to values (used for encode
            expressions).
        instruction_operands: Optional list of operand definitions providing
            metadata such as offset relationships (used for encode expressions).

    Returns:
        The value returned by the IDL function body, or ``None`` if the body
        completes without an explicit ``return``.

    Raises:
        IdlExecutionError: If compilation or evaluation fails.
    """
    ast = _compile_idl_function_body(idl)
    env = {
        "operands": operands or {},
        "operand_defs": instruction_operands or [],
        "vars": dict(variables or {}),
        "xlen": xlen,
    }

    try:
        _exec_idl_body(ast, env)
    except _IdlReturn as ret:
        return ret.value

    return None
