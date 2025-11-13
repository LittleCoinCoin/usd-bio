# ./CMakeList.txt
cmake_minimum_required (VERSION 3.20)

set(TargetName "OpenUSD-setup-vcpkg")
project (${TargetName})

# Because the USD plugin file directory resolution expects the dlls to be in a "/bin" folder
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${TargetName}/$<CONFIG>/bin" CACHE STRING "" )

add_subdirectory (${TargetName})

# USD-Bio Extension Library
option(BUILD_USD_BIO "Build USD-Bio extension library" ON)
if(BUILD_USD_BIO)
    add_subdirectory(src)
endif()

# Testing (will be configured in Milestone 1.3)
option(BUILD_TESTS "Build test suite" OFF)
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# Examples (optional)
option(BUILD_EXAMPLES "Build example programs" ON)
if(BUILD_EXAMPLES AND BUILD_USD_BIO)
    add_subdirectory(examples)
endif()
