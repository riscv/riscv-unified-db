# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "psych"
require "sorbet-runtime"

module Udb
  module Yaml
    # Represents a single comment in a YAML file
    class Comment
      extend T::Sig

      sig { returns(Integer) }
      attr_reader :line

      sig { returns(Integer) }
      attr_reader :column

      sig { returns(String) }
      attr_reader :content

      sig { returns(Symbol) }
      attr_reader :type

      sig { returns(Integer) }
      attr_reader :indent

      sig {
        params(
          line: Integer,
          column: Integer,
          content: String,
          type: Symbol,
          indent: Integer
        ).void
      }
      def initialize(line, column, content, type, indent)
        @line = T.let(line, Integer)
        @column = T.let(column, Integer)
        @content = T.let(content, String)
        @type = T.let(type, Symbol)
        @indent = T.let(indent, Integer)
      end

      sig { returns(String) }
      def to_s
        "##{content}"
      end
    end

    # Maps key paths to their associated comments and string styles
    class CommentMap
      extend T::Sig

      sig { void }
      def initialize
        @comments = T.let({}, T::Hash[String, T::Array[Comment]])
        @header_comments = T.let([], T::Array[Comment])
        @trailing_comments = T.let([], T::Array[Comment])
        @string_styles = T.let({}, T::Hash[String, Symbol])
        @multiline_content = T.let({}, T::Hash[String, T::Array[String]])
        @source_locations = T.let({}, T::Hash[String, T::Hash[Symbol, T.untyped]])
      end

      sig { returns(T::Array[Comment]) }
      attr_reader :header_comments

      sig { returns(T::Array[Comment]) }
      attr_reader :trailing_comments

      private

      sig { params(key_path: T::Array[T.any(String, Integer)]).returns(String) }
      def path_key_for(key_path)
        key_path.join("/")
      end

      public

      sig {
        params(
          key_path: T::Array[T.any(String, Integer)],
          comment: Comment
        ).void
      }
      def add_comment(key_path, comment)
        path_key = path_key_for(key_path)
        @comments[path_key] ||= []
        @comments.fetch(path_key) << comment
      end

      sig {
        params(key_path: T::Array[T.any(String, Integer)]).returns(T::Array[Comment])
      }
      def get_comments(key_path)
        path_key = path_key_for(key_path)
        @comments[path_key] || []
      end

      sig { params(comment: Comment).void }
      def add_header_comment(comment)
        @header_comments << comment
      end

      sig { params(comment: Comment).void }
      def add_trailing_comment(comment)
        @trailing_comments << comment
      end

      sig {
        params(
          key_path: T::Array[T.any(String, Integer)],
          style: Symbol
        ).void
      }
      def set_string_style(key_path, style)
        path_key = path_key_for(key_path)
        @string_styles[path_key] = style
      end

      sig {
        params(key_path: T::Array[T.any(String, Integer)]).returns(T.nilable(Symbol))
      }
      def get_string_style(key_path)
        path_key = path_key_for(key_path)
        @string_styles[path_key]
      end

      # Copy string styles from +base_map+ for any keys not already present in this map.
      # Used when merging an overlay on top of a base file so that keys only present
      # in the base retain their original style.
      sig { params(base_map: CommentMap).void }
      def merge_styles_from(base_map)
        base_map.instance_variable_get(:@string_styles).each do |path_key, style|
          @string_styles[path_key] ||= style
        end
      end

      sig {
        params(
          key_path: T::Array[T.any(String, Integer)],
          lines: T::Array[String]
        ).void
      }
      def set_multiline_content(key_path, lines)
        path_key = path_key_for(key_path)
        @multiline_content[path_key] = lines
      end

      sig {
        params(key_path: T::Array[T.any(String, Integer)]).returns(T.nilable(T::Array[String]))
      }
      def get_multiline_content(key_path)
        path_key = path_key_for(key_path)
        @multiline_content[path_key]
      end

      sig {
        params(
          key_path: T::Array[T.any(String, Integer)],
          file: T.any(String, Pathname),
          line: Integer,
          column: Integer,
          offset: T.nilable(Integer),
          line_file_offsets: T.nilable(T::Array[Integer])
        ).void
      }
      def set_source_location(key_path, file, line, column, offset = nil, line_file_offsets = nil)
        path_key = path_key_for(key_path)
        @source_locations[path_key] = { file: file.to_s, line: line, column: column, offset: offset, line_file_offsets: line_file_offsets }
      end

      sig {
        params(key_path: T::Array[T.any(String, Integer)]).returns(T.nilable(T::Hash[Symbol, T.untyped]))
      }
      def get_source_location(key_path)
        path_key = path_key_for(key_path)
        @source_locations[path_key]
      end

      sig { returns(T::Hash[String, T::Hash[Symbol, T.untyped]]) }
      def all_source_locations
        @source_locations
      end

      sig { returns(T::Array[Comment]) }
      def all_comments
        @comments.values.flatten + @header_comments + @trailing_comments
      end
    end

    # Parses YAML files and extracts comments with their positions
    class CommentParser
      extend T::Sig

      sig {
        params(yaml_string: String).returns(T::Hash[Symbol, T.untyped])
      }
      def parse(yaml_string)
        lines = yaml_string.lines
        comment_map = CommentMap.new

        comments_by_line = extract_comments(lines)
        data = Psych.safe_load(yaml_string, permitted_classes: [Date, Symbol], aliases: true) || {}
        line_to_path = build_line_to_path_map(yaml_string)
        detect_string_styles(yaml_string, line_to_path, comment_map)
        associate_comments(comments_by_line, line_to_path, comment_map, data)

        { data: data, comments: comment_map }
      end

      sig {
        params(file_path: T.any(String, Pathname)).returns(T::Hash[Symbol, T.untyped])
      }
      def parse_file(file_path)
        parse(File.read(file_path, encoding: "utf-8"))
      end

      private

      sig {
        params(lines: T::Array[String]).returns(T::Hash[Integer, Comment])
      }
      def extract_comments(lines)
        comments = T.let({}, T::Hash[Integer, Comment])
        in_document = T.let(false, T::Boolean)

        lines.each_with_index do |line, line_num|
          next if line.strip.empty?

          unless in_document
            if line.strip.start_with?("#")
              indent = T.must(line[/^\s*/]).length
              content = T.must(line.strip[1..-1]).strip
              comments[line_num] = Comment.new(line_num, indent, content, :header, indent)
              next
            else
              in_document = true
            end
          end

          comment_pos = find_comment_position(line)
          if comment_pos
            before_hash = T.must(line[0...comment_pos])
            comment_content = T.must(line[comment_pos + 1..-1]).strip
            type = before_hash.strip.empty? ? :block : :inline
            indent = T.must(line[/^\s*/]).length
            comments[line_num] = Comment.new(line_num, comment_pos, comment_content, type, indent)
          end
        end

        comments
      end

      sig {
        params(line: String).returns(T.nilable(Integer))
      }
      def find_comment_position(line)
        in_single_quote = T.let(false, T::Boolean)
        in_double_quote = T.let(false, T::Boolean)
        escape_next = T.let(false, T::Boolean)

        line.chars.each_with_index do |char, idx|
          if escape_next
            escape_next = false
            next
          end

          case char
          when "\\"
            escape_next = true if in_single_quote || in_double_quote
          when "'"
            in_single_quote = !in_single_quote unless in_double_quote
          when '"'
            in_double_quote = !in_double_quote unless in_single_quote
          when "#"
            return idx unless in_single_quote || in_double_quote
          end
        end

        nil
      end

      sig {
        params(yaml_string: String).returns(T::Hash[Integer, T::Array[String]])
      }
      def build_line_to_path_map(yaml_string)
        line_to_path = T.let({}, T::Hash[Integer, T::Array[String]])
        current_path = T.let([], T::Array[String])
        indent_stack = T.let([0], T::Array[Integer])

        yaml_string.lines.each_with_index do |line, line_num|
          next if line.strip.empty? || line.strip.start_with?("#")

          indent = T.must(line[/^\s*/]).length

          while indent_stack.length > 1 && indent <= indent_stack.fetch(-1)
            indent_stack.pop
            current_path.pop
          end

          if line.include?(":")
            key = T.must(line.split(":", 2)).fetch(0).strip
            key = key.sub(/^-\s*/, "")

            unless key.empty?
              current_path << key
              line_to_path[line_num] = current_path.dup
              indent_stack << indent
            end
          end
        end

        line_to_path
      end

      sig {
        params(
          yaml_string: String,
          line_to_path: T::Hash[Integer, T::Array[String]],
          comment_map: CommentMap
        ).void
      }
      def detect_string_styles(yaml_string, line_to_path, comment_map)
        lines = yaml_string.lines
        lines.each_with_index do |line, line_num|
          next if line.strip.empty? || line.strip.start_with?("#")

          path = line_to_path[line_num]
          next unless line.include?(":") && path

          value_part = line.split(":", 2)[1]
          next if value_part.nil?

          value_part = value_part.strip

          if value_part.start_with?("|")
            comment_map.set_string_style(path, :literal)
          elsif value_part.start_with?(">")
            comment_map.set_string_style(path, :folded)
          elsif value_part.empty?
            next_line_idx = line_num + 1
            if next_line_idx < lines.length
              next_line = lines.fetch(next_line_idx)
              current_indent = T.must(line[/^\s*/]).length
              next_indent = T.must(next_line[/^\s*/]).length

              if next_indent > current_indent &&
                 !next_line.strip.empty? &&
                 !next_line.strip.start_with?("#") &&
                 !next_line.strip.start_with?("-") &&
                 !next_line.include?(":")
                comment_map.set_string_style(path, :plain_multiline)

                multiline_lines = T.let([], T::Array[String])
                idx = next_line_idx
                while idx < lines.length
                  line_content = lines.fetch(idx)
                  line_indent = T.must(line_content[/^\s*/]).length

                  break if line_indent <= current_indent && !line_content.strip.empty?
                  break if line_content.strip.start_with?("#")
                  break if line_content.include?(":")

                  if line_indent > current_indent && !line_content.strip.empty?
                    multiline_lines << line_content.strip
                  end

                  idx += 1
                end

                comment_map.set_multiline_content(path, multiline_lines) if multiline_lines.any?
              end
            end
          elsif value_part.start_with?('"', "'")
            comment_map.set_string_style(path, :quoted)
          else
            comment_map.set_string_style(path, :plain)
          end
        end
      end

      sig {
        params(
          comments_by_line: T::Hash[Integer, Comment],
          line_to_path: T::Hash[Integer, T::Array[String]],
          comment_map: CommentMap,
          data: T.untyped
        ).void
      }
      def associate_comments(comments_by_line, line_to_path, comment_map, data)
        sorted_lines = comments_by_line.keys.sort
        path_lines = line_to_path.keys.sort

        sorted_lines.each do |comment_line|
          comment = comments_by_line.fetch(comment_line)

          if comment.type == :header
            comment_map.add_header_comment(comment)
            next
          end

          if comment.type == :inline
            if line_to_path[comment_line]
              comment_map.add_comment(line_to_path.fetch(comment_line), comment)
            end
          else
            next_key_line = path_lines.find { |l| l > comment_line }
            if next_key_line
              comment_map.add_comment(line_to_path.fetch(next_key_line), comment)
            else
              comment_map.add_trailing_comment(comment)
            end
          end
        end
      end
    end
  end
end
