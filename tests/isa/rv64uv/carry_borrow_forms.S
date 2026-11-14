# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

#include "riscv_test.h"
#include "test_macros.h"

RVTEST_RV64UV
RVTEST_CODE_BEGIN

  TEST_CASE(1, x2, 3, \
    vsetivli x0, 1, e8, m1; vmv.v.i v0, 0; vmv.v.i v2, 1; vmv.v.i v3, 2; \
    vadc.vvm v4, v2, v3, v0; vmv.x.s x2, v4; \
  )
  TEST_CASE(2, x2, 3, \
    vsetivli x0, 1, e8, m1; vmv.v.i v0, 0; vmv.v.i v2, 1; li x5, 2; \
    vadc.vxm v4, v2, x5, v0; vmv.x.s x2, v4; \
  )
  TEST_CASE(3, x2, 3, \
    vsetivli x0, 1, e8, m1; vmv.v.i v0, 0; vmv.v.i v2, 1; \
    vadc.vim v4, v2, 2, v0; vmv.x.s x2, v4; \
  )
  TEST_CASE(4, x2, 1, \
    vsetivli x0, 1, e8, m1; vmv.v.i v0, 0; vmv.v.i v2, 3; vmv.v.i v3, 2; \
    vsbc.vvm v4, v2, v3, v0; vmv.x.s x2, v4; \
  )
  TEST_CASE(5, x2, 1, \
    vsetivli x0, 1, e8, m1; vmv.v.i v0, 0; vmv.v.i v2, 3; li x5, 2; \
    vsbc.vxm v4, v2, x5, v0; vmv.x.s x2, v4; \
  )

  TEST_PASSFAIL
RVTEST_CODE_END
RVTEST_DATA_BEGIN
RVTEST_DATA_END
