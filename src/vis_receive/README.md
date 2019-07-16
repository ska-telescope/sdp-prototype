# Simple visibility receive workflow prototype

This code was originally written for the 
[SKA Science Data Processor Integration Prototype](https://github.com/SKA-ScienceDataProcessor/integration-prototype) and copied 
to this repository.

## Introduction

This workflow script uses a combination of SPEAD asyncio and blocking worker
threads to asynchronously receive and perform ingest processing on visibility
data streamed from CSP.

This workflow assumes that each ingest process receives and processes the 
complete time stream for a set of channels (which may be as many as ~300).

The total data from CSP for the scheduling block, which may consist of as much
as ~65k channels, is then split between a number of ingest processes.

The assumption we are taking is that these ingest processes can be deployed 
as a set of Docker containers using container orchestration (currently 
Docker Swarm).

## Build Instructions
To build the code on a local machine, ensure `make` and `CMake` are both install
ed and give the following commands from the current directory:

```bash
mkdir build
cd build
cmake ..
make
```

To run the unit tests from the build directory, either run

```bash
ctest
```
or run the unit test binary directly using:

```bash
./test/recv_test
```

## Test Instructions

To be written
