# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require_relative "test_helper"
require_relative "../lib/udb/z3"

begin
  require "udb/resolver"
  $db_resolver = Udb::Resolver.new(Udb.repo_root)
  $db_cfg_arch = $db_resolver.cfg_arch_for("_")
rescue RuntimeError
  $db_cfg_arch = nil
end

class TestZ3Extensions < Minitest::Test
  def setup
    @solver = Udb::Z3Solver.new
  end

  # Z3ExtensionVersion tests
  def test_extension_version_initialization
    skip "Database not available" if $db_cfg_arch.nil?

    ext_ver = @solver.ext_ver("A", "1.0", $db_cfg_arch)
    assert_instance_of Udb::Z3ExtensionVersion, ext_ver
  end

  def test_extension_version_caching
    skip "Database not available" if $db_cfg_arch.nil?

    ext_ver1 = @solver.ext_ver("A", "1.0", $db_cfg_arch)
    ext_ver2 = @solver.ext_ver("A", "1.0", $db_cfg_arch)

    # Should return the same cached instance
    assert_equal ext_ver1.object_id, ext_ver2.object_id
  end

  def test_extension_version_different_versions
    skip "Database not available" if $db_cfg_arch.nil?

    ext_ver_10 = @solver.ext_ver("A", "1.0", $db_cfg_arch)
    ext_ver_20 = @solver.ext_ver("A", "2.0", $db_cfg_arch)

    # Should be different instances
    refute_equal ext_ver_10.object_id, ext_ver_20.object_id
  end

  def test_extension_version_equality
    skip "Database not available" if $db_cfg_arch.nil?

    ext_ver = @solver.ext_ver("A", "1.0", $db_cfg_arch)

    @solver.push
    @solver.assert(ext_ver == "1.0")
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_extension_version_greater_than
    skip "Database not available" if $db_cfg_arch.nil?

    ext_ver = @solver.ext_ver("A", "2.0", $db_cfg_arch)

    @solver.push
    @solver.assert(ext_ver > "1.0")
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_extension_version_less_than
    skip "Database not available" if $db_cfg_arch.nil?

    ext_ver = @solver.ext_ver("A", "1.0", $db_cfg_arch)

    @solver.push
    @solver.assert(ext_ver < "2.0")
    assert @solver.satisfiable?, proc { "Should be satisfiable: #{@solver.assertions}" }
    @solver.pop
  end

  def test_extension_version_greater_than_or_equal
    skip "Database not available" if $db_cfg_arch.nil?

    ext_ver = @solver.ext_ver("A", "1.0", $db_cfg_arch)

    @solver.push
    @solver.assert(ext_ver >= "1.0")
    assert @solver.satisfiable?
    @solver.pop

    @solver.push
    @solver.assert(ext_ver >= "0.9")
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_extension_version_less_than_or_equal
    skip "Database not available" if $db_cfg_arch.nil?

    ext_ver = @solver.ext_ver("A", "1.0", $db_cfg_arch)

    @solver.push
    @solver.assert(ext_ver <= "1.0")
    assert @solver.satisfiable?
    @solver.pop

    @solver.push
    @solver.assert(ext_ver <= "2.0")
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_extension_version_prerelease_handling
    skip "Database not available" if $db_cfg_arch.nil?

    # Test with pre-release version if available
    ext_ver = @solver.ext_ver("A", "1.0.0-pre", $db_cfg_arch)

    @solver.push
    @solver.assert(ext_ver >= "1.0.0-pre")
    assert @solver.satisfiable?
    @solver.pop
  end

  # Z3ExtensionRequirement tests
  def test_extension_requirement_initialization
    skip "Database not available" if $db_cfg_arch.nil?

    ext_req = @solver.ext_req("A", Udb::RequirementSpec.new(">= 1.0"), $db_cfg_arch)
    assert_instance_of Udb::Z3ExtensionRequirement, ext_req
  end

  def test_extension_requirement_caching
    skip "Database not available" if $db_cfg_arch.nil?

    ext_req1 = @solver.ext_req("A", Udb::RequirementSpec.new(">= 1.0"), $db_cfg_arch)
    ext_req2 = @solver.ext_req("A", Udb::RequirementSpec.new(">= 1.0"), $db_cfg_arch)

    # Should return the same cached instance
    assert_equal ext_req1.object_id, ext_req2.object_id
  end

  def test_extension_requirement_different_requirements
    skip "Database not available" if $db_cfg_arch.nil?

    ext_req1 = @solver.ext_req("A", Udb::RequirementSpec.new(">= 1.0"), $db_cfg_arch)
    ext_req2 = @solver.ext_req("A", Udb::RequirementSpec.new(">= 2.0"), $db_cfg_arch)

    # Should be different instances
    refute_equal ext_req1.object_id, ext_req2.object_id
  end

  def test_extension_requirement_satisfied_by_exact_version
    skip "Database not available" if $db_cfg_arch.nil?

    ext_req = @solver.ext_req("A", Udb::RequirementSpec.new("= 2.1.0"), $db_cfg_arch)
    ext_ver = @solver.ext_ver("A", "2.1.0", $db_cfg_arch)

    @solver.push
    @solver.assert ext_req.term & ext_ver.term
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_extension_requirement_satisfied_by_greater_version
    skip "Database not available" if $db_cfg_arch.nil?

    ext_req = @solver.ext_req("A", Udb::RequirementSpec.new(">= 1.0"), $db_cfg_arch)
    ext_ver = @solver.ext_ver("A", "2.1", $db_cfg_arch)

    @solver.push
    @solver.assert ext_req.term & ext_ver.term
    assert @solver.satisfiable?, proc { "Should be satisfiable: #{@solver.assertions}" }
    @solver.pop
  end

  def test_extension_requirement_empty_version_list
    skip "Database not available" if $db_cfg_arch.nil?

    # Test with extension that has no versions
    ext_req = @solver.ext_req("NonExistent", Udb::RequirementSpec.new(">= 1.0"), $db_cfg_arch)

    # Should handle gracefully
    assert_instance_of Udb::Z3ExtensionRequirement, ext_req
  end

  # Integration tests
  def test_extension_version_and_requirement_integration
    skip "Database not available" if $db_cfg_arch.nil?

    ext_req = @solver.ext_req("A", Udb::RequirementSpec.new(">= 1.0"), $db_cfg_arch)
    ext_ver = @solver.ext_ver("A", Udb::VersionSpec.new("2.1"), $db_cfg_arch)

    @solver.push
    @solver.assert ext_req.term & ext_ver.term
    @solver.assert(ext_ver >= "1.0")
    @solver.assert(ext_ver < "3.0")
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_multiple_extension_requirements
    skip "Database not available" if $db_cfg_arch.nil?

    ext_req_a = @solver.ext_req("A", Udb::RequirementSpec.new(">= 2.1"), $db_cfg_arch)
    ext_req_b = @solver.ext_req("B", Udb::RequirementSpec.new(">= 1.0"), $db_cfg_arch)

    ext_ver_a = @solver.ext_ver("A", Udb::VersionSpec.new("2.1"), $db_cfg_arch)
    ext_ver_b = @solver.ext_ver("B", Udb::VersionSpec.new("1.0"), $db_cfg_arch)

    @solver.push
    @solver.assert ext_req_a.term & ext_ver_a.term
    @solver.assert ext_req_b.term & ext_ver_b.term
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_extension_requirement_operators
    skip "Database not available" if $db_cfg_arch.nil?

    # Test various requirement operators
    operators = ["=", ">=", ">", "<=", "<", "!="]

    operators.each do |op|
      ext_req = @solver.ext_req("A", Udb::RequirementSpec.new("#{op} 1.0"), $db_cfg_arch)
      assert_instance_of Udb::Z3ExtensionRequirement, ext_req
    end
  end

  def test_extension_version_comparison_chain
    skip "Database not available" if $db_cfg_arch.nil?

    ext_ver = @solver.ext_ver("A", "1.5", $db_cfg_arch)

    @solver.push
    @solver.assert(ext_ver > "1.0")
    @solver.assert(ext_ver < "2.0")
    @solver.assert(ext_ver >= "1.5")
    @solver.assert(ext_ver <= "1.5")
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_extension_version_with_parameter_constraints
    skip "Database not available" if $db_cfg_arch.nil?

    ext_ver = @solver.ext_ver("A", "1.0", $db_cfg_arch)
    param = @solver.param("TEST_PARAM", { "type" => "integer", "minimum" => 0, "maximum" => 10 })

    @solver.push
    @solver.assert(ext_ver == "1.0")
    @solver.assert(param == 5)
    assert @solver.satisfiable?
    @solver.pop
  end
end
