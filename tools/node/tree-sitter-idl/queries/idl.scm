; Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
; SPDX-License-Identifier: BSD-3-Clause-Clear

; Topiary formatting queries for IDL (ISA Description Language).
; Reference: https://topiary.tweag.io/book/query-language.html

; -----------------------------------------------------------------------
; Leaf nodes
; -----------------------------------------------------------------------

; Comments are line-based (#...) so MUST have a hardline after them.
; @allow_blank_line_before preserves blank lines before comment groups.
; The scope-based @prepend_space (rule 5) ensures trailing comments keep a space
; before # while standalone comments are not given an unwanted leading space.
(comment) @leaf @append_hardline @allow_blank_line_before
; Scope: measure the gap from after the comment to the start of the next sibling.
; If that gap is multi-line (i.e., the comment ends with a hardline before the next
; node), the comment is standalone and gets a prepended space for trailing flavour.
(
  (comment) @prepend_begin_scope @append_begin_measuring_scope
  .
  _ @prepend_end_measuring_scope @prepend_end_scope
  (#scope_id! "line_break_after_comment")
)
(
  (comment) @prepend_space
  (#multi_line_scope_only! "line_break_after_comment")
)
; description_content is free prose — preserve verbatim, no extra hardline
; (the content itself has leading/trailing newlines that handle line breaks)
(description_content) @leaf
(string_literal) @leaf
(int_literal) @leaf

; -----------------------------------------------------------------------
; Blank-line preservation
; -----------------------------------------------------------------------

; Allow blank lines before any node that commonly appears in sequence.
; Mirrors bash's approach: enumerate all statement-level constructs so
; that blank lines used to separate logical groups are preserved.
;
; Note: body_statement (not if_statement/return_statement/etc.) is the correct
; node — the individual statement types start at the same position as their
; body_statement wrapper, so blank_lines_before detection fires on the wrapper,
; not the inner type. Same pattern as (definition) vs (function_definition).
[
  (body_statement)
  (comment)
  (definition)
  (implication_for_loop)
  (implication_statement)
  (include_statement)
] @allow_blank_line_before

; Preserve blank lines before the isa_file tree (e.g. after a copyright
; comment block at the top of an .isa/.idl file, before %version:).
; Comments at the top of the file are siblings of isa_file under source_file,
; so the blank line is detected before isa_file, not before %version:.
(isa_file) @allow_blank_line_before

; -----------------------------------------------------------------------
; ISA file header
; -----------------------------------------------------------------------

"%version:" @append_space
(version_string) @append_hardline

; -----------------------------------------------------------------------
; Block delimiters
;
; description_block and body_block are named sub-nodes (grammar.js) so
; each { / } can be targeted precisely without multi-match ambiguity.
;
; Combined patterns (capturing { and } in the same match) are required —
; separate patterns cause Topiary 0.7.x to error with "Trying to close
; an unopened indentation block".
; -----------------------------------------------------------------------

; Space before { from @append_space on the preceding named token.
(body_function_definition (function_name) @append_space)
(builtin_function_definition (function_name) @append_space)
(enum_definition (type_identifier) @append_space)
(bitfield_definition (type_identifier) @append_space)
; @prepend_hardline on the member name: no-op when already at start of line
; (first member after '{', or after an inline comment's @append_hardline),
; fires otherwise to separate consecutive members without inline comments.
(enum_member (type_identifier) @prepend_hardline)
(enum_member (int_literal) @prepend_space)

; Bitfield members: same one-per-line pattern; @append_space after the name
; puts a space between the field name and its bit range (e.g. "N 63", "PBMT 62-61").
(bitfield_member (type_identifier) @prepend_hardline)
(bitfield_member (identifier) @prepend_hardline)
(bitfield_member (type_identifier) @append_space)
(bitfield_member (identifier) @append_space)
(struct_definition (type_identifier) @append_space)
; if_condition is a named rule wrapping each branch's "if (cond)" — one ( and )
; per branch, so the combined pattern is unambiguous (no multi-match).
; Duplicate pattern gives 2 indent levels so continuations sit deeper than the body.
(if_condition "(" @append_indent_start ")" @prepend_indent_end)
(if_condition "(" @append_indent_start ")" @prepend_indent_end)
(if_condition ")" @append_space)
; for_loop: same 2-level hanging indent for multi-line loop headers.
(for_loop "(" @append_indent_start ")" @prepend_indent_end @append_space)
(for_loop "(" @append_indent_start ")" @prepend_indent_end)

; body_function_definition: outer block
; @allow_blank_line_before on (definition) preserves source blank lines;
; (definition) is the correct node — function_definition starts at the same
; position so its blank_lines_before check fails; definition's does not.
(body_function_definition . (function_name) . "{" @append_spaced_softline @append_indent_start "}" @prepend_spaced_softline @prepend_indent_end @append_hardline .)
(builtin_function_definition . _ "{" @append_spaced_softline @append_indent_start "}" @prepend_spaced_softline @prepend_indent_end @append_hardline .)

; description_block: no softlines — description_content's own whitespace
; provides newlines, avoiding extra blank lines around the prose text
(description_block "{" @append_indent_start "}" @prepend_indent_end)

; statement_block: used by if_statement branches, for_loop, body_block, fetch_definition
; Each statement_block has exactly one { and } — no multi-match, correct indentation.
; @append_hardline on { ensures single-line source like "if (c) { return X; }" always
; expands to multi-line on pass 1.
; @prepend_hardline on } (not @prepend_spaced_softline) ensures idempotence: the softline
; variant causes non-idempotent output when multiple closing braces appear on the same
; line (e.g., "} } }").  "} else" still works because the existing @prepend_space on
; "else" (below) inserts the space between } and else.  Hardlines before each
; body_statement come from the rule below.
(statement_block "{" @append_hardline @append_indent_start "}" @prepend_hardline @prepend_indent_end)
; Hardline before every body_statement inside a statement_block.
; This replaces the @append_hardline that used to be on "}" — which also fired
; before "else", preventing K&R style.  The extra Hardline before the first
; body_statement (after "{"'s own @append_hardline) is deduplicated by topiary.
(body_statement) @prepend_hardline

; Simple single-block nodes (struct/enum/bitfield use { } directly)
; @append_hardline on } ensures subsequent standalone comments don't collapse
; onto the closing brace line (e.g. "}\n\n# comment" stays on its own line).
(enum_definition (type_identifier) . "{" @append_spaced_softline @append_indent_start "}" @prepend_spaced_softline @prepend_indent_end @append_hardline .)
(bitfield_definition (type_identifier) . "{" @append_spaced_softline @append_indent_start "}" @prepend_spaced_softline @prepend_indent_end @append_hardline .)
(struct_definition (type_identifier) . "{" @append_spaced_softline @append_indent_start "}" @prepend_spaced_softline @prepend_indent_end @append_hardline .)

; implication_for_loop still uses { } directly (rare construct)
(implication_for_loop "{" @append_spaced_softline @append_indent_start "}" @prepend_spaced_softline @prepend_indent_end)

"else" @prepend_space @append_space

; -----------------------------------------------------------------------
; Semicolons
; -----------------------------------------------------------------------

; Hanging indent for return expressions: { and } in same match to avoid Topiary
; ordering bugs with separate @prepend_indent_end patterns.
; @append_hardline on ; ensures each statement ends on its own line.
; Inline comments that were on the same line as ; (e.g. "return x; # note")
; will be placed on the next line — this is standard formatter behavior
; (bash does the same).
(return_statement (return_expression "return" @append_indent_start) ";" @prepend_antispace @prepend_indent_end @append_hardline)
(statement ";") @prepend_antispace @append_hardline
(implication_statement ";") @prepend_antispace @append_hardline
; global_definition and struct_definition also use @append_hardline.
(global_definition ";") @prepend_antispace @append_hardline
(struct_definition ";") @prepend_antispace @append_hardline
; For-loop header: @append_space on ; doesn't cross named-field boundaries;
; use @prepend_space on the condition and update fields instead.
(for_loop ";") @prepend_antispace
(for_loop condition: (expression) @prepend_space)
(for_loop update: _ @prepend_space)

; -----------------------------------------------------------------------
; Function section keywords
; -----------------------------------------------------------------------

"returns" @prepend_hardline @append_space
"arguments" @prepend_hardline @append_space
; Hanging indent for multi-line arguments: combined pattern so indent_start and
; indent_end are in the same Topiary match (avoiding the ordering bug).
(body_function_definition (arguments_clause "arguments" @append_indent_start) (description_block "description" @prepend_indent_end))
(builtin_function_definition (arguments_clause "arguments" @append_indent_start) (description_block "description" @prepend_indent_end))
"description" @prepend_hardline @append_space
"body" @prepend_hardline @append_space

; -----------------------------------------------------------------------
; Keywords
; -----------------------------------------------------------------------

"if" @append_space
; Space before trailing conditional 'if' in statements (e.g. "return true if N == 8;")
(statement "if" @prepend_space)
(return_statement "if" @prepend_space)
"for" @append_space
"return" @append_space
"enum" @append_space
"struct" @append_space
"fetch" @append_space
"include" @append_space
; include_statement has no ; so needs an explicit hardline after the path
(include_statement (string_literal) @append_hardline)
"builtin" @append_space
"generated" @append_space
"external" @append_space
"const" @append_space
"function" @append_space
"bitfield" @append_antispace
(bitfield_definition ")" @append_space)
"CSR" @append_antispace

; -----------------------------------------------------------------------
; Operators
; -----------------------------------------------------------------------

[
  "+" "*" "/" "%"
  "==" "!=" "<=" ">="
  "&" "|" "^"
  "<<" ">>" ">>>"
  "`+" "`-" "`*" "`<<"
  "="
  "->"
] @prepend_space @append_space

; Logical operators: use input softline so multi-line chains from source are preserved
"&&" @prepend_space @append_input_softline
"||" @prepend_space @append_input_softline

; < and > only in binary/template comparison contexts, NOT in Bits<N>
(binary_expression "<" @prepend_space @append_space)
(binary_expression ">" @prepend_space @append_space)
(template_binary_expression "<" @prepend_space @append_space)

; Minus: binary context gets spaces; unary context gets only @append_antispace
; (not @prepend_antispace — that would eat the space from the preceding token)
(binary_expression "-" @prepend_space @append_space)
(unary_expression "-") @append_antispace
"::" @prepend_antispace @append_antispace
; Ternary: preserve reflow-inserted breaks before ? and :, and indent continuations.
; The first child is the condition (@append_indent_start opens one level after it);
; the last child is the alternative (@append_indent_end closes it after).
; When the expression fits on one line the softlines collapse to spaces (no-op).
(ternary_expression . (_) @append_indent_start)
(ternary_expression "?" @prepend_input_softline @append_space)
(ternary_expression ":" @prepend_input_softline @append_space)
(ternary_expression (_) @append_indent_end .)
(subscript_expression ":" @prepend_space @append_space)

; -----------------------------------------------------------------------
; Type/identifier spacing in declarations
; -----------------------------------------------------------------------

; Space between type_name and identifier in all declaration contexts
(global_definition (type_name) @append_space)
(struct_definition (type_name) @append_space)
(declaration (type_name) @append_space)
(single_declaration (type_name) @append_space)
(single_declaration_with_initialization (type_name) @append_space)
(for_loop_iteration_variable_declaration (type_name) @append_space)

; -----------------------------------------------------------------------
; Unary operators
; -----------------------------------------------------------------------

["~" "!"] @append_antispace
["++" "--"] @prepend_antispace

; -----------------------------------------------------------------------
; Punctuation
; -----------------------------------------------------------------------

; @append_input_softline: space when source had no line break after comma
; (single-line calls stay single-line), line break when source did (multi-line
; argument lists preserve their structure).
"," @prepend_antispace @append_input_softline
; Hanging indent for multi-line function/method calls (2 levels so continuation
; arguments sit deeper than the statement, matching if_condition style).
(function_call "(" @append_indent_start ")" @prepend_indent_end)
(function_call "(" @append_indent_start ")" @prepend_indent_end)
; Hanging indent for multi-line array literals (e.g. global array initializers).
; @append_spaced_softline / @prepend_spaced_softline become newlines in expanded
; (multi-line) mode and are suppressed by @append_antispace in flat (single-line) mode.
(array_literal "[" @append_indent_start @append_spaced_softline "]" @prepend_indent_end @prepend_spaced_softline)
"(" @append_antispace
")" @prepend_antispace
"[" @append_antispace
"]" @prepend_antispace
"." @prepend_antispace @append_antispace
