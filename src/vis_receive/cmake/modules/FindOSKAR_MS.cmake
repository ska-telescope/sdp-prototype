# FindOSKAR_MS.cmake
# ============================================================================
# CMake script to find the OSKAR ms library.
#
# ============================================================================
# Defines the following variables:
#   OSKAR_MS_FOUND
#   OSKAR_MS_INCLUDE_DIR
#   OSKAR_MS_LIBRARY
#
# Environment and CMake varaibles affecting this script.
#   OSKAR_MS_INSTALL_DIR
#
# ============================================================================


# Include default error handling macro
include(FindPackageHandleStandardArgs)

# Find the oskar-ms include directory
find_path(OSKAR_MS_INCLUDE_DIR oskar_measurement_set.h
        HINTS ${OSKAR_MS_INSTALL_DIR} $ENV{OSKAR_MS_INSTALL_DIR}
        PATH_SUFFIXES include include/oskar include/oskar/ms)

get_filename_component(OSKAR_MS_INCLUDE_DIR ${OSKAR_MS_INCLUDE_DIR} DIRECTORY)

# Find the oskar-ms library
find_library(OSKAR_MS_LIBRARY oskar_ms
        NAMES oskar_ms
        HINTS ${OSKAR_MS_INSTALL_DIR} $ENV{OSKAR_MS_INSTALL_DIR}
        PATH_SUFFIXES lib
        )

find_package_handle_standard_args(oskar_ms
        DEFAULT_MSG OSKAR_MS_LIBRARY OSKAR_MS_INCLUDE_DIR)

mark_as_advanced(
        OSKAR_MS_FOUND
        OSKAR_MS_LIBRARY
        OSKAR_MS_INCLUDE_DIR
)
