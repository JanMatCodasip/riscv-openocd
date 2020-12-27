
from utils.utils import MeasureTime, ChangeWorkdir, run_cmd, info_box, check_dir_exists, check_file_exists
import logging
from logging import info
from multiprocessing import cpu_count
import os
import sys


def parse_args():
    import argparse
    parser = argparse.ArgumentParser("Build Spike (RISC-V ISA Simulator) from local (checked-out) source code")
    parser.add_argument("--src-dir", required=True, help="Directory where Spike source code is located")
    parser.add_argument("--install-dir", required=True, help="Directory where to install Spike after the build")
    return parser.parse_args()


def print_spike_rev(src_dir):
    rev = git_revision_info(src_dir)
    info_box("Spike revision")
    info("Commit ID:   {}".format(rev["hash"]))
    info("Subject:     {}".format(rev["subject"]))
    info("Author:      {}".format(rev["author"]))
    info("Author date: {}".format(rev["author_date"]))
    info("Commit date: {}".format(rev["commit_date"]))


def build_spike(src_dir, install_dir):
    check_dir_exists(src_dir)
    build_dir = os.path.join(src_dir, "build")
    os.mkdir(build_dir)
    with ChangeWorkdir(build_dir):
        info_box("Configuring Spike ...")
        run_cmd(["bash", "../configure", "--prefix=" + install_dir])
        info_box("Building Spike ...")
        run_cmd(["make", "clean"])  # safety
        run_cmd(["make", "-j" + str(cpu_count())])
        info_box("Installing Spike ...")
        run_cmd(["make", "install"])
        info_box("Finished Spike build. ")


def check_spike_runs(install_dir):
    spike_binary = os.path.join(install_dir, "bin", "spike")
    check_file_exists(spike_binary)
    info("Checking that Spike runs")
    run_cmd([spike_binary, "--help"], display_stderr=False)


def main():
    args = parse_args()

    # use absolute paths
    args.src_dir = os.path.abspath(args.src_dir)
    args.install_dir = os.path.abspath(args.install_dir)

    print_spike_rev(args.src_dir)
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
