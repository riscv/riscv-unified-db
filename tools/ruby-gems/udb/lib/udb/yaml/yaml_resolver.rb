# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "psych"
require "pathname"
require "fileutils"
require "json"
require "sorbet-runtime"

require "idlc"

require_relative "comment_parser"
require_relative "preserving_emitter"

module Udb
  module Yaml
    # Ruby implementation of YAML resolver that preserves comments and order
    class Resolver
      extend T::Sig

      sig { params(quiet: T::Boolean, compile_idl: T::Boolean).void }
      def initialize(quiet: false, compile_idl: false)
        @quiet = T.let(quiet, T::Boolean)
        @compile_idl = T.let(compile_idl, T::Boolean)
        @compiler = T.let(nil, T.nilable(Idl::Compiler))
        if @compile_idl
          @compiler = Idl::Compiler.new
        end
        @resolved_objs = T.let({}, T::Hash[String, T::Hash[Symbol, T.untyped]])
        @current_comment_map = T.let(nil, T.nilable(CommentMap))
      end

      sig {
        params(
          base_dir: T.any(String, Pathname),
          overlay_dir: T.nilable(T.any(String, Pathname)),
          output_dir: T.any(String, Pathname)
        ).void
      }
      def merge_files(base_dir, overlay_dir, output_dir)
        base_dir = Pathname.new(base_dir)
        overlay_dir = overlay_dir.nil? ? nil : Pathname.new(overlay_dir)
        output_dir = Pathname.new(output_dir)

        base_files = Dir.glob((base_dir / "**" / "*.yaml").to_s).map { |f| Pathname.new(f).relative_path_from(base_dir).to_s }
        overlay_files = overlay_dir.nil? ? [] : Dir.glob((overlay_dir / "**" / "*.yaml").to_s).map { |f| Pathname.new(f).relative_path_from(overlay_dir).to_s }
        all_files = (base_files + overlay_files).uniq

        all_files.each do |rel_path|
          merge_file(rel_path, base_dir, overlay_dir, output_dir)
        end

        puts "[INFO] Merged architecture files written to #{output_dir}" unless @quiet
      end

      sig {
        params(
          rel_path: String,
          base_dir: Pathname,
          overlay_dir: T.nilable(Pathname),
          output_dir: Pathname
        ).void
      }
      def merge_file(rel_path, base_dir, overlay_dir, output_dir)
        base_path = base_dir / rel_path
        overlay_path = overlay_dir.nil? ? nil : (overlay_dir / rel_path)
        output_path = output_dir / rel_path

        FileUtils.mkdir_p(output_path.dirname)

        if !base_path.exist? && (overlay_path.nil? || !overlay_path.exist?)
          FileUtils.rm_f(output_path) if output_path.exist?
        elsif overlay_path.nil? || !overlay_path.exist?
          if !output_path.exist? || base_path.mtime > output_path.mtime
            FileUtils.cp(base_path, output_path)
          end
        elsif !base_path.exist?
          if !output_path.exist? || overlay_path.mtime > output_path.mtime
            FileUtils.cp(overlay_path, output_path)
          end
        else
          if !output_path.exist? ||
             base_path.mtime > output_path.mtime ||
             overlay_path.mtime > output_path.mtime

            parser = CommentParser.new
            base_result = parser.parse_file(base_path)
            overlay_result = parser.parse_file(overlay_path)

            merged_data = json_merge_patch(base_result[:data], overlay_result[:data])

            emitter = PreservingEmitter.new(overlay_result[:comments])
            emitter.emit_file(merged_data, output_path)
          end
        end
      end

      sig {
        params(
          input_dir: T.any(String, Pathname),
          output_dir: T.any(String, Pathname),
          options: T::Hash[Symbol, T.untyped]
        ).void
      }
      def resolve_files(input_dir, output_dir, options = {})
        input_dir = Pathname.new(input_dir)
        output_dir = Pathname.new(output_dir)
        no_checks = options[:no_checks] || false

        yaml_files = Dir.glob((input_dir / "**" / "*.yaml").to_s).map do |f|
          Pathname.new(f).relative_path_from(input_dir).to_s
        end

        yaml_files.each do |rel_path|
          resolve_file(rel_path, input_dir, output_dir, no_checks)
        end

        yaml_files.each do |rel_path|
          write_resolved_file(rel_path, input_dir, output_dir, no_checks)
        end

        FileUtils.mkdir_p(output_dir)
        File.write(output_dir / "index.yaml", Psych.dump(yaml_files))
        File.write(output_dir / "index.json", JSON.pretty_generate(yaml_files))

        puts "[INFO] Resolved architecture files written to #{output_dir}" unless @quiet
      end

      sig {
        params(
          rel_path: String,
          input_dir: Pathname,
          output_dir: Pathname,
          no_checks: T::Boolean
        ).void
      }
      def resolve_file(rel_path, input_dir, output_dir, no_checks)
        input_path = input_dir / rel_path

        return unless input_path.exist?

        parser = CommentParser.new
        result = parser.parse_file(input_path)
        data = result[:data]

        track_source_locations(input_path, result[:comments])
        @current_comment_map = result[:comments]

        if !no_checks && data.key?("name")
          fn_name = Pathname.new(rel_path).basename(".yaml").to_s
          if fn_name != data["name"]
            raise "ERROR: 'name' key (#{data["name"]}) must match filename (#{fn_name}) in #{rel_path}"
          end
        end

        resolved_data = resolve_object(data, [], rel_path, data, input_dir, no_checks)

        @resolved_objs[rel_path] = { data: resolved_data, comments: result[:comments] }
      end

      sig {
        params(
          rel_path: String,
          input_dir: Pathname,
          output_dir: Pathname,
          no_checks: T::Boolean
        ).void
      }
      def write_resolved_file(rel_path, input_dir, output_dir, no_checks)
        output_path = output_dir / rel_path

        return unless @resolved_objs.key?(rel_path)

        resolved_obj = @resolved_objs.fetch(rel_path).fetch(:data)
        comments = @resolved_objs.fetch(rel_path).fetch(:comments)

        resolved_obj["$source"] = (input_dir / rel_path).realpath.to_s

        FileUtils.mkdir_p(output_path.dirname)

        emitter = PreservingEmitter.new(comments)
        emitter.emit_file(resolved_obj, output_path)

        FileUtils.chmod(0o666, output_path)
      end

      sig {
        params(
          obj: T.untyped,
          obj_path: T::Array[T.untyped],
          obj_file_path: T.any(String, Pathname),
          doc_obj: T.untyped,
          arch_root: Pathname,
          no_checks: T::Boolean
        ).returns(T.untyped)
      }
      def resolve_object(obj, obj_path, obj_file_path, doc_obj, arch_root, no_checks)
        return obj unless obj.is_a?(Hash) || obj.is_a?(Array)

        if obj.is_a?(Array)
          return obj.map.with_index do |item, idx|
            resolve_object(item, obj_path + [idx], obj_file_path, doc_obj, arch_root, no_checks)
          end
        end

        if obj.key?("$inherits")
          return resolve_inherits(obj, obj_path, obj_file_path, doc_obj, arch_root, no_checks)
        end

        resolved = T.let({}, T::Hash[String, T.untyped])
        obj.each do |key, value|
          resolved[key] = resolve_object(value, obj_path + [key], obj_file_path, doc_obj, arch_root, no_checks)
        end

        if resolved.key?("$remove")
          remove_keys = resolved["$remove"]
          remove_keys = [remove_keys] unless remove_keys.is_a?(Array)
          remove_keys.each { |key| resolved.delete(key) }
          resolved.delete("$remove")
        end

        if @compile_idl
          idl_keys = obj.keys.select { |k| k.end_with?(")") }.reject { |k| k == "sail()" }
          idl_keys.each do |key|
            key_minus_args = key.split("(")[0]
            source_loc = @current_comment_map&.get_source_location(obj_path + [key])
            starting_line = source_loc ? source_loc[:line] : 0
            starting_offset = source_loc ? (source_loc[:offset] || 0) : 0
            parse_root =
              if key == "operation()"
                :instruction_operation
              elsif obj_path.include?("requirements")
                :constraint_body
              else
                :function_body
              end
            compiler = T.must(@compiler)
            compiler.parser.set_input_file(obj_file_path, starting_line)
            m = compiler.parser.parse(obj.fetch(key), root: parse_root)
            if m.nil?
              raise SyntaxError, <<~MSG
                While parsing #{obj_file_path}:#{compiler.parser.failure_line}

                #{compiler.parser.failure_reason}
              MSG
            end
            ast = m.to_ast
            if ast.nil?
              raise "IDL compiler could not convert to ast"
            end
            ast.set_input_file(obj_file_path, starting_line, starting_offset)
            resolved[key_minus_args] = ast.to_h
          end
        end

        resolved
      end

      sig {
        params(
          obj: T::Hash[String, T.untyped],
          obj_path: T::Array[T.untyped],
          obj_file_path: T.any(String, Pathname),
          doc_obj: T.untyped,
          arch_root: Pathname,
          no_checks: T::Boolean
        ).returns(T::Hash[String, T.untyped])
      }
      def resolve_inherits(obj, obj_path, obj_file_path, doc_obj, arch_root, no_checks)
        inherits_targets = obj["$inherits"].is_a?(Array) ? obj["$inherits"] : [obj["$inherits"]]

        obj["$child_of"] = obj["$inherits"]
        obj.delete("$inherits")

        parent_obj = T.let({}, T::Hash[String, T.untyped])

        inherits_targets.each do |inherits_target|
          if inherits_target.include?("#")
            ref_file_path, ref_obj_path_str = inherits_target.split("#", 2)
          else
            ref_file_path = ""
            ref_obj_path_str = inherits_target.start_with?("/") ? inherits_target : "/#{inherits_target}"
          end

          ref_obj_path = ref_obj_path_str.split("/").drop(1)

          ref_obj = T.let(nil, T.nilable(T::Hash[String, T.untyped]))
          if ref_file_path.empty?
            ref_obj = T.unsafe(self).dig(doc_obj, *ref_obj_path)
            raise "#{ref_obj_path.join("/")} cannot be found in #{obj_file_path}" if ref_obj.nil?
            ref_obj = resolve_object(ref_obj, ref_obj_path, obj_file_path, doc_obj, arch_root, no_checks)
          else
            ref_full_path = arch_root / ref_file_path
            raise "#{ref_file_path} does not exist in #{arch_root}/" unless ref_full_path.exist?

            ref_doc_obj = get_resolved_object(ref_file_path, arch_root, no_checks)
            ref_obj = T.unsafe(self).dig(ref_doc_obj, *ref_obj_path)
            raise "#{ref_obj_path.join("/")} cannot be found in #{ref_file_path}" if ref_obj.nil?
          end

          ref_obj.each do |key, value|
            next if key == "$parent_of" || key == "$child_of"

            if parent_obj.key?(key) && parent_obj[key].is_a?(Hash) && value.is_a?(Hash)
              deep_merge!(parent_obj[key], value)
            else
              parent_obj[key] = deep_copy(value)
            end
          end

          child_ref = "#{obj_file_path}#/#{obj_path.join("/")}"
          if ref_obj.key?("$parent_of")
            ref_obj["$parent_of"] = [ref_obj["$parent_of"]] unless ref_obj["$parent_of"].is_a?(Array)
            ref_obj["$parent_of"] << child_ref
          else
            ref_obj["$parent_of"] = child_ref
          end
        end

        final_obj = T.let({}, T::Hash[String, T.untyped])
        all_keys = (parent_obj.keys + obj.keys).uniq

        all_keys.each do |key|
          if !obj.key?(key)
            final_obj[key] = parent_obj[key]
          elsif !parent_obj.key?(key)
            final_obj[key] = resolve_object(obj[key], obj_path + [key], obj_file_path, doc_obj, arch_root, no_checks)
          else
            if parent_obj[key].is_a?(Hash) && obj[key].is_a?(Hash)
              final_obj[key] = deep_merge(parent_obj[key], resolve_object(obj[key], obj_path + [key], obj_file_path, doc_obj, arch_root, no_checks))
            else
              final_obj[key] = resolve_object(obj[key], obj_path + [key], obj_file_path, doc_obj, arch_root, no_checks)
            end
          end
        end

        if final_obj.key?("$remove")
          remove_keys = final_obj["$remove"]
          remove_keys = [remove_keys] unless remove_keys.is_a?(Array)
          remove_keys.each { |key| final_obj.delete(key) }
          final_obj.delete("$remove")
        end

        final_obj
      end

      sig {
        params(
          rel_path: String,
          arch_root: Pathname,
          no_checks: T::Boolean
        ).returns(T::Hash[String, T.untyped])
      }
      def get_resolved_object(rel_path, arch_root, no_checks)
        return @resolved_objs.fetch(rel_path).fetch(:data) if @resolved_objs.key?(rel_path)

        input_path = arch_root / rel_path
        parser = CommentParser.new
        result = parser.parse_file(input_path)
        data = result[:data]

        resolved_data = resolve_object(data, [], rel_path, data, arch_root, no_checks)
        @resolved_objs[rel_path] = { data: resolved_data, comments: result[:comments] }

        resolved_data
      end

      sig { params(obj: T.untyped, keys: T.untyped).returns(T.untyped) }
      def dig(obj, *keys)
        return nil if obj.nil?
        return obj if keys.empty?

        key = keys[0]
        next_obj = obj[key]
        return nil if next_obj.nil?

        T.unsafe(self).dig(next_obj, *keys[1..])
      end

      sig {
        params(
          base: T.untyped,
          patch: T.untyped
        ).returns(T.untyped)
      }
      def json_merge_patch(base, patch)
        return patch unless patch.is_a?(Hash)
        return patch unless base.is_a?(Hash)

        result = base.dup

        patch.each do |key, value|
          if value.nil?
            result.delete(key)
          elsif value.is_a?(Hash) && result[key].is_a?(Hash)
            result[key] = json_merge_patch(result[key], value)
          else
            result[key] = deep_copy(value)
          end
        end

        result
      end

      sig {
        params(
          base: T::Hash[T.untyped, T.untyped],
          other: T::Hash[T.untyped, T.untyped]
        ).returns(T::Hash[T.untyped, T.untyped])
      }
      def deep_merge!(base, other)
        other.each do |key, value|
          if base[key].is_a?(Hash) && value.is_a?(Hash)
            deep_merge!(base[key], value)
          else
            base[key] = deep_copy(value)
          end
        end
        base
      end

      sig {
        params(
          base: T::Hash[T.untyped, T.untyped],
          other: T::Hash[T.untyped, T.untyped]
        ).returns(T::Hash[T.untyped, T.untyped])
      }
      def deep_merge(base, other)
        result = base.dup
        deep_merge!(result, other)
      end

      sig { params(obj: T.untyped).returns(T.untyped) }
      def deep_copy(obj)
        case obj
        when Hash
          obj.transform_values { |v| deep_copy(v) }
        when Array
          obj.map { |item| deep_copy(item) }
        else
          begin
            obj.dup
          rescue TypeError
            obj
          end
        end
      end

      sig {
        params(
          file_path: T.any(String, Pathname),
          comment_map: CommentMap
        ).void
      }
      def track_source_locations(file_path, comment_map)
        yaml_string = File.read(file_path, encoding: "utf-8")
        lines = yaml_string.lines

        cumulative_offsets = T.let([], T::Array[Integer])
        offset = 0
        lines.each do |line|
          cumulative_offsets << offset
          offset += line.bytesize
        end

        current_path = T.let([], T::Array[String])
        indent_stack = T.let([0], T::Array[Integer])
        in_multiline_string = T.let(false, T::Boolean)
        multiline_base_indent = 0

        lines.each_with_index do |line, line_num|
          next if line.strip.empty? || line.strip.start_with?("#")

          indent = T.must(line[/^\s*/]).length

          if in_multiline_string
            if indent > multiline_base_indent
              next
            else
              in_multiline_string = false
            end
          end

          while indent_stack.length > 1 && indent <= indent_stack.fetch(-1)
            indent_stack.pop
            current_path.pop
          end

          if line.include?(":")
            key = T.must(line.split(":", 2)).fetch(0).strip
            key = key.sub(/^-\s*/, "")

            unless key.empty?
              current_path << key

              value_part = T.must(line.split(":", 2))[1]
              column = calculate_value_column(line, value_part, line_num, lines)
              content_offset = calculate_content_offset(line, value_part, line_num, lines, cumulative_offsets)

              comment_map.set_source_location(current_path.dup, file_path.to_s, line_num + 1, column + 1, content_offset)
              indent_stack << indent

              if value_part && (value_part.strip.start_with?("|", ">"))
                in_multiline_string = true
                multiline_base_indent = indent
              end
            end
          end
        end
      end

      sig {
        params(
          line: String,
          value_part: T.nilable(String),
          line_num: Integer,
          lines: T::Array[String]
        ).returns(Integer)
      }
      def calculate_value_column(line, value_part, line_num, lines)
        return 0 if value_part.nil?

        colon_pos = line.index(":")
        return 0 if colon_pos.nil?

        value_stripped = value_part.strip

        if value_stripped.start_with?("|", ">")
          next_line_idx = line_num + 1
          while next_line_idx < lines.length
            next_line = lines.fetch(next_line_idx)
            if !next_line.strip.empty?
              return T.must(next_line[/^\s*/]).length
            end
            next_line_idx += 1
          end
          return colon_pos + 2
        end

        value_start = colon_pos + 1
        while value_start < line.length && line[value_start] == " "
          value_start += 1
        end

        value_start
      end

      sig {
        params(
          line: String,
          value_part: T.nilable(String),
          line_num: Integer,
          lines: T::Array[String],
          cumulative_offsets: T::Array[Integer]
        ).returns(Integer)
      }
      def calculate_content_offset(line, value_part, line_num, lines, cumulative_offsets)
        return 0 if value_part.nil?

        colon_pos = line.index(":")
        return 0 if colon_pos.nil?

        value_stripped = value_part.strip

        if value_stripped.start_with?("|", ">")
          next_line_idx = line_num + 1
          while next_line_idx < lines.length
            next_line = lines.fetch(next_line_idx)
            if !next_line.strip.empty?
              content_col = T.must(next_line[/^\s*/]).length
              return cumulative_offsets.fetch(next_line_idx) + content_col
            end
            next_line_idx += 1
          end
          return cumulative_offsets.fetch(line_num) + colon_pos + 2
        end

        value_start = colon_pos + 1
        value_start += 1 while value_start < line.length && line[value_start] == " "
        cumulative_offsets.fetch(line_num) + value_start
      end
    end
  end
end
