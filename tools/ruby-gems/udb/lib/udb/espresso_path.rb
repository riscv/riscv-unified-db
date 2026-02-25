# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "rbconfig"
require_relative "espresso_version"

module Udb
  # Returns the path to the managed espresso binary downloaded at gem install time.
  module EspressoPath
    class << self
      # Returns the absolute path to the espresso binary.
      # Raises if the binary is not present (i.e. the gem was not installed correctly).
      def binary
        path = File.join(bin_dir, "espresso")
        unless File.exist?(path)
          raise "espresso binary not found at #{path}. " \
                "Re-install the udb gem to download it."
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
    end
  end
end
