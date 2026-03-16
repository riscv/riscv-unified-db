#!/usr/bin/env ruby
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Generates (or updates) a JSON index of all available schema versions.
# Usage: gen_schema_index.rb <schemas_dir> <output_json>
#
# Each schema has its own independent version history. The directory layout is:
#   <schemas_dir>/<schema_name>/<version>/<schema_name>
#
# If <output_json> already exists, its contents are used as the base and any
# schema/version combinations found in <schemas_dir> are merged in. Entries
# that exist in the current index but are absent from <schemas_dir> are
# preserved, so that old versions stored only in release assets are not dropped.
#
# The output JSON has the structure:
#   {
#     "schemas": {
#       "csr_schema.json": ["v0.1", "v0.2", ...],
#       "ext_schema.json": ["v0.1"],
#       ...
#     }
#   }

require "json"
require "pathname"

schemas_dir = Pathname.new(ARGV[0])
output_path = Pathname.new(ARGV[1])

# Load existing index as the base so old versions are preserved.
schemas =
  if output_path.exist?
    JSON.parse(output_path.read).fetch("schemas", {})
  else
    {}
  end

# Merge in any schema/version combinations present on disk.
if schemas_dir.exist?
  schemas_dir.each_child.select(&:directory?).sort.each do |schema_dir|
    schema_name = schema_dir.basename.to_s
    next if schema_name == "index.json"

    versions = schema_dir.each_child.select(&:directory?).map { |d| d.basename.to_s }.sort
    next if versions.empty?

    # Union with any versions already recorded for this schema.
    schemas[schema_name] = ((schemas[schema_name] || []) | versions).sort
  end
end

output_path.write(JSON.pretty_generate({ "schemas" => schemas }) + "\n")
puts "Schema index written to #{output_path}"
