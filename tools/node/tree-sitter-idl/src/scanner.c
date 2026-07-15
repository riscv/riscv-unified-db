// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear

// External scanner for IDL integer literals.
//
// Tree-sitter's regex tokenizer cannot distinguish a plain decimal like `32`
// from the width prefix of a Verilog literal like `32'b1010` because both
// start identically. This scanner handles every integer literal format
// atomically, consuming the entire token in one pass.
//
// Formats handled:
//   Plain decimal:        42, 42s
//   C-style binary:       0b1010, 0b1010s
//   C-style octal:        077, 077s
//   C-style hex:          0xDEAD_BEEF, 0xfs
//   Special zero:         0, 0s  (NOT followed by ')
//   Verilog with width:   32'b1010, 8'sd42, MXLEN'h3f
//   Verilog bare:         'b1010, 'h3f, '0, 'd63
//   Verilog x/z bits:     8'bxxxx_xxxx
//   All signed variants use 's' suffix (C-style) or 's' before base (Verilog).

#include "tree_sitter/parser.h"
#include <ctype.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

enum TokenType {
  INT_LITERAL,
};

void *tree_sitter_idl_external_scanner_create(void) { return NULL; }
void  tree_sitter_idl_external_scanner_destroy(void *p) { (void)p; }
void  tree_sitter_idl_external_scanner_reset(void *p) { (void)p; }
unsigned tree_sitter_idl_external_scanner_serialize(void *p, char *buf) { (void)p; (void)buf; return 0; }
void  tree_sitter_idl_external_scanner_deserialize(void *p, const char *buf, unsigned n) { (void)p; (void)buf; (void)n; }

// Advance the lexer one character.
static inline void adv(TSLexer *lexer) {
  lexer->advance(lexer, false);
}

// Consume one or more hex digit chars (0-9, a-f, A-F, x, X, z, Z, _).
static bool consume_verilog_digits(TSLexer *lexer) {
  if (!isxdigit(lexer->lookahead) &&
      lexer->lookahead != 'x' && lexer->lookahead != 'X' &&
      lexer->lookahead != 'z' && lexer->lookahead != 'Z') {
    return false;
  }
  while (isxdigit(lexer->lookahead) ||
         lexer->lookahead == 'x' || lexer->lookahead == 'X' ||
         lexer->lookahead == 'z' || lexer->lookahead == 'Z' ||
         lexer->lookahead == '_') {
    adv(lexer);
  }
  return true;
}

// Consume one or more binary digits (0, 1, x, X, z, Z, _).
static bool consume_binary_digits(TSLexer *lexer) {
  if (lexer->lookahead != '0' && lexer->lookahead != '1' &&
      lexer->lookahead != 'x' && lexer->lookahead != 'X' &&
      lexer->lookahead != 'z' && lexer->lookahead != 'Z') {
    return false;
  }
  while (lexer->lookahead == '0' || lexer->lookahead == '1' ||
         lexer->lookahead == 'x' || lexer->lookahead == 'X' ||
         lexer->lookahead == 'z' || lexer->lookahead == 'Z' ||
         lexer->lookahead == '_') {
    adv(lexer);
  }
  return true;
}

// Consume one or more octal digits (0-7, x, X, _).
static bool consume_octal_digits(TSLexer *lexer) {
  if (lexer->lookahead < '0' || lexer->lookahead > '7') return false;
  while ((lexer->lookahead >= '0' && lexer->lookahead <= '7') ||
         lexer->lookahead == '_') {
    adv(lexer);
  }
  return true;
}

// Consume one or more decimal digits (0-9, _).
static bool consume_decimal_digits(TSLexer *lexer) {
  if (!isdigit(lexer->lookahead)) return false;
  while (isdigit(lexer->lookahead) || lexer->lookahead == '_') adv(lexer);
  return true;
}

// After consuming the width and the '\'' separator, consume the base + digits.
// Returns true on success.
static bool consume_verilog_base_and_digits(TSLexer *lexer) {
  // Optional signed flag before base
  if (lexer->lookahead == 's') {
    adv(lexer);  // consume 's'
    if (isdigit(lexer->lookahead)) {
      // 's' alone as signed marker followed immediately by decimal digits
      consume_decimal_digits(lexer);
      return true;
    }
    // 'sb, 'so, 'sh, 'sd — signed base follows
    if (lexer->lookahead != 'b' && lexer->lookahead != 'B' &&
        lexer->lookahead != 'o' && lexer->lookahead != 'O' &&
        lexer->lookahead != 'h' && lexer->lookahead != 'H' &&
        lexer->lookahead != 'd' && lexer->lookahead != 'D') {
      return true;  // bare 's' suffix — already consumed
    }
  }
  // Base character (or implicit decimal if digit follows directly)
  switch (lexer->lookahead) {
    case 'b': case 'B':
      adv(lexer);
      return consume_binary_digits(lexer);
    case 'o': case 'O':
      adv(lexer);
      return consume_octal_digits(lexer);
    case 'd': case 'D':
      adv(lexer);
      // 'd' with no following digit is valid (e.g. '0 style handled above)
      consume_decimal_digits(lexer);
      return true;
    case 'h': case 'H':
      adv(lexer);
      return consume_verilog_digits(lexer);
    default:
      if (isdigit(lexer->lookahead)) {
        // Implicit decimal: no 'd' letter, digits follow directly (e.g. '63 or 63'63)
        consume_decimal_digits(lexer);
        return true;
      }
      return false;
  }
}

bool tree_sitter_idl_external_scanner_scan(
    void *payload, TSLexer *lexer, const bool *valid_symbols) {
  (void)payload;

  if (!valid_symbols[INT_LITERAL]) return false;

  // Skip any leading whitespace (extras are handled by tree-sitter but the
  // scanner may be called with whitespace as lookahead during error recovery).
  while (lexer->lookahead == ' ' || lexer->lookahead == '\t' ||
         lexer->lookahead == '\n' || lexer->lookahead == '\r') {
    lexer->advance(lexer, true);  // skip as whitespace
  }

  int32_t c = lexer->lookahead;

  // -----------------------------------------------------------------------
  // Case 1: starts with a digit
  // -----------------------------------------------------------------------
  if (isdigit(c)) {
    if (c == '0') {
      adv(lexer);
      // Peek: could be 0b, 0x, 0<octal>, 0'<verilog>, or bare 0
      if (lexer->lookahead == 'b' || lexer->lookahead == 'B') {
        // C-style binary
        adv(lexer);
        if (lexer->lookahead != '0' && lexer->lookahead != '1') return false;
        while (lexer->lookahead == '0' || lexer->lookahead == '1' || lexer->lookahead == '_') adv(lexer);
        if (lexer->lookahead == 's') adv(lexer);
        lexer->result_symbol = INT_LITERAL;
        return true;
      }
      if (lexer->lookahead == 'x' || lexer->lookahead == 'X') {
        // C-style hex
        adv(lexer);
        if (!isxdigit(lexer->lookahead)) return false;
        while (isxdigit(lexer->lookahead) || lexer->lookahead == '_') adv(lexer);
        if (lexer->lookahead == 's') adv(lexer);
        lexer->result_symbol = INT_LITERAL;
        return true;
      }
      if (lexer->lookahead >= '0' && lexer->lookahead <= '7') {
        // C-style octal
        while ((lexer->lookahead >= '0' && lexer->lookahead <= '7') || lexer->lookahead == '_') adv(lexer);
        if (lexer->lookahead == 's') adv(lexer);
        lexer->result_symbol = INT_LITERAL;
        return true;
      }
      if (lexer->lookahead == '\'') {
        // 0 followed by ' — this would be Verilog "0'" which is unusual; treat 0 as decimal
        // (the ' is NOT part of this token when the number before it is 0 and it's a zero-width)
        // Actually treetop says: '0' !"'" 's'? — so bare 0 must NOT be followed by '
        // If we see 0' we should NOT emit 0 as an int_literal here; let the grammar handle it
        // as a Verilog bare literal starting with '
        // Don't consume the ' — just emit the 0
        // But we already consumed '0' and lookahead is "'" — emit just the 0
        if (lexer->lookahead == '\'') {
          // bare 0, confirmed NOT followed by ' for verilog (treetop rule says !"'")
          // We consumed '0', next is '\'' — do NOT include '\'' in this token
          // emit the 0 alone and let tree-sitter re-lex from '\''
          lexer->result_symbol = INT_LITERAL;
          return true;
        }
      }
      // bare 0
      if (lexer->lookahead == 's') adv(lexer);
      lexer->result_symbol = INT_LITERAL;
      return true;
    }

    // Non-zero decimal: consume all digits
    while (isdigit(lexer->lookahead) || lexer->lookahead == '_') adv(lexer);

    if (lexer->lookahead == '\'') {
      // Verilog with explicit decimal width
      adv(lexer);  // consume '\''
      if (!consume_verilog_base_and_digits(lexer)) return false;
      lexer->result_symbol = INT_LITERAL;
      return true;
    }
    // C-style plain decimal (optional 's' suffix)
    if (lexer->lookahead == 's') adv(lexer);
    lexer->result_symbol = INT_LITERAL;
    return true;
  }

  // -----------------------------------------------------------------------
  // Case 2: starts with 'M' — could be MXLEN'<base> Verilog literal
  // -----------------------------------------------------------------------
  if (c == 'M') {
    // Speculatively advance through "MXLEN" and check for '\''
    // If the sequence breaks, return false and let tree-sitter use the
    // standard lexer (which will produce an identifier token for MXLEN).
    adv(lexer);  // consumed 'M'
    if (lexer->lookahead != 'X') return false;
    adv(lexer);  // consumed 'X'
    if (lexer->lookahead != 'L') return false;
    adv(lexer);  // consumed 'L'
    if (lexer->lookahead != 'E') return false;
    adv(lexer);  // consumed 'E'
    if (lexer->lookahead != 'N') return false;
    adv(lexer);  // consumed 'N'
    if (lexer->lookahead != '\'') return false;
    adv(lexer);  // consumed '\''
    if (!consume_verilog_base_and_digits(lexer)) return false;
    lexer->result_symbol = INT_LITERAL;
    return true;
  }

  // -----------------------------------------------------------------------
  // Case 3: starts with '\'' — bare Verilog (no width prefix)
  // -----------------------------------------------------------------------
  if (c == '\'') {
    adv(lexer);  // consume '\''
    if (!consume_verilog_base_and_digits(lexer)) return false;
    lexer->result_symbol = INT_LITERAL;
    return true;
  }

  return false;
}
