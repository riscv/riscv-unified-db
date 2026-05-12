# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require_relative "lib/schema_doc_gen/version"

Gem::Specification.new do |s|
  s.name        = "schema_doc_gen"
  s.version     = SchemaDocGen::VERSION
  s.summary     = "JSON Schema documentation generator for UDB"
  s.description = <<~DESC
    Generates Markdown documentation from JSON Schema files for the
    RISC-V Unified Database documentation site.
  DESC
  s.authors     = ["Derek Hower"]
  s.email       = ["dhower@qti.qualcomm.com"]
  s.homepage    = "https://github.com/riscv/riscv-unified-db"
  s.files       = Dir["lib/**/*.rb", "bin/*"]
  s.license     = "BSD-3-Clause-Clear"
  s.metadata    = {
    "homepage_uri" => "https://github.com/riscv/riscv-unified-db",
    "bug_tracker_uri" => "https://github.com/riscv/riscv-unified-db/issues"
  }
  s.required_ruby_version = "~> 3.2"

  s.require_paths = ["lib"]
  s.bindir = "bin"
  s.executables << "schema-doc-gen"
  s.executables << "schema-docs-all"

  s.add_dependency "tty-option"
  s.add_dependency "tty-exit"

  s.add_development_dependency "rake"
end
