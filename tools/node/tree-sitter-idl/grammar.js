// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear

// Tree-sitter grammar for the ISA Description Language (IDL).
// Canonical reference: tools/ruby-gems/idlc/lib/idlc/idl.treetop

const PREC = {
  TERNARY:  1,
  OR:       2,
  AND:      3,
  BITOR:    4,
  XOR:      5,
  BITAND:   6,
  EQ:       7,
  REL:      8,
  SHIFT:    9,
  ADD:     10,
  MUL:     11,
  UNARY:   12,
  POSTFIX: 13,
  CALL:    14,
};

module.exports = grammar({
  name: 'idl',

  // Whitespace and comments are skipped between any two tokens.
  extras: $ => [/[ \t\n\r]+/, $.comment],

  // 'identifier' is used for keyword extraction via the word mechanism.
  word: $ => $.identifier,

  // Integer literals are handled by the external scanner (src/scanner.c).
  externals: $ => [$.int_literal],

  conflicts: $ => [
    // 'identifier ?' could be function_name (part of a call) or identifier + ternary '?'
    [$.function_name, $.primary_expression],
    // 'CSR[n].TypeName ?' could be csr_field_access or csr_function_call with '?'-named method
    [$.function_name, $.csr_field_access],
  ],

  rules: {

    // -----------------------------------------------------------------------
    // Source file roots
    // -----------------------------------------------------------------------

    // The grammar supports all parse roots used by idlc. tree-sitter always
    // starts at source_file; the choice order below disambiguates based on
    // leading tokens. expression_root is last because a bare expression can't
    // match any of the prior alternatives (they all require ';' or keywords).
    // optional() at the top level handles the empty-body case (operation(): "").
    // Note: the idlc :for_loop root is handled by statement_list (one body_statement).
    source_file: $ => optional(choice(
      $.isa_file,        // '%version:' — unambiguous
      $.constraint_body, // sequence of '->' implication statements
      $.statement_list,  // one-or-more ';'-terminated statements (incl. for loops)
      $.expression_root, // single expression, no ';'
    )),

    isa_file: $ => seq(
      '%version:', field('version', $.version_string),
      repeat($.definition),
    ),

    // repeat1 — tree-sitter does not allow named rules to match the empty
    // string (unless they are the start rule). The empty-body case is handled
    // at the source_file level via optional().
    statement_list: $ => repeat1($.body_statement),

    body_statement: $ => choice(
      $.return_statement,
      $.if_statement,
      $.for_loop,
      $.statement,
    ),

    constraint_body: $ => repeat1(choice(
      $.implication_statement,
      $.implication_for_loop,
    )),

    expression_root: $ => $.expression,

    // -----------------------------------------------------------------------
    // Lexical terminals
    // -----------------------------------------------------------------------

    comment: $ => token(seq('#', /.*/)),

    string_literal: $ => token(seq('"', /[^"]*/, '"')),

    true_literal:  $ => 'true',
    false_literal: $ => 'false',

    // Base identifier — used for word/keyword extraction; no '?' suffix.
    identifier: $ => /[A-Za-z][A-Za-z0-9_]*/,

    // Type names start with an uppercase letter.
    // token(prec(1, ...)) gives this terminal higher priority than 'identifier'
    // when both patterns match (e.g., for 'ExtensionName' or 'U32').
    type_identifier: $ => token(prec(1, /[A-Z][A-Za-z0-9_]*/)),

    // CSR register names: lowercase with optional dots (e.g. mip, fcsr.fflags).
    csr_name: $ => /[a-z][a-z0-9_.]*/,

    // CSR field names: mixed case (e.g. VSEW, MXL).
    // Lowercase CSR field names (e.g. fflags); uppercase ones are type_identifier.
    csr_field_name: $ => /[a-z][a-z0-9_]*/,

    // Dollar-prefixed variables: $foo, $signed.
    // The name may contain '?' (e.g. $array_includes?), matching the treetop rule.
    dollar_variable: $ => /\$[a-zA-Z_][a-zA-Z0-9_?]*/,

    version_string: $ => /[0-9]+\.[0-9]+/,

    // Content inside description { ... } blocks — anything that isn't '}'.
    description_content: $ => token(prec(1, /[^}]*/)),

    // -----------------------------------------------------------------------
    // Grammar-level rules for identifiers with special roles
    // -----------------------------------------------------------------------

    // Function names may optionally end with '?' (e.g. misaligned?).
    // Using a grammar rule rather than a terminal avoids a token conflict with
    // plain identifier and lets the word mechanism apply to the identifier base.
    // Both lowercase and uppercase function names are accepted.
    function_name: $ => seq(
      choice($.identifier, $.type_identifier),
      optional('?'),
    ),

    // -----------------------------------------------------------------------
    // Type system
    // -----------------------------------------------------------------------

    type_name: $ => choice(
      seq('Bits', '<', field('size', $.template_expression), '>'),
      alias($.type_identifier, $.type_name),
    ),

    array_size: $ => seq('[', $.expression, ']'),

    // -----------------------------------------------------------------------
    // Expressions
    // -----------------------------------------------------------------------

    expression: $ => choice(
      $.ternary_expression,
      $.binary_expression,
      $.unary_expression,
    ),

    ternary_expression: $ => prec.right(PREC.TERNARY,
      seq($.expression, '?', $.expression, ':', $.expression),
    ),

    binary_expression: $ => choice(
      prec.left(PREC.OR,     seq($.expression, '||',  $.expression)),
      prec.left(PREC.AND,    seq($.expression, '&&',  $.expression)),
      prec.left(PREC.BITOR,  seq($.expression, '|',   $.expression)),
      prec.left(PREC.XOR,    seq($.expression, '^',   $.expression)),
      prec.left(PREC.BITAND, seq($.expression, '&',   $.expression)),
      prec.left(PREC.EQ,     seq($.expression, choice('==', '!='), $.expression)),
      prec.left(PREC.REL,    seq($.expression, choice('<', '>', '<=', '>='), $.expression)),
      prec.left(PREC.SHIFT,  seq($.expression, choice('<<', '>>', '>>>'), $.expression)),
      prec.left(PREC.ADD,    seq($.expression, choice('+', '-'), $.expression)),
      prec.left(PREC.MUL,    seq($.expression, choice('*', '/', '%'), $.expression)),
      // Widening operators (backtick-prefix) — semantics: result type grows to hold full value
      prec.left(PREC.SHIFT,  seq($.expression, '`<<',  $.expression)),
      prec.left(PREC.ADD,    seq($.expression, choice('`+', '`-'), $.expression)),
      prec.left(PREC.MUL,    seq($.expression, '`*',   $.expression)),
    ),

    unary_expression: $ => choice(
      prec(PREC.UNARY, seq(choice('~', '-', '!'), $.expression)),
      $.postfix_expression,
    ),

    postfix_expression: $ => choice(
      $.post_increment_expression,
      $.post_decrement_expression,
      $.subscript_expression,
      $.primary_expression,
    ),

    post_increment_expression: $ => prec(PREC.POSTFIX, seq(choice($.identifier, $.type_identifier), '++')),
    post_decrement_expression: $ => prec(PREC.POSTFIX, seq(choice($.identifier, $.type_identifier), '--')),

    // Array indexing and Verilog bit-range slicing: arr[idx] or arr[msb:lsb].
    // The subscript operator is chainable: arr[a][b:c].
    subscript_expression: $ => prec.left(PREC.POSTFIX, seq(
      $.primary_expression,
      repeat1(seq(
        '[',
        field('index', $.expression),
        optional(seq(':', field('lsb', $.expression))),
        ']',
      )),
    )),

    primary_expression: $ => choice(
      $.paren_expression,
      $.replication_expression,
      $.concatenation_expression,
      $.array_literal,
      $.field_access_expression,
      $.csr_function_call,
      $.csr_field_access,
      $.csr_register_access,
      $.dollar_function_call,
      $.function_call,
      $.enum_ref,
      $.true_literal,
      $.false_literal,
      $.int_literal,
      $.string_literal,
      $.dollar_variable,
      $.type_identifier, // uppercase identifiers used as values (e.g. 'N' in 'N == 8')
      $.identifier,
    ),

    paren_expression: $ => seq('(', $.expression, ')'),

    // Verilog concatenation: {a, b, c}
    concatenation_expression: $ => seq(
      '{', $.expression, repeat(seq(',', $.expression)), '}',
    ),

    // Verilog replication: {N{val}} — given higher precedence than concatenation.
    replication_expression: $ => prec(1, seq(
      '{', field('count', $.expression), '{', field('value', $.expression), '}', '}',
    )),

    // Array literal: [a, b, c]
    array_literal: $ => seq('[', $.expression, repeat(seq(',', $.expression)), ']'),

    field_access_expression: $ => prec(PREC.POSTFIX, seq(
      choice($.paren_expression, $.function_call, $.identifier),
      '.', field('field', $.identifier),
    )),

    enum_ref: $ => seq(
      field('enum_type', $.type_identifier),
      '::',
      field('member', $.type_identifier),
    ),

    function_call: $ => prec(PREC.CALL, seq(
      field('name', $.function_name),
      '(', optional($.argument_list), ')',
    )),

    // $fn(args) — dollar function call.
    // dollar_variable (/\$name/) is consumed as a single token by the lexer, so we
    // can't parse '$' + identifier separately. Instead, use dollar_variable as the
    // name prefix and check whether '(' follows to decide call vs variable.
    dollar_function_call: $ => seq(
      field('name', $.dollar_variable),
      '(', optional($.argument_list), ')',
    ),

    argument_list: $ => seq($.expression, repeat(seq(',', $.expression))),

    // -----------------------------------------------------------------------
    // CSR access
    // -----------------------------------------------------------------------

    // CSR[name]
    csr_register_access: $ => seq('CSR', '[', field('name', $.csr_name), ']'),

    // CSR[name].field — read expression
    // Field names can be lowercase (identifier), mixed case (identifier), or uppercase (type_identifier, e.g. VSEW).
    // The 'identifier' word terminal wins for lowercase/mixed, type_identifier for ALL-CAPS.
    csr_field_access: $ => seq(
      $.csr_register_access, '.', field('field', choice($.type_identifier, $.identifier)),
    ),

    // CSR[name].sw_write(val) or CSR[name].fn(args) — method call
    csr_function_call: $ => seq(
      $.csr_register_access,
      '.', field('method', $.function_name),
      '(', optional($.argument_list), ')',
    ),

    // -----------------------------------------------------------------------
    // Template-safe expressions
    // Used inside Bits<N> to prevent '>' from closing the template prematurely.
    // Only '<' and '<=' are allowed as relational operators (not '>' or '>=').
    // -----------------------------------------------------------------------

    template_expression: $ => choice(
      $.template_ternary_expression,
      $.template_binary_expression,
      $.unary_expression,
    ),

    template_ternary_expression: $ => prec.right(PREC.TERNARY,
      seq($.template_expression, '?', $.expression, ':', $.expression),
    ),

    template_binary_expression: $ => choice(
      prec.left(PREC.OR,     seq($.template_expression, '||',  $.template_expression)),
      prec.left(PREC.AND,    seq($.template_expression, '&&',  $.template_expression)),
      prec.left(PREC.BITOR,  seq($.template_expression, '|',   $.template_expression)),
      prec.left(PREC.XOR,    seq($.template_expression, '^',   $.template_expression)),
      prec.left(PREC.BITAND, seq($.template_expression, '&',   $.template_expression)),
      prec.left(PREC.EQ,     seq($.template_expression, choice('==', '!='), $.template_expression)),
      // '>' and '>=' excluded here — both start with '>' which closes the template
      prec.left(PREC.REL,    seq($.template_expression, choice('<', '<='), $.template_expression)),
      prec.left(PREC.SHIFT,  seq($.template_expression, choice('<<', '>>', '>>>'), $.template_expression)),
      prec.left(PREC.ADD,    seq($.template_expression, choice('+', '-'), $.template_expression)),
      prec.left(PREC.MUL,    seq($.template_expression, choice('*', '/', '%'), $.template_expression)),
      prec.left(PREC.SHIFT,  seq($.template_expression, '`<<',  $.template_expression)),
      prec.left(PREC.ADD,    seq($.template_expression, choice('`+', '`-'), $.template_expression)),
      prec.left(PREC.MUL,    seq($.template_expression, '`*',   $.template_expression)),
    ),

    // -----------------------------------------------------------------------
    // Implication expressions (constraint bodies only)
    // -----------------------------------------------------------------------

    implication_expression: $ => choice(
      // Parenthesized form: (ant -> cons) — tried first
      seq('(', optional($.expression), '->', $.expression, ')'),
      seq(optional($.expression), '->', $.expression),
    ),

    implication_statement: $ => seq($.implication_expression, ';'),

    implication_for_loop: $ => seq(
      'for', '(',
      $.for_loop_iteration_variable_declaration, ';',
      field('condition', $.expression), ';',
      field('update', choice($.assignment, $.post_increment_expression, $.post_decrement_expression)),
      ')', '{',
      repeat1(choice($.implication_statement, $.implication_for_loop)),
      '}',
    ),

    // -----------------------------------------------------------------------
    // Statements
    // -----------------------------------------------------------------------

    // A statement is either a plain action ending with ';' or a conditional
    // action with a trailing 'if cond' modifier (treetop line 531-534).
    statement: $ => choice(
      seq($.action, 'if', $.expression, ';'),
      seq($.action, ';'),
    ),

    // The set of things that can appear as statement actions.
    // More specific forms first to resolve ambiguity.
    action: $ => choice(
      $.single_declaration_with_initialization,
      $.csr_field_assignment,
      $.array_assignment,
      $.field_assignment,
      $.dollar_variable_assignment,
      $.variable_assignment,
      $.declaration,
      $.function_call,
      $.csr_function_call,
      $.dollar_function_call,
    ),

    // TypeName id [size] = expr;
    single_declaration_with_initialization: $ => seq(
      field('type', $.type_name),
      field('name', choice($.identifier, $.type_identifier)),
      optional(field('size', $.array_size)),
      '=',
      field('value', $.expression),
    ),

    // CSR[name].field = expr
    csr_field_assignment: $ => seq(
      $.csr_field_access, '=', field('value', $.expression),
    ),

    // arr[idx] = expr  or  arr[msb:lsb] = expr
    array_assignment: $ => seq(
      field('target', $.primary_expression),
      repeat1(seq(
        '[',
        field('index', $.expression),
        optional(seq(':', field('lsb', $.expression))),
        ']',
      )),
      '=', field('value', $.expression),
    ),

    // id.field = expr
    field_assignment: $ => seq(
      field('object', choice($.identifier, $.type_identifier)), '.', field('field', $.identifier),
      '=', field('value', $.expression),
    ),

    // $var = expr
    dollar_variable_assignment: $ => seq(
      $.dollar_variable, '=', field('value', $.expression),
    ),

    // id = expr
    variable_assignment: $ => seq(
      field('name', choice($.identifier, $.type_identifier)), '=', field('value', $.expression),
    ),

    // TypeName id [size];  or  TypeName id, id2, ...;
    declaration: $ => choice(
      seq(
        field('type', $.type_name),
        choice($.identifier, $.type_identifier),
        repeat1(seq(',', choice($.identifier, $.type_identifier))),
      ),
      $.single_declaration,
    ),

    single_declaration: $ => seq(
      field('type', $.type_name),
      field('name', choice($.identifier, $.type_identifier)),
      optional(field('size', $.array_size)),
    ),

    // Same syntax as single_declaration_with_initialization but treated
    // differently by idlc semantics (loop variable may be const in unrolling).
    for_loop_iteration_variable_declaration: $ => seq(
      field('type', $.type_name),
      field('name', choice($.identifier, $.type_identifier)),
      optional(field('size', $.array_size)),
      '=', field('value', $.expression),
    ),

    // Don't-care placeholder for return statements
    dontcare_return:  $ => '-',

    // -----------------------------------------------------------------------
    // Return statements
    // -----------------------------------------------------------------------

    return_statement: $ => choice(
      seq($.return_expression, 'if', $.expression, ';'),
      seq($.return_expression, ';'),
    ),

    return_expression: $ => seq(
      'return',
      optional(seq(
        choice($.expression, $.dontcare_return),
        repeat(seq(',', choice($.expression, $.dontcare_return))),
      )),
    ),

    // -----------------------------------------------------------------------
    // Control flow
    // -----------------------------------------------------------------------

    if_statement: $ => seq(
      $.if_condition, $.statement_block,
      repeat(seq('else', $.if_condition, $.statement_block)),
      optional(seq('else', $.statement_block)),
    ),

    // Named rule for each if/else-if condition so the ( ) pair can be targeted
    // precisely for hanging-indent of multi-line conditions.
    if_condition: $ => seq('if', '(', field('condition', $.expression), ')'),

    for_loop: $ => seq(
      'for', '(',
      $.for_loop_iteration_variable_declaration, ';',
      field('condition', $.expression), ';',
      field('update', choice($.assignment, $.post_increment_expression, $.post_decrement_expression)),
      ')', $.statement_block,
    ),

    // Assignment used in for-loop update steps (subset of 'action').
    assignment: $ => choice(
      $.variable_assignment,
      $.array_assignment,
      $.field_assignment,
      $.csr_field_assignment,
      $.dollar_variable_assignment,
    ),

    // -----------------------------------------------------------------------
    // ISA file definitions
    // -----------------------------------------------------------------------

    definition: $ => choice(
      $.include_statement,
      $.global_definition,
      $.enum_definition,
      $.bitfield_definition,
      $.struct_definition,
      $.function_definition,
      $.fetch_definition,
    ),

    include_statement: $ => seq('include', $.string_literal),

    global_definition: $ => choice(
      seq(optional('const'), $.type_name, choice($.identifier, $.type_identifier), optional($.array_size), '=', $.expression, ';'),
      seq($.type_name, choice($.identifier, $.type_identifier), optional($.array_size), ';'),
    ),

    enum_definition: $ => choice(
      seq('generated', 'enum', $.type_identifier, ';'),
      seq('enum', $.type_identifier, '{',
        repeat1($.enum_member),
        '}',
      ),
    ),

    enum_member: $ => seq($.type_identifier, optional($.int_literal)),

    bitfield_definition: $ => seq(
      'bitfield', '(', $.int_literal, ')', $.type_identifier, '{',
      repeat1($.bitfield_member),
      '}',
    ),

    bitfield_member: $ => seq(
      choice($.identifier, $.type_identifier),
      $.int_literal,
      optional(seq('-', $.int_literal)),
    ),

    struct_definition: $ => seq(
      'struct', $.type_identifier, '{',
      repeat1(seq($.type_name, choice($.identifier, $.type_identifier), ';')),
      '}',
    ),

    fetch_definition: $ => seq('fetch', $.statement_block),

    function_definition: $ => choice(
      $.body_function_definition,
      $.builtin_function_definition,
    ),

    body_function_definition: $ => seq(
      optional('external'), 'function', $.function_name, '{',
      optional(seq(
        'returns',
        $.type_name, repeat(seq(',', $.type_name)),
      )),
      optional($.arguments_clause),
      $.description_block,
      $.body_block,
      '}',
    ),

    builtin_function_definition: $ => seq(
      choice('builtin', 'generated'), 'function', $.function_name, '{',
      optional(seq('returns', $.type_name)),
      optional($.arguments_clause),
      $.description_block,
      '}',
    ),

    arguments_clause: $ => seq(
      'arguments',
      $.single_declaration, repeat(seq(',', $.single_declaration)),
    ),

    description_block: $ => seq('description', '{', $.description_content, '}'),

    body_block: $ => seq('body', $.statement_block),

    statement_block: $ => seq('{', repeat($.body_statement), '}'),

  },
});
