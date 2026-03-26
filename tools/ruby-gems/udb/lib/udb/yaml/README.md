<!--
Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
SPDX-License-Identifier: BSD-3-Clause-Clear
-->

# Ruby YAML Resolver

This directory contains a pure Ruby implementation of YAML resolution that preserves comments and key order.

## Overview

The Ruby YAML resolver provides YAML resolution while staying entirely within Ruby. It consists of three main components:

### Components

1. **CommentParser** (`comment_parser.rb`)
   - Parses YAML files and extracts comments with their positions
   - Tracks comment types (header, inline, block)
   - Associates comments with their corresponding key paths
   - Maintains a `CommentMap` for efficient comment lookup

2. **PreservingEmitter** (`preserving_emitter.rb`)
   - Emits YAML while preserving comments
   - Maintains key order (using Ruby's ordered hashes)
   - Handles proper indentation and formatting
   - Reinserts comments at appropriate positions

3. **Resolver** (`resolver.rb`)
   - Main resolver logic for merge and resolve operations
   - Implements `$inherits` expansion
   - Handles `$remove` directives
   - Performs JSON Merge Patch (RFC 7386)
   - Manages two-pass resolution for cross-file references

## Features

### Comment Preservation
- **Header comments**: Comments before the document starts
- **Inline comments**: Comments on the same line as a key-value pair
- **Block comments**: Comments on their own line before a key

### Key Order Preservation
- Uses Ruby's built-in ordered hash behavior (Ruby 1.9+)
- Maintains the original order of keys in YAML files

### Operations

#### Merge Operation
Merges an overlay YAML file on top of a base file:
```ruby
resolver = Udb::Yaml::Resolver.new
resolver.merge_files(base_dir, overlay_dir, output_dir)
```

#### Resolve Operation
Resolves `$inherits` references and applies defaults:
```ruby
resolver = Udb::Yaml::Resolver.new
resolver.resolve_files(input_dir, output_dir, no_checks: false)
```

## Integration

The resolver is integrated into `Udb::Resolver` in `lib/udb/resolver.rb`:

```ruby
# Merge operation
yaml_resolver = Udb::Yaml::Resolver.new(quiet: @quiet, compile_idl: @compile_idl)
yaml_resolver.merge_files(std_path.to_s, overlay_path&.to_s, merged_spec_path(config_name).to_s)

# Resolve operation
yaml_resolver = Udb::Yaml::Resolver.new(quiet: @quiet, compile_idl: @compile_idl)
yaml_resolver.resolve_files(merged_spec_path(config_name).to_s, resolved_spec_path(config_name).to_s, no_checks: false)
```

## Implementation Details

### Comment Association Algorithm

Comments are associated with keys using a proximity-based algorithm:
- **Inline comments**: Belong to the key on the same line
- **Block comments**: Belong to the next key after the comment
- **Header comments**: Stored separately at the document level

### Inheritance Resolution

The resolver handles `$inherits` in two passes:
1. **First pass**: Build a cache of all resolved objects
2. **Second pass**: Write resolved files with proper `$parent_of` tracking

This two-pass approach ensures that cross-file references are properly resolved even when files reference each other.

### Deep Merging

The resolver implements deep merging for nested hashes:
- Hash values are recursively merged
- Array and scalar values are replaced (not merged)
- `null` values in the patch remove keys from the base

## Limitations

### Current Limitations

1. **Comment positioning**: The current implementation uses a simplified line-to-key-path mapping. Complex YAML structures (deeply nested arrays, flow-style collections) may have imperfect comment association.

2. **Quote style preservation**: The emitter uses a heuristic to determine when strings need quoting. It may not preserve the exact quote style from the original file.
