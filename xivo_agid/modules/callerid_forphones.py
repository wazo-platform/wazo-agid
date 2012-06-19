# -*- coding: UTF-8 -*-

__license__ = """
    Copyright (C) 2012  Avencall

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

import logging
from xivo_agid import agid

logger = logging.getLogger(__name__)


def callerid_forphones(agi, cursor, args):
    logger.warning('callerid_forphones not yet implemented -- doing nothing')


agid.register(callerid_forphones)
