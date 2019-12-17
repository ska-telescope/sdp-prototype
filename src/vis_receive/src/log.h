#ifndef LOG_H_
#define LOG_H_

#include <stdarg.h>

#ifdef __cplusplus
extern "C" {
#endif

enum LOG_SEVERITY
{
    LOG_LVL_DEBUG,
    LOG_LVL_INFO,
    LOG_LVL_WARN,
    LOG_LVL_ERROR,
    LOG_LVL_CRITICAL
};

void log_message(
    int severity,
    int thread_id,
    const char* function,
    const char* file,
    const int line,
    const char* format, ...);

#ifndef SOURCE_PATH_SIZE
#define SOURCE_PATH_SIZE 0
#endif

#define FILENAME (__FILE__ + SOURCE_PATH_SIZE)

#define LOG_MSG(SEVERITY, THREAD_ID, ...) \
    log_message(SEVERITY, THREAD_ID, __func__,\
    FILENAME, __LINE__, __VA_ARGS__);

/* Convenience macros to log messages with the appropriate
 * severity level. */

#define LOG_DEBUG(THREAD_ID, ...) \
    LOG_MSG(LOG_LVL_DEBUG, THREAD_ID, __VA_ARGS__)

#define LOG_INFO(THREAD_ID, ...) \
    LOG_MSG(LOG_LVL_INFO, THREAD_ID, __VA_ARGS__)

#define LOG_WARN(THREAD_ID, ...) \
    LOG_MSG(LOG_LVL_WARN, THREAD_ID, __VA_ARGS__)

#define LOG_ERROR(THREAD_ID, ...) \
    LOG_MSG(LOG_LVL_ERROR, THREAD_ID, __VA_ARGS__)

#define LOG_CRITICAL(THREAD_ID, ...) \
    LOG_MSG(LOG_LVL_CRITICAL, THREAD_ID, __VA_ARGS__)

#ifdef __cplusplus
}
#endif

#endif /* include guard */
