---
sidebar_position: 15
status: in-progress
---

# The IDL Compiler

:::warning[Status: In Progress]
This documentation is partially complete. Some sections may be missing or outdated.
:::

The IDL compiler (`idlc`) is the Ruby-based compiler that parses IDL source code, builds an abstract syntax tree (AST), performs type checking, and runs analysis passes to extract semantic information. This page describes how the compiler works internally — its architecture, compilation pipeline, and extension points for building custom analysis tools.

:::info
This page is about **compiler internals**. For IDL language syntax, see the [Language Reference](./overview.mdx). For CLI usage and gem installation, see the Tools section.
:::

## Overview

The `idlc` compiler transforms IDL source code into a typed, analyzable AST. It is used throughout the UDB toolchain:

- **During data resolution**: to compile instruction `operation()` bodies and CSR `sw_read()`/`sw_write()` functions
- **By generators**: to analyze instruction semantics (register dependencies, reachable functions, exception conditions)
- **For validation**: to type-check IDL code and report errors with precise file/line information

You typically interact with `idlc` **indirectly** through UDB tools like `udb` and `udb-gen`, but you can also use it **programmatically** via its Ruby API to build custom analysis tools.

## Compilation Pipeline

The compiler processes IDL code in several phases:

### 1. Parse

The parser is generated from a [Treetop](https://github.com/nathansobo/treetop) PEG grammar (`idl.treetop`). It reads IDL source and produces a concrete syntax tree, reporting syntax errors with line/column precision if parsing fails.

The grammar is automatically recompiled if `idl.treetop` is newer than the generated parser.

### 2. AST Construction

The concrete syntax tree is transformed into a semantic AST by calling `to_ast` on the root node. Each syntax node type knows how to construct its corresponding AST node. The result is a tree of `AstNode` subclasses that preserve source location information and support semantic queries.

### 3. Type Check

The AST is walked recursively, calling `type_check(symtab)` on each node. The compiler:

- Infers types bottom-up from expressions
- Validates type compatibility (e.g., ensuring operands to `+` can be widened to a common type)
- Checks function call signatures
- Detects undefined variables and type mismatches

Type checking is symbol-table-aware: it uses the current scope to resolve names and track variable types.

**Configuration sensitivity**: Type checking with `strict: false` (the default) skips unreachable code. This means the same IDL source can type-check differently depending on the configuration. For example:

```idl
if (implemented?(ExtensionName::C)) {
  // This code is not type-checked if compressed instructions are known to be disabled at compile time
  Bits<16> instr = ...;
}
```

This allows IDL code to be conditionally valid based on configuration parameters, and avoids type checking issues where IDL code is only valid under certain conditions (e.g., accessing page table bits that are only defined in RV64).

### 4. Analysis Passes (Optional)

After type checking, you can run analysis passes to extract information or transform the AST:

- **Reachable functions**: trace the call graph from an instruction/CSR to find all functions it uses
- **Prune**: constant-fold expressions and eliminate dead branches when configuration values are known
- **Find referenced CSRs**: list all CSRs accessed by an operation
- **Find source registers**: extract register operands (for dependency analysis)

Passes are implemented as methods added to `AstNode` subclasses (see [Analysis Passes](#analysis-passes) below).

## The Abstract Syntax Tree (AST)

Every node in the AST is a subclass of `Idl::AstNode`. The base class provides:

### Core Attributes

- **`text_value`**: The original IDL source text for this node
- **`input_file`**: Path to the source file (as a `Pathname`)
- **`lineno`**: Starting line number in the source file
- **`interval`**: Character range within the input
- **`parent`**: Parent node (or `nil` for the root)
- **`children`**: Array of child `AstNode` instances

### Semantic Methods

- **`type(symtab)`**: Returns the `Type` of this expression (e.g., `Bits<32>`, `Boolean`)
- **`value(symtab)`**: Attempts to evaluate the expression at compile time, returning a Ruby value (Integer, Boolean, String, Array, or Hash). Raises a `ValueError` if the value depends on runtime state.

### Error Types

The AST defines two error classes:

- **`AstNode::TypeError`**: Raised when type checking detects a type error (e.g., incompatible operand types)
- **`AstNode::InternalError`**: Raised when the compiler encounters an unexpected state (indicates a compiler bug)

Both capture a backtrace starting from the error call site for debugging.

### Tree Traversal Pattern

Most compiler operations walk the tree recursively:

```ruby
class AstNode
  def some_analysis(symtab)
    # Default: recursively visit children
    children.each { |child| child.some_analysis(symtab) }
  end
end

class IfAst < AstNode
  def some_analysis(symtab)
    # Override for specific node types
    if_cond.some_analysis(symtab)
    if_body.some_analysis(symtab)
    elseifs.each { |eif| eif.some_analysis(symtab) }
    final_else_body.some_analysis(symtab)
  end
end
```

This pattern makes it easy to add new analyses without modifying the core AST structure.

## The Symbol Table

The `SymbolTable` tracks all visible names at the current point in the program. It manages:

### Scoping

IDL has four scope levels (see [Scope](./scope.mdx) for details):

1. **Global scope**: functions, enumerations, bitfields defined in `.idl` files
2. **Function scope**: arguments and local variables inside a function
3. **Instruction scope**: decode variables inside an instruction's `operation()` body
4. **CSR scope**: CSR fields inside a CSR's `sw_read()`/`sw_write()` functions

The symbol table is a stack: `symtab.push(node)` opens a new scope, `symtab.pop` closes it.

### Compile-Time vs. Runtime Values

A symbol table entry (`Var`) stores:

- **Name**: the variable identifier
- **Type**: its IDL type (e.g., `Bits<5>`, `Boolean`)
- **Value**: its compile-time value (if known) or `nil` (if unknown)

The compiler tracks values **optimistically**: whenever it can evaluate an expression at compile time, it does. This enables constant folding, dead code elimination, and conditional compilation.

## Compile-Time Value Tracking and Unknown Values

The compiler distinguishes between **known** and **unknown** information at compile time. There are **two categories of "unknown"**:

### 1. Unknown Values

A variable has an **unknown value** when its value depends on runtime state. For example:

```idl
Bits<5> rs1 = X[rs1_idx];  // rs1_idx comes from the instruction encoding
if (rs1 == 5'd0) {
  // Compiler doesn't know if this branch will execute
}
```

The compiler tracks which variables have known values and propagates them through expressions. When a value depends on an unknown, the result is also unknown.

### 2. Unknown Bit Widths

A `Bits<N>` type has an **unknown width** when `N` depends on a runtime parameter:

```idl
Bits<XLEN> result;  // XLEN is a configuration parameter (32 or 64)
```

If the configuration is not fully specified (e.g., building an "unconfig" that supports both RV32 and RV64), the compiler must treat the width as **`:unknown`**. This affects certain optimizations like constant folding (since the bit width determines wraparound behavior), but **does not prevent type checking** — operations between `Bits` of different widths are allowed, with automatic widening (see [Operators](./operators.mdx)).

### The `value_try` / `value_else` Pattern

The compiler uses a value-error mechanism (similar to exceptions, but lighter-weight) to handle unknowns gracefully:

```ruby
result = value_try do
  v = some_expression.value(symtab)
  # Use v here
end
value_else(result) do
  # Expression has unknown value; handle the fallback
end
```

This pattern allows the compiler to attempt optimistic evaluation and fall back cleanly when information is missing.

### Value Snapshotting

**Problem**: When the compiler analyzes control flow (if/else, loops), it needs to track how variable values change along different execution paths. But the compiler doesn't know which path will execute at runtime.

**Solution**: The symbol table supports **snapshotting**: capturing the current state of all variable values, and later restoring that snapshot.

#### Why Snapshotting is Needed

Consider this code:

```idl
Bits<32> x = 10;
if (some_condition) {
  x = 20;
}
// What is the value of x here?
```

If `some_condition` is unknown at compile time, the compiler cannot assume `x` is either `10` or `20` after the `if` — it must mark `x` as **unknown** because the assignment may or may not have happened.

#### Snapshot API

```ruby
snapshot = symtab.snapshot_values       # Capture current state
# ... modify variable values ...
symtab.restore_values(snapshot)         # Restore to captured state
```

This is used in:

- **If statements**: Each branch gets a snapshot; after analyzing all branches, values assigned in uncertain branches are nullified
- **Loops**: The loop body may execute 0 or N times, so any assignments inside the loop invalidate outer-scope variables (they're set to `nil`)
- **Conditional statements**: `if (cond) x = y;` — if `cond` is unknown, `x` becomes unknown after the statement

#### Nullification

When control flow is uncertain, the compiler **nullifies** variables by setting their `value` to `nil`. This prevents incorrect constant propagation.

Example from the prune pass:

```ruby
class ForLoopAst < AstNode
  def prune(symtab, forced_type: nil)
    # Nullify any outer-scope variable assigned in the loop body
    stmts.each { |stmt| stmt.nullify_assignments(symtab) }

    # Snapshot AFTER nullification, so restore brings back nil values
    snapshot = symtab.snapshot_values
    # ... analyze loop body ...
    symtab.restore_values(snapshot)
  end
end
```

### Example: If Statement Value Propagation

Here's how the compiler handles an `if` statement:

```ruby
class IfAst < AstNode
  def prune(symtab, forced_type: nil)
    value_result = value_try do
      if if_cond.value(symtab)
        # Condition is true at compile time; only the if-body is reachable
        return if_body.prune(symtab, restore: false)
      elsif !elseifs.empty?
        # Condition is false; check else-if branches
        # ...
      elsif !final_else_body.stmts.empty?
        # Condition is false; only else-body is reachable
        return final_else_body.prune(symtab, restore: false)
      else
        # Condition is false and no else; this is a no-op
        return NoopAst.new
      end
    end
    value_else(value_result) do
      # Condition is unknown; all branches are potentially reachable
      # Nullify any variable assigned in any branch
      if_body.nullify_assignments(symtab)
      unknown_elsifs.each { |eif| eif.body.nullify_assignments(symtab) }
      final_else_body.nullify_assignments(symtab)
      # Return pruned if statement with all branches intact
      # ...
    end
  end
end
```

## Analysis Passes

Analysis passes extract information from or transform the AST. They are implemented by defining methods on `AstNode` subclasses.

### Built-in Passes

The compiler includes several standard passes:

#### Reachable Functions

**File**: `idlc/passes/reachable_functions.rb`

Traces the function call graph starting from a given AST node (e.g., an instruction's `operation()` body) and returns the list of all functions that may be called, directly or transitively.

**Usage**: Generators use this to determine which global functions must be included when compiling an instruction for an ISS or formal model.

**Implementation pattern**: Recursively visits function calls, applies arguments to build a context-specific symbol table, and analyzes each function body in that context. Uses caching to handle recursion cycles.

#### Reachable Exceptions

**File**: `idlc/passes/reachable_exceptions.rb`

Determines which exceptions can be raised by a given piece of IDL code. Returns a set of `ExceptionCode` values.

**Usage**: Generators use this to know which exception handling code is required for an instruction.

#### Find Referenced CSRs

**File**: `idlc/passes/find_referenced_csrs.rb`

Returns a list of CSR names accessed (read or written) by the code.

**Usage**: Dependency analysis for instruction scheduling or ISS optimization.

#### Find Source Registers

**File**: `idlc/passes/find_src_registers.rb`

Extracts the register operands read by an instruction (e.g., `X[rs1]`, `X[rs2]`).

**Usage**: Dependency analysis for out-of-order execution models.

#### Prune

**File**: `idlc/passes/prune.rb`

Performs **constant folding** and **dead code elimination** when configuration parameters are known. Returns a simplified AST with:

- Known expressions replaced by their literal values
- Dead branches removed (e.g., `if (false) { ... }` → deleted)
- Unreachable code after early returns eliminated

**Requires**: Known values (not just known widths). If a variable has an unknown value, pruning preserves the expression.

**Usage**: Generating configuration-specific ISS code where parameters like `XLEN` or extension support are fixed.

**Example**:

```idl
// Original
if (MISA.C) {
  // Compressed instructions supported
} else {
  raise(IllegalInstruction);
}

// After pruning with MISA.C = 1
// (only the if-body remains)
```

### Writing a Custom Pass

To add a new pass:

1. Define a method on `AstNode` with a default implementation that recursively visits children
2. Override the method on specific node types to extract or transform information
3. Call your pass on the root of the tree

#### Example: Counting Assignments

Let's write a pass that counts how many assignments appear in an AST:

```ruby
module Idl
  class AstNode
    # Default: sum counts from children
    def count_assignments
      children.sum(0) { |child| child.count_assignments }
    end
  end

  class VariableAssignmentAst < AstNode
    def count_assignments
      1 + super  # Count this assignment, plus any in the RHS
    end
  end

  class AryElementAssignmentAst < AstNode
    def count_assignments
      1 + super
    end
  end

  class FieldAssignmentAst < AstNode
    def count_assignments
      1 + super
    end
  end
end

# Usage:
ast = compiler.compile_func_body(idl_source, symtab: symtab)
num_assignments = ast.count_assignments
puts "Found #{num_assignments} assignments"
```

#### Tips for Writing Passes

- **Use the symbol table**: Most passes need type or value information — pass `symtab` as an argument
- **Handle scoping correctly**: If your pass needs to evaluate expressions, push/pop scopes as you traverse function bodies and loops
- **Use `value_try`**: If your pass depends on compile-time values, wrap calls to `value(symtab)` in `value_try` and provide a fallback
- **Consider caching**: If your pass is expensive and may visit the same subtree multiple times (e.g., function bodies), use a cache keyed by node identity or argument values

## Type Checking

Type checking is the process of verifying that every expression has a well-defined type and that operations are type-compatible.

### How Types are Inferred

Types flow **bottom-up** through the AST:

- Literals have intrinsic types: `32'd10` is `Bits<32>`, `true` is `Boolean`
- Variables have the type they were declared with
- Function calls have the return type declared in the function signature
- Binary operators infer their result type from their operands (see [Operators](./operators.mdx) for widening rules)

### Widening Rules for Bit-Vectors

When two `Bits<N>` values of different widths are combined, the result is widened to the larger width:

```idl
Bits<5> a = 5'd10;
Bits<32> b = 32'd100;
Bits<32> result = a + b;  // a is zero-extended to 32 bits
```

Widening is **zero-extension** by default. Use the `$signed()` cast for sign-extension (see [Type Conversions](./type-conversions.mdx)).

### Error Reporting with File/Line Information

Type errors include precise source locations:

```
TypeError: Type mismatch: expected Bits<32>, got Boolean
  at my_instruction.yaml:42
  in operation() body
```

The AST preserves `input_file` and `lineno` for every node, allowing errors to point directly to the problematic source line.

## Using the Compiler Programmatically (Ruby API)

The `Idl::Compiler` class provides a Ruby API for parsing and compiling IDL code.

### Creating a Compiler Instance

```ruby
require 'idlc'

compiler = Idl::Compiler.new
```

### Key Methods

#### `compile_file(path, source_mapper = nil)`

Compiles an entire `.idl` file.

**Arguments**:
- `path` (Pathname): Path to the file
- `source_mapper` (Hash, optional): If provided, stores the file contents keyed by path (useful for error reporting)

**Returns**: The root `AstNode` of the file

**Raises**: `SyntaxError` if parsing fails

**Example**:

```ruby
ast = compiler.compile_file(Pathname.new("spec/std/isa/inst.idl"))
```

#### `compile_func_body(body, return_type:, symtab:, name:, input_file:, input_line:)`

Compiles a function body (a sequence of statements).

**Arguments**:
- `body` (String): IDL source code for the function body
- `return_type` (Type, optional): Expected return type
- `symtab` (SymbolTable): Symbol table with global definitions
- `name` (String): Function name (for error messages)
- `input_file` (String/Pathname): Source file path
- `input_line` (Integer): Starting line number in the source file

**Returns**: A `FunctionBodyAst` node

**Example**:

```ruby
ast = compiler.compile_func_body(
  inst["operation()"],
  symtab: global_symtab,
  name: "#{inst.name}::operation()",
  input_file: inst_file_path,
  input_line: line_number
)
```

#### `compile_inst_scope(idl, symtab:, input_file:, input_line:)`

Compiles an instruction `operation()` body. Unlike `compile_func_body`, this method automatically extracts the decode variable declarations from the IDL source and adds them to the symbol table before compiling the operation statements — so decode fields (e.g., `xs1`, `xs2`, `imm`) are already in scope when the body is analyzed.

**Arguments**:
- `idl` (String): IDL source code
- `symtab` (SymbolTable): Symbol table with global definitions
- `input_file` (String/Pathname): Source file path
- `input_line` (Integer): Starting line number

**Returns**: An instruction-scope AST node

#### `compile_expression(expression, symtab)`

Compiles a single expression (e.g., for evaluating a parameter default value).

**Arguments**:
- `expression` (String): IDL expression
- `symtab` (SymbolTable): Symbol table for name resolution

**Returns**: An expression AST node

**Example**:

```ruby
expr_ast = compiler.compile_expression("XLEN / 8", global_symtab)
num_bytes = expr_ast.value(global_symtab)
```

#### `type_check(ast, symtab, what)`

Type-checks an already-constructed AST.

**Arguments**:
- `ast` (AstNode): The root of the tree to check
- `symtab` (SymbolTable): Symbol table for name resolution
- `what` (String): Description of what is being checked (for error messages)

**Raises**: `AstNode::TypeError` if type checking fails

**Example**:

```ruby
compiler.type_check(ast, symtab, "instruction ADD operation()")
```

### Complete Example: Compiling an Instruction

:::note Symbol table in practice
In most use cases you won't construct `global_symtab` by hand. The UDB framework builds and populates it from the database YAML files (instruction definitions, CSR fields, type declarations, global functions) before handing it to your code. The example below shows the compiler API in isolation; in a real generator the symbol table arrives pre-populated.
:::

```ruby
require 'idlc'
require 'pathname'

# Assume we have:
# - global_symtab: a SymbolTable with global function and type definitions
# - inst_data: a hash with instruction metadata, including inst_data["operation()"]

compiler = Idl::Compiler.new

ast = compiler.compile_inst_scope(
  inst_data["operation()"],
  symtab: global_symtab,
  input_file: "spec/std/isa/inst/RV32I/add.yaml",
  input_line: 15
)

# Type-check the AST
compiler.type_check(ast, global_symtab, "ADD operation()")

# Run a pass to find reachable functions
functions = ast.reachable_functions(global_symtab)
puts "ADD calls: #{functions.map(&:name).join(', ')}"

# Run the prune pass (assumes configuration parameters are set in global_symtab)
pruned_ast = ast.prune(global_symtab)
puts "Pruned AST:\n#{pruned_ast.text_value}"
```

## Error Handling

The compiler reports three categories of errors:

### `SyntaxError`

Raised during parsing when the input does not match the IDL grammar.

**Includes**:
- File path
- Line and column number
- Reason (e.g., "Expected 'end', found '}'")

**Example**:

```
SyntaxError: While parsing spec/std/isa/inst/RV32I/add.yaml:18:5

Expected ';' after statement
```

### `AstNode::TypeError`

Raised during type checking when an operation is applied to incompatible types.

**Includes**:
- Error message describing the type mismatch
- Compiler backtrace showing where the error was detected

**Example**:

```ruby
begin
  compiler.type_check(ast, symtab, "SUB operation()")
rescue Idl::AstNode::TypeError => e
  puts e.what  # "Cannot apply operator '+' to Boolean and Bits<32>"
  puts e.bt    # Backtrace from the type_error call site
end
```

### `AstNode::InternalError`

Raised when the compiler encounters an unexpected state, indicating a compiler bug (not a user error).

**Includes**:
- Error message
- Compiler backtrace

**If you encounter an `InternalError`**: Please report it as a bug with a minimal reproducible example.

---

## Further Reading

- [IDL Overview](./overview.mdx) — Design goals and language basics
- [IDL Data Types](./data-types.mdx) — Type system reference
- [IDL Functions](./functions.mdx) — Function declarations and rules
- [Scope](./scope.mdx) — Scoping rules for global, function, instruction, and CSR contexts
- [Operators](./operators.mdx) — Operator precedence and widening rules
- [Type Conversions](./type-conversions.mdx) — Implicit widening and explicit casts
