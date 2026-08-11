# typed: false
# frozen_string_literal: true

# Loaded when COVERAGE=1 to add IDL source coverage probes to the generated C++.
#
# Probes are injected at statement-list boundaries (FunctionBodyAst, IfAst arms,
# ForLoopAst body, ConditionalStatementAst) rather than on individual AST node
# types. This avoids the problem that some node types (VariableDeclaration*,
# PostIncrement*, VariableAssignment*) appear both as standalone statements AND
# as for-loop init/update clauses, where probe injection would produce invalid C++.

require "json"

module IdlCoverageManifest
  @probes = []
  @counter = 0
  @current_source = nil
  @current_kind = "func"

  def self.kind_for(file)
    path = file.to_s
    if path.include?("/inst/")
      "inst"
    elsif path.include?("/csr/")
      "csr"
    else
      "func"
    end
  end

  def self.set_current_source(name, kind)
    @current_source = name.to_s
    @current_kind = kind.to_s
  end

  def self.next_id(file, lineno, type = :stmt)
    id = @counter
    file_str = file.to_s
    if file_str.empty?
      source = @current_source || "unknown"
      kind   = @current_kind
    else
      source = File.basename(file_str, ".*")
      kind   = kind_for(file_str)
    end
    @probes << {
      id:     id,
      source: source,
      kind:   kind,
      file:   file_str,
      lineno: lineno,
      type:   type.to_s
    }
    @counter += 1
    id
  end

  def self.write(path)
    File.write(path, JSON.pretty_generate({ probes: @probes }))
  end

  def self.reset!
    @probes = []
    @counter = 0
    @current_source = nil
    @current_kind = "func"
  end
end

module Idl
  # FunctionBodyAst: inject a statement probe before each top-level statement.
  class FunctionBodyAst
    def gen_cpp(symtab, indent = 0, indent_spaces: 2)
      cpp = []
      statements.each do |s|
        id = IdlCoverageManifest.next_id(s.input_file, s.lineno)
        cpp << "#{' ' * indent}COVERAGE_PROBE(#{id});"
        cpp << "#{' ' * indent}#{s.gen_cpp(symtab, 0, indent_spaces:)}"
      end
      cpp.join("\n")
    end
  end

  # IfAst: branch probes at the start of each arm plus statement probes in bodies.
  # Always emits a synthetic else so the false path is observable.
  class IfAst
    def gen_cpp(symtab, indent = 0, indent_spaces: 2)
      true_id  = IdlCoverageManifest.next_id(input_file, lineno, :branch_true)
      false_id = IdlCoverageManifest.next_id(input_file, lineno, :branch_false)

      cpp = ["if (#{if_cond.gen_cpp(symtab, 0, indent_spaces:)}) {",
             "COVERAGE_PROBE(#{true_id});"]
      if_body.stmts.each do |s|
        id = IdlCoverageManifest.next_id(s.input_file, s.lineno)
        cpp << "COVERAGE_PROBE(#{id});"
        cpp << s.gen_cpp(symtab, indent_spaces, indent_spaces:)
      end

      elseifs.each do |eif|
        ei_id = IdlCoverageManifest.next_id(input_file, eif.cond.lineno, :branch_true)
        cpp << "} else if (#{eif.cond.gen_cpp(symtab, 0, indent_spaces:)}) {"
        cpp << "COVERAGE_PROBE(#{ei_id});"
        eif.body.stmts.each do |s|
          id = IdlCoverageManifest.next_id(s.input_file, s.lineno)
          cpp << "COVERAGE_PROBE(#{id});"
          cpp << s.gen_cpp(symtab, indent_spaces, indent_spaces:)
        end
      end

      cpp << "} else {"
      cpp << "COVERAGE_PROBE(#{false_id});"
      final_else_body.stmts.each do |s|
        id = IdlCoverageManifest.next_id(s.input_file, s.lineno)
        cpp << "COVERAGE_PROBE(#{id});"
        cpp << s.gen_cpp(symtab, indent_spaces, indent_spaces:)
      end
      cpp << "}"
      cpp.map { |l| "#{' ' * indent}#{l}" }.join("\n")
    end
  end

  # ForLoopAst: loop-entry probe as first body statement; statement probes for
  # each body statement. init/condition/update are NOT probed — they are
  # sub-expressions, not statements, and probe injection there breaks C++ syntax.
  class ForLoopAst
    def gen_cpp(symtab, indent = 0, indent_spaces: 2)
      entry_id = IdlCoverageManifest.next_id(input_file, lineno, :loop_entry)
      lines = ["COVERAGE_PROBE(#{entry_id});"]
      symtab.push(nil)
      init.add_symbol(symtab)
      symtab.get(init.lhs.text_value).value = nil
      stmts.each do |s|
        id = IdlCoverageManifest.next_id(s.input_file, s.lineno)
        lines << "COVERAGE_PROBE(#{id});"
        lines << s.gen_cpp(symtab, indent_spaces, indent_spaces:)
      end
      cpp = <<~LOOP
        for (#{init.gen_cpp(symtab, 0, indent_spaces:)}; #{condition.gen_cpp(symtab, 0, indent_spaces:)}; #{update.gen_cpp(symtab, 0, indent_spaces:)}) {
          #{lines.join("\n  ")}
        }
      LOOP
      symtab.pop
      cpp.lines.map { |l| "#{' ' * indent}#{l}" }.join("")
    end
  end

  # ConditionalStatementAst: branch probes with synthetic else for false-path.
  class ConditionalStatementAst
    def gen_cpp(symtab, indent = 0, indent_spaces: 2)
      true_id  = IdlCoverageManifest.next_id(input_file, lineno, :branch_true)
      false_id = IdlCoverageManifest.next_id(input_file, lineno, :branch_false)
      cpp = <<~IF
        if (#{condition.gen_cpp(symtab, 0, indent_spaces:)}) {
          COVERAGE_PROBE(#{true_id});
          #{action.gen_cpp(symtab, indent_spaces, indent_spaces:)};
        } else {
          COVERAGE_PROBE(#{false_id});
        }
      IF
      cpp.lines.map { |l| "#{' ' * indent}#{l}" }.join("")
    end
  end

  # ConditionalReturnStatementAst: branch probes with synthetic else.
  class ConditionalReturnStatementAst
    def gen_cpp(symtab, indent = 0, indent_spaces: 2)
      true_id  = IdlCoverageManifest.next_id(input_file, lineno, :branch_true)
      false_id = IdlCoverageManifest.next_id(input_file, lineno, :branch_false)
      cpp = <<~CPP
        if (#{condition.gen_cpp(symtab, 0, indent_spaces:)}) {
          COVERAGE_PROBE(#{true_id});
          #{return_expression.gen_cpp(symtab, indent_spaces, indent_spaces:)};
        } else {
          COVERAGE_PROBE(#{false_id});
        }
      CPP
      cpp.lines.map { |l| "#{' ' * indent}#{l}" }.join("")
    end
  end
end
