#!/usr/bin/python
# encoding: utf-8
#
# Copyright (c) 2016 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2016-03-22
#

"""dfx.py [-t <type>...] [<query>]

Usage:
    dfx.py [-t <type>...] [<query>]
    dfx.py -h | --help
    dfx.py --version

Options:
    -t <TYPE>, --type=<TYPE>  Show only items of type. May be "fav", "rfile",
                              "rfolder" or "all" [default: all].
    -h, --help                Show this message and exit.
    --version                 Show version number and exit.

"""

from __future__ import print_function, unicode_literals, absolute_import

from collections import namedtuple
import sys

import docopt
from workflow import Workflow, ICON_WARNING
from workflow.background import is_running, run_in_background

log = None

# Initial values for `settings.json`
DEFAULT_SETTINGS = {}

# Auto-update from GitHub releases
UPDATE_SETTINGS = {
    'github_slug': 'deanishe/alfred-default-folder-x',
}

HELP_URL = 'https://github.com/deanishe/alfred-default-folder-x/issues'

# Where data will be cached by `update.py`
DFX_CACHE_KEY = 'dfx-entries'
MAX_CACHE_AGE = 10  # seconds

# Data model. `type` is one of 'fav', 'rfolder' or 'rfile'
# ("favorite", "recent folder" and "recent file" respectively)
# `name` is the basename of `path` and `pretty_path` is `path` with
# $HOME replaced with ~
DfxEntry = namedtuple('DfxEntry', ['type', 'path', 'name', 'pretty_path'])


#                            oo            dP
#                                          88
# .d8888b. .d8888b. 88d888b. dP 88d888b. d8888P
# Y8ooooo. 88'  `"" 88'  `88 88 88'  `88   88
#       88 88.  ... 88       88 88.  .88   88
# `88888P' `88888P' dP       dP 88Y888P'   dP
#                               88
#                               dP

def prefix_name(entry):
    """Prepend a Unicode icon to `entry.name` based on `entry.type`.

    Args:
        entry (DfxEntry): `DfxEntry` or something else with `type`
            and `name` properties.

    Returns:
        unicode: `entry.name` with Unicode icon prefix.
    """
    if entry.type == 'fav':
        prefix = '\U00002764'  # HEAVY BLACK HEART
    else:
        prefix = '\U0001F55E'  # CLOCK FACE THREE-THIRTY

    return '{} {}'.format(prefix, entry.name)


def main(wf):
    """Run workflow script."""
    # Parse input ------------------------------------------------------
    # Call this to ensure magic arguments are parsed
    wf.args
    args = docopt.docopt(__doc__, version=wf.version)
    query = args.get('<query>') or b''
    query = wf.decode(query).strip()
    types = args.get('--type')
    log.debug('args=%r', args)

    # Load data --------------------------------------------------------
    # Load cached entries first and start update if they've
    # expired (or don't exist)
    entries = wf.cached_data(DFX_CACHE_KEY, max_age=0)
    if not entries or not wf.cached_data_fresh(DFX_CACHE_KEY, MAX_CACHE_AGE):
        if not is_running('update'):
            run_in_background(
                'update',
                ['/usr/bin/python', wf.workflowfile('update.py')]
            )

    # No data in cache yet. Show warning and exit.
    if entries is None:
        wf.add_item('Waiting for Default Folder X data…',
                    'Please try again in a second or two',
                    icon=ICON_WARNING)
        wf.send_feedback()
        return

    # Filter entries ---------------------------------------------------
    if types != ['all']:
        log.debug('Filtering for types : %r', types)
        entries = [e for e in entries if e.type in types]

    # Filter data against query if there is one
    if query:
        entries = wf.filter(query, entries, lambda e: e.name, min_score=30)

    # Display results --------------------------------------------------
    if not entries:
        wf.add_item(
            'Nothing found',
            'Try a different query?',
            icon=ICON_WARNING)

    # Don't add duplicate entries for paths in both favourites and recent
    seen = set()
    for e in entries:
        if e.path in seen:
            continue

        if types == ['all']:
            title = prefix_name(e)
        else:
            title = e.name

        wf.add_item(
            title,
            e.pretty_path,
            arg=e.path,
            uid=e.path,
            copytext=e.path,
            largetext=e.path,
            type='file',
            valid=True,
            icon=e.path,
            icontype='fileicon')

        seen.add(e.path)

    wf.send_feedback()

    return 0


if __name__ == '__main__':
    wf = Workflow(
        default_settings=DEFAULT_SETTINGS,
        update_settings=UPDATE_SETTINGS,
        help_url=HELP_URL,
    )
    log = wf.logger
    sys.exit(wf.run(main))
