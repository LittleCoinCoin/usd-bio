# tests/CMakeLists.txt

add_executable(smoke_test
    smoke_test.cpp
)

target_link_libraries(smoke_test
    PRIVATE
        GTest::gtest
        GTest::gtest_main
        usd_bio
)

include(GoogleTest)
gtest_discover_tests(smoke_test PROPERTIES TIMEOUT 60) # Set a generous timeout (e.g., 60 seconds)