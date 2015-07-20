#!/usr/bin/python
import argparse
import os
import subprocess
import sys

CLI = argparse.ArgumentParser(
    description="Transfer and clone output from a grid-control job as part of "
                "the script hook pipeline.",
    epilog="This script should be called on the submission machine by "
           "grid-control as a hook and is then executed within the "
           "environment of the grid-control process."
)
CLI.add_argument(
    "source_storage",
    help="base path of data storage",
)
CLI.add_argument(
    "dest_storage",
    help="base path of data destination",
)
CLI.add_argument(
    "--verbose",
    action="store_true",
    help="output non-critical runtime information",
)
CLI.add_argument(
    "--copy-via",
    nargs=argparse.REMAINDER,
    help="command(s) to use for copying. Default: %(default)s",
    default=["rsync", "-aPp"],
)

def resolve_transfer(source_storage, dest_storage):
    output_name = os.environ["GC_SE_OUTPUT_PATTERN"]
    return [source_storage + "/" + output_name, dest_storage + "/" + output_name]

if __name__ == "__main__":
    args = CLI.parse_args()
    output = "<no output>"
    try:
        #output = subprocess.check_output(args.copy_via+resolve_transfer(args.source_storage, args.dest_storage))
        print args.copy_via+resolve_transfer(args.source_storage, args.dest_storage)
    except subprocess.CalledProcessError:
        print(output)
        sys.exit(1)
    else:
        if args.verbose:
            print("Cloned output for Job", os.environ.get("GC_MY_JOBID", "<unknown>"))
