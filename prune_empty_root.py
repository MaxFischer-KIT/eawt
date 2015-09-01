#!/usr/bin/python
"""
**Remove empty root files from folders**

Inspects files for content, looking for any that do not contain events.

**Requires**

:py:mod:`argparse`
:py:mod:`ROOT`

**Arguments**

.. argparse::
   :ref: gc_clone_output.CLI
   :prog: gc_clone_output
"""
# standard library imports
import argparse
import glob
import itertools
import os
try:
    import ROOT
    # suppress ROOT output
    ROOT.PyConfig.IgnoreCommandLineOptions = True
    ROOT.gErrorIgnoreLevel = ROOT.kError
except ImportError:
    ROOT = None

# third party imports

# application/library imports
from utility.formatting import Progress

def _file_has_events(file_path, branch_name):
    try:
        data = ROOT.TFile(file_path)
        return data.Get(branch_name).GetEntries() > 0
    except AttributeError:
        # some data structure is missing
        return False

CLI = argparse.ArgumentParser(
    description="Remove empty ROOT files",
    epilog="This scripts inspects files by opening them and checking whether\n"
           "the Branch BRANCH_NAME has any entries."
)
CLI.add_argument(
    "files",
    nargs="*",
    help="Files to check"
)
CLI.add_argument(
    "--branch-name",
    default="Events",
    help="Branch name inside the files containing relevant content",
)
CLI.add_argument(
    "-p",
    "--progress",
    action="store_true",
    help="Display a progress bar",
)
CLI.add_argument(
    "-d",
    "--dry-run",
    action="store_true",
    help="Do not actually delete anything, just report",
)

if __name__ == "__main__":
    if ROOT is None:
        raise ImportError("Module ROOT is not available")
    args = CLI.parse_args()
    progress = Progress(maximum=len(list(itertools.chain(*(glob.glob(cand) for cand in args.files))))) if args.progress else None
    for file_path in itertools.chain(*(glob.glob(cand) for cand in args.files)):
        if not _file_has_events(file_path, args.branch_name):
            print "rm", file_path
            if not args.dry_run:
                os.unlink(file_path)
        if progress is not None:
            progress.step()
