# See LICENSE for license details

#*****************************************************************************
# vsetvli.S
#-----------------------------------------------------------------------------
#
# Test vsetvli instruction when source register rs1 is equal to zero
#
# vsetvli xd, x0, vtypei
# vtypei[7:0] = VLMUL[2:0], VSEW[5:3], VTA[6], VMA[7]
# AVL is taken to be ~0 (the maximum unsigned integer) and VL is set to VLMAX

#include "riscv_test.h"
#include "test_macros.h"

RVTEST_RV64UV
RVTEST_CODE_BEGIN

# tests for VLEN=128bits, AVL = ~0 (rs1 = x0)
  # vtypei = 0x03 -> VMA_VTA_VSEW_VLMUL == 0_0_000_011 -> SEW=8, LMUL=8
  # VLMAX=LMUL*VLEN/SEW = 8*128/8 = 128
  TEST_CASE(1, x5, 0x80, \
    vsetvli x5, x0, 0x03; \
  )

  # vtypei = 0x0b -> VMA_VTA_VSEW_VLMUL == 0_0_001_011 -> SEW=16, LMUL=8
  # VLMAX=LMUL*VLEN/SEW = 8*128/16 = 64
  TEST_CASE(2, x5, 0x40, \
    vsetvli x5, x0, 0x0b; \
  )
  # vtypei = 0x23 -> VMA_VTA_VSEW_VLMUL == 0_0_100_011 -> SEW=RESERVED, LMUL=8
  # Change to
  # vtypei = 0x13 -> VMA_VTA_VSEW_VLMUL == 0_0_010_011 -> SEW=32, LMUL=8
  # VLMAX=LMUL*VLEN/SEW = 8*128/32 = 32
  TEST_CASE(3, x5, 0x20, \
    vsetvli x5, x0, 0x13; \
  )

  # vtypei = 0xeb-> VMA_VTA_VSEW_VLMUL == 1_1_101_011 -> SEW=RESERVED, LMUL=8
  # Change to
  # vtypei = 0xdb -> VMA_VTA_VSEW_VLMUL == 1_1_011_011 -> SEW=64, LMUL=8
  # VLMAX=LMUL*VLEN/SEW = 8*128/64 = 16
  TEST_CASE(4, x5, 0x10, \
    vsetvli x5, x0, 0xdb; \
  )

  # vtypei = 0x07 -> VMA_VTA_VSEW_VLMUL == 0_0_000_111 -> SEW=8, LMUL=1/2
  # VLMAX=LMUL*VLEN/SEW = 128/2/8 = 8
  TEST_CASE(5, x5, 0x8, \
    vsetvli x5, x0, 0x07; \
  )

  # vtypei = 0x06 -> VMA_VTA_VSEW_VLMUL == 0_0_000_110 -> SEW=8, LMUL=1/4
  # VLMAX=LMUL*VLEN/SEW = 128/4/8 = 4
  TEST_CASE(6, x5, 0x4, \
    vsetvli x5, x0, 0x06; \
  )

  # rd = x0, rs1 = x0 keeps vl: set vl=5 with SEW=8, LMUL=1/2, then
  # change to SEW=16, LMUL=1. Both have VLMAX = 8.
  TEST_CASE(7, x5, 0x5, \
    li x2, 0x5; \
    vsetvli x6, x2, 0x07; \
    vsetvli x0, x0, 0x08; \
    csrr x5, vl; \
  )

  # and writes the new vtype without setting vtype.vill
  TEST_CASE(8, x5, 0x08, \
    li x2, 0x5; \
    vsetvli x6, x2, 0x07; \
    vsetvli x0, x0, 0x08; \
    csrr x5, vtype; \
  )

  TEST_PASSFAIL

RVTEST_CODE_END

  .data
RVTEST_DATA_BEGIN

RVTEST_DATA_END
