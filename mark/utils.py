from collections import defaultdict

import sqlparse

from blessings import Terminal
t = Terminal()

from mark.template import makeEnvironment, parseVariables
from mark.errors import QueryError

def _escapeSplit(sep, argstr):
    """
    Allows for escaping of the separator: e.g. task:arg='foo\, bar'

    It should be noted that the way bash et. al. do command line parsing, those
    single quotes are required.

    (copied from fabric/main.py)
    """
    escaped_sep = r'\%s' % sep

    if escaped_sep not in argstr:
        return argstr.split(sep)

    before, _, after = argstr.partition(escaped_sep)
    startlist = before.split(sep)  # a regular split is fine here
    unfinished = startlist[-1]
    startlist = startlist[:-1]

    # recurse because there may be more escaped separators
    endlist = _escapeSplit(sep, after)

    # finish building the escaped value. we use endlist[0] becaue the first
    # part of the string sent in recursion is the rest of the escaped value.
    unfinished += sep + endlist[0]

    return startlist + [unfinished] + endlist[1:]  # put together all the parts

def parseArgumentCall(call):
    """
    Parse string list into list of tuples: task_name, args, kwargs

    (modified from fabric/main.py)
    """
    args = []
    kwargs = {}
    if ':' in call:
        call, argstr = call.split(':', 1)
        for pair in _escapeSplit(',', argstr):
            result = _escapeSplit('=', pair)
            if len(result) > 1:
                k, v = result
                kwargs[k] = v
            else:
                args.append(result[0])
    return call, args, kwargs

def pad(string, padding, align="<"):
    return ("{:" + str(align) + str(padding) + "}").format(string)


