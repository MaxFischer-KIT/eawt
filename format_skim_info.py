#!/usr/bin/python
# standard library imports
"""
Compile information from skims for overviews

:warning: Currently, skims and directories are expected to have a unique 1:1
          relation. This constraint will likely be dropped in the future.

**Arguments**

.. argparse::
   :ref: gc_clone_output.CLI
   :prog: gc_clone_output
"""
try:
    import ROOT
    # suppress ROOT output
    ROOT.PyConfig.IgnoreCommandLineOptions = True
    ROOT.gErrorIgnoreLevel = ROOT.kError
except ImportError:
    ROOT = None
import os
import sys
import glob
import argparse
import socket
import logging
import collections
import itertools
import ast

# third party imports

# application/library imports
from utility.utils import flatten


logger = logging.getLogger()

if ROOT is not None:
    def get_event_count(file_path, branch_name="Events"):
        try:
            data = ROOT.TFile(file_path)
            return data.Get(branch_name).GetEntries()
        except AttributeError:
            # some data structure is missing
            return -1
else:
    def get_event_count(file_path, branch_name="Events"):
        return -1

CLI = argparse.ArgumentParser(
    description="Pretty-Print information on skims",
    epilog="This script will descend into subdirectories of DATAPATH, looking "
           "for any folders containing files matching the glob '*.root'. Each "
           "folder is then considered a skim and information is pulled from "
           "all files in the folder."
)
CLI.add_argument(
    "datapath",
    nargs="*",
    help="Basepath to any skims"
)
CLI.add_argument(
    "-f",
    "--formatter",
    default="raw",
    help="Style to use for output [%(default)s]",
)
CLI.add_argument(
    "-v",
    "--verbosity",
    action="count",
    default=0,
    help="Verbosity level [%(default)s/5]",
)


def formatter_factory(formatter_str):
    for formatter in [RawFormatter, TwikiFormatter]:
        try:
            return formatter.from_raw(formatter_str)
        except SyntaxWarning as err:
            print err
    raise ValueError("Formatter string '%s' does not match '%s'" % (
        formatter_str,
        ",".join(itertools.chain(RawFormatter.formatter_string, TwikiFormatter.formatter_string
    ))))


class BaseFormatter(object):
    formatter_string = []

    @staticmethod
    def _read_args(args_string):
        """Convert an argument string to kwargs"""
        all_args = [key_val.rsplit("=", 1) for key_val in args_string.split(",")]
        if all_args == [['']]:
            return (), {}
        args = [ast.literal_eval(arg[0]) for arg in all_args if len(arg) == 1]
        kwargs = dict((arg[0].strip(), ast.literal_eval(arg[1])) for arg in all_args if len(arg) == 2)
        return args, kwargs

    @classmethod
    def from_raw(cls, formatter_string):
        class_name, _, arg_string = formatter_string.partition("(")
        if class_name in cls.formatter_string:
            args, kwargs = cls._read_args(arg_string.rstrip(")"))
            return cls(*args, **kwargs)
        raise SyntaxWarning


class RawFormatter(BaseFormatter):
    formatter_string = ["raw", "RawOutput"]

    def _print_dir(self, obj, indent=0):
        if isinstance(obj, collections.Mapping):
            for key in obj:
                print "  "*indent, "-", key
                self._print_dir(obj[key], indent=indent+1)
        else:
            print "  "*indent, obj

    def digest(self, skim_info):
        self._print_dir(skim_info)
        print


class TwikiFormatter(BaseFormatter):
    formatter_string = ["twiki", "TwikiFormatter"]
    _undefined_field = "---"

    def __init__(self, compact=False):
        self.compact = compact
        self.table_lines = [("*Type*", "*Dataset (DBS)*", "*Path*", "*Global Tag*", "*Cross-section (pb)*", "*No. Events*", "*Size [B]*")]

    def __del__(self):
        if self.compact:
            for line in self.table_lines:
                print "| %s |" % " | ".join(str(item) for item in line)
        else:
            item_lengths = [max(len(str(item)) for item in column) for column in zip(*self.table_lines)]
            for line in self.table_lines:
                print "| %s |" % " | ".join(str(line[idx]).center(item_lengths[idx]) for idx in xrange(len(line)))

    def _format_path(self, path_dict):
        return (
            r"%PURPLE%EKP:%ENDCOLOR% " + path_dict.get("EKP", self._undefined_field),
            r"%NAVY%NAF:%ENDCOLOR% " + path_dict.get("NAF", self._undefined_field)
        )

    def digest(self, skim_info):
        columns = [
            skim_info.get("type", self._undefined_field),
            skim_info.get("dbs", self._undefined_field),
            self._format_path(skim_info["path"]),
            skim_info.get("globaltag", self._undefined_field),
            skim_info.get("xsection", self._undefined_field),
            skim_info.get("event_count", self._undefined_field),
            skim_info.get("file_size", self._undefined_field),
        ]
        columns = [flatten(column) for column in columns]
        line_count = max(len(column) for column in columns)
        columns = [flatten(column) + ["^"]*(line_count-len(column)) for column in columns]
        self.table_lines.extend(zip(*columns))



def find_skims_dirs(datapath):
    """
    Walk through directories, locating any that contain '*.root' files

    :param datapath: basepath to start search from
    :type datapath: str
    :return: directories containing skims
    :rtype: list[str]
    """
    skim_dirs = []
    for dirpath, _, _ in os.walk(datapath):
        if glob.glob(os.path.join(dirpath, '*.root')):
            logger.log(2, "adding skim dir %s", dirpath)
            skim_dirs.append(dirpath)
    return skim_dirs


def collect_skim_info(skim_dir):
    """
    Collect all information available on a skim from its directory

    :param skim_dir: directory containing the skim files
    :type skim_dir: str
    :return:
    :rtype: dict
    """
    logger.log(2, "collecting information on skim %s", skim_dir)
    skim_info = {
        "path": {
            socket.gethostname()[:3].upper(): skim_dir
        },
        "file_count": len(glob.glob(os.path.join(skim_dir, "*.root"))),
        "file_size": sum(os.path.getsize(filename) for filename in glob.glob(os.path.join(skim_dir, "*.root"))),
        "event_count": sum(get_event_count(filename) for filename in glob.glob(os.path.join(skim_dir, "*.root")))
    }
    return skim_info

if __name__ == "__main__":
    args = CLI.parse_args()
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=5-args.verbosity,
    )
    formatter = formatter_factory(args.formatter)
    for datapath in args.datapath:
        for skim_dir in find_skims_dirs(datapath):
            formatter.digest(collect_skim_info(skim_dir))

