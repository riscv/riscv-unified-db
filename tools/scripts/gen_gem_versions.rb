#!/usr/bin/env ruby
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

# Script to:
#   Step B: Update inter-gem dependency pins in gemspecs to exact current versions
#   Step C: Regenerate Gemfile.lock files (sync only, no --update)
#
#   With --auto-bump:
#   Step A0: Bring any version files that lag behind the base ref forward
#   Step A:  Auto-increment versions for gems whose source changed without a bump (with cascade)
#
# Usage:
#   gen_gem_versions.rb [--auto-bump] [--fail-on-change] [--base-ref <ref>]
#
#   --auto-bump       Detect source changes and auto-increment gem versions (Steps A0+A)
#   --fail-on-change  Exit 1 if any file changed (for CI drift detection)
#   --base-ref <ref>  Git ref to compare against (default: $GITHUB_BASE_REF or origin/main)

require "digest"
require "optparse"
require "pathname"
require "rubygems"
require "set"

UDB_ROOT = Pathname.new(__FILE__).dirname.parent.parent.realpath

# Parse gem metadata by loading gemspecs via Gem::Specification.
# Returns a hash with keys :gems, :dependents, :gemspec_pins, :gemfiles.
#
# Discovers gem directories by looking for *.gemspec files under tools/ruby-gems/.
def parse_gem_metadata(udb_root)
  # Discover gem dirs via gemspec files and load each gemspec using the
  # official Gem::Specification API.
  # Load each spec from within its own directory so that Dir.glob patterns in
  # the spec's `files` list (e.g. "lib/**/*.rb") resolve correctly.
  spec_entries = Dir.glob("#{udb_root}/tools/ruby-gems/*/*.gemspec").filter_map do |gemspec_path|
    dir = Pathname.new(gemspec_path).dirname

    spec = Dir.chdir(dir) { Gem::Specification.load(gemspec_path) }
    next unless spec

    [spec, Pathname.new(gemspec_path)]
  end

  local_names = spec_entries.map { |spec, _| spec.name }.to_set

  gems = spec_entries.map do |spec, gemspec_path|
    rel_dir = gemspec_path.dirname.relative_path_from(udb_root).to_s
    gemspec_rel = gemspec_path.relative_path_from(udb_root).to_s
    version_file = "#{rel_dir}/lib/#{spec.name}/version.rb"
    additional_dirs = (gemspec_path.dirname / "spec").directory? ? ["#{rel_dir}/spec"] : []
    # Build the set of repo-relative paths that count as gem source.
    # spec.files was resolved in the gem dir (see spec_entries loading above).
    source_files = spec.files
                      .map { |f| "#{rel_dir}/#{f}" }
                      .to_set
    source_files << gemspec_rel
    {
      name: spec.name,
      dir: rel_dir,
      version_file:,
      additional_dirs:,
      source_files: source_files.freeze,
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

  # Topological sort (Kahn's algorithm) for dependency ordering.
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
  gemfiles = ["Gemfile"] # single root Gemfile

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
  # Always fetch so origin/main is fresh locally (CI always has a fresh checkout).
  # Silent: if the network is unavailable the cached ref is used and the diff below
  # will still succeed as long as origin/main was fetched at some point before.
  system("git fetch --no-tags --prune --no-recurse-submodules origin main 2>/dev/null")

  cmd = "git diff --name-only #{base_ref}...HEAD 2>&1"
  output = `#{cmd}`
  if $?.exitstatus != 0
    warn "git diff failed: #{output.strip}"
    warn "Skipping version auto-increment (git history unavailable)"
    return nil
  end
  output.lines.map(&:strip)
end

def needs_bump?(gem_config, changed_files, base_ref)
  version_file = gem_config[:version_file]
  source_files = gem_config[:source_files]
  additional_dirs = gem_config[:additional_dirs] || []

  gem_files_changed = changed_files.any? { |f| source_files.include?(f) }
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

  # A bump is needed unless the branch version is already strictly ahead of base.
  Gem::Version.new(current_version) <= Gem::Version.new(base_version)
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

def do_version_bumps(needs_bump_set, base_ref)
  GEMS.each do |gem_config|
    next unless needs_bump_set.include?(gem_config[:name])
    current = read_version(gem_config[:version_file])
    base_content = `git show #{base_ref}:#{gem_config[:version_file]} 2>&1`
    base = ($?.exitstatus == 0 && base_content =~ /["'](\d+\.\d+\.\d+)["']/) ? $1 : current
    start_from = Gem::Version.new(current) >= Gem::Version.new(base) ? current : base
    new_version = bump_patch(start_from)
    write_version(gem_config[:version_file], new_version)
    puts "  Bumped #{gem_config[:name]}: #{current} → #{new_version}"
  end
end

def bring_versions_forward(base_ref)
  GEMS.each do |gem_config|
    current = read_version(gem_config[:version_file])
    base_content = `git show #{base_ref}:#{gem_config[:version_file]} 2>&1`
    next unless $?.exitstatus == 0
    next unless base_content =~ /["'](\d+\.\d+\.\d+)["']/
    base = $1
    next unless Gem::Version.new(current) < Gem::Version.new(base)
    write_version(gem_config[:version_file], base)
    puts "  Brought #{gem_config[:name]} forward: #{current} → #{base}"
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

# Update the version strings for local gems in the PATH sections of a
# Gemfile.lock, without running `bundle lock` (which would drop platform
# variants resolved on a different architecture).
#
# Two classes of lines are rewritten inside each PATH specs: block:
#
# 1. The gem's own PATH spec header line (4-space indent), e.g.:
#      udb_helpers (0.1.1)   →   udb_helpers (0.1.2)
#    This is updated to match the current version from the gem's version.rb.
#
# 2. Inter-gem dependency lines (6-space indent), e.g.:
#      idlc (= 0.1.1)   →   idlc (= 0.1.2)
#      idlc              →   idlc (= 0.1.2)
#    These are updated to the pinned version from GEMSPEC_PINS.
def update_lockfiles
  # Build a map of gem_name → current version for ALL local gems.
  # Used to update the 4-space-indented PATH spec header lines.
  gem_version_map = {}
  GEMS.each do |gem_config|
    gem_version_map[gem_config[:name]] = read_version(gem_config[:version_file])
  end

  # Build a map of dep_name → pinned version from GEMSPEC_PINS.
  # Used to update the 6-space-indented inter-gem dependency lines.
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
    lines = content.lines

    in_path_section = false
    in_specs_block = false
    path_spec_header_seen = false

    lines.map! do |line|
      # Detect start of a PATH section (top-level "PATH" line).
      if line == "PATH\n" || line == "PATH"
        in_path_section = true
        in_specs_block = false
        path_spec_header_seen = false
        next line
      end

      # Any new top-level section (non-indented, non-empty line) ends the PATH section.
      if line.match?(/^\S/) && line.strip != ""
        in_path_section = false
        in_specs_block = false
        path_spec_header_seen = false
        next line
      end

      # Inside PATH, detect the "  specs:" stanza.
      if in_path_section && line.match?(/^  specs:/)
        in_specs_block = true
        path_spec_header_seen = false
        next line
      end

      if in_path_section && in_specs_block
        # The first 4-space-indented gem line after "  specs:" is the PATH spec
        # header — the gem's own name and version, e.g. "    udb_helpers (0.1.1)".
        # Update it to the current version from version.rb.
        if !path_spec_header_seen && line.match?(/^    \S/)
          path_spec_header_seen = true
          gem_version_map.each do |gem_name, version|
            header_pattern = /^(    #{Regexp.escape(gem_name)})\s*\(\d+\.\d+\.\d+\)/
            if line.match?(header_pattern)
              newline_char = line.end_with?("\n") ? "\n" : ""
              line = "    #{gem_name} (#{version})#{newline_char}"
              break
            end
          end
          next line
        end

        # 6-space-indented lines are inter-gem dependency lines.
        # Update pinned local gem dependencies to their current versions.
        pin_map.each do |dep_name, version|
          dep_pattern = /^(      #{Regexp.escape(dep_name)})(?:\s*\([^)]*\))?$/
          if line.match?(dep_pattern)
            newline_char = line.end_with?("\n") ? "\n" : ""
            line = "      #{dep_name} (= #{version})#{newline_char}"
            break
          end
        end
      end

      line
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

# --- Main ---

def default_base_ref
  if (base = ENV["GITHUB_BASE_REF"])&.match?(/\S/)
    "origin/#{base}"
  else
    "origin/main"
  end
end

if __FILE__ == $PROGRAM_NAME
  options = { fail_on_change: false, auto_bump: false, base_ref: default_base_ref }

  OptionParser.new do |opts|
    opts.on("--auto-bump", "Auto-increment versions for gems with source changes (Steps A0+A)") do
      options[:auto_bump] = true
    end
    opts.on("--fail-on-change", "Exit 1 if any file changed") do
      options[:fail_on_change] = true
    end
    opts.on("--base-ref REF", "Git ref to compare against (default: $GITHUB_BASE_REF or origin/main)") do |ref|
      options[:base_ref] = ref
    end
  end.parse!

  # Normal / --fail-on-change mode
  tracked = all_tracked_files
  sha_before = options[:fail_on_change] ? sha256_files(tracked) : nil

  if options[:auto_bump]
    # Step A0: bring any version files that are behind the base ref forward
    puts "Step A0: Bringing stale version files forward to base..."
    bring_versions_forward(options[:base_ref])

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
        do_version_bumps(needs_bump, options[:base_ref])
      end
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
