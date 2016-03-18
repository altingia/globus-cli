from __future__ import print_function

import sys
import os
import errno

from globus_cli.parser.shared_parser import GlobusCLISharedParser
from globus_cli.parser.command_tree import build_command_tree


def _gen_parser():
    """
    Produces a top-level argument parser built out of all of the various
    subparsers for different services.
    """
    # create the top parser and give it subparsers
    top_level_parser = GlobusCLISharedParser()
    subparsers = top_level_parser.add_subparsers(
        title='Commands',
        parser_class=GlobusCLISharedParser, metavar='')

    build_command_tree(subparsers)

    # return the created parser in all of its glory
    return top_level_parser


def _load_args():
    """
    Load commandline arguments, and do any necessary post-processing.
    """
    parser = _gen_parser()
    args = parser.parse_args()

    return args


def _except_hook(exception_type, exception, traceback,
                 _bound_except_hook=sys.excepthook):
    """
    Abuses bind at defintiion time to capture the old sys.excepthook
    """
    if os.environ.get('GLOBUS_CLI_DEBUGMODE', None):
        _bound_except_hook(exception_type, exception, traceback)
    else:
        print('{}: {}'.format(exception_type.__name__, exception))
sys.excepthook = _except_hook


def run_command():
    """
    Whatever arguments were loaded, they set a function to be invoked on the
    arguments themselves -- somewhat circular, but a nifty way of passing the
    args to a function that this module doesn't even know about
    """
    args = _load_args()
    try:
        args.func(args)
    except IOError as e:
        # handle a broken pipe by doing nothing
        # this is normal, and often shows up in piped commands when the
        # consumer closes before the producer
        if e.errno is errno.EPIPE:
            pass
        else:
            raise
