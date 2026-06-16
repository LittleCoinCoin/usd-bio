# src/CMakeLists.txt

add_library(usd_bio STATIC
    core/extension.cpp
    include/usd_bio/extension.h
)

target_include_directories(usd_bio PUBLIC include ${TBB_INCLUDE_DIRS})

# Link dependencies
target_link_libraries(usd_bio PUBLIC ${TBB_LIBRARIES} ${PXR_LIBRARIES})

# Installation
install(TARGETS usd_bio
    EXPORT usd_bio_targets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(DIRECTORY include/
    DESTINATION include
)