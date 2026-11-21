# Copyright (c) Openchip and Software Technologies, S.L.
# SPDX-License-Identifier: BSD-3-Clause-Clear

#*****************************************************************************
# vsetvl_rs1_eq_zero.S
#-----------------------------------------------------------------------------
#
# Test vsetvl when rs1 is x0, and when the new vtype value is not supported.
#
# The AVL encoding of the vector specification applies to both vsetvli and
# vsetvl ("AVL encoding" in vector-common.adoc):
#   rd != x0, rs1 == x0: AVL is ~0, vl is set to VLMAX
#   rd == x0, rs1 == x0: AVL is the current vl, vl is kept
# vsetvli_rs1_eq_zero.S tests the same cases for vsetvli.
# An unsupported vtype value sets vtype.vill and sets vl to 0.
#
# The case rd == x0, rs1 == x0 with a new SEW/LMUL ratio is reserved, so it
# is not tested here.

#include "riscv_test.h"
#include "test_macros.h"

RVTEST_RV64UV
RVTEST_CODE_BEGIN

# tests for VLEN=128 bits

  # rd != x0, rs1 == x0: SEW=8, LMUL=8, VLMAX = 8*128/8 = 128
  TEST_CASE(2, x5, 0x80, \
    li x4, 0x03; \
    vsetvl x5, x0, x4; \
  )

  # rd != x0, rs1 == x0: SEW=16, LMUL=1, VLMAX = 128/16 = 8
  TEST_CASE(3, x5, 0x8, \
    li x4, 0x08; \
    vsetvl x5, x0, x4; \
  )

  # rd == x0, rs1 == x0 keeps vl: set vl=5 with SEW=8, LMUL=1, then
  # change to SEW=16, LMUL=2, which has the same SEW/LMUL ratio
  TEST_CASE(4, x5, 0x5, \
    li x2, 0x5; \
    li x4, 0x00; \
    vsetvl x6, x2, x4; \
    li x4, 0x09; \
    vsetvl x0, x0, x4; \
    csrr x5, vl; \
  )

  # an unsupported vtype value (vsew = 100, reserved) sets vl to 0
  TEST_CASE(5, x5, 0x0, \
    li x2, 0x5; \
    li x4, 0x00; \
    vsetvl x6, x2, x4; \
    li x4, 0x20; \
    vsetvl x5, x2, x4; \
  )

  # and sets vtype.vill
  TEST_CASE(6, x5, 0x1, \
    li x2, 0x5; \
    li x4, 0x20; \
    vsetvl x6, x2, x4; \
    csrr x5, vtype; \
    srli x5, x5, __riscv_xlen - 1; \
  )

  TEST_PASSFAIL

RVTEST_CODE_END

  .data
RVTEST_DATA_BEGIN

RVTEST_DATA_END
