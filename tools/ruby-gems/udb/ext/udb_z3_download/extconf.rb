# typed: false
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

# This extconf.rb runs at `gem install` time to download the Z3 shared library
# from the GitHub release for the current platform. It requires no external
# tools — only Ruby's built-in Net::HTTP.

require "rbconfig"
require "fileutils"
require "net/http"
require "uri"

# Check that required build tools are present
def find_executable(name)
  ENV.fetch("PATH", "").split(File::PATH_SEPARATOR).any? do |dir|
    File.executable?(File.join(dir, name))
  end
end

abort "ERROR: 'make' is not installed or not on PATH. Please install make before continuing." \
  unless find_executable("make")

# Load Z3_VERSION from the sibling lib file without requiring the full gem
z3_version_rb = File.expand_path("../../lib/udb/z3_version.rb", __dir__)
load z3_version_rb

Z3_VERSION = Udb::Z3_VERSION

GITHUB_REPO = "riscv/riscv-unified-db"

cpu =
  case RbConfig::CONFIG["host_cpu"]
  when /arm64|aarch64/
    "arm64"
  when /x86_64|x64/
    "x64"
  else
    raise "Unsupported host cpu: #{RbConfig::CONFIG["host_cpu"]}. " \
          "Only x64 and arm64 are supported."
  end

xdg_cache = ENV.fetch("XDG_CACHE_HOME", File.join(Dir.home, ".cache"))
dest_dir  = File.join(xdg_cache, "udb", "z3", Z3_VERSION, cpu)
dest_file = File.join(dest_dir, "libz3.so")

unless File.exist?(dest_file)
  FileUtils.mkdir_p(dest_dir)

  asset_name = "libz3-#{cpu}.so"
  url_str = "https://github.com/#{GITHUB_REPO}/releases/download/#{Z3_VERSION}/#{asset_name}"

  $stderr.puts "Downloading Z3 (#{Z3_VERSION}, #{cpu}) from GitHub releases..."
  $stderr.puts "  URL: #{url_str}"

  # Follow redirects (GitHub releases use a CDN redirect)
  def download_with_redirects(url_str, limit = 10)
    raise "Too many HTTP redirects" if limit.zero?

    uri = URI.parse(url_str)
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = (uri.scheme == "https")
    http.open_timeout = 30
    http.read_timeout = 120

    request = Net::HTTP::Get.new(uri.request_uri)
    request["User-Agent"] = "udb-gem/z3-installer"

    response = http.request(request)

    case response
    when Net::HTTPSuccess
      response.body
    when Net::HTTPRedirection
      download_with_redirects(response["location"], limit - 1)
    else
      raise "Failed to download #{url_str}\n" \
            "HTTP #{response.code} #{response.message}\n" \
            "If you are a maintainer, run: bin/chore update z3"
    end
  end

  body = download_with_redirects(url_str)
  File.binwrite(dest_file, body)
  $stderr.puts "  Saved to #{dest_file}"
end

# Write a no-op Makefile — we have no C extension to compile
File.write("Makefile", <<~MAKEFILE)
  all:
  \t@true
  install:
  \t@true
  clean:
  \t@true
MAKEFILE
