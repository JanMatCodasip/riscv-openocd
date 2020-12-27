from contextlib import contextmanager
from datetime import timedelta
from logging import info
import os
import shutil
import subprocess
import sys
import time


def info_box(msg):
    box = " +==" + ("=" * len(msg)) + "==+"
    info("")
    info(box)
    info(" |  " + msg + "  |")
    info(box)
    info("")


@contextmanager
def _stdout_manager(display_stdout=False, stdout_to_file=None, stdout_capture=False):
    assert sum([bool(display_stdout), bool(stdout_to_file), bool(stdout_capture)]) <= 1, \
        "Can't direct stdout to multiple places at the same time"
    f = None
    try:
        if display_stdout:
            # inherit stdout from parent
            yield None
        elif stdout_to_file:
            # log stdout to file
            f = open(stdout_to_file, "w")
            yield f
        elif stdout_capture:
            # capture stdout for further processing
            yield subprocess.PIPE
        else:
            # drop stdout
            yield subprocess.DEVNULL
    finally:
        if f:
            f.close()


def run_cmd(args, cwd=None, timeout=None, display_stdout=True, stdout_to_file=None,
            stdout_capture=False, suppress_info=False, display_stderr=True):
    from subprocess import check_call
    if cwd is None:
        cwd = os.getcwd()
    with _stdout_manager(display_stdout=display_stdout,
                         stdout_to_file=stdout_to_file,
                         stdout_capture=stdout_capture) as stdout:

        if not suppress_info:
            info("Running cmd: {}".format(args))
            info("  cwd: {}".format(cwd))
            if stdout_to_file:
                info("  log file: {}".format(stdout_to_file))
        return subprocess.run(args, check=True, cwd=cwd, stdout=stdout,
                              stderr=None if display_stderr else subprocess.DEVNULL,
                              timeout=timeout, encoding="utf-8")


def git_apply_patch(patch_file, target_dir):
    check_file_exists(patch_file)
    check_dir_exists(target_dir)
    patch_file = os.path.abspath(patch_file)
    with ChangeWorkdir(target_dir):
        run_cmd(["git", "apply", patch_file])


def require_python_ver(major, minor, patch):
    if sys.version_info < (major, minor, patch):
        raise RuntimeError("Python {}.{}.{} or newer is required.".format(major, minor, patch))


def require_module(mod_name, hint=None):
    import importlib
    try:
        importlib.import_module(mod_name)
    except ImportError:
        msg = "Python module '{}' is required.".format(mod_name)
        if hint:
            msg += " Hint: " + hint
        raise RuntimeError(msg)


def require_in_path(tool_name):
    if shutil.which(tool_name) is None:
        raise RuntimeError("Did not find '{}' in your system PATH.".format(tool_name))


def git_revision_info(repo_dir):
    def _git_show(format):
        proc = run_cmd(["git", "show", "-s", "--format=" + format], display_stdout=False, stdout_capture=True)
        return proc.stdout.strip()

    check_dir_exists(repo_dir)
    with ChangeWorkdir(repo_dir):
        return {
            "hash": _git_show("%H"),
            "subject": _git_show("%s"),
            "author": _git_show("%an"),
            "author_date": _git_show("%ai"),
            "commit_date": _git_show("%ci")
        }


def check_file_exists(f):
    if not os.path.exists(f):
        raise RuntimeError("File does not exist: {}".format(f))
    if not os.path.isfile(f):
        raise RuntimeError("Not a file: {}".format(f))


def check_dir_exists(d):
    if not os.path.exists(d):
        raise RuntimeError("Directory does not exist: {}".format(f))
    if not os.path.isdir(d):
        raise RuntimeError("Not a directory: {}".format(f))


class MeasureTime(object):
    def __init__(self, description):
        self.description = description

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        # print the duration into the log
        duration_secs = time.time() - self.start
        duration_secs = int(duration_secs)  # drop usec
        result = "completed" if exc_type is None else "FAILED"
        delta = timedelta(seconds=duration_secs)
        info("{} {}, duration: {}".format(self.description, result, delta))


@contextmanager
def ChangeWorkdir(path):
    old_wd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_wd)
