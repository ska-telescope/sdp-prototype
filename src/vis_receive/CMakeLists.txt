cmake_minimum_required(VERSION 3.6)
project(vis_recv_c C CXX)
find_package(Threads REQUIRED)

set(CMAKE_CXX_STANDARD 14)

# -----------------------------------------------------------------------------
# List of source files.
# -----------------------------------------------------------------------------

include_directories(src)
set(recv_SRC
    ${PROJECT_SOURCE_DIR}/src/buffer.c
    ${PROJECT_SOURCE_DIR}/src/receiver.c
    ${PROJECT_SOURCE_DIR}/src/stream.c
    ${PROJECT_SOURCE_DIR}/src/thread_barrier.c
    ${PROJECT_SOURCE_DIR}/src/thread_pool.c
    ${PROJECT_SOURCE_DIR}/src/timer.c
)

# -----------------------------------------------------------------------------
# Measurement Set write support 
# -----------------------------------------------------------------------------

if(OSKAR_DIR)
		find_path(OSKAR_INCLUDE_DIR oskar_measurement_set.h
    		     	HINTS ${OSKAR_DIR}
							PATH_SUFFIXES include)	
		find_path(OSKAR_LIBRARY_DIR liboskar_ms.so
    		    	HINTS ${OSKAR_DIR}
							PATH_SUFFIXES lib)	
		if(OSKAR_INCLUDE_DIR AND OSKAR_LIBRARY_DIR)
				include_directories("${OSKAR_INCLUDE_DIR}")
				link_directories("${OSKAR_LIBRARY_DIR}")
				list(APPEND recv_SRC
  		  		${PROJECT_SOURCE_DIR}/src/write_ms_access.c
				)
				include_directories("${CASACORE_HOME}/include")
				link_directories("${CASACORE_HOME}/lib")
				set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D WITH_MS")
				set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -D WITH_MS")
		endif()
endif()

# -----------------------------------------------------------------------------
# Coveralls
# -----------------------------------------------------------------------------

option(COVERALLS "Turn on coveralls support" OFF)
option(COVERALLS_UPLOAD "Upload the generated coveralls json" ON)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH}
	${PROJECT_SOURCE_DIR}/coveralls-cmake/cmake)

if (COVERALLS)
	include(Coveralls)
	coveralls_turn_on_coverage()
endif()

if (COVERALLS)
	coveralls_setup(
        "${recv_SRC}"
        ${COVERALLS_UPLOAD}
        "${PROJECT_SOURCE_DIR}/coveralls-cmake/cmake")
endif()

# -----------------------------------------------------------------------------
# Google Sanitizers
# -----------------------------------------------------------------------------

if(ENABLE_ASAN)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O1")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fuse-ld=gold")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fno-omit-frame-pointer")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=leak")
endif()

if(ENABLE_USAN)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fuse-ld=gold")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=undefined")
endif()

if(ENABLE_TSAN)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fuse-ld=gold")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=thread")
endif()

# -----------------------------------------------------------------------------
# Valgrind
# -----------------------------------------------------------------------------

include (CTest)

# -----------------------------------------------------------------------------
# Unit test
# -----------------------------------------------------------------------------

# Get version number from file and add to definitions for compiler.
file(STRINGS "VERSION" RECV_VERSION)
add_definitions(-DRECV_VERSION="${RECV_VERSION}")


# Build library.
add_library(vis_recv ${recv_SRC})
target_link_libraries(vis_recv Threads::Threads)
if(OSKAR_LIBRARY_DIR)
	target_link_libraries(vis_recv oskar_ms casa_casa casa_ms casa_meas)
endif()

# Build executable.
add_executable(recv src/main.c)
target_link_libraries(recv vis_recv Threads::Threads)
if(OSKAR_LIBRARY_DIR)
	target_link_libraries(recv oskar_ms casa_casa casa_ms casa_meas)
endif()

# Build tests.
include(CTest)
add_subdirectory(tests)

# Build unit testing framework.
add_subdirectory(extern/gtest)
