#!/usr/bin/python

from __future__ import print_function

# standard library imports
import os
import sys
import re
import glob
import argparse
import datetime
import subprocess
import random

# third party imports

# application/library imports

# TODO: add include switch that copies in plots


CLI = argparse.ArgumentParser(
    description="Compare collections of websync items side by side",
)

CLI.add_argument(
    "plot_collection",
    nargs="+",
    help="Collection of plots as a glob or containing directory.",
)
CLI.add_argument(
    "-v",
    "--verbosity",
    action="count",
    help="Verbosity level. [Default: %s/2]"
)

selection = CLI.add_argument_group("Selection")
selection.add_argument(
    "-b",
    "--blacklist",
    nargs="*",
    help="regexp(s) for files to ignore. [Default: %(default)s]",
    default=["\.html", "\.json"],
)
selection.add_argument(
    "-w",
    "--whitelist",
    nargs="*",
    help="regexp(s) for files to include. [Default: %(default)s]",
    default=[""],
)
selection.add_argument(
    "--ignore-less",
    type=int,
    help="Ignore plots which are not in at least this many collections. [Default: %(default)s]",
    default=1,
)

formatting = CLI.add_argument_group("Formatting")
formatting.add_argument(
    "--headers",
    nargs="*",
    default=False,
    help="Add headers describing collections to each row. "
         "Explicit names for each row may be given as a list."
)

output = CLI.add_argument_group("Output")
output.add_argument(
    "--target-dir",
    help="Dirname to store the resulting output in. [Default: %(default)s]",
    default=os.path.join("websync", datetime.date.today().strftime("%Y_%m_%d"))
)
output.add_argument(
    "--target-name",
    help="Basename to store the resulting output in. [Default: %(default)s]",
    default=datetime.datetime.now().strftime("comparison_%H%M%S.html"),
)
# use HarryPlotter remote settings if possible
try:
    sync_target = \
        ((os.environ["HARRY_REMOTE_USER"] + "@") if "HARRY_REMOTE_USER" in os.environ else "") +\
        os.environ["HARRY_SSHPC"] + ":" +\
        os.environ["HARRY_REMOTE_PATH"] + os.sep + os.environ["HARRY_REMOTE_DIR"]
    harry_sync = True
except KeyError:
    sync_target = None
    harry_sync = False

output.add_argument(
    "--sync",
    nargs="?",
    default=None,
    const=sync_target,
    help="Sync output to a (remote) directory." +\
    " Target defaults to the HarryPlotter www directory." if harry_sync else "",
)


def vprint(level, *items):
    if level <= _v_level:
        print(*items, file=sys.stderr)
_v_level = 0


def get_collection(collection_str, blacklist=(), whitelist=("",)):
    """
    Get dirname and basename for all items that match ``collection_str``

    :param collection_str: a glob or directory containing the items
    :type collection_str: str
    :param blacklist: regexp for items to ignore
    :type blacklist: list[str]
    :param whitelist: regexp for items to use
    :type whitelist: list[str]
    :return: dirname and basename of valid items
    :rtype: list[list[str]]
    """
    if os.path.isdir(collection_str):
        collection_str = os.path.join(collection_str, "*")
    return [
        [os.path.dirname(item), os.path.basename(item)]
        for item in glob.glob(collection_str)
        if
        any(re.search(pattern, item) for pattern in whitelist)
        and
        not any(re.search(pattern, item) for pattern in blacklist)
        and
        os.path.isfile(item)
    ]


def resolve_paths(target_path, collections):
    """
    Transform item paths to relative paths

    :param target_path: path from which items will be referenced
    :param collections: collections of items to referr to
    :type collections: list[list[list[str]]]
    :return: collections with item path expressed relatively
    :rtype collections: list[list[list[str]]]
    """
    for collection in collections:
        for item in collection:
            item[0] = os.path.relpath(
                item[0],
                target_path
            )
    return collections


def compile_comparison(collections, min_count=1):
    """
    Compile a comparison table for all items in given collections

    :param collections: collections of items as (dirname, basename)
    :param min_count: filter for minimum number of colelctions an item must be in
    :return: items sorted into rows for a table
    :rtype: list[list[list[str]]]
    """
    comparison_rows = []
    # order in reverse since list pops from the back
    collections = [sorted(collection, reverse=True, key=lambda item: item[1]) for collection in collections]
    current_items = [None]*len(collections)
    while any(any(collection) for collection in collections):
        # advance any empty == consumed item to the next in its owning list
        for ci_idx in xrange(len(current_items)):
            if current_items[ci_idx] is None:
                try:
                    current_items[ci_idx] = collections[ci_idx].pop()
                except IndexError:
                    current_items[ci_idx] = None
        # extract all items that match the lexicographically next one
        this_row = []
        current_base = min(item[1] for item in current_items if item is not None)
        current_count = 0
        for ci_idx in xrange(len(current_items)):
            if current_items[ci_idx] is not None and current_items[ci_idx][1] == current_base:
                this_row.append(current_items[ci_idx])
                current_count += 1
                current_items[ci_idx] = None
                continue
            else:
                this_row.append(None)
        if current_count >= min_count:
            comparison_rows.append(this_row)
    return comparison_rows


def xformat_comparison_to_html(comparison_rows, headers=False):
    """
    Generate HTML formatted comparison

    :param comparison_rows:
    :param headers:
    :return:
    """
    yield '<!DOCTYPE html>'
    yield '<html>'
    yield '<head>'
    yield '<style type="text/css">'
    yield 'div { float:left; }'
    yield 'pre { display: inline; padding: 3px 7px; font-size: 16px; background-color: #F5F5F5; border: 1px solid rgba(0, 0, 0, 0.15); border-radius: 4px; }'
    yield 'h3 { color: #888; font-size: 16px; }'
    yield '</style>'
    yield '</head>'
    yield '<body>'
    yield '<table>'
    if headers is not False:
        yield "<tr>" + "".join("<th><b>%s</b></th>" % item for item in headers) + "</tr>"
    for row in comparison_rows:
        line = ['<tr>']
        for item in row:
            if item is None:
                line += ['<td>Not Available</td>']
            elif len(item) == 2:
                line += ['<td><h3>%(name)s</h3><a href="%(path)s" title="%(name)s"><img src="%(path)s" height="400"></a></dh>' % {
                    'path': os.path.join(*item),
                    'name': item[1]
                }]
            else:
                raise ValueError(row)
        line += ['</tr>']
        yield "".join(line)
    yield '</table>'
    yield '</body>'
    yield '</html>'


if __name__ == "__main__":
    options = CLI.parse_args()
    _v_level = options.verbosity
    # aggregate dynamic information
    if options.headers is not False:
        options.headers.extend(options.plot_collection[len(options.headers):])
    collections = resolve_paths(
        options.target_dir,
        [
            get_collection(
                collection_str,
                blacklist=options.blacklist,
                whitelist=options.whitelist
            )
            for collection_str in options.plot_collection
        ]
    )
    comparison_table = compile_comparison(collections, min_count=options.ignore_less)
    # output
    if not os.path.exists(options.target_dir):
        os.makedirs(os.path.abspath(options.target_dir))
    with open(os.path.join(options.target_dir, options.target_name), 'w') as outfile:
        for line in xformat_comparison_to_html(comparison_table, options.headers):
            outfile.write(line)
    if options.sync is not None:
        if harry_sync and options.sync == sync_target:
            # when syncing for harry, remove potential websync references
            remote_target = options.sync + os.sep + os.path.relpath(os.path.join(options.target_dir.replace("websync/", "", 1), options.target_name))
        else:
            remote_target = options.sync + os.sep + os.path.relpath(os.path.join(options.target_dir, options.target_name))
        user_host, remote_path = remote_target.split(":")
        # create the directory in case it does not exist
        mkdir_call = ["mkdir", "-p", os.path.dirname(remote_path)]
        if user_host:
            mkdir_call = ["ssh", user_host] + mkdir_call
        vprint(1, "Creating remote directory...")
        vprint(2, "Calling", " ".join(mkdir_call))
        vprint(3, *subprocess.check_output(mkdir_call))
        sync_call = ["rsync", "-au", os.path.join(options.target_dir, options.target_name), remote_target]
        vprint(1, "Syncing to remote directory...")
        vprint(2, "Calling", " ".join(sync_call))
        vprint(3, *subprocess.check_output(sync_call))