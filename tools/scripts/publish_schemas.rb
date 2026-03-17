#!/usr/bin/env ruby
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Publishes resolved schema files as GitHub release assets.
#
# Each schema has its own independent version. For each schema found in
# gen/schemas/<schema_name>/<version>/, this script:
#   1. Checks if a release tag "schemas/<schema_name>/<version>" already exists.
#   2. If not, creates a new release with that tag.
#   3. Checks if the schema file asset already exists and whether it has changed.
#   4. Uploads new or changed schema files as release assets.
#
# Requires the GH_TOKEN environment variable and the `gh` CLI to be available.

require "json"
require "pathname"
require "open3"

root = Pathname.new(__dir__).parent.parent
gen_schemas_dir = root / "gen" / "schemas"

unless gen_schemas_dir.exist?
  warn "gen/schemas does not exist; run './do gen:schemas' first"
  exit 1
end

def run_cmd(*args)
  stdout, stderr, status = Open3.capture3(*args)
  unless status.success?
    warn "Command failed: #{args.join(' ')}\n#{stderr}"
    exit 1
  end
  stdout
end

def gh(*args)
  run_cmd("gh", *args)
end

def release_exists?(tag)
  _stdout, _stderr, status = Open3.capture3("gh", "release", "view", tag)
  status.success?
end

def asset_content(tag, asset_name)
  stdout, _stderr, status = Open3.capture3(
    "gh", "release", "download", tag,
    "--pattern", asset_name,
    "--output", "-"
  )
  status.success? ? stdout : nil
end

# gen/schemas/<schema_name>/<version>/<schema_name>
gen_schemas_dir.each_child.select(&:directory?).sort.each do |schema_dir|
  schema_name = schema_dir.basename.to_s

  schema_dir.each_child.select(&:directory?).sort.each do |version_dir|
    version = version_dir.basename.to_s
    tag = "schemas/#{schema_name}/#{version}"

    puts "Processing #{schema_name} #{version}"

    unless release_exists?(tag)
      puts "  Creating release #{tag}..."
      gh(
        "release", "create", tag,
        "--title", "#{schema_name} #{version}",
        "--notes", "#{schema_name} version #{version} for riscv-unified-db.\n\n" \
                   "Published at:\n" \
                   "https://riscv.github.io/riscv-unified-db/schemas/#{schema_name}/#{version}/#{schema_name}",
        "--latest=false"
      )
    end

    version_dir.glob("*.json").sort.each do |schema_file|
      asset_name = schema_file.basename.to_s
      local_content = schema_file.read
      remote_content = asset_content(tag, asset_name)

      if remote_content.nil?
        puts "  Uploading new asset: #{asset_name}"
        gh("release", "upload", tag, schema_file.to_s, "--clobber")
      elsif remote_content.strip != local_content.strip
        puts "  Updating changed asset: #{asset_name}"
        gh("release", "upload", tag, schema_file.to_s, "--clobber")
      else
        puts "  Unchanged: #{asset_name}"
      end
    end
  end
end

puts "Schema release publishing complete."
