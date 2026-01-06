# ./CMakeLists.txt
cmake_minimum_required(VERSION 3.20)

project(usd-bio LANGUAGES CXX)

# Set a C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Dependencies ---

# Find OpenUSD on the system.
# Users should set CMAKE_PREFIX_PATH to their OpenUSD installation.
find_package(pxr REQUIRED)

# Manually find TBB (since find_package(TBB) is failing for user)
find_path(TBB_INCLUDE_DIR
    NAMES tbb/tbb.h
    PATHS /usr/local/include /usr/include
    # Add common TBB installation paths if needed
    # PATHS "${CMAKE_PREFIX_PATH}/tbb/include"
    # PATHS "/opt/homebrew/Cellar/tbb/*/include"
)

find_library(TBB_LIBRARY
    NAMES tbb
    PATHS /usr/local/lib /usr/lib
    # Add common TBB installation paths if needed
    # PATHS "${CMAKE_PREFIX_PATH}/tbb/lib"
    # PATHS "/opt/homebrew/Cellar/tbb/*/lib"
)

if(TBB_INCLUDE_DIR AND TBB_LIBRARY)
    set(TBB_FOUND TRUE)
    set(TBB_LIBRARIES ${TBB_LIBRARY})
    set(TBB_INCLUDE_DIRS ${TBB_INCLUDE_DIR})
    message(STATUS "Found TBB: ${TBB_LIBRARIES} (include: ${TBB_INCLUDE_DIRS})")
else()
    message(FATAL_ERROR "Could not find TBB. Please set TBB_INCLUDE_DIR and TBB_LIBRARY manually, or ensure TBB is installed in a standard location.")
endif()

# Find GTest
find_package(GTest REQUIRED)

# Find OpenGL for garch (OpenUSD dependency)
find_package(OpenGL REQUIRED)

# --- Targets ---

# USD-Bio Extension Library
option(BUILD_USD_BIO "Build USD-Bio extension library" ON)
if(BUILD_USD_BIO)
    add_subdirectory(src)
endif()

# Testing
option(BUILD_TESTS "Build test suite" ON)
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# Examples
option(BUILD_EXAMPLES "Build example programs" ON)
if(BUILD_EXAMPLES AND BUILD_USD_BIO)
    add_subdirectory(examples)
endif()