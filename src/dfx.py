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
    dfx.py -u
    dfx.py -h | --help
    dfx.py --version

Options:
    -t <TYPE>, --type=<TYPE>  Show only items of type. May be "fav", "rfile",
                              "rfolder" or "all" [default: all].
    -u, --update              Update cached data.
    -h, --help                Show this message and exit.
    --version                 Show version number and exit.

"""

from __future__ import print_function, unicode_literals, absolute_import

from collections import namedtuple
import os
from subprocess import check_output
import sys
from time import time

import docopt
from workflow import Workflow3, ICON_WARNING
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


def get_dfx_data():
    """Return DFX favourites and recent items.

    Returns:
        list: Sequence of `DfxEntry` objects.
    """
    st = time()
    script = wf.workflowfile('DFX Files.scpt')
    output = wf.decode(check_output(['/usr/bin/osascript', script]))
    log.debug('DFX files updated in %0.3fs', time() - st)

    entries = []

    home = os.getenv('HOME')
    for line in [s.strip() for s in output.split('\n') if s.strip()]:
        row = line.split('\t')
        if len(row) != 2:
            log.warning('Invalid output from DFX : %r', line)
            continue
        typ, path = row
        # Remove trailing slash from path or things go wrong...
        path = path.rstrip('/')
        e = DfxEntry(
            typ,
            path,
            os.path.basename(path),
            path.replace(home, '~'),
        )
        log.debug('entry=%r', e)
        entries.append(e)

    return entries


def do_update():
    """Update cached DFX files and folders."""
    log.info('Updating DFX data...')
    data = get_dfx_data()
    wf.cache_data(DFX_CACHE_KEY, data)


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
    # Parse input
    wf.args
    args = docopt.docopt(__doc__, version=wf.version)
    query = args.get('<query>') or b''
    query = wf.decode(query).strip()
    types = args.get('--type')
    log.debug('args=%r', args)

    # -----------------------------------------------------------------
    # Update cached DFX data

    if args.get('--update'):
        return do_update()

    # -----------------------------------------------------------------
    # Script Filter

    # Load cached entries first and start update if they've
    # expired (or don't exist)
    entries = wf.cached_data(DFX_CACHE_KEY, max_age=0)
    if not entries or not wf.cached_data_fresh(DFX_CACHE_KEY, MAX_CACHE_AGE):
        if not is_running('update'):
            run_in_background(
                'update',
                ['/usr/bin/python', wf.workflowfile('dfx.py'), '--update']
            )

    # Tell Alfred to re-run the Script Filter if cache is being updated
    if is_running('update'):
        wf.rerun = 1

    # No data in cache yet. Show warning and exit.
    if entries is None:
        wf.add_item('Waiting for Default Folder X data…',
                    'Please try again in a second or two',
                    icon=ICON_WARNING)
        wf.send_feedback()
        return

    # Filter entries
    if types != ['all']:
        log.debug('Filtering for types : %r', types)
        entries = [e for e in entries if e.type in types]

    # Remove duplicates and non-existent files
    entries = [e for e in set(entries) if os.path.exists(e.path)]

    # Filter data against query if there is one
    if query:
        total = len(entries)
        entries = wf.filter(query, entries, lambda e: e.name, min_score=30)
        log.info('%d/%d entries match `%s`', len(entries), total, query)

    # Prepare Alfred results
    if not entries:
        wf.add_item(
            'Nothing found',
            'Try a different query?',
            icon=ICON_WARNING)

    for e in entries:

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

    wf.send_feedback()

    return 0


if __name__ == '__main__':
    wf = Workflow3(
        default_settings=DEFAULT_SETTINGS,
        update_settings=UPDATE_SETTINGS,
        help_url=HELP_URL,
    )
    log = wf.logger
    sys.exit(wf.run(main))
