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
import os
import subprocess
import sys

import docopt
from workflow import Workflow, ICON_WARNING

log = None

# Initial values for `settings.json`
DEFAULT_SETTINGS = {}

# Auto-update from GitHub releases
UPDATE_SETTINGS = {
    'github_slug': 'deanishe/alfred-default-folder-x',
}

HELP_URL = 'https://github.com/deanishe/alfred-default-folder-x/issues'


# Data model. `type` is one of 'fav', 'rfolder' or 'rfile'
# ("favorite", "recent folder" and "recent file" respectively)
# `name` is the basename of `path` and `pretty_path` is `path` with
# $HOME replaced with ~
DfxEntry = namedtuple('DfxEntry', ['type', 'path', 'name', 'pretty_path'])


#                            oo            dP
#                                          88
# .d8888b. .d8888b. 88d888b. dP 88d888b. d8888P .d8888b.
# Y8ooooo. 88'  `"" 88'  `88 88 88'  `88   88   Y8ooooo.
#       88 88.  ... 88       88 88.  .88   88         88
# `88888P' `88888P' dP       dP 88Y888P'   dP   `88888P'
#                               88
#                               dP

AS_DFX_FOLDERS = """
(*
Print a list of Default Folder X's favourite and recent
folders and files to STDOUT.

The output is TSV format. Each line has 2 columns: the type of
the path ("fav", "rfolder" or "rfile" for favorites, recent folders
and recent files respectively), and the absolute path.
*)

-- Return array of DFX folders
-- Each result item is a 2-length array of `type`, `POSIX path`
on dxFolders()
    set thePaths to {}
    tell application "Default Folder X"
        repeat with thePath in GetFavoriteFolders
            set the end of thePaths to {"fav", POSIX path of thePath}
        end repeat
        repeat with thePath in GetRecentFolders
            set the end of thePaths to {"rfolder", POSIX path of thePath}
        end repeat
        repeat with thePath in GetRecentFiles
            set the end of thePaths to {"rfile", POSIX path of thePath}
        end repeat
    end tell
    return thePaths
end dxFolders

-- Retrieve list of DFX's folders and files, and output
-- them to STDOUT as TSV lines.
on run (argv)
    set output to ""
    repeat with theItem in my dxFolders()
        if output is not "" then
            set output to output & linefeed
        end if
        set theLine to (item 1 of theItem) & tab & (item 2 of theItem)
        set output to output & theLine
    end repeat
    return output
end run
"""


# dP                dP
# 88                88
# 88d888b. .d8888b. 88 88d888b. .d8888b. 88d888b. .d8888b.
# 88'  `88 88ooood8 88 88'  `88 88ooood8 88'  `88 Y8ooooo.
# 88    88 88.  ... 88 88.  .88 88.  ... 88             88
# dP    dP `88888P' dP 88Y888P' `88888P' dP       `88888P'
#                      88
#                      dP

def run_as(script, *args):
    """Run an AppleScript and return the output.
    Args:
        script (str): The AppleScript to run.
        *args: Additional arguments to `/usr/bin/osascript`.
    Returns:
        str: The output (on STDOUT) of the executed script.
    """
    cmd = ('/usr/bin/osascript', '-l', 'AppleScript', '-e', script) + args
    return subprocess.check_output(cmd)


def get_dfx_data():
    """Return DFX favourites and recent items.

    Returns:
        list: Sequence of `DfxEntry` objects.
    """
    output = wf.decode(run_as(AS_DFX_FOLDERS))

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


#                            oo            dP
#                                          88
# .d8888b. .d8888b. 88d888b. dP 88d888b. d8888P
# Y8ooooo. 88'  `"" 88'  `88 88 88'  `88   88
#       88 88.  ... 88       88 88.  .88   88
# `88888P' `88888P' dP       dP 88Y888P'   dP
#                               88
#                               dP

def main(wf):
    """Run workflow script."""
    args = docopt.docopt(__doc__, argv=wf.args, version=wf.version)
    query = args.get('<query>')
    types = args.get('--type')
    log.debug('args=%r', args)

    # Get DFX data. Keep in cache for 30 seconds to improve performance
    entries = wf.cached_data('dfx-entries', get_dfx_data, max_age=30)

    # Filter entries by type
    if types != ['all']:
        log.debug('Filtering by types : %r', types)
        entries = [e for e in entries if e.type in types]

    # Filter data against query if there is one
    if query:
        entries = wf.filter(query, entries, lambda e: e.name, min_score=30)

    if not entries:
        wf.add_item(
            'Nothing found',
            'Try a different query?',
            icon=ICON_WARNING)

    for e in entries:
        wf.add_item(
            e.name,
            e.pretty_path,
            arg=e.path,
            uid=e.path,
            copytext=e.path,
            valid=True,
            icon=e.path,
            icontype='fileicon')

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
