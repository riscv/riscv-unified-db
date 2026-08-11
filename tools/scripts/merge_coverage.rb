#!/usr/bin/env ruby
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Merges multiple per-test IDL coverage JSON files into a single aggregate report.
#
# Usage: merge_coverage.rb <manifest.json> <output_dir> [coverage_file1.json ...]
#
# Arguments:
#   manifest.json     - Probe manifest listing all probes with id, source, kind, etc.
#   output_dir        - Directory where merged output files are written.
#   coverage_file...  - One or more per-test coverage JSON files to merge.
#
# Output files written to output_dir:
#   merged_coverage.json   - Summed hit counts for every probe id.
#   coverage_summary.json  - Per-source summary with probe count, hit count, and pct.

require "json"
require "pathname"

if ARGV.length < 2
  warn "Usage: merge_coverage.rb <manifest.json> <output_dir> [coverage_file1.json ...]"
  exit 1
end

manifest_path = Pathname.new(ARGV[0])
output_dir    = Pathname.new(ARGV[1])
coverage_files = ARGV[2..]

unless manifest_path.exist?
  warn "Error: manifest file not found: #{manifest_path}"
  exit 1
end

# Parse manifest and build probe table.
manifest = JSON.parse(manifest_path.read)
probes = manifest.fetch("probes")

# Initialize merged counts to zero for every known probe id.
merged = {}
probes.each { |p| merged[p["id"].to_s] = 0 }

# Accumulate hit counts from each coverage file.
coverage_files.each do |path|
  pn = Pathname.new(path)
  unless pn.exist?
    warn "Warning: coverage file not found, skipping: #{path}"
    next
  end
  data = JSON.parse(pn.read)
  data.each do |id_str, count|
    if merged.key?(id_str)
      merged[id_str] += count.to_i
    else
      warn "Warning: probe id #{id_str} in #{path} is not in the manifest (skipping)"
    end
  end
end

# Ensure output directory exists.
output_dir.mkpath

# Write merged_coverage.json.
merged_path = output_dir / "merged_coverage.json"
merged_path.write(JSON.pretty_generate(merged) + "\n")

# Build per-source summary.
# Group probes by source; preserve insertion order (manifest order).
summary = {}
probes.each do |p|
  source = p["source"]
  summary[source] ||= { "probes" => 0, "hit" => 0, "kind" => p["kind"] }
  summary[source]["probes"] += 1
  summary[source]["hit"] += 1 if merged[p["id"].to_s].to_i > 0
end

# Compute percentages.
summary.each_value do |s|
  s["pct"] = s["probes"] > 0 ? (s["hit"].to_f / s["probes"] * 100.0).round(1) : 0.0
end

# Write coverage_summary.json.
summary_path = output_dir / "coverage_summary.json"
summary_path.write(JSON.pretty_generate(summary) + "\n")

# Print brief summary to stdout.
total_probes = probes.length
total_hit    = merged.values.count { |c| c > 0 }
pct          = total_probes > 0 ? (total_hit.to_f / total_probes * 100.0).round(1) : 0.0

puts "Coverage: #{total_hit} / #{total_probes} probes hit (#{pct}%)"
puts "Wrote: #{merged_path}"
puts "Wrote: #{summary_path}"
