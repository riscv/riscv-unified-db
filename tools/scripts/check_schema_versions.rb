#!/usr/bin/env ruby
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Checks that each resolved schema file either:
#   (a) does not yet exist at its published $id URL, or
#   (b) is an identical match to the file at that URL.
#
# This ensures that once a schema version is published, it is immutable.

require "json"
require "net/http"
require "uri"
require "pathname"

root = Pathname.new(__dir__).parent.parent
gen_schemas_dir = root / "gen" / "schemas"

unless gen_schemas_dir.exist?
  warn "gen/schemas does not exist; run './do gen:schemas' first"
  exit 1
end

failures = []

gen_schemas_dir.glob("**/*.json").sort.each do |schema_file|
  next if File.directory?(schema_file)
  schema_data = JSON.parse(schema_file.read)
  published_id = schema_data["$id"]
  if published_id.nil?
    warn "WARNING: #{schema_file} has no '$id' field (skipping version check)"
    next
  end

  uri = URI.parse(published_id)
  begin
    response = Net::HTTP.get_response(uri)
  rescue => e
    warn "WARNING: Could not reach #{published_id}: #{e.message} (skipping)"
    next
  end

  if response.code == "200"
    remote_content = response.body
    local_content = schema_file.read
    if remote_content.strip != local_content.strip
      failures << "Schema mismatch for #{published_id}:\n" \
                  "  Local:  #{schema_file}\n" \
                  "  Remote: #{published_id}\n" \
                  "  The published schema differs from the local version.\n" \
                  "  To fix: bump the schema version (\$id) to a new version number.\n" \
                  "  Note: new versions are published automatically when merged to main.\n" \
                  "  To skip this check locally, do not run check_schema_versions."
    else
      puts "OK (matches published): #{published_id}"
    end
  elsif response.code == "404"
    puts "OK (not yet published): #{published_id}"
  else
    warn "WARNING: Unexpected HTTP #{response.code} for #{published_id} (skipping)"
  end
end

if failures.any?
  failures.each { |f| warn f }
  exit 1
end

puts "All schema version checks passed."
