# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Verify that an out-of-bounds vstart traps before executing a vector instruction.

#include "riscv_test.h"
#include "test_macros.h"

RVTEST_RV64UV
RVTEST_CODE_BEGIN

  # With VLEN=128, SEW=8, and LMUL=1, VLMAX is 16.
  vsetivli x0, 16, e8, m1
  csrwi vstart, 16

vstart_out_of_bounds:
  vadd.vv v1, v2, v3
  j fail

  TEST_PASSFAIL

  .align 2
  .global mtvec_handler
mtvec_handler:
  csrr t0, mcause
  li t1, CAUSE_ILLEGAL_INSTRUCTION
  bne t0, t1, fail

  csrr t0, mepc
  la t1, vstart_out_of_bounds
  bne t0, t1, fail

  csrr t0, vstart
  li t1, 16
  bne t0, t1, fail

  RVTEST_PASS

RVTEST_CODE_END

RVTEST_DATA_BEGIN
RVTEST_DATA_END
