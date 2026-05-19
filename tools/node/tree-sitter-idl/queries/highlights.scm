; Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
; SPDX-License-Identifier: BSD-3-Clause-Clear

; Tree-sitter highlights for IDL (ISA Description Language).
; Replaces doc/src/prism/idl.js and tools/vscode/idl/syntaxes/idl.tmLanguage.json.

"if" "else" "for" "return" "returns" "arguments" "body" "description"
"function" "enum" "bitfield" "struct"
"builtin" "generated" "external" "fetch" "include" "const" @keyword

"CSR" @keyword.special

(comment) @comment

(int_literal) @constant.numeric
(string_literal) @string
(true_literal) (false_literal) @constant.builtin

(type_name) @type
(type_identifier) @type

(enum_ref enum_type: (type_identifier) @type)
(enum_ref member: (type_identifier) @type.member)

(function_name) @function
(function_call name: (function_name) @function)
(csr_function_call method: (function_name) @function)

(csr_register_access name: (csr_name) @variable.member)
(csr_field_access field: (csr_field_name) @variable.member)

(identifier) @variable

; Widening operators are anonymous nodes matched by string content.
(binary_expression "`+" @operator.special)
(binary_expression "`-" @operator.special)
(binary_expression "`*" @operator.special)
(binary_expression "`<<" @operator.special)

"::" "->" @operator

; Ternary '?' is a standalone anonymous token inside ternary_expression.
; It is NOT the same as the '?' suffix inside function_name tokens.
(ternary_expression "?" @operator)
