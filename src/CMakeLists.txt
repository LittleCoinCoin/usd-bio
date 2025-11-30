# USD-Bio Extension Library
project(usd_bio VERSION 0.1.0 LANGUAGES CXX)

# Source files
set(USD_BIO_SOURCES
    core/extension.cpp
)

# Header files
set(USD_BIO_HEADERS
    include/usd_bio/extension.h
)

# Create library
add_library(usd_bio_lib STATIC
    ${USD_BIO_SOURCES}
    ${USD_BIO_HEADERS}
)

# Set C++20 standard
target_compile_features(usd_bio_lib PUBLIC cxx_std_20)

# Include directories
target_include_directories(usd_bio_lib
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

# Link USD libraries
find_package(pxr CONFIG REQUIRED)
target_link_libraries(usd_bio_lib
    PUBLIC
        usd
)

# Install targets
install(TARGETS usd_bio_lib
    EXPORT usd_bio_targets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(DIRECTORY include/
    DESTINATION include
)
