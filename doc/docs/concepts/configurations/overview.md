---
sidebar_position: 1
status: in-progress
---

# Configurations Overview

:::warning[Status: In Progress]
This documentation is partially complete. Some sections may be missing or outdated.
:::

A **configuration** is a YAML file that describes a RISC-V system or family of systems by specifying which extensions are implemented, what their parameter values are, and how implementation-defined behavior is resolved. Configurations control how UDB generates artifacts — from fully general tools to highly specialized ISS code — and also provide a **standard machine-readable format** for precisely describing RISC-V implementations (used, for example, in RISC-V certification applications).

Configurations are also where **spec overlays** are enabled, allowing vendor-specific customizations to be applied on top of the standard specification data (see [The Data Pipeline](../data-pipeline/overview.md)).

:::tip Schema Reference
For the complete technical schema definition including all fields and validation rules, see the [Configuration Schema Reference](/docs/schemas/v0.1/config_schema).
:::

## Why Configurations Exist

The RISC-V ISA is highly modular and leaves many details up to implementers:

- **Extension selection**: Does this system support floating-point? Vector? Compressed instructions?
- **MXLEN**: Is this a 32-bit or 64-bit M-mode machine (or does it support both)?
- **Parameters**: How wide is the physical address space? Are misaligned accesses supported? What exceptions are reported in `mtval`?
- **Optional features**: Is the `misa` CSR implemented? Can extensions be dynamically enabled/disabled?

UDB's specification data describes **all possible behaviors** across the entire RISC-V design space. A configuration lets you specify **how much you know** about the target system — from nothing (the full design space) to everything (a specific implementation) — and UDB generates artifacts appropriate to that level of specificity.

## The Three Types of Configurations

UDB supports three levels of specificity, each serving different use cases:

### 1. Fully Configured (`type: fully configured`)

**Specifies every parameter and extension** — represents a single concrete implementation.

Every implementation-defined choice is pinned to a value. This is what you use to model a real hardware design or generate an ISS for a specific chip.

**Example**: `cfgs/mc100-32-full-example.yaml` — a complete MC100-32 processor configuration with all extensions, parameters, and CSR behaviors fully specified.

**Use cases**:
- Generating a configuration-specific ISS for a shipping product
- Producing documentation for a specific chip
- Validating that a design conforms to a RISC-V profile
- Submitting a design for certification

**Key property**: All semantic ([IDL](../../idl/overview.mdx)) code can be fully evaluated and optimized; no unknowns remain. Generated artifacts are tailored to this exact configuration.

### 2. Partially Configured (`type: partially configured`)

**Specifies some parameters and extensions, leaving others unspecified** — represents a family of implementations that share common characteristics.

**Example**: `cfgs/rv32.yaml` — specifies `MXLEN: 32` and requires the `I` and `Sm` extensions, but leaves all other parameters and optional extensions unspecified. This describes "any RV32 system."

**Use cases**:
- Generating documentation or test suites that apply to a range of implementations
- Building tools for a product line or processor family
- Exploring "what if" scenarios (e.g., "what instructions are available if we add the `V` extension?")
- Defining a baseline for vendor-specific customization

**Key property**: Some IDL expressions can be evaluated (those depending only on known parameters), but code paths that depend on unknown parameters remain conditional. Generated artifacts must handle the full range of possibilities for unspecified parameters.

### 3. Unconfigured (`type: unconfigured`)

**Specifies nothing** — represents the entire RISC-V design space with no constraints.

The special configuration **`_`** (underscore) is the canonical unconfigured architecture.

**Example**: `cfgs/_.yaml` — describes "any RVI-standard architecture" with no parameters set, not even `MXLEN`.

**Use cases**:
- Generating the full RISC-V specification manual (covering all possible behaviors)
- Building general-purpose tooling that works across all RISC-V systems (assemblers, disassemblers, debuggers)
- Studying the full scope of the ISA without implementation assumptions
- Generating schemas and abstract models

**Key property**: No configuration-dependent IDL expressions can be evaluated at compile time; all parameter-dependent behavior must be preserved in generated artifacts. Generated code must be maximally generic.

## Configuration File Structure

All configuration files share a common YAML structure:

```yaml
$schema: config_schema.json#
kind: architecture configuration
type: fully configured | partially configured | unconfigured
name: MyConfig
description: A brief description of this configuration

# Full configs only: exact extensions and versions
implemented_extensions:  # Omit for partial/unconfigured
  - [ExtName, "version"]

# Partial configs only: minimum extension requirements
mandatory_extensions:  # Omit for full/unconfigured
  - name: "ExtName"
    version: ">= min_version"

# Full and partial configs only: parameter values
params:  # Omit for unconfigured
  PARAM_NAME: value

# Optional: spec overlay directory
arch_overlay: path/to/overlay  # See Config File Format and Data Pipeline
```

:::note
`arch_overlay` is the current name for the spec overlay feature. This will be renamed to `spec_overlay` in a future version for clarity.
:::

See Config File Format for the complete reference.

## What's Next

More detailed documentation on configurations is coming soon, including:

- Full Configurations — Detailed format and examples
- Partial Configurations — Specifying requirements without full detail
- Unconfigured — The `_` config and when to use it
- Config File Format — Complete YAML reference
- Validating Configs — Checking compliance and catching errors
