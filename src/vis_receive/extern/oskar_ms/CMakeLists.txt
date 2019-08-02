#
# ms/CMakeLists.txt
#
cmake_minimum_required(VERSION 2.8)

list(INSERT CMAKE_MODULE_PATH 0 ${PROJECT_SOURCE_DIR}/cmake/modules)

find_package(CasaCore REQUIRED)

if (CASACORE_FOUND)

    set(OSKAR_LIB_INSTALL_DIR "${CMAKE_INSTALL_PREFIX}/lib")
    set(OSKAR_VERSION "1.1.3")

    set(ms_SRC
        src/oskar_ms_accessors.cpp
        src/oskar_ms_add_history.cpp
        src/oskar_ms_close.cpp
        src/oskar_ms_create.cpp
        src/oskar_ms_open.cpp
        src/oskar_ms_read.cpp
        src/oskar_ms_write.cpp
    )

    # Build and install the oskar_ms library.
    add_library(oskar_ms SHARED ${ms_SRC})
    include_directories(
			${CASACORE_INCLUDE_DIR}
	    ${CASACORE_INCLUDE_DIR}/casacore
      ${PROJECT_SOURCE_DIR}
		)
    set_target_properties(oskar_ms PROPERTIES
        SOVERSION ${OSKAR_VERSION}
        VERSION ${OSKAR_VERSION}
        COMPILE_FLAGS "-Wno-cast-qual -fvisibility=default")
    target_link_libraries(oskar_ms ${CASACORE_LIBRARIES})
    install(TARGETS oskar_ms
        ARCHIVE DESTINATION ${OSKAR_LIB_INSTALL_DIR} COMPONENT libraries
        LIBRARY DESTINATION ${OSKAR_LIB_INSTALL_DIR} COMPONENT libraries
        RUNTIME DESTINATION ${OSKAR_BIN_INSTALL_DIR} COMPONENT runtime
    )

    # ==== Recurse into test subdirectory.
		#add_subdirectory(../gtest)
		if (GTEST_INCLUDE_DIR)
			add_subdirectory(test)
		endif(GTEST_INCLUDE_DIR)
		set(OSKAR_MS_INCLUDE_DIR "${CMAKE_INSTALL_PREFIX}/include")


endif(CASACORE_FOUND)
