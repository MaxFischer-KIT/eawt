
# standard library imports
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