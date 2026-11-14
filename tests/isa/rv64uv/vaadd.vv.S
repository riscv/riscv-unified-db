# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Verify signed vector averaging and vxrm rounding.

#include "riscv_test.h"
#include "test_macros.h"

RVTEST_RV64UV
RVTEST_CODE_BEGIN

  # Exercise every rounding mode at SEW=8.
  TEST_CASE(6, x2, 2, \
    vsetivli x0, 1, e8, m1; vmv.v.i v2, 3; vmv.v.i v3, 0; \
    csrwi vxrm, 0; vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )
  TEST_CASE(7, x2, 2, \
    vsetivli x0, 1, e8, m1; vmv.v.i v2, 3; vmv.v.i v3, 0; \
    csrwi vxrm, 1; vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )
  TEST_CASE(8, x2, 1, \
    vsetivli x0, 1, e8, m1; vmv.v.i v2, 3; vmv.v.i v3, 0; \
    csrwi vxrm, 2; vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )
  TEST_CASE(9, x2, 1, \
    vsetivli x0, 1, e8, m1; vmv.v.i v2, 3; vmv.v.i v3, 0; \
    csrwi vxrm, 3; vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )

  # Exercise every rounding mode at SEW=16.
  TEST_CASE(10, x2, 2, \
    vsetivli x0, 1, e16, m1; vmv.v.i v2, 3; vmv.v.i v3, 0; \
    csrwi vxrm, 0; vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )
  TEST_CASE(11, x2, 2, \
    vsetivli x0, 1, e16, m1; vmv.v.i v2, 3; vmv.v.i v3, 0; \
    csrwi vxrm, 1; vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )
  TEST_CASE(12, x2, 1, \
    vsetivli x0, 1, e16, m1; vmv.v.i v2, 3; vmv.v.i v3, 0; \
    csrwi vxrm, 2; vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )
  TEST_CASE(13, x2, 1, \
    vsetivli x0, 1, e16, m1; vmv.v.i v2, 3; vmv.v.i v3, 0; \
    csrwi vxrm, 3; vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )

  # 3 / 2 rounds to 2 with RNU and RNE, and to 1 with RDN and ROD.
  TEST_CASE(1, x2, 2, \
    vsetivli x0, 1, e32, m1; \
    la x5, three; \
    vle32.v v2, (x5); \
    vmv.v.i v3, 0; \
    csrwi vxrm, 0; \
    vaadd.vv v4, v2, v3; \
    la x5, result; \
    vse32.v v4, (x5); \
    lw x2, 0(x5); \
  )

  TEST_CASE(2, x2, 2, \
    vsetivli x0, 1, e32, m1; \
    la x5, three; \
    vle32.v v2, (x5); \
    vmv.v.i v3, 0; \
    csrwi vxrm, 1; \
    vaadd.vv v4, v2, v3; \
    la x5, result; \
    vse32.v v4, (x5); \
    lw x2, 0(x5); \
  )

  TEST_CASE(3, x2, 1, \
    vsetivli x0, 1, e32, m1; \
    la x5, three; \
    vle32.v v2, (x5); \
    vmv.v.i v3, 0; \
    csrwi vxrm, 2; \
    vaadd.vv v4, v2, v3; \
    la x5, result; \
    vse32.v v4, (x5); \
    lw x2, 0(x5); \
  )

  TEST_CASE(4, x2, 1, \
    vsetivli x0, 1, e32, m1; \
    la x5, three; \
    vle32.v v2, (x5); \
    vmv.v.i v3, 0; \
    csrwi vxrm, 3; \
    vaadd.vv v4, v2, v3; \
    la x5, result; \
    vse32.v v4, (x5); \
    lw x2, 0(x5); \
  )

  # This requires a SEW+1 signed sum: INT32_MIN averaged with itself is INT32_MIN.
  TEST_CASE(5, x2, -2147483648, \
    vsetivli x0, 1, e32, m1; \
    la x5, int32_min; \
    vle32.v v2, (x5); \
    vle32.v v3, (x5); \
    csrwi vxrm, 0; \
    vaadd.vv v4, v2, v3; \
    la x5, result; \
    vse32.v v4, (x5); \
    lw x2, 0(x5); \
  )

  TEST_CASE(19, x2, -128, \
    vsetivli x0, 1, e8, m1; li x5, -128; \
    vmv.v.x v2, x5; vmv.v.x v3, x5; csrwi vxrm, 0; \
    vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )

  TEST_CASE(20, x2, -32768, \
    vsetivli x0, 1, e16, m1; li x5, -32768; \
    vmv.v.x v2, x5; vmv.v.x v3, x5; csrwi vxrm, 0; \
    vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )

#if __riscv_xlen == 64
  # RV64 additionally covers the ELEN=64 case.
  TEST_CASE(14, x2, 2, \
    vsetivli x0, 1, e64, m1; vmv.v.i v2, 3; vmv.v.i v3, 0; \
    csrwi vxrm, 0; vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )
  TEST_CASE(15, x2, 2, \
    vsetivli x0, 1, e64, m1; vmv.v.i v2, 3; vmv.v.i v3, 0; \
    csrwi vxrm, 1; vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )
  TEST_CASE(16, x2, 1, \
    vsetivli x0, 1, e64, m1; vmv.v.i v2, 3; vmv.v.i v3, 0; \
    csrwi vxrm, 2; vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )
  TEST_CASE(17, x2, 1, \
    vsetivli x0, 1, e64, m1; vmv.v.i v2, 3; vmv.v.i v3, 0; \
    csrwi vxrm, 3; vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )

  TEST_CASE(18, x2, -9223372036854775808, \
    vsetivli x0, 1, e64, m1; li x5, 1; slli x5, x5, 63; \
    vmv.v.x v2, x5; vmv.v.x v3, x5; csrwi vxrm, 0; \
    vaadd.vv v4, v2, v3; vmv.x.s x2, v4; \
  )
#endif

  TEST_PASSFAIL

RVTEST_CODE_END

RVTEST_DATA_BEGIN

  .balign 4
three:
  .word 3
int32_min:
  .word 0x80000000
result:
  .word 0

RVTEST_DATA_END
