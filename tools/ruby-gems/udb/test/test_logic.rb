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

class TestLogic < Minitest::Test
  extend T::Sig
  include Udb

  sig { returns(ConfiguredArchitecture) }
  def cfg_arch
    return @cfg_arch unless @cfg_arch.nil?

    udb_gem_root = (Pathname.new(__dir__) / "..").realpath
    @gen_path = Pathname.new(Dir.mktmpdir)
    $resolver ||= Udb::Resolver.new(
      schemas_path_override: udb_gem_root / "schemas",
      cfgs_path_override: udb_gem_root / "test" / "mock_cfgs",
      gen_path_override: @gen_path,
      std_path_override: udb_gem_root / "test" / "mock_spec" / "isa",
      quiet: false
    )
    @cfg_arch = T.let(nil, T.nilable(ConfiguredArchitecture))
    capture_io do
      @cfg_arch = $resolver.cfg_arch_for("_")
    end
    T.must(@cfg_arch)
  end

  sig { returns(ConfiguredArchitecture) }
  def partial_cfg_arch
    return @partial_cfg_arch unless @partial_cfg_arch.nil?

    udb_gem_root = (Pathname.new(__dir__) / "..").realpath
    @partial_gen_path = Pathname.new(Dir.mktmpdir)
    $resolver ||= Udb::Resolver.new(
      schemas_path_override: udb_gem_root / "schemas",
      cfgs_path_override: udb_gem_root / "test" / "mock_cfgs",
      gen_path_override: @partial_gen_path,
      std_path_override: udb_gem_root / "test" / "mock_spec" / "isa",
      quiet: false
    )
    @partial_cfg_arch = T.let(nil, T.nilable(ConfiguredArchitecture))
    capture_io do
      @partial_cfg_arch = $resolver.cfg_arch_for("little_is_better")
    end
    T.must(@partial_cfg_arch)
  end

  sig { void }
  def test_simple_or
    n =
      LogicNode.new(
        LogicNodeType::Or,
        [
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")]),
        ]
      )

    assert_equal "(A=1.0.0 OR B=1.0.0)", n.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_equal "out = (a | b)", n.to_eqntott.eqn
    assert n.satisfiable?(cfg_arch)
    assert n.cnf?
    assert_equal SatisfiedResult::Yes, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Yes : SatisfiedResult::No })
    assert_equal SatisfiedResult::Yes, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Yes : SatisfiedResult::No })
    assert_equal SatisfiedResult::Yes, n.eval_cb(proc { |_term| SatisfiedResult::Yes })
    assert_equal SatisfiedResult::No, n.eval_cb(proc { |_term| SatisfiedResult::No })
    assert_equal SatisfiedResult::Maybe, n.eval_cb(proc { |_term| SatisfiedResult::Maybe })
    assert_equal SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::No })
    assert_equal SatisfiedResult::Yes, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Yes : SatisfiedResult::Maybe })
  end

  sig { void }
  def test_simple_and
    n =
      LogicNode.new(
        LogicNodeType::And,
        [
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")]),
        ]
      )

    assert_equal "(A=1.0.0 AND B=1.0.0)", n.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_equal "out = (a & b)", n.to_eqntott.eqn
    assert n.cnf?
    assert n.satisfiable?(cfg_arch)
    assert_equal SatisfiedResult::No, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Yes : SatisfiedResult::No })
    assert_equal SatisfiedResult::No, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Yes : SatisfiedResult::No })
    assert_equal SatisfiedResult::Yes, n.eval_cb(proc { |_term| SatisfiedResult::Yes })
    assert_equal SatisfiedResult::No, n.eval_cb(proc { |_term| SatisfiedResult::No })
    assert_equal SatisfiedResult::Maybe, n.eval_cb(proc { |_term| SatisfiedResult::Maybe })
    assert_equal SatisfiedResult::No, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::No })
    assert_equal SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Yes : SatisfiedResult::Maybe })
  end

  sig { void }
  def test_simple_not
    n =
      LogicNode.new(LogicNodeType::Not, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])])

    assert_equal "NOT A=1.0.0", n.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_equal "out = !(a)", n.to_eqntott.eqn
    assert n.satisfiable?(cfg_arch)
    assert n.cnf?
    assert_equal SatisfiedResult::No, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Yes : SatisfiedResult::No })
    assert_equal SatisfiedResult::Yes, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Yes : SatisfiedResult::No })
    assert_equal SatisfiedResult::No, n.eval_cb(proc { |_term| SatisfiedResult::Yes })
    assert_equal SatisfiedResult::Yes, n.eval_cb(proc { |_term| SatisfiedResult::No })
    assert_equal SatisfiedResult::Maybe, n.eval_cb(proc { |_term| SatisfiedResult::Maybe })
    assert_equal SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::No })
  end

  sig { void }
  def test_ext_ver_convert
    term = ExtensionTerm.new("A", "=", "1.0.0")

    assert_equal cfg_arch.extension_version("A", "1.0.0"), term.to_ext_ver(cfg_arch)
    assert_equal ["name", "version"], term.to_h.keys
    assert_equal cfg_arch.extension_version("A", "1.0.0"), cfg_arch.extension_version(term.to_h["name"], term.to_h["version"].gsub("= ", ""))
  end

  sig { void }
  def test_group_by_2
    n =
      LogicNode.new(
        LogicNodeType::And,
        [
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("C", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("D", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("E", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("F", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("G", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("H", "=", "1.0.0")]),
        ]
      )

    assert_equal "(A=1.0.0 AND B=1.0.0 AND C=1.0.0 AND D=1.0.0 AND E=1.0.0 AND F=1.0.0 AND G=1.0.0 AND H=1.0.0)", n.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_equal "out = (a & b & c & d & e & f & g & h)", n.to_eqntott.eqn
    assert_equal "(((((((A=1.0.0 AND B=1.0.0) AND C=1.0.0) AND D=1.0.0) AND E=1.0.0) AND F=1.0.0) AND G=1.0.0) AND H=1.0.0)", n.group_by_2.to_s(format: LogicNode::LogicSymbolFormat::English)
  end

  sig { void }
  def test_duplicate_and_terms
    n =
      LogicNode.new(
        LogicNodeType::And,
        [
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")]),
        ]
      )

    assert_equal "(A=1.0.0 AND B=1.0.0 AND A=1.0.0 AND B=1.0.0 AND A=1.0.0 AND B=1.0.0 AND A=1.0.0 AND B=1.0.0)", n.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_equal "out = (a & b & a & b & a & b & a & b)", n.to_eqntott.eqn
    assert_equal "(((((((A=1.0.0 AND B=1.0.0) AND A=1.0.0) AND B=1.0.0) AND A=1.0.0) AND B=1.0.0) AND A=1.0.0) AND B=1.0.0)", n.group_by_2.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_includes ["(A=1.0.0 AND B=1.0.0)", "(B=1.0.0 AND A=1.0.0)"], n.espresso(LogicNode::CanonicalizationType::SumOfProducts, false).to_s(format: LogicNode::LogicSymbolFormat::English)
    assert n.equivalent?(n.espresso(LogicNode::CanonicalizationType::SumOfProducts, false), cfg_arch)
  end

  sig { void }
  def test_duplicate_or_terms
    n =
      LogicNode.new(
        LogicNodeType::Or,
        [
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")]),
        ]
      )

    assert_equal "(A=1.0.0 OR B=1.0.0 OR A=1.0.0 OR B=1.0.0 OR A=1.0.0 OR B=1.0.0 OR A=1.0.0 OR B=1.0.0)", n.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_equal "out = (a | b | a | b | a | b | a | b)", n.to_eqntott.eqn
    assert_equal "(((((((A=1.0.0 OR B=1.0.0) OR A=1.0.0) OR B=1.0.0) OR A=1.0.0) OR B=1.0.0) OR A=1.0.0) OR B=1.0.0)", n.group_by_2.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_includes ["(A=1.0.0 OR B=1.0.0)", "(B=1.0.0 OR A=1.0.0)"], n.espresso(LogicNode::CanonicalizationType::SumOfProducts, false).to_s(format: LogicNode::LogicSymbolFormat::English)
    assert n.equivalent?(n.espresso(LogicNode::CanonicalizationType::SumOfProducts, false), cfg_arch)
  end

  def test_array_param_terms
    h = {
      "name" => "SCOUNTENABLE_EN",
      "index" => 3,
      "equal" => true,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert term.to_logic_node.equivalent?(ParamCondition.new(term.to_h, cfg_arch).to_logic_tree_internal, cfg_arch)
    assert_equal "(SCOUNTENABLE_EN[3]==true)", term.to_s
    assert_equal SatisfiedResult::Yes, term.eval_value(true)
    assert_equal SatisfiedResult::No, term.eval_value(false)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "index" => 4,
      "notEqual" => true,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert term.to_logic_node.equivalent?(ParamCondition.new(term.to_h, cfg_arch).to_logic_tree_internal, cfg_arch)
    assert_equal "(SCOUNTENABLE_EN[4]!=true)", term.to_s
    assert_equal SatisfiedResult::Yes, term.eval_value(false)
    assert_equal SatisfiedResult::No, term.eval_value(true)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "index" => 4,
      "equal" => false,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert term.to_logic_node.equivalent?(ParamCondition.new(term.to_h, cfg_arch).to_logic_tree_internal, cfg_arch)
    assert_equal "(SCOUNTENABLE_EN[4]==false)", term.to_s
    assert_equal SatisfiedResult::Yes, term.eval_value(false)
    assert_equal SatisfiedResult::No, term.eval_value(true)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "index" => 4,
      "notEqual" => false,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert term.to_logic_node.equivalent?(ParamCondition.new(term.to_h, cfg_arch).to_logic_tree_internal, cfg_arch)
    assert_equal "(SCOUNTENABLE_EN[4]!=false)", term.to_s
    assert_equal SatisfiedResult::Yes, term.eval_value(true)
    assert_equal SatisfiedResult::No, term.eval_value(false)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "index" => 10,
      "lessThan" => 5,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert term.to_logic_node.equivalent?(ParamCondition.new(term.to_h, cfg_arch).to_logic_tree_internal, cfg_arch)
    assert_equal "(SCOUNTENABLE_EN[10]<5)", term.to_s
    assert_equal SatisfiedResult::Yes, term.eval_value(4)
    assert_equal SatisfiedResult::No, term.eval_value(5)
    assert_equal SatisfiedResult::No, term.eval_value(6)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "index" => 10,
      "greaterThan" => 5,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert term.to_logic_node.equivalent?(ParamCondition.new(term.to_h, cfg_arch).to_logic_tree_internal, cfg_arch)
    assert_equal "(SCOUNTENABLE_EN[10]>5)", term.to_s
    assert_equal SatisfiedResult::No, term.eval_value(4)
    assert_equal SatisfiedResult::No, term.eval_value(5)
    assert_equal SatisfiedResult::Yes, term.eval_value(6)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "index" => 10,
      "lessThanOrEqual" => 5,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert term.to_logic_node.equivalent?(ParamCondition.new(term.to_h, cfg_arch).to_logic_tree_internal, cfg_arch)
    assert_equal "(SCOUNTENABLE_EN[10]<=5)", term.to_s
    assert_equal SatisfiedResult::Yes, term.eval_value(4)
    assert_equal SatisfiedResult::Yes, term.eval_value(5)
    assert_equal SatisfiedResult::No, term.eval_value(6)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "index" => 10,
      "greaterThanOrEqual" => 5,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert term.to_logic_node.equivalent?(ParamCondition.new(term.to_h, cfg_arch).to_logic_tree_internal, cfg_arch)
    assert_equal "(SCOUNTENABLE_EN[10]>=5)", term.to_s
    assert_equal SatisfiedResult::No, term.eval_value(4)
    assert_equal SatisfiedResult::Yes, term.eval_value(5)
    assert_equal SatisfiedResult::Yes, term.eval_value(6)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "index" => 10,
      "not_a_comparison" => 5,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert_raises { term.to_s }
    assert_raises { term.eval_value(5) }
  end

  def test_scalar_param_terms
    h = {
      "name" => "SCOUNTENABLE_EN",
      "equal" => true,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert term.to_logic_node.equivalent?(ParamCondition.new(term.to_h, cfg_arch).to_logic_tree_internal, cfg_arch)
    assert_equal "(SCOUNTENABLE_EN==true)", term.to_s
    assert_equal SatisfiedResult::Yes, term.eval_value(true)
    assert_equal SatisfiedResult::No, term.eval_value(false)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "notEqual" => true,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert_equal "(SCOUNTENABLE_EN!=true)", term.to_s
    assert_equal SatisfiedResult::Yes, term.eval_value(false)
    assert_equal SatisfiedResult::No, term.eval_value(true)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "equal" => false,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert_equal "(SCOUNTENABLE_EN==false)", term.to_s
    assert_equal SatisfiedResult::Yes, term.eval_value(false)
    assert_equal SatisfiedResult::No, term.eval_value(true)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "notEqual" => false,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert_equal "(SCOUNTENABLE_EN!=false)", term.to_s
    assert_equal SatisfiedResult::Yes, term.eval_value(true)
    assert_equal SatisfiedResult::No, term.eval_value(false)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "lessThan" => 5,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert_equal "(SCOUNTENABLE_EN<5)", term.to_s
    assert_equal SatisfiedResult::Yes, term.eval_value(4)
    assert_equal SatisfiedResult::No, term.eval_value(5)
    assert_equal SatisfiedResult::No, term.eval_value(6)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "greaterThan" => 5,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert_equal "(SCOUNTENABLE_EN>5)", term.to_s
    assert_equal SatisfiedResult::No, term.eval_value(4)
    assert_equal SatisfiedResult::No, term.eval_value(5)
    assert_equal SatisfiedResult::Yes, term.eval_value(6)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "lessThanOrEqual" => 5,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert_equal "(SCOUNTENABLE_EN<=5)", term.to_s
    assert_equal SatisfiedResult::Yes, term.eval_value(4)
    assert_equal SatisfiedResult::Yes, term.eval_value(5)
    assert_equal SatisfiedResult::No, term.eval_value(6)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "greaterThanOrEqual" => 5,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert_equal "(SCOUNTENABLE_EN>=5)", term.to_s
    assert_equal SatisfiedResult::No, term.eval_value(4)
    assert_equal SatisfiedResult::Yes, term.eval_value(5)
    assert_equal SatisfiedResult::Yes, term.eval_value(6)

    h = {
      "name" => "SCOUNTENABLE_EN",
      "not_a_comparison" => 5,
      "reason" => "blah"
    }
    term = ParameterTerm.new(h)
    assert_raises { term.to_s }
    assert_raises { term.eval_value(5) }
  end

  def test_parameter_term_comparison
    # Same comparison_type with different comparison_value types (bool scalar vs bool array).
    # equal: [true, false] is schema-valid (array of booleans is permitted for equal).
    # Should not raise a TypeError and must return a stable non-nil Integer result.
    term_scalar = ParameterTerm.new("name" => "A", "equal" => true)
    term_array  = ParameterTerm.new("name" => "A", "equal" => [true, false])
    result = term_scalar <=> term_array
    refute_nil result
    assert_kind_of Integer, result

    # Sorting a mix of the two must not raise and must produce a stable order.
    terms = [term_array, term_scalar]
    terms.sort!
    assert_equal 2, terms.size

    # Two ParameterTerms with the same comparison_type (equal) but differing
    # comparison_value types (TrueClass vs FalseClass – different classes) must
    # produce a non-nil, Integer result.
    term_true  = ParameterTerm.new("name" => "A", "equal" => true)
    term_false = ParameterTerm.new("name" => "A", "equal" => false)
    result2 = term_true <=> term_false
    refute_nil result2
    assert_kind_of Integer, result2

    # Two ParameterTerms with equal: [bool, ...] arrays of different lengths must compare
    # without returning nil (true <=> false is nil in Ruby's default <=>).
    # Using equal (which allows boolean arrays) rather than oneOf (which does not).
    term_bool_arr1 = ParameterTerm.new("name" => "A", "equal" => [true])
    term_bool_arr2 = ParameterTerm.new("name" => "A", "equal" => [true, false])
    result3 = term_bool_arr1 <=> term_bool_arr2
    refute_nil result3
    assert_kind_of Integer, result3
    [term_bool_arr2, term_bool_arr1].sort!

    # Same-length equal bool arrays with different element order must also compare
    # without returning nil.
    term_bool_arr3 = ParameterTerm.new("name" => "A", "equal" => [true, false])
    term_bool_arr4 = ParameterTerm.new("name" => "A", "equal" => [false, true])
    result4 = term_bool_arr3 <=> term_bool_arr4
    refute_nil result4
    assert_kind_of Integer, result4
    [term_bool_arr3, term_bool_arr4].sort!

    # Two ParameterTerms with oneOf arrays of integers (schema-valid type) must compare.
    term_int_arr1 = ParameterTerm.new("name" => "A", "oneOf" => [1, 2])
    term_int_arr2 = ParameterTerm.new("name" => "A", "oneOf" => [1, 2, 3])
    result_oa = term_int_arr1 <=> term_int_arr2
    refute_nil result_oa
    assert_kind_of Integer, result_oa
    [term_int_arr1, term_int_arr2].sort!

    # Same-length oneOf integer arrays with different elements must also compare.
    term_int_arr3 = ParameterTerm.new("name" => "A", "oneOf" => [1, 2])
    term_int_arr4 = ParameterTerm.new("name" => "A", "oneOf" => [3, 4])
    result_ob = term_int_arr3 <=> term_int_arr4
    refute_nil result_ob
    assert_kind_of Integer, result_ob
    [term_int_arr3, term_int_arr4].sort!

    # When only one side has oneOf, comparison is ordered: oneOf > non-oneOf.
    term_one_of = ParameterTerm.new("name" => "A", "oneOf" => [1, 2])
    term_equal  = ParameterTerm.new("name" => "A", "equal" => 1)
    assert_equal  1, (term_one_of <=> term_equal)
    assert_equal(-1, (term_equal  <=> term_one_of))

    # String comparison_value: two equal-typed String terms with different values
    # must produce a stable non-nil Integer result.
    term_str1 = ParameterTerm.new("name" => "A", "equal" => "foo")
    term_str2 = ParameterTerm.new("name" => "A", "equal" => "bar")
    result5 = term_str1 <=> term_str2
    refute_nil result5
    assert_kind_of Integer, result5
    [term_str1, term_str2].sort!

    # Integer (else) comparison_value: two equal-typed Integer terms with different values.
    # Integers are the only reachable same-class, non-String, non-Array pair.
    term_int1 = ParameterTerm.new("name" => "A", "equal" => 1)
    term_int2 = ParameterTerm.new("name" => "A", "equal" => 2)
    result6 = term_int1 <=> term_int2
    refute_nil result6
    assert_kind_of Integer, result6
    [term_int1, term_int2].sort!

    # Array comparison_value: two equal-typed Array terms with different values
    # (same element class) must compare using the map-based ordering.
    term_arr1 = ParameterTerm.new("name" => "A", "equal" => [1, 2])
    term_arr2 = ParameterTerm.new("name" => "A", "equal" => [3, 4])
    result7 = term_arr1 <=> term_arr2
    refute_nil result7
    assert_kind_of Integer, result7
    [term_arr1, term_arr2].sort!
  end

  def test_bad_logic_nodes
    assert_raises { LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "1.0.0"), ExtensionTerm.new("B", "1.0.0")]) }
    assert_raises { LogicNode.new(LogicNodeType::Term, [5]) }
    assert_raises { LogicNode.new(LogicNodeType::Not, [ExtensionTerm.new("A", "1.0.0"), ExtensionTerm.new("B", "1.0.0")]) }
    assert_raises { LogicNode.new(LogicNodeType::And, [ExtensionTerm.new("A", "1.0.0")]) }
    assert_raises { LogicNode.new(LogicNodeType::Or, [ExtensionTerm.new("A", "1.0.0")]) }
    assert_raises { LogicNode.new(LogicNodeType::Xor, [ExtensionTerm.new("A", "1.0.0")]) }
    assert_raises { LogicNode.new(LogicNodeType::None, [ExtensionTerm.new("A", "1.0.0")]) }
    assert_raises { LogicNode.new(LogicNodeType::If, [ExtensionTerm.new("A", "1.0.0")]) }
    assert_raises { LogicNode.new(LogicNodeType::True, [ExtensionTerm.new("A", "1.0.0")]) }
    assert_raises { LogicNode.new(LogicNodeType::False, [ExtensionTerm.new("A", "1.0.0")]) }
  end

  def test_eval
    n = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])
    cb = LogicNode.make_eval_cb do |term|
      if term.is_a?(ExtensionTerm)
        if cfg_arch.possible_extension_versions.include?(term.to_ext_ver(cfg_arch))
          SatisfiedResult::Yes
        else
          SatisfiedResult::No
        end
      else
        term.eval(cfg_arch)
      end
    end
    assert_equal(SatisfiedResult::Yes, n.eval_cb(cb))
    assert_equal(SatisfiedResult::No, n.eval_cb(proc { |term| SatisfiedResult::No }))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| SatisfiedResult::Maybe }))

    # as of PR #891, we can no longer instatiate ExtensionVersions that are not defined
    # thus, removing this whole sequence
    # n = LogicNode.new(
    #   LogicNodeType::And,
    #   [
    #     LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
    #     LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")]) # which isn't defined
    #   ]
    # )
    # assert_equal(SatisfiedResult::No, n.eval_cb(cb))
    # assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| SatisfiedResult::Maybe }))
    # assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::Yes }))
    # assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Maybe : SatisfiedResult::Yes }))
    # assert_equal(SatisfiedResult::No, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::No }))
    # assert_equal(SatisfiedResult::No, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Maybe : SatisfiedResult::No }))


    n = LogicNode.new(
      LogicNodeType::And,
      [
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "2.1.0")])
      ]
    )
    assert_equal(SatisfiedResult::Yes, n.eval_cb(cb))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| SatisfiedResult::Maybe }))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::Yes }))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Maybe : SatisfiedResult::Yes }))
    assert_equal(SatisfiedResult::No, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::No }))
    assert_equal(SatisfiedResult::No, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Maybe : SatisfiedResult::No }))

    n = LogicNode.new(
      LogicNodeType::Or,
      [
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "2.1.0")])
      ]
    )
    assert_equal(SatisfiedResult::Yes, n.eval_cb(cb))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| SatisfiedResult::Maybe }))
    assert_equal(SatisfiedResult::Yes, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::Yes }))
    assert_equal(SatisfiedResult::Yes, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Maybe : SatisfiedResult::Yes }))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::No }))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Maybe : SatisfiedResult::No }))

    n = LogicNode.new(
      LogicNodeType::Xor,
      [
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "2.1.0")])
      ]
    )
    assert_equal(SatisfiedResult::No, n.eval_cb(cb))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| SatisfiedResult::Maybe }))
    assert_equal(
      SatisfiedResult::Maybe,
      n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::Yes })
    )
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Maybe : SatisfiedResult::Yes }))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::No }))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Maybe : SatisfiedResult::No }))


    n = LogicNode.new(
      LogicNodeType::Xor,
      [
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "2.1.0")]),
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("C", "=", "1.0")])
      ]
    )
    assert_equal(SatisfiedResult::No, n.eval_cb(cb))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| SatisfiedResult::Maybe }))
    assert_equal(
      SatisfiedResult::No,
      n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::Yes })
    )
    assert_equal(
      SatisfiedResult::No,
      n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Maybe : SatisfiedResult::Yes }))
    assert_equal(
      SatisfiedResult::No,
      n.eval_cb(proc { |term| term.name == "C" ? SatisfiedResult::Maybe : SatisfiedResult::Yes }))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::No }))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Maybe : SatisfiedResult::No }))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "C" ? SatisfiedResult::Maybe : SatisfiedResult::No }))

    n = LogicNode.new(
      LogicNodeType::None,
      [
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "2.1.0")])
      ]
    )
    assert_equal(SatisfiedResult::No, n.eval_cb(cb))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| SatisfiedResult::Maybe }))
    assert_equal(SatisfiedResult::No, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::Yes }))
    assert_equal(SatisfiedResult::No, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Maybe : SatisfiedResult::Yes }))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::No }))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Maybe : SatisfiedResult::No }))

    n = LogicNode.new(
      LogicNodeType::Not,
      [
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
      ]
    )
    assert_equal(SatisfiedResult::No, n.eval_cb(cb))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| SatisfiedResult::Maybe }))

    n = LogicNode.new(
      LogicNodeType::If,
      [
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "2.1.0")]),
      ]
    )
    assert_equal(SatisfiedResult::Yes, n.eval_cb(cb))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| SatisfiedResult::Maybe }))
    assert_equal(SatisfiedResult::Yes, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::Yes }))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Maybe : SatisfiedResult::Yes }))
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(proc { |term| term.name == "A" ? SatisfiedResult::Maybe : SatisfiedResult::No }))
    assert_equal(SatisfiedResult::Yes, n.eval_cb(proc { |term| term.name == "B" ? SatisfiedResult::Maybe : SatisfiedResult::No }))

    n = LogicNode.new(
      LogicNodeType::If,
      [
        LogicNode.new(
          LogicNodeType::Or,
          [
            LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
            LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("C", "=", "1.0")])
          ]
        ),
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "2.1.0")]),
      ]
    )
    assert_equal(SatisfiedResult::Yes, n.eval_cb(cb))
    assert_equal(SatisfiedResult::Yes, n.eval_cb(proc { |term| SatisfiedResult::No }))
    cb2 = LogicNode.make_eval_cb do |term|
      if term.to_ext_ver(cfg_arch) == cfg_arch.extension_version("A", "1.0.0")
        SatisfiedResult::Yes
      else
        SatisfiedResult::No
      end
    end
    assert_equal(SatisfiedResult::No, n.eval_cb(cb2))
    cb2 = LogicNode.make_eval_cb do |term|
      if term.to_ext_ver(cfg_arch) == cfg_arch.extension_version("C", "1.0")
        SatisfiedResult::Yes
      else
        SatisfiedResult::No
      end
    end
    assert_equal(SatisfiedResult::No, n.eval_cb(cb2))
    cb2 = LogicNode.make_eval_cb do |term|
      if term.to_ext_ver(cfg_arch) == cfg_arch.extension_version("B", "2.1.0")
        SatisfiedResult::Yes
      else
        SatisfiedResult::No
      end
    end
    assert_equal(SatisfiedResult::Yes, n.eval_cb(cb2))
    cb2 = LogicNode.make_eval_cb do |term|
      if term.to_ext_ver(cfg_arch) == cfg_arch.extension_version("A", "1.0.0") || term.to_ext_ver(cfg_arch) == cfg_arch.extension_version("B", "2.1.0")
        SatisfiedResult::Yes
      else
        SatisfiedResult::No
      end
    end
    assert_equal(SatisfiedResult::Yes, n.eval_cb(cb2))
    cb2 = LogicNode.make_eval_cb do |term|
      if term.is_a?(ExtensionTerm)
        if term.to_ext_ver(cfg_arch) == cfg_arch.extension_version("C", "1.0") || term.to_ext_ver(cfg_arch) == cfg_arch.extension_version("B", "2.1.0")
          SatisfiedResult::Yes
        else
          SatisfiedResult::No
        end
      else
        term.eval(cfg_arch.symtab)
      end
    end
    assert_equal(SatisfiedResult::Yes, n.eval_cb(cb2))

    n = LogicNode.new(LogicNodeType::True, [])
    assert_equal(SatisfiedResult::Yes, n.eval_cb(cb))
    assert_equal(SatisfiedResult::Yes, n.eval_cb(proc { |term| SatisfiedResult::No }))

    n = LogicNode.new(LogicNodeType::False, [])
    assert_equal(SatisfiedResult::No, n.eval_cb(cb))
    assert_equal(SatisfiedResult::No, n.eval_cb(proc { |term| SatisfiedResult::Yes }))

    n = LogicNode.new(LogicNodeType::Term, [ParameterTerm.new({
      "name" => "MXLEN",
      "equal" => 32,
      "reason" => "blah"
    })])
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(cb))
    cb2 = LogicNode.make_eval_cb do |term|
      if term.is_a?(ExtensionTerm)
        if partial_cfg_arch.possible_extension_versions.include?(term.to_ext_ver(partial_cfg_arch))
          SatisfiedResult::Yes
        else
          SatisfiedResult::No
        end
      else
        term.eval(partial_cfg_arch)
      end
    end
    assert_equal(SatisfiedResult::Yes, n.eval_cb(cb2))

    n = LogicNode.new(
      LogicNodeType::And,
      [
        LogicNode.new(
          LogicNodeType::Term,
          [
            ParameterTerm.new({
                                "name" => "MXLEN",
                                "equal" => 32,
                                "reason" => "blah"
                              })
          ]),
        LogicNode.new(
          LogicNodeType::Term,
          [
            ParameterTerm.new({
                                "name" => "LITTLE_IS_BETTER",
                                "equal" => true,
                                "reason" => "blah"
                              })
          ])
      ]
    )
    assert n.satisfiable?(cfg_arch)
    assert n.equivalent?(n.espresso(LogicNode::CanonicalizationType::SumOfProducts, false), cfg_arch)
    assert_equal(SatisfiedResult::Maybe, n.eval_cb(cb))
    assert_equal(SatisfiedResult::Yes, n.eval_cb(cb2))
  end

  def test_to_s
    n = LogicNode.new(LogicNodeType::True, [])
    assert_equal "1", n.to_s(format: LogicNode::LogicSymbolFormat::C)
    assert_equal "ONE", n.to_s(format: LogicNode::LogicSymbolFormat::Eqn)
    assert_equal "true", n.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_equal "true", n.to_s(format: LogicNode::LogicSymbolFormat::Predicate)

    n = LogicNode.new(LogicNodeType::False, [])
    assert_equal "0", n.to_s(format: LogicNode::LogicSymbolFormat::C)
    assert_equal "ZERO", n.to_s(format: LogicNode::LogicSymbolFormat::Eqn)
    assert_equal "false", n.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_equal "false", n.to_s(format: LogicNode::LogicSymbolFormat::Predicate)

    n = LogicNode.new(LogicNodeType::Not, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])])
    assert_equal "!A=1.0.0", n.to_s(format: LogicNode::LogicSymbolFormat::C)
    assert_equal "!A=1.0.0", n.to_s(format: LogicNode::LogicSymbolFormat::Eqn)
    assert_equal "NOT A=1.0.0", n.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_equal "\u00acA=1.0.0", n.to_s(format: LogicNode::LogicSymbolFormat::Predicate)

    n = LogicNode.new(LogicNodeType::And, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]), LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "2.1.0")])])
    assert_equal "(A=1.0.0 && B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::C)
    assert_equal "(A=1.0.0 & B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::Eqn)
    assert_equal "(A=1.0.0 AND B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_equal "(A=1.0.0 \u2227 B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::Predicate)

    n = LogicNode.new(LogicNodeType::Or, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]), LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "2.1.0")])])
    assert_equal "(A=1.0.0 || B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::C)
    assert_equal "(A=1.0.0 | B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::Eqn)
    assert_equal "(A=1.0.0 OR B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_equal "(A=1.0.0 \u2228 B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::Predicate)

    n = LogicNode.new(LogicNodeType::Xor, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]), LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "2.1.0")])])
    assert_equal "(A=1.0.0 ^ B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::C)
    assert_equal "(A=1.0.0 XOR B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_equal "(A=1.0.0 \u2295 B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::Predicate)

    n = LogicNode.new(LogicNodeType::If, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]), LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "2.1.0")])])
    assert_equal "(A=1.0.0 IMPLIES B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_equal "(A=1.0.0 \u2192 B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::Predicate)

    n = LogicNode.new(LogicNodeType::None, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]), LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "2.1.0")])])
    assert_equal "!(A=1.0.0 || B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::C)
    assert_equal "!(A=1.0.0 | B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::Eqn)
    assert_equal "NOT (A=1.0.0 OR B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::English)
    assert_equal "\u00ac(A=1.0.0 \u2228 B=2.1.0)", n.to_s(format: LogicNode::LogicSymbolFormat::Predicate)

  end

  def test_to_h
    assert LogicNode.new(LogicNodeType::True, []).to_h
    refute LogicNode.new(LogicNodeType::False, []).to_h

    a_node = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])
    assert_equal ({ "extension" => { "name" => "A", "version" => "= 1.0.0" } }), a_node.to_h
    assert_equal ({ "param" => { "name" => "A", "equal" => true } }), LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "A", "equal" => true)]).to_h

    n = LogicNode.new(LogicNodeType::Not, [a_node])
    assert_equal ({ "extension" => { "not" => { "name" => "A", "version" => "= 1.0.0" } } }), n.to_h

    n = LogicNode.new(LogicNodeType::Not, [n])
    assert_equal ({ "extension" => { "not" => { "not" => { "name" => "A", "version" => "= 1.0.0" } } } }), n.to_h

    n = LogicNode.new(LogicNodeType::Not, [LogicNode.new(LogicNodeType::Term, [ParameterTerm.new({ "name" => "A", "equal" => true, "reason" => "blah" })])])
    assert_equal ({ "param" => { "not" => { "name" => "A", "equal" => true, "reason" => "blah" } } }), n.to_h

    n = LogicNode.new(LogicNodeType::Not, [n])
    assert_equal ({ "param" => { "not" => { "not" => { "name" => "A", "equal" => true, "reason" => "blah" } } } }), n.to_h


    n = LogicNode.new(
      LogicNodeType::And,
      [
        LogicNode.new(
          LogicNodeType::Term,
          [
            ParameterTerm.new({
                                "name" => "MXLEN",
                                "equal" => 32,
                                "reason" => "blah"
                              })
          ]),
        LogicNode.new(
          LogicNodeType::Term,
          [
            ParameterTerm.new({
                                "name" => "LITTLE_IS_BETTER",
                                "equal" => true,
                                "reason" => "blah"
                              })
          ])
      ]
    )
    h = {
      "param" => {
        "allOf" => [
          { "name" => "MXLEN", "equal" => 32, "reason" => "blah" },
          { "name" => "LITTLE_IS_BETTER", "equal" => true, "reason" => "blah" }
        ]
      }
    }
    assert_equal h, n.to_h
    assert n.equivalent?(n.espresso(LogicNode::CanonicalizationType::SumOfProducts, false), cfg_arch)
    assert n.satisfiable?(cfg_arch)

    n = LogicNode.new(
      LogicNodeType::And,
      [
        LogicNode.new(
          LogicNodeType::Term,
          [
            ExtensionTerm.new("A", "=", "1.0.0")
          ]),
        LogicNode.new(
          LogicNodeType::Term,
          [
            ExtensionTerm.new("B", "=", "1.0.0")
          ])
      ]
    )
    h = {
      "extension" => {
        "allOf" => [
          { "name" => "A", "version" => "= 1.0.0" },
          { "name" => "B", "version" => "= 1.0.0" }
        ]
      }
    }
    assert_equal h, n.to_h
    assert n.equivalent?(n.espresso(LogicNode::CanonicalizationType::SumOfProducts, false), cfg_arch)
    assert n.satisfiable?(cfg_arch)

    n = LogicNode.new(
      LogicNodeType::And,
      [
        LogicNode.new(
          LogicNodeType::Term,
          [
            ParameterTerm.new({
                                "name" => "MXLEN",
                                "equal" => 32,
                                "reason" => "blah"
                              })
          ]),
        LogicNode.new(
          LogicNodeType::Term,
          [
            ExtensionTerm.new("B", "=", "1.0.0")
          ])
      ]
    )
    h = {
        "allOf" => [
          { "param" => { "name" => "MXLEN", "equal" => 32, "reason" => "blah" } },
          { "extension" => { "name" => "B", "version" => "= 1.0.0" } }
        ]
      }
    assert_equal h, n.to_h
    assert n.equivalent?(n.espresso(LogicNode::CanonicalizationType::SumOfProducts, false), cfg_arch)
    assert n.satisfiable?(cfg_arch)

    n = LogicNode.new(
      LogicNodeType::Or,
      [
        LogicNode.new(
          LogicNodeType::Term,
          [
            ParameterTerm.new({
                                "name" => "MXLEN",
                                "equal" => 32,
                                "reason" => "blah"
                              })
          ]),
        LogicNode.new(
          LogicNodeType::Term,
          [
            ParameterTerm.new({
                                "name" => "LITTLE_IS_BETTER",
                                "equal" => true,
                                "reason" => "blah"
                              })
          ])
      ]
    )
    h = {
      "param" => {
        "anyOf" => [
          { "name" => "MXLEN", "equal" => 32, "reason" => "blah" },
          { "name" => "LITTLE_IS_BETTER", "equal" => true, "reason" => "blah" }
        ]
      }
    }
    assert_equal h, n.to_h
    assert n.equivalent?(n.espresso(LogicNode::CanonicalizationType::SumOfProducts, false), cfg_arch)
    assert n.satisfiable?(cfg_arch)

    n = LogicNode.new(
      LogicNodeType::Or,
      [
        LogicNode.new(
          LogicNodeType::Term,
          [
            ExtensionTerm.new("A", "=", "1.0.0")
          ]),
        LogicNode.new(
          LogicNodeType::Term,
          [
            ExtensionTerm.new("B", "=", "1.0.0")
          ])
      ]
    )
    h = {
      "extension" => {
        "anyOf" => [
          { "name" => "A", "version" => "= 1.0.0" },
          { "name" => "B", "version" => "= 1.0.0" }
        ]
      }
    }
    assert_equal h, n.to_h
    assert n.equivalent?(n.espresso(LogicNode::CanonicalizationType::SumOfProducts, false), cfg_arch)
    assert n.satisfiable?(cfg_arch)

    n = LogicNode.new(
      LogicNodeType::Or,
      [
        LogicNode.new(
          LogicNodeType::Term,
          [
            ParameterTerm.new({
                                "name" => "MXLEN",
                                "equal" => 32,
                                "reason" => "blah"
                              })
          ]),
        LogicNode.new(
          LogicNodeType::Term,
          [
            ExtensionTerm.new("B", "=", "1.0.0")
          ])
      ]
    )
    h = {
        "anyOf" => [
          { "param" => { "name" => "MXLEN", "equal" => 32, "reason" => "blah" } },
          { "extension" => { "name" => "B", "version" => "= 1.0.0" } }
        ]
      }
    assert_equal h, n.to_h

    n = LogicNode.new(
      LogicNodeType::Xor,
      [
        LogicNode.new(
          LogicNodeType::Term,
          [
            ParameterTerm.new({
                                "name" => "MXLEN",
                                "equal" => 32,
                                "reason" => "blah"
                              })
          ]),
        LogicNode.new(
          LogicNodeType::Term,
          [
            ParameterTerm.new({
                                "name" => "LITTLE_IS_BETTER",
                                "equal" => true,
                                "reason" => "blah"
                              })
          ])
      ]
    )
    h = {
      "param" => {
        "oneOf" => [
          { "name" => "MXLEN", "equal" => 32, "reason" => "blah" },
          { "name" => "LITTLE_IS_BETTER", "equal" => true, "reason" => "blah" }
        ]
      }
    }
    assert_equal h, n.to_h

    n = LogicNode.new(
      LogicNodeType::Xor,
      [
        LogicNode.new(
          LogicNodeType::Term,
          [
            ExtensionTerm.new("A", "=", "1.0.0")
          ]),
        LogicNode.new(
          LogicNodeType::Term,
          [
            ExtensionTerm.new("B", "=", "1.0.0")
          ])
      ]
    )
    h = {
      "extension" => {
        "oneOf" => [
          { "name" => "A", "version" => "= 1.0.0" },
          { "name" => "B", "version" => "= 1.0.0" }
        ]
      }
    }
    assert_equal h, n.to_h

    n = LogicNode.new(
      LogicNodeType::Xor,
      [
        LogicNode.new(
          LogicNodeType::Term,
          [
            ParameterTerm.new({
                                "name" => "MXLEN",
                                "equal" => 32,
                                "reason" => "blah"
                              })
          ]),
        LogicNode.new(
          LogicNodeType::Term,
          [
            ExtensionTerm.new("B", "=", "1.0.0")
          ])
      ]
    )
    h = {
        "oneOf" => [
          { "param" => { "name" => "MXLEN", "equal" => 32, "reason" => "blah" } },
          { "extension" => { "name" => "B", "version" => "= 1.0.0" } }
        ]
      }
    assert_equal h, n.to_h

    n = LogicNode.new(
      LogicNodeType::None,
      [
        LogicNode.new(
          LogicNodeType::Term,
          [
            ParameterTerm.new({
                                "name" => "MXLEN",
                                "equal" => 32,
                                "reason" => "blah"
                              })
          ]),
        LogicNode.new(
          LogicNodeType::Term,
          [
            ParameterTerm.new({
                                "name" => "LITTLE_IS_BETTER",
                                "equal" => true,
                                "reason" => "blah"
                              })
          ])
      ]
    )
    h = {
      "param" => {
        "noneOf" => [
          { "name" => "MXLEN", "equal" => 32, "reason" => "blah" },
          { "name" => "LITTLE_IS_BETTER", "equal" => true, "reason" => "blah" }
        ]
      }
    }
    assert_equal h, n.to_h

    n = LogicNode.new(
      LogicNodeType::None,
      [
        LogicNode.new(
          LogicNodeType::Term,
          [
            ExtensionTerm.new("A", "=", "1.0.0")
          ]),
        LogicNode.new(
          LogicNodeType::Term,
          [
            ExtensionTerm.new("B", "=", "1.0.0")
          ])
      ]
    )
    h = {
      "extension" => {
        "noneOf" => [
          { "name" => "A", "version" => "= 1.0.0" },
          { "name" => "B", "version" => "= 1.0.0" }
        ]
      }
    }
    assert_equal h, n.to_h

    n = LogicNode.new(
      LogicNodeType::None,
      [
        LogicNode.new(
          LogicNodeType::Term,
          [
            ParameterTerm.new({
                                "name" => "MXLEN",
                                "equal" => 32,
                                "reason" => "blah"
                              })
          ]),
        LogicNode.new(
          LogicNodeType::Term,
          [
            ExtensionTerm.new("B", "=", "1.0.0")
          ])
      ]
    )
    h = {
        "noneOf" => [
          { "param" => { "name" => "MXLEN", "equal" => 32, "reason" => "blah" } },
          { "extension" => { "name" => "B", "version" => "= 1.0.0" } }
        ]
      }
    assert_equal h, n.to_h

    n = LogicNode.new(
      LogicNodeType::If,
      [
        LogicNode.new(LogicNodeType::True, []),
        LogicNode.new(
          LogicNodeType::Term,
          [
            ExtensionTerm.new("B", "=", "1.0.0")
          ])
      ]
    )

    h = {
      "if" => true,
      "then" => {
        "extension" => {
          "name" => "B", "version" => "= 1.0.0"
        }
      }
    }
    assert_equal h, n.to_h

    n = LogicNode.new(
      LogicNodeType::And,
      [
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]),
        LogicNode.new(LogicNodeType::If,
          [
            LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "2.1.0")]),
            LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("C", "=", "1.0.0")])
          ]
        ),
        LogicNode.new(LogicNodeType::If,
          [
            LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("D", "=", "2.1.0")]),
            LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("E", "=", "1.0.0")])
          ]
        ),
      ]
    )

    h = {
      "extension" => {
        "allOf" => [
          { "name" => "A", "version" => "= 1.0.0" },
          {
            "if" => { "extension" => { "name" => "B", "version" => "= 2.1.0" } },
            "then" => { "name" => "C", "version" => "= 1.0.0" }
          },
          {
            "if" => { "extension" => { "name" => "D", "version" => "= 2.1.0" } },
            "then" => { "name" => "E", "version" => "= 1.0.0" }
          }
        ]
      }
    }
    assert_equal h, n.to_h
  end

  def test_nnf
    n = LogicNode.new(
      LogicNodeType::Not,
      [
        LogicNode.new(
          LogicNodeType::Not,
          [
            LogicNode.new(
              LogicNodeType::Not,
              [
                LogicNode.new(
                  LogicNodeType::Term,
                  [
                    ExtensionTerm.new("A", "=", "1.0.0")
                  ]
                )
              ]
            )
          ]
        )
      ]
    )

    nnf_n =
      LogicNode.new(
        LogicNodeType::Not,
        [
          LogicNode.new(
            LogicNodeType::Term,
            [
              ExtensionTerm.new("A", "=", "1.0.0")
            ]
          )
        ]
      )

    assert n.nnf.nnf?
    # nnf_n is also the minimal form
    assert_equal n.espresso(LogicNode::CanonicalizationType::SumOfProducts, false).to_s, n.nnf.to_s
    assert n.equivalent?(nnf_n, cfg_arch)
    assert nnf_n.equivalent?(n, cfg_arch)

    n = LogicNode.new(
      LogicNodeType::If,
      [
        LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "A", "equal" => true, "reason" => "blah")]),
        LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "B", "equal" => true, "reason" => "blah")]),
      ]
    )

    nnf_n = LogicNode.new(
      LogicNodeType::Or,
      [
        LogicNode.new(
          LogicNodeType::Not,
          [
            LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "A", "equal" => true, "reason" => "blah")]),
          ]
        ),
        LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "B", "equal" => true, "reason" => "blah")]),
      ]
    )

    assert n.nnf.nnf?
    assert n.equivalent?(nnf_n, cfg_arch)
    assert nnf_n.equivalent?(n, cfg_arch)

    n = LogicNode.new(
      LogicNodeType::Xor,
      [
        LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "A", "equal" => true, "reason" => "blah")]),
        LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "B", "equal" => true, "reason" => "blah")]),
        LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "C", "equal" => true, "reason" => "blah")]),
      ]
    )

    nnf_n = LogicNode.new(
      LogicNodeType::Or,
      [
        LogicNode.new(
          LogicNodeType::And,
          [
            LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "A", "equal" => true, "reason" => "blah")]),
            LogicNode.new(
              LogicNodeType::Not,
              [
                LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "B", "equal" => true, "reason" => "blah")]),
              ]
            ),
            LogicNode.new(
              LogicNodeType::Not,
              [
                LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "C", "equal" => true, "reason" => "blah")]),
              ]
            )
          ]
        ),
        LogicNode.new(
          LogicNodeType::And,
          [
            LogicNode.new(
              LogicNodeType::Not,
              [
                LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "A", "equal" => true, "reason" => "blah")]),
              ]
            ),
            LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "B", "equal" => true, "reason" => "blah")]),
            LogicNode.new(
              LogicNodeType::Not,
              [
                LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "C", "equal" => true, "reason" => "blah")]),
              ]
            )
          ]
        ),
        LogicNode.new(
          LogicNodeType::And,
          [
            LogicNode.new(
              LogicNodeType::Not,
              [
                LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "A", "equal" => true, "reason" => "blah")]),
              ]
            ),
            LogicNode.new(
              LogicNodeType::Not,
              [
                LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "B", "equal" => true, "reason" => "blah")]),
              ]
            ),
            LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "C", "equal" => true, "reason" => "blah")])
          ]
        ),
      ]
    )

    assert n.nnf.nnf?
    assert n.equivalent?(nnf_n, cfg_arch)
    assert nnf_n.equivalent?(n, cfg_arch)

    n = LogicNode.new(LogicNodeType::Not, [n])

    nnf_n = LogicNode.new(
      LogicNodeType::And,
      [
        LogicNode.new(
          LogicNodeType::Or,
          [
            LogicNode.new(
              LogicNodeType::Not,
              [
                LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "A", "equal" => true, "reason" => "blah")]),
              ]
            ),
            LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "B", "equal" => true, "reason" => "blah")]),
            LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "C", "equal" => true, "reason" => "blah")]),
          ]
        ),
        LogicNode.new(
          LogicNodeType::Or,
          [
            LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "A", "equal" => true, "reason" => "blah")]),
            LogicNode.new(
              LogicNodeType::Not,
              [
                LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "B", "equal" => true, "reason" => "blah")]),
              ]
            ),
            LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "C", "equal" => true, "reason" => "blah")]),
          ]
        ),
        LogicNode.new(
          LogicNodeType::Or,
          [
            LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "A", "equal" => true, "reason" => "blah")]),
            LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "B", "equal" => true, "reason" => "blah")]),
            LogicNode.new(
              LogicNodeType::Not,
              [
                LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "C", "equal" => true, "reason" => "blah")]),
              ]
            ),
          ]
        ),
      ]
    )

    assert n.nnf.nnf?
    assert n.equivalent?(nnf_n, cfg_arch)
    assert nnf_n.equivalent?(n, cfg_arch)

    n = LogicNode.new(
      LogicNodeType::None,
      [
        LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "A", "equal" => true, "reason" => "blah")]),
        LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "B", "equal" => true, "reason" => "blah")]),
        LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "C", "equal" => true, "reason" => "blah")])
      ]
    )

    nnf_n = LogicNode.new(
      LogicNodeType::And,
      [
        LogicNode.new(LogicNodeType::Not, [LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "A", "equal" => true, "reason" => "blah")])]),
        LogicNode.new(LogicNodeType::Not, [LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "B", "equal" => true, "reason" => "blah")])]),
        LogicNode.new(LogicNodeType::Not, [LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "C", "equal" => true, "reason" => "blah")])])
      ]
    )

    assert n.nnf.nnf?
    assert n.equivalent?(nnf_n, cfg_arch)
    assert nnf_n.equivalent?(n, cfg_arch)

    n = LogicNode.new(LogicNodeType::Not, [n])

    nnf_n =
    LogicNode.new(
      LogicNodeType::Or,
      [
        LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "A", "equal" => true, "reason" => "blah")]),
        LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "B", "equal" => true, "reason" => "blah")]),
        LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "C", "equal" => true, "reason" => "blah")])
      ]
    )

    assert n.nnf.nnf?
    assert n.equivalent?(nnf_n, cfg_arch)
    assert nnf_n.equivalent?(n, cfg_arch)
  end

  def test_equivalence
    n = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])
    m = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])

    assert n.equivalent?(m, cfg_arch)
    assert m.equivalent?(n, cfg_arch)


    n = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])
    m = LogicNode.new(LogicNodeType::Term, [ParameterTerm.new("name" => "A", "equal" => true, "reason" => "blah")])

    refute n.equivalent?(m, cfg_arch)
    refute m.equivalent?(n, cfg_arch)


    n = LogicNode.new(LogicNodeType::None, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]), LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")]), LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("C", "=", "1.0.0")])])
    m = LogicNode.new(LogicNodeType::And, [LogicNode.new(LogicNodeType::Not, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])]), LogicNode.new(LogicNodeType::Not, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")])]), LogicNode.new(LogicNodeType::Not, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("C", "=", "1.0.0")])])])

    assert n.equisat_cnf.cnf?
    assert m.equisat_cnf.cnf?
    assert n.equivalent?(m, cfg_arch)
    assert m.equivalent?(n, cfg_arch)

    n = LogicNode.new(LogicNodeType::None, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")]), LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")])])
    m = LogicNode.new(LogicNodeType::And, [LogicNode.new(LogicNodeType::Not, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])]), LogicNode.new(LogicNodeType::Not, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")])])])

    assert n.equisat_cnf.cnf?
    assert m.equisat_cnf.cnf?
    assert n.equivalent?(m, cfg_arch)
    assert m.equivalent?(n, cfg_arch)


  end

  def test_prime_implicants

    mterms = ["0100", "1000", "1001", "1010", "1011", "1100", "1110", "1111"]
    res = LogicNode.find_prime_implicants(mterms, "1")
    assert_equal res.essential.sort, ["-100", "10--", "1-1-"].sort
    assert_equal res.minimal.sort, ["-100", "10--", "1-1-"].sort
    # assert false

    # @example
    #   given the equation (reqpresenting implications of the "C" extension):
    #      Zca AND (!F OR Zcf) AND (!D OR Zcd)
    #
    #   return:
    #     [
    #        { term: Zca, cond: True },
    #        { term: Zcf, cond: !F },
    #        { term: Zcd, cond: !D }
    #     ]
    t = LogicNode.new(LogicNodeType::And,
      [
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("Zca", "=", "1.0.0")]),
        LogicNode.new(LogicNodeType::Or,
          [
            LogicNode.new(LogicNodeType::Not, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("F", "=", "2.0.0")])]),
            LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("Zcf", "=", "1.0.0")])
          ]
        ),
        LogicNode.new(LogicNodeType::Or,
          [
            LogicNode.new(LogicNodeType::Not, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("D", "=", "2.0.0")])]),
            LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("Zcd", "=", "1.0.0")])
          ]
        )
      ]
    )
    mpi = t.minimize(LogicNode::CanonicalizationType::ProductOfSums)

    assert_equal 5, mpi.terms.size
    assert_equal LogicNodeType::And, mpi.type
    assert_equal 3, mpi.children.size

    assert mpi.equivalent?(t, cfg_arch)

    # @example
    #   given the equation
    #     Zca AND ((Zc1 AND Zc2) OR (!Zcond))
    #
    #   return
    #     [
    #       { term: Zca, cond True},
    #       { term: Zc1, cond: !Zcond},
    #       { term: Zc2, cond: !Zcond}
    #     ]
    t =
      LogicNode.new(LogicNodeType::And,
        [
          LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("Zca", "=", "1.0.0")]),
          LogicNode.new(
            LogicNodeType::Or,
            [
              LogicNode.new(
                LogicNodeType::And,
                [
                  LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("Zc1", "=", "1.0.0")]),
                  LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("Zc2", "=", "1.0.0")])
                ]
              ),
              LogicNode.new(
                LogicNodeType::Not,
                [
                  LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("Zcond", "=", "1.0.0")])
                ]
              )
            ]
          )
        ]
      )

    mpi = t.minimize(LogicNode::CanonicalizationType::ProductOfSums)

    assert_equal 4, mpi.terms.size
    assert_equal LogicNodeType::And, mpi.type
    assert_equal 3, mpi.children.size

    assert mpi.equivalent?(t, cfg_arch)
  end

  def node_from_json(ary, terms = {})
    case ary[0]
    when ":AND"
      LogicNode.new(LogicNodeType::And, ary[1..].map { |a| node_from_json(a, terms) })
    when ":OR"
      LogicNode.new(LogicNodeType::Or, ary[1..].map { |a| node_from_json(a, terms) })
    when ":XOR"
      LogicNode.new(LogicNodeType::Xor, ary[1..].map { |a| node_from_json(a, terms) })
    when ":NOT"
      LogicNode.new(LogicNodeType::Not, [node_from_json(ary[1], terms)])
    when ":IMPLIES"
      LogicNode.new(LogicNodeType::If, [node_from_json(ary[1], terms), node_from_json(ary[2], terms)])
    when /[a-z]/
      term = terms.key?(ary[0]) ? terms.fetch(ary[0]) : FreeTerm.new
      terms[ary[0]] ||= term
      LogicNode.new(LogicNodeType::Term, [term])
    else
      raise "unhandled: #{ary[0]}"
    end
  end

  def test_tseytin
    f = LogicNode.new(LogicNodeType::Not, [LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])])
    # assert_equal 2, f.tseytin.terms.size
    assert f.tseytin.cnf?
    assert f.satisfiable?(cfg_arch)

    f = LogicNode.new(LogicNodeType::And,
      [
        f,
        LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")])
      ]
    )
    # assert_equal 4, f.tseytin.terms.size
    assert f.tseytin.cnf?
    assert f.satisfiable?(cfg_arch)

    f = LogicNode.new(LogicNodeType::Or,
    [
      f,
      LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("C", "=", "1.0.0")])
    ]
    )
    # assert_equal 6, f.tseytin.terms.size
    assert f.tseytin.cnf?
    assert f.satisfiable?(cfg_arch)

    unsat = LogicNode.new(LogicNodeType::And, [f, LogicNode.new(LogicNodeType::Not, [f])])
    refute unsat.satisfiable?(cfg_arch)
  end

  bool_eqns = JSON.load_file(File.join(__dir__, "boolean_expressions.json"))
  bool_eqns.each_with_index do |json_eqn, index|
    define_method("test_random_#{index}") do
      LogicNode.reset_stats
      node = node_from_json(json_eqn)
      # return if (node.terms.size > 20) # z3 is too slow
      if node.satisfiable?(cfg_arch)
        # test all the transformations

        assert_equal 1, LogicNode.num_brute_force_sat_solves + LogicNode.num_z3_sat_solves

        # nnf gets covered by equiv_cnf
        # nnf = node.nnf
        # assert nnf.nnf?
        # assert node.equivalent?(nnf)

        cnf = node.equisat_cnf
        assert cnf.cnf?
        assert node.equisatisfiable?(cnf, cfg_arch)

        pos = node.minimize(LogicNode::CanonicalizationType::ProductOfSums)
        assert \
          node.equivalent?(pos, cfg_arch),
          "#{node} was minimized to #{pos}, which is not equivalent"
        assert pos.cnf?

        sop = node.minimize(LogicNode::CanonicalizationType::SumOfProducts)
        assert node.equivalent?(sop, cfg_arch)
        assert sop.dnf?
      else
        cnf = node.equisat_cnf
        assert cnf.cnf?
        assert node.equisatisfiable?(cnf, cfg_arch)

        min = node.minimize(LogicNode::CanonicalizationType::ProductOfSums)
        assert_equal \
          LogicNodeType::False,
          min.type,
          "Unsatisfiable equation #{node} did not minimize to false. Got #{min}"

        min = node.minimize(LogicNode::CanonicalizationType::SumOfProducts)
        assert_equal \
          LogicNodeType::False,
          min.type,
          "Unsatisfiable equation #{node} did not minimize to false. Got #{min}"
      end
    end
  end

  def test_failing_conjuncts_single_false_term
    n = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])
    cb = proc { |_term| SatisfiedResult::No }
    result = n.failing_conjuncts(cb)
    assert_equal 1, result.size
    assert_equal n, result.first
  end

  def test_failing_conjuncts_and_one_false
    a = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])
    b = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")])
    n = LogicNode.new(LogicNodeType::And, [a, b])
    cb = proc { |term| term.name == "A" ? SatisfiedResult::Yes : SatisfiedResult::No }
    result = n.failing_conjuncts(cb)
    assert_equal 1, result.size
    assert_equal b, result.first
  end

  def test_failing_conjuncts_and_multiple_false
    a = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])
    b = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")])
    c = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("C", "=", "1.0.0")])
    n = LogicNode.new(LogicNodeType::And, [a, b, c])
    cb = proc { |term| term.name == "A" ? SatisfiedResult::Yes : SatisfiedResult::No }
    result = n.failing_conjuncts(cb)
    assert_equal 2, result.size
    assert_includes result, b
    assert_includes result, c
  end

  def test_failing_conjuncts_or_clause_false
    a = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])
    or_clause = LogicNode.new(LogicNodeType::Or, [
      LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")]),
      LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("C", "=", "1.0.0")])
    ])
    n = LogicNode.new(LogicNodeType::And, [a, or_clause])
    # A is true, B and C are false — only the or_clause fails
    cb = proc { |term| term.name == "A" ? SatisfiedResult::Yes : SatisfiedResult::No }
    result = n.failing_conjuncts(cb)
    assert_equal 1, result.size
    assert_equal or_clause, result.first
  end

  def test_failing_conjuncts_maybe_not_reported
    a = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])
    b = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")])
    n = LogicNode.new(LogicNodeType::And, [a, b])
    cb = proc { |term| term.name == "A" ? SatisfiedResult::No : SatisfiedResult::Maybe }
    result = n.failing_conjuncts(cb)
    assert_equal 1, result.size
    assert_equal a, result.first
  end

  def test_failing_conjuncts_not_clause
    inner = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])
    n = LogicNode.new(LogicNodeType::Not, [inner])
    cb = proc { |_term| SatisfiedResult::Yes }
    result = n.failing_conjuncts(cb)
    assert_equal 1, result.size
    assert_equal n, result.first
  end

  def test_failing_conjuncts_and_all_maybe
    # AND where every child is Maybe: the whole expression is unknown, not failing
    # failing_conjuncts should return [] — nothing is definitively false
    a = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])
    b = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("B", "=", "1.0.0")])
    n = LogicNode.new(LogicNodeType::And, [a, b])
    cb = proc { |_term| SatisfiedResult::Maybe }
    result = n.failing_conjuncts(cb)
    assert_empty result
  end

  def test_failing_conjuncts_single_maybe_term
    # A single Maybe term: the expression is unknown, not failing
    # failing_conjuncts should return [self] because the non-And else branch fires,
    # but the caller (cfg_arch) only invokes failing_conjuncts when the condition is
    # != Yes, so a Maybe top-level node returns [self] to surface the unknown clause
    n = LogicNode.new(LogicNodeType::Term, [ExtensionTerm.new("A", "=", "1.0.0")])
    cb = proc { |_term| SatisfiedResult::Maybe }
    result = n.failing_conjuncts(cb)
    assert_equal 1, result.size
    assert_equal n, result.first
  end
end
