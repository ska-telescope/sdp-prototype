# SKA Logging Package

This package contains logging-related utility classes and
functions.

In particular it provides functions to configure logging for
both Tango and non-Tango devices to use a a standard format.

Note that the way this is currently packaged, an application
that only wants to use Python logging will have an unwanted
dependency on pytango. Hence in its current organisation this
is suitable for evaluation only. However the core_logging
module does not depend on pytango, only the package.
