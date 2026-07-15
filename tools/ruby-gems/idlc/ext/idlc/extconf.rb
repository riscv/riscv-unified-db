# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

# Provisions libtree-sitter-idl for the source (non-platform) gem at install
# time. Used only by the source gem variant; platform gems bundle a pre-compiled
# .so directly and never run this file.
#
# Strategy (mirrors the udb gem's z3/espresso/eqntott/must download approach in
# ext/udb_download/extconf.rb):
#
#   1. Try to download a prebuilt grammar binary for this OS+CPU from the
#      project's GitHub releases and verify its checksum. No C compiler needed.
#   2. Fall back to compiling parser.c + scanner.c from the bundled sources when
#      the download is unavailable (unsupported platform, offline, 404, checksum
#      mismatch) or when IDLC_BUILD_FROM_SOURCE is set in the environment.
#
# The download path still needs `make` (the gem-install infrastructure runs the
# Makefile we write below) but not a compiler; the source path needs both.

require "digest"
require "fileutils"
require "net/http"
require "rbconfig"
require "uri"

GITHUB_REPO = "riscv/riscv-unified-db"

SRC_DIR = __dir__
LIB_DIR = File.expand_path("../../lib/idlc", SRC_DIR)
# Always emit ".so": the gemspec and Ruby loaders key off this name on every
# platform. On macOS the artifact is a Mach-O dynamic library named .so, which
# dlopen (and ruby_tree_sitter) load regardless of extension.
SO_DEST = File.join(LIB_DIR, "libtree-sitter-idl.so")

FileUtils.mkdir_p(LIB_DIR)

# Follow redirects (GitHub release assets redirect to a CDN).
def http_get(url_str, limit: 10)
  raise "Too many HTTP redirects" if limit.zero?

  uri = URI.parse(url_str)
  http = Net::HTTP.new(uri.host, uri.port)
  http.use_ssl = (uri.scheme == "https")
  http.open_timeout = 30
  http.read_timeout = 120

  request = Net::HTTP::Get.new(uri.request_uri)
  request["User-Agent"] = "idlc-gem/installer"

  response = http.request(request)
  case response
  when Net::HTTPSuccess
    response.body
  when Net::HTTPRedirection
    http_get(response["location"], limit: limit - 1)
  else
    raise "HTTP #{response.code} #{response.message} for #{url_str}"
  end
end

# Attempts to download and verify a prebuilt grammar binary into SO_DEST.
# Returns true on success, false if a prebuilt binary could not be provisioned
# (caller falls back to compiling from source).
def download_prebuilt
  version_file = File.join(SRC_DIR, "TS_IDL_VERSION")
  return false unless File.exist?(version_file)

  version = File.read(version_file).strip
  return false if version.empty?

  os, ext =
    case RbConfig::CONFIG["host_os"]
    when /darwin|mac os/ then ["macos", "dylib"]
    when /linux/         then ["linux", "so"]
    else return false
    end
  cpu =
    case RbConfig::CONFIG["host_cpu"]
    when /arm64|aarch64/ then "arm64"
    when /x86_64|x64/    then "x64"
    else return false
    end

  tag   = "tree-sitter-idl-#{version}"
  asset = "libtree-sitter-idl-#{os}-#{cpu}.#{ext}"
  base  = "https://github.com/#{GITHUB_REPO}/releases/download/#{tag}"

  $stderr.puts "Downloading prebuilt IDL grammar (#{tag}, #{os}-#{cpu})..."
  $stderr.puts "  URL: #{base}/#{asset}"
  body = http_get("#{base}/#{asset}")

  checksum_body = http_get("#{base}/#{asset}.checksum")
  expected = checksum_body.strip.split(":")[1]
  actual   = Digest::SHA256.hexdigest(body)
  if expected != actual
    $stderr.puts "  Checksum mismatch (expected #{expected}, got #{actual})."
    return false
  end

  File.binwrite(SO_DEST, body)
  $stderr.puts "  Saved to #{SO_DEST} (checksum verified)."
  true
rescue StandardError => e
  $stderr.puts "  Prebuilt grammar download failed: #{e.message}"
  false
end

# Compiles parser.c + scanner.c from the bundled sources.
def compile_from_source
  cc = RbConfig::CONFIG["CC"]
  cc = "cc" if cc.nil? || cc.empty?
  # platform-appropriate flag for producing a loadable shared object
  shared_flag = RbConfig::CONFIG["host_os"] =~ /darwin/ ? "-dynamiclib" : "-shared"

  cmd = "#{cc} #{shared_flag} -fPIC -std=c11 -I#{SRC_DIR} -o #{SO_DEST} " \
        "#{SRC_DIR}/parser.c #{SRC_DIR}/scanner.c"

  return if system(cmd)

  raise "Failed to provision libtree-sitter-idl: no prebuilt binary for this " \
        "platform and source compilation failed — ensure a C compiler is installed."
end

provisioned = false
if ENV["IDLC_BUILD_FROM_SOURCE"]
  $stderr.puts "IDLC_BUILD_FROM_SOURCE set — building libtree-sitter-idl from source..."
else
  provisioned = download_prebuilt
end

# Fall back to (or, when forced, use) the bundled C sources.
compile_from_source unless provisioned

# Write the no-op Makefile expected by the gem install infrastructure.
File.write(File.join(SRC_DIR, "Makefile"), "all:\n\ninstall:\n\nclean:\n")
