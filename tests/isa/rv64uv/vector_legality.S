# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

#include "riscv_test.h"
#include "test_macros.h"

// Check vector-instruction legality conditions that assemblers intentionally
// refuse to encode. The raw encodings ensure the ISS semantic checks see them.

RVTEST_RV64UV
RVTEST_CODE_BEGIN

  vsetivli x0, 1, e8, m1
  vmv.v.i v0, -1
  li s0, 0
masked_vd_v0:
  .word 0x00310057  // vadd.vv v0, v2, v3, v0.t

  vsetivli x0, 1, e8, m8
  li s0, 1
invalid_lmul_vd:
  .word 0x0304007f  // vadd.vv v31, v8, v16

  li s0, 2
invalid_lmul_vs2:
  .word 0x03f8005f  // vadd.vv v8, v16, v31

  li s0, 3
invalid_lmul_vs1:
  .word 0x030f805f  // vadd.vv v8, v31, v16

  vsetivli x0, 1, e8, m1
  li s0, 4
unmasked_vadc_vd_v0:
  .word 0x40203057  // vadc.vim v0, v2, 0
  j fail

  TEST_PASSFAIL

  .align 2
  .global mtvec_handler
mtvec_handler:
  csrr t0, mcause
  li t1, CAUSE_ILLEGAL_INSTRUCTION
  bne t0, t1, fail

  csrr t0, mepc
  beq s0, x0, expected_masked_vd_v0
  li t1, 1
  beq s0, t1, expected_invalid_lmul_vd
  li t1, 2
  beq s0, t1, expected_invalid_lmul_vs2
  li t1, 3
  beq s0, t1, expected_invalid_lmul_vs1
  li t1, 4
  bne s0, t1, fail
  la t1, unmasked_vadc_vd_v0
  bne t0, t1, fail
  RVTEST_PASS

expected_masked_vd_v0:
  la t1, masked_vd_v0
  j check_expected_pc
expected_invalid_lmul_vd:
  la t1, invalid_lmul_vd
  j check_expected_pc
expected_invalid_lmul_vs2:
  la t1, invalid_lmul_vs2
  j check_expected_pc
expected_invalid_lmul_vs1:
  la t1, invalid_lmul_vs1

check_expected_pc:
  bne t0, t1, fail
  addi t0, t0, 4
  csrw mepc, t0
  mret

RVTEST_CODE_END

RVTEST_DATA_BEGIN
RVTEST_DATA_END
