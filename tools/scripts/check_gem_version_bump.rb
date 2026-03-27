#!/usr/bin/env ruby
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

# Script to check if a gem's source files have changed without a version bump.
# Used in CI to enforce version bumps when gems are modified.

require "pathname"

# Gem configurations: name, source directory, and version file
# additional_dirs: optional array of directories to monitor in addition to the gem directory
GEMS = [
  {
    name: "udb",
    dir: "tools/ruby-gems/udb",
    version_file: "tools/ruby-gems/udb/lib/udb/version.rb",
    version_method: "Udb.version",
    additional_dirs: ["spec"]
  },
  {
    name: "idlc",
    dir: "tools/ruby-gems/idlc",
    version_file: "tools/ruby-gems/idlc/lib/idlc/version.rb",
    version_method: "Idl::Compiler.version"
  },
  {
    name: "udb_helpers",
    dir: "tools/ruby-gems/udb_helpers",
    version_file: "tools/ruby-gems/udb_helpers/lib/udb_helpers/version.rb",
    version_method: "Udb::Helpers.version"
  },
  {
    name: "udb-gen",
    dir: "tools/ruby-gems/udb-gen",
    version_file: "tools/ruby-gems/udb-gen/lib/udb-gen/version.rb",
    version_method: "UdbGen.version",
    additional_dirs: ["spec"]
  }
].freeze

def get_changed_files(base_ref)
  # Get list of changed files compared to base branch. Retry fetch if needed
  cmd = "git diff --name-only #{base_ref}...HEAD 2>&1"
  output = `#{cmd}`
  if $?.exitstatus != 0
    warn "Initial git diff failed: #{output}"
    # Try fetching the base branch and retry
    system("git fetch --no-tags --prune --no-recurse-submodules origin main")
    output = `#{cmd}`
    if $?.exitstatus != 0
      warn "Retry git diff failed: #{output}"
      # Fallback: list all tracked files to avoid false negatives in CI
      files = `git ls-files 2>/dev/null`.lines.map(&:strip)
      warn "Falling back to listing all tracked files (#{files.size} files)"
      return files
    end
  end
  output.lines.map(&:strip)
end

def get_gem_version(version_file)
  # Read version from the version file
  content = File.read(version_file)
  # Extract version string using regex (matches x.y.z format)
  if content =~ /["'](\d+\.\d+\.\d+)["']/
    $1
  else
    nil
  end
end

def check_gem(gem_config, changed_files, base_ref)
  gem_name = gem_config[:name]
  gem_dir = gem_config[:dir]
  version_file = gem_config[:version_file]
  additional_dirs = gem_config[:additional_dirs] || []

  # Check if any files in the gem directory have changed
  gem_files_changed = changed_files.any? { |f| f.start_with?(gem_dir) }

  # Also check additional directories if specified
  additional_files_changed = additional_dirs.any? do |dir|
    changed_files.any? { |f| f.start_with?(dir) }
  end

  return :no_changes unless gem_files_changed || additional_files_changed

  # Check if the version file itself changed
  version_file_changed = changed_files.include?(version_file)

  if version_file_changed
    # Version file changed, so version was bumped - OK
    return :version_bumped
  end

  # Files changed but version didn't - check if version is actually different
  # (in case version was bumped in a different way, like find-replace)
  current_version = get_gem_version(version_file)
  base_version_content = `git show #{base_ref}:#{version_file} 2>&1`

  if $?.exitstatus != 0
    # File might not exist in base branch (new gem)
    return :new_gem
  end

  base_version = nil
  if base_version_content =~ /["'](\d+\.\d+\.\d+)["']/
    base_version = $1
  end

  if current_version != base_version
    # Version changed but file wasn't in git diff (shouldn't normally happen)
    return :version_bumped
  end

  # Files changed but version didn't - FAIL
  return :version_not_bumped
end

def main
  # Get base branch from argument or default to origin/main
  base_ref = ARGV[0] || "origin/main"

  # Ensure we have the latest base branch
  system("git fetch origin main:refs/remotes/origin/main 2>/dev/null")

  changed_files = get_changed_files(base_ref)

  if changed_files.empty?
    puts "No files changed."
    exit 0
  end

  puts "Checking gem version bumps..."
  puts "Base ref: #{base_ref}"
  puts

  failures = []

  GEMS.each do |gem_config|
    gem_name = gem_config[:name]
    status = check_gem(gem_config, changed_files, base_ref)

    case status
    when :no_changes
      puts "✓ #{gem_name}: No changes"
    when :version_bumped
      current_version = get_gem_version(gem_config[:version_file])
      puts "✓ #{gem_name}: Version bumped to #{current_version}"
    when :new_gem
      puts "✓ #{gem_name}: New gem (no base version)"
    when :version_not_bumped
      current_version = get_gem_version(gem_config[:version_file])
      puts "✗ #{gem_name}: Files changed but version not bumped (current: #{current_version})"
      failures << gem_name
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

main if __FILE__ == $PROGRAM_NAME
