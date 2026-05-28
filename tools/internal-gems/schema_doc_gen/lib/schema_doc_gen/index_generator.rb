# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "pathname"

module SchemaDocGen
  # Generates an index page for schema documentation
  class IndexGenerator
    attr_reader :output_dir

    def initialize(output_dir)
      @output_dir = Pathname(output_dir.to_s)
    end

    # Scan the output directory for generated schema docs and create an index
    # @return [String] MDX content for the index page
    def generate
      versions = scan_versions
      schemas_by_version = scan_schemas(versions)

      parts = []
      parts << generate_frontmatter
      parts << generate_header
      parts << generate_overview
      parts << generate_schemas_section(versions, schemas_by_version)

      parts.join("\n\n").rstrip + "\n"
    end

    private

    def scan_versions
      return [] unless @output_dir.exist?

      @output_dir.children
        .select(&:directory?)
        .map { |d| d.basename.to_s }
        .select { |d| d.match?(/^v\d+(\.\d+)*$/) }
        .sort_by { |d| Gem::Version.new(d.delete_prefix("v")) }
        .reverse # Highest version first
    end

    def scan_schemas(versions)
      schemas = {}

      versions.each do |version|
        version_dir = @output_dir / version
        schema_files = version_dir.glob("*.mdx").map { |f| f.basename(".mdx").to_s }.sort

        schemas[version] = schema_files
      end

      schemas
    end

    def generate_frontmatter
      <<~FRONTMATTER
        ---
        title: Schema Reference
        sidebar_position: 1
        ---
      FRONTMATTER
    end

    def generate_header
      <<~HEADER
        # Schema Reference

        UDB uses JSON Schema to define and validate the structure of YAML files in `spec/`. Each schema is versioned independently — the version shown on each card is that schema's current version.
      HEADER
    end

    def generate_overview
      <<~OVERVIEW
        ## About Schema Versions

        Schemas are versioned independently of the UDB repository. Each schema file declares its version in the `$id` field. When a schema format changes, a new version is created to maintain backward compatibility with existing data files.
      OVERVIEW
    end

    def generate_schemas_section(versions, schemas_by_version)
      return "No schema documentation found." if versions.empty?

      # Collect all schemas across all versions, sorted alphabetically by name.
      # Each entry: {name:, version:, path:}
      all_schemas = []
      versions.each do |version|
        (schemas_by_version[version] || []).each do |schema|
          all_schemas << {name: schema, version: version}
        end
      end
      all_schemas.sort_by! { |s| [s[:name], s[:version]] }

      md = "## Schemas\n\n"
      md += "<div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem', marginBottom: '2rem'}}>\n\n"

      all_schemas.each do |schema|
        schema_title = schema[:name].split("_").map(&:capitalize).join(" ")
        md += <<~CARD
          <div style={{padding: '1rem', border: '1px solid var(--ifm-color-emphasis-300)', borderRadius: '8px'}}>
            <strong><a href="./#{schema[:version]}/#{schema[:name]}">#{schema_title}</a></strong><br />
            <span className="badge badge--secondary" style={{marginTop: '0.4rem', display: 'inline-block'}}>#{schema[:version]}</span>
          </div>

        CARD
      end

      md += "</div>\n\n"
      md
    end
  end
end
