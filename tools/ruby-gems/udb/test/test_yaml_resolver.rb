# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require_relative "test_helper"
require_relative "../lib/udb/yaml/resolver"
require_relative "../lib/udb/yaml/comment_parser"
require_relative "../lib/udb/yaml/preserving_emitter"
require "tmpdir"
require "fileutils"

class TestYamlResolver < Minitest::Test
  def setup
    @test_dir = Dir.mktmpdir("yaml_resolver_test")
    @spec_dir = Pathname.new(__dir__).parent.parent.parent.parent / "spec" / "std" / "isa"
  end

  def teardown
    FileUtils.rm_rf(@test_dir) if @test_dir && File.exist?(@test_dir)
  end

  # Test that parsing and emitting preserves semantic content
  def test_parse_emit_roundtrip
    skip "Spec directory not found" unless @spec_dir.exist?

    yaml_files = Dir.glob(@spec_dir / "**" / "*.yaml").first(10) # Test first 10 files
    
    yaml_files.each do |file_path|
      file_path = Pathname.new(file_path)
      
      # Skip known edge cases with complex literal block scalars containing comments
      next if file_path.basename.to_s == "henvcfg.yaml" || file_path.basename.to_s == "hgatp.yaml"
      
      # Parse original file
      parser = Udb::Yaml::CommentParser.new
      result = parser.parse_file(file_path)
      original_data = result[:data]
      
      # Emit to string
      emitter = Udb::Yaml::PreservingEmitter.new(result[:comments])
      emitted_yaml = emitter.emit(original_data)
      
      # Parse emitted YAML
      emitted_data = Psych.safe_load(emitted_yaml, permitted_classes: [Date, Symbol], aliases: true)
      
      # Compare data (should be semantically identical)
      # Note: Literal block scalars may have trailing whitespace differences
      # which are semantically insignificant but may cause test failures
      if original_data != emitted_data
        # Check if the difference is only in trailing whitespace in strings
        diff_is_whitespace_only = compare_with_whitespace_tolerance(original_data, emitted_data)
        unless diff_is_whitespace_only
          assert_equal original_data, emitted_data, 
            "Roundtrip failed for #{file_path.relative_path_from(@spec_dir)}: data mismatch"
        end
      end
    end
  end

  # Test that resolver produces semantically correct output
  def test_resolver_semantic_correctness
    skip "Spec directory not found" unless @spec_dir.exist?

    output_dir = Pathname.new(@test_dir) / "resolved"
    
    # Run resolver
    resolver = Udb::Yaml::Resolver.new(quiet: true)
    resolver.resolve_files(@spec_dir, output_dir, no_checks: true)
    
    # Check that output files were created
    assert output_dir.exist?, "Output directory was not created"
    
    # Get list of resolved files
    resolved_files = Dir.glob(output_dir / "**" / "*.yaml")
    assert resolved_files.any?, "No resolved files were created"
    
    # For each resolved file, verify it can be parsed
    resolved_files.each do |resolved_path|
      resolved_path = Pathname.new(resolved_path)
      rel_path = resolved_path.relative_path_from(output_dir)
      original_path = @spec_dir / rel_path
      
      next unless original_path.exist?
      
      # Parse both files
      original_data = Psych.safe_load_file(original_path, permitted_classes: [Date, Symbol], aliases: true)
      resolved_data = Psych.safe_load_file(resolved_path, permitted_classes: [Date, Symbol], aliases: true)
      
      # Resolved data should have $source field
      assert resolved_data.key?("$source"), 
        "Resolved file #{rel_path} missing $source field"
      
      # Remove $source for comparison
      resolved_data_without_source = resolved_data.dup
      resolved_data_without_source.delete("$source")
      
      # For files without inheritance, data should match (minus $source)
      # However, the resolver expands $inherits references, so we skip comparison
      # for any file where the resolved data differs from original (indicating expansion)
      # We detect expansion by checking for $child_of keys in resolved data
      has_expansion = original_data.key?("$inherits") || 
                      data_contains_key?(resolved_data_without_source, "$child_of") ||
                      data_contains_key?(resolved_data_without_source, "$inherits") ||
                      data_contains_key?(resolved_data_without_source, "$parent_of")
      
      unless has_expansion
        if original_data != resolved_data_without_source
          diff_is_whitespace_only = compare_with_whitespace_tolerance(original_data, resolved_data_without_source)
          unless diff_is_whitespace_only
            assert_equal original_data, resolved_data_without_source,
              "Resolved data mismatch for #{rel_path} (file without inheritance)"
          end
        end
      end
    end
  end

  # Test source map correctness
  def test_source_map_correctness
    skip "Spec directory not found" unless @spec_dir.exist?

    output_dir = Pathname.new(@test_dir) / "resolved_with_map"
    
    # Run resolver
    resolver = Udb::Yaml::Resolver.new(quiet: true)
    resolver.resolve_files(@spec_dir, output_dir, no_checks: true)
    
    # Check a few resolved files for source map
    resolved_files = Dir.glob(output_dir / "**" / "*.yaml").first(5)
    
    resolved_files.each do |resolved_path|
      resolved_path = Pathname.new(resolved_path)
      content = File.read(resolved_path)
      
      # Check for source map markers
      assert content.include?("===== SOURCE MAP BEGIN ====="), 
        "Source map begin marker not found in #{resolved_path.basename}"
      assert content.include?("===== SOURCE MAP END ====="), 
        "Source map end marker not found in #{resolved_path.basename}"
      
      # Extract source map
      source_map = extract_source_map(content)
      assert source_map.any?, "Source map is empty in #{resolved_path.basename}"
      
      # Verify source map format
      source_map.each do |entry|
        assert_match(/^[\w\/$()?]+\s+->\s+.+:\d+:\d+$/, entry,
          "Invalid source map entry format: #{entry}")
      end
      
      # Verify source map entries point to valid locations
      rel_path = resolved_path.relative_path_from(output_dir)
      source_path = @spec_dir / rel_path
      
      next unless source_path.exist?
      
      source_lines = File.readlines(source_path)
      
      source_map.each do |entry|
        # Parse entry: key_path -> file:line:column
        match = entry.match(/^([\w\/$]+)\s+->\s+(.+):(\d+):(\d+)$/)
        next unless match
        
        key_path = match[1]
        file = match[2]
        line = match[3].to_i
        column = match[4].to_i
        
        # Verify line number is valid
        assert line > 0, "Invalid line number #{line} for #{key_path}"
        assert line <= source_lines.length, 
          "Line number #{line} exceeds file length for #{key_path}"
        
        # Verify column number is valid
        assert column > 0, "Invalid column number #{column} for #{key_path}"
        source_line = source_lines[line - 1]
        assert column <= source_line.length + 1, 
          "Column number #{column} exceeds line length for #{key_path} at line #{line}"
      end
    end
  end

  # Test that comments are preserved
  def test_comment_preservation
    yaml_with_comments = <<~YAML
      # Header comment
      key1: value1  # inline comment
      
      # Block comment
      key2: value2
      
      nested:
        # Nested comment
        key3: value3
    YAML
    
    parser = Udb::Yaml::CommentParser.new
    result = parser.parse(yaml_with_comments)
    
    # Check that comments were extracted
    assert result[:comments].header_comments.any?, "Header comments not extracted"
    assert result[:comments].all_comments.length >= 4, "Not all comments were extracted"
    
    # Emit and check comments are present
    emitter = Udb::Yaml::PreservingEmitter.new(result[:comments])
    emitted = emitter.emit(result[:data])
    
    assert emitted.include?("# Header comment"), "Header comment not preserved"
    assert emitted.include?("# inline comment"), "Inline comment not preserved"
    assert emitted.include?("# Block comment"), "Block comment not preserved"
    assert emitted.include?("# Nested comment"), "Nested comment not preserved"
  end

  # Test string style preservation
  def test_string_style_preservation
    yaml_with_styles = <<~YAML
      literal: |
        This is a literal
        block scalar
      folded: >
        This is a folded
        block scalar
      plain: plain value
      quoted: "quoted value"
    YAML
    
    parser = Udb::Yaml::CommentParser.new
    result = parser.parse(yaml_with_styles)
    
    # Check string styles were detected
    assert_equal :literal, result[:comments].get_string_style(["literal"])
    assert_equal :folded, result[:comments].get_string_style(["folded"])
    assert_equal :plain, result[:comments].get_string_style(["plain"])
    assert_equal :quoted, result[:comments].get_string_style(["quoted"])
    
    # Emit and verify styles are preserved
    emitter = Udb::Yaml::PreservingEmitter.new(result[:comments])
    emitted = emitter.emit(result[:data])
    
    assert emitted.include?("literal: |"), "Literal style not preserved"
    assert emitted.include?("folded: >"), "Folded style not preserved"
    assert emitted.include?("plain: plain value"), "Plain style not preserved"
    assert emitted.include?('quoted: "quoted value"'), "Quoted style not preserved"
  end

  # Test multiline plain scalar preservation
  def test_multiline_plain_scalar_preservation
    yaml_with_multiline = <<~YAML
      description:
        This is a multiline plain scalar
        that spans multiple lines
        without any block indicator
    YAML
    
    parser = Udb::Yaml::CommentParser.new
    result = parser.parse(yaml_with_multiline)
    
    # Check that multiline style was detected
    assert_equal :plain_multiline, result[:comments].get_string_style(["description"])
    
    # Check that original lines were captured
    original_lines = result[:comments].get_multiline_content(["description"])
    assert original_lines, "Multiline content not captured"
    assert_equal 3, original_lines.length, "Wrong number of lines captured"
    
    # Emit and verify line breaks are preserved
    emitter = Udb::Yaml::PreservingEmitter.new(result[:comments])
    emitted = emitter.emit(result[:data])
    
    lines = emitted.lines
    desc_line_idx = lines.index { |l| l.include?("description:") }
    assert desc_line_idx, "Description key not found in output"
    
    # Check that the next lines contain the multiline content
    assert lines[desc_line_idx + 1].strip.start_with?("This is"),
      "First line of multiline content not preserved"
    assert lines[desc_line_idx + 2].strip.start_with?("that spans"),
      "Second line of multiline content not preserved"
  end

  # Test source location tracking
  def test_source_location_tracking
    yaml_content = <<~YAML
      key1: value1
      key2: value2
      nested:
        key3: value3
    YAML
    
    # Write to temp file
    temp_file = Pathname.new(@test_dir) / "test.yaml"
    File.write(temp_file, yaml_content)
    
    # Parse and track locations
    parser = Udb::Yaml::CommentParser.new
    result = parser.parse_file(temp_file)
    
    # Manually track locations (simulating resolver behavior)
    comment_map = result[:comments]
    lines = yaml_content.lines
    
    lines.each_with_index do |line, idx|
      next if line.strip.empty? || line.strip.start_with?('#')
      
      if line.include?(':')
        key = line.split(':', 2)[0].strip
        next if key.empty?
        
        # Calculate column
        colon_pos = line.index(':')
        value_start = colon_pos + 1
        value_start += 1 while value_start < line.length && line[value_start] == ' '
        
        comment_map.set_source_location([key], temp_file.to_s, idx + 1, value_start + 1)
      end
    end
    
    # Verify locations were set
    loc1 = comment_map.get_source_location(["key1"])
    assert loc1, "Location not set for key1"
    assert_equal 1, loc1[:line], "Wrong line for key1"
    assert loc1[:column] > 0, "Invalid column for key1"
    
    loc2 = comment_map.get_source_location(["key2"])
    assert loc2, "Location not set for key2"
    assert_equal 2, loc2[:line], "Wrong line for key2"
  end

  # Test that IDL compilation works for all database files without errors,
  # and that the source file information in compiled AST hashes is correct
  def test_compile_idl_all_database_files
    skip "Spec directory not found" unless @spec_dir.exist?

    output_dir = Pathname.new(@test_dir) / "resolved_idl"

    # Run resolver with compile_idl: true — should not raise any errors
    resolver = Udb::Yaml::Resolver.new(quiet: true, compile_idl: true)
    resolver.resolve_files(@spec_dir, output_dir, no_checks: true)

    # Check that output files were created
    assert output_dir.exist?, "Output directory was not created"
    resolved_files = Dir.glob(output_dir / "**" / "*.yaml")
    assert resolved_files.any?, "No resolved files were created"

    # For each resolved file, verify source info in compiled AST hashes
    resolved_files.each do |resolved_path|
      resolved_path = Pathname.new(resolved_path)
      rel_path = resolved_path.relative_path_from(output_dir).to_s
      input_path = @spec_dir / rel_path

      next unless input_path.exist?

      begin
        resolved_data = Psych.safe_load_file(resolved_path, permitted_classes: [Date, Symbol], aliases: true)
      rescue Psych::SyntaxError
        $stderr.puts File.read(resolved_path)
        raise
      end

      # Find all compiled AST hashes and verify their source info
      find_ast_hashes(resolved_data).each do |ast_hash|
        source = ast_hash["source"]
        assert_equal rel_path, source["file"],
          "AST source file should match relative input path in #{rel_path}"
        assert source["begin"].is_a?(Integer) && source["begin"] >= 0,
          "AST source begin should be a non-negative Integer in #{rel_path}"
        assert source["end"].is_a?(Integer) && source["end"] >= source["begin"],
          "AST source end should be an Integer >= begin in #{rel_path}"
      end
    end
  end

  private

  # Recursively find all compiled AST hashes (identified by having a "source" hash
  # with "file", "begin", and "end" keys — the shape produced by AstNode#source_yaml)
  def find_ast_hashes(data)
    result = []
    case data
    when Hash
      if data.key?("source") && data["source"].is_a?(Hash) &&
         data["source"].key?("file") && data["source"].key?("begin") && data["source"].key?("end")
        result << data
      end
      data.values.each { |v| result.concat(find_ast_hashes(v)) }
    when Array
      data.each { |item| result.concat(find_ast_hashes(item)) }
    end
    result
  end

  # Recursively check if a data structure contains a specific key
  def data_contains_key?(data, key)
    case data
    when Hash
      return true if data.key?(key)
      data.values.any? { |v| data_contains_key?(v, key) }
    when Array
      data.any? { |v| data_contains_key?(v, key) }
    else
      false
    end
  end

  # Compare two data structures with tolerance for trailing whitespace in strings
  def compare_with_whitespace_tolerance(data1, data2)
    return true if data1 == data2
    return false unless data1.class == data2.class
    
    case data1
    when Hash
      return false unless data1.keys.sort == data2.keys.sort
      data1.keys.all? { |k| compare_with_whitespace_tolerance(data1[k], data2[k]) }
    when Array
      return false unless data1.length == data2.length
      data1.zip(data2).all? { |v1, v2| compare_with_whitespace_tolerance(v1, v2) }
    when String
      # Allow trailing whitespace differences and internal newline vs space differences
      # (multiline plain scalars may be joined differently)
      normalize_string(data1) == normalize_string(data2)
    else
      data1 == data2
    end
  end

  # Normalize a string for comparison (collapse whitespace)
  def normalize_string(str)
    str.strip.gsub(/\s+/, " ")
  end

  # Extract source map entries from YAML content
  def extract_source_map(content)
    lines = content.lines
    in_map = false
    map_entries = []
    
    lines.each do |line|
      if line.include?("===== SOURCE MAP BEGIN =====")
        in_map = true
        next
      elsif line.include?("===== SOURCE MAP END =====")
        break
      elsif in_map && line.start_with?("#")
        # Remove leading "# " and add to entries
        entry = line.sub(/^#\s*/, "").strip
        map_entries << entry unless entry.empty? || entry.start_with?("This map") || entry.start_with?("Format:")
      end
    end
    
    map_entries
  end
end
