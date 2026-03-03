# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require 'psych'
require 'pathname'
require 'fileutils'
require 'json'

require 'idlc'

require_relative 'comment_parser'
require_relative 'preserving_emitter'

module Udb
  module Yaml
    # Ruby implementation of YAML resolver that preserves comments and order
    class Resolver
      def initialize(quiet: false, compile_idl: false)
        @quiet = quiet
        @compile_idl = compile_idl
        if @compile_idl
          @compiler = Idl::Compiler.new
        end
        @resolved_objs = {}
      end

      # Merge overlay on top of base architecture files
      # @param base_dir [String, Pathname] Base architecture directory
      # @param overlay_dir [String, Pathname] Overlay directory (can be nil)
      # @param output_dir [String, Pathname] Output directory for merged files
      def merge_files(base_dir, overlay_dir, output_dir)
        base_dir = Pathname.new(base_dir)
        overlay_dir = overlay_dir.nil? ? nil : Pathname.new(overlay_dir)
        output_dir = Pathname.new(output_dir)

        # Find all YAML files in base and overlay
        base_files = Dir.glob(base_dir / "**" / "*.yaml").map { |f| Pathname.new(f).relative_path_from(base_dir).to_s }
        overlay_files = overlay_dir.nil? ? [] : Dir.glob(overlay_dir / "**" / "*.yaml").map { |f| Pathname.new(f).relative_path_from(overlay_dir).to_s }
        all_files = (base_files + overlay_files).uniq

        all_files.each do |rel_path|
          merge_file(rel_path, base_dir, overlay_dir, output_dir)
        end

        puts "[INFO] Merged architecture files written to #{output_dir}" unless @quiet
      end

      # Merge a single file
      def merge_file(rel_path, base_dir, overlay_dir, output_dir)
        base_path = base_dir / rel_path
        overlay_path = overlay_dir.nil? ? nil : (overlay_dir / rel_path)
        output_path = output_dir / rel_path

        # Create output directory
        FileUtils.mkdir_p(output_path.dirname)

        if !base_path.exist? && (overlay_path.nil? || !overlay_path.exist?)
          # Neither exists, remove merged file if it exists
          FileUtils.rm_f(output_path) if output_path.exist?
        elsif overlay_path.nil? || !overlay_path.exist?
          # No overlay, just copy base
          if !output_path.exist? || base_path.mtime > output_path.mtime
            FileUtils.cp(base_path, output_path)
          end
        elsif !base_path.exist?
          # No base, just copy overlay
          if !output_path.exist? || overlay_path.mtime > output_path.mtime
            FileUtils.cp(overlay_path, output_path)
          end
        else
          # Both exist, merge them
          if !output_path.exist? || 
             base_path.mtime > output_path.mtime || 
             overlay_path.mtime > output_path.mtime
            
            # Parse both files with comments
            parser = CommentParser.new
            base_result = parser.parse_file(base_path)
            overlay_result = parser.parse_file(overlay_path)

            # Merge the data (overlay takes precedence)
            merged_data = json_merge_patch(base_result[:data], overlay_result[:data])

            # Use overlay's comments (they take precedence)
            emitter = PreservingEmitter.new(overlay_result[:comments])
            emitter.emit_file(merged_data, output_path)
          end
        end
      end

      # Resolve all files in a directory
      # @param input_dir [String, Pathname] Input directory with unresolved files
      # @param output_dir [String, Pathname] Output directory for resolved files
      # @param options [Hash] Options hash
      # @option options [Boolean] :no_checks Skip validation
      def resolve_files(input_dir, output_dir, options = {})
        input_dir = Pathname.new(input_dir)
        output_dir = Pathname.new(output_dir)
        no_checks = options[:no_checks] || false

        # Find all YAML files
        yaml_files = Dir.glob(input_dir / "**" / "*.yaml").map do |f|
          Pathname.new(f).relative_path_from(input_dir).to_s
        end

        # First pass: resolve all files
        yaml_files.each do |rel_path|
          resolve_file(rel_path, input_dir, output_dir, no_checks)
        end

        # Second pass: write resolved files (after all inheritance is resolved)
        yaml_files.each do |rel_path|
          write_resolved_file(rel_path, input_dir, output_dir, no_checks)
        end

        # Create index files
        FileUtils.mkdir_p(output_dir)
        File.write(output_dir / "index.yaml", Psych.dump(yaml_files))
        File.write(output_dir / "index.json", JSON.pretty_generate(yaml_files))

        puts "[INFO] Resolved architecture files written to #{output_dir}" unless @quiet
      end

      private

      # Resolve a single file (first pass - build resolution cache)
      def resolve_file(rel_path, input_dir, output_dir, no_checks)
        input_path = input_dir / rel_path
        output_path = output_dir / rel_path

        return unless input_path.exist?

        # Parse the file and track source locations
        parser = CommentParser.new
        result = parser.parse_file(input_path)
        data = result[:data]
        
        # Track source locations for all keys
        track_source_locations(input_path, result[:comments])
        @current_comment_map = result[:comments]

        # Validate name matches filename
        if !no_checks && data.key?("name")
          fn_name = Pathname.new(rel_path).basename(".yaml").to_s
          if fn_name != data["name"]
            raise "ERROR: 'name' key (#{data['name']}) must match filename (#{fn_name}) in #{rel_path}"
          end
        end

        # Resolve the data
        resolved_data = resolve_object(data, [], rel_path, data, input_dir, no_checks)
        
        # Cache the resolved object
        @resolved_objs[rel_path] = { data: resolved_data, comments: result[:comments] }
      end

      # Write a resolved file (second pass - after all resolutions are cached)
      def write_resolved_file(rel_path, input_dir, output_dir, no_checks)
        output_path = output_dir / rel_path
        
        return unless @resolved_objs.key?(rel_path)

        resolved_obj = @resolved_objs[rel_path][:data]
        comments = @resolved_objs[rel_path][:comments]

        # Add source metadata
        resolved_obj["$source"] = (input_dir / rel_path).realpath.to_s

        # Create output directory
        FileUtils.mkdir_p(output_path.dirname)

        # Write the resolved file
        emitter = PreservingEmitter.new(comments)
        emitter.emit_file(resolved_obj, output_path)

        # Set permissions
        FileUtils.chmod(0o666, output_path)
      end

      # Resolve an object (handle $inherits, $remove, etc.)
      def resolve_object(obj, obj_path, obj_file_path, doc_obj, arch_root, no_checks)
        return obj unless obj.is_a?(Hash) || obj.is_a?(Array)

        if obj.is_a?(Array)
          return obj.map.with_index do |item, idx|
            resolve_object(item, obj_path + [idx], obj_file_path, doc_obj, arch_root, no_checks)
          end
        end

        # Handle $inherits
        if obj.key?("$inherits")
          return resolve_inherits(obj, obj_path, obj_file_path, doc_obj, arch_root, no_checks)
        end

        # Recursively resolve nested objects
        resolved = {}
        obj.each do |key, value|
          resolved[key] = resolve_object(value, obj_path + [key], obj_file_path, doc_obj, arch_root, no_checks)
        end

        # Handle $remove
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
            # Look up the 1-indexed line number of the key in the source file.
            # For '|' style multiline strings, the IDL content starts on the line
            # after the key, so the 0-indexed content start line equals source_loc[:line]
            # (the 1-indexed key line number) — a convenient coincidence.
            source_loc = @current_comment_map&.get_source_location(obj_path + [key])
            starting_line = source_loc ? source_loc[:line] : 0
            parse_root =
              if key == "operation()"
                :instruction_operation
              elsif obj_path.include?("requirements")
                :constraint_body
              else
                :function_body
              end
            @compiler.parser.set_input_file(obj_file_path, starting_line)
            m = @compiler.parser.parse(obj.fetch(key), root: parse_root)
            if m.nil?
              raise SyntaxError, <<~MSG
                While parsing #{obj_file_path}:#{@compiler.parser.failure_line}

                #{@compiler.parser.failure_reason}
              MSG
            end
            ast = m.to_ast
            if ast.nil?
              raise "IDL compiler could not convert to ast"
            end
            ast.set_input_file(obj_file_path, starting_line)
            resolved[key_minus_args] = ast.to_h
          end
        end

        resolved
      end

      # Resolve $inherits directive
      def resolve_inherits(obj, obj_path, obj_file_path, doc_obj, arch_root, no_checks)
        inherits_targets = obj["$inherits"].is_a?(Array) ? obj["$inherits"] : [obj["$inherits"]]
        
        # Track inheritance
        obj["$child_of"] = obj["$inherits"]
        obj.delete("$inherits")

        # Build parent object by merging all inheritance targets
        parent_obj = {}

        inherits_targets.each do |inherits_target|
          # Handle both "file#/path" and "#/path" formats
          if inherits_target.include?("#")
            ref_file_path, ref_obj_path_str = inherits_target.split("#", 2)
          else
            # If no #, treat the whole thing as a path in the same file
            ref_file_path = ""
            ref_obj_path_str = inherits_target.start_with?("/") ? inherits_target : "/#{inherits_target}"
          end
          
          ref_obj_path = ref_obj_path_str.split("/").drop(1) # Drop empty first element

          ref_obj = nil
          if ref_file_path.empty?
            # Reference in same document
            ref_obj = dig(doc_obj, *ref_obj_path)
            raise "#{ref_obj_path.join('/')} cannot be found in #{obj_file_path}" if ref_obj.nil?
            ref_obj = resolve_object(ref_obj, ref_obj_path, obj_file_path, doc_obj, arch_root, no_checks)
          else
            # Reference to another document
            ref_full_path = arch_root / ref_file_path
            raise "#{ref_file_path} does not exist in #{arch_root}/" unless ref_full_path.exist?

            # Get or resolve the referenced document
            ref_doc_obj = get_resolved_object(ref_file_path, arch_root, no_checks)
            ref_obj = dig(ref_doc_obj, *ref_obj_path)
            raise "#{ref_obj_path.join('/')} cannot be found in #{ref_file_path}" if ref_obj.nil?
          end

          # Merge parent object
          ref_obj.each do |key, value|
            next if key == "$parent_of" || key == "$child_of"
            
            if parent_obj.key?(key) && parent_obj[key].is_a?(Hash) && value.is_a?(Hash)
              deep_merge!(parent_obj[key], value)
            else
              parent_obj[key] = deep_copy(value)
            end
          end

          # Track parent relationship
          child_ref = "#{obj_file_path}#/#{obj_path.join('/')}"
          if ref_obj.key?("$parent_of")
            ref_obj["$parent_of"] = [ref_obj["$parent_of"]] unless ref_obj["$parent_of"].is_a?(Array)
            ref_obj["$parent_of"] << child_ref
          else
            ref_obj["$parent_of"] = child_ref
          end
        end

        # Merge child over parent
        final_obj = {}
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

        # Handle $remove
        if final_obj.key?("$remove")
          remove_keys = final_obj["$remove"]
          remove_keys = [remove_keys] unless remove_keys.is_a?(Array)
          remove_keys.each { |key| final_obj.delete(key) }
          final_obj.delete("$remove")
        end

        final_obj
      end

      # Get a resolved object from cache or resolve it
      def get_resolved_object(rel_path, arch_root, no_checks)
        return @resolved_objs[rel_path][:data] if @resolved_objs.key?(rel_path)

        # Need to resolve it now
        input_path = arch_root / rel_path
        parser = CommentParser.new
        result = parser.parse_file(input_path)
        data = result[:data]

        resolved_data = resolve_object(data, [], rel_path, data, arch_root, no_checks)
        @resolved_objs[rel_path] = { data: resolved_data, comments: result[:comments] }
        
        resolved_data
      end

      # Navigate nested hash
      def dig(obj, *keys)
        return nil if obj.nil?
        return obj if keys.empty?

        key = keys[0]
        next_obj = obj[key]
        return nil if next_obj.nil?

        dig(next_obj, *keys[1..-1])
      end

      # JSON Merge Patch (RFC 7386)
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

      # Deep merge (mutating)
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

      # Deep merge (non-mutating)
      def deep_merge(base, other)
        result = base.dup
        deep_merge!(result, other)
      end

      # Deep copy an object
      def deep_copy(obj)
        case obj
        when Hash
          obj.transform_values { |v| deep_copy(v) }
        when Array
          obj.map { |item| deep_copy(item) }
        else
          obj.dup rescue obj
        end
      end

      # Track source locations for all keys in a file
      def track_source_locations(file_path, comment_map)
        yaml_string = File.read(file_path, encoding: "utf-8")
        lines = yaml_string.lines
        current_path = []
        indent_stack = [0]
        in_multiline_string = false
        multiline_base_indent = 0
        multiline_start_line = nil
        
        lines.each_with_index do |line, line_num|
          next if line.strip.empty? || line.strip.start_with?('#')
          
          indent = line[/^\s*/].length
          
          # If we're in a multiline string and this line is more indented than the key, skip it
          if in_multiline_string
            if indent > multiline_base_indent
              next  # Skip lines that are part of the multiline string content
            else
              # We've exited the multiline string
              in_multiline_string = false
            end
          end
          
          # Adjust path based on indentation
          while indent_stack.length > 1 && indent <= indent_stack[-1]
            indent_stack.pop
            current_path.pop
          end
          
          # Extract key if this is a key-value line (and not part of multiline content)
          if line.include?(':')
            key = line.split(':', 2)[0].strip
            key = key.sub(/^-\s*/, '')
            
            unless key.empty?
              current_path << key
              
              # Calculate column where value starts
              value_part = line.split(':', 2)[1]
              column = calculate_value_column(line, value_part, line_num, lines)
              
              # Store source location (1-indexed line and column numbers for user-friendliness)
              comment_map.set_source_location(current_path.dup, file_path.to_s, line_num + 1, column + 1)
              indent_stack << indent
              
              # Check if this key starts a multiline string (literal | or folded >)
              if value_part && (value_part.strip.start_with?('|') || value_part.strip.start_with?('>'))
                in_multiline_string = true
                multiline_base_indent = indent
                multiline_start_line = line_num
              end
            end
          end
        end
      end
      
      # Calculate the column where the value starts
      # For multiline strings (| or >), returns the column of the first content line
      # For inline values, returns the column after the colon and space
      def calculate_value_column(line, value_part, line_num, lines)
        return 0 if value_part.nil?
        
        # Find the colon position
        colon_pos = line.index(':')
        return 0 if colon_pos.nil?
        
        value_stripped = value_part.strip
        
        # For multiline strings (| or >), find the first content line
        if value_stripped.start_with?('|') || value_stripped.start_with?('>')
          # Look for the first non-empty line after the | or >
          next_line_idx = line_num + 1
          while next_line_idx < lines.length
            next_line = lines[next_line_idx]
            if !next_line.strip.empty? && !next_line.strip.start_with?('#')
              # Return the column where the content starts (after indentation)
              return next_line[/^\s*/].length
            end
            next_line_idx += 1
          end
          # If no content found, return column after the indicator
          return colon_pos + 2
        end
        
        # For inline values, find where the value actually starts (after colon and spaces)
        # Skip the colon and any following whitespace
        value_start = colon_pos + 1
        while value_start < line.length && line[value_start] == ' '
          value_start += 1
        end
        
        value_start
      end
    end
  end
end
