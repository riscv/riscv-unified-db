#!/usr/bin/env node
// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear
//
// Generates all IDL syntax highlighting artifacts from the tree-sitter grammar.
//
// Usage:
//   node tools/node/idl-gen/index.js               # generate all three
//   node tools/node/idl-gen/index.js --only textmate
//   node tools/node/idl-gen/index.js --only hljs
//   node tools/node/idl-gen/index.js --only rouge
//   node tools/node/idl-gen/index.js --only prism
//   bin/chore gen idl-highlight

'use strict';

const { loadGrammarData } = require('./lib/parse-grammar');
const textmate = require('./lib/textmate');
const hljs     = require('./lib/hljs');
const rouge    = require('./lib/rouge');
const prism    = require('./lib/prism');

const args  = process.argv.slice(2);
const only  = args.indexOf('--only') !== -1 ? args[args.indexOf('--only') + 1] : null;

const data = loadGrammarData();

if (!only || only === 'textmate') textmate.generate(data);
if (!only || only === 'hljs')     hljs.generate(data);
if (!only || only === 'rouge')    rouge.generate(data);
if (!only || only === 'prism')    prism.generate(data);
