# USD-Bio Test Suite

# Find Google Test
find_package(GTest CONFIG REQUIRED)

# Smoke test executable
add_executable(usd_bio_smoke_test
    smoke_test.cpp
)

target_link_libraries(usd_bio_smoke_test
    PRIVATE
        GTest::gtest
        GTest::gtest_main
        usd_bio_lib
)

# Register test with CTest
add_test(NAME SmokeTest COMMAND usd_bio_smoke_test)

# Additional test executables will be added in future milestones
