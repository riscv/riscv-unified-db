# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require_relative "test_helper"

require "fileutils"
require "tmpdir"
require "yaml"

require "udb/logic"
require "udb/cfg_arch"
require "udb/resolver"

class TestCfgArch < Minitest::Test
  include Udb

  def setup
    @gen_dir = Dir.mktmpdir
    @resolver = Udb::Resolver.new(
      Udb.repo_root,
      gen_path_override: Pathname.new(@gen_dir)
    )
  end

  def teardown
    FileUtils.rm_rf @gen_dir
  end

  def test_invalid_partial_config
    cfg = <<~CFG
      $schema: config_schema.json#
      kind: architecture configuration
      type: partially configured
      name: rv32-bad
      description: A generic RV32 system; only MXLEN is known
      params:
        MXLEN: 31
        NOT_A: false
        CACHE_BLOCK_SIZE: 64

      mandatory_extensions:
        - name: "I"
          version: ">= 0"
        - name: "Sm"
          version: ">= 0"
        - name: Znotanextension
          version: ">= 0"
        - name: D
          version: "= 50"
        - name: Zcd
          version: ">= 0"
        - name: Zcmp
          version: ">= 0"
    CFG

    Tempfile.create do |f|
      f.write cfg
      f.flush

      cfg_arch = @resolver.cfg_arch_for(Pathname.new f.path)
      result = cfg_arch.valid?

      refute result.valid
      assert_includes result.reasons, "Extension requirement can never be met (no match in the database): Znotanextension "
      assert_includes result.reasons, "Extension requirement can never be met (no match in the database): D = 50"
      assert_includes result.reasons, "Parameter value violates the schema: 'MXLEN' = '31'"
      assert_includes result.reasons, "Parameter has no definition: 'NOT_A'"
    end

    cfg = <<~CFG
      $schema: config_schema.json#
      kind: architecture configuration
      type: partially configured
      name: rv32-bad2
      description: A generic RV32 system; only MXLEN is known
      params:
        MXLEN: 32
        CACHE_BLOCK_SIZE: 64

      mandatory_extensions:
        - name: "I"
          version: ">= 0"
        - name: "Sm"
          version: ">= 0"
        - name: Zcd
          version: ">= 0"
        - name: Zcmp
          version: ">= 0"
    CFG

    Tempfile.create do |f|
      f.write cfg
      f.flush

      cfg_arch = @resolver.cfg_arch_for(Pathname.new f.path)
      result = cfg_arch.valid?

      refute result.valid
      param_reasons = result.reasons.select { |r| r.include?("Parameter is not defined by this config: 'CACHE_BLOCK_SIZE'") }
      assert_equal 1, param_reasons.size, "Expected exactly one reason about CACHE_BLOCK_SIZE"
      assert param_reasons.first.include?("Failing condition(s):"), "Expected failing conjuncts header in: #{param_reasons.first}"
      assert param_reasons.first.include?("  - "), "Expected at least one failing conjunct line in: #{param_reasons.first}"
      assert result.reasons.any? { |r| r =~ /Mandatory extension requirements conflict: This is not satisfiable: / }
    end
  end

  def test_invalid_full_config
    cfg = <<~CFG
      $schema: config_schema.json#
      kind: architecture configuration
      type: fully configured
      name: rv32-bad
      description: A generic RV32 system
      params:

        # bad params
        MXLEN: 31
        NOT_A: false
        CACHE_BLOCK_SIZE: 64

        # good params
        TRAP_ON_EBREAK: true
        TRAP_ON_ECALL_FROM_M: true
        TRAP_ON_ILLEGAL_WLRL: true
        TRAP_ON_RESERVED_INSTRUCTION: true
        TRAP_ON_UNIMPLEMENTED_CSR: true
        TRAP_ON_UNIMPLEMENTED_INSTRUCTION: true

      implemented_extensions:
        - [I, "2.1.0"]
        - [Sm, "1.13.0"]
        - [C, "2.0.0"]
        - [Zca, "1.0.0"]

        # should fail; not a real extension
        - [Znotanextension, "1.0.0"]

        # should cause validation error: Not a known version of F
        - [F, "0.1"]

        # should cause validation error: Zcd requires D
        - [Zcd, "1.0.0"]

        # should cause validation error: Zcmp condlicts with Zcd
        - [Zcmp, "1.0.0"]
    CFG

    Tempfile.create do |f|
      f.write cfg
      f.flush

      cfg_arch = @resolver.cfg_arch_for(Pathname.new f.path)
      result = cfg_arch.valid?

      refute result.valid
      assert_includes result.reasons, "Parameter value violates the schema: 'MXLEN' = '31'"
      assert_includes result.reasons, "Parameter has no definition: 'NOT_A'"
      assert_includes result.reasons, "Znotanextension is not a known extension"
      assert result.reasons.any? { |r| r.include?("0.1") && r.include?("not a known extension") }, "Unknown version should be rejected"
      # ... and more, which are not being explictly checked because the above need resolved before they will print
      # assert_includes result.reasons, "Parameter is not defined by this config: 'CACHE_BLOCK_SIZE'. Needs: (Zicbom>=0 || Zicbop>=0 || Zicboz>=0)"
      # assert_includes result.reasons, "Extension requirement is unmet: Zcmp@1.0.0. Needs: (Zca>=0 && !Zcd>=0)"
      # assert_includes result.reasons, "Parameter is required but missing: 'M_MODE_ENDIANNESS'"
      # assert_includes result.reasons, "Parameter is required but missing: 'PHYS_ADDR_WIDTH'"
      # assert_includes result.reasons, "Extension version has no definition: F@0.1.0"
      # assert_includes result.reasons, "Extension version has no definition: Znotanextension@1.0.0"
    end

    cfg = <<~CFG
      $schema: config_schema.json#
      kind: architecture configuration
      type: fully configured
      name: rv32-bad-version-only
      description: A generic RV32 system
      params:
        MXLEN: 32

      implemented_extensions:
        - [I, "9.9.9"]
    CFG

    Tempfile.create do |f|
      f.write cfg
      f.flush

      cfg_arch = @resolver.cfg_arch_for(Pathname.new f.path)
      result = cfg_arch.valid?

      refute result.valid
      assert result.reasons.any? { |r| r.include?("9.9.9") && r.include?("not a known extension") }, "Unknown version should be rejected"
    end


    cfg = <<~CFG
      $schema: config_schema.json#
      kind: architecture configuration
      type: fully configured
      name: rv32-bad2
      description: A generic RV32 system
      params:

        MXLEN: 32
        CACHE_BLOCK_SIZE: 64

        TRAP_ON_EBREAK: true
        TRAP_ON_ECALL_FROM_M: true
        TRAP_ON_ILLEGAL_WLRL: true
        TRAP_ON_RESERVED_INSTRUCTION: true
        TRAP_ON_UNIMPLEMENTED_CSR: true
        TRAP_ON_UNIMPLEMENTED_INSTRUCTION: true

      implemented_extensions:
        - [I, "2.1.0"]
        - [Sm, "1.13.0"]
        - [C, "2.0.0"]
        - [Zca, "1.0.0"]

        # should cause validation error: Zcd requires D
        - [Zcd, "1.0.0"]

        # should cause validation error: Zcmp condlicts with Zcd
        - [Zcmp, "1.0.0"]
    CFG

    Tempfile.create do |f|
      f.write cfg
      f.flush

      cfg_arch = @resolver.cfg_arch_for(Pathname.new f.path)
      result = cfg_arch.valid?

      refute result.valid
      assert result.reasons.any? { |r| r =~ /Parameter is not defined by this config: 'CACHE_BLOCK_SIZE'/ }, "Parameter CACHE_BLOCK_SIZE should not be allowed"
      assert result.reasons.any? { |r| r =~ /Extension requirement is unmet: Zcmp@1\.0\.0/ }, "Zcmp requirements haven't been met, but the config does't pick that up"
      assert_includes result.reasons, "Parameter is required but missing: 'M_MODE_ENDIANNESS'"
      assert_includes result.reasons, "Parameter is required but missing: 'PHYS_ADDR_WIDTH'"
      # ... plus more
    end
  end

  def test_cfg_arch_properties
    cfg = <<~CFG
      $schema: config_schema.json#
      kind: architecture configuration
      type: partially configured
      name: rv32
      description: A generic RV32 system; only MXLEN is known
      params:
        MXLEN: 32
      mandatory_extensions:
        - name: "I"
          version: ">= 0"
        - name: "Sm"
          version: ">= 0"
    CFG

    Tempfile.create(%w/cfg .yaml/) do |f|
      f.write cfg
      f.flush

      cfg_arch = @resolver.cfg_arch_for(Pathname.new f.path)

      cfg_arch.type_check(show_progress: true)

      assert_equal cfg_arch.config.param_values.size, cfg_arch.params_with_value.size

      total_params = cfg_arch.params_with_value.size + cfg_arch.params_without_value.size + cfg_arch.out_of_scope_params.size
      assert_equal cfg_arch.params.size, total_params

      if cfg_arch.fully_configured?
        assert_equal cfg_arch.config.implemented_extensions.size, cfg_arch.explicitly_implemented_extensions.size
        assert cfg_arch.config.implemented_extensions.size <= cfg_arch.implemented_extensions.size
        assert cfg_arch.config.implemented_extensions.size <= cfg_arch.implemented_extensions.size
      elsif cfg_arch.partially_configured?
        mandatory = cfg_arch.mandatory_extension_reqs
        mandatory.each do |ext_req|
          assert ext_req.to_condition.could_be_satisfied_by_cfg_arch?(cfg_arch)
        end
      end

      possible = cfg_arch.possible_extension_versions

      possible.each do |ext_ver|
        assert ext_ver.to_condition.could_be_satisfied_by_cfg_arch?(cfg_arch)
      end

      cfg_arch.not_prohibited_extensions.each do |ext|
        assert \
          ext.versions.any? do |ext_ver|
            ext_ver.to_condition.could_be_satisfied_by_cfg_arch?(cfg_arch)
          end
      end

      cfg_arch.prohibited_extension_versions.each do |ext_ver|
        refute ext_ver.to_condition.could_be_satisfied_by_cfg_arch?(cfg_arch)
        assert cfg_arch.prohibited_ext?(ext_ver)
        assert cfg_arch.prohibited_ext?(ext_ver.name)
        assert cfg_arch.prohibited_ext?(ext_ver.name.to_s)
      end
    end
  end

  def test_transitive
    cfg = <<~YAML
      ---
      $schema: config_schema.json#
      kind: architecture configuration
      type: partially configured
      name: rv64_no32
      description: A generic RV64 system, no RV32 possible
      params:
        MXLEN: 64
        SXLEN: [64]
        UXLEN: [64]
      mandatory_extensions:
        - name: "I"
          version: ">= 0"
        - name: "Sm"
          version: ">= 0"
      prohibited_extensions:
        - name: H
          version: ">= 0"
    YAML
    cfg_arch = nil

    Tempfile.create do |f|
      f.write cfg
      f.flush
      cfg_arch = @resolver.cfg_arch_for(Pathname.new f.path)
    end

    refute Udb::Condition.new({ "xlen" => 32 }, cfg_arch).satisfiable_by_cfg_arch?(cfg_arch)
    assert Udb::Condition.new({ "xlen" => 64 }, cfg_arch).satisfiable_by_cfg_arch?(cfg_arch)

    # make sure that RV32-only extensions are not possible
    refute_includes cfg_arch.possible_extension_versions.map(&:name), "Zilsd"
    refute_includes cfg_arch.possible_extensions.map(&:name), "Zilsd"
    refute_includes cfg_arch.possible_extensions.map(&:name), "Zclsd"

  end

  def test_transitive_full

    cfg_arch = @resolver.cfg_arch_for("rv64")

    assert_equal cfg_arch.extension_version("C", "2.0.0"), cfg_arch.extension_version("C", "2.0.0")
    assert cfg_arch.extension_version("C", "2.0.0").eql?(cfg_arch.extension_version("C", "2.0.0"))
    assert_equal cfg_arch.extension_version("C", "2.0.0").hash, cfg_arch.extension_version("C", "2.0.0").hash

    assert_equal \
      [
        cfg_arch.extension_version("C", "2.0.0"),
        cfg_arch.extension_version("Zca", "1.0.0"),
      ],
      cfg_arch.expand_implemented_extension_list(
        [
          cfg_arch.extension_version("C", "2.0.0")
        ]
      ).sort

    assert_equal \
      [
        cfg_arch.extension_version("C", "2.0.0"),
        cfg_arch.extension_version("F", "2.2.0"),
        cfg_arch.extension_version("Zca", "1.0.0"),
        cfg_arch.extension_version("Zcf", "1.0.0"),
        cfg_arch.extension_version("Zicsr", "2.0.0")
      ],
      [
        cfg_arch.extension_version("C", "2.0.0"),
        cfg_arch.extension_version("F", "2.2.0"),
        cfg_arch.extension_version("Zca", "1.0.0"),
        cfg_arch.extension_version("Zcf", "1.0.0"),
        cfg_arch.extension_version("Zicsr", "2.0.0")
    ].uniq

    assert_equal \
      [
        cfg_arch.extension_version("C", "2.0.0"),
        cfg_arch.extension_version("F", "2.2.0"),
        cfg_arch.extension_version("Zca", "1.0.0"),
        cfg_arch.extension_version("Zicsr", "2.0.0")
      ],
      cfg_arch.expand_implemented_extension_list(
        [
          cfg_arch.extension_version("C", "2.0.0"),
          cfg_arch.extension_version("F", "2.2.0")
        ]
      ).sort

    assert_equal \
      [
        cfg_arch.extension_version("C", "2.0.0"),
        cfg_arch.extension_version("D", "2.2.0"),
        cfg_arch.extension_version("F", "2.2.0"),
        cfg_arch.extension_version("Zca", "1.0.0"),
        cfg_arch.extension_version("Zcd", "1.0.0"),
        cfg_arch.extension_version("Zicsr", "2.0.0")
      ],
      cfg_arch.expand_implemented_extension_list(
        [
          cfg_arch.extension_version("C", "2.0.0"),
          cfg_arch.extension_version("D", "2.2.0")
        ]
      ).sort
  end

  def test_xqci

    cfg_arch = @resolver.cfg_arch_for("qc_iu")

    exts = [
      cfg_arch.extension("Xqci"),
      cfg_arch.extension("Xqcia"),
      cfg_arch.extension("Xqciac"),
      cfg_arch.extension("Xqcibi"),
      cfg_arch.extension("Xqcibm"),
      cfg_arch.extension("Xqcicli"),
      cfg_arch.extension("Xqcicm"),
      cfg_arch.extension("Xqcics"),
      cfg_arch.extension("Xqcicsr"),
      cfg_arch.extension("Xqciint"),
      cfg_arch.extension("Xqciio"),
      cfg_arch.extension("Xqcilb"),
      cfg_arch.extension("Xqcili"),
      cfg_arch.extension("Xqcilia"),
      cfg_arch.extension("Xqcilo"),
      cfg_arch.extension("Xqcilsm"),
      cfg_arch.extension("Xqcisim"),
      cfg_arch.extension("Xqcisls"),
      cfg_arch.extension("Xqcisync")
    ]

    assert_equal 11, cfg_arch.extension("Xqcia").max_version.directly_defined_instructions.size
    assert_equal 157, cfg_arch.extension("Xqci").max_version.implied_instructions.count { |i| exts.any? { |e| i.defined_by_condition.mentions?(e) } }
  end

  def test_full_config_extension_requirement_failure_reports_failing_conjuncts
    # Zcd requires D, but D is not in the config — verify the error uses failing_conjuncts format
    cfg = <<~CFG
      $schema: config_schema.json#
      kind: architecture configuration
      type: fully configured
      name: rv32-zcd-no-d
      description: A config with Zcd but without D
      params:
        MXLEN: 32
        TRAP_ON_EBREAK: true
        TRAP_ON_ECALL_FROM_M: true
        TRAP_ON_ILLEGAL_WLRL: true
        TRAP_ON_RESERVED_INSTRUCTION: true
        TRAP_ON_UNIMPLEMENTED_CSR: true
        TRAP_ON_UNIMPLEMENTED_INSTRUCTION: true
        M_MODE_ENDIANNESS: little
        PHYS_ADDR_WIDTH: 32

      implemented_extensions:
        - [I, "2.1.0"]
        - [Sm, "1.13.0"]
        - [C, "2.0.0"]
        - [Zca, "1.0.0"]
        - [Zcd, "1.0.0"]
    CFG

    Tempfile.create(%w/cfg .yaml/) do |f|
      f.write cfg
      f.flush

      cfg_arch = @resolver.cfg_arch_for(Pathname.new f.path)
      result = cfg_arch.valid?

      refute result.valid
      unmet = result.reasons.select { |r| r.include?("Extension requirement is unmet: Zcd@") }
      assert_equal 1, unmet.size, proc { "Expected exactly one unmet-extension reason for Zcd. Got: \n #{unmet}" }
      assert unmet.first.include?("Failing condition(s):"), "Expected failing conjuncts header in: #{unmet.first}"
      assert unmet.first.include?("  - "), "Expected at least one failing conjunct line in: #{unmet.first}"
    end
  end

  def test_partial_config_parameter_defined_by_reports_failing_conjuncts
    # rv32-bad2 config has CACHE_BLOCK_SIZE but no Zicbom/Zicbop/Zicboz — verify failing_conjuncts format
    cfg = <<~CFG
      $schema: config_schema.json#
      kind: architecture configuration
      type: partially configured
      name: rv32-bad2
      description: A generic RV32 system; only MXLEN is known
      params:
        MXLEN: 32
        CACHE_BLOCK_SIZE: 64

      mandatory_extensions:
        - name: "I"
          version: ">= 0"
        - name: "Sm"
          version: ">= 0"
        - name: Zcd
          version: ">= 0"
        - name: Zcmp
          version: ">= 0"
    CFG

    Tempfile.create(%w/cfg .yaml/) do |f|
      f.write cfg
      f.flush

      cfg_arch = @resolver.cfg_arch_for(Pathname.new f.path)
      result = cfg_arch.valid?

      refute result.valid
      param_reasons = result.reasons.select { |r| r.include?("Parameter is not defined by this config: 'CACHE_BLOCK_SIZE'") }
      assert_equal 1, param_reasons.size, "Expected exactly one reason about CACHE_BLOCK_SIZE"
      assert param_reasons.first.include?("Failing condition(s):"), "Expected failing conjuncts header in: #{param_reasons.first}"
      assert param_reasons.first.include?("  - "), "Expected at least one failing conjunct line in: #{param_reasons.first}"
    end
  end

  def test_partial_config_parameter_defined_by_unknown_terms
    # When the defining extensions are possible but not mandatory, terms show as {unknown}.
    # failing_conjuncts should still return the whole unsatisfied clause (not an empty list),
    # so the error message remains actionable.
    cfg = <<~CFG
      $schema: config_schema.json#
      kind: architecture configuration
      type: partially configured
      name: rv32-maybe-cache
      description: I+Sm only; Zicbom/Zicbop/Zicboz are possible but not mandatory
      params:
        MXLEN: 32
        CACHE_BLOCK_SIZE: 64

      mandatory_extensions:
        - name: "I"
          version: ">= 0"
        - name: "Sm"
          version: ">= 0"
    CFG

    Tempfile.create(%w/cfg .yaml/) do |f|
      f.write cfg
      f.flush

      cfg_arch = @resolver.cfg_arch_for(Pathname.new f.path)
      result = cfg_arch.valid?

      refute result.valid
      param_reasons = result.reasons.select { |r| r.include?("Parameter is not defined by this config: 'CACHE_BLOCK_SIZE'") }
      assert_equal 1, param_reasons.size, "Expected exactly one reason about CACHE_BLOCK_SIZE"
      # The message must still have a bullet line — not an empty list — even though terms are unknown
      assert param_reasons.first.include?("  - "), "Expected at least one failing conjunct line even with unknown terms"
      # The bullet should contain {unknown} annotations, not {false}, since the extensions are possible
      assert param_reasons.first.include?("{unknown}"), "Expected {unknown} annotations for possible-but-not-mandatory extensions"
    end
  end
end
