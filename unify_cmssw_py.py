#!/usr/bin/python
import os
import errno
import shutil
import argparse
import cPickle as pickle

def write_unification(root, **kwargs):
    """
    Write down the meta-data of a unification

    :param root: target directory below which packages are mounted
    :type root: str
    :param **kwargs: any arguments as received by :py:func:`unify`
    :return:
    """
    if not os.path.exists(os.path.dirname(root)):
        os.makedirs(os.path.dirname(root))
    unity_path = os.path.join(root, ".cmssw_py.uni")
    try:
        unity_file = os.fdopen(
            os.open(unity_path, os.O_CREAT|os.O_EXCL|os.O_WRONLY),
            'w'
        )
    except OSError as err:
        if err.errno == errno.EEXIST:
            raise ValueError("Directory already hosts a unification ('%s')"%unity_path)
        raise
    else:
        kwargs["root"] = root
        unity_file.write(pickle.dumps(kwargs))


def make_init(init_path, dry_run=False):
    """
    Safely create an ``__init__.py`` file

    :param init_path: expected dirname and basename of the file
    :type init_path: str
    :return:
    """
    if dry_run:
        if not os.path.exists(init_path):
            print "touch", init_path
        return True
    try:
        init_file = os.fdopen(os.open(init_path, os.O_CREAT|os.O_EXCL|os.O_WRONLY), 'w')
    except OSError as err:
        if err.errno == errno.EEXIST:
            return False
        raise
    else:
        print "touch", init_path
        init_file.write("# generated #")
        init_file.flush()
        return True


def _link_package_py(root_path, target_path, source_path, dry_run=False):
    _include_package_py(root_path, target_path, source_path, dry_run=dry_run, include_func=os.symlink, include_str="ln -s")

def _copy_package_py(root_path, target_path, source_path, dry_run=False):
    _include_package_py(root_path, target_path, source_path, dry_run=dry_run, include_func=shutil.copytree, include_str="cp -r")

def _include_package_py(root_path, target_path, source_path, dry_run=False, include_func=None, include_str=None):
    if not os.path.isdir(os.path.dirname(target_path)):
        if not dry_run:
            os.makedirs(os.path.dirname(target_path))
        print "mkdir -p", os.path.dirname(target_path)
    print "%s %s %s" % (include_str, source_path, target_path)
    if not dry_run:
        include_func(source_path, target_path)
    for link_dir, link_subs, link_files in os.walk(source_path):
        make_init(os.path.join(link_dir, "__init__.py"), dry_run=dry_run)

    rel_target_dirs = os.path.relpath(target_path, root_path).split(os.sep)
    for real_dir in [os.path.join(root_path, *rel_target_dirs[:idx+1]) for idx in range(len(rel_target_dirs))]:
        make_init(os.path.join(real_dir, "__init__.py"), dry_run=dry_run)


def unify(root, cmssw_dir=None, collection_paths=(), copy=False, dry_run=False):
    """
    Create a unified directory structure from CMSSW python paths

    :param root: target directory below which to mount packages
    :type root: str
    :param cmssw_dir: a CMSSW directory from which to fetch packages - UNSUPPORTED
    :type cmssw_dir: str
    :param collection_paths: individual collections to add
    :type collection_paths: list[str]
    :param copy: copy in collections instead of linking to them
    :type copy: bool
    :return:
    """
    print "Creating", root
    print "Linking", collection_paths
    if not dry_run:
        write_unification(root=root, collection_paths=collection_paths)
    if isinstance(collection_paths, basestring):
        raise ValueError
    if not collection_paths:
        raise ValueError
    for collection_path in collection_paths:
        collection_path = collection_path.rstrip(os.sep)
        for dirpath, dirnames, filenames in os.walk(collection_path):
            if os.path.basename(dirpath) == "python":
                relative_path = os.path.relpath(os.path.dirname(dirpath), os.path.dirname(collection_path))
                if copy:
                    _copy_package_py(root, os.path.join(root, *relative_path.split(os.sep)), dirpath, dry_run=dry_run)
                else:
                    _link_package_py(root, os.path.join(root, *relative_path.split(os.sep)), dirpath, dry_run=dry_run)
                # already linked, do not decend further
                del dirnames[:]
                continue
            # ignore all magic directories
            dirnames[:] = [dirname for dirname in dirnames if not dirname.startswith(".")]


def disolve(root, cmssw_dir=None, collection_paths=(), copy=False, dry_run=False):
    """
    Tear down a unified directory structure

    :param root:
    :param cmssw_dir:
    :param collection_paths:
    :param copy:
    :param dry_run:
    :return:
    """
    raise NotImplementedError


CLI = argparse.ArgumentParser(
    description="Merge python code from multiple CMSSW like source directories"
                " into a single tree."
)
CLI.add_argument(
    "--root",
    help="The directory beneath which to mount all packages",
    default=".",
    )
CLI.add_argument(
    "--packages",
    nargs="*",
    help="List of root directories for CMSSW python packages",
    default=[],
    )
CLI.add_argument(
    "--add-in",
    nargs="*",
    help="List of additional directories to link into TARGET",
    default=[],
    )
CLI.add_argument(
    "-c",
    "--copy",
    help="Create copies instead of linking originals",
    action="store_true"
)
CLI.add_argument(
    "-u",
    "--unlink",
    help="Unlink a previous unification",
    action="store_true"
)
CLI.add_argument(
    "-d",
    "--dry-run",
    action="store_true",
    help="Do not actually delete anything, just report",
)


if __name__ == "__main__":
    args = CLI.parse_args()
    unify(root=args.root, collection_paths=args.packages, copy=args.copy, dry_run=args.dry_run)