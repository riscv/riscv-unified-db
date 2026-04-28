# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
# See LICENSE for license details

#*****************************************************************************
# vnsra.wi.S
#-----------------------------------------------------------------------------
#
# Test vnsra.wi instruction.
#
# vnsra.wi

#include "riscv_test.h"
#include "test_macros.h"

RVTEST_RV64UV
RVTEST_CODE_BEGIN

# Write tests for vnsra.wi
# vlen = 128
# SEW=8, LMUL=1. x7 should contain VL == 10 (AVL, since its < VLMAX==128)
# VLMAX=vlen*LMUL/sew, so VLMAX=16.
# Use x5 to hold addresses

# Testcase 1: SEW = 8, LMUL = 1,Mask Bit = 0, VL = 10
    # IMM      = 4
    # VS2 (v22)       = [3aef 5ff4 34b8 0fd4 f600 a3d1 195b 62bf fbba 7ae7 2c63 c847 0692 dadf 7ca6 60db]
    # ELEMENTS          [--   --   --   --   --   --   ff   ff   ff   ff   ff   ff   ff   ff   ff   ff]
    # VD (v28) BEFORE = [19   5b   62   bf   fb   ba   7a   e7   2c   63   c8   47   06   92   da   df]
    # VD (v28) AFTER  = [19   5b   62   bf   fb   ba   95   2b   bb   ae   c6   84   69   ad   ca   0d]

  TEST_CASE(1, x2, 0xbbaec68469adca0d, \
# Set VL to VLMAX and load values into registers
    li x7, -1; \
    la x5, input1; \
    li x6, 4; \
    add x5, x5, x6; \
    vsetvli x0, x7, e16,m2; \
    vle16.v v22, (x5); \      # Load value into vs2
    li x6, 4; \
    add x5, x5, x6; \
    vsetvli x0, x7, e16,m1; \
    vle16.v v28, (x5); \       # Load value into vd
    li x6, 4; \
    add x5, x5, x6; \

    li  x7, 10; \ # VL = 10
    vsetvli x6, x7, e8,m1; \
    vnsra.wi v28, v22, 4; \
    la      x5, result; \
    vse8.v  v28, (x5); \
    lw      x2, (x5); \
    )
  TEST_PASSFAIL

RVTEST_CODE_END

# Input data section.
# This section is optional, and this data is NOT saved in the output.
.data
  .balign 4
input1:
	.word 0xe54c8c1e
	.word 0x7ca660db
	.word 0x0692dadf
	.word 0x2c63c847
	.word 0xfbba7ae7
	.word 0x195b62bf
	.word 0xf600a3d1
  .word 0x34b80fd4
	.word 0x3aef5ff4

# Output data section.
# This section is optional, but this data IS saved in the output.
RVTEST_DATA_BEGIN

result:
  .word -1

RVTEST_DATA_END
