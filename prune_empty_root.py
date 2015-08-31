#!/usr/bin/python
import argparse
import glob
import itertools
import os
import ROOT
# suppress ROOT output
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gErrorIgnoreLevel = ROOT.kError

def file_has_events(file_path, branch_name):
    try:
        data = ROOT.TFile(file_path)
        return data.Get(branch_name).GetEntries() > 0
    except AttributeError:
        # some data structure is missing
        return False

CLI = argparse.ArgumentParser(
    description="Remove empty ROOT files",
    epilog="This scripts inspects files by opening them and checking whether"
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
    "-d",
    "--dry-run",
    action="store_true",
    help="Do not actually delete anything, just report",
)

if __name__ == "__main__":
    args = CLI.parse_args()
    for file_path in itertools.chain(*(glob.glob(cand) for cand in args.files)):
        if not file_has_events(file_path, args.branch_name):
            print "rm", file_path
            if not args.dry_run:
                os.unlink(file_path)
