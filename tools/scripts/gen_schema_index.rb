#!/usr/bin/env ruby
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Generates a JSON index of all available schema versions and files.
# Usage: gen_schema_index.rb <schemas_dir> <output_json>
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

unless schemas_dir.exist?
  # No schemas published yet; write an empty index
  output_path.write(JSON.pretty_generate({ "versions" => {} }) + "\n")
  exit 0
end

versions = {}
schemas_dir.each_child.select(&:directory?).sort.each do |version_dir|
  version = version_dir.basename.to_s
  files = version_dir.glob("*.json").map { |f| f.basename.to_s }.sort
  versions[version] = files unless files.empty?
end

output_path.write(JSON.pretty_generate({ "versions" => versions }) + "\n")
puts "Schema index written to #{output_path}"
