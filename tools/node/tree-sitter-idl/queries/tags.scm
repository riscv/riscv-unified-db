; Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
; SPDX-License-Identifier: BSD-3-Clause-Clear

; Tree-sitter tags for IDL — used by ctags, symbol search, etc.

(function_definition
  name: (function_name) @name) @definition.function

(enum_definition
  name: (type_identifier) @name) @definition.type

(struct_definition
  name: (type_identifier) @name) @definition.type

(bitfield_definition
  name: (type_identifier) @name) @definition.type

(function_call
  name: (function_name) @name) @reference.call
