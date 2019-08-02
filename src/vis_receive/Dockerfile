# =============================================================================
# Visibility Receive image : Base image
# =============================================================================
FROM kernsuite/base:5 AS build

WORKDIR /app
COPY . /app

# Install Casacore Binary Packages
RUN docker-apt-install gpg gcc g++ cmake libblas-dev \
    liblapack-dev git

RUN docker-apt-install casacore-dev

RUN git clone https://github.com/OxfordSKA/OSKAR.git

# Install OSKAR
RUN mkdir OSKAR/oskar/ms/build && cd OSKAR/oskar/ms/build && cmake OSKAR/oskar/ms/build  --DCASACORE_LIB_DIR=/usr/lib/x86_64-linux-gnu  .. \
    && make -j4 && make install

RUN cd /app && mkdir build && cd build && cmake build .. && make -j4

# -----------------------------------------------------------------------------
# Final layer
# -----------------------------------------------------------------------------
FROM kernsuite/base:5

WORKDIR /app

RUN docker-apt-install libcasa-ms3

# Copy OSKAR
COPY --from=build /usr/local/lib/liboskar_ms.* /usr/local/lib/
COPY --from=build /app/build/recv /app
COPY --from=build /app/build/tests/recv_test /app
