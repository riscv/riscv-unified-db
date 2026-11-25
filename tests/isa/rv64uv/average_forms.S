# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

#include "riscv_test.h"
#include "test_macros.h"

// Exercise each corrected vector averaging form at every vxrm setting.

#define AVG_VV_CASE(num, inst, rhs, rm, expected) \
  TEST_CASE(num, x2, expected, \
    vsetivli x0, 1, e8, m1; vmv.v.i v2, 3; vmv.v.i v3, rhs; \
    csrwi vxrm, rm; inst v4, v2, v3; vmv.x.s x2, v4; \
  )

#define AVG_VX_CASE(num, inst, rhs, rm, expected) \
  TEST_CASE(num, x2, expected, \
    vsetivli x0, 1, e8, m1; vmv.v.i v2, 3; li x5, rhs; \
    csrwi vxrm, rm; inst v4, v2, x5; vmv.x.s x2, v4; \
  )

RVTEST_RV64UV
RVTEST_CODE_BEGIN

  // 3 + 0 rounds to 2, 2, 1, 1 for RNU, RNE, RDN, ROD.
  AVG_VX_CASE(1, vaadd.vx, 0, 0, 2)
  AVG_VX_CASE(2, vaadd.vx, 0, 1, 2)
  AVG_VX_CASE(3, vaadd.vx, 0, 2, 1)
  AVG_VX_CASE(4, vaadd.vx, 0, 3, 1)
  AVG_VV_CASE(5, vaaddu.vv, 0, 0, 2)
  AVG_VV_CASE(6, vaaddu.vv, 0, 1, 2)
  AVG_VV_CASE(7, vaaddu.vv, 0, 2, 1)
  AVG_VV_CASE(8, vaaddu.vv, 0, 3, 1)
  AVG_VX_CASE(9, vaaddu.vx, 0, 0, 2)
  AVG_VX_CASE(10, vaaddu.vx, 0, 1, 2)
  AVG_VX_CASE(11, vaaddu.vx, 0, 2, 1)
  AVG_VX_CASE(12, vaaddu.vx, 0, 3, 1)

  // 3 - 2 rounds to 1, 1, 0, 1 for RNU, RNE, RDN, ROD.
  AVG_VV_CASE(13, vasub.vv, 2, 0, 1)
  AVG_VV_CASE(14, vasub.vv, 2, 1, 1)
  AVG_VV_CASE(15, vasub.vv, 2, 2, 0)
  AVG_VV_CASE(16, vasub.vv, 2, 3, 1)
  AVG_VX_CASE(17, vasub.vx, 2, 0, 1)
  AVG_VX_CASE(18, vasub.vx, 2, 1, 1)
  AVG_VX_CASE(19, vasub.vx, 2, 2, 0)
  AVG_VX_CASE(20, vasub.vx, 2, 3, 1)
  AVG_VV_CASE(21, vasubu.vv, 2, 0, 1)
  AVG_VV_CASE(22, vasubu.vv, 2, 1, 1)
  AVG_VV_CASE(23, vasubu.vv, 2, 2, 0)
  AVG_VV_CASE(24, vasubu.vv, 2, 3, 1)
  AVG_VX_CASE(25, vasubu.vx, 2, 0, 1)
  AVG_VX_CASE(26, vasubu.vx, 2, 1, 1)
  AVG_VX_CASE(27, vasubu.vx, 2, 2, 0)
  AVG_VX_CASE(28, vasubu.vx, 2, 3, 1)

  TEST_PASSFAIL
RVTEST_CODE_END
RVTEST_DATA_BEGIN
RVTEST_DATA_END
