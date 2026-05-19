# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "pathname"
require "sorbet-runtime"

require_relative "idlc/syntax_node"

require_relative "idlc/ast"
require_relative "idlc/symbol_table"
require_relative "idlc/ts_parser"
require_relative "idlc/ts_ast_builder"

module Idl
  # the Idl compiler
  class Compiler
    extend T::Sig

    # Class-level parse cache: absolute file path (String) → IsaSyntaxNode.
    # Shared across all Compiler instances so each file is parsed only once per
    # process.  Safe to share because IsaSyntaxNode#to_ast is non-destructive
    # and returns a fresh, independent IsaAst on every call.
    # Mutex guards writes; under MRI, reads without the lock are safe.
    @@parse_cache = {}
    @@parse_cache_mutex = Mutex.new

    # set a progressbar
    def pb=(pb)
      @pb = pb
    end

    # unset a progressbar
    def unset_pb
      @pb.finish unless @pb.nil?
      @pb = nil
    end

    # Build an AST from source without running type-checking. This is the
    # tree-sitter replacement for the old `compiler.parser.parse(src, root: :x)`
    # + `m.to_ast` pattern used in tests.
    #
    # root: accepts the same symbolic names as Treetop's root: argument and
    # performs any wrapping/unwrapping needed to produce an equivalent AST node.
    def build_ast(source, root: :auto, input_file: "[build_ast]", starting_line: 0)
      src = source
      # ISA definitions need the %version: header to be detected by tree-sitter.
      isa_def_roots = %i[enum_definition bitfield_definition struct_definition]
      if isa_def_roots.include?(root)
        src = "%version: 1.0\n#{source}"
      end
      # :assignment and :single_declaration lack the trailing ';' in some
      # Treetop usages; tree-sitter needs a statement-terminated input.
      if %i[assignment single_declaration].include?(root)
        src = src.end_with?(";") ? src : "#{src};"
      end

      ast = ts_build(src, filename: input_file.to_s, starting_line: starting_line.to_i)

      # Unwrap to match what Treetop's root: argument returned.
      ast = case root
            when :statement
              ast.is_a?(FunctionBodyAst) ? ast.stmts.first : ast
            when :assignment, :single_declaration
              stmt = ast.is_a?(FunctionBodyAst) ? ast.stmts.first : ast
              stmt.respond_to?(:action) ? stmt.action : stmt
            when *isa_def_roots
              ast.is_a?(IsaAst) ? ast.children.first : ast
            else
              ast
            end

      ast.set_input_file(input_file, starting_line) if ast
      ast
    end

    private

    def ts_syntax_detail(source, filename:, starting_line: 0)
      errors = TsParser.check_errors(source)
      return nil if errors.empty?
      TsParser.format_errors(source, errors, filename: filename.to_s, starting_line: starting_line)
    end

    def ts_parser
      @ts_parser ||= TreeSitter::Parser.new.tap { |p| p.language = TsParser.language }
    end

    public

    # Parse +source+ with tree-sitter, raise SyntaxError on parse errors, and
    # return the built AST. Does not call set_input_file — callers handle that.
    #
    # root: :for_loop unwraps FunctionBodyAst → its single inner ForLoopAst,
    # matching what Treetop's `root: :for_loop` returned.
    sig {
      params(
        source: String,
        filename: T.any(String, Pathname),
        starting_line: Integer,
        root: Symbol
      )
      .returns(AstNode)
      .checked(:never)
    }
    def ts_build(source, filename:, starting_line: 0, root: :auto)
      tree  = ts_parser.parse_string(nil, source)
      errs  = TsParser.collect_errors(tree.root_node, [])
      unless errs.empty?
        detail = TsParser.format_errors(source, errs, filename: filename.to_s, starting_line: starting_line.to_i)
        raise SyntaxError, "While parsing #{filename}:\n\n#{detail}"
      end
      ast = TsAstBuilder.new(source).build(tree.root_node)
      if root == :for_loop && ast.is_a?(FunctionBodyAst)
        ast.stmts.first
      else
        ast
      end
    end

    def compile_file(path, source_mapper = nil)
      path_key = path.realpath.to_s

      # Cache now stores IsaAst directly (built by TsAstBuilder).
      # Reads without the lock are safe under MRI; writes are locked.
      cached = T.let(@@parse_cache[path_key], T.nilable(IsaAst))

      if cached.nil?
        @@parse_cache_mutex.synchronize do
          unless @@parse_cache.key?(path_key)
            content = path.read
            source_mapper[path_key] = content unless source_mapper.nil?

            old_format = @pb.format unless @pb.nil?
            @pb.format = "Parsing #{File.basename(path)} [:bar]" unless @pb.nil?
            pid = unless @pb.nil?
                    fork {
                      loop do
                        sleep 1
                        @pb.advance unless @pb.nil?
                      end
                    }
                  end

            ast = ts_build(content, filename: path_key)

            unless @pb.nil?
              Process.kill("TERM", T.must(pid))
              Process.wait(T.must(pid))
              @pb.format = old_format
            end

            @@parse_cache[path_key] = ast
          end
          cached = @@parse_cache[path_key]
        end
      else
        source_mapper[path_key] = path.read unless source_mapper.nil?
      end

      ast = T.must(cached)

      ast.children.each do |child|
        next unless child.is_a?(IncludeStatementAst)

        if child.filename.empty?
          raise SyntaxError, <<~MSG
            While parsing #{path}:#{child.lineno}:

            Empty include statement
          MSG
        end

        include_path =
          if child.filename[0] == "/"
            Pathname.new(child.filename)
          else
            (path.dirname / child.filename)
          end

        unless include_path.exist?
          raise SyntaxError, <<~MSG
            While parsing #{path}:#{child.lineno}:

            Path #{include_path} does not exist
          MSG
        end
        unless include_path.readable?
          raise SyntaxError, <<~MSG
            While parsing #{path}:#{child.lineno}:

            Path #{include_path} cannot be read
          MSG
        end

        include_ast = compile_file(include_path)
        include_ast.set_input_file_unless_already_set(include_path)
        ast.replace_include!(child, include_ast)
      end

      # we may have already set an input file from an include, so only set it if it's not already set
      ast.set_input_file_unless_already_set(path.to_s)

      ast
    end

    sig { params(loop: String, symtab: SymbolTable, pass_error: T::Boolean).returns(ForLoopAst) }
    def compile_for_loop(loop, symtab, pass_error: false)
      ast = T.cast(ts_build(loop, filename: "[for loop]", root: :for_loop), ForLoopAst)
      ast.set_input_file("[LOOP]", 0)
      value_result = ast.value_try do
        ast.freeze_tree(symtab)
      end
      if value_result == :unknown_value
        raise AstNode::TypeError, "Bad literal value" if pass_error

        warn "Compiling #{loop}"
        warn "Bad literal value"
        exit 1
      end
      begin
        ast.type_check(symtab, strict: false)
      rescue AstNode::TypeError => e
        raise e if pass_error

        warn "Compiling #{loop}"
        warn e.what
        warn T.must(e.backtrace).join("\n")
        exit 1
      rescue AstNode::InternalError => e
        raise e if pass_error

        warn "Compiling #{loop}"
        warn e.what
        warn T.must(e.backtrace).join("\n")
        exit 1
      end

      ast
    end

    # compile a function body, and return the abstract syntax tree
    #
    # @param body [String] Function body source code
    # @param return_type [Type] Expected return type, if known
    # @param symtab [SymbolTable] Symbol table to use for type checking
    # @param name [String] Function name, used for error messages
    # @param input_file [Pathname] Path to the input file this source comes from
    # @param input_line [Integer] Starting line in the input file that this source comes from
    # @param no_rescue [Boolean] Whether or not to automatically catch any errors
    # @return [Ast] The root of the abstract syntax tree
    def compile_func_body(body, return_type: nil, symtab: nil, name: nil, input_file: nil, input_line: 0, starting_offset: 0, line_file_offsets: nil, no_rescue: false, extra_syms: {}, type_check: true)
      ast = T.cast(ts_build(body, filename: input_file || name.to_s, starting_line: input_line.to_i), FunctionBodyAst)
      ast.set_input_file(input_file, input_line, starting_offset, line_file_offsets)
      ast.freeze_tree(symtab)

      # type check
      unless type_check == false
        cloned_symtab = symtab.deep_clone

        cloned_symtab.push(ast)
        cloned_symtab.add("__expected_return_type", return_type) unless return_type.nil?

        extra_syms.each { |k, v|
          cloned_symtab.add(k, v)
        }

        begin
          ast.statements.each do |s|
            s.type_check(cloned_symtab, strict: false)
          end
        rescue AstNode::TypeError => e
          raise e if no_rescue

          warn "In function #{name}:"
          warn e.what
          exit 1
        rescue AstNode::InternalError => e
          raise if no_rescue

          warn "In function #{name}:"
          warn e.what
          warn T.must(e.backtrace).join("\n")
          exit 1
        ensure
          cloned_symtab.pop
        end

      end

      ast
    end

    sig {
      params(
        idl: String,
        symtab: SymbolTable,
        input_file: T.any(String, Pathname),
        input_line: Integer,
        starting_offset: Integer,
        line_file_offsets: T.nilable(T::Array[Integer])
      )
      .returns(FunctionBodyAst)
    }
    def compile_inst_scope(idl, symtab:, input_file:, input_line: 0, starting_offset: 0, line_file_offsets: nil)
      if idl.empty?
        return FunctionBodyAst.new(nil, 0...0, [])
      end
      ast = T.cast(ts_build(idl, filename: input_file, starting_line: input_line.to_i), FunctionBodyAst)
      ast.set_input_file(input_file, input_line, starting_offset, line_file_offsets)
      ast.freeze_tree(symtab)

      ast
    end

    # compile an instruction operation, and return the abstract syntax tree
    #
    # @param inst [Instruction] Instruction object
    # @param symtab [SymbolTable] Symbol table
    # @param input_file [Pathname] Path to the input file this source comes from
    # @param input_line [Integer] Starting line in the input file that this source comes from
    # @return [Ast] The root of the abstract syntax tree
    def compile_inst_operation(inst, symtab:, input_file: nil, input_line: 0, starting_offset: 0, line_file_offsets: nil)
      operation = inst.data["operation()"]
      compile_inst_scope(operation, symtab:, input_file:, input_line:, starting_offset:, line_file_offsets:)
    end

    # Type check an abstract syntax tree
    #
    # @param ast [AstNode] An abstract syntax tree
    # @param symtab [SymbolTable] The compilation context
    # @param what [String] A description of what you are type checking (for error messages)
    # @raise AstNode::TypeError if a type error is found
    def type_check(ast, symtab, what)
      # type check
      raise "Tree should be frozen" unless ast.frozen?

      begin
        value_result = AstNode.value_try do
          ast.type_check(symtab, strict: false)
        end
        AstNode.value_else(value_result) do
          warn "While type checking #{what}, got a value error on:"
          warn ast.text_value
          warn AstNode.value_error_reason
          warn symtab.callstack
          unless AstNode.value_error_ast.nil?
            warn "At #{AstNode.value_error_ast.input_file}:#{AstNode.value_error_ast.lineno}"
          end
          exit 1
        end
      rescue AstNode::InternalError => e
        warn "While type checking #{what}:"
        warn e.what
        warn T.must(e.backtrace).join("\n")
        exit 1
      end

      ast
    end

    def compile_expression(expression, symtab, pass_error: false)
      ast = ts_build(expression, filename: "[expression]")
      ast.set_input_file("[EXPRESSION]", 0)
      value_result = ast.value_try do
        ast.freeze_tree(symtab)
      end
      if value_result == :unknown_value
        raise AstNode::TypeError, "Bad literal value" if pass_error

        warn "Compiling #{expression}"
        warn "Bad literal value"
        exit 1
      end
      begin
        ast.type_check(symtab, strict: false)
      rescue AstNode::TypeError => e
        raise e if pass_error

        warn "Compiling #{expression}"
        warn e.what
        warn T.must(e.backtrace).join("\n")
        exit 1
      rescue AstNode::InternalError => e
        raise e if pass_error

        warn "Compiling #{expression}"
        warn e.what
        warn T.must(e.backtrace).join("\n")
        exit 1
      end

      ast
    end

    sig {
      params(
        body: String,
        symtab: SymbolTable,
        pass_error: T::Boolean,
        input_file: T.any(String, Pathname),
        input_line: Integer,
        starting_offset: Integer,
        line_file_offsets: T.nilable(T::Array[Integer])
      ).returns(ConstraintBodyAst)
    }
    def compile_constraint(body, symtab, pass_error: false,
                           input_file: "[CONSTRAINT]", input_line: 0,
                           starting_offset: 0, line_file_offsets: nil)
      ast = T.cast(ts_build(body, filename: input_file, root: :constraint_body), ConstraintBodyAst)
      ast.set_input_file(input_file, input_line, starting_offset, line_file_offsets)
      ast.freeze_tree(symtab)

      ast
    end
  end
end
