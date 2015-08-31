
# standard library imports
import os
import shutil
import collections

# third party imports

# application/library imports

# TODO: Add FlatList class


def flatten(*args):
    """Returns a flat list, resolving **any** non-string, non-mapping iterable"""
    if isinstance(args, basestring):
        return [ args ]
    retList = []
    for thing in args:
        try:
            # ignore non-sequence-ish containers
            if isinstance(thing, (collections.Mapping, basestring)):
                raise TypeError
            retList.extend(flatten(*thing))
        except TypeError:
            retList.append(thing)
    return retList


def ensure_rm(path):
    """Ensure that a path does not exist"""
    if os.path.isfile(path) or os.path.islink(path):
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
