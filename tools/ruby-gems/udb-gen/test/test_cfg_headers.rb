# Copyright (c) Jordan Carlin, Harvey Mudd College.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require_relative "test_helper"

require "fileutils"
require "rexml/document"
require "tmpdir"
require "pathname"

require "udb/resolver"
require "udb-gen/generators/cfg_c_header/generator"
require "udb-gen/generators/cfg_svh_header/generator"
require "udb-gen/generators/cfg_gdb_xml/generator"

class TestCfgHeaders < Minitest::Test
  GOLDEN_DIR = Pathname.new(__dir__).parent.parent.parent.parent / "tests" / "golden"
  TEST_CONFIG = "mc100-32-full-example"

  module GeneratorTestHelper
    def configure_for_test(resolver:, cfg:)
      @resolver = resolver
      parse(["--cfg", cfg])
      self
    end
  end

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

  def test_cfg_c_header_matches_golden
    gen = UdbGen::GenCfgCHeaderOptions.new
    gen.extend(GeneratorTestHelper).configure_for_test(resolver: @resolver, cfg: TEST_CONFIG)
    output = gen.generate_header
    golden = File.read(GOLDEN_DIR / "#{TEST_CONFIG}.golden.h")
    assert_equal golden, output,
      "C header output does not match golden file. " \
      "If this is expected, update the golden file with: ./bin/chore gen cfg-headers"
  end

  def test_cfg_svh_header_matches_golden
    gen = UdbGen::GenCfgSvhHeaderOptions.new
    gen.extend(GeneratorTestHelper).configure_for_test(resolver: @resolver, cfg: TEST_CONFIG)
    output = gen.generate_header
    golden = File.read(GOLDEN_DIR / "#{TEST_CONFIG}.golden.svh")
    assert_equal golden, output,
      "SystemVerilog header output does not match golden file. " \
      "If this is expected, update the golden file with: ./bin/chore gen cfg-headers"
  end

  def test_cfg_gdb_xml_matches_golden
    gen = UdbGen::GenCfgGdbXmlOptions.new
    gen.extend(GeneratorTestHelper).configure_for_test(resolver: @resolver, cfg: TEST_CONFIG)
    output = gen.generate_xml
    golden = File.read(GOLDEN_DIR / "#{TEST_CONFIG}.golden.xml")
    assert_equal golden, output,
      "GDB target description output does not match golden file. " \
      "If this is expected, update the golden file with: ./bin/chore gen cfg-headers"
  end

  # The golden file pins the exact text; these pin the properties a debugger relies on,
  # so a well-formed but wrong description cannot pass by regenerating the golden.
  def test_cfg_gdb_xml_is_valid_target_description
    gen = UdbGen::GenCfgGdbXmlOptions.new
    gen.extend(GeneratorTestHelper).configure_for_test(resolver: @resolver, cfg: TEST_CONFIG)
    doc = REXML::Document.new(gen.generate_xml)

    root = doc.root
    assert_equal "target", root.name
    assert_equal "1.0", root.attributes["version"]
    assert_equal "riscv:rv32", REXML::XPath.first(doc, "/target/architecture").text

    features = REXML::XPath.match(doc, "/target/feature").map { |f| f.attributes["name"] }
    assert_includes features, "org.gnu.gdb.riscv.cpu"

    regs = REXML::XPath.match(doc, "/target/feature/reg")
    names = regs.map { |r| r.attributes["name"] }
    assert_equal names.uniq, names, "duplicate register names would be rejected by GDB"
    assert_includes names, "pc"
    assert_includes names, "priv"

    # MC100-32 has no F/D/Q and no V, so those features must be absent entirely.
    refute_includes features, "org.gnu.gdb.riscv.fpu"
    refute_includes features, "org.gnu.gdb.riscv.vector"

    # Every register must declare a positive bitsize, and no CSR may exceed MXLEN.
    regs.each do |reg|
      bitsize = Integer(reg.attributes["bitsize"])
      assert_operator bitsize, :>, 0, "#{reg.attributes["name"]} has a non-positive bitsize"
    end
    csr_regs = REXML::XPath.match(doc, "/target/feature[@name='org.gnu.gdb.riscv.csr']/reg")
    refute_empty csr_regs
    csr_regs.each do |reg|
      assert_operator Integer(reg.attributes["bitsize"]), :<=, 32,
        "#{reg.attributes["name"]} is wider than MXLEN, which a debugger cannot read in one access"
    end
  end
end
