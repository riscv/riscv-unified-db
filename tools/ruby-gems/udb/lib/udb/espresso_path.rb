# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "rbconfig"
require "fileutils"
require "net/http"
require "uri"
require_relative "espresso_version"

module Udb
  # Returns the path to the managed espresso binary downloaded at gem install time.
  module EspressoPath
    GITHUB_REPO = "riscv/riscv-unified-db"

    class << self
      # Returns the absolute path to the espresso binary.
      # Attempts to download the binary if not present.
      # Raises only if the download or installation fails.
      def binary
        path = File.join(bin_dir, "espresso")
        unless File.exist?(path)
          begin
            download_binary(path)
          rescue => e
            raise "espresso binary not found at #{path} and download failed: #{e.message}"
          end
        end
        path
      end

      def bin_dir
        cpu =
          case RbConfig::CONFIG["host_cpu"]
          when /arm64|aarch64/ then "arm64"
          when /x86_64|x64/    then "x64"
          else raise "Unsupported host cpu: #{RbConfig::CONFIG["host_cpu"]}"
          end
        xdg_cache = ENV.fetch("XDG_CACHE_HOME", File.join(Dir.home, ".cache"))
        File.join(xdg_cache, "udb", "espresso", Udb::ESPRESSO_VERSION, cpu)
      end

      private

      def download_binary(dest_file)
        dest_dir = File.dirname(dest_file)
        FileUtils.mkdir_p(dest_dir)

        cpu =
          case RbConfig::CONFIG["host_cpu"]
          when /arm64|aarch64/ then "arm64"
          when /x86_64|x64/    then "x64"
          else raise "Unsupported host cpu: #{RbConfig::CONFIG["host_cpu"]}"
          end

        asset_name = "espresso-#{cpu}"
        url_str = "https://github.com/#{GITHUB_REPO}/releases/download/#{Udb::ESPRESSO_VERSION}/#{asset_name}"

        $stderr.puts "Downloading espresso (#{Udb::ESPRESSO_VERSION}, #{cpu}) from GitHub releases..."
        $stderr.puts "  URL: #{url_str}"

        body = download_with_redirects(url_str)
        File.binwrite(dest_file, body)
        File.chmod(0o755, dest_file)
        $stderr.puts "  Saved to #{dest_file}"
      end

      def download_with_redirects(url_str, limit = 10)
        raise "Too many HTTP redirects" if limit.zero?

        uri = URI.parse(url_str)
        http = Net::HTTP.new(uri.host, uri.port)
        http.use_ssl = (uri.scheme == "https")
        http.open_timeout = 30
        http.read_timeout = 120

        request = Net::HTTP::Get.new(uri.request_uri)
        request["User-Agent"] = "udb-gem/espresso-installer"

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
    end
  end
end
