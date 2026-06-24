# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

# Compiles libtree-sitter-idl.so from bundled C sources at gem install time.
# Used only by the source (non-platform) gem variant. Platform gems bundle
# a pre-compiled .so directly and do not include this file.

require "fileutils"
require "rbconfig"

src_dir = __dir__
lib_dir = File.expand_path("../../lib/idlc", src_dir)
# Always emit ".so": the gemspec and Ruby loaders key off this name on every
# platform. On macOS the artifact is a Mach-O dynamic library named .so, which
# dlopen (and ruby_tree_sitter) load regardless of extension.
so_dest = File.join(lib_dir, "libtree-sitter-idl.so")

FileUtils.mkdir_p(lib_dir)

# Use the compiler Ruby was built with, and the platform-appropriate flag for
# producing a loadable shared object (-dynamiclib on macOS, -shared elsewhere).
cc = RbConfig::CONFIG["CC"]
cc = "cc" if cc.nil? || cc.empty?
shared_flag = RbConfig::CONFIG["host_os"] =~ /darwin/ ? "-dynamiclib" : "-shared"

cmd = "#{cc} #{shared_flag} -fPIC -std=c11 -I#{src_dir} -o #{so_dest} " \
      "#{src_dir}/parser.c #{src_dir}/scanner.c"

raise "Failed to compile libtree-sitter-idl.so — ensure a C compiler is installed" unless system(cmd)

# Write no-op Makefile expected by the gem install infrastructure.
File.write(File.join(src_dir, "Makefile"), "all:\n\ninstall:\n\nclean:\n")
