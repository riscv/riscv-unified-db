# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "sorbet-runtime"

require_relative "database_obj"
require_relative "../fields"

module Idl
  class AstNode
    def replace_var(from, to)
      if self.is_a?(Idl::IdAst) && @name == from
        @name = to
      end
      @children.each { |child| child.replace_var(from, to) }
    end
  end
end

module Udb

  class InstructionOperandType < TopLevelDatabaseObject; end
  class InstructionOperand < TopLevelDatabaseObject

    sig { returns(InstructionOperandType) }
    def type
      @type ||= @cfg_arch.ref(@data.fetch("type").fetch("$ref"))
    end

    # a contiguous "piece" of the operand within the encoding
    class Field < EncodingField
      extend T::Sig

      sig { params(operand: InstructionOperand, loc: T.any(Integer, String, T::Range[Integer])).void }
      def initialize(operand, loc)
        super(loc)
        @operand = operand
      end

      sig { returns(String) }
      def pretty_name
        if @range.size == @operand.size_in_encoding
          @operand.pretty_name
        else
          idx_str = @operand.encoding_range_to_operand_range(@operand.size_in_encoding, @range)
          "#{@operand.pretty_name}[#{idx_str}]"
        end
      end

      def var_name
        if @range.size == @operand.size_in_encoding
          @operand.var_name
        else
          idx_str = @operand.encoding_range_to_operand_range(@operand.size_in_encoding, @range)
          "#{@operand.var_name}[#{idx_str}]"
        end
      end

      sig { returns(T::Boolean) }
      def opcode? = false
    end

    sig { override.params(resolver: Resolver).void }
    def validate(resolver)
      super(resolver)

      type_ref = T.let(@data.fetch("type").fetch("$ref"), String)
      type = @cfg_arch.ref(type_ref)
      if type.nil?
        raise SchemaValidationError.new(@data_path, "Reference '#{type_ref}' does not exist")
      end

      if @data.key("assembly(var, abi_names)")
        # call assembly_ast to type check the IDL
        assembly_ast
      end

      if @data.key("transform(var)")
        # call transform_ast to type check the IDL
        transform_ast
      end

      # check that the location makes sense
      location.fields.each_with_index do |field, idx|
        ((idx + 1)...location.fields.size).each do |other_idx|
          if location.fields.fetch(idx).overlaps?(location.fields.fetch(other_idx))
            raise SchemaValidationError.new(@data_path, "location has overlapping fields (#{location.fields.fetch(idx)} and #{location.fields.fetch(other_idx)})")
          end
        end
        next if idx.zero?

        if location.fields.fetch(idx - 1).range.max == location.fields.fetch(idx).range.min
          raise SchemaValidationError.new(@data_path, "location has consecutive bits separated by |. Use a single range (e.g., 14-12) instead.")
        end
      end

    end

    sig { returns(EncodingLocation) }
    def location = @location ||= EncodingLocation.new(@data.fetch("location"))

    sig {
      params(other: T.any(InstructionOperand, EncodingField, EncodingLocation))
      .returns(T::Boolean)
    }
    def overlaps?(other)
      case other
      when InstructionOperand
        location.overlaps?(other.location)
      when EncodingField
        other.overlaps?(location)
      when EncodingLocation
        location.overlaps?(other)
      else
        T.absurd(other)
      end
    end

    sig { returns(Integer) }
    def size_in_encoding = location.size

    sig { returns(Integer) }
    def size
      if !transform_ast.nil?
        T.cast(transform_type.width, Integer)
      elsif @data.key?("left_shift")
        location.size + @data.fetch("left_shift")
      else
        location.size
      end
    end

    sig { returns(Integer) }
    def left_shift
      @data.key?("left_shift") ? @data.fetch("left_shift") : 0
    end

    # @return Specific values that are prohibited for this operand
    sig { returns(T::Array[Integer]) }
    def excludes
      @excludes ||=
        if @data.key?("not")
          if @data.fetch("not").is_a?(Array)
            @data.fetch("not")
          else
            [@data.fetch("not")]
          end
        else
          []
        end
    end

    sig { returns(T.nilable(EncodingLocation)) }
    def dissimilar
      return nil unless @data.key?("dissimilar")

      EncodingLocation.new(@data.fetch("dissimilar"))
    end

    sig { returns(T.nilable(Idl::FunctionBodyAst)) }
    def assembly_ast
      return nil unless @data.key?("assembly(var, abi_names)")

      @assembly_ast ||= begin
        # the only things in scope are 'var' and 'abi_names'
        symtab = @cfg_arch.symtab.global_clone
        symtab.push(nil)
        symtab.add(
          "var",
          Idl::Var.new(
            "var",
            Idl::Type.new(:bits, width: size, qualifiers: [:const, :known])
          )
        )
        symtab.add(
          "abi_names",
          Idl::Var.new(
            "abi_names",
            Idl::Type.new(:boolean, qualifiers: [:const])
          )
        )
        symtab.add(
          "__expected_return_type",
          Idl::Type.new(:string)
        )
        ast = cfg_arch.idl_compiler.compile_func_body(
          @data.fetch("assembly(var, abi_names)"),
          symtab:,
          input_file: @data_path,
          input_line: source_line(["assembly(var, abi_names)"]),
          type_check: true
        )
        symtab.release
        ast
      end
    end

    # returns bits of the encoding that make up the field, as an array
    #   Each item of the array is either:
    #     - A number, to represent a single bit
    #     - A range, to represent a continugous range of bits
    #
    #  The array is ordered from encoding MSB (at index 0) to LSB (at index n-1)
    sig { returns(T::Array[T.any(Integer, T::Range[Integer])]) }
    def bits
      location.fields.map do |ef|
        ef.range.size == 1 ? ef.range.first : ef.range
      end
    end

    # return IDL code to extract the operand from $encoding
    sig { returns(String) }
    def decode_idl
      ops = []
      so_far = 0
      bits.each do |b|
        if b.is_a?(Integer)
          op = "$encoding[#{b}]"
          ops << op
          so_far += 1
        elsif b.is_a?(Range)
          op = "$encoding[#{b.end}:#{b.begin}]"
          ops << op
          so_far += T.must(b.size)
        end
      end
      ops << "#{left_shift}'d0" unless left_shift.zero?
      ops =
        if ops.size > 1
          "{#{ops.join(', ')}}"
        else
          ops.fetch(0)
        end

      if transform_ast.nil?
        ops
      else
        ast = T.must(transform_ast).deep_dup
        ast.replace_var("var", "(#{ops})")
        ast.to_idl
      end
    end

    sig { returns(T.nilable(Idl::RvalueAst)) }
    def transform_ast
      return nil unless @data.key?("transform(var)").nil?

      @transform_ast ||= begin
        # the only thing in scope is 'var'
        symtab = @cfg_arch.symtab.global_clone
        symtab.push(nil)
        symtab.add("var", Idl::Var.new("var", Idl::Type.new(:bits, width: size_in_encoding, qualifiers: [:const, :known])))
        ast = @cfg_arch.idl_compiler.compile_expression(
          @data.fetch("transform(var)"),
          symtab,
          input_file: @data_path,
          input_line: source_line(["transform(var)"])
        )
        symtab.release
        ast
      end
    end

    sig { returns(Idl::Type) }
    def transform_type
      raise "Internal error" if transform_ast.nil?

      @transform_type ||= begin
        symtab = @cfg_arch.symtab.global_clone
        symtab.push(nil)
        symtab.add(
          "var",
          Idl::Var.new(
            "var",
            Idl::Type.new(
              :bits,
              width: size_in_encoding,
              qualifiers: [:const, :known]
            )
          )
        )
        type = T.must(transform_ast).type(symtab)
        symtab.release
        type
      end
    end

    # @return Name, along with any != constraints,
    # @example
    #   pretty_name #=> "rd ≠ 0"
    #   pretty_name #=> "rd ≠ {0,2}"
    sig { returns(String) }
    def pretty_name
      @data.fetch("displayName")
    end

    sig { returns(String) }
    def var_name
      @data.fetch("varName")
    end

    sig { returns(T::Boolean) }
    def signed?
      type.signed?
    end

    # return a map, indexed by encoding position, that gives back the operand
    # position (or nil if the operand does not live there)
    # @example
    #   11-7       #=> [..., nil, 4, 3, 2, 1, 0, nil, nil, nil, nil, nil, nil, nil]
    #   2|11-7     #=> [..., nil, 4, 3, 2, 1, 0, nil, nil, nil, nil, 5, nil, nil]
    #   2|8-7|11-9 #=> [..., nil, 2, 1, 0, 4, 3, nil, nil, nil, nil, 5, nil, nil]
    sig { params(encoding_size: Integer).returns(T::Array[T.nilable(Integer)]) }
    def encoding_pos_to_operand_pos(encoding_size)
      @encoding_pos_to_operand_pos ||= begin
        s = size
        map = T.let(Array.new(encoding_size, nil), T::Array[T.nilable(Integer)])
        location.fields.each do |f|
          f.range.to_a.reverse_each do |f_i|
            raise "unexpected" if s <= 0

            map[f_i] = s - 1
            s -= 1
          end
        end
        map
      end
    end

    # given a range of the instruction, return a string representing the bits of the operand the range
    # represents
    sig { params(encoding_size: Integer, r: T::Range[Integer]).returns(String) }
    def encoding_range_to_operand_range(encoding_size, r)
      var_bits = encoding_pos_to_operand_pos(encoding_size)

      raise "?" if var_bits[r.last].nil?
      parts = [var_bits[r.last]..var_bits[r.last]]
      T.must(r.to_a.reverse[1..]).each do |i|
        if var_bits[i] == (parts.last.min - 1)
          raise "??" if parts.last.max.nil?
          parts[-1] = var_bits[i]..parts.last.max
        else
          parts << Range.new(var_bits[i], var_bits[i])
        end
      end

      parts.map { |p| p.size == 1 ? p.first.to_s : "#{p.last}:#{p.first}" }.join("|")
    end

    # @param encoding as a string of 1, 0, and - with MSB at index 0
    # @param value for the operand
    # @return encoding with the operand location replaced with value
    sig { params(encoding: String, value: Integer).returns(String) }
    def encoding_repl(encoding, value)
      new_encoding = encoding.dup
      encoding_pos_to_operand_pos(encoding.size).each_with_index do |pos, idx|
        next if pos.nil?
        raise "Bad encoding" if idx >= encoding.size

        new_encoding[encoding.size - idx - 1] = ((value >> pos) & 1).to_s
      end
      new_encoding
    end

    # array of fields, with consecutive fields merged into one, ordered msb to lsb
    # @example
    #    # given location "31|7|27-25|11-8"
    #    assert_equal 3, operand.grouped_fields.size
    #    assert_equal 31..31, operand.grouped_fields[0].range
    #    assert_equal 25..27, operand.grouped_fields[1].range
    #    assert_equal 7..11, operand.grouped_fields[2].range
    sig { returns(T::Array[Field]) }
    def grouped_fields
      @grouped_fields ||= begin
        sorted_fields = location.fields.sort { |a, b| b.range.last <=> a.range.last }
        # need to group encoding_fields if they are consecutive
        groups = [sorted_fields.fetch(0).range]
        T.must(sorted_fields[1..]).each do |f|
          if (f.range.last + 1) == groups.last.first
            groups[-1] = (f.range.first..groups.last.last)
          else
            groups << f.range
          end
        end
        if groups.size == 1
          if groups.last.size == size
            [Field.new(self, groups.fetch(0))]
          else
            [Field.new(self, groups.fetch(0))]
          end
        else
          groups.map do |f|
            Field.new(self, f)
          end
        end
      end
    end
  end
end
