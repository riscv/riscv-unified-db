# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require_relative "ast"

module Idl
  # Builds an idlc AST from a tree-sitter parse tree, producing the same
  # structure as the Treetop-based parser.
  class TsAstBuilder
    def initialize(source)
      @source = source
    end

    # @param node [TreeSitter::Node] root node of a tree-sitter parse tree
    # @return [AstNode]
    def build(node)
      return nil if node.nil? || node.null?
      visit(node)
    end

    private

    def visit(node)
      return nil if node.nil? || node.null?
      send(:"visit_#{node.type}", node)
    rescue NoMethodError
      loc = "#{node.type} at #{node.start_point.row + 1}:#{node.start_point.column + 1}"
      ctx = @source[node.start_byte...node.end_byte].inspect
      raise "TsAstBuilder: no visitor for #{loc} (text: #{ctx[0..40]})"
    end

    def iv(node)
      node.start_byte...node.end_byte
    end

    # --- Transparent wrappers ------------------------------------------------

    # Comments are extras and appear as named children; skip them to find content.
    # Any comment nodes that immediately precede the content node (with no blank
    # line between) are attached as leading comments on the first statement of the
    # returned body, matching how attach_comments_to_siblings works inside a block.
    def visit_source_file(node)
      ts_kids = all_named_children(node)
      content_idx = ts_kids.index { |c| c.type != :comment }
      return nil if content_idx.nil?

      result = visit(ts_kids[content_idx])

      if result.respond_to?(:stmts) && result.stmts.any?
        leading = ts_kids[0...content_idx].select { |c| c.type == :comment }
        first_stmt = result.stmts.first
        leading.each do |c|
          next if blank_line_between?(c.end_point.row, ts_kids[content_idx].start_point.row)
          first_stmt.attach_leading_comment(CommentAst.new(@source, iv(c), node_text(c)))
        end
      end

      result
    end
    def visit_expression_root(node) = visit(node.named_child(0))
    def visit_expression(node)      = visit(node.named_child(0))

    def visit_unary_expression(node)
      if node.child_count == 1
        visit(node.child(0))
      else
        op   = @source[node.child(0).start_byte...node.child(0).end_byte]
        expr = visit(node.named_child(0))
        UnaryOperatorExpressionAst.new(@source, iv(node), op, expr)
      end
    end

    def visit_postfix_expression(node) = visit(node.named_child(0))
    def visit_primary_expression(node) = visit(node.named_child(0))

    # --- Literals ------------------------------------------------------------

    def visit_true_literal(node)
      TrueExpressionAst.new(@source, iv(node))
    end

    def visit_false_literal(node)
      FalseExpressionAst.new(@source, iv(node))
    end

    def visit_int_literal(node)
      text = @source[node.start_byte...node.end_byte]
      IntLiteralAst.new(@source, iv(node), text)
    end

    # --- Identifiers ---------------------------------------------------------

    def visit_identifier(node)
      IdAst.new(@source, iv(node), @source[node.start_byte...node.end_byte])
    end

    def visit_type_identifier(node)
      IdAst.new(@source, iv(node), @source[node.start_byte...node.end_byte])
    end

    # --- Expressions ---------------------------------------------------------

    def visit_binary_expression(node)
      # Comments may appear as named children between the operands; skip them.
      exprs = named_children(node).reject { |c| c.type == :comment }
      left  = visit(exprs[0])
      right = visit(exprs[1])
      # The operator is always an anonymous (non-named) child.
      op = nil
      node.child_count.times do |i|
        c = node.child(i)
        next if c.named? || c.null?
        op = node_text(c)
        break
      end
      BinaryExpressionAst.new(@source, iv(node), left, op, right)
    end

    def visit_ternary_expression(node)
      cond  = visit(node.named_child(0))
      true_expr  = visit(node.named_child(1))
      false_expr = visit(node.named_child(2))
      TernaryOperatorExpressionAst.new(@source, iv(node), cond, true_expr, false_expr)
    end

    def visit_paren_expression(node)
      ParenExpressionAst.new(@source, iv(node), visit(node.named_child(0)))
    end

    # --- Statements ----------------------------------------------------------

    def visit_statement_list(node)
      ts_kids  = all_named_children(node)
      ast_kids = ts_kids.reject { |c| c.type == :comment }.map { |c| visit(c) }
      attach_comments_to_siblings(ts_kids, ast_kids)
      FunctionBodyAst.new(@source, iv(node), ast_kids)
    end

    def visit_body_statement(node) = visit(node.named_child(0))

    def visit_statement(node)
      action = visit(node.named_child(0))
      if node.named_child_count == 2
        cond = visit(node.named_child(1))
        ConditionalStatementAst.new(@source, iv(node), action, cond)
      else
        StatementAst.new(@source, iv(node), action)
      end
    end

    def visit_action(node)     = visit(node.named_child(0))
    def visit_assignment(node) = visit(node.named_child(0))

    # --- Type names ----------------------------------------------------------

    BUILTIN_TYPE_NAMES = %w[Bits XReg Boolean U32 U64 String].freeze

    def visit_type_name(node)
      # For Bits<N>, child(0) is the 'Bits' keyword token.
      # For non-parameterized types (Boolean, XReg, etc.), the node is a leaf.
      type_kw = node_text(node.child_count > 0 ? node.child(0) : node)
      width = node.named_child_count > 0 ? visit(node.named_child(0)) : nil
      if BUILTIN_TYPE_NAMES.include?(type_kw)
        BuiltinTypeNameAst.new(@source, iv(node), type_kw, width)
      else
        UserTypeNameAst.new(@source, iv(node), type_kw)
      end
    end

    def visit_template_expression(node) = visit(node.named_child(0))
    def visit_template_binary_expression(node)
      left  = visit(node.named_child(0))
      op    = @source[node.child(1).start_byte...node.child(1).end_byte]
      right = visit(node.named_child(1))
      BinaryExpressionAst.new(@source, iv(node), left, op, right)
    end

    # --- Declarations --------------------------------------------------------

    def visit_declaration(node)
      first = node.named_child(0)
      if first.type == :single_declaration
        visit_single_declaration(first)
      else
        # Multi-variable declaration: type_name followed by two or more identifiers
        type_ast = visit(first)
        id_asts  = named_children(node).drop(1).map { |n| visit_as_id(n) }
        MultiVariableDeclarationAst.new(@source, iv(node), type_ast, id_asts)
      end
    end

    def visit_single_declaration(node)
      type_ast = visit(node.named_child(0))
      id_ast   = visit(node.named_child(1))
      ary_size = node.named_child_count > 2 ? visit(node.named_child(2)) : nil
      VariableDeclarationAst.new(@source, iv(node), type_ast, id_ast, ary_size)
    end

    def visit_single_declaration_with_initialization(node)
      type_ast  = visit(node.named_child(0))
      id_ast    = visit(node.named_child(1))
      # named_child(2) is either array_size or the value expression
      if node.named_child_count == 4
        ary_size  = visit(node.named_child(2))
        value_ast = visit(node.named_child(3))
      else
        ary_size  = nil
        value_ast = visit(node.named_child(2))
      end
      VariableDeclarationWithInitializationAst.new(
        @source, iv(node), type_ast, id_ast, ary_size, value_ast, false
      )
    end

    def visit_for_loop_iteration_variable_declaration(node)
      type_ast  = visit(node.named_child(0))
      id_ast    = visit(node.named_child(1))
      value_ast = visit(node.named_child(2))
      VariableDeclarationWithInitializationAst.new(
        @source, iv(node), type_ast, id_ast, nil, value_ast, true
      )
    end

    # --- Post-increment / decrement ------------------------------------------

    def visit_post_increment_expression(node)
      PostIncrementExpressionAst.new(@source, iv(node), visit(node.named_child(0)))
    end

    def visit_post_decrement_expression(node)
      PostDecrementExpressionAst.new(@source, iv(node), visit(node.named_child(0)))
    end

    # --- Subscript access ----------------------------------------------------

    def visit_subscript_expression(node)
      var = visit(node.named_child(0))  # primary_expression
      # Collect (index, lsb?) pairs by scanning [ ] boundaries so that
      # chained subscripts like arr[0][3:0] are handled correctly.
      pairs = []
      in_bracket = false
      cur_idx = cur_lsb = nil
      node.child_count.times do |i|
        c = node.child(i)
        next if c.null?
        if !c.named? && node_text(c) == "["
          in_bracket = true; cur_idx = cur_lsb = nil
        elsif !c.named? && node_text(c) == "]"
          pairs << [cur_idx, cur_lsb] if cur_idx
          in_bracket = false
        elsif in_bracket && c.named?
          case node.field_name_for_child(i)
          when "index" then cur_idx = visit(c)
          when "lsb"   then cur_lsb = visit(c)
          end
        end
      end
      pairs.each do |idx, lsb|
        var = lsb ? AryRangeAccessAst.new(@source, iv(node), var, idx, lsb)
                  : AryElementAccessAst.new(@source, iv(node), var, idx)
      end
      var
    end

    # --- Conditional statement / return --------------------------------------

    def visit_statement(node)
      # Filter comments — they may appear between action and the `if` guard.
      parts = named_children(node).reject { |c| c.type == :comment }
      action = visit(parts[0])
      if parts.size >= 2
        cond = visit(parts[1])
        ConditionalStatementAst.new(@source, iv(node), action, cond)
      else
        StatementAst.new(@source, iv(node), action)
      end
    end

    def visit_return_statement(node)
      parts = named_children(node).reject { |c| c.type == :comment }
      ret_expr = visit(parts[0])
      if parts.size >= 2
        cond = visit(parts[1])
        ConditionalReturnStatementAst.new(@source, iv(node), ret_expr, cond)
      else
        ReturnStatementAst.new(@source, iv(node), ret_expr)
      end
    end

    # --- If statement --------------------------------------------------------

    def visit_if_statement(node)
      children = named_children(node)
      # First pair: if_condition + statement_block
      if_cond = visit(children[0].named_child(0))   # expression inside if_condition
      if_body = make_if_body(children[1])

      elseifs = []
      final_else = nil
      i = 2
      while i < children.size
        if children[i].type == :if_condition
          elseif_cond  = visit(children[i].named_child(0))
          elseif_block = children[i + 1]
          elseifs << ElseIfAst.new(@source, iv(children[i]), iv(elseif_block),
                                   elseif_cond, block_stmts(elseif_block))
          i += 2
        else
          final_else = make_if_body(children[i])
          i += 1
        end
      end

      final_else ||= IfBodyAst.new(@source, 0...0, [])
      IfAst.new(@source, iv(node), if_cond, if_body, elseifs, final_else)
    end

    def make_if_body(block_node)
      stmts = block_stmts(block_node)
      # Treetop's IfBodyAst interval covers only the content inside the braces:
      # from the first statement's start_byte up to (but not including) the '}'.
      content_iv = if stmts.empty?
        0...0
      else
        block_node.named_child(0).start_byte...(block_node.end_byte - 1)
      end
      IfBodyAst.new(@source, content_iv, stmts)
    end

    def block_stmts(block_node)
      ts_kids  = all_named_children(block_node)
      ast_kids = ts_kids.reject { |c| c.type == :comment }.filter_map { |c| visit(c) }
      attach_comments_to_siblings(ts_kids, ast_kids)
      ast_kids
    end

    # --- For loop ------------------------------------------------------------

    def visit_for_loop(node)
      children = named_children(node)
      init      = visit(children[0])   # for_loop_iteration_variable_declaration
      condition = visit(children[1])   # expression
      update    = visit(children[2])   # post_increment / post_decrement / assignment
      stmts     = block_stmts(children[3])  # statement_block
      ForLoopAst.new(@source, iv(node), init, condition, update, stmts)
    end

    def visit_variable_assignment(node)
      lhs = visit(node.named_child(0))
      rhs = visit(node.named_child(1))
      VariableAssignmentAst.new(@source, iv(node), lhs, rhs)
    end

    def visit_return_statement(node)
      ret_expr = visit(node.named_child(0))
      if node.named_child_count == 2
        cond = visit(node.named_child(1))
        ConditionalReturnStatementAst.new(@source, iv(node), ret_expr, cond)
      else
        ReturnStatementAst.new(@source, iv(node), ret_expr)
      end
    end

    def visit_return_expression(node)
      exprs = named_children(node).map { |c| visit(c) }
      ReturnExpressionAst.new(@source, iv(node), exprs)
    end

    # --- Helpers -------------------------------------------------------------

    # Returns named children, excluding comment nodes (which appear as named
    # extras and would otherwise produce nil from visit_comment).
    def named_children(node)
      node.named_child_count.times.filter_map do |i|
        c = node.named_child(i)
        c.type == :comment ? nil : c
      end
    end

    # Returns ALL named children including comment nodes.
    # Used by sequential-child call sites that need to classify comments.
    def all_named_children(node)
      node.named_child_count.times.map { |i| node.named_child(i) }
    end

    def visit_by_field(node, field_name)
      c = node.child_by_field_name(field_name)
      return nil if c.nil? || c.null?
      visit(c)
    end

    def node_text(node)
      @source[node.start_byte...node.end_byte]
    end

    # Classify comment nodes in +ts_kids+ and attach them as leading or trailing
    # comments on the corresponding elements of +ast_kids+ (parallel arrays where
    # ast_kids[i] corresponds to ts_kids that are non-comment nodes in order).
    #
    # Uses the prettier blank-line heuristic:
    #   - same start row as preceding sibling's end row  → trailing of preceding
    #   - no blank line between run's last comment and following sibling → leading of following
    #   - otherwise → trailing of preceding (or dangling/ignored if no preceding node)
    #
    # ts_kids  - Array of TreeSitter::Node (all named children, including comments)
    # ast_kids - Array of AstNode (built from the non-comment ts_kids, in order)
    def attach_comments_to_siblings(ts_kids, ast_kids)
      return if ts_kids.none? { |c| c.type == :comment }

      # Build a parallel index: ts_kids index → ast_kids index (nil for comments)
      ast_idx = []
      ai = 0
      ts_kids.each do |c|
        if c.type == :comment
          ast_idx << nil
        else
          ast_idx << ai
          ai += 1
        end
      end

      # Walk ts_kids, collecting runs of consecutive comment nodes
      i = 0
      while i < ts_kids.length
        unless ts_kids[i].type == :comment
          i += 1
          next
        end

        # Start of a comment run
        run_start = i
        i += 1
        i += 1 while i < ts_kids.length && ts_kids[i].type == :comment
        run_end = i - 1  # inclusive

        run = ts_kids[run_start..run_end]
        first_comment = run.first
        last_comment  = run.last

        # Find nearest non-comment neighbors
        preceding_ts_idx  = (0...run_start).reverse_each.find { |j| ts_kids[j].type != :comment }
        following_ts_idx  = (run_end + 1...ts_kids.length).find { |j| ts_kids[j].type != :comment }

        preceding_ast = preceding_ts_idx ? ast_kids[ast_idx[preceding_ts_idx]] : nil
        following_ast = following_ts_idx ? ast_kids[ast_idx[following_ts_idx]] : nil

        comment_asts = run.map { |c| CommentAst.new(@source, iv(c), node_text(c)) }

        eol_of_preceding = preceding_ast && ts_kids[preceding_ts_idx].end_point.row == first_comment.start_point.row
        # "} # comment" pattern: preceding ends with '}' and there's a following
        # sibling — the comment introduces the code after the closed block, so
        # attach it as leading of the following node rather than trailing of the block.
        brace_label = eol_of_preceding && @source[ts_kids[preceding_ts_idx].end_byte - 1] == '}' && following_ast

        if eol_of_preceding && !brace_label
          # Normal end-of-line comment: trailing of preceding sibling
          comment_asts.each { |c| preceding_ast.attach_trailing_comment(c) }
        elsif following_ast && (brace_label || !blank_line_between?(last_comment.end_point.row, ts_kids[following_ts_idx].start_point.row))
          # "} # label" pattern, or own-line comment(s) with no blank line before next sibling → leading
          comment_asts.each { |c| following_ast.attach_leading_comment(c) }
        elsif preceding_ast
          # Blank line on both sides (or no following node) → trailing of preceding
          comment_asts.each { |c| preceding_ast.attach_trailing_comment(c) }
        end
        # If neither preceding nor following, comments are dangling (ignored for now)
      end
    end

    def blank_line_between?(row_a, row_b)
      (row_b - row_a) > 1
    end

    # --- Compound expressions ------------------------------------------------

    def visit_concatenation_expression(node)
      exprs = named_children(node).map { |c| visit(c) }
      ConcatenationExpressionAst.new(@source, iv(node), exprs)
    end

    def visit_replication_expression(node)
      count = visit(node.named_child(0))
      value = visit(node.named_child(1))
      ReplicationExpressionAst.new(@source, iv(node), count, value)
    end

    def visit_array_literal(node)
      entries = named_children(node).map { |c| visit(c) }
      ArrayLiteralAst.new(@source, iv(node), entries)
    end

    def visit_field_access_expression(node)
      obj        = visit(node.named_child(0))
      field_name = node_text(node.named_child(1))
      FieldAccessExpressionAst.new(@source, iv(node), obj, field_name)
    end

    def visit_enum_ref(node)
      class_name  = node_text(node.named_child(0))
      member_name = node_text(node.named_child(1))
      EnumRefAst.new(@source, iv(node), class_name, member_name)
    end

    # --- Function calls ------------------------------------------------------

    def visit_function_call(node)
      fname_node = node.named_child(0)  # function_name
      fname      = node_text(fname_node)
      arg_list   = node.named_child_count > 1 ? node.named_child(1) : nil
      args = (arg_list && !arg_list.null?) ? named_children(arg_list).map { |c| visit(c) } : []
      FunctionCallExpressionAst.new(@source, iv(node), fname, args)
    end

    def visit_function_name(node) = visit(node.named_child(0))

    # --- Dollar variables / functions ----------------------------------------

    def visit_dollar_variable(node)
      BuiltinVariableAst.new(@source, iv(node), node_text(node))
    end

    def visit_dollar_function_call(node)
      fname    = node_text(node.named_child(0))
      arg_list = node.named_child(1)
      case fname
      when "$signed"            then SignCastAst.new(@source, iv(node), visit(arg_list.named_child(0)))
      when "$unsigned", "$bits" then BitsCastAst.new(@source, iv(node), visit(arg_list.named_child(0)))
      when "$width"             then WidthRevealAst.new(@source, iv(node), visit(arg_list.named_child(0)))
      when "$array_size"        then ArraySizeAst.new(@source, iv(node), visit(arg_list.named_child(0)))
      when "$enum_element_size" then EnumElementSizeAst.new(@source, iv(node), visit(arg_list.named_child(0)))
      when "$enum_to_a"         then EnumArrayCastAst.new(@source, iv(node), visit(arg_list.named_child(0)))
      when "$enum"
        # $enum(TypeName, expr) — first arg is a type name, second is the value
        type_node = arg_list.named_child(0)
        type_name = UserTypeNameAst.new(@source, iv(type_node), node_text(type_node))
        EnumCastAst.new(@source, iv(node), type_name, visit(arg_list.named_child(1)))
      when "$array_includes?"
        ArrayIncludesAst.new(@source, iv(node),
                             visit(arg_list.named_child(0)),
                             visit(arg_list.named_child(1)))
      else
        args = named_children(arg_list).map { |c| visit(c) }
        FunctionCallExpressionAst.new(@source, iv(node), fname, args)
      end
    end

    def visit_dollar_variable_assignment(node)
      fname = node_text(node.named_child(0))
      value = visit(node.named_child(1))
      case fname
      when "$pc"
        PcAssignmentAst.new(@source, iv(node), value)
      else
        raise "TsAstBuilder: unhandled dollar variable assignment #{fname.inspect}"
      end
    end

    # --- CSR access ----------------------------------------------------------

    def visit_csr_field_access(node)
      csr_reg    = node.named_child(0)   # csr_register_access
      field_node = node.named_child(1)   # type_identifier or identifier
      csr_name_str = node_text(csr_reg.named_child(0))  # csr_name text
      csr_ast      = CsrReadExpressionAst.new(@source, iv(csr_reg), csr_name_str)
      CsrFieldReadExpressionAst.new(@source, iv(node), csr_ast, node_text(field_node))
    end

    def visit_csr_register_access(node)
      csr_name_str = node_text(node.named_child(0))  # csr_name
      CsrReadExpressionAst.new(@source, iv(node), csr_name_str)
    end

    def visit_csr_field_assignment(node)
      csr_field_ast = visit(node.named_child(0))
      value_ast     = visit(node.named_child(1))
      CsrFieldAssignmentAst.new(@source, iv(node), csr_field_ast, value_ast)
    end

    # --- Array / field assignments -------------------------------------------

    def visit_array_assignment(node)
      target = visit(node.named_child(0))  # primary_expression
      value  = visit_by_field(node, "value")

      # Collect (index, lsb?) pairs by scanning across [ ] boundaries.
      # field_name_for_child tells us which field each child belongs to.
      pairs = []
      in_bracket = false
      cur_idx = cur_lsb = nil
      node.child_count.times do |i|
        c = node.child(i)
        next if c.null?
        if !c.named? && node_text(c) == "["
          in_bracket = true; cur_idx = cur_lsb = nil
        elsif !c.named? && node_text(c) == "]"
          pairs << [cur_idx, cur_lsb] if cur_idx
          in_bracket = false
        elsif in_bracket && c.named?
          case node.field_name_for_child(i)
          when "index" then cur_idx = visit(c)
          when "lsb"   then cur_lsb = visit(c)
          end
        end
      end

      # Build intermediate access nodes for all-but-last subscript pairs.
      lhs = target
      pairs[0..-2].each do |idx, lsb|
        lhs = lsb ? AryRangeAccessAst.new(@source, iv(node), lhs, idx, lsb)
                  : AryElementAccessAst.new(@source, iv(node), lhs, idx)
      end

      # The last pair determines assignment type.
      last_idx, last_lsb = pairs.last
      if last_lsb
        AryRangeAssignmentAst.new(@source, iv(node), lhs, last_idx, last_lsb, value)
      else
        AryElementAssignmentAst.new(@source, iv(node), lhs, last_idx, value)
      end
    end

    def visit_field_assignment(node)
      id         = visit(node.named_child(0))
      field_name = node_text(node.named_child(1))
      value      = visit(node.named_child(2))
      FieldAssignmentAst.new(@source, iv(node), id, field_name, value)
    end

    def visit_array_size(node)
      visit(node.named_child(0))
    end

    # --- String literals -----------------------------------------------------

    def visit_string_literal(node)
      # node_text includes the surrounding quotes; StringLiteralAst stores the
      # raw text and strips quotes itself in value().
      StringLiteralAst.new(@source, iv(node), node_text(node))
    end

    # Comments are extras in the grammar but appear as named nodes in the CST.
    # When encountered in a sequential child list, they are handled by
    # attach_comments_to_siblings rather than via visit dispatch.
    def visit_comment(node)
      CommentAst.new(@source, iv(node), node_text(node))
    end

    # --- CSR function calls --------------------------------------------------

    def visit_csr_function_call(node)
      csr_reg    = node.named_child(0)   # csr_register_access
      fname_node = node.named_child(1)   # function_name
      arg_list   = node.named_child_count > 2 ? node.named_child(2) : nil
      csr_name_str = node_text(csr_reg.named_child(0))
      csr_ast      = CsrReadExpressionAst.new(@source, iv(csr_reg), csr_name_str)
      fname        = node_text(fname_node)
      args = (arg_list && !arg_list.null?) ? named_children(arg_list).map { |c| visit(c) } : []
      if fname == "sw_write"
        # sw_write(value) is a side-effecting operation, not a generic function call
        CsrSoftwareWriteAst.new(@source, iv(node), csr_ast, args.first)
      else
        CsrFunctionCallAst.new(@source, iv(node), fname, csr_ast, args)
      end
    end

    # --- Constraint body -----------------------------------------------------

    def visit_constraint_body(node)
      ts_kids  = all_named_children(node)
      ast_kids = ts_kids.reject { |c| c.type == :comment }.map { |c| visit(c) }
      attach_comments_to_siblings(ts_kids, ast_kids)
      ConstraintBodyAst.new(@source, iv(node), ast_kids)
    end

    def visit_implication_statement(node)
      ImplicationStatementAst.new(@source, iv(node), visit(node.named_child(0)))
    end

    def visit_implication_expression(node)
      children = named_children(node)
      if children.size >= 2
        antecedent = visit(children[0])
        consequent = visit(children[1])
      else
        antecedent = TrueExpressionAst.new(@source, node.start_byte...node.start_byte)
        consequent = visit(children[0])
      end
      ImplicationExpressionAst.new(@source, iv(node), antecedent, consequent)
    end

    def visit_implication_for_loop(node)
      children = named_children(node)
      init      = visit(children[0])   # for_loop_iteration_variable_declaration
      condition = visit(children[1])   # expression (condition)
      update    = visit(children[2])   # assignment / post_increment / post_decrement
      stmts     = children[3..].map { |c| visit(c) }
      ForLoopAst.new(@source, iv(node), init, condition, update, stmts)
    end

    # --- Fetch definition ----------------------------------------------------

    def visit_fetch_definition(node)
      block = node.named_child(0)  # statement_block
      stmts = block_stmts(block)
      content_iv = stmts.empty? ? 0...0 : block.named_child(0).start_byte...(block.end_byte - 1)
      body = FunctionBodyAst.new(@source, content_iv, stmts)
      FetchAst.new(@source, iv(node), body)
    end

    # --- ISA file ------------------------------------------------------------

    def visit_isa_file(node)
      defs = named_children(node).select { |c| c.type == :definition }.filter_map { |c| visit(c) }
      IsaAst.new(@source, iv(node), defs)
    end

    def visit_definition(node)           = visit(node.named_child(0))
    def visit_function_definition(node)  = visit(node.named_child(0))

    def visit_body_function_definition(node)
      children  = named_children(node)
      fname     = node_text(children[0])  # function_name
      qualifier = node.child(0).type == :external ? :external : :normal

      return_types = []
      args_node    = nil
      desc_node    = nil
      body_node    = nil

      children[1..].each do |c|
        case c.type
        when :type_name         then return_types << visit(c)
        when :arguments_clause  then args_node  = c
        when :description_block then desc_node  = c
        when :body_block        then body_node  = c
        end
      end

      arguments = extract_arguments(args_node)
      desc      = extract_description(desc_node)
      body      = build_function_body(body_node)

      FunctionDefAst.new(@source, iv(node), fname, return_types, arguments, desc, qualifier, body)
    end

    def visit_builtin_function_definition(node)
      children  = named_children(node)
      fname     = node_text(children[0])
      qualifier = node.child(0).type == :generated ? :generated : :builtin

      return_types = []
      args_node    = nil
      desc_node    = nil

      children[1..].each do |c|
        case c.type
        when :type_name         then return_types << visit(c)
        when :arguments_clause  then args_node = c
        when :description_block then desc_node = c
        end
      end

      FunctionDefAst.new(@source, iv(node), fname, return_types,
                         extract_arguments(args_node), extract_description(desc_node),
                         qualifier, nil)
    end

    def visit_enum_definition(node)
      # Two forms:
      #   generated enum TypeName ;        → BuiltinEnumDefinitionAst (no members)
      #   enum TypeName { member... }      → EnumDefinitionAst
      if node_text(node.child(0)) == "generated"
        type_ast = make_user_type_name(node.named_child(0))
        return BuiltinEnumDefinitionAst.new(@source, iv(node), type_ast)
      end

      children     = named_children(node)
      type_ast     = make_user_type_name(children[0])
      member_nodes = children[1..].reject { |c| c.type == :comment }

      names  = member_nodes.map do |m|
        type_id = named_children(m).find { |c| c.type == :type_identifier }
        make_user_type_name(type_id)
      end
      values = member_nodes.map do |m|
        lit = named_children(m).find { |c| c.type == :int_literal }
        lit ? visit(lit) : nil
      end

      EnumDefinitionAst.new(@source, iv(node), type_ast, names, values)
    end

    def visit_bitfield_definition(node)
      children = named_children(node)
      size_ast  = visit(children[0])            # int_literal
      name_ast  = make_user_type_name(children[1]) # type_identifier
      # Build fields with comment attachment on the sequential member list
      field_ts_kids  = all_named_children(node).drop_while { |c| c.type != :bitfield_member }
      field_ast_kids = field_ts_kids.reject { |c| c.type == :comment }.filter_map { |c| visit(c) }
      attach_comments_to_siblings(field_ts_kids, field_ast_kids)
      BitfieldDefinitionAst.new(@source, iv(node), name_ast, size_ast, field_ast_kids)
    end

    def visit_bitfield_member(node)
      children = named_children(node)
      name_str = node_text(children[0])
      if children.size == 3
        # range: name msb-lsb
        msb = visit(children[1])
        lsb = visit(children[2])
      else
        # single bit: name pos
        msb = lsb = visit(children[1])
      end
      BitfieldFieldDefinitionAst.new(@source, iv(node), name_str, msb, lsb)
    end

    def visit_struct_definition(node)
      children     = named_children(node).reject { |c| c.type == :comment }
      name_str     = node_text(children[0])  # type_identifier — stored as String
      member_types = []
      member_names = []
      i = 1
      while i < children.size
        member_types << visit(children[i])           # type_name
        member_names << node_text(children[i + 1])   # identifier name as String
        i += 2
      end
      StructDefinitionAst.new(@source, iv(node), name_str, member_types, member_names)
    end

    def visit_global_definition(node)
      children = named_children(node)
      # Determine if this has an initializer by checking for an expression child
      # (last named child will be expression if init is present; no-init ends with identifier)
      has_init = children.last.type == :expression
      type_ast = visit(children[0])
      id_ast   = visit_as_id(children[1])   # identifier or type_identifier
      if has_init
        ary_size = children.size == 4 ? visit(children[2]) : nil
        value    = visit(children.last)
        decl     = VariableDeclarationWithInitializationAst.new(
          @source, iv(node), type_ast, id_ast, ary_size, value, false
        )
        GlobalWithInitializationAst.new(@source, iv(node), decl)
      else
        ary_size = children.size == 3 ? visit(children[2]) : nil
        decl     = VariableDeclarationAst.new(@source, iv(node), type_ast, id_ast, ary_size)
        GlobalAst.new(@source, iv(node), decl)
      end
    end

    def visit_include_statement(node)
      str_node = node.named_child(0)
      str_text = node_text(str_node)
      str_ast  = StringLiteralAst.new(@source, iv(str_node), str_text)
      IncludeStatementAst.new(@source, iv(node), str_ast)
    end

    # --- ISA helpers ---------------------------------------------------------

    def make_user_type_name(node)
      UserTypeNameAst.new(@source, iv(node), node_text(node))
    end

    def visit_as_id(node)
      IdAst.new(@source, iv(node), node_text(node))
    end

    def extract_arguments(args_node)
      return [] if args_node.nil?
      named_children(args_node).filter_map { |c| visit(c) }
    end

    def extract_description(desc_node)
      return "" if desc_node.nil?
      content = desc_node.named_child(0)  # description_content
      # Treetop's grammar consumes the leading space after '{' as part of the
      # 'description {' token, so the content string has no leading space.
      @source[content.start_byte...content.end_byte].sub(/\A /, "")
    end

    def build_function_body(body_node)
      return nil if body_node.nil?
      block = body_node.named_child(0)  # statement_block
      stmts = block_stmts(block)
      # Use content-only interval (between { and }) to match Treetop's interval.
      content_iv = stmts.empty? ? 0...0 : block.named_child(0).start_byte...(block.end_byte - 1)
      FunctionBodyAst.new(@source, content_iv, stmts)
    end
  end
end
