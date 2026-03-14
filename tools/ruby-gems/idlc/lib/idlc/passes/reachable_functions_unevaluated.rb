# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

# finds all reachable functions from a give sequence of statements

module Idl
  class AstNode
    # @param cfg_arch [ConfiguredArchitecture] Architecture definition
    # @return [Array<FunctionBodyAst>] List of all functions that can be reached (via function calls) from this node, without considering value evaluation
    def reachable_functions_unevaluated(cfg_arch)
      seen = {}
      children.each_with_object([]) do |child, result|
        child.reachable_functions_unevaluated(cfg_arch).each do |fn|
          unless seen.key?(fn.name)
            seen[fn.name] = true
            result << fn
          end
        end
      end
    end
  end

  class FunctionCallExpressionAst
    def reachable_functions_unevaluated(cfg_arch)
      fns_by_name = {}

      if template?
        template_arg_nodes.each do |t|
          t.reachable_functions_unevaluated(cfg_arch).each { |fn| fns_by_name[fn.name] ||= fn }
        end
      end

      arg_nodes.each do |a|
        a.reachable_functions_unevaluated(cfg_arch).each { |fn| fns_by_name[fn.name] ||= fn }
      end

      func_def_ast = cfg_arch.function(name)
      raise "No function '#{name}' found in Architecture def" if func_def_ast.nil?

      func_def_ast.reachable_functions_unevaluated(cfg_arch).each { |fn| fns_by_name[fn.name] ||= fn }
      fns_by_name.values
    end
  end

  class FunctionDefAst
    def reachable_functions_unevaluated(cfg_arch)
      fns_by_name = { name => self }

      unless builtin?
        body.stmts.each do |stmt|
          stmt.reachable_functions_unevaluated(cfg_arch).each { |fn| fns_by_name[fn.name] ||= fn }
        end
      end

      fns_by_name.values
    end
  end
end
