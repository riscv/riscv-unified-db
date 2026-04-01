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
require "rubygems"
require "set"

UDB_ROOT = Pathname.new(__FILE__).dirname.parent.parent.realpath

# Parse gem metadata by loading gemspecs via Gem::Specification.
# Returns a hash with keys :gems, :dependents, :gemspec_pins, :gemfiles.
#
# Only gem directories that have BOTH a Gemfile AND a *.gemspec are included
# (this naturally excludes idl_highlighter which has no Gemfile).
def parse_gem_metadata(udb_root)
  # Discover gem dirs that have both a Gemfile and a gemspec, and load each
  # gemspec using the official Gem::Specification API.
  spec_entries = Dir.glob("#{udb_root}/tools/ruby-gems/*/Gemfile").filter_map do |gf|
    dir = Pathname.new(gf).dirname
    gemspec_path = Dir.glob("#{dir}/*.gemspec").first
    next unless gemspec_path

    spec = Gem::Specification.load(gemspec_path)
    next unless spec

    [spec, Pathname.new(gemspec_path)]
  end

  local_names = spec_entries.map { |spec, _| spec.name }.to_set

  gems = spec_entries.map do |spec, gemspec_path|
    rel_dir = gemspec_path.dirname.relative_path_from(udb_root).to_s
    gemspec_rel = gemspec_path.relative_path_from(udb_root).to_s
    version_file = "#{rel_dir}/lib/#{spec.name}/version.rb"
    additional_dirs = (gemspec_path.dirname / "spec").directory? ? ["spec"] : []
    {
      name: spec.name,
      dir: rel_dir,
      version_file:,
      additional_dirs:,
      gemspec_path: gemspec_rel
    }
  end

  # Build forward dependency graph from runtime_dependencies reported by each
  # gemspec: gem_name -> [local gem names it depends on].
  deps = gems.each_with_object({}) { |g, h| h[g[:name]] = [] }
  gemspec_pins = []

  spec_entries.each do |spec, _|
    gem_entry = gems.find { |g| g[:name] == spec.name }
    spec.runtime_dependencies.each do |dep|
      next unless local_names.include?(dep.name)

      deps[spec.name] << dep.name
      gemspec_pins << { gemspec: gem_entry[:gemspec_path], dep_name: dep.name, version_gem: dep.name }
    end
  end

  # Invert deps to get DEPENDENTS (dep -> [gems that depend on it])
  dependents = gems.each_with_object(Hash.new { |h, k| h[k] = [] }) { |g, h| h[g[:name]] }
  deps.each do |gem_name, dep_list|
    dep_list.each { |dep| dependents[dep] << gem_name }
  end

  # Topological sort (Kahn's algorithm) for GEMFILES order: leaves first.
  in_degree = gems.each_with_object({}) { |g, h| h[g[:name]] = deps[g[:name]].size }
  queue = gems.map { |g| g[:name] }.select { |n| in_degree[n] == 0 }.sort
  ordered_names = []
  until queue.empty?
    n = queue.shift
    ordered_names << n
    dependents[n].sort.each do |dep|
      in_degree[dep] -= 1
      queue << dep if in_degree[dep] == 0
    end
  end
  gemfiles = ordered_names.map { |n| gems.find { |g| g[:name] == n }[:dir] + "/Gemfile" }
  gemfiles << "Gemfile" # root Gemfile always last

  {
    gems: gems.map { |g| g.reject { |k, _| k == :gemspec_path } }.freeze,
    dependents: dependents.transform_values(&:freeze).freeze,
    gemspec_pins: gemspec_pins.freeze,
    gemfiles: gemfiles.freeze
  }
end

_metadata = parse_gem_metadata(UDB_ROOT)

# Gem metadata: name, source dir, version file, additional watched dirs
GEMS = _metadata[:gems]

# Dependency graph: gem name → list of gem names that depend on it (reverse deps)
DEPENDENTS = _metadata[:dependents]

# Gemspec files that have inter-gem dependencies to pin
GEMSPEC_PINS = _metadata[:gemspec_pins]

# Gemfiles to re-lock, in dependency order
GEMFILES = _metadata[:gemfiles]

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
      warn "git diff failed twice; falling back to git ls-files to determine files"
      ls_output = `git ls-files 2>&1`
      if $?.exitstatus != 0
        warn "git ls-files also failed: #{ls_output.strip}"
        abort "Unable to determine changed files from git; aborting version generation"
      end
      return ls_output.lines.map(&:strip)
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
      raise "Expected lockfile #{lockfile_path} to exist. " \
            "Generate it with `bundle lock --gemfile #{UDB_ROOT / gemfile_rel}`."
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
    lines = content.lines

    # Restrict rewrites to dependency lines inside PATH specs blocks.
    pin_map.each do |dep_name, version|
      pattern = /^(      #{Regexp.escape(dep_name)})(?:\s*\([^)]*\))?$/
      in_path_section = false
      in_specs_block = false

      lines.map!.with_index do |line, idx|
        # Detect start of a PATH section (top-level "PATH" line).
        if line == "PATH\n" || line == "PATH"
          in_path_section = true
          in_specs_block = false
          line
        # Any new top-level section (non-indented line) other than PATH ends the PATH section.
        elsif line.match?(/^\S/) && !line.start_with?("PATH")
          in_path_section = false
          in_specs_block = false
          line
        # Inside PATH, detect the specs: stanza.
        elsif in_path_section && line.match?(/^  specs:/)
          in_specs_block = true
          line
        else
          if in_path_section && in_specs_block && line.match?(pattern)
            # Preserve the original indentation and gem name (capture group 1),
            # and overwrite any version constraint with the pinned version.
            prefix = Regexp.last_match(1)
            # Keep the original line ending (if any).
            newline = line.end_with?("\n") ? "\n" : ""
            "#{prefix} (= #{version})#{newline}"
          else
            line
          end
        end
      end
    end

    updated = lines.join
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

if __FILE__ == $PROGRAM_NAME
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
end
