cmake_minimum_required(VERSION 3.22.1)
project("aion_post_engine" CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Optimization flags for native performance
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -ffast-math")
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -O0 -g")

# Global linker flags for 16 KB page alignment (Android 15 compatibility)
add_link_options("-Wl,-z,common-page-size=16384")
add_link_options("-Wl,-z,max-page-size=16384")
add_link_options("-Wl,-z,relro")
add_link_options("-Wl,-z,now")





# Source files for native C++ PoST core
set(NATIVE_SOURCES
    src/main/cpp/post_engine.cpp
    src/main/cpp/sha256.cpp
    src/main/cpp/jni_bridge.cpp
)

# Shared library target for Android JNI (libaion_post.so)
add_library(aion_post SHARED ${NATIVE_SOURCES})

# Include header directories
target_include_directories(aion_post PRIVATE src/main/cpp)

# Locate NDK logging library
find_library(log-lib log)

# Link libraries
target_link_libraries(aion_post PRIVATE ${log-lib} c++)

# Enable 16 KB page alignment for Android 15+ compatibility (Reinforcement)
target_link_options(aion_post PRIVATE "-Wl,-z,common-page-size=16384" "-Wl,-z,max-page-size=16384")


