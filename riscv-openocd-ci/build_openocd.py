

import logging
from logging import info
from multiprocessing import cpu_count
import os
import sys
from utils.utils import MeasureTime, ChangeWorkdir, run_cmd, info_box, git_apply_patch, git_revision_info, \
    check_file_exists, check_dir_exists


def parse_args():
    import argparse
    parser = argparse.ArgumentParser("Build OpenOCD from local (checked-out) source")
    parser.add_argument("--src-dir", required=True, help="Directory where OpenOCD source code is located")
    parser.add_argument("--install-dir", required=True, help="Directory where to install OpenOCD after the build")
    parser.add_argument("--coverage", action="store_true", default=False,
                        help="Compile OpenOCD with support for code coverage collection (using gcov)")
    return parser.parse_args()


def print_openocd_rev(src_dir):
    rev = git_revision_info(src_dir)
    info_box("OpenOCD revision")
    info("Commit ID:   {}".format(rev["hash"]))
    info("Subject:     {}".format(rev["subject"]))
    info("Author:      {}".format(rev["author"]))
    info("Author date: {}".format(rev["author_date"]))
    info("Commit date: {}".format(rev["commit_date"]))


def build_openocd(src_dir, install_dir, with_coverage=False):
    check_dir_exists(src_dir)
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


def check_openocd_runs(install_dir):
    openocd_binary = os.path.join(install_dir, "bin", "openocd")
    check_file_exists(openocd_binary)
    info("Checking that OpenOCD runs ...")
    run_cmd([openocd_binary, "--version"])


def main():
    args = parse_args()

    # use absolute paths
    args.src_dir = os.path.abspath(args.src_dir)
    args.install_dir = os.path.abspath(args.install_dir)

    print_openocd_rev(args.src_dir)
    build_openocd(args.src_dir, args.install_dir, with_coverage=args.coverage)
    check_openocd_runs(args.install_dir)

    return 0


script_dir = None

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    script_name = os.path.basename(__file__)
    script_dir = os.path.abspath(os.path.dirname(__file__))
    with MeasureTime("Script " + script_name):
        retcode = main()
    sys.exit(retcode)
