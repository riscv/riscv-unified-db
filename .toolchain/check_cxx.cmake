# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
#
# Shared C++ compiler requirements check.
# Used by:
#   - backends/cpp_hart_gen/CMakeLists.txt (build-time check)
#   - bin/.toolchain.sh (wrapper pre-flight check via cmake)
#
# To change C++ requirements, update this file only.

cmake_policy(SET CMP0067 NEW) # Force check_cxx_source_compiles to respect CMAKE_CXX_STANDARD
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED True)

include(CheckCXXSourceCompiles)
check_cxx_source_compiles(
  "#include <version>
   #if !defined(__cpp_concepts) || (__cpp_concepts < 201907)
   #error \"No concepts\"
   #endif
   int main(void) { return 0; }"
  HAVE_CONCEPTS
)
if(NOT HAVE_CONCEPTS)
  message(FATAL_ERROR "Compiler (${CMAKE_CXX_COMPILER}) does not support C++23 with concepts")
endif()

check_cxx_source_compiles(
  "#include <version>
   #if !defined(__cpp_lib_constexpr_charconv) || (__cpp_lib_constexpr_charconv < 202207L)
   #error \"No constexpr from_chars\"
   #endif
   int main(void) { return 0; }"
  HAVE_CONSTEXPR_CHARCONV
)
if(NOT HAVE_CONSTEXPR_CHARCONV)
  message(FATAL_ERROR "Compiler (${CMAKE_CXX_COMPILER}) does not support constexpr from_chars (__cpp_lib_constexpr_charconv >= 202207L, requires GCC 14+ or Clang 17+)")
endif()
