# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "ffi"
require "fileutils"
require "net/http"
require "uri"
require "rbconfig"
require "tmpdir"
require "sorbet-runtime"
require "zip"

require_relative "log"
require_relative "z3_version"

module FFI
  class DynamicLibrary
    class << self
      alias_method :orig_load_library, :load_library
    end
    def self.load_library(name, flags)
      names =
        if name.is_a?(::Array)
          name
        else
          [name]
        end
      names.map! do |name|
        if name =~ /z3/
          unless Pathname.new(name).absolute?
            # when we load z3, make sure we get our installed version
            File.join(Udb::Z3Loader.z3_lib_dir, name)
          else
            name
          end
        else
          name
        end
      end
      orig_load_library(names, flags)
    end
  end
end

module Udb
  # Manages automatic download and installation of the Z3 library
  module Z3Loader
    extend T::Sig

    class Z3LoadError < StandardError; end

    class << self
      extend T::Sig

      # Main entry point - ensures Z3 is available before requiring the z3 gem
      sig { void }
      def ensure_z3_loaded
        # If Z3 is in our custom location, always configure the path
        if correct_version_installed?
          configure_library_path
          return
        end

        # Need to download and install Z3
        download_and_install_z3
        configure_library_path
      end

      sig { returns(String) }
      def z3_lib_dir
        File.join(z3_install_dir, Z3_VERSION.to_s)
      end

      private

      # Returns the platform-specific library name
      sig { returns(String) }
      def library_name
        case RbConfig::CONFIG["host_os"]
        when /darwin|mac os/
          "libz3.dylib"
        when /linux/
          "libz3.so"
        when /mswin|mingw|cygwin/
          "libz3.dll"
        else
          "libz3.so" # fallback
        end
      end

      # Check if the correct version of Z3 is installed in our local directory
      sig { returns(T::Boolean) }
      def correct_version_installed?
        return false unless Dir.exist?(z3_install_dir)

        version_file = File.join(z3_install_dir, "VERSION")
        return false unless File.exist?(version_file)

        installed_version = File.read(version_file).strip
        installed_version == Z3_VERSION
      end

      # Returns the base installation directory for Z3
      sig { returns(String) }
      def z3_install_dir
        base =
          if ENV.key?("IN_UDB_CONTAINER")
            "/opt"
          else
            if ENV["XDG_DATA_HOME"] && !T.must(ENV["XDG_DATA_HOME"]).empty?
              ENV["XDG_DATA_HOME"]
            else
              File.join(Dir.home, ".local", "share")
            end
          end
        File.join(base, "udb", "z3")
      end

      sig { returns(String) }
      def z3_bin_dir = z3_lib_dir

      # Configure the library search path to include our Z3 installation
      sig { void }
      def configure_library_path
        lib_dir = z3_lib_dir
        return unless Dir.exist?(lib_dir)

        case RbConfig::CONFIG["host_os"]
        when /darwin|mac os/
          # macOS uses DYLD_LIBRARY_PATH
          current = ENV["DYLD_LIBRARY_PATH"] || ""
          paths = current.split(":").reject(&:empty?)
          paths.unshift(lib_dir) unless paths.include?(lib_dir)
          ENV["DYLD_LIBRARY_PATH"] = paths.join(":")
        when /linux/
          # Linux uses LD_LIBRARY_PATH
          current = ENV["LD_LIBRARY_PATH"] || ""
          paths = current.split(":").reject(&:empty?)
          paths.unshift(lib_dir) unless paths.include?(lib_dir)
          ENV["LD_LIBRARY_PATH"] = paths.join(":")
        when /mswin|mingw|cygwin/
          # Windows uses PATH
          current = ENV["PATH"] || ""
          paths = current.split(";").reject(&:empty?)
          paths.unshift(lib_dir) unless paths.include?(lib_dir)
          ENV["PATH"] = paths.join(";")
        end
      end

      # Detect the current platform and return the Z3 release identifier
      sig { returns(String) }
      def detect_platform
        os = RbConfig::CONFIG["host_os"]
        cpu = RbConfig::CONFIG["host_cpu"]

        case os
        when /darwin|mac os/
          # macOS
          case cpu
          when /arm64|aarch64/
            "arm64-osx-11.0"
          when /x86_64|x64/
            "x64-osx-10.16"
          else
            raise Z3LoadError, "Unsupported macOS architecture: #{cpu}"
          end
        when /linux/
          # Linux - Z3 provides glibc builds
          case cpu
          when /x86_64|x64/
            "x64-glibc-2.39"
          when /arm64|aarch64/
            "arm64-glibc-2.39"
          else
            raise Z3LoadError, "Unsupported Linux architecture: #{cpu}"
          end
        when /mswin|mingw|cygwin/
          # Windows
          case cpu
          when /x86_64|x64/
            "x64-win"
          when /arm64|aarch64/
            "arm64-win"
          else
            raise Z3LoadError, "Unsupported Windows architecture: #{cpu}"
          end
        else
          raise Z3LoadError, "Unsupported operating system: #{os}"
        end
      end

      # Download and install Z3 from GitHub releases
      sig { void }
      def download_and_install_z3
        platform = detect_platform
        version = Z3_VERSION

        # Construct download URL
        filename = "z3-#{version}-#{platform}.zip"
        url = "https://github.com/Z3Prover/z3/releases/download/z3-#{version}/#{filename}"

        Udb.logger.debug "Downloading Z3 #{version} for #{platform}..."
        Udb.logger.debug "URL: #{url}"

        # Download to temporary directory
        Dir.mktmpdir do |tmpdir|
          zip_path = File.join(tmpdir, filename)

          begin
            download_file(url, zip_path)
          rescue => e
            raise Z3LoadError, "Failed to download Z3 from #{url}: #{e.message}\n" \
              "Please check your internet connection and try again.\n" \
              "You can also manually download Z3 and place libz3 in one of these directories:\n" \
              "  - #{z3_lib_dir}\n" \
              "  - /usr/local/lib\n" \
              "  - ~/.local/lib"
          end

          # verify checksum
          alg, expected_checksum = Z3_CHECKSUM.fetch(platform).split(":")
          case alg
          when "sha256"
            actual_checksum = Digest::SHA256.digest(File.read zip_path)
            if expected_checksum != actual_checksum
              raise Z3LoadError, "Checksum did not match on Z3 download. Please try again"
            end
          else
            raise Z3LoadError, "Unexpected checksum"
          end


          # Extract the archive
          extract_dir = File.join(tmpdir, "extracted")
          begin
            extract_zip(zip_path, extract_dir)
          rescue => e
            raise Z3LoadError, "Failed to extract Z3 archive: #{e.message}"
          end

          # Find the extracted directory (should be z3-version-platform)
          extracted_z3_dir = Dir.glob(File.join(extract_dir, "z3-*")).first
          unless extracted_z3_dir && Dir.exist?(extracted_z3_dir)
            raise Z3LoadError, "Could not find extracted Z3 directory"
          end

          # Install to our target directory
          install_z3(extracted_z3_dir)
        end

        Udb.logger.debug "Z3 #{version} installed successfully to #{z3_install_dir}"
      end

      # Download a file from a URL
      sig { params(url: String, destination: String).void }
      def download_file(url, destination)
        uri = URI.parse(url)

        Net::HTTP.start(uri.host, uri.port, open_timeout: 10, read_timeout: 10, use_ssl: uri.scheme == "https") do |http|
          request = Net::HTTP::Get.new(uri)

          http.request(request) do |response|
            case response
            when Net::HTTPSuccess
              File.open(destination, "wb") do |file|
                response.read_body do |chunk|
                  file.write(chunk)
                end
              end
            when Net::HTTPRedirection
              # Follow redirect
              redirect_url = response["location"]
              download_file(redirect_url, destination)
            else
              raise "HTTP #{response.code}: #{response.message}"
            end
          end
        end
      end

      # Extract a zip file
      sig { params(zip_path: String, destination: String).void }
      def extract_zip(zip_path, destination)
        FileUtils.mkdir_p(destination)

        Zip::File.open(zip_path) do |zip_file|
          zip_file.each do |entry|
            FileUtils.mkdir_p(File.dirname(File.join(destination, entry.name)))
            entry.extract(destination_directory: destination)
          end
        end
      end

      # Install Z3 from extracted directory to our target location
      sig { params(source_dir: String).void }
      def install_z3(source_dir)
        target_dir = File.join(z3_install_dir, Z3_VERSION)

        # Remove old installation if it exists
        FileUtils.rm_rf(target_dir) if Dir.exist?(target_dir)

        # Create target directory
        FileUtils.mkdir_p(target_dir)

        # Copy bin directories
        source_subdir = File.join(source_dir, 'bin')

        if Dir.exist?(source_subdir)
          FileUtils.cp_r(Dir.glob("#{source_subdir}/*"), target_dir)
        end

        # Write version file
        File.write(File.join(z3_install_dir, "VERSION"), Z3_VERSION)

        # Make binaries executable
        if Dir.exist?(target_dir)
          Dir.glob(File.join(target_dir, "*")).each do |file|
            FileUtils.chmod(0755, file) if File.file?(file)
          end
        end
      end
    end
  end
end
