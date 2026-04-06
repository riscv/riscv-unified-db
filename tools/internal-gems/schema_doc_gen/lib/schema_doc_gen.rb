# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "json"
require "yaml"
require_relative "schema_doc_gen/version"
require_relative "schema_doc_gen/index_generator"

module SchemaDocGen
  # Generates MDX documentation from a JSON Schema file for Docusaurus
  class Generator
    attr_reader :schema, :schema_path, :ref_base

    def initialize(schema_path, ref_base: "spec/schemas")
      @schema_path = schema_path
      @ref_base = ref_base
      @schema = JSON.parse(File.read(schema_path))
      @schema_defs_cache = nil # Lazy-loaded cache for schema_defs.json
    end

    # Get the schema version from $id
    def schema_version
      @schema_version ||= @schema["$id"]
    end

    # Load schema_defs.json definitions (cached)
    def schema_defs
      return @schema_defs_cache if @schema_defs_cache

      schema_defs_path = File.join(@ref_base, "schema_defs.json")
      if File.exist?(schema_defs_path)
        schema_defs_content = JSON.parse(File.read(schema_defs_path))
        @schema_defs_cache = schema_defs_content["$defs"] || {}
      else
        @schema_defs_cache = {}
      end

      @schema_defs_cache
    end

    # Generate MDX documentation for this schema
    # @return [String] MDX content
    def generate
      frontmatter = generate_frontmatter
      body_parts = []

      # Title and description (Overview)
      body_parts << generate_header

      # Quick Start examples (tagged with _quick_start: true)
      body_parts << generate_quick_start_section if @schema["examples"]

      # Composition schemas (oneOf/anyOf/allOf)
      if @schema["oneOf"] || @schema["anyOf"] || @schema["allOf"]
        composition_key = @schema["oneOf"] ? "oneOf" : (@schema["anyOf"] ? "anyOf" : "allOf")
        variants = @schema[composition_key]

        if all_internal_object_refs?(variants)
          # All variants are internal $defs references to object types — render inline as named sections
          body_parts << generate_variants_section(composition_key, variants)
          # Any $defs that are NOT referenced by the composition (e.g., shared types) still get a Definitions section
          referenced_def_names = variants.map { |v| v["$ref"].split("/").last }
          remaining_defs = (@schema["$defs"] || {}).reject { |name, _| referenced_def_names.include?(name) }
          body_parts << generate_defs_section(remaining_defs) unless remaining_defs.empty?
        else
          # Mixed or external refs — fall back to the original Schema Structure + Definitions rendering
          body_parts << generate_composition_section
          body_parts << generate_defs_section(@schema["$defs"]) if @schema["$defs"]
        end
      elsif @schema["$defs"]
        # No composition, but has $defs — render them
        body_parts << generate_defs_section(@schema["$defs"])
      end

      # Top-level properties (for simple object schemas with no composition)
      if @schema["type"] == "object" && @schema["properties"] && !@schema["oneOf"] && !@schema["anyOf"] && !@schema["allOf"]
        body_parts << generate_properties_section(@schema)
      end

      # Full examples (non-quick-start)
      body_parts << generate_examples_section if @schema["examples"]

      # Schema metadata
      body_parts << generate_metadata if @schema["$id"] || @schema["$schema"]

      body = body_parts.compact.join("\n\n")

      # If the page has any <details> blocks, inject the AnchorOpenDetails component
      # so that anchor links to collapsed blocks open them automatically
      if body.include?("<details")
        import_line = "import AnchorOpenDetails from '@site/src/components/AnchorOpenDetails';"
        [frontmatter, import_line, "<AnchorOpenDetails />", body].join("\n\n")
      else
        [frontmatter, body].join("\n\n")
      end
    end

    private

    # Escape HTML angle brackets while preserving markdown syntax
    def escape_html_in_markdown(text)
      # Preserve markdown blockquotes (> at line start) and comparison operators (>=, <=)
      # Also preserve content inside backticks
      result = ""
      in_backtick = false

      text.split("\n").each_with_index do |line, idx|
        result += "\n" if idx > 0

        if line.strip.start_with?(">")
          # This is a markdown blockquote, don't escape
          result += line
        else
          # Process character by character to handle backticks
          line_result = ""
          i = 0
          while i < line.length
            char = line[i]

            if char == '`'
              in_backtick = !in_backtick
              line_result += char
            elsif in_backtick
              # Inside backticks, don't escape
              line_result += char
            elsif char == '>' && i + 1 < line.length && line[i + 1] == '='
              # >= operator
              line_result += "&gt;="
              i += 1  # Skip the =
            elsif char == '<' && i + 1 < line.length && line[i + 1] == '='
              # <= operator
              line_result += "&lt;="
              i += 1  # Skip the =
            elsif char == '<'
              line_result += "&lt;"
            elsif char == '>'
              line_result += "&gt;"
            else
              line_result += char
            end

            i += 1
          end
          result += line_result
        end
      end

      result
    end

    def generate_frontmatter
      title = @schema["title"] || File.basename(@schema_path, ".json").split("_").map(&:capitalize).join(" ")

      <<~FRONTMATTER
        ---
        title: #{title}#{schema_version ? " (#{schema_version})" : ""}
        sidebar_label: #{title}
        custom_edit_url: null
        # This file is auto-generated from #{File.basename(@schema_path)}
        # Do not edit manually - run `bin/chore gen schema-docs` to regenerate
        ---
      FRONTMATTER
    end

    def generate_header
      title = @schema["title"] || File.basename(@schema_path, ".json").split("_").map(&:capitalize).join(" ")
      description = @schema["description"] || ""

      md = "# #{title}\n"
      if schema_version
        schema_filename = File.basename(@schema_path)
        github_schema_url = "https://github.com/riscv/riscv-unified-db/blob/main/spec/schemas/#{schema_filename}"
        github_gen_url = "https://github.com/riscv/riscv-unified-db/blob/main/tools/internal-gems/schema_doc_gen/lib/schema_doc_gen.rb"
        md += "\n<span class=\"badge badge--secondary\">#{schema_version}</span>\n"
        md += "\n<br />\n"
        md += "\n:::note Auto-generated\n"
        md += "This page is generated from [`#{schema_filename}`](#{github_schema_url}) by the [schema doc generator](#{github_gen_url}). "
        md += "To update this page, edit the schema file and run `bin/chore gen schema-docs`.\n"
        md += ":::\n"
      end
      unless description.empty?
        escaped_desc = escape_html_in_markdown(description)
        md += "\n#{escaped_desc}\n"
      end
      md
    end

    def generate_metadata
      md = "## Schema Information\n\n"
      md += "| Property | Value |\n"
      md += "|----------|-------|\n"
      md += "| Version | `#{@schema['$id']}` |\n" if @schema["$id"]
      if @schema["$schema"]
        # Link to the metaschema documentation
        schema_url = @schema["$schema"]
        # Extract draft version and create user-friendly link to json-schema.org
        if schema_url =~ %r{/draft/(\d{4}-\d{2})/}
          # Year-based version (e.g., 2020-12, 2019-09)
          version = $1
          friendly_url = "https://json-schema.org/draft/#{version}"
          md += "| JSON Schema Version | [Draft #{version}](#{friendly_url}) |\n"
        elsif schema_url =~ /draft-(\d+)/
          # Numbered draft version (e.g., draft-07, draft-04)
          draft_num = $1
          friendly_url = "https://json-schema.org/draft-#{draft_num}"
          md += "| JSON Schema Version | [Draft #{draft_num}](#{friendly_url}) |\n"
        else
          # Fallback to original URL if pattern doesn't match
          md += "| JSON Schema Version | [`#{schema_url}`](#{schema_url}) |\n"
        end
      end
      md
    end

    # Returns true if all variants in a oneOf/anyOf are internal $defs references to object types
    def all_internal_object_refs?(variants)
      return false if variants.nil? || variants.empty?
      variants.all? do |v|
        next false unless v.is_a?(Hash) && v["$ref"]&.start_with?("#/$defs/")
        def_name = v["$ref"].split("/").last
        def_schema = @schema.dig("$defs", def_name)
        def_schema && def_schema["type"] == "object"
      end
    end

    # Human-readable label for a $def variant.
    # Prefers the value of the `type` const property (e.g., "fully configured"),
    # falling back to the def name with underscores replaced by spaces.
    def variant_label(def_name, def_schema)
      type_prop = def_schema.dig("properties", "type")
      if type_prop.is_a?(Hash) && type_prop["const"]
        type_prop["const"].to_s
      else
        def_name.gsub("_", " ")
      end
    end

    # Render all composition variants as inline named sections (### headings + property tables).
    # Used when all variants are internal $defs references to object types.
    def generate_variants_section(composition_key, variants)
      label = case composition_key
              when "oneOf" then "one of"
              when "anyOf" then "any of"
              when "allOf" then "all of"
              else composition_key
              end

      md = "## Variants\n\n"
      md += "This schema accepts **#{label}** the following variants, distinguished by the `type` field:\n\n"

      # TOC list — plain links, no backticks (these are type names, not code identifiers)
      variants.each do |variant|
        def_name = variant["$ref"].split("/").last
        def_schema = @schema.dig("$defs", def_name)
        label_str = variant_label(def_name, def_schema)
        anchor = label_str.downcase.gsub(/[^a-z0-9]+/, "-").gsub(/^-|-$/, "")
        md += "- [#{label_str}](##{anchor})\n"
      end
      md += "\n"

      # Each variant as a subsection
      variants.each do |variant|
        def_name = variant["$ref"].split("/").last
        def_schema = @schema.dig("$defs", def_name)
        next unless def_schema

        label_str = variant_label(def_name, def_schema)
        md += "### `#{label_str}`\n\n"

        if def_schema["description"]
          escaped_desc = escape_html_in_markdown(def_schema["description"])
          md += "#{escaped_desc}\n\n"
        end

        md += generate_properties_table(def_schema)
        md += "\n"
      end

      md
    end

    def generate_composition_section
      md = "## Schema Structure\n\n"

      if @schema["oneOf"]
        md += "This schema accepts **one of** the following types:\n\n"
        @schema["oneOf"].each do |variant|
          md += format_composition_variant(variant)
        end
      elsif @schema["anyOf"]
        md += "This schema accepts **any of** the following types:\n\n"
        @schema["anyOf"].each do |variant|
          md += format_composition_variant(variant)
        end
      elsif @schema["allOf"]
        md += "This schema requires **all of** the following:\n\n"
        @schema["allOf"].each do |variant|
          md += format_composition_variant(variant)
        end
      end

      md
    end

    def format_composition_variant(variant)
      if variant["$ref"] && variant["$ref"].start_with?("#/$defs/")
        # Internal reference to a definition
        def_name = variant["$ref"].split("/").last
        anchor = def_name.downcase.gsub("_", "-")
        "- [`#{def_name}`](##{anchor})\n"
      elsif variant["type"]
        "- Type: `#{variant['type']}`\n"
      else
        "- (Complex type)\n"
      end
    end

    def generate_defs_section(defs)
      return "" if defs.nil? || defs.empty?

      md = "## Definitions\n\n"

      defs.each do |def_name, def_schema|
        anchor_id = def_name.downcase.gsub("_", "-")
        # Use collapsible details for each definition, with anchor inside <summary> so
        # clicking an anchor link to this block opens it automatically (via AnchorOpenDetails)
        md += "<details>\n"
        md += "<summary><a id=\"#{anchor_id}\"></a><strong><code>#{def_name}</code></strong>"
        if def_schema["description"]
          first_line = def_schema['description'].split("\n").first
          md += " — #{first_line.gsub("<", "&lt;").gsub(">", "&gt;")}"
        end
        md += "</summary>\n\n"

        if def_schema["description"]
          escaped_desc = def_schema['description'].gsub("<", "&lt;").gsub(">", "&gt;")
          md += "#{escaped_desc}\n\n"
        end

        if def_schema["type"] == "object"
          md += generate_properties_table(def_schema)
          md += "\n"
        elsif def_schema["enum"]
          md += generate_enum_section(def_schema)
          md += "\n"
        elsif def_schema["type"]
          md += "**Type:** `#{def_schema['type']}`\n\n"
        end

        md += "</details>\n\n"
      end

      md
    end

    def generate_properties_section(schema)
      return "" unless schema["properties"]

      md = "## Properties\n\n"
      md += generate_properties_table(schema)
      md
    end

    def generate_properties_table(schema)
      return "" unless schema["properties"]

      md = "| Property | Type | Required | Description |\n"
      md += "|----------|------|----------|-------------|\n"

      required_fields = schema["required"] || []
      properties_with_examples = []
      properties_with_item_schemas = []
      has_source_field = false

      # Sort: required fields first, then optional, preserving original order within each group
      sorted_props = schema["properties"].sort_by { |name, _| required_fields.include?(name) ? 0 : 1 }

      sorted_props.each do |prop_name, prop_schema|
        # Skip non-schema properties
        next unless prop_schema.is_a?(Hash) || prop_schema.is_a?(TrueClass) || prop_schema.is_a?(FalseClass)

        # Skip properties with type: null (they're placeholders to prevent usage)
        next if prop_schema.is_a?(Hash) && prop_schema["type"] == "null"

        # Skip $source — it's a tooling field, documented in a note below the table
        if prop_name == "$source"
          has_source_field = true
          next
        end

        required_str = required_fields.include?(prop_name) ? "✓" : ""
        description = prop_schema.is_a?(Hash) ? (prop_schema["description"] || "") : ""

        # Clean up description for table cell - take first sentence or line
        description = description.to_s.split(/\n\n/).first.to_s.gsub("\n", " ").strip
        # Escape angle brackets to prevent MDX from interpreting them as JSX tags
        description = description.gsub("<", "&lt;").gsub(">", "&gt;")

        # Check if this is an array-of-objects — if so, use short type + collapsible schema block
        item_obj = prop_schema.is_a?(Hash) ? resolve_array_item_object(prop_schema) : nil
        if item_obj
          item_props = item_obj[:properties]
          item_required = item_obj[:required]
          anchor_id = "#{prop_name.downcase.gsub('_', '-')}-schema"
          type_str = "#{format_array_object_type(item_props, anchor_id)} [↓&nbsp;schema](##{anchor_id})"
          properties_with_item_schemas << {name: prop_name, properties: item_props, required: item_required, anchor_id: anchor_id}
        else
          type_str = format_type(prop_schema)
        end

        # Mark properties that have examples - we'll add them after the table
        if prop_schema.is_a?(Hash) && prop_schema["examples"]
          description += " [↓&nbsp;example](##{prop_name.downcase.gsub('_', '-')}-example)" unless description.empty?
          properties_with_examples << {name: prop_name, examples: prop_schema["examples"]}
        end

        md += "| `#{prop_name}` | #{type_str} | #{required_str} | #{description} |\n"
      end

      # Add item schema blocks and examples after the table
      unless properties_with_item_schemas.empty? && properties_with_examples.empty?
        md += "\n"
        properties_with_item_schemas.each do |prop|
          md += format_item_schema_block(prop[:name], prop[:properties], prop[:required], prop[:anchor_id])
        end
        properties_with_examples.each do |prop|
          md += format_property_example(prop[:name], prop[:examples])
        end
      end

      # Note about $source if present
      if has_source_field
        md += "\n:::note Tooling field\n`$source` is an optional field set automatically by UDB tooling to record the file path this object was loaded from. You do not need to set it manually.\n:::\n"
      end

      md
    end

    # Resolve the item schema of an array property to an object with properties, if possible.
    # Returns {properties:, required:} or nil.
    def resolve_array_item_object(prop_schema)
      return nil unless prop_schema["type"] == "array" && prop_schema["items"].is_a?(Hash)

      items = prop_schema["items"]

      # Inline object
      if items["type"] == "object" && items["properties"]
        return {properties: items["properties"], required: items["required"] || []}
      end

      # $ref to schema_defs object
      if items["$ref"]&.include?("schema_defs.json#/$defs/")
        def_name = items["$ref"].split("/").last
        def_schema = schema_defs[def_name]
        if def_schema && def_schema["type"] == "object" && def_schema["properties"]
          return {properties: def_schema["properties"], required: def_schema["required"] || []}
        end
      end

      nil
    end

    # Short type string for an array-of-objects cell.
    # ≤3 keys: Array<{name, version}>; >3 keys: Array<object>
    INLINE_KEY_THRESHOLD = 3

    def format_array_object_type(item_props, anchor_id)
      if item_props.size <= INLINE_KEY_THRESHOLD
        keys = item_props.keys.map { |k| "`#{k}`" }.join(", ")
        "Array&lt;\\{#{keys}\\}&gt;"
      else
        "Array&lt;object&gt;"
      end
    end

    # Collapsible mini-table showing the item schema fields for an array-of-objects property
    def format_item_schema_block(prop_name, item_props, item_required, anchor_id)
      md = "<details style={{padding: '1rem', backgroundColor: 'var(--ifm-color-emphasis-100)', borderLeft: '4px solid var(--ifm-color-primary)', borderRadius: '4px', marginBottom: '1rem'}}>\n"
      md += "<summary style={{cursor: 'pointer', fontWeight: 'bold'}}><a id=\"#{anchor_id}\"></a><code>#{prop_name}</code> item schema</summary>\n\n"

      md += "| Property | Type | Required | Description |\n"
      md += "|----------|------|----------|-------------|\n"

      item_props.each do |key, key_schema|
        next if key_schema.is_a?(Hash) && key_schema["type"] == "null"
        req = item_required.include?(key) ? "✓" : ""

        # For $ref properties, split type and description cleanly:
        # - Type column: the underlying scalar type (string, integer, etc.)
        # - Description column: the def's description (or the property's own description)
        if key_schema.is_a?(Hash) && key_schema["$ref"]
          ref = key_schema["$ref"]
          if ref.start_with?("#/$defs/")
            # Internal ref within schema_defs — resolve for description
            def_name = ref.split("/").last
            def_schema = schema_defs[def_name]
            if def_schema
              type_str = format_ref_type(def_name, def_schema)
              desc = key_schema["description"] || format_ref_description(def_name, def_schema)
            else
              type_str = format_type(key_schema)
              desc = key_schema["description"] || ""
            end
          elsif ref.include?("schema_defs.json#/$defs/")
            # External ref to schema_defs
            def_name = ref.split("/").last
            def_schema = schema_defs[def_name]
            if def_schema
              type_str = format_ref_type(def_name, def_schema)
              desc = key_schema["description"] || format_ref_description(def_name, def_schema)
            else
              type_str = format_type(key_schema)
              desc = key_schema["description"] || ""
            end
          else
            type_str = format_type(key_schema)
            desc = key_schema["description"] || ""
          end
        else
          type_str = format_type(key_schema)
          desc = key_schema.is_a?(Hash) ? (key_schema["description"] || "") : ""
        end

        desc = desc.to_s.split(/\n\n/).first.to_s.gsub("\n", " ").strip
        desc = desc.gsub("<", "&lt;").gsub(">", "&gt;")
        md += "| `#{key}` | #{type_str} | #{req} | #{desc} |\n"
      end

      md += "\n</details>\n\n"
      md
    end

    # Format a property example as a collapsible details section after the table
    def format_property_example(prop_name, examples)
      example = examples.first # Use first example
      anchor_id = "#{prop_name.downcase.gsub('_', '-')}-example"

      md = "<details style={{padding: '1rem', backgroundColor: 'var(--ifm-color-emphasis-100)', borderLeft: '4px solid var(--ifm-color-primary)', borderRadius: '4px', marginBottom: '1rem'}}>\n"
      md += "<summary style={{cursor: 'pointer', fontWeight: 'bold'}}><a id=\"#{anchor_id}\"></a><code>#{prop_name}</code> example</summary>\n\n"
      md += "```yaml\n"
      if example.is_a?(Hash) || example.is_a?(Array)
        display_example = example.is_a?(Hash) ? example.reject { |k, _| k.start_with?("_") } : example
        md += YAML.dump(display_example).sub(/^---\n/, '')
      else
        md += example.to_s
      end
      md += "\n```\n\n"
      md += "</details>\n\n"
      md
    end

    def generate_enum_section(schema)
      return "" unless schema["enum"]

      md = "**Allowed values:**\n\n"
      schema["enum"].each do |value|
        md += "- `#{value}`\n"
      end
      md
    end

    def generate_quick_start_section
      return "" unless @schema["examples"]

      quick_start = @schema["examples"].select { |e| e.is_a?(Hash) && e["_quick_start"] }
      return "" if quick_start.empty?

      md = "## Quick Start\n\n"
      quick_start.each do |example|
        title = example["_title"] || "Example"
        md += "**#{title}:**\n"
        md += "```yaml\n"
        display_example = example.reject { |k, _| k.start_with?("_") }
        md += YAML.dump(display_example).sub(/^---\n/, '')
        md += "\n```\n\n"
      end
      md
    end

    def generate_examples_section
      return "" unless @schema["examples"]

      # Only show non-quick-start examples
      examples = @schema["examples"].reject { |e| e.is_a?(Hash) && e["_quick_start"] }
      return "" if examples.empty?

      md = "## Examples\n\n"
      examples.each_with_index do |example, idx|
        md += "<details style={{padding: '1rem', backgroundColor: 'var(--ifm-color-emphasis-100)', borderLeft: '4px solid var(--ifm-color-primary)', borderRadius: '4px', marginBottom: '1rem'}}>\n"

        # Add a descriptive summary if the example has a title/description
        title = if example.is_a?(Hash) && example["_title"]
          example["_title"]
        else
          "Example #{idx + 1}"
        end
        md += "<summary style={{cursor: 'pointer', fontWeight: 'bold'}}>#{title}</summary>\n\n"

        md += "```yaml\n"
        if example.is_a?(Hash) || example.is_a?(Array)
          # Remove meta fields like _title before displaying
          display_example = example.is_a?(Hash) ? example.reject { |k, _| k.start_with?("_") } : example
          # Convert to YAML for better readability of config files
          md += YAML.dump(display_example).sub(/^---\n/, '') # Remove YAML document separator
        else
          md += example.to_s
        end
        md += "\n```\n\n"
        md += "</details>\n\n"
      end

      md
    end

    # Return the underlying scalar type string for a schema_defs definition,
    # for use in the Type column of a property table.
    # Follows $ref chains until a type, enum, or oneOf/anyOf is found.
    def format_ref_type(def_name, def_schema)
      return "`string`" unless def_schema.is_a?(Hash)
      if def_schema["$ref"]&.start_with?("#/$defs/")
        nested = schema_defs[def_schema["$ref"].split("/").last]
        return format_ref_type(def_schema["$ref"].split("/").last, nested) if nested
      end
      if def_schema["type"]
        if def_schema["type"] == "array" && def_schema["items"].is_a?(Hash)
          items = def_schema["items"]
          if items["$ref"]&.start_with?("#/$defs/")
            item_def_name = items["$ref"].split("/").last
            item_def = schema_defs[item_def_name]
            item_type = item_def ? format_ref_type(item_def_name, item_def) : "`string`"
          else
            item_type = format_type(items)
          end
          "Array&lt;#{item_type}&gt;"
        elsif def_schema["enum"]
          def_schema["enum"].map { |v| "`#{v}`" }.join(" \\| ")
        else
          "`#{def_schema['type']}`"
        end
      elsif def_schema["enum"]
        def_schema["enum"].map { |v| "`#{v}`" }.join(" \\| ")
      elsif def_schema["oneOf"] || def_schema["anyOf"]
        key = def_schema["oneOf"] ? "oneOf" : "anyOf"
        def_schema[key].map { |s|
          if s.is_a?(Hash) && s["$ref"]&.start_with?("#/$defs/")
            rn = s["$ref"].split("/").last
            rd = schema_defs[rn]
            rd ? format_ref_type(rn, rd) : format_type(s)
          elsif s.is_a?(Hash) && s["type"] == "array" && s["items"].is_a?(Hash) && s["items"]["$ref"]&.start_with?("#/$defs/")
            item_def_name = s["items"]["$ref"].split("/").last
            item_def = schema_defs[item_def_name]
            item_type = item_def ? format_ref_type(item_def_name, item_def) : "`string`"
            "Array&lt;#{item_type}&gt;"
          else
            format_type(s)
          end
        }.join(" \\| ")
      else
        "`any`"
      end
    end

    # Return the human-readable description for a schema_defs definition,
    # for use in the Description column of a property table.
    # Returns the first definition in the chain that has a description.
    def format_ref_description(def_name, def_schema)
      return "" unless def_schema.is_a?(Hash)
      return def_schema["description"] if def_schema["description"]
      if def_schema["$ref"]&.start_with?("#/$defs/")
        nested_name = def_schema["$ref"].split("/").last
        nested = schema_defs[nested_name]
        return format_ref_description(nested_name, nested) if nested
      end
      ""
    end

    # Format a sub-schema that may be a #/$defs/ ref within schema_defs.
    # Used when expanding oneOf/anyOf inside format_inline_definition, where
    # #/$defs/ refs point into schema_defs (not the current page's $defs).
    def format_inline_or_type(sub_schema)
      if sub_schema.is_a?(Hash) && sub_schema["$ref"]&.start_with?("#/$defs/")
        def_name = sub_schema["$ref"].split("/").last
        def_schema = schema_defs[def_name]
        return format_inline_definition(def_name, def_schema) if def_schema
      end
      format_type(sub_schema)
    end

    # Format an inlined definition from schema_defs
    def format_inline_definition(def_name, def_schema)
      # If the def has its own description, use it directly — don't follow $ref chains
      return def_schema["description"] if def_schema["description"]

      # Handle nested $ref in def_schema (e.g., extension_version -> rvi_version)
      if def_schema["$ref"]
        ref = def_schema["$ref"]
        if ref.start_with?("#/$defs/")
          nested_def_name = ref.split("/").last
          nested_def_schema = schema_defs[nested_def_name]
          return format_inline_definition(nested_def_name, nested_def_schema) if nested_def_schema
        end
      end

      parts = []

      # Add type if present
      if def_schema["type"]
        # If enum is present, show the allowed values regardless of type
        if def_schema["enum"]
          parts << def_schema["enum"].map { |v| "`#{v}`" }.join(" \\| ")
        elsif def_schema["type"] == "string"
          # If there's a description, use it as the human-readable type label
          if def_schema["description"]
            parts << def_schema["description"]
          else
            # For strings, show any constraints
            constraints = []
            constraints << "pattern: `#{def_schema['pattern']}`" if def_schema["pattern"]
            constraints << "format: `#{def_schema['format']}`" if def_schema["format"]
            constraints << "min: #{def_schema['minLength']}" if def_schema["minLength"]
            constraints << "max: #{def_schema['maxLength']}" if def_schema["maxLength"]

            if constraints.empty?
              parts << "`string`"
            else
              parts << "`string` (#{constraints.join(", ")})"
            end
          end
        elsif def_schema["type"] == "integer" || def_schema["type"] == "number"
          # For numbers, show any constraints
          constraints = []
          constraints << "min: #{def_schema['minimum']}" if def_schema["minimum"]
          constraints << "max: #{def_schema['maximum']}" if def_schema["maximum"]

          if constraints.empty?
            parts << "`#{def_schema['type']}`"
          else
            parts << "`#{def_schema['type']}` (#{constraints.join(", ")})"
          end
        elsif def_schema["type"] == "object"
          # For open objects, use description if available
          if def_schema["description"]
            parts << def_schema["description"].split(/\n\n/).first.to_s.gsub("\n", " ").strip
          else
            parts << "`object`"
          end
        else
          parts << "`#{def_schema['type']}`"
        end
      elsif def_schema["enum"]
        # Show enum values
        parts << def_schema["enum"].map { |v| "`#{v}`" }.join(" \\| ")
      elsif def_schema["oneOf"]
        # Use description if available, otherwise expand the oneOf
        if def_schema["description"]
          parts << def_schema["description"]
        else
          types = def_schema["oneOf"].map { |s| format_inline_or_type(s) }.join(" \\| ")
          parts << types
        end
      elsif def_schema["anyOf"]
        # Use description if available, otherwise expand the anyOf
        if def_schema["description"]
          parts << def_schema["description"]
        else
          types = def_schema["anyOf"].map { |s| format_inline_or_type(s) }.join(" \\| ")
          parts << types
        end
      else
        parts << "`any`"
      end

      parts.join(" ")
    end

    def format_type(schema)
      # Handle boolean shorthand (true/false in JSON Schema)
      return "`any`" if schema == true
      return "`never`" if schema == false

      if schema["type"]
        type = schema["type"]

        # Handle const - show type with the constant value
        if schema["const"]
          return "`#{type}` (const: `#{schema['const']}`)"
        end

        # Handle enum - show allowed values
        if schema["enum"]
          return schema["enum"].map { |v| "`#{v}`" }.join(" \\| ")
        end

        # Handle arrays
        if type == "array" && schema["items"]
          items_schema = schema["items"]
          if items_schema == true
            return "Array&lt;`any`&gt;"
          elsif items_schema == false
            return "Array&lt;`never`&gt;"
          elsif items_schema["$ref"] && items_schema["$ref"].include?("schema_defs.json#/$defs/")
            # $ref to schema_defs — inline the definition type (non-object refs, e.g. simple strings)
            def_name = items_schema["$ref"].split("/").last
            def_schema = schema_defs[def_name]
            if def_schema && !(def_schema["type"] == "object" && def_schema["properties"])
              return "Array&lt;#{format_inline_definition(def_name, def_schema)}&gt;" if def_schema
            end
            # Object refs are handled by resolve_array_item_object in generate_properties_table
            return "Array&lt;object&gt;"
          elsif items_schema["type"] == "object" && items_schema["properties"]
            # Inline object items are handled by resolve_array_item_object in generate_properties_table
            return "Array&lt;object&gt;"
          else
            item_type = format_type(items_schema)
            return "Array&lt;#{item_type}&gt;"
          end
        end

        "`#{type}`"
      elsif schema["$ref"]
        # Reference to another definition
        ref = schema["$ref"]
        if ref.start_with?("#")
          # Internal reference - link to anchor
          ref_name = ref.split("/").last
          "[`#{ref_name}`](##{ref_name.downcase.gsub("_", "-")})"
        else
          # External reference
          # Check if this is an absolute URL (http:// or https://) BEFORE splitting
          if ref.start_with?("http://", "https://")
            # Link directly to the external URL
            return "[`#{ref}`](#{ref})"
          end

          # Split at # first to separate file from anchor
          parts = ref.split("#", 2)
          ref_file_name = File.basename(parts[0], ".json")

          # Check if this is a reference to schema_defs - if so, inline it
          if ref_file_name == "schema_defs" && parts.length > 1
            # Extract the definition name from the anchor
            # Handle both draft-07 /definitions/ and draft-2020-12 /$defs/
            def_path = parts[1].split("/")
            if def_path[0] == "" && (def_path[1] == "$defs" || def_path[1] == "definitions") && def_path.length == 3
              def_name = def_path[2]
              # Get the definition from schema_defs
              def_schema = schema_defs[def_name]
              if def_schema
                # Inline the definition
                return format_inline_definition(def_name, def_schema)
              end
            end
          end

          # Not schema_defs or couldn't inline - create a link
          ref_anchor = parts.length > 1 ? parts[1].gsub("/", "-").downcase : ""

          # Determine the version of the referenced schema
          ref_schema_path = File.join(@ref_base, parts[0])
          ref_version = schema_version # default to same version
          if File.exist?(ref_schema_path)
            begin
              ref_schema = JSON.parse(File.read(ref_schema_path))
              ref_version = ref_schema["$id"] if ref_schema["$id"]
            rescue
              # If we can't read it, assume same version
            end
          end

          # If the referenced schema's $id is a URL, link to it directly
          if ref_version&.start_with?("http://", "https://")
            return "[`#{ref_file_name}`](#{ref_version})"
          end

          # Build the relative path
          path_prefix = if ref_version == schema_version
            "./"
          else
            "../#{ref_version}/"
          end

          if ref_anchor.empty?
            "[`#{ref_file_name}`](#{path_prefix}#{ref_file_name}.mdx)"
          else
            "[`#{ref_file_name}##{ref_anchor}`](#{path_prefix}#{ref_file_name}.mdx##{ref_anchor})"
          end
        end
      elsif schema["enum"]
        # Infer type from enum values and display them
        schema["enum"].map { |v| "`#{v}`" }.join(" \\| ")
      elsif schema["oneOf"]
        types = schema["oneOf"].map { |s| format_type(s) }.join(" \\| ")
        "One of: #{types}"
      elsif schema["anyOf"]
        types = schema["anyOf"].map { |s| format_type(s) }.join(" \\| ")
        "Any of: #{types}"
      else
        "`any`"
      end
    end
  end
end
