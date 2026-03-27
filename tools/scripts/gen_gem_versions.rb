#!/usr/bin/env ruby
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

# Script to:
#   Step A: Auto-increment versions for gems whose source changed without a bump (with cascade)
#   Step B: Update inter-gem dependency pins in gemspecs to exact current versions
#   Step C: Regenerate Gemfile.lock files (sync only, no --update)
#
# Usage:
#   gen_gem_versions.rb [--fail-on-change] [--check] [--base-ref <ref>]
#
#   --fail-on-change  Exit 1 if any file changed (for CI drift detection)
#   --check           Only detect version-bump issues, no writes; exit 1 if any found
#   --base-ref <ref>  Git ref to compare against (default: origin/main)

require "digest"
require "optparse"
require "pathname"
require "set"

UDB_ROOT = Pathname.new(__FILE__).dirname.parent.parent.realpath

# Gem metadata: name, source dir, version file, additional watched dirs
GEMS = [
  {
    name: "idlc",
    dir: "tools/ruby-gems/idlc",
    version_file: "tools/ruby-gems/idlc/lib/idlc/version.rb",
    additional_dirs: []
  },
  {
    name: "udb_helpers",
    dir: "tools/ruby-gems/udb_helpers",
    version_file: "tools/ruby-gems/udb_helpers/lib/udb_helpers/version.rb",
    additional_dirs: []
  },
  {
    name: "udb",
    dir: "tools/ruby-gems/udb",
    version_file: "tools/ruby-gems/udb/lib/udb/version.rb",
    additional_dirs: ["spec"]
  },
  {
    name: "udb-gen",
    dir: "tools/ruby-gems/udb-gen",
    version_file: "tools/ruby-gems/udb-gen/lib/udb-gen/version.rb",
    additional_dirs: ["spec"]
  }
].freeze

# Dependency graph: gem name → list of gem names that depend on it (reverse deps)
DEPENDENTS = {
  "idlc"        => ["udb"],
  "udb_helpers" => ["udb"],
  "udb"         => ["udb-gen"],
  "udb-gen"     => []
}.freeze

# Gemspec files that have inter-gem dependencies to pin
GEMSPEC_PINS = [
  { gemspec: "tools/ruby-gems/udb/udb.gemspec",         dep_name: "idlc",        version_gem: "idlc" },
  { gemspec: "tools/ruby-gems/udb/udb.gemspec",         dep_name: "udb_helpers", version_gem: "udb_helpers" },
  { gemspec: "tools/ruby-gems/udb-gen/udb-gen.gemspec", dep_name: "udb",         version_gem: "udb" }
].freeze

# Gemfiles to re-lock, in dependency order
GEMFILES = [
  "tools/ruby-gems/idlc/Gemfile",
  "tools/ruby-gems/udb_helpers/Gemfile",
  "tools/ruby-gems/udb/Gemfile",
  "tools/ruby-gems/udb-gen/Gemfile",
  "Gemfile"
].freeze

def read_version(version_file)
  content = File.read(UDB_ROOT / version_file)
  if content =~ /["'](\d+\.\d+\.\d+)["']/
    $1
  else
    raise "Could not extract version from #{version_file}"
  end
end

def write_version(version_file, new_version)
  path = UDB_ROOT / version_file
  content = File.read(path)
  updated = content.gsub(/["']\d+\.\d+\.\d+["']/, "\"#{new_version}\"")
  File.write(path, updated)
end

def bump_patch(version)
  parts = version.split(".")
  parts[2] = (parts[2].to_i + 1).to_s
  parts.join(".")
end

def get_changed_files(base_ref)
  cmd = "git diff --name-only #{base_ref}...HEAD 2>&1"
  output = `#{cmd}`
  if $?.exitstatus != 0
    warn "Initial git diff failed: #{output.strip}"
    # Try fetching the base branch and retry
    system("git fetch --no-tags --prune --no-recurse-submodules origin main 2>/dev/null")
    output = `#{cmd}`
    if $?.exitstatus != 0
      warn "Retry git diff failed: #{output.strip}"
      warn "Skipping version auto-increment (git history unavailable)"
      return nil
    end
  end
  output.lines.map(&:strip)
end

def needs_bump?(gem_config, changed_files, base_ref)
  gem_dir = gem_config[:dir]
  version_file = gem_config[:version_file]
  additional_dirs = gem_config[:additional_dirs] || []

  gem_files_changed = changed_files.any? { |f| f.start_with?(gem_dir) }
  additional_files_changed = additional_dirs.any? do |dir|
    changed_files.any? { |f| f.start_with?(dir) }
  end

  return false unless gem_files_changed || additional_files_changed

  # Check if version file itself changed
  return false if changed_files.include?(version_file)

  # Version file not in diff — check if version actually differs from base
  current_version = read_version(version_file)
  base_content = `git show #{base_ref}:#{version_file} 2>&1`
  if $?.exitstatus != 0
    # New gem — no base version, no bump needed
    return false
  end

  base_version = nil
  if base_content =~ /["'](\d+\.\d+\.\d+)["']/
    base_version = $1
  end

  # If version already differs (e.g., find-replace), no bump needed
  current_version == base_version
end

def compute_needs_bump_set(changed_files, base_ref)
  needs_bump = Set.new

  GEMS.each do |gem_config|
    if needs_bump?(gem_config, changed_files, base_ref)
      needs_bump.add(gem_config[:name])
    end
  end

  # Cascade: any gem that depends on a bumped gem also needs a bump
  # Iterate until no new gems are added
  loop do
    added = Set.new
    needs_bump.each do |gem_name|
      (DEPENDENTS[gem_name] || []).each do |dependent|
        added.add(dependent) unless needs_bump.include?(dependent)
      end
    end
    break if added.empty?
    needs_bump.merge(added)
  end

  needs_bump
end

def do_version_bumps(needs_bump_set)
  GEMS.each do |gem_config|
    next unless needs_bump_set.include?(gem_config[:name])
    current = read_version(gem_config[:version_file])
    new_version = bump_patch(current)
    write_version(gem_config[:version_file], new_version)
    puts "  Bumped #{gem_config[:name]}: #{current} → #{new_version}"
  end
end

def update_gemspec_pins
  GEMSPEC_PINS.each do |pin|
    gemspec_path = UDB_ROOT / pin[:gemspec]
    dep_name = pin[:dep_name]
    version = read_version(GEMS.find { |g| g[:name] == pin[:version_gem] }[:version_file])

    content = File.read(gemspec_path)
    # Match: s.add_dependency "dep_name" (no version) or s.add_dependency "dep_name", "= X.Y.Z"
    pattern = /^(\s*s\.add_dependency\s+["']#{Regexp.escape(dep_name)}["'])(?:\s*,\s*["'][^"']*["'])?/
    new_line = "\\1, \"= #{version}\""
    updated = content.gsub(pattern, new_line)

    if updated != content
      File.write(gemspec_path, updated)
      puts "  Pinned #{dep_name} to = #{version} in #{pin[:gemspec]}"
    else
      puts "  #{dep_name} already pinned to = #{version} in #{pin[:gemspec]}"
    end
  end
end

# Update the version strings for local gem dependencies in the PATH sections
# of a Gemfile.lock, without running `bundle lock` (which would drop platform
# variants resolved on a different architecture).
#
# Only the dependency lines inside PATH specs blocks are rewritten, e.g.:
#   idlc (= 0.1.1)   →   idlc (= 0.1.2)
#   idlc              →   idlc (= 0.1.2)
# The gem's own version line (the first line of the spec) is left alone.
def update_lockfiles
  # Build a map of dep_name → pinned version from GEMSPEC_PINS
  pin_map = {}
  GEMSPEC_PINS.each do |pin|
    version = read_version(GEMS.find { |g| g[:name] == pin[:version_gem] }[:version_file])
    pin_map[pin[:dep_name]] = version
  end

  GEMFILES.each do |gemfile_rel|
    lockfile_path = UDB_ROOT / "#{gemfile_rel}.lock"

    unless lockfile_path.exist?
      puts "  Skipping #{gemfile_rel}.lock (not found)"
      next
    end

    content = File.read(lockfile_path)
    updated = content.dup

    pin_map.each do |dep_name, version|
      # Match dependency lines inside PATH specs: lines like
      #   "      dep_name" or "      dep_name (= X.Y.Z)" or "      dep_name (X.Y.Z)"
      # but NOT the gem's own name line (which has exactly 4 spaces of indent).
      # Dependency lines have 6 spaces of indent.
      pattern = /^(      #{Regexp.escape(dep_name)})(?:\s*\([^)]*\))?$/
      updated = updated.gsub(pattern, "\\1 (= #{version})")
    end

    if updated != content
      File.write(lockfile_path, updated)
      puts "  Updated #{gemfile_rel}.lock"
    else
      puts "  #{gemfile_rel}.lock already up to date"
    end
  end
end

def sha256_files(file_list)
  file_list.each_with_object({}) do |rel_path, hash|
    path = UDB_ROOT / rel_path
    hash[rel_path] = path.exist? ? Digest::SHA256.file(path).hexdigest : nil
  end
end

def all_tracked_files
  version_files = GEMS.map { |g| g[:version_file] }
  gemspec_files = GEMSPEC_PINS.map { |p| p[:gemspec] }.uniq
  lockfiles = GEMFILES.map { |f| "#{f}.lock" }
  version_files + gemspec_files + lockfiles
end

def run_check_mode(base_ref)
  puts "Checking gem version bumps..."
  puts "Base ref: #{base_ref}"
  puts

  changed_files = get_changed_files(base_ref)
  if changed_files.nil?
    puts "No git history available; skipping check."
    exit 0
  end

  if changed_files.empty?
    puts "No files changed."
    exit 0
  end

  failures = []

  GEMS.each do |gem_config|
    gem_name = gem_config[:name]
    if needs_bump?(gem_config, changed_files, base_ref)
      current_version = read_version(gem_config[:version_file])
      puts "✗ #{gem_name}: Files changed but version not bumped (current: #{current_version})"
      failures << gem_name
    else
      # Determine why it's OK
      gem_dir = gem_config[:dir]
      additional_dirs = gem_config[:additional_dirs] || []
      gem_files_changed = changed_files.any? { |f| f.start_with?(gem_dir) }
      additional_files_changed = additional_dirs.any? { |dir| changed_files.any? { |f| f.start_with?(dir) } }

      if gem_files_changed || additional_files_changed
        current_version = read_version(gem_config[:version_file])
        puts "✓ #{gem_name}: Version bumped to #{current_version}"
      else
        puts "✓ #{gem_name}: No changes"
      end
    end
  end

  if failures.any?
    puts
    puts "ERROR: The following gems have source changes without version bumps:"
    failures.each { |name| puts "  - #{name}" }
    puts
    puts "Please bump the version in the version.rb file for each modified gem."
    exit 1
  end

  puts
  puts "All gem version checks passed!"
  exit 0
end

# --- Main ---

options = { fail_on_change: false, check: false, base_ref: "origin/main" }

OptionParser.new do |opts|
  opts.on("--fail-on-change", "Exit 1 if any file changed") do
    options[:fail_on_change] = true
  end
  opts.on("--check", "Only check for version-bump issues, no writes") do
    options[:check] = true
  end
  opts.on("--base-ref REF", "Git ref to compare against (default: origin/main)") do |ref|
    options[:base_ref] = ref
  end
end.parse!

if options[:check]
  run_check_mode(options[:base_ref])
  # run_check_mode exits internally
end

# Normal / --fail-on-change mode
tracked = all_tracked_files
sha_before = options[:fail_on_change] ? sha256_files(tracked) : nil

# Step A: auto-increment versions for changed gems (with cascade)
puts "Step A: Checking for gems that need version bumps..."
changed_files = get_changed_files(options[:base_ref])
if changed_files.nil?
  puts "  Skipping (git history unavailable)"
else
  needs_bump = compute_needs_bump_set(changed_files, options[:base_ref])
  if needs_bump.empty?
    puts "  No version bumps needed"
  else
    do_version_bumps(needs_bump)
  end
end

# Step B: update inter-gem dependency pins in gemspecs
puts "Step B: Updating inter-gem dependency pins in gemspecs..."
update_gemspec_pins

# Step C: update version pins in Gemfile.lock files
puts "Step C: Updating inter-gem version pins in Gemfile.lock files..."
update_lockfiles

if options[:fail_on_change]
  sha_after = sha256_files(tracked)
  changed = tracked.select { |f| sha_before[f] != sha_after[f] }
  if changed.any?
    puts
    puts "ERROR: The following files changed; run './bin/chore gen gem-versions' to update:"
    changed.each { |f| puts "  #{f}" }
    exit 1
  end
end

puts
puts "Done."
