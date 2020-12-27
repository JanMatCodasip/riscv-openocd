
from utils.utils import MeasureTime, ChangeWorkdir, run_cmd, info_box
import logging
from logging import info
from multiprocessing import cpu_count
import os
import sys


def parse_args():
    import argparse
    parser = argparse.ArgumentParser("Build Spike (RISC-V ISA Simulator) from local (checked-out) source code")
    parser.add_argument("--src-dir", required=True, help="Directory where OpenOCD source code is located")
    parser.add_argument("--install-dir", required=True, help="Directory where to install OpenOCD after the build")
    return parser.parse_args()


def build_spike(src_dir, install_dir, with_coverage=False):
    assert os.path.isdir(src_dir)
    with ChangeWorkdir(src_dir):
        info_box("Bootstrapping OpenOCD ...")
        run_cmd(["bash", "./bootstrap"])
        info_box("Configuring OpenOCD ...")
        configure_args = [
            "--enable-remote-bitbang",
            "--enable-jtag_vpi",
            "--enable-ftdi",
            "--prefix=" + install_dir
        ]
        if with_coverage:
            configure_args += [
                "CFLAGS=-O0 --coverage -fprofile-arcs -ftest-coverage",
                "CXXFLAGS=-O0 --coverage -fprofile-arcs -ftest-coverage",
                "LDFLAGS=-fprofile-arcs -lgcov"
            ]
        run_cmd(["bash", "./configure"] + configure_args)
        if with_coverage:
            # Need to patch OpenOCD source so that coverage is collected even if OpenOCD
            # gets terminated by a signal.
            patch_file = os.path.join(script_dir, "patches", "openocd_gcov_flush.patch")
            git_apply_patch(patch_file, src_dir)
        info_box("Building OpenOCD ...")
        run_cmd(["make", "clean"])  # safety
        run_cmd(["make", "-j" + str(cpu_count())])
        info_box("Installing OpenOCD ...")
        run_cmd(["make", "install"])
        info_box("Finished build of OpenOCD. ")


def check_spike_runs(install_dir):
    spike_binary = os.path.join(install_dir, "bin", "spike")
    assert os.path.isfile(spike_binary)
    run_cmd([spike_binary, "--version"])


def main():
    args = parse_args()

    # use absolute paths
    args.src_dir = os.path.abspath(args.src_dir)
    args.install_dir = os.path.abspath(args.install_dir)

    build_spike(args.src_dir, args.install_dir)
    check_spike_runs(args.install_dir)

    return 0


script_dir = None

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    script_name = os.path.basename(__file__)
    script_dir = os.path.abspath(os.path.dirname(__file__))
    with MeasureTime("Script " + script_name):
        retcode = main()
    sys.exit(retcode)
