# typed: false
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

# finds all reachable functions from a give sequence of statements

module Idl
  class AstNode
    ReachableFunctionCacheType = T.type_alias { T::Hash[T::Array[T.untyped], T::Array[FunctionDefAst]] }

    # @return [Array<FunctionDefAst>] List of all functions that can be reached (via function calls) from this node
    sig {
      params(symtab: SymbolTable, cache: ReachableFunctionCacheType )
      .returns(T::Array[FunctionDefAst])
    }
    def reachable_functions(symtab, cache = T.let({}, ReachableFunctionCacheType))
      seen = {}
      children.each_with_object([]) do |child, result|
        child.reachable_functions(symtab, cache).each do |fn|
          unless seen.key?(fn.name)
            seen[fn.name] = true
            result << fn
          end
        end
      end
    end
  end

  class FunctionCallExpressionAst
    sig {
      params(symtab: SymbolTable, cache: ReachableFunctionCacheType )
      .returns(T::Array[FunctionDefAst])
    }
    def reachable_functions(symtab, cache = T.let({}, ReachableFunctionCacheType))
      func_def_type = func_type(symtab)

      body_symtab = symtab.global_clone
      body_symtab.push(func_def_type.func_def_ast)

      # Use a hash keyed by name to accumulate unique functions without repeated uniq scans
      fns_by_name = {}

      begin
        arg_nodes.each do |a|
          a.reachable_functions(symtab, cache).each { |fn| fns_by_name[fn.name] ||= fn }
        end

        unless func_def_type.builtin? || func_def_type.generated?
          avals = func_def_type.apply_arguments(body_symtab, arg_nodes, symtab, self)

          idx = [name, avals].hash

          if cache.key?(idx)
            # Use cached results from a prior traversal (e.g., same function called
            # by an earlier instruction). The sentinel [] handles recursion cycles.
            cache[idx].each { |fn| fns_by_name[fn.name] ||= fn }
          else
            cache[idx] = [] # sentinel: breaks recursion cycles before body is traversed
            body_fns = func_def_type.body.reachable_functions(body_symtab, cache)
            cache[idx] = body_fns
            body_fns.each { |fn| fns_by_name[fn.name] ||= fn }
          end
        end

        fns_by_name[func_def_type.func_def_ast.name] ||= func_def_type.func_def_ast
      ensure
        body_symtab.pop
        body_symtab.release
      end

      fns_by_name.values
    end
  end

  class StatementAst
    sig {
      params(symtab: SymbolTable, cache: ReachableFunctionCacheType )
      .returns(T::Array[FunctionDefAst])
    }
    def reachable_functions(symtab, cache = T.let({}, ReachableFunctionCacheType))
      fns = action.reachable_functions(symtab, cache)

      action.add_symbol(symtab) if action.declaration?
      value_try do
        action.execute(symtab) if action.executable?
      rescue SystemStackError
        type_error "Detected unbounded recursion during compile-time constant evaluation at #{input_file}:#{input_line}.. This recursion cannot be represented or validated."
      end
      # ok

      fns
    end
  end


  class IfAst
    sig {
      params(symtab: SymbolTable, cache: ReachableFunctionCacheType )
      .returns(T::Array[FunctionDefAst])
    }
    def reachable_functions(symtab, cache = T.let({}, ReachableFunctionCacheType))
      fns = []
      value_try do
        fns.concat if_cond.reachable_functions(symtab, cache)
        value_result = value_try do
          if (if_cond.value(symtab))
            fns.concat if_body.reachable_functions(symtab, cache)
            return fns # no need to continue
          else
            if (if_cond.text_value == "pending_and_enabled_interrupts != 0")
              warn symtab.get("pending_and_enabled_interrupts")
              raise "???"
            end
            elseifs.each do |eif|
              fns.concat eif.cond.reachable_functions(symtab, cache)
              value_result = value_try do
                if (eif.cond.value(symtab))
                  fns.concat eif.body.reachable_functions(symtab, cache)
                  return fns # no need to keep going
                end
              end
              value_else(value_result) do
                # condition isn't known; body is potentially reachable
                fns.concat eif.body.reachable_functions(symtab, cache)
              end
            end
            fns.concat final_else_body.reachable_functions(symtab, cache)
          end
        end
        value_else(value_result) do
          fns.concat if_body.reachable_functions(symtab, cache)

          elseifs.each do |eif|
            fns.concat eif.cond.reachable_functions(symtab, cache)
            value_result = value_try do
              if (eif.cond.value(symtab))
                fns.concat eif.body.reachable_functions(symtab, cache)
                return fns # no need to keep going
              end
            end
            value_else(value_result) do
              # condition isn't known; body is potentially reachable
              fns.concat eif.body.reachable_functions(symtab, cache)
            end
          end
          fns.concat final_else_body.reachable_functions(symtab, cache)
        end
      end
      return fns
    end
  end

  class ConditionalReturnStatementAst
    sig {
      params(symtab: SymbolTable, cache: ReachableFunctionCacheType )
      .returns(T::Array[FunctionDefAst])
    }
    def reachable_functions(symtab, cache = T.let({}, ReachableFunctionCacheType))
      fns = condition.is_a?(FunctionCallExpressionAst) ? condition.reachable_functions(symtab, cache) : []
      value_result = value_try do
        cv = condition.value(symtab)
        if cv
          fns.concat return_expression.reachable_functions(symtab, cache)
        end
      end
      value_else(value_result) do
        fns.concat return_expression.reachable_functions(symtab, cache)
      end

      fns
    end
  end

  class ConditionalStatementAst
    sig {
      params(symtab: SymbolTable, cache: ReachableFunctionCacheType )
      .returns(T::Array[FunctionDefAst])
    }
    def reachable_functions(symtab, cache = T.let({}, ReachableFunctionCacheType))

      fns = condition.is_a?(FunctionCallExpressionAst) ? condition.reachable_functions(symtab, cache) : []

      value_result = value_try do
        if condition.value(symtab)
          fns.concat action.reachable_functions(symtab, cache)
          # no need to execute action (return)
        end
      end
      value_else(value_result) do
        # condition not known
        fns = fns.concat action.reachable_functions(symtab, cache)
      end

      fns
    end
  end

  class ForLoopAst
    sig {
      params(symtab: SymbolTable, cache: ReachableFunctionCacheType )
      .returns(T::Array[FunctionDefAst])
    }
    def reachable_functions(symtab, cache = T.let({}, ReachableFunctionCacheType))
      symtab.push(self)
      begin
        symtab.add(init.lhs.name, Var.new(init.lhs.name, init.lhs_type(symtab)))
        fns = init.is_a?(FunctionCallExpressionAst) ? init.reachable_functions(symtab, cache) : []
        fns.concat(condition.reachable_functions(symtab, cache))
        fns.concat(update.reachable_functions(symtab, cache))
        stmts.each do |stmt|
          fns.concat(stmt.reachable_functions(symtab, cache))
        end
      ensure
        symtab.pop
      end
      fns
    end
  end
end
