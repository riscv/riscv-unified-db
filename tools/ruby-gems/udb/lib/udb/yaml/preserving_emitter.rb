# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "psych"
require "stringio"
require "sorbet-runtime"
require_relative "comment_parser"

module Udb
  module Yaml
    # Emits YAML while preserving comments and formatting
    class PreservingEmitter
      extend T::Sig

      sig { params(comment_map: T.nilable(CommentMap)).void }
      def initialize(comment_map = nil)
        @comment_map = T.let(comment_map || CommentMap.new, CommentMap)
      end

      sig {
        params(
          data: T.untyped,
          io: T.nilable(T.any(IO, String))
        ).returns(String)
      }
      def emit(data, io = nil)
        output = StringIO.new

        @comment_map.header_comments.each do |comment|
          content = comment.content.strip
          output.puts "# #{content}" unless content.empty?
        end

        output.puts if @comment_map.header_comments.any?

        emit_value(data, output, [], 0)

        @comment_map.trailing_comments.each do |comment|
          output.puts "#{" " * comment.indent}# #{comment.content}"
        end

        source_locations = @comment_map.all_source_locations
        if source_locations.any?
          output.puts
          output.puts "# ===== SOURCE MAP BEGIN ====="
          output.puts "# This map tracks the original source file and line:column for each key"
          output.puts "# Format: key_path -> file:line:column"

          source_locations.keys.sort.each do |path_key|
            location = source_locations.fetch(path_key)
            output.puts "# #{path_key} -> #{location[:file]}:#{location[:line]}:#{location[:column]}"
          end

          output.puts "# ===== SOURCE MAP END ====="
        end

        result = output.string

        if io
          if io.is_a?(String)
            File.write(io, result)
          else
            io.write(result)
          end
        end

        result
      end

      sig {
        params(
          data: T.untyped,
          file_path: T.any(String, Pathname)
        ).void
      }
      def emit_file(data, file_path)
        emit(data, file_path.to_s)
      end

      private

      sig {
        params(
          value: T.untyped,
          output: StringIO,
          path: T::Array[T.any(String, Integer)],
          indent: Integer
        ).void
      }
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

      sig {
        params(
          hash: T::Hash[T.untyped, T.untyped],
          output: StringIO,
          path: T::Array[T.any(String, Integer)],
          indent: Integer
        ).void
      }
      def emit_hash(hash, output, path, indent)
        return output.puts "#{" " * indent}{}" if hash.empty?

        hash.each do |key, value|
          current_path = path + [key.to_s]
          comments = @comment_map.get_comments(current_path)

          block_comments = comments.select { |c| c.type == :block }
          block_comments.each do |comment|
            output.puts "#{" " * indent}# #{comment.content}"
          end

          if value.is_a?(Hash) || value.is_a?(Array)
            output.print "#{" " * indent}#{key}:"

            inline_comments = comments.select { |c| c.type == :inline }
            if inline_comments.any?
              output.print " # #{T.must(inline_comments.first).content}"
            end
            output.puts

            emit_value(value, output, current_path, indent + 2)
          else
            string_style = @comment_map.get_string_style(current_path)

            if string_style == :literal && value.is_a?(String) && value.include?("\n")
              output.print "#{" " * indent}#{key}: |"
              inline_comments = comments.select { |c| c.type == :inline }
              output.print " # #{T.must(inline_comments.first).content}" if inline_comments.any?
              output.puts
              value.lines.each { |line| output.print "#{" " * (indent + 2)}#{line}" }
            elsif string_style == :folded && value.is_a?(String) && value.include?("\n")
              output.print "#{" " * indent}#{key}: >"
              inline_comments = comments.select { |c| c.type == :inline }
              output.print " # #{T.must(inline_comments.first).content}" if inline_comments.any?
              output.puts
              value.lines.each { |line| output.print "#{" " * (indent + 2)}#{line}" }
            elsif string_style == :plain_multiline && value.is_a?(String)
              output.print "#{" " * indent}#{key}:"
              inline_comments = comments.select { |c| c.type == :inline }
              output.print " # #{T.must(inline_comments.first).content}" if inline_comments.any?
              output.puts

              original_lines = @comment_map.get_multiline_content(current_path)
              if original_lines && !original_lines.empty?
                original_lines.each { |line| output.puts "#{" " * (indent + 2)}#{line}" }
              else
                words = value.split(/\s+/)
                current_line = T.let("", String)
                words.each do |word|
                  if current_line.empty?
                    current_line = word
                  elsif (current_line.length + word.length + 1) <= 75
                    current_line += " #{word}"
                  else
                    output.puts "#{" " * (indent + 2)}#{current_line}"
                    current_line = word
                  end
                end
                output.puts "#{" " * (indent + 2)}#{current_line}" unless current_line.empty?
              end
            else
              output.print "#{" " * indent}#{key}: "
              emit_scalar(value, output, current_path, 0, inline: true, preserve_style: true)
              inline_comments = comments.select { |c| c.type == :inline }
              output.print " # #{T.must(inline_comments.first).content}" if inline_comments.any?
              output.puts
            end
          end
        end
      end

      sig {
        params(
          array: T::Array[T.untyped],
          output: StringIO,
          path: T::Array[T.any(String, Integer)],
          indent: Integer
        ).void
      }
      def emit_array(array, output, path, indent)
        return output.puts "#{" " * indent}[]" if array.empty?

        array.each_with_index do |item, index|
          current_path = path + [index]
          comments = @comment_map.get_comments(current_path)

          block_comments = comments.select { |c| c.type == :block }
          block_comments.each do |comment|
            output.puts "#{" " * indent}# #{comment.content}"
          end

          if item.is_a?(Hash)
            output.print "#{" " * indent}- "
            if item.empty?
              output.puts "{}"
            else
              first_key, first_value = item.first
              output.print "#{first_key}: "
              if first_value.is_a?(Hash) || first_value.is_a?(Array)
                output.puts
                emit_value(first_value, output, current_path + [first_key.to_s], indent + 4)
              else
                emit_scalar(first_value, output, current_path + [first_key.to_s], 0, inline: true)
                output.puts
              end

              item.drop(1).each do |key, value|
                output.print "#{" " * (indent + 2)}#{key}: "
                if value.is_a?(Hash) || value.is_a?(Array)
                  output.puts
                  emit_value(value, output, current_path + [key.to_s], indent + 4)
                else
                  emit_scalar(value, output, current_path + [key.to_s], 0, inline: true)
                  output.puts
                end
              end
            end
          elsif item.is_a?(Array)
            output.puts "#{" " * indent}-"
            emit_array(item, output, current_path, indent + 2)
          else
            output.print "#{" " * indent}- "
            emit_scalar(item, output, current_path, 0, inline: true)

            inline_comments = comments.select { |c| c.type == :inline }
            output.print " # #{T.must(inline_comments.first).content}" if inline_comments.any?
            output.puts
          end
        end
      end

      sig {
        params(
          value: T.untyped,
          output: StringIO,
          path: T::Array[T.any(String, Integer)],
          indent: Integer,
          inline: T::Boolean,
          preserve_style: T::Boolean
        ).void
      }
      def emit_scalar(value, output, path, indent, inline: false, preserve_style: false)
        formatted = format_scalar(value, path, preserve_style)
        if inline
          output.print formatted
        else
          output.puts "#{" " * indent}#{formatted}"
        end
      end

      sig {
        params(
          value: T.untyped,
          path: T::Array[T.any(String, Integer)],
          preserve_style: T::Boolean
        ).returns(String)
      }
      def format_scalar(value, path = [], preserve_style = false)
        case value
        when NilClass
          "null"
        when TrueClass
          "true"
        when FalseClass
          "false"
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

      sig {
        params(
          str: String,
          path: T::Array[T.any(String, Integer)],
          preserve_style: T::Boolean
        ).returns(String)
      }
      def format_string(str, path = [], preserve_style = false)
        if preserve_style
          string_style = @comment_map.get_string_style(path)
          if string_style == :plain
            return str unless needs_quoting?(str)
          elsif string_style == :quoted
            return "\"#{str.gsub('"', '\\"').gsub("\n", "\\n")}\""
          end
        end

        if needs_quoting?(str)
          "\"#{str.gsub('"', '\\"').gsub("\n", "\\n")}\""
        else
          str
        end
      end

      sig { params(str: String).returns(T::Boolean) }
      def needs_quoting?(str)
        return true if str.empty?
        return true if str.start_with?(" ") || str.end_with?(" ")
        return true if str.include?("\n")
        return true if str.include?(":") && str.include?(" ")
        return true if str.start_with?("#")
        return true if str.start_with?("-") && (str.length == 1 || str[1] == " ")
        return true if str.start_with?("[", "{")
        return true if str.start_with?(">", "<")
        return true if str.start_with?("|")
        return true if str.start_with?("`", "@")
        return true if str.start_with?("&", "*")
        return true if str.start_with?("!", "%")
        return true if str.start_with?("'", '"')
        return true if str.match?(/^(true|false|null|yes|no|on|off|~)$/i)
        return true if str.match?(/^\d+$/)
        return false if str.match?(/^\d+-\d+$/)
        return true if str.match?(/^[0-9]/)

        false
      end
    end
  end
end
