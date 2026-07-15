# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Topiary language configuration for IDL (ISA Description Language).
#
# NOTE: bin/idl-format generates a runtime version of this config with
# absolute paths so Topiary can locate the grammar. Edit the template in
# bin/idl-format (the TOPIARY_CONFIG_FILE heredoc) to change language settings.
#
# The grammar must be compiled before using the formatter:
#   cd tools/node/tree-sitter-idl && make libtree-sitter-idl.so
{
  languages = {
    idl = {
      extensions | default = ["idl", "isa"],
      indent | default = "  ",
      grammar.source | default = {
        path = "<absolute-path-to>/tools/node/tree-sitter-idl/libtree-sitter-idl",
      },
    },
  },
}
