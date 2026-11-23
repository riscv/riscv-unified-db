# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
# See LICENSE for license details

#*****************************************************************************
# vsetivli.S
#-----------------------------------------------------------------------------
#
# Test vsetivli instruction.
#
# vsetivli xd, uimm, vtypei
# vtypei[7:0] = VLMUL[2:0], VSEW[5:3], VTA[6], VMA[7]
# uimm[4:0] = AVL

#include "riscv_test.h"
#include "test_macros.h"

RVTEST_RV64UV
RVTEST_CODE_BEGIN

# tests for VLEN=128bits, AVL < VLMAX

  # SEW=8, LMUL=8, VLMAX=128
  TEST_CASE(2, x2, 0x2, \
    vsetivli x2, 0x2, 3; \
  )

  # SEW=8, LMUL=2, VLMAX=32
  TEST_CASE(3, x2, 0x2, \
    vsetivli x2, 0x2, 0x01; \
  )

  # SEW=8, LMUL=1/2, VLMAX=8
  TEST_CASE(4, x2, 0x2, \
    vsetivli x2, 0x2, 0xc7; \
  )

# tests for VLEN=128bits, AVL >= 2*VLMAX

  # SEW=8, LMUL=1/2, VLMAX=8
  TEST_CASE(5, x2, 0x8, \
    vsetivli x2, 31, 0x07; \
  )

  # SEW=8, LMUL=1/4, VLMAX=4
  TEST_CASE(6, x2, 0x4, \
    vsetivli x2, 31, 0x06; \
  )

# an unsupported vtype value (vsew = 100, reserved) sets vl to 0

  TEST_CASE(7, x2, 0x0, \
    vsetivli x2, 0x2, 0x20; \
  )

  TEST_PASSFAIL

RVTEST_CODE_END

  .data
RVTEST_DATA_BEGIN

RVTEST_DATA_END
