#!/usr/bin/python

from __future__ import print_function

# standard library imports
import os
import sys
import argparse
import shutil
import subprocess

# third party imports
import sphinx

# application/library imports

CLI = argparse.ArgumentParser(
    description="Build the sphinx documentation"
)
CLI.add_argument(
    "-t",
    "--target",
    nargs="*",
    help="Documentations to build [%(default)s]",
    default=("html", "man"),
    choices=["html", "man"],
)
CLI.add_argument(
    "-c",
    "--clean",
    help="Clear temporary/cached files",
    action="store_true",
)
CLI.add_argument(
    "-v",
    "--verbosity",
    action="count",
    default=0,
    help="Verbosity level [%(default)s/2]",
)


options = CLI.parse_args()
def report(level, message, *args):
    if options.verbosity >= level:
        print(message % args, file=sys.stderr)

def report_file(level):
    if options.verbosity >= level:
        return sys.stderr
    return open("/dev/null")

if __name__ == "__main__":
    options = CLI.parse_args()
    if options.clean:
        report(1, "Cleaning old ApiDoc...")
        shutil.rmtree(os.path.join(os.path.dirname(os.path.realpath(__file__)), "api"))
        report(1, "Cleaning old build...")
        shutil.rmtree(os.path.join(os.path.dirname(os.path.realpath(__file__)), "_build"))
    report(1, "Building ApiDoc...")
    if sphinx.version_info >= (1,3):
        print(subprocess.check_output(["sphinx-apidoc", "-M", "-e", "-o", "api", ".."]), file=report_file(2))
    else:
        print(subprocess.check_output(["sphinx-apidoc", "-o", "api", ".."]), file=report_file(2))
    report(1, "Building HTML...")
    print(subprocess.check_output(["make", "html"]), file=report_file(2))