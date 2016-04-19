#!/usr/bin/python
# encoding: utf-8
#
# Copyright (c) 2016 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2016-03-24
#

"""
Update cache of Default Folder X files and folders.
"""

from __future__ import print_function, unicode_literals, absolute_import

import os
import subprocess
import sys
from time import time

from workflow import Workflow
from workflow.notify import notify

from dfx import DfxEntry, DFX_CACHE_KEY

log = None


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


def main(wf):
    """Update cached DFX files and folders.

    Args:
        wf (workflow.Workflow): Active `Workflow` object.
    """
    start = time()
    log.info('Updating DFX data...')
    notify('Updating DFX data…',
           "This won't take a second.")
    data = get_dfx_data()
    wf.cache_data(DFX_CACHE_KEY, data)
    elapsed = time() - start
    log.info('DFX data updated in %0.3f seconds.', elapsed)


if __name__ == '__main__':
    wf = Workflow()
    log = wf.logger
    sys.exit(wf.run(main))
