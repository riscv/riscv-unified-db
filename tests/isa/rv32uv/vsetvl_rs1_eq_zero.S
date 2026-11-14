# Copyright (c) Openchip and Software Technologies, S.L.
# SPDX-License-Identifier: BSD-3-Clause-Clear

#include "riscv_test.h"
#undef RVTEST_RV64UV
#define RVTEST_RV64UV RVTEST_RV32UV

#include "../rv64uv/vsetvl_rs1_eq_zero.S"
