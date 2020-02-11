This code was originally written for the 
[SKA Science Data Processor Integration Prototype](https://github.com/SKA-ScienceDataProcessor/integration-prototype) and copied 
to this repository.

## Introduction

This is a simple C code for a visibility receiver capable of receiving UDP-based
SPEAD (Streaming Protocol for Exchanging Astronomical Data) streams containing 
the item identifiers specified in the of the SDP-CSP ICD.

More information about SPEAD can be found here 
https://casper.ssl.berkeley.edu/astrobaki/images/9/93/SPEADsignedRelease.pdf 

## Dependencies

- CASACORE >= 2.0.0 : https://github.com/casacore/casacore
- OSKAR measurement set library : https://github.com/OxfordSKA/OSKAR
    - The OSKAR ms library can be installed as a standalone library   
      from the `oskar/ms` folder of the repo. eg.: 
      ```
      git clone https://github.com/OxfordSKA/OSKAR.git
      mkdir OSKAR/oskar/ms/release
      cd OSAKR/oskar/ms/release
      cmake ..
      make
      make install
      ```  

## Build Instructions

To build the code on a local machine, ensure `make` and `CMake` are both installed 
and give the following commands from the current directory:

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

### Starting the receiver

Run natively with:

```bash
./recv -d .
```

or with Docker:

```bash
docker run -t --rm \
    -p 41000:41000/udp \
    -v $(pwd)/output:/app/output \
    --env USER=orca \
    nexus.engageska-portugal.pt/sdp-prototype/vis-receive:latest
```

### Staring the sender

```bash
python3 send.py
```