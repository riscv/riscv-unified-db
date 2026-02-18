# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "minitest/autorun"
require "fileutils"
require "tmpdir"
require_relative "../lib/udb/z3_version"
require_relative "../lib/udb/z3_loader"

class TestZ3Loader < Minitest::Test
  def setup
    @original_env = ENV.to_h.dup
    @temp_home = Dir.mktmpdir("z3_loader_test")
    @temp_xdg = File.join(@temp_home, "xdg_data")
    FileUtils.mkdir_p(@temp_xdg)

    # Override home directory for testing
    ENV["HOME"] = @temp_home
    ENV["XDG_DATA_HOME"] = @temp_xdg

    # Clear library paths
    ENV.delete("LD_LIBRARY_PATH")
    ENV.delete("DYLD_LIBRARY_PATH")

    # Reset the Z3Loader module state by clearing any cached values
    # This ensures each test starts fresh
  end

  def teardown
    # Restore original environment
    ENV.replace(@original_env)

    # Clean up temporary directory
    FileUtils.rm_rf(@temp_home) if @temp_home && Dir.exist?(@temp_home)
  end

  def test_z3_version_constant_exists
    assert_equal "4.13.4", Udb::Z3_VERSION
  end

  def test_library_name_linux
    skip "Only runs on Linux" unless RbConfig::CONFIG["host_os"] =~ /linux/

    lib_name = Udb::Z3Loader.send(:library_name)
    assert_equal "libz3.so", lib_name
  end

  def test_library_name_macos
    skip "Only runs on macOS" unless RbConfig::CONFIG["host_os"] =~ /darwin|mac os/

    lib_name = Udb::Z3Loader.send(:library_name)
    assert_equal "libz3.dylib", lib_name
  end

  def test_z3_install_dir_uses_xdg_data_home
    expected = File.join(@temp_xdg, "udb", "z3")
    actual = Udb::Z3Loader.send(:z3_install_dir)
    assert_equal expected, actual
  end

  def test_z3_install_dir_falls_back_to_local_share
    ENV.delete("XDG_DATA_HOME")

    expected = File.join(@temp_home, ".local", "share", "udb", "z3")
    actual = Udb::Z3Loader.send(:z3_install_dir)
    assert_equal expected, actual
  end

  def test_z3_lib_dir_includes_version
    lib_dir = Udb::Z3Loader.send(:z3_lib_dir)
    assert_includes lib_dir, Udb::Z3_VERSION
  end

  def test_correct_version_installed_returns_false_when_not_installed
    refute Udb::Z3Loader.send(:correct_version_installed?)
  end

  def test_correct_version_installed_returns_true_when_version_matches
    # Create the directory structure
    install_dir = Udb::Z3Loader.send(:z3_install_dir)
    lib_dir = Udb::Z3Loader.send(:z3_lib_dir)
    FileUtils.mkdir_p(lib_dir)

    # Write the version file
    File.write(File.join(install_dir, "VERSION"), Udb::Z3_VERSION)

    assert Udb::Z3Loader.send(:correct_version_installed?)
  end

  def test_correct_version_installed_returns_false_when_version_mismatch
    # Create the directory structure
    install_dir = Udb::Z3Loader.send(:z3_install_dir)
    lib_dir = Udb::Z3Loader.send(:z3_lib_dir)
    FileUtils.mkdir_p(lib_dir)

    # Write a different version
    File.write(File.join(install_dir, "VERSION"), "4.0.0")

    refute Udb::Z3Loader.send(:correct_version_installed?)
  end

  def test_configure_library_path_sets_ld_library_path_on_linux
    skip "Only runs on Linux" unless RbConfig::CONFIG["host_os"] =~ /linux/

    lib_dir = Udb::Z3Loader.send(:z3_lib_dir)
    FileUtils.mkdir_p(lib_dir)

    Udb::Z3Loader.send(:configure_library_path)

    assert_includes ENV["LD_LIBRARY_PATH"], lib_dir
  end

  def test_configure_library_path_sets_dyld_library_path_on_macos
    skip "Only runs on macOS" unless RbConfig::CONFIG["host_os"] =~ /darwin|mac os/

    lib_dir = Udb::Z3Loader.send(:z3_lib_dir)
    FileUtils.mkdir_p(lib_dir)

    Udb::Z3Loader.send(:configure_library_path)

    assert_includes ENV["DYLD_LIBRARY_PATH"], lib_dir
  end

  def test_detect_platform_returns_valid_string
    platform = Udb::Z3Loader.send(:detect_platform)

    assert platform.is_a?(String)
    assert platform.length > 0

    # Should match one of the known platform patterns
    valid_patterns = [
      /x64-glibc/,
      /arm64-glibc/,
      /x64-osx/,
      /arm64-osx/,
      /x64-win/,
      /arm64-win/
    ]

    assert valid_patterns.any? { |pattern| platform =~ pattern },
      "Platform '#{platform}' doesn't match any known pattern"
  end

  def test_z3_load_error_is_standard_error
    assert Udb::Z3Loader::Z3LoadError < StandardError
  end

  def test_ensure_z3_loaded_with_existing_installation
    # Set up a mock installation
    install_dir = Udb::Z3Loader.send(:z3_install_dir)
    lib_dir = Udb::Z3Loader.send(:z3_lib_dir)
    FileUtils.mkdir_p(lib_dir)

    # Write version file
    File.write(File.join(install_dir, "VERSION"), Udb::Z3_VERSION)

    # Create mock library
    lib_name = Udb::Z3Loader.send(:library_name)
    File.write(File.join(lib_dir, lib_name), "mock library")

    # This should not raise an error and should configure the path
    Udb::Z3Loader.ensure_z3_loaded

    # Verify library path was configured
    if RbConfig::CONFIG["host_os"] =~ /linux/
      assert ENV.key?("LD_LIBRARY_PATH"), "LD_LIBRARY_PATH should be set"
      assert_includes ENV["LD_LIBRARY_PATH"], lib_dir if ENV["LD_LIBRARY_PATH"]
    elsif RbConfig::CONFIG["host_os"] =~ /darwin|mac os/
      assert ENV.key?("DYLD_LIBRARY_PATH"), "DYLD_LIBRARY_PATH should be set"
      assert_includes ENV["DYLD_LIBRARY_PATH"], lib_dir if ENV["DYLD_LIBRARY_PATH"]
    end
  end
end
