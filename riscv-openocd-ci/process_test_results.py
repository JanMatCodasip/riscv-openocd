

import logging
from logging import info
from multiprocessing import cpu_count
import os
import re
import shutil
import sys
from utils.utils import MeasureTime, ChangeWorkdir, run_cmd, info_box, git_apply_patch, git_revision_info, \
    check_file_exists, check_dir_exists

KNOWN_RESULTS = ["pass", "fail", "not_applicable", "exception"]
SUMMARY_FILE = "test_summary.txt"


def parse_args():
    import argparse
    parser = argparse.ArgumentParser("Process logs from riscv-tests/debug")
    parser.add_argument("--log-dir", required=True, help="Directory where logs from RISC-V debug tests are stored")
    parser.add_argument("--output-dir", required=True, help="Directory where put post-processed logs")
    return parser.parse_args()


def process_test_logs(log_dir, output_dir):
    from glob import glob
    check_dir_exists(log_dir)
    os.makedirs(output_dir, exist_ok=True)

    # process log files
    file_pattern = os.path.join(log_dir, "*.log")
    res = []
    for lf in sorted(glob(file_pattern)):
        target, result = process_one_log(lf)
        copy_one_log(lf, result, output_dir)
        res += [(lf, target, result)]

    any_failed = aggregate_results(res)
    return any_failed


def process_one_log(log_file):
    check_file_exists(log_file)
    target = None
    result = None
    for line in open(log_file, "r"):
        target_match = re.match(r"^Target: (\S+)$", line)
        if target_match is not None:
            target = target_match.group(1)
        result_match = re.match(r"^Result: (\S+)$", line)
        if result_match is not None:
            result = result_match.group(1)
            if result not in KNOWN_RESULTS:
                msg = ("Unknown test result '{}' in file {}. Expected one of: {}"
                       .format(result, log_file, KNOWN_RESULTS))
                raise RuntimeError(msg)

    if target is None:
        raise RuntimeError("Could not find target name in log file {}".format(log_file))
    if result is None:
        raise RuntimeError("Could not find test result in log file {}".format(log_file))

    return target, result


def copy_one_log(log_file, result, output_dir):
    # copy the log to an output sub-folder based on the result
    target_dir = os.path.join(output_dir, result)
    os.makedirs(target_dir, exist_ok=True)
    assert os.path.isdir(target_dir)
    shutil.copy2(log_file, target_dir)


def aggregate_results(res):

    outcomes = {
        "Passed tests" : "pass",
        "Not applicable tests": "not_applicable",
        "Failed tests": "fail",
        "Tests ended with exception": "exception",
    }

    for caption, filter in outcomes.items():
        info_box(caption)
        tests_filtered = [lf for lf, _, r in res if r == filter]
        for lf in tests_filtered:
            name = os.path.splitext(os.path.basename(lf))[0]
            info(name)
        if not tests_filtered:
            info("(none)")

    target_names = set([t for (_, t, _) in res])

    info_box("Summary")

    def _print_row(target, total, num_pass, num_na, num_fail, num_exc):
        info("{:<25} {:<10} {:<10} {:<10} {:<10} {:<10}".format(target, total, num_pass, num_na, num_fail, num_exc))

    _print_row("Target", "# tests", "Pass", "Not_appl.", "Fail", "Exception")
    _print_row("-----", "-----", "-----", "-----", "-----", "-----")
    sum_pass = sum_na = sum_fail = sum_exc = 0
    for tn in target_names:
        t_pass = sum([1 for _, t, r in res if t == tn and r == "pass"])
        t_na = sum([1 for _, t, r in res if t == tn and r == "not_applicable"])
        t_fail = sum([1 for _, t, r in res if t == tn and r == "fail"])
        t_exc = sum([1 for _, t, r in res if t == tn and r == "exception"])
        t_sum = sum([1 for _, t, _ in res if t == tn])
        assert t_sum == t_pass + t_na + t_fail + t_exc
        _print_row(tn, t_sum, t_pass, t_na, t_fail, t_exc)
        sum_pass += t_pass
        sum_na += t_na
        sum_fail += t_fail
        sum_exc += t_exc
    assert len(res) == sum_pass + sum_na + sum_fail + sum_exc
    _print_row("-----", "-----", "-----", "-----", "-----", "-----")
    _print_row("All targets:", len(res), sum_pass, sum_na, sum_fail, sum_exc)
    _print_row("-----", "-----", "-----", "-----", "-----", "-----")

    any_failed = (sum_fail + sum_exc) > 0
    return any_failed


def main():
    args = parse_args()

    # use absolute paths
    args.log_dir = os.path.abspath(args.log_dir)
    args.output_dir = os.path.abspath(args.output_dir)

    any_failed = process_test_logs(args.log_dir, args.output_dir)
    return 1 if any_failed else 0


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    sys.exit(main())
