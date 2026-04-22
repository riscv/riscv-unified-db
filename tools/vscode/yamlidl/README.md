<!--
Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
SPDX-License-Identifier: BSD-3-Clause-Clear
-->

# YAML with IDL Injection

This extension provides syntax highlighting for YAML files with intelligent language injection based on key names:
- **IDL syntax** for keys ending with parentheses
- **AsciiDoc syntax** for keys named "description"

## Features

### IDL Injection
- Automatically detects YAML keys ending with `()` or `(args)` patterns
- Applies IDL syntax highlighting to both the arguments and the associated string values
- Supports all YAML string value types:
  - Unquoted single-line scalars: `key(): X[rd] = X[rs1] + X[rs2];`
  - Quoted strings: `key(): "IDL code"`
  - Single-quoted strings: `key(): 'IDL code'`
  - Block scalars (literal): `key(): |`
  - Block scalars (folded): `key(): >`
- Works with nested YAML structures at any depth

### AsciiDoc Injection
- Automatically detects YAML keys named "description"
- Applies AsciiDoc syntax highlighting to the string values
- Supports all YAML string value types (quoted, single-quoted, block scalars)

## Example

```yaml
# Description key - AsciiDoc highlighting applied
description: "This is a *bold* description with `code` markup"

# Key ending with () - IDL highlighting applied
operation(): "X[rd] = X[rs1] + X[rs2]"

# Key with arguments - IDL highlighting applied to both args and value
execute(Bits<5> rd, Bits<5> rs1): |
  if (rd != 0) {
    X[rd] = X[rs1] + 1
  }

# Nested structure - IDL highlighting applied
instruction:
  description: |
    = Instruction Overview

    This uses *AsciiDoc* formatting with `inline code`.

  encoding(): "0000000 rs2 rs1 000 rd 0110011"
  behavior(): |
    X[rd] = X[rs1] & X[rs2]
```

## Requirements

This extension requires the IDL language extension to be installed for proper syntax highlighting of the injected IDL code.

## Release Notes

### 0.1.0

Initial release of YAML with IDL injection support.

## License

See LICENSE file for details.
