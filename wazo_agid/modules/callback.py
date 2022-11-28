# Copyright 2006-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import pwd
import time
from wazo_agid import agid

ASTERISK_UID = None
ASTERISK_GID = None


def callback(agi, cursor, args):
    context = args[0]
    srcnum = agi.get_variable('XIVO_SRCNUM')
    spooldir = agi.get_variable('AST_CONFIG(asterisk.conf,directories,astspooldir)')

    if srcnum in (None, ''):
        agi.dp_break(f"Unable to find srcnum, srcnum = {srcnum!r}")

    if not spooldir:
        agi.dp_break("Unable to fetch AST_SPOOL_DIR")

    mtime = time.time() + 5
    filepath = f"{spooldir}/{{subdir}}/{srcnum}-{int(mtime)}.call"

    tmpfile = filepath.format(subdir="tmp")
    realfile = filepath.format(subdir="outgoing")

    f = open(tmpfile, 'w')
    f.write("Channel: Local/{}@{}\n"
            "MaxRetries: 0\n"
            "RetryTime: 30\n"
            "WaitTime: 30\n"
            "CallerID: {}\n"
            "Set: XIVO_DISACONTEXT={}\n"
            "Context: xivo-callbackdisa\n"
            "Extension: s".format(srcnum, context, srcnum, context))
    f.close()

    os.utime(tmpfile, (mtime, mtime))
    os.chown(tmpfile, ASTERISK_UID, ASTERISK_GID)
    os.rename(tmpfile, realfile)


def setup_callback(cursor):
    global ASTERISK_UID, ASTERISK_GID
    ASTERISK_UID, ASTERISK_GID = _get_uid_gid("asterisk")


def _get_uid_gid(name):
    pw_name, pw_passwd, pw_uid, pw_gid, pw_gecos, pw_dir, pw_shell = pwd.getpwnam(name)
    return pw_uid, pw_gid


agid.register(callback, setup_callback)
