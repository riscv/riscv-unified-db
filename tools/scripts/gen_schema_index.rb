#!/usr/bin/env ruby
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Generates (or updates) a JSON index of all available schema versions and files.
# Usage: gen_schema_index.rb <schemas_dir> <output_json>
#
# If <output_json> already exists, its contents are used as the base and any
# versions/files found in <schemas_dir> are merged in.  Versions that exist in
# the current index but are absent from <schemas_dir> are preserved, so that
# old versions stored only in git history or release assets are not dropped.
#
# The output JSON has the structure:
#   {
#     "versions": {
#       "v0.1": ["csr_schema.json", "ext_schema.json", ...],
#       ...
#     }
#   }

require "json"
require "pathname"

schemas_dir = Pathname.new(ARGV[0])
output_path = Pathname.new(ARGV[1])

# Load existing index as the base so old versions are preserved.
versions =
  if output_path.exist?
    JSON.parse(output_path.read).fetch("versions", {})
  else
    {}
  end

# Merge in any versions/files present on disk.
if schemas_dir.exist?
  schemas_dir.each_child.select(&:directory?).sort.each do |version_dir|
    version = version_dir.basename.to_s
    files = version_dir.glob("*.json").map { |f| f.basename.to_s }.sort
    next if files.empty?

    # Union with any files already recorded for this version.
    versions[version] = ((versions[version] || []) | files).sort
  end
end

output_path.write(JSON.pretty_generate({ "versions" => versions }) + "\n")
puts "Schema index written to #{output_path}"
