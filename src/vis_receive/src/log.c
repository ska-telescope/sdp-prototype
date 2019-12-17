#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
#include <sys/time.h>
#include <unistd.h>

#include "log.h"

static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

void log_message(
    int severity,
    int thread_id,
    const char* function,
    const char* file,
    const int line,
    const char* format, ...)
{
    FILE* stream;
    va_list args;

    /* Get timestamp. */
    char time_str[36];
    struct timeval tv;
    struct tm* timeinfo;
    const time_t unix_time = time(NULL);
    timeinfo = gmtime(&unix_time);
    gettimeofday(&tv, 0);
    const int msec = tv.tv_usec / 1000;
    snprintf(time_str, sizeof(time_str),
        "%04d-%02d-%02dT%02d:%02d:%02d.%03dZ",
        timeinfo->tm_year + 1900,
        timeinfo->tm_mon + 1,
        timeinfo->tm_mday,
        timeinfo->tm_hour,
        timeinfo->tm_min,
        timeinfo->tm_sec,
        msec);

    /* Convert severity level to string. */
    const char* severity_str;
    switch (severity)
    {
        case LOG_LVL_DEBUG:
            stream = stdout;
            severity_str = "DEBUG";
            break;
        case LOG_LVL_INFO:
            stream = stdout;
            severity_str = "INFO";
            break;
        case LOG_LVL_WARN:
            stream = stdout;
            severity_str = "WARNING";
            break;
        case LOG_LVL_ERROR:
            stream = stderr;
            severity_str = "ERROR";
            break;
        case LOG_LVL_CRITICAL:
            stream = stderr;
            severity_str = "CRITICAL";
            break;
        default:
            stream = stderr;
            severity_str = "UNKNOWN";
            break;
    }

    /* Print formatted message. */
    const int version = 1;
    pthread_mutex_lock(&lock);
    va_start(args, format);
    fprintf(stream, "%d|%s|%s|Thread-%d|%s|%s#%d||",
            version, time_str, severity_str, thread_id,
            function, file, line);
    vfprintf(stream, format, args);
    fprintf(stream, "\n");
    va_end(args);
    pthread_mutex_unlock(&lock);
}
