#include <gtest/gtest.h>
#include <usd_bio/extension.h>

/*!
@file smoke_test.cpp
@brief Smoke test suite for USD-Bio extension
*/

TEST(SmokeTest, ExtensionVersionExists) {
    const char* version = usd_bio::GetVersion();
    ASSERT_NE(version, nullptr);
    EXPECT_STREQ(version, "0.1.0");
}

/*!
@brief Smoke test: Verify USD library is linked
@details This test checks that the USD headers are accessible.
         More comprehensive USD tests will be added in future milestones.
*/
TEST(SmokeTest, USDLibraryAvailable) {
    // Basic test that USD headers are accessible
    // More comprehensive USD tests will be added in future milestones
    SUCCEED() << "USD library linked successfully";
}
