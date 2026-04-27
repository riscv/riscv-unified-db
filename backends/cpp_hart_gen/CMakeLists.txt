cmake_minimum_required(VERSION 3.20)

include(ExternalProject)

project(udb LANGUAGES CXX C)

# Add Asan build type
SET(CMAKE_CXX_FLAGS_ASAN
    "-g -Og -fsanitize=address"
    CACHE STRING "Flags used by the C++ compiler during address sanitizer builds."
    FORCE )
SET(CMAKE_C_FLAGS_ASAN
    "-g -Og -fsanitize=address"
    CACHE STRING "Flags used by the C compiler during address address sanitizer builds."
    FORCE )
SET(CMAKE_EXE_LINKER_FLAGS_ASAN
    ""
    CACHE STRING "Flags used for linking binaries during address address sanitizer builds."
    FORCE )
SET(CMAKE_SHARED_LINKER_FLAGS_ASAN
    ""
    CACHE STRING "Flags used by the shared libraries linker during address sanitizer builds."
    FORCE )
MARK_AS_ADVANCED(
    CMAKE_CXX_FLAGS_ASAN
    CMAKE_C_FLAGS_ASAN
    CMAKE_EXE_LINKER_FLAGS_ASAN
    CMAKE_SHARED_LINKER_FLAGS_ASAN )
IF(NOT CMAKE_BUILD_TYPE)
  SET(CMAKE_BUILD_TYPE RelWithDebInfo
      CACHE STRING "Choose the type of build : None Debug Release RelWithDebInfo MinSizeRel Asan."
      FORCE)
ENDIF(NOT CMAKE_BUILD_TYPE)
message("* Current build type is : ${CMAKE_BUILD_TYPE}")

set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_CXX_FLAGS ${CMAKE_CXX_FLAGS} -no-pie)

if(NOT DEFINED UDB_ROOT OR UDB_ROOT STREQUAL "")
  get_filename_component(UDB_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
endif()

set(UDB_CHECK_CXX_CMAKE "${UDB_ROOT}/.toolchain/check_cxx.cmake")
if(NOT EXISTS "${UDB_CHECK_CXX_CMAKE}")
  message(FATAL_ERROR
    "Unable to locate '${UDB_CHECK_CXX_CMAKE}'. "
    "Set UDB_ROOT to the repository root or configure from the expected source tree.")
endif()
# Check C++ compiler requirements (C++23 + concepts) — single source of truth in check_cxx.cmake
include(${UDB_ROOT}/.toolchain/check_cxx.cmake)

include(FetchContent)

FetchContent_Declare(fmt
  GIT_REPOSITORY https://github.com/fmtlib/fmt.git
  GIT_TAG 10.2.1
)
FetchContent_MakeAvailable(fmt)

FetchContent_Declare(
  yaml-cpp
  GIT_REPOSITORY https://github.com/jbeder/yaml-cpp.git
  GIT_TAG yaml-cpp-0.7.0
)
FetchContent_MakeAvailable(yaml-cpp)

FetchContent_Declare(
    cli11_proj
    QUIET
    GIT_REPOSITORY https://github.com/CLIUtils/CLI11.git
    GIT_TAG f4d0731
)

FetchContent_MakeAvailable(cli11_proj)

FetchContent_Declare(
  Catch2
  GIT_REPOSITORY https://github.com/catchorg/Catch2.git
  GIT_TAG        v3.7.1
)

FetchContent_MakeAvailable(Catch2)

FetchContent_Declare(
  nlohmann_json_schema_validator
  GIT_REPOSITORY https://github.com/pboettch/json-schema-validator.git
  GIT_TAG        2.3.0
)

FetchContent_MakeAvailable(nlohmann_json_schema_validator)

FetchContent_Declare(
  compile_time_regular_expressions
  GIT_REPOSITORY https://github.com/hanickadot/compile-time-regular-expressions.git
  GIT_TAG        v3.9.0
)
FetchContent_MakeAvailable(compile_time_regular_expressions)

# -----------------------------------------------------------------------
# libelf — built from elfutils source; no system package required
# -----------------------------------------------------------------------
ExternalProject_Add(elfutils_libelf
  URL      https://sourceware.org/elfutils/ftp/0.192/elfutils-0.192.tar.bz2
  URL_HASH SHA256=616099beae24aba11f9b63d86ca6cc8d566d968b802391334c91df54eab416b4
  CONFIGURE_COMMAND ""
  BUILD_COMMAND   ${UDB_ROOT}/.toolchain/.build-elfutils.sh
                    <SOURCE_DIR> <BINARY_DIR> <INSTALL_DIR>
  INSTALL_COMMAND ""
)

ExternalProject_Get_Property(elfutils_libelf INSTALL_DIR BINARY_DIR)

# cmake validates INTERFACE_INCLUDE_DIRECTORIES at configure time, but ExternalProject
# only creates them at build time — pre-create so the check passes.
file(MAKE_DIRECTORY "${INSTALL_DIR}/include")

# libeu is elfutils' internal utility library; not installed, but libelf.a needs it at link time.
add_library(libeu_static STATIC IMPORTED)
set_target_properties(libeu_static PROPERTIES
  IMPORTED_LOCATION "${BINARY_DIR}/lib/libeu.a"
)
add_dependencies(libeu_static elfutils_libelf)

add_library(libelf_static STATIC IMPORTED)
set_target_properties(libelf_static PROPERTIES
  IMPORTED_LOCATION             "${INSTALL_DIR}/lib/libelf.a"
  INTERFACE_INCLUDE_DIRECTORIES "${INSTALL_DIR}/include"
  INTERFACE_LINK_LIBRARIES      "libeu_static;-lz"
)
add_dependencies(libelf_static elfutils_libelf)


add_library(hart
  ${CMAKE_SOURCE_DIR}/src/db_data.cxx
  ${CMAKE_SOURCE_DIR}/src/enum.cxx
  ${CMAKE_SOURCE_DIR}/src/memory.cpp
  ${GENERATED_SRCS}
#  ../gen/iss/oryon/src/types.cxx
#  ../gen/iss/oryon/src/csr_types.cxx
#  ../gen/iss/oryon/src/hart_funcs.cxx
#  ../gen/iss/oryon/src/decode.cxx
)
target_include_directories(hart PUBLIC ${CMAKE_SOURCE_DIR}/include)
if(IGNOREUNDEFINED STREQUAL "YES")
target_compile_definitions(hart PUBLIC IGNOREUNDEFINED)
endif()
target_link_libraries(hart PUBLIC yaml-cpp::yaml-cpp nlohmann_json_schema_validator fmt::fmt ctre::ctre -lgmp -lgmpxx)

# add_library(hart_c ${CMAKE_SOURCE_DIR}/src/libhart_c.cpp)
# target_include_directories(hart_c PUBLIC ${CMAKE_SOURCE_DIR}/include)
# target_link_libraries(hart_c hart)

add_library(hart_renode SHARED ${CMAKE_SOURCE_DIR}/src/libhart_renode.cpp)
target_compile_options(hart_renode PRIVATE -fvisibility=hidden)
target_include_directories(hart_renode PUBLIC
  ${CMAKE_SOURCE_DIR}/include
)
target_link_libraries(hart_renode PUBLIC hart)

add_executable(iss
  ${CMAKE_SOURCE_DIR}/src/iss.cpp
  ${CMAKE_SOURCE_DIR}/src/elf_reader.cpp
  ${CMAKE_SOURCE_DIR}/src/GDBServer.cpp
  ${CMAKE_SOURCE_DIR}/src/NotificationHandler.cpp
)
if(IGNOREUNDEFINED STREQUAL "YES")
target_compile_definitions(iss PUBLIC IGNOREUNDEFINED)
endif()
target_link_libraries(iss PRIVATE hart libelf_static CLI11::CLI11)
add_dependencies(iss elfutils_libelf)


## TESTS

add_executable(test_bits_directed
  ${CMAKE_SOURCE_DIR}/test/test_bits_directed.cpp
)
target_include_directories(test_bits_directed PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(test_bits_directed PRIVATE hart Catch2::Catch2WithMain)
target_compile_options(test_bits_directed PRIVATE -fprofile-arcs -ftest-coverage)
target_link_options(test_bits_directed PRIVATE -fprofile-arcs -ftest-coverage)

set(RANDOM_TESTS "")
foreach (i RANGE 5)
  add_executable(test_bits_random_${i}
    ${CMAKE_SOURCE_DIR}/test/test_bits_random_${i}.cpp
  )
  target_include_directories(test_bits_random_${i} PUBLIC ${CMAKE_SOURCE_DIR}/include)
  target_link_libraries(test_bits_random_${i} PRIVATE hart Catch2::Catch2WithMain)
  target_compile_options(test_bits_random_${i} PRIVATE -fprofile-arcs -ftest-coverage)
  target_link_options(test_bits_random_${i} PRIVATE -fprofile-arcs -ftest-coverage)

  list(APPEND RANDOM_TESTS test_bits_random_${i})
endforeach()
add_custom_target(test_bits_random)
add_dependencies(test_bits_random ${RANDOM_TESTS})

add_executable(test_util
  ${CMAKE_SOURCE_DIR}/test/test_util.cpp
)
target_include_directories(test_util PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(test_util PRIVATE hart Catch2::Catch2WithMain)

add_executable(test_csr
  ${CMAKE_SOURCE_DIR}/test/test_csr.cpp
)
target_include_directories(test_csr PUBLIC ${CMAKE_SOURCE_DIR}/include)
 target_link_libraries(test_csr PRIVATE hart Catch2::Catch2WithMain)

add_executable(test_version
  ${CMAKE_SOURCE_DIR}/test/test_version.cpp
)
target_include_directories(test_version PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(test_version PRIVATE hart Catch2::Catch2WithMain)

# add_executable(test_decode
#   ${CMAKE_SOURCE_DIR}/test/test_decode.cpp
# )
# target_include_directories(test_decode PUBLIC ${CMAKE_SOURCE_DIR}/include)
# target_link_libraries(test_decode PRIVATE hart Catch2::Catch2WithMain)

include(CTest)
include(Catch)
catch_discover_tests(test_bits_directed)

foreach (random_test IN LISTS RANDOM_TESTS)
  catch_discover_tests(${random_test})
endforeach()

# catch_discover_tests(test_version)
# catch_discover_tests(test_csr)
