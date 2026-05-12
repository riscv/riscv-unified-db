# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

module Idl
  class ComplexRegDetermination < RuntimeError
  end

  class AstNode
    def find_src_registers(symtab)
      # if executable?
      #   value_result = value_try do
      #     execute(symtab)
      #   end
      #   value_else(value_result) do
      #     execute_unknown(symtab)
      #   end
      # end
      add_symbol(symtab) if declaration?

      srcs = []
      @children.each do |child|
        srcs.concat(child.find_src_registers(symtab))
      end
      srcs.uniq
    end

    def find_dst_registers(symtab)
      # if executable?
      #   value_result = value_try do
      #     execute(symtab)
      #   end
      #   value_else(value_result) do
      #     execute_unknown(symtab)
      #   end
      # end
      add_symbol(symtab) if declaration?

      srcs = []
      @children.each do |child|
        srcs.concat(child.find_dst_registers(symtab))
      end
      srcs.uniq
    end
  end

  class ForLoopAst
    # we don't unroll, but we don't add the index variable to the symtab, either
    # that will cause any register accesses dependent on the index variable to raise Complex
    def find_src_registers(symtab)
      srcs = init.find_src_registers(symtab)
      # don't add init to the symtab, since we don't want to use it...
      srcs += condition.find_src_registers(symtab)

      stmts.each do |stmt|
        srcs += stmt.find_src_registers(symtab)
      end
      srcs += update.find_src_registers(symtab)

      srcs
    end

    # we don't unroll, but we don't add the index variable to the symtab, either
    # that will cause any register accesses dependent on the index variable to raise Complex
    def find_dst_registers(symtab)
      dsts = init.find_dst_registers(symtab)
      # don't add init to the symtab, since we don't want to use it...
      dsts += condition.find_dst_registers(symtab)

      stmts.each do |stmt|
        dsts += stmt.find_dst_registers(symtab)
      end
      dsts += update.find_dst_registers(symtab)

      dsts
    end
  end

  class AryElementAccessAst
    def find_src_registers(symtab)
      value_result = value_try do
        var_type = var.type(symtab) rescue nil
        if var_type&.kind == :array && var_type.sub_type.is_a?(RegFileElementType) && var_type.qualifiers.include?(:global)
          rf_name = var_type.sub_type.name
          return [[rf_name, index.value(symtab)]]
        else
          return []
        end
      end
      value_else(value_result) do
        var_type = var.type(symtab) rescue nil
        if var_type&.kind == :array && var_type.sub_type.is_a?(RegFileElementType) && var_type.qualifiers.include?(:global)
          rf_name = var_type.sub_type.name
          if index.type(symtab).const?
            return [[rf_name, index.gen_cpp(symtab, 0)]]
          else
            raise ComplexRegDetermination
          end
        else
          return []
        end
      end
    end
  end

  class AryElementAssignmentAst
    def find_dst_registers(symtab)
      # Identify the base variable and the register index based on assignment shape.
      # F[rd] = v    → lhs is IdAst(F),              reg_idx = idx
      # F[rd][b] = v → lhs is AryElementAccessAst(F[rd]), reg_idx = lhs.index
      lhs_base, reg_idx =
        if lhs.is_a?(Idl::IdAst)
          [lhs, idx]
        elsif lhs.is_a?(Idl::AryElementAccessAst) && lhs.var.is_a?(Idl::IdAst)
          [lhs.var, lhs.index]
        else
          return []
        end

      # Only proceed if the base variable is a global array of RegFileElementType.
      var_type = lhs_base.type(symtab) rescue nil
      return [] unless var_type&.kind == :array &&
                       var_type.sub_type.is_a?(RegFileElementType) &&
                       var_type.qualifiers.include?(:global)

      rf_name = var_type.sub_type.name

      value_result = value_try do
        return [[rf_name, reg_idx.value(symtab)]]
      end
      value_else(value_result) do
        if reg_idx.type(symtab).const?
          return [[rf_name, reg_idx.gen_cpp(symtab, 0)]]
        else
          raise ComplexRegDetermination
        end
      end
    end
  end

  class AryRangeAssignmentAst
    def find_dst_registers(symtab)
      return [] unless variable.is_a?(Idl::AryElementAccessAst)

      var_type = variable.var.type(symtab) rescue nil
      return [] unless var_type&.kind == :array &&
                       var_type.sub_type.is_a?(RegFileElementType) &&
                       var_type.qualifiers.include?(:global)

      rf_name = var_type.sub_type.name

      value_result = value_try do
        return [[rf_name, variable.index.value(symtab)]]
      end
      value_else(value_result) do
        if variable.index.type(symtab).const?
          return [[rf_name, variable.index.gen_cpp(symtab, 0)]]
        else
          raise ComplexRegDetermination
        end
      end
    end
  end
end
