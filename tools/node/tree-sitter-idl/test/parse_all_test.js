#!/usr/bin/env node
// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear

// Parse-all test: drives tree-sitter against all IDL in the repo without
// requiring hand-written corpus files. Failures print the first ERROR node
// location and source label, then exit 1.
//
// Usage: node test/parse_all_test.js
// Prerequisite: npm run generate && npm run build

'use strict';

const path = require('path');
const fs   = require('fs');
const yaml = require('js-yaml');
const Parser = require('tree-sitter');
const IDL    = require('../bindings/node');

const REPO_ROOT = path.resolve(__dirname, '..', '..', '..', '..');
const IDLC_ROOT = path.join(REPO_ROOT, 'tools', 'ruby-gems', 'idlc');

const parser = new Parser();
parser.setLanguage(IDL);

let pass = 0, fail = 0;
const failures = [];

function check(source, label) {
  const tree = parser.parse(source);
  if (tree.rootNode.hasError) {
    fail++;
    failures.push({ label, err: firstError(tree.rootNode) });
  } else {
    pass++;
  }
}

function firstError(n) {
  if (n.type === 'ERROR' || n.type === 'MISSING') {
    return `${n.startPosition.row + 1}:${n.startPosition.column + 1}: "${n.text.slice(0, 60).replace(/\n/g, '\\n')}"`;
  }
  for (const c of n.children) {
    const e = firstError(c);
    if (e) return e;
  }
  return null;
}

// Walk a directory recursively, calling cb(filePath) for each .yaml file.
function walkYamlFiles(dir, cb) {
  if (!fs.existsSync(dir)) return;
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) {
      walkYamlFiles(full, cb);
    } else if (name.endsWith('.yaml') || name.endsWith('.yml')) {
      cb(full);
    }
  }
}

// Walk a YAML doc object depth-first, calling cb(value, key, filePath) for
// each key that matches one of the given field names.
function walkDocFields(obj, fields, filePath, cb) {
  if (!obj || typeof obj !== 'object') return;
  if (Array.isArray(obj)) {
    obj.forEach(item => walkDocFields(item, fields, filePath, cb));
    return;
  }
  for (const [key, val] of Object.entries(obj)) {
    if (fields.includes(key) && val != null) {
      cb(String(val), key, filePath);
    } else {
      walkDocFields(val, fields, filePath, cb);
    }
  }
}

function skipBlank(src) {
  const s = src.trim();
  return s === '' || s === '#do nothing' || s === '# do nothing';
}

// ---------------------------------------------------------------------------
// Pass 1: idlc expression tests (literals.yaml + expressions.yaml)
// ---------------------------------------------------------------------------
for (const rel of [
  'test/idl/literals.yaml',
  'test/idl/expressions.yaml',
]) {
  const fullPath = path.join(IDLC_ROOT, rel);
  if (!fs.existsSync(fullPath)) { console.warn(`SKIP (not found): ${fullPath}`); continue; }
  let doc;
  try { doc = yaml.load(fs.readFileSync(fullPath, 'utf-8')); } catch (e) { console.warn(`SKIP (parse error): ${fullPath}`); continue; }
  const tests = (doc && doc.tests) || [];
  for (const t of tests) {
    if (t.e == null) continue;
    const src = String(t.e);
    if (!skipBlank(src)) check(src, `${rel}: ${t.d || src.slice(0, 40)}`);
  }
}

// ---------------------------------------------------------------------------
// Pass 2: idlc constraint tests
// ---------------------------------------------------------------------------
{
  const fullPath = path.join(IDLC_ROOT, 'test/idl/constraints.yaml');
  if (fs.existsSync(fullPath)) {
    let doc;
    try { doc = yaml.load(fs.readFileSync(fullPath, 'utf-8')); } catch (e) { doc = null; }
    const tests = (doc && doc.tests) || [];
    for (const t of tests) {
      if (t.c == null) continue;
      const src = String(t.c);
      if (!skipBlank(src)) check(src, `constraints.yaml: ${src.slice(0, 40)}`);
    }
  }
}

// ---------------------------------------------------------------------------
// Pass 3: idlc control flow tests
// ---------------------------------------------------------------------------
{
  const fullPath = path.join(IDLC_ROOT, 'test/data/control_flow_tests.yaml');
  if (fs.existsSync(fullPath)) {
    let doc;
    try { doc = yaml.load(fs.readFileSync(fullPath, 'utf-8')); } catch (e) { doc = null; }
    if (doc && typeof doc === 'object') {
      for (const [category, tests] of Object.entries(doc)) {
        if (!Array.isArray(tests)) continue;
        for (const t of tests) {
          if (t.idl == null) continue;
          const rawSrc = String(t.idl);
          if (skipBlank(rawSrc)) continue;
          // 'root' context: idlc wraps with %version:; 'body' context: bare statement list
          const src = (t.context === 'root')
            ? `%version: 1.0\n\n${rawSrc}`
            : rawSrc;
          check(src, `control_flow_tests.yaml [${category}/${t.name || '?'}]`);
        }
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Pass 4: standalone .idl files (ISA definitions)
// ---------------------------------------------------------------------------
for (const rel of ['spec/std/isa/isa', 'gen/resolved_spec/_/isa']) {
  const dir = path.join(REPO_ROOT, rel);
  if (!fs.existsSync(dir)) continue;
  for (const name of fs.readdirSync(dir).filter(f => f.endsWith('.idl'))) {
    const full = path.join(dir, name);
    const src = fs.readFileSync(full, 'utf-8');
    if (!skipBlank(src)) check(src, `${rel}/${name}`);
  }
}

// ---------------------------------------------------------------------------
// Pass 5: instruction operation() fields
// ---------------------------------------------------------------------------
walkYamlFiles(path.join(REPO_ROOT, 'spec/std/isa/inst'), fullPath => {
  let doc;
  try { doc = yaml.load(fs.readFileSync(fullPath, 'utf-8')); } catch { return; }
  if (!doc || typeof doc !== 'object') return;
  const val = doc['operation()'];
  if (val == null) return;
  const src = String(val);
  if (!skipBlank(src)) {
    check(src, `${path.relative(REPO_ROOT, fullPath)} [operation()]`);
  }
});

// ---------------------------------------------------------------------------
// Pass 6: CSR YAML IDL fields
// type(), reset_value(), sw_write(csr_value), sw_read() — all function_body roots
// ---------------------------------------------------------------------------
const CSR_IDL_FIELDS = ['type()', 'reset_value()', 'sw_write(csr_value)', 'sw_read()'];
walkYamlFiles(path.join(REPO_ROOT, 'spec/std/isa/csr'), fullPath => {
  let doc;
  try { doc = yaml.load(fs.readFileSync(fullPath, 'utf-8')); } catch { return; }
  if (!doc) return;
  const label = path.relative(REPO_ROOT, fullPath);
  walkDocFields(doc, CSR_IDL_FIELDS, fullPath, (src, key) => {
    if (!skipBlank(src)) check(src, `${label} [${key}]`);
  });
});

// ---------------------------------------------------------------------------
// Pass 7: extension YAML idl() fields
// ---------------------------------------------------------------------------
walkYamlFiles(path.join(REPO_ROOT, 'spec/std/isa/ext'), fullPath => {
  let doc;
  try { doc = yaml.load(fs.readFileSync(fullPath, 'utf-8')); } catch { return; }
  if (!doc) return;
  const label = path.relative(REPO_ROOT, fullPath);
  walkDocFields(doc, ['idl()'], fullPath, (src, key) => {
    if (!skipBlank(src)) check(src, `${label} [${key}]`);
  });
});

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------
const total = pass + fail;
console.log(`\n${pass}/${total} passed, ${fail} failed`);
if (failures.length > 0) {
  const shown = failures.slice(0, 20);
  for (const { label, err } of shown) {
    console.log(`  FAIL ${label}`);
    console.log(`       ${err}`);
  }
  if (failures.length > 20) {
    console.log(`  ...and ${failures.length - 20} more failures`);
  }
  process.exit(1);
}
