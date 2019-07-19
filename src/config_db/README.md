SKA SDP Configuration Database
==============================

This is the frontend module for accessing SKA SDP configuration
information. It provides ways for SDP controller and processing
components to discover and manipulate the intended state of the
system.

At the moment this is implemented on top of `etcd`, a highly-available
database. This library provides primitives for atomic queries and
updates to the stored configuration information.

See SCHEMA.md for the implemented configuration schema.
