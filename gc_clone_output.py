#!/usr/bin/python
"""
**Clones the output from a GC job to another location**

This application is an event hook for grid-control, cloning job output to other
locations or remote sites. The app must be called from grid-control as a hook::

  [job]
  monitor = scripts

  [events]
  silent = False
  on output = gc_clone_output.py analysis_host:/remote/skim/storage

Additional options may be set by appending them to the ``on output`` call. For
example, if a job writes to a site's dCache which is locally mounted on the
submit host, ``--source-storage /pnfs/foo/bar`` can often be used to access the
files without grid tools.

:note: Most transfer protocols require the remote directory to exist. There is
       currently no way have the app create the remote directory implicitly.

**Arguments**

.. argparse::
   :ref: gc_clone_output.CLI
   :prog: gc_clone_output
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
    default=["rsync", "-aPRp"],
)


if __name__ == "__main__":
    args = CLI.parse_args()
    # read job meta information
    gc_job_meta = gc_tools.gc_job.GCJobMeta(os.environ["GC_WORKDIR"], os.environ["GC_MY_JOBID"])
    if gc_job_meta.exitcode != 0:
        if args.verbose:
            print "Ignoring failed Job", gc_job_meta.job_id
        sys.exit(0)
    # joining with '.' to file name allows rsync to create containing directories
    source_path = os.path.join(
        (args.source_storage or gc_job_meta.environ["SE_OUTPUT_PATH"]),
        '.',
        (args.file_names or gc_job_meta.environ["SE_OUTPUT_PATTERN"])
    )
    dest_path = os.path.join(
        args.dest_storage,
        (args.file_names or gc_job_meta.environ["SE_OUTPUT_PATTERN"])
    )
    # clone
    output = "<no output>"
    if args.verbose:
        print "Job", gc_job_meta.job_id, ":", " ".join(args.copy_via + [source_path, dest_path])
    try:
        output = subprocess.check_output(args.copy_via + [source_path, dest_path])
    except subprocess.CalledProcessError:
        print(output)
        sys.exit(1)
