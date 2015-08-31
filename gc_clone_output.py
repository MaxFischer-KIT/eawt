#!/usr/bin/python
"""
Clone the output from a GC job to another location


"""
# standard library imports
import argparse
import os
import subprocess
import sys

# third party imports

# application/library imports
import py_compat
import gc_tools.gc_job

CLI = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="Transfer and clone output from a grid-control job as part of\n"
                "the script hook pipeline.",
    epilog="This script should be called on the submission machine by GC\n"
           "as a hook and is then executed within the environment of the\n"
           "GC process. A job output directory is required to extract job\n"
           "variables and status.\n"
           "\n"
           "The following GC environment variables are used:\n"
           "GC_WORKDIR - working directory\n"
           "GC_MY_JOBID - job number\n"
)
CLI.add_argument(
    "dest_storage",
    help="base path of data destination",
)
CLI.add_argument(
    "--source-storage",
    nargs="?",
    help="overwrite base path of data storage. [<GC Job: $SE_OUTPUT_PATH>]",
)
CLI.add_argument(
    "--file-names",
    nargs="?",
    help="overwrite base path of data storage. [<GC Job: $SE_OUTPUT_PATTERN>]",
)
CLI.add_argument(
    "-v",
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
    gc_env = gc_tools.gc_job.GCJobMeta(os.environ["GC_WORKDIR"], os.environ["GC_MY_JOBID"])
    if gc_env.exitcode != 0:
        if args.verbose:
            print "Ignoring failed Job", os.environ.get("GC_MY_JOBID", "<unknown>")
        sys.exit(0)
    source_path = os.path.join(
        (args.source_storage or gc_env.environ["SE_OUTPUT_PATH"]),
        (args.file_names or gc_env.environ["SE_OUTPUT_PATTERN"])
    )
    dest_path = os.path.join(
        args.dest_storage,
        (args.file_names or gc_env.environ["SE_OUTPUT_PATTERN"])
    )
    try:
        output = subprocess.check_output(args.copy_via + [source_path, dest_path])
    except subprocess.CalledProcessError:
        print(output)
        sys.exit(1)
    else:
        if args.verbose:
            print "Cloned output for Job", os.environ.get("GC_MY_JOBID", "<unknown>")
