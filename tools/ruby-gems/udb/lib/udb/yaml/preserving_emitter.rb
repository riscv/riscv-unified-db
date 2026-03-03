# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require 'psych'
require 'stringio'
require_relative 'comment_parser'

module Udb
  module Yaml
    # Emits YAML while preserving comments and formatting
    class PreservingEmitter
      def initialize(comment_map = nil)
        @comment_map = comment_map || CommentMap.new
      end

      # Emit data as YAML with comments preserved
      # @param data [Hash, Array] The data to emit
      # @param io [IO, String] Output destination (IO object or file path)
      # @return [String] The emitted YAML string
      def emit(data, io = nil)
        output = StringIO.new

        # Write header comments
        @comment_map.header_comments.each do |comment|
          content = comment.content.strip
          output.puts "# #{content}" unless content.empty?
        end

        # Add blank line after header comments if there are any
        output.puts if @comment_map.header_comments.any?

        # Emit the data with inline comments
        emit_value(data, output, [], 0)

        # Write trailing comments
        @comment_map.trailing_comments.each do |comment|
          output.puts "#{' ' * comment.indent}# #{comment.content}"
        end

        # Write source map if we have source locations
        source_locations = @comment_map.all_source_locations
        if source_locations.any?
          output.puts
          output.puts "# ===== SOURCE MAP BEGIN ====="
          output.puts "# This map tracks the original source file and line:column for each key"
          output.puts "# Format: key_path -> file:line:column"

          # Sort by key path for consistent output
          source_locations.keys.sort.each do |path_key|
            location = source_locations[path_key]
            output.puts "# #{path_key} -> #{location[:file]}:#{location[:line]}:#{location[:column]}"
          end

          output.puts "# ===== SOURCE MAP END ====="
        end

        result = output.string

        # Write to IO if provided
        if io
          if io.is_a?(String)
            File.write(io, result)
          else
            io.write(result)
          end
        end

        result
      end

      # Emit to a file
      # @param data [Hash, Array] The data to emit
      # @param file_path [String, Pathname] Path to output file
      def emit_file(data, file_path)
        emit(data, file_path)
      end

      private

      # Emit a value (hash, array, or scalar) with proper indentation and comments
      def emit_value(value, output, path, indent)
        case value
        when Hash
          emit_hash(value, output, path, indent)
        when Array
          emit_array(value, output, path, indent)
        else
          emit_scalar(value, output, path, indent)
        end
      end

      # Emit a hash with comments
      def emit_hash(hash, output, path, indent)
        return output.puts "#{' ' * indent}{}" if hash.empty?

        hash.each_with_index do |(key, value), index|
          current_path = path + [key]
          comments = @comment_map.get_comments(current_path)

          # Write block comments before the key
          block_comments = comments.select { |c| c.type == :block }
          block_comments.each do |comment|
            output.puts "#{' ' * indent}# #{comment.content}"
          end

          # Write the key
          if value.is_a?(Hash) || value.is_a?(Array)
            output.print "#{' ' * indent}#{key}:"

            # Write inline comments
            inline_comments = comments.select { |c| c.type == :inline }
            if inline_comments.any?
              output.print " # #{inline_comments.first.content}"
            end
            output.puts

            # Write the value on next line(s)
            emit_value(value, output, current_path, indent + 2)
          else
            # Check if this is a multiline string with a specific style
            string_style = @comment_map.get_string_style(current_path)

            if string_style == :literal && value.is_a?(String) && value.include?("\n")
              # Emit as literal block scalar (|)
              output.print "#{' ' * indent}#{key}: |"

              # Write inline comments
              inline_comments = comments.select { |c| c.type == :inline }
              if inline_comments.any?
                output.print " # #{inline_comments.first.content}"
              end
              output.puts

              # Write the string content with proper indentation
              value.lines.each do |line|
                output.print "#{' ' * (indent + 2)}#{line}"
              end
            elsif string_style == :folded && value.is_a?(String) && value.include?("\n")
              # Emit as folded block scalar (>)
              output.print "#{' ' * indent}#{key}: >"

              # Write inline comments
              inline_comments = comments.select { |c| c.type == :inline }
              if inline_comments.any?
                output.print " # #{inline_comments.first.content}"
              end
              output.puts

              # Write the string content with proper indentation
              value.lines.each do |line|
                output.print "#{' ' * (indent + 2)}#{line}"
              end
            elsif string_style == :plain_multiline && value.is_a?(String)
              # Emit as implicit multiline plain scalar (no | or >)
              output.print "#{' ' * indent}#{key}:"

              # Write inline comments
              inline_comments = comments.select { |c| c.type == :inline }
              if inline_comments.any?
                output.print " # #{inline_comments.first.content}"
              end
              output.puts

              # Check if we have the original line structure
              original_lines = @comment_map.get_multiline_content(current_path)
              if original_lines && !original_lines.empty?
                # Use the original line breaks
                original_lines.each do |line|
                  output.puts "#{' ' * (indent + 2)}#{line}"
                end
              else
                # Fall back to word wrapping
                words = value.split(/\s+/)
                current_line = ""
                words.each do |word|
                  if current_line.empty?
                    current_line = word
                  elsif (current_line.length + word.length + 1) <= 75
                    current_line += " #{word}"
                  else
                    output.puts "#{' ' * (indent + 2)}#{current_line}"
                    current_line = word
                  end
                end
                output.puts "#{' ' * (indent + 2)}#{current_line}" unless current_line.empty?
              end
            else
              # Regular scalar - check if it should be quoted or plain
              output.print "#{' ' * indent}#{key}: "
              emit_scalar(value, output, current_path, 0, inline: true, preserve_style: true)

              # Write inline comments
              inline_comments = comments.select { |c| c.type == :inline }
              if inline_comments.any?
                output.print " # #{inline_comments.first.content}"
              end
              output.puts
            end
          end
        end
      end

      # Emit an array with comments
      def emit_array(array, output, path, indent)
        return output.puts "#{' ' * indent}[]" if array.empty?

        array.each_with_index do |item, index|
          current_path = path + [index]
          comments = @comment_map.get_comments(current_path)

          # Write block comments before the item
          block_comments = comments.select { |c| c.type == :block }
          block_comments.each do |comment|
            output.puts "#{' ' * indent}# #{comment.content}"
          end

          if item.is_a?(Hash)
            # For hash items, write the dash and then the hash on the same line
            output.print "#{' ' * indent}- "
            if item.empty?
              output.puts "{}"
            else
              # Write first key-value pair on same line as dash
              first_key, first_value = item.first
              output.print "#{first_key}: "
              if first_value.is_a?(Hash) || first_value.is_a?(Array)
                output.puts
                emit_value(first_value, output, current_path + [first_key], indent + 4)
              else
                emit_scalar(first_value, output, current_path + [first_key], 0, inline: true)
                output.puts
              end

              # Write remaining key-value pairs
              item.drop(1).each do |key, value|
                output.print "#{' ' * (indent + 2)}#{key}: "
                if value.is_a?(Hash) || value.is_a?(Array)
                  output.puts
                  emit_value(value, output, current_path + [key], indent + 4)
                else
                  emit_scalar(value, output, current_path + [key], 0, inline: true)
                  output.puts
                end
              end
            end
          elsif item.is_a?(Array)
            output.puts "#{' ' * indent}-"
            emit_array(item, output, current_path, indent + 2)
          else
            output.print "#{' ' * indent}- "
            emit_scalar(item, output, current_path, 0, inline: true)

            # Write inline comments
            inline_comments = comments.select { |c| c.type == :inline }
            if inline_comments.any?
              output.print " # #{inline_comments.first.content}"
            end
            output.puts
          end
        end
      end

      # Emit a scalar value
      def emit_scalar(value, output, path, indent, inline: false, preserve_style: false)
        formatted = format_scalar(value, path, preserve_style)
        if inline
          output.print formatted
        else
          output.puts "#{' ' * indent}#{formatted}"
        end
      end

      # Format a scalar value appropriately
      def format_scalar(value, path = [], preserve_style = false)
        case value
        when nil
          'null'
        when true
          'true'
        when false
          'false'
        when Numeric
          value.to_s
        when String
          format_string(value, path, preserve_style)
        when Symbol
          ":#{value}"
        when Date
          value.to_s
        else
          value.to_s
        end
      end

      # Format a string value, adding quotes if necessary
      def format_string(str, path = [], preserve_style = false)
        # If preserving style, check if it was originally plain (unquoted)
        if preserve_style
          string_style = @comment_map.get_string_style(path)
          if string_style == :plain
            # Keep it plain/unquoted unless it absolutely needs quoting
            return str unless needs_quoting?(str)
          elsif string_style == :quoted
            # It was originally quoted, keep it quoted
            return "\"#{str.gsub('"', '\\"').gsub("\n", '\\n')}\""
          end
        end

        # Default behavior: quote if necessary
        if needs_quoting?(str)
          "\"#{str.gsub('"', '\\"').gsub("\n", '\\n')}\""
        else
          str
        end
      end

      # Determine if a string needs quoting
      def needs_quoting?(str)
        return true if str.empty?
        return true if str.start_with?(' ') || str.end_with?(' ')
        return true if str.include?("\n")
        return true if str.include?(':') && str.include?(' ')
        return true if str.start_with?('#')
        return true if str.start_with?('-') && (str.length == 1 || str[1] == ' ')  # Quote standalone '-' and list markers
        return true if str.start_with?('[') || str.start_with?('{')
        return true if str.start_with?('>') || str.start_with?('<')  # Quote comparison operators
        return true if str.start_with?('|')  # Quote literal block scalar indicator
        return true if str.start_with?('`') || str.start_with?('@')  # YAML reserved indicators
        return true if str.start_with?('&') || str.start_with?('*')  # YAML anchor/alias indicators
        return true if str.start_with?('!') || str.start_with?('%')  # YAML tag/directive indicators
        return true if str.start_with?("'") || str.start_with?('"')  # Quote characters
        return true if str.match?(/^(true|false|null|yes|no|on|off|~)$/i)
        # Quote pure integers (strings that look like integers must be quoted to preserve type)
        return true if str.match?(/^\d+$/)
        # Don't quote bit ranges like "31-0"
        return false if str.match?(/^\d+-\d+$/)
        # Quote if starts with digit but isn't a bit range (e.g., "1.5", "1e10")
        return true if str.match?(/^[0-9]/)
        false
      end
    end
  end
end
