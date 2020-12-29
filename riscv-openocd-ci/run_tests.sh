#!/bin/bash

CHECKOUT_DIR=`pwd`/riscv-openocd-ci/work/riscv-isa-sim

# Fail on first error.
set -e

# Echo commands.
set -o xtrace

# Checkout riscv-tests.
mkdir -p "$CHECKOUT_DIR"
cd "$CHECKOUT_DIR"
git clone --recursive https://github.com/riscv/riscv-tests .

# Run the debug tests.
# Do not stop even if there is a failed test.
cd debug
make -k || true

