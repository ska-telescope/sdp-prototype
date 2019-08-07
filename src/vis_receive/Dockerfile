# =============================================================================
# Visibility Receive image : build stage
# =============================================================================
FROM kernsuite/base:5 AS buildenv

WORKDIR /app

# Install depdendencies
RUN docker-apt-install \
    gpg \
    gcc \
    g++ \
    git \
    cmake \
    libblas-dev \
    liblapack-dev \
    casacore-dev

# Install and install OSKAR MS library
RUN git clone https://github.com/OxfordSKA/OSKAR.git && \
    mkdir OSKAR/oskar/ms/build && \
    cd OSKAR/oskar/ms/build && \
    cmake --DCASACORE_LIB_DIR=/usr/lib/x86_64-linux-gnu  .. && \
    make -j4 && \
    make install

# Copy vis_receive code into buildenv
COPY extern /app/vis_receive/extern
COPY src /app/vis_receive/src
COPY CMakeLists.txt /app/vis_receive/CMakeLists.txt
COPY Makefile /app/vis_receive/Makefile
COPY VERSION /app/vis_receive/VERSION
COPY tests /app/vis_receive/tests

# Build the vis_receive application
RUN cd /app/vis_receive && \
    mkdir build && cd build && cmake build .. && make -j4

# =============================================================================
# Visibility receive image : Final stage
# =============================================================================
FROM kernsuite/base:5

WORKDIR /app

# Install casa(core?) ms runtime library
RUN docker-apt-install libcasa-ms3

# Copy binaries compiled in the buid stage into the final image.
COPY --from=buildenv /usr/local/lib/liboskar_ms.* /usr/local/lib/
COPY --from=buildenv /app/vis_receive/build/recv /usr/local/bin/

# Copy test into final layer
# FIXME(BMo) Remove this when done debugging!
COPY --from=buildenv /app/vis_receive/build/tests/recv_test /app/
