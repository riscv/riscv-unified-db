# typed: false
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

# This extconf.rb runs at `gem install` time to download the must binary
# from the GitHub release for the current platform. It requires no external
# tools — only Ruby's built-in Net::HTTP.

require "rbconfig"
require "fileutils"
require "net/http"
require "uri"

# Load MUST_VERSION from the sibling lib file without requiring the full gem
must_version_rb = File.expand_path("../../lib/udb/must_version.rb", __dir__)
load must_version_rb

MUST_VERSION = Udb::MUST_VERSION

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
dest_dir  = File.join(xdg_cache, "udb", "must", MUST_VERSION, cpu)
dest_file = File.join(dest_dir, "must")

unless File.exist?(dest_file)
  FileUtils.mkdir_p(dest_dir)

  asset_name = "must-#{cpu}"
  url_str = "https://github.com/#{GITHUB_REPO}/releases/download/#{MUST_VERSION}/#{asset_name}"

  $stderr.puts "Downloading must (#{MUST_VERSION}, #{cpu}) from GitHub releases..."
  $stderr.puts "  URL: #{url_str}"

  def download_with_redirects(url_str, limit = 10)
    raise "Too many HTTP redirects" if limit.zero?

    uri = URI.parse(url_str)
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = (uri.scheme == "https")
    http.open_timeout = 30
    http.read_timeout = 120

    request = Net::HTTP::Get.new(uri.request_uri)
    request["User-Agent"] = "udb-gem/must-installer"

    response = http.request(request)

    case response
    when Net::HTTPSuccess
      response.body
    when Net::HTTPRedirection
      download_with_redirects(response["location"], limit - 1)
    else
      raise "Failed to download #{url_str}\n" \
            "HTTP #{response.code} #{response.message}"
    end
  end

  body = download_with_redirects(url_str)
  File.binwrite(dest_file, body)
  File.chmod(0o755, dest_file)
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
