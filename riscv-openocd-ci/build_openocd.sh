#!/bin/bash

INSTALL_DIR=`pwd`/riscv-openocd-ci/work/install

# Fail on first error.
set -e

# Assuming OpenOCD source is already checked-out in the CWD.

./bootstrap

# Enable most frequently used JTAG drivers.
# Allow for code coverage collection.
./configure \
    --enable-remote-bitbang \
    --enable-jtag_vpi \
    --enable-ftdi \
    --prefix=$INSTALL_DIR \
    CFLAGS="-O0 --coverage -fprofile-arcs -ftest-coverage" \
    CXXFLAGS="-O0 --coverage -fprofile-arcs -ftest-coverage" \
    LDFLAGS="-fprofile-arcs -lgcov"

# Patch OpenOCD so that coverage is recorded also when terminated
# by a signal.
git apply riscv-openocd-ci/patches/openocd_gcov_flush.patch

# Build and install OpenOCD
make clean  # safety
make -j`nproc`
make install
