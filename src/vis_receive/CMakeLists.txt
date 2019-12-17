# CMake initialisation.
cmake_minimum_required(VERSION 3.6 FATAL_ERROR)

# Set policies to avoid CMake warnings.
if (POLICY CMP0042)
    cmake_policy(SET CMP0042 NEW)
endif()
if (POLICY CMP0045)
    cmake_policy(SET CMP0045 NEW)
endif()
if (POLICY CMP0068)
    cmake_policy(SET CMP0068 OLD)
endif()

# Declare the CMake project.
project(vis_recv_c C CXX)

set(CMAKE_C_STANDARD 99)
set(CMAKE_CXX_STANDARD 14)

# Add local CMake module path.
list(INSERT CMAKE_MODULE_PATH 0 ${CMAKE_SOURCE_DIR}/cmake/modules)

# Get version number from file
file(STRINGS "VERSION" RECV_VERSION)

# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------
find_package(Threads REQUIRED)
find_package(CasaCore)
find_package(OSKAR_MS)


# -----------------------------------------------------------------------------
# Measurement Set write support
# -----------------------------------------------------------------------------
if (OSKAR_MS_FOUND AND CASACORE_FOUND)
    include_directories(${OSKAR_MS_INCLUDE_DIR})
    include_directories(${OSKAR_MS_INCLUDE_DIR}/ms)
    include_directories(${CASACORE_INCLUDE_DIR})
    include_directories(${CASACORE_INCLUDE_DIR}/casacore)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D WITH_MS")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -D WITH_MS")
endif()


# -----------------------------------------------------------------------------
# Coveralls (code coverage) set up
# -----------------------------------------------------------------------------
option(COVERALLS "Turn on coveralls support" OFF)
option(COVERALLS_UPLOAD "Upload the generated coveralls json" OFF)

if (COVERALLS)
    include(Coveralls)
    coveralls_turn_on_coverage()
    coveralls_setup("${recv_SRC}" ${COVERALLS_UPLOAD}
        "${PROJECT_SOURCE_DIR}/extern/coveralls-cmake/cmake")
endif()

# -----------------------------------------------------------------------------
# Set compiler flags for Google Sanitizers
# -----------------------------------------------------------------------------
# Address sanitiser
if(ENABLE_ASAN)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O1")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fuse-ld=gold")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fno-omit-frame-pointer")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=leak")
endif()

# Undefined sanitiser
if(ENABLE_USAN)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fuse-ld=gold")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=undefined")
endif()

# Thread sanitiser
if(ENABLE_TSAN)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fuse-ld=gold")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=thread")
endif()

# -----------------------------------------------------------------------------
# Source files
# -----------------------------------------------------------------------------

include_directories(src)
string(LENGTH "${CMAKE_SOURCE_DIR}/" SOURCE_PATH_SIZE)
add_definitions(-DSOURCE_PATH_SIZE=${SOURCE_PATH_SIZE})
set(recv_SRC
    ${PROJECT_SOURCE_DIR}/src/buffer.c
    ${PROJECT_SOURCE_DIR}/src/log.c
    ${PROJECT_SOURCE_DIR}/src/receiver.c
    ${PROJECT_SOURCE_DIR}/src/stream.c
    ${PROJECT_SOURCE_DIR}/src/thread_barrier.c
    ${PROJECT_SOURCE_DIR}/src/thread_pool.c
    ${PROJECT_SOURCE_DIR}/src/timer.c
)

if (OSKAR_MS_FOUND)
    list(APPEND recv_SRC ${PROJECT_SOURCE_DIR}/src/write_ms_access.c)
endif(OSKAR_MS_FOUND)

# -----------------------------------------------------------------------------
# Automatically set the build type if not specified
# -----------------------------------------------------------------------------
if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    # Use debug mode if building in dbg or debug directory.
    get_filename_component(dirname ${CMAKE_BINARY_DIR} NAME)
    if (${dirname} MATCHES "dbg" OR ${dirname} MATCHES "debug")
        set(CMAKE_BUILD_TYPE Debug)
    else()
        set(CMAKE_BUILD_TYPE Release)
    endif()
    message(STATUS "INFO: Setting CMAKE_BUILD_TYPE to ${CMAKE_BUILD_TYPE}")
endif()

# -----------------------------------------------------------------------------
# Build
# -----------------------------------------------------------------------------

add_definitions(-DRECV_VERSION="${RECV_VERSION}")

if ("${CMAKE_C_COMPILER_ID}" MATCHES ".*Clang.*"
        OR "${CMAKE_C_COMPILER_ID}" STREQUAL "GNU")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra")
endif()

# Build library.
set(libname vis_recv)
add_library(${libname} ${recv_SRC})
target_link_libraries(${libname} Threads::Threads)
if (OSKAR_MS_FOUND)
    target_link_libraries(${libname} ${OSKAR_MS_LIBRARY} ${CASACORE_LIBRARIES})
endif()
set_target_properties(${libname} PROPERTIES
        SOVERSION ${RECV_VERSION}
        VERSION ${RECV_VERSION})

# Build executable.
add_executable(recv src/main.c)
target_link_libraries(recv vis_recv Threads::Threads)
if (OSKAR_MS_FOUND)
    target_link_libraries(recv ${OSKAR_MS_LIBRARY} ${CASACORE_LIBRARIES})
endif()

# -----------------------------------------------------------------------------
# Unit tests
# -----------------------------------------------------------------------------

# Build tests.
include(CTest)
add_subdirectory(tests)

# Build unit testing framework.
add_subdirectory(extern/gtest)
