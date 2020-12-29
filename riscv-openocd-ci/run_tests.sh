#!/bin/bash

CHECKOUT_DIR=`pwd`/riscv-openocd-ci/work/riscv-tests

# Fail on first error.
set -e

# Echo commands.
set -o xtrace

# Checkout riscv-tests.
mkdir -p "$CHECKOUT_DIR"
cd "$CHECKOUT_DIR"
git clone --recursive https://github.com/riscv/riscv-tests .

# Run the debug tests.
# Do not stop even on a failed test.
cd debug
make -k -j`nproc` all || true
