# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: strict
# frozen_string_literal: true

require "forwardable"
require "sorbet-runtime"
require "udb/version_spec"
require "z3"

module Z3
  class Solver
    extend T::Sig

    # assert 'ast' and track it as 'name' in core dumps
    sig { params(ast: Z3::Expr, name: String).void }
    def assert_as(ast, name)
      reset_model!
      Z3::LowLevel.solver_assert_and_track(
        self,
        ast, Z3::Bool(name))
    end
  end
end

module Udb
  class Z3Sovler; end

  # type constraint callback for an array item
  class TypeConstraint < T::Struct
    const :mthd, Method
    const :schema, T::Hash[String, T.untyped]
  end

  # constraints for an array
  class ArrayConstraints < T::Struct
    # schema that is applied by index position
    prop :item_by_idx, T::Hash[Integer, TypeConstraint], default: {}

    # schema that is applied generally, unless there is a specific schema for the position
    prop :item_rest, T.nilable(TypeConstraint)

    # when not nil, the array must contain an item matching the JSON schema "contains"
    prop :contains, T.nilable(TypeConstraint)

    # whether or not the items must be unique
    prop :unique, T::Boolean, default: false

    # maximum number of elements
    prop :max_size, T.nilable(Integer)

    # minimum number of elements
    prop :min_size, T.nilable(Integer)
  end

  # Arrays in Z3 are unbounded, but we need to occasionally represent the length of an array
  # therefore, we use this class to model a finite-sized array as a size plus constiuent scalars
  #
  # We can't currently *truly* represent arrays with unbounded size, as that would require
  # first-order quantifiers (ForAll, Exists) that aren't currently supported by the z3 ruby bindings
  #
  # When the max array size is unpractical to model (specifically, > 64), we assume it is 64 and
  # emit an error if more are needed
  class Z3FiniteArray
    extend T::Sig

    sig {
      params(
        solver: Z3Solver,
        name: String,
        sort: T.any(T.class_of(Z3::IntSort), T.class_of(Z3::BoolSort), T.class_of(Z3::BitvecSort)),
        constraints: ArrayConstraints,
        bitvec_width: T.nilable(Integer))
      .void
    }
    def initialize(solver, name, sort, constraints, bitvec_width: nil)
      @name = name
      @solver = solver
      @subtype_sort =
        T.let(
          if sort == Z3::BitvecSort
            sort.new(T.must(bitvec_width))
          else
            sort.new
          end,
          Z3::Sort
        )
      @constraints = constraints
      @num_items =
        T.let(
          if @constraints.max_size.nil?
            64
          else
            if T.must(@constraints.max_size) > 64
              64
            else
              T.must(@constraints.max_size)
            end
          end,
          Integer
        )
      @items = T.let(
        Array.new(@num_items) { |index|
          v = @subtype_sort.var("#{@name}_idx#{index}")
          constrain_element(index, v)
        },
        T::Array[T.any(Z3::BitvecExpr, Z3::IntExpr, Z3::BoolExpr)]
      )
      # @array_term = Z3::ArraySort.new(Z3::IntSort.new, @subtype_sort).var(name)
      @size = T.let(Z3.Int("#{@name}_size"), Z3::IntExpr)
      unless @constraints.min_size.nil?
        solver.assert_as @size >= @constraints.min_size, "#{@name}_size_lower_bound"
      end
      unless @constraints.max_size.nil?
        solver.assert_as @size <= @constraints.max_size, "#{@name}_size_upper_bound"
      end
      unless @constraints.contains.nil?
        target_value = @subtype_sort.var("#{@name}_contain_value")
        T.must(@constraints.contains).mthd.call(@solver, target_value, T.must(@constraints.contains).schema, assert: true)
        exprs = @items.map do |item|
          item == target_value
        end
        solver.assert Z3.Or(exprs)
      end
      if @constraints.unique
        solver.assert Z3.Distinct(@items)
      end
    end

    sig { void }
    def pop
      # undo any assignments since the last push
    end

    sig { void }
    def push
    end

    sig { params(idx: Integer).returns(T.any(Z3::BitvecExpr, Z3::IntExpr, Z3::BoolExpr)) }
    def [](idx)
      if idx >= @num_items
        raise "array index (#{idx}) is out of bounds (#{@num_items}). May need to increase the upper limit of Z3FiniteArray from 64"
      end
      @items.fetch(idx)
    end

    # apply type constraints to array element 'v' at index 'i'
    # return 'v'
    sig { params(i: Integer, v: Z3::Expr).returns(Z3::Expr) }
    def constrain_element(i, v)
      if !@constraints.item_by_idx.empty?
        already_constrained = T.let(false, T::Boolean)
        @constraints.item_by_idx.each do |idx, typ_constr|
          if idx == i
            already_constrained = true
            assertions =
              typ_constr.mthd.call(@solver, v, typ_constr.schema, assert: false)
            assertions.each { |a| @solver.assert a }
          end
        end
        if !already_constrained && !@constraints.item_rest.nil?
          assertions =
            T.must(@constraints.item_rest).mthd.call(@solver, v, T.must(@constraints.item_rest).schema, assert: false)
          assertions.each { |a| @solver.assert a }
        end
      elsif !@constraints.item_rest.nil?
        T.must(@constraints.item_rest).mthd.call(@solver, v, T.must(@constraints.item_rest).schema)
      end
      v
    end

    # assert that there must be at least one element of the array that equals val
    sig { params(val: T.any(Integer, T::Boolean, String, Z3::Expr)).returns(Z3::BoolExpr) }
    def has_value?(val)
      exprs = @items.each_with_index.map do |i, idx|
        (i == (val.is_a?(String) ? val.hash : val)) & (@size > idx)
      end
      T.unsafe(Z3).Or(*exprs)
    end

    # equality here is defined as same elements, in the same position
    sig { params(ary: T::Array[T.any(Integer, String, T::Boolean)]).returns(Z3::BoolExpr) }
    def ==(ary)
      if ary.empty?
        @size == 0
      elsif ary.size > @num_items
        # is this a real constraint, or just a limitation of the 64 entry limit?
        if @constraints.max_size.nil?
          # this is artifical
          raise "Comparison of array larger than proof model can handle. May need to increase the 64-entry limit"
        elsif T.must(@constraints.max_size) > @num_items
          raise "Comparison of array larger than proof model can handle. May need to increase the 64-entry limit"
        else
          # ary cant' be equal, because it's larger than allowed
          return Z3.False
        end
      elsif !@constraints.min_size.nil? && (ary.size < T.must(@constraints.min_size))
        return Z3.False
      else
        exprs = ary.each_index.map do |i|
          @items.fetch(i) == (ary[i].is_a?(String) ? ary[i].hash : ary[i])
        end
        T.unsafe(Z3).And(@size == ary.size, *exprs)
      end
    end

    sig { params(ary: T::Array[T.any(Integer, String, T::Boolean)]).returns(Z3::BoolExpr) }
    def !=(ary)
      ~(self == ary)
    end

    sig { returns(Z3::IntExpr) }
    def size_term = @size

    sig { returns(T.nilable(Integer)) }
    def max_size = @constraints.max_size
  end

  # represent a parameter in Z3
  # There will only ever be one parameter term per parameter
  # When a parameter term is constructed, it adds all relevant assertions to the solver
  class Z3ParameterTerm
    extend T::Sig

    sig { returns(String) }
    attr_reader :name

    sig { returns(T.any(Z3::BoolExpr, Z3::IntExpr, Z3::BitvecExpr, Z3FiniteArray)) }
    attr_reader :term

    # construct all constraints for an integer parameter and return them
    # if `assert` is true, also assert them to the solver
    sig {
      params(
        solver: Z3Solver,
        term: Z3::BitvecExpr,
        schema_hsh: T::Hash[String, T.untyped],
        name: T.nilable(String),
        assert: T::Boolean
      )
      .returns(T::Array[Z3::BoolExpr])
    }
    def self.constrain_int(solver, term, schema_hsh, name: nil, assert: true)
      assertions = T.let([], T::Array[Z3::BoolExpr])
      if schema_hsh.key?("const")
        assertions << (term == schema_hsh.fetch("const"))
      end

      if schema_hsh.key?("enum")
        expr = (term == schema_hsh.fetch("enum")[0])
        schema_hsh.fetch("enum")[1..].each do |v|
          expr = expr | (term == v)
        end
        assertions << expr
      end

      if schema_hsh.key?("minimum")
        assertions << term.unsigned_ge(schema_hsh.fetch("minimum"))
      end

      if schema_hsh.key?("maximum")
        assertions << term.unsigned_le(schema_hsh.fetch("maximum"))
      end

      if schema_hsh.key?("allOf")
        schema_hsh.fetch("allOf").each do |subschema|
          assertions += constrain_int(solver, term, subschema, name:, assert: false)
        end
      end

      if schema_hsh.key?("anyOf")
        raise "TODO"
      end

      if schema_hsh.key?("oneOf")
        raise "TODO"
      end

      if schema_hsh.key?("noneOf")
        raise "TODO"
      end

      if schema_hsh.key?("if")
        raise "TODO"
      end

      if schema_hsh.key?("$ref")
        if schema_hsh.fetch("$ref").split("/").last == "uint32"
          assertions << term.unsigned_ge(0)
          assertions << term.unsigned_le(2**32 - 1)
        elsif schema_hsh.fetch("$ref").split("/").last == "uint64"
          assertions << term.unsigned_ge(0)
          assertions << term.unsigned_le(2**64 - 1)
        else
          raise "Unhandled schema $ref: #{schema_hsh.fetch("$ref")}"
        end
      end

      if assert
        assertions.each { |a| solver.assert a }
      end
      assertions
    end

    # assert all constraints for a boolean parameter
    sig {
      params(
        solver: Z3Solver,
        term: Z3::BoolExpr,
        schema_hsh: T::Hash[String, T.untyped],
        name: T.nilable(String),
        assert: T::Boolean
      )
      .returns(T::Array[Z3::BoolExpr])
    }
    def self.constrain_bool(solver, term, schema_hsh, name: nil, assert: true)
      assertions = T.let([], T::Array[Z3::BoolExpr])
      if schema_hsh.key?("const")
        assertions << (term == schema_hsh.fetch("const"))
      end

      if schema_hsh.key?("allOf")
        assertions += constrain_bool(solver, term, schema_hsh.fetch("allOf"), name:, assert: false)
      end

      if schema_hsh.key?("anyOf")
        raise "TODO"
      end

      if schema_hsh.key?("oneOf")
        raise "TODO"
      end

      if schema_hsh.key?("noneOf")
        raise "TODO"
      end

      if schema_hsh.key?("if")
        raise "TODO"
      end

      if assert
        assertions.each { |a| solver.assert a }
      end
      assertions
    end

    sig {
      params(
        solver: Z3Solver,
        term: Z3::IntExpr,
        schema_hsh: T::Hash[String, T.untyped],
        name: T.nilable(String),
        assert: T::Boolean
      )
      .returns(T::Array[Z3::BoolExpr])
    }
    def self.constrain_string(solver, term, schema_hsh, name: nil, assert: true)
      assertions = T.let([], T::Array[Z3::BoolExpr])
      if schema_hsh.key?("const")
        assertions << (term == schema_hsh.fetch("const").hash)
      end

      if schema_hsh.key?("enum")
        expr = (term == schema_hsh.fetch("enum")[0].hash)
        schema_hsh.fetch("enum")[1..].each do |v|
          expr = expr | (term == v.hash)
        end
        assertions << expr
      end

      if schema_hsh.key?("anyOf")
        raise "TODO"
      end

      if schema_hsh.key?("oneOf")
        raise "TODO"
      end

      if schema_hsh.key?("noneOf")
        raise "TODO"
      end

      if schema_hsh.key?("if")
        raise "TODO"
      end

      if assert
        assertions.each { |a| solver.assert a }
      end
      assertions
    end

    # assert all constraints for an array parameter
    sig {
      params(
        solver: Z3Solver,
        schema_hsh: T::Hash[String, T.untyped],
        subtype_constrain: Method,
      )
      .returns(ArrayConstraints)
    }
    def self.constrain_array(solver, schema_hsh, subtype_constrain)
      constraints = ArrayConstraints.new
      if schema_hsh.key?("items")
        if schema_hsh.fetch("items").is_a?(Array)
          schema_hsh.fetch("items").each_with_index do |item_schema, idx|
            constraints.item_by_idx[idx] = TypeConstraint.new(mthd: subtype_constrain, schema: item_schema)
          end
        elsif schema_hsh.fetch("items").is_a?(Hash)
          # just remember subtype_constrain for lazy constraints
          constraints.item_rest = TypeConstraint.new(mthd: subtype_constrain, schema: schema_hsh.fetch("items"))
        else
          raise "unexpected"
        end
      end

      if schema_hsh.key?("additionalItems") && schema_hsh.fetch("additionalItems") != false
        constraints.item_rest = TypeConstraint.new(mthd: subtype_constrain, schema: schema_hsh.fetch("additionalItems"))
      end

      if schema_hsh.key?("contains")
        constraints.contains = TypeConstraint.new(mthd: subtype_constrain, schema: schema_hsh.fetch("contains"))
      end

      if schema_hsh.key?("unique")
        constraints.unique = true
      end

      if schema_hsh.key?("maxItems")
        constraints.max_size = schema_hsh.fetch("maxItems")
      end

      if schema_hsh.key?("minItems")
        constraints.min_size = schema_hsh.fetch("minItems")
      end

      if schema_hsh.key?("anyOf")
        raise "TODO"
      end

      if schema_hsh.key?("oneOf")
        raise "TODO"
      end

      if schema_hsh.key?("noneOf")
        raise "TODO"
      end

      if schema_hsh.key?("if")
        raise "TODO"
      end
      constraints
    end

    sig { params(schema_hsh: T::Hash[String, T.untyped]).returns(Symbol) }
    def self.detect_type(schema_hsh)
      if schema_hsh.key?("type")
        case schema_hsh["type"]
        when "boolean"
          :boolean
        when "integer"
          :int
        when "string"
          :string
        when "array"
          :array
        else
          raise "Unhandled JSON schema type"
        end
      elsif schema_hsh.key?("const")
        case schema_hsh["const"]
        when TrueClass, FalseClass
          :boolean
        when Integer
          :int
        when String
          :string
        else
          raise "Unhandled const type"
        end
      elsif schema_hsh.key?("enum")
        raise "Mixed types in enum" unless schema_hsh["enum"].all? { |e| e.class == schema_hsh["enum"].fetch(0).class }

        case schema_hsh["enum"].fetch(0)
        when TrueClass, FalseClass
          :boolean
        when Integer
          :int
        when String
          :string
        else
          raise "unhandled enum type"
        end
      elsif schema_hsh.key?("allOf")
        subschema_types = schema_hsh.fetch("allOf").map { |subschema| detect_type(subschema) }

        if subschema_types.fetch(0) == :string
          raise "Subschema types do not agree" unless subschema_types[1..].all? { |t| t == :string }

          :string
        elsif subschema_types.fetch(0) == :boolean
          raise "Subschema types do not agree" unless subschema_types[1..].all? { |t| t == :boolean }

          :boolean
        elsif subschema_types.fetch(0) == :int
          raise "Subschema types do not agree" unless subschema_types[1..].all? { |t| t == :int }

          :int
        else
          raise "unhandled subschema type"
        end
      elsif schema_hsh.key?("anyOf")
        subschema_types = schema_hsh.fetch("anyOf").map { |subschema| detect_type(subschema) }

        if subschema_types.fetch(0) == :string
          raise "Subschema types do not agree" unless subschema_types[1..].all? { |t| t == :string }

          :string
        elsif subschema_types.fetch(0) == :boolean
          raise "Subschema types do not agree" unless subschema_types[1..].all? { |t| t == :boolean }

          :boolean
        elsif subschema_types.fetch(0) == :int
          raise "Subschema types do not agree" unless subschema_types[1..].all? { |t| t == :int }

          :int
        else
          raise "unhandled subschema type"
        end
      elsif schema_hsh.key?("$ref")
        if schema_hsh.fetch("$ref") == "schema_defs.json#/$defs/uint32"
          :int
        elsif schema_hsh.fetch("$ref") == "schema_defs.json#/$defs/uint64"
          :int
        else
          raise "unhandled ref: #{schema_hsh.fetch("$ref")}"
        end
      elsif schema_hsh.key?("not")
        detect_type(schema_hsh.fetch("not"))
      else
        raise "unhandled scalar schema:\n#{schema_hsh}"
      end
    end

    sig { params(schema_hsh: T::Hash[String, T.untyped]).returns(Symbol) }
    def self.detect_array_subtype(schema_hsh)
      if schema_hsh.key?("items") && schema_hsh.fetch("items").is_a?(Array)
        detect_type(schema_hsh.fetch("items")[0])
      elsif schema_hsh.key?("items")
        detect_type(schema_hsh.fetch("items"))
      else
        raise "Can't detect array subtype"
      end
    end

    sig { params(name: String, solver: Z3Solver, schema_hsh: T::Hash[String, T.untyped]).void }
    def initialize(name, solver, schema_hsh)
      @name = name
      @solver = solver
      @type = T.let(Z3ParameterTerm.detect_type(schema_hsh), Symbol)

      @term = T.let(
        case @type
        when :int
          t = Z3.Bitvec(name, 64)   # width doesn't matter here, so just make it large
          Z3ParameterTerm.constrain_int(@solver, t, schema_hsh, name:)
          t
        when :boolean
          t = Z3.Bool(name)
          Z3ParameterTerm.constrain_bool(@solver, t, schema_hsh, name:)
          t
        when :string
          t = Z3.Int(name)
          Z3ParameterTerm.constrain_string(@solver, t, schema_hsh, name:)
          t
        when :array
          subtype = Z3ParameterTerm.detect_array_subtype(schema_hsh)

          case subtype
          when :int
            constraints = Z3ParameterTerm.constrain_array(@solver, schema_hsh, Z3ParameterTerm.method(:constrain_int))
            Z3FiniteArray.new(@solver, name, Z3::BitvecSort, constraints, bitvec_width: 64)
          when :boolean
            constraints = Z3ParameterTerm.constrain_array(@solver, schema_hsh, Z3ParameterTerm.method(:constrain_bool))
            Z3FiniteArray.new(@solver, name, Z3::BoolSort, constraints)
          when :string
            constraints = Z3ParameterTerm.constrain_array(@solver, schema_hsh, Z3ParameterTerm.method(:constrain_string))
            Z3FiniteArray.new(@solver, name, Z3::IntSort, constraints)
          else
            raise "TODO"
          end
        end,
        T.any(Z3::BoolExpr, Z3::IntExpr, Z3::BitvecExpr, Z3FiniteArray)
      )
    end

    sig { returns(Z3::IntExpr) }
    def size_term
      raise "Not an array parameter" unless @term.is_a?(Z3FiniteArray)
      @term.size_term
    end

    sig { params(msb: Integer, lsb: Integer).returns(Z3::BitvecExpr) }
    def extract(msb, lsb)
      T.cast(@term, Z3::BitvecExpr).extract(msb, lsb)
    end

    sig { params(idx: Integer).returns(T.any(Z3::BoolExpr, Z3::IntExpr, Z3::BitvecExpr)) }
    def [](idx)
      unless @term.is_a?(Z3FiniteArray)
        raise "#{@name} is not an array parameter"
      end
      @term[idx]
    end

    sig { params(val: T.any(Integer, T::Boolean, String, Z3::Expr)).returns(Z3::Expr) }
    def has_value?(val)
      unless @term.is_a?(Z3FiniteArray)
        raise "#{@name} is not an array parameter"
      end
      @term.has_value?(val)
    end

    sig { params(val: T.any(Integer, String, T::Boolean, T::Array[Integer], T::Array[String], T::Array[T::Boolean])).returns(Z3::BoolExpr) }
    def ==(val)
      case val
      when String
        T.cast(@term, Z3::IntExpr) == val.hash
      when Array
        T.cast(@term, Z3FiniteArray) == val
      else
        T.cast(@term, Z3::Expr) == val
      end
    end

    sig { params(val: T.any(Integer, String, T::Boolean, T::Array[Integer], T::Array[String], T::Array[T::Boolean])).returns(Z3::BoolExpr) }
    def !=(val)
      case val
      when String
        T.cast(@term, Z3::IntExpr) != val.hash
      when Array
        T.cast(@term, Z3FiniteArray) != val
      else
        T.cast(@term, Z3::Expr) != val
      end
    end

    sig { params(val: Integer).returns(Z3::BoolExpr) }
    def <=(val)
      T.cast(@term, Z3::BitvecExpr).unsigned_le(val)
    end

    sig { params(val: Integer).returns(Z3::BoolExpr) }
    def <(val)
      T.cast(@term, Z3::BitvecExpr).unsigned_lt(val)
    end

    sig { params(val: Integer).returns(Z3::BoolExpr) }
    def >=(val)
      T.cast(@term, Z3::BitvecExpr).unsigned_ge(val)
    end

    sig { params(val: Integer).returns(Z3::BoolExpr) }
    def >(val)
      T.cast(@term, Z3::BitvecExpr).unsigned_gt(val)
    end

  end

  class Z3ExtensionRequirement
    extend T::Sig

    sig { params(name: String, req: T.any(RequirementSpec, T::Array[RequirementSpec]), solver: Z3Solver, cfg_arch: ConfiguredArchitecture).void }
    def initialize(name, req, solver, cfg_arch)
      @name = name
      @reqs = req
      @solver = solver

      @ext_req = T.let(cfg_arch.extension_requirement(name, @reqs), ExtensionRequirement)
      vers = @ext_req.satisfying_versions
      @term = T.let(
        Z3.Bool("#{name} #{@reqs.is_a?(Array) ? @reqs.map { |r| r.to_s }.join(", ") : @reqs.to_s}"),
        Z3::BoolExpr
      )
      if vers.empty?
        @solver.assert @term.implies(Z3.False)
      else
        if vers.size == 1
          @solver.assert @term.implies(@solver.ext_ver(name, vers.fetch(0).version_spec, cfg_arch).term)
        elsif vers.size == 2
          @solver.assert @term.implies(T.unsafe(Z3).Xor(*vers.map { |v| @solver.ext_ver(name, v.version_spec, cfg_arch).term }))
        else
          uneven_number_is_true = T.unsafe(Z3).Xor(*vers.map { |v| @solver.ext_ver(name, v.version_spec, cfg_arch).term })
          max_one_is_true =
            T.unsafe(Z3).And(
              *vers.combination(2).map do |pair|
                !(@solver.ext_ver(name, pair.fetch(0).version_spec, cfg_arch).term & @solver.ext_ver(name, pair.fetch(1).version_spec, cfg_arch).term)
              end
            )
          @solver.assert @term.implies(uneven_number_is_true & max_one_is_true)
        end
      end
      vers.each do |v|
        @solver.assert @solver.ext_ver(name, v.version_spec, cfg_arch).term.implies(@term)
      end
    end

    sig { returns(Z3::BoolExpr).checked(:never) }
    def term = @term
  end

  class Z3ExtensionVersion
    extend T::Sig

    sig { returns(Z3::BoolExpr) }
    attr_reader :term

    sig { params(name: String, version: VersionSpec, solver: Z3Solver, cfg_arch: ConfiguredArchitecture).void }
    def initialize(name, version, solver, cfg_arch)
      @name = name
      @solver = T.let(solver, Z3Solver)
      @term = T.let(Z3::Bool("#{name}@#{version}"), Z3::BoolExpr)
      @major_term = T.let(solver.ext_major(name), Z3::IntExpr)
      @minor_term = T.let(solver.ext_minor(name), Z3::IntExpr)
      @patch_term = T.let(solver.ext_patch(name), Z3::IntExpr)
      @pre_term = T.let(solver.ext_pre(name), Z3::BoolExpr)

      @solver.assert @term.implies(
        Z3.And(
          @major_term == version.major,
          @minor_term == version.minor,
          @patch_term == version.patch,
          @pre_term == version.pre,
        )
      )
    end

    sig { params(ver: T.any(String, VersionSpec)).returns(Z3::BoolExpr) }
    def ==(ver)
      ver_spec = ver.is_a?(VersionSpec) ? ver : VersionSpec.new(ver)

      Z3.And((@major_term == ver_spec.major), (@minor_term == ver_spec.minor), (@patch_term == ver_spec.patch), (@pre_term == ver_spec.pre))
    end

    sig { params(ver: T.any(String, VersionSpec)).returns(Z3::BoolExpr) }
    def !=(ver)
      ver_spec = ver.is_a?(VersionSpec) ? ver : VersionSpec.new(ver)

      Z3.Or((@major_term != ver_spec.major), (@minor_term != ver_spec.minor), (@patch_term != ver_spec.patch), (@pre_term != ver_spec.pre))
    end

    sig { params(ver: T.any(String, VersionSpec)).returns(Z3::BoolExpr) }
    def >=(ver)
      ver_spec = ver.is_a?(VersionSpec) ? ver : VersionSpec.new(ver)

      (self == ver) | (self > ver)
    end

    sig { params(ver: T.any(String, VersionSpec)).returns(Z3::BoolExpr) }
    def >(ver)
      ver_spec = ver.is_a?(VersionSpec) ? ver : VersionSpec.new(ver)

      e =
        Z3.Or(
          (@major_term > ver_spec.major),
          ((@major_term == ver_spec.major) & (@minor_term > ver_spec.minor)),
          Z3.And((@major_term == ver_spec.major), (@minor_term == ver_spec.minor), (@patch_term > ver_spec.patch))
        )
      if ver_spec.pre
        e & Z3.And((@major_term == ver_spec.major), (@minor_term == ver_spec.minor), (@patch_term == ver_spec.patch), (!@pre_term))
      else
        e
      end
    end

    sig { params(ver: T.any(String, VersionSpec)).returns(Z3::BoolExpr) }
    def <=(ver)
      ver_spec = ver.is_a?(VersionSpec) ? ver : VersionSpec.new(ver)

      (self == ver) | (self < ver)
    end

    sig { params(ver: T.any(String, VersionSpec)).returns(Z3::BoolExpr) }
    def <(ver)
      ver_spec = ver.is_a?(VersionSpec) ? ver : VersionSpec.new(ver)

      e =
        Z3.Or(
          (@major_term < ver_spec.major),
          ((@major_term == ver_spec.major) & (@minor_term < ver_spec.minor)),
          Z3.And((@major_term == ver_spec.major), (@minor_term == ver_spec.minor), (@patch_term < ver_spec.patch))
        )
      if ver_spec.pre
        e
      else
        e & Z3.And((@major_term == ver_spec.major), (@minor_term == ver_spec.minor), (@patch_term == ver_spec.patch), (@pre_term))
      end
    end
  end

  class Z3Solver
    extend T::Sig
    extend Forwardable

    def_delegators :@solver,
      :assert, :assert_as,
      :prove!, :assertions,
      :check, :satisfiable?, :unsatisfiable?,
      :model

    sig { returns(Z3::Solver) }
    attr_reader :solver

    sig { void }
    def initialize
      @solver = T.let(Z3::Solver.new, Z3::Solver)
      @ext_vers = T.let([{}], T::Array[T::Hash[String, Z3ExtensionVersion]])
      @ext_reqs = T.let([{}], T::Array[T::Hash[String, Z3ExtensionRequirement]])
      @param_terms = T.let([{}], T::Array[T::Hash[String, Z3ParameterTerm]])

      @ext_majors = T.let([{}], T::Array[T::Hash[String, Z3::IntExpr]])
      @ext_minors = T.let([{}], T::Array[T::Hash[String, Z3::IntExpr]])
      @ext_patches = T.let([{}], T::Array[T::Hash[String, Z3::IntExpr]])
      @ext_pres = T.let([{}], T::Array[T::Hash[String, Z3::BoolExpr]])

      @xlen = T.let(nil, T.nilable(Z3::IntExpr))
    end

    sig { void }
    def pop
      if @ext_vers.size == 1
        Udb.logger.error "Popping solver at base level"
        raise
      end
      @ext_vers.pop
      @ext_reqs.pop
      @param_terms.pop
      @ext_majors.pop
      @ext_minors.pop
      @ext_patches.pop
      @ext_pres.pop
      @solver.pop
    end

    sig { void }
    def push
      @ext_vers.push({})
      @ext_reqs.push({})
      @param_terms.push({})
      @ext_majors.push({})
      @ext_minors.push({})
      @ext_patches.push({})
      @ext_pres.push({})
      @solver.push
    end

    sig { returns(Z3::IntExpr) }
    def xlen
      unless @xlen
        @xlen = Z3.Int("xlen")
        @solver.assert_as((@xlen == 32) | (@xlen == 64), "_pxlen")
      end
      @xlen
    end

    sig { params(name: String, version: T.any(String, VersionSpec), cfg_arch: ConfiguredArchitecture).returns(Z3ExtensionVersion) }
    def ext_ver(name, version, cfg_arch)
      version_spec = version.is_a?(VersionSpec) ? version : VersionSpec.new(version)
      key = [name, version_spec].hash
      @ext_vers.reverse_each do |h|
        if h.key?(key)
          return h.fetch(key)
        end
      end
      ev = Z3ExtensionVersion.new(name, version_spec, self, cfg_arch)
      T.must(@ext_vers.last)[key] = ev
      ev
    end

    sig { params(name: String, req: T.any(RequirementSpec, T::Array[RequirementSpec]), cfg_arch: ConfiguredArchitecture).returns(Z3ExtensionRequirement) }
    def ext_req(name, req, cfg_arch)
      key = [name, req].hash
      @ext_reqs.reverse_each do |h|
        if h.key?(key)
          return h.fetch(key)
        end
      end
      T.must(@ext_reqs.last)[key] ||= Z3ExtensionRequirement.new(name, req, self, cfg_arch)
    end

    sig { params(name: String).returns(Z3::IntExpr) }
    def ext_major(name)
      @ext_majors.reverse_each do |h|
        if h.key?(name)
          return h.fetch(name)
        end
      end
      T.must(@ext_majors.last)[name] ||= Z3.Int("#{name}_major")
    end

    sig { params(name: String).returns(Z3::IntExpr) }
    def ext_minor(name)
      @ext_minors.reverse_each do |h|
        if h.key?(name)
          return h.fetch(name)
        end
      end
      T.must(@ext_minors.last)[name] ||= Z3.Int("#{name}_minor")
    end

    sig { params(name: String).returns(Z3::IntExpr) }
    def ext_patch(name)
      @ext_patches.reverse_each do |h|
        if h.key?(name)
          return h.fetch(name)
        end
      end
      T.must(@ext_patches.last)[name] ||= Z3.Int("#{name}_patch")
    end

    sig { params(name: String).returns(Z3::BoolExpr) }
    def ext_pre(name)
      @ext_pres.reverse_each do |h|
        if h.key?(name)
          return h.fetch(name)
        end
      end
      T.must(@ext_pres.last)[name] ||= Z3.Bool("#{name}_pre")
    end


    sig { params(name: String, schema_hsh: T::Hash[String, T.untyped]).returns(Z3ParameterTerm) }
    def param(name, schema_hsh)
      @param_terms.reverse_each do |h|
        if h.key?(name)
          return h.fetch(name)
        end
      end
      T.must(@param_terms.last)[name] = Z3ParameterTerm.new(name, self, schema_hsh)
    end
  end
end
