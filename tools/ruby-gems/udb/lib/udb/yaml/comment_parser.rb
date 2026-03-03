# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require 'psych'

module Udb
  module Yaml
    # Represents a single comment in a YAML file
    class Comment
      attr_reader :line, :column, :content, :type, :indent

      # @param line [Integer] Line number (0-indexed)
      # @param column [Integer] Column number (0-indexed)
      # @param content [String] Comment text (without the # character)
      # @param type [Symbol] :inline, :block, or :header
      # @param indent [Integer] Indentation level
      def initialize(line, column, content, type, indent)
        @line = line
        @column = column
        @content = content
        @type = type
        @indent = indent
      end

      def to_s
        "##{content}"
      end
    end

    # Maps key paths to their associated comments and string styles
    class CommentMap
      def initialize
        @comments = {}
        @header_comments = []
        @trailing_comments = []
        @string_styles = {}
        @multiline_content = {}
        @source_locations = {}
      end

      attr_reader :header_comments, :trailing_comments

      # Add a comment associated with a key path
      # @param key_path [Array<String, Integer>] Path to the key (e.g., ["extensions", 0, "name"])
      # @param comment [Comment] The comment to add
      def add_comment(key_path, comment)
        path_key = key_path.join("/")
        @comments[path_key] ||= []
        @comments[path_key] << comment
      end

      # Get comments for a key path
      # @param key_path [Array<String, Integer>] Path to the key
      # @return [Array<Comment>] Comments associated with this path
      def get_comments(key_path)
        path_key = key_path.join("/")
        @comments[path_key] || []
      end

      # Add a header comment (before document starts)
      def add_header_comment(comment)
        @header_comments << comment
      end

      # Add a trailing comment (after document ends)
      def add_trailing_comment(comment)
        @trailing_comments << comment
      end

      # Set the string style for a key path
      # @param key_path [Array<String, Integer>] Path to the key
      # @param style [Symbol] :literal (|), :folded (>), :quoted, or :plain
      def set_string_style(key_path, style)
        path_key = key_path.join("/")
        @string_styles[path_key] = style
      end

      # Get the string style for a key path
      # @param key_path [Array<String, Integer>] Path to the key
      # @return [Symbol, nil] The string style or nil if not set
      def get_string_style(key_path)
        path_key = key_path.join("/")
        @string_styles[path_key]
      end

      # Set the original multiline content for a key path
      # @param key_path [Array<String, Integer>] Path to the key
      # @param lines [Array<String>] The original lines of the multiline string
      def set_multiline_content(key_path, lines)
        path_key = key_path.join("/")
        @multiline_content[path_key] = lines
      end

      # Get the original multiline content for a key path
      # @param key_path [Array<String, Integer>] Path to the key
      # @return [Array<String>, nil] The original lines or nil if not set
      def get_multiline_content(key_path)
        path_key = key_path.join("/")
        @multiline_content[path_key]
      end

      # Set the source location for a key path
      # @param key_path [Array<String, Integer>] Path to the key
      # @param file [String] Source file path
      # @param line [Integer] Line number in source file
      # @param column [Integer] Column number where value starts in source file
      def set_source_location(key_path, file, line, column)
        path_key = key_path.join("/")
        @source_locations[path_key] = { file: file, line: line, column: column }
      end

      # Get the source location for a key path
      # @param key_path [Array<String, Integer>] Path to the key
      # @return [Hash, nil] Hash with :file, :line, and :column keys, or nil if not set
      def get_source_location(key_path)
        path_key = key_path.join("/")
        @source_locations[path_key]
      end

      # Get all source locations as a hash
      # @return [Hash] Map of path keys to source locations
      def all_source_locations
        @source_locations
      end

      def all_comments
        @comments.values.flatten + @header_comments + @trailing_comments
      end
    end

    # Parses YAML files and extracts comments with their positions
    class CommentParser
      # Parse a YAML string and extract both data and comments
      # @param yaml_string [String] The YAML content
      # @return [Hash] { data: parsed_hash, comments: CommentMap }
      def parse(yaml_string)
        lines = yaml_string.lines
        comment_map = CommentMap.new
        
        # Extract comments with their line numbers
        comments_by_line = extract_comments(lines)
        
        # Parse the YAML data
        data = Psych.safe_load(yaml_string, permitted_classes: [Date, Symbol], aliases: true) || {}
        
        # Build a map of line numbers to key paths
        line_to_path = build_line_to_path_map(yaml_string)
        
        # Detect string styles
        detect_string_styles(yaml_string, line_to_path, comment_map)
        
        # Associate comments with key paths
        associate_comments(comments_by_line, line_to_path, comment_map, data)
        
        { data: data, comments: comment_map }
      end

      # Parse a YAML file
      # @param file_path [String, Pathname] Path to the YAML file
      # @return [Hash] { data: parsed_hash, comments: CommentMap }
      def parse_file(file_path)
        parse(File.read(file_path, encoding: "utf-8"))
      end

      private

      # Extract all comments from lines with their positions
      def extract_comments(lines)
        comments = {}
        in_document = false
        
        lines.each_with_index do |line, line_num|
          # Skip empty lines
          next if line.strip.empty?
          
          # Check if we've started the document (first non-comment, non-empty line)
          unless in_document
            if line.strip.start_with?('#')
              # Header comment
              indent = line[/^\s*/].length
              content = line.strip[1..-1].strip
              comments[line_num] = Comment.new(line_num, indent, content, :header, indent)
              next
            else
              in_document = true
            end
          end
          
          # Check for inline or block comments
          # Need to be careful about # in strings
          comment_pos = find_comment_position(line)
          if comment_pos
            before_hash = line[0...comment_pos]
            comment_content = line[comment_pos+1..-1].strip
            
            # Determine if it's inline or block
            type = before_hash.strip.empty? ? :block : :inline
            indent = line[/^\s*/].length
            
            comments[line_num] = Comment.new(line_num, comment_pos, comment_content, type, indent)
          end
        end
        
        comments
      end
      
      # Find the position of a comment # character, ignoring # inside strings
      def find_comment_position(line)
        in_single_quote = false
        in_double_quote = false
        escape_next = false
        
        line.chars.each_with_index do |char, idx|
          if escape_next
            escape_next = false
            next
          end
          
          case char
          when '\\'
            escape_next = true if in_single_quote || in_double_quote
          when "'"
            in_single_quote = !in_single_quote unless in_double_quote
          when '"'
            in_double_quote = !in_double_quote unless in_single_quote
          when '#'
            return idx unless in_single_quote || in_double_quote
          end
        end
        
        nil
      end

      # Build a map from line numbers to key paths
      # This is a simplified version - a full implementation would use Psych's AST
      def build_line_to_path_map(yaml_string)
        line_to_path = {}
        current_path = []
        indent_stack = [0]
        
        yaml_string.lines.each_with_index do |line, line_num|
          # Skip comments and empty lines
          next if line.strip.empty? || line.strip.start_with?('#')
          
          indent = line[/^\s*/].length
          
          # Adjust path based on indentation
          while indent_stack.length > 1 && indent <= indent_stack[-1]
            indent_stack.pop
            current_path.pop
          end
          
          # Extract key if this is a key-value line
          if line.include?(':')
            key = line.split(':', 2)[0].strip
            # Remove array indicator if present
            key = key.sub(/^-\s*/, '')
            
            unless key.empty?
              current_path << key
              line_to_path[line_num] = current_path.dup
              indent_stack << indent
            end
          elsif line.strip.start_with?('-')
            # Array item
            # For simplicity, we'll track these as numeric indices
            # A full implementation would need more sophisticated tracking
          end
        end
        
        line_to_path
      end

      # Detect string styles (literal |, folded >, implicit multiline, quoted, etc.)
      def detect_string_styles(yaml_string, line_to_path, comment_map)
        lines = yaml_string.lines
        lines.each_with_index do |line, line_num|
          # Skip comments and empty lines
          next if line.strip.empty? || line.strip.start_with?('#')
          
          # Check if this line has a key with a value
          if line.include?(':') && line_to_path[line_num]
            value_part = line.split(':', 2)[1]
            next if value_part.nil?
            
            value_part = value_part.strip
            
            # Check for literal block scalar (|) or folded block scalar (>)
            if value_part.start_with?('|')
              comment_map.set_string_style(line_to_path[line_num], :literal)
            elsif value_part.start_with?('>')
              comment_map.set_string_style(line_to_path[line_num], :folded)
            elsif value_part.empty?
              # Key with no value on same line - check if next lines are indented plain scalar
              # (not a nested object with keys)
              next_line_idx = line_num + 1
              if next_line_idx < lines.length
                next_line = lines[next_line_idx]
                current_indent = line[/^\s*/].length
                next_indent = next_line[/^\s*/].length
                
                # If next line is more indented and doesn't have a colon (not a nested key)
                if next_indent > current_indent && 
                   !next_line.strip.empty? && 
                   !next_line.strip.start_with?('#') &&
                   !next_line.strip.start_with?('-') &&
                   !next_line.include?(':')
                  # This is an implicit multiline plain scalar
                  comment_map.set_string_style(line_to_path[line_num], :plain_multiline)
                  
                  # Capture the original lines
                  multiline_lines = []
                  idx = next_line_idx
                  while idx < lines.length
                    line_content = lines[idx]
                    line_indent = line_content[/^\s*/].length
                    
                    # Stop if we hit a line that's not part of this multiline string
                    break if line_indent <= current_indent && !line_content.strip.empty?
                    break if line_content.strip.start_with?('#')
                    break if line_content.include?(':')
                    
                    # Add this line if it's part of the multiline content
                    if line_indent > current_indent && !line_content.strip.empty?
                      multiline_lines << line_content.strip
                    end
                    
                    idx += 1
                  end
                  
                  comment_map.set_multiline_content(line_to_path[line_num], multiline_lines) if multiline_lines.any?
                end
              end
            elsif value_part.start_with?('"') || value_part.start_with?("'")
              # Quoted string
              comment_map.set_string_style(line_to_path[line_num], :quoted)
            else
              # Plain unquoted scalar on same line
              comment_map.set_string_style(line_to_path[line_num], :plain)
            end
          end
        end
      end

      # Associate comments with their nearest key paths
      def associate_comments(comments_by_line, line_to_path, comment_map, data)
        sorted_lines = comments_by_line.keys.sort
        path_lines = line_to_path.keys.sort
        
        sorted_lines.each do |comment_line|
          comment = comments_by_line[comment_line]
          
          if comment.type == :header
            comment_map.add_header_comment(comment)
            next
          end
          
          # Find the nearest key path
          if comment.type == :inline
            # Inline comment belongs to the same line
            if line_to_path[comment_line]
              comment_map.add_comment(line_to_path[comment_line], comment)
            end
          else
            # Block comment belongs to the next key
            next_key_line = path_lines.find { |l| l > comment_line }
            if next_key_line
              comment_map.add_comment(line_to_path[next_key_line], comment)
            else
              comment_map.add_trailing_comment(comment)
            end
          end
        end
      end
    end
  end
end
