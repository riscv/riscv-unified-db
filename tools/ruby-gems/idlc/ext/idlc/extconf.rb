# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

# Compiles libtree-sitter-idl.so from bundled C sources at gem install time.
# Used only by the source (non-platform) gem variant. Platform gems bundle
# a pre-compiled .so directly and do not include this file.

require "fileutils"

src_dir = __dir__
lib_dir = File.expand_path("../../lib/idlc", src_dir)
so_dest = File.join(lib_dir, "libtree-sitter-idl.so")

FileUtils.mkdir_p(lib_dir)

cmd = "gcc -shared -fPIC -std=c11 -I#{src_dir} -o #{so_dest} " \
      "#{src_dir}/parser.c #{src_dir}/scanner.c"

raise "Failed to compile libtree-sitter-idl.so — ensure gcc is installed" unless system(cmd)

# Write no-op Makefile expected by the gem install infrastructure.
File.write(File.join(src_dir, "Makefile"), "all:\n\ninstall:\n\nclean:\n")
