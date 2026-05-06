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
      base_name = Idl::AstNode.extract_base_var_name(lhs)
      return [] unless base_name == "X"

      if lhs.is_a?(Idl::IdAst) && lhs.name == "X"
        # Direct X register assignment: X[idx] = val
        reg_idx = idx
      elsif lhs.is_a?(Idl::AryElementAccessAst) && lhs.var.is_a?(Idl::IdAst) && lhs.var.name == "X"
        # Nested X register access: X[rs1][bit] = val — register is lhs.index
        reg_idx = lhs.index
      else
        raise ComplexRegDetermination
      end

      value_result = value_try do
        var_type = lhs.type(symtab) rescue nil
        if var_type&.kind == :array && var_type.sub_type.is_a?(RegFileElementType) && var_type.qualifiers.include?(:global)
          rf_name = var_type.sub_type.name
          return [[rf_name, reg_idx.value(symtab)]]
        else
          return []
        end
      end
      value_else(value_result) do
        var_type = lhs.type(symtab) rescue nil
        if var_type&.kind == :array && var_type.sub_type.is_a?(RegFileElementType) && var_type.qualifiers.include?(:global)
          rf_name = var_type.sub_type.name
          if reg_idx.type(symtab).const?
            return [[rf_name, reg_idx.gen_cpp(symtab, 0)]]
          else
            raise ComplexRegDetermination
          end
        else
          raise ComplexRegDetermination
        end
      end
    end
  end

  class AryRangeAssignmentAst
    def find_dst_registers(symtab)
      # Check if this is an X register assignment
      base_name = Idl::AstNode.extract_base_var_name(variable)
      if base_name == "X"
        # For X[idx][msb:lsb] = val, we need the idx
        if variable.is_a?(Idl::AryElementAccessAst) && variable.var.is_a?(Idl::IdAst) && variable.var.name == "X"
          # Direct X register access: X[idx][msb:lsb] = val
          value_result = value_try do
            return [variable.index.value(symtab)]
          end
          value_else(value_result) do
            if variable.index.type(symtab).const?
              return [variable.index.gen_cpp(symtab, 0)]
            else
              raise ComplexRegDetermination
            end
          end
        else
          # More complex X register nesting
          raise ComplexRegDetermination
        end
      else
        return []
      end
    end
  end
end
