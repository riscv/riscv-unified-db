# Internal Gems

This directory contains Ruby gems used internally for UDB development, build processes, and tooling. These gems are **not** published to RubyGems.org and are **not** intended for external use.

## Directory Purpose

- **External/published gems**: Located in `tools/ruby-gems/`
  - `udb` - Core UDB library
  - `idlc` - IDL compiler
  - `udb-gen` - UDB generator framework
  - `idl_highlighter` - Syntax highlighting for IDL
  - `udb_helpers` - Helper utilities

- **Internal/build gems**: Located in `tools/internal-gems/` (this directory)
  - `schema_doc_gen` - Generates documentation from JSON schemas
  - (Future internal tooling gems)

## When to Add a Gem Here

Place a gem in `tools/internal-gems/` if it is:
- Used only during the build/CI process
- Generates documentation or build artifacts
- Not intended to be used by external consumers
- Specific to UDB's development workflow

## Usage

Internal gems are included in the top-level `Gemfile`:

```ruby
# internal gems (build/tooling only)
gemspec path: "tools/internal-gems/schema_doc_gen"
```

Run `bundle install` from the repository root to install all dependencies.

## See Also

- `tools/ruby-gems/` - Published/external gems
- `tools/scripts/` - Simple standalone scripts for chores
