# -*- coding: UTF-8 -*-

__license__ = """
    Copyright (C) 2011  Avencall

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import json
import logging
import urllib2
from xivo_agid import agid

logger = logging.getLogger(__name__)

AUTOPROV_URL = 'http://localhost/xivo/configuration/json.php/private/provisioning/autoprov?act=configure'
HEADERS = {'Content-Type': 'application/json'}
TIMEOUT = 10


def _do_provision(provcode, ip):
    data = json.dumps({'code': provcode, 'ip': ip})
    request = urllib2.Request(AUTOPROV_URL, data, HEADERS)
    f = urllib2.urlopen(request, timeout=TIMEOUT)
    try:
        f.read()
    finally:
        f.close()


def provision(agi, cursor, args):
    try:
        provcode = args[0]
        ip = args[1]
        _do_provision(provcode, ip)
    except Exception, e:
        logger.error('Error during provisioning: %s', e)
    else:
        agi.set_variable('XIVO_PROV_OK', '1')


agid.register(provision)
