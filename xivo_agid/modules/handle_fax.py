# -*- coding: utf-8 -*-

# Copyright (C) 2006-2016 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import logging
import os
import subprocess
import ftplib
from ConfigParser import RawConfigParser
from xivo_agid import agid

logger = logging.getLogger(__name__)

CONFIG_FILE = "/etc/xivo/asterisk/xivo_fax.conf"
TIFF2PDF_PATH = "/usr/bin/tiff2pdf"
MUTT_PATH = "/usr/bin/mutt"
LP_PATH = "/usr/bin/lp"
DESTINATIONS = {}


def _pdffile_from_file(fileobj):
    return fileobj.rsplit(".", 1)[0] + ".pdf"


def _convert_tiff_to_pdf(tifffile, pdffile=None):
    # Convert tifffile to pdffile and return the name of the pdf file.
    if pdffile is None:
        pdffile = _pdffile_from_file(tifffile)
    subprocess.check_call([TIFF2PDF_PATH, "-o", pdffile, tifffile],
                          close_fds=True)
    return pdffile


# A backend is a callable object taking 3 arguments, in this order:
#   faxfile -- the path to the fax file (in TIFF format)
#   dstnum -- the content of the the XIVO_DSTNUM dialplan variable
#   args -- args specific to the backend
def _new_mail_backend(subject, content_file, email_from, email_realname='XiVO Fax'):
    # Return a backend taking one additional argument, an email address,
    # which sends the fax file as a pdf to the given email address when
    # called.
    fobj = open(content_file)
    try:
        content = fobj.read()
    finally:
        fobj.close()

    def aux(faxfile, dstnum, args):
        # args[0] is the email address to send the fax to
        email = args[0]
        if not email:
            raise ValueError("Invalid email value: %s" % email)

        pdffile = _convert_tiff_to_pdf(faxfile)
        try:
            fmt_dict = {"dstnum": dstnum}
            p = subprocess.Popen([MUTT_PATH,
                                 "-e", "set copy=no",
                                 "-e", "set from=%s" % email_from,
                                 "-e", "set realname='%s'" % email_realname,
                                 "-e", "set use_from=yes",
                                 "-s", subject % fmt_dict,
                                 "-a", pdffile, "--",
                                 email],
                                 stdin=subprocess.PIPE,
                                 close_fds=True)
            p.communicate(content % fmt_dict)
            if p.returncode:
                raise Exception("mutt exit code was %s" % p.returncode)
        finally:
            try:
                os.remove(pdffile)
            except OSError, e:
                logger.info("Could not remove pdffile %s: %s", pdffile, e)
    return aux


def _new_printer_backend(name=None, convert_to_pdf=None):
    # Return a backend taking no additional argument, which prints the fax
    # to the given printer when called.
    # Note that if name is None, it use the default printer.
    convert_to_pdf = _convert_config_value_to_bool(convert_to_pdf, True, 'convert_to_pdf')

    def aux(faxfile, dstnum, args):
        lp_cmd = [LP_PATH, '-s']
        if name:
            lp_cmd.extend(['-d', name])
        if convert_to_pdf:
            pdffile = _convert_tiff_to_pdf(faxfile)
            lp_cmd.append(pdffile)
        else:
            lp_cmd.append(faxfile)
        try:
            subprocess.check_call(lp_cmd, close_fds=True)
        finally:
            if convert_to_pdf:
                try:
                    os.remove(pdffile)
                except OSError, e:
                    logger.info('Could not remove pdffile %s: %s', pdffile, e)
    return aux


def _convert_config_value_to_bool(config_value, default, param_name):
    if config_value is None:
        return default
    elif config_value == '0':
        return False
    elif config_value == '1':
        return True
    else:
        logger.warning('invalid param %s: %r', param_name, config_value)
        return default


def _new_ftp_backend(host, username, password, port=21, directory=None, convert_to_pdf=None):
    # Return a backend taking no argument, which transfers the fax,
    # in its original format, to the given FTP server when called.
    # Note that a connection is made every time the backend is called.
    convert_to_pdf = _convert_config_value_to_bool(convert_to_pdf, True, 'convert_to_pdf')
    port = int(port)

    def aux(faxfile, dstnum, args):
        if convert_to_pdf:
            filename = _convert_tiff_to_pdf(faxfile)
        else:
            filename = faxfile
        try:
            with open(filename, "rb") as fobj:
                ftp_serv = ftplib.FTP()
                ftp_serv.connect(host, port)
                ftp_serv.login(username, password)
                try:
                    if directory:
                        ftp_serv.cwd(directory)
                    stor_command = "STOR %s" % os.path.basename(filename)
                    ftp_serv.storbinary(stor_command, fobj)
                finally:
                    ftp_serv.close()
        finally:
            if convert_to_pdf:
                try:
                    os.remove(filename)
                except OSError as e:
                    logger.info('Could not remove file %s: %s', filename, e)

    return aux


def _do_handle_fax(faxfile, dstnum, args):
    logger.info('Handling fax for destination %s', dstnum)
    if not faxfile:
        raise ValueError("Invalid faxfile value: %s" % faxfile)
    if not dstnum:
        raise ValueError("Invalid dstnum value: %s" % dstnum)

    if dstnum in DESTINATIONS:
        logger.debug("Using backends for destination %s", dstnum)
        backends = DESTINATIONS[dstnum]
    else:
        if "default" in DESTINATIONS:
            logger.debug("Using backends for destination default")
            backends = DESTINATIONS["default"]
        else:
            raise ValueError("No backends associated with dstnum %s" % dstnum)

    for backend in backends:
        try:
            backend(faxfile, dstnum, args)
        except Exception:
            logger.error("Fax backend %s failed to handle fax", backend, exc_info=True)
            raise

    try:
        os.remove(faxfile)
    except OSError, e:
        logger.info("Could not remove faxfile %s: %s", faxfile, e)


def handle_fax(agi, cursor, args):
    try:
        faxfile = args[0]
        dstnum = agi.get_variable("XIVO_DSTNUM")
        _do_handle_fax(faxfile, dstnum, args[1:])
    except Exception, e:
        agi.dp_break(e)


_BACKENDS_FACTORY = [("mail", _new_mail_backend),
                     ("printer", _new_printer_backend),
                     ("ftp", _new_ftp_backend),
                     ("log", None)]


def setup_handle_fax(cursor):
    # Raise an error if a backend creation failed, etc.
    # 1. read config
    config = RawConfigParser()
    fobj = open(CONFIG_FILE)
    try:
        config.readfp(fobj)
    finally:
        fobj.close()

    # 2. read general section...
    global TIFF2PDF_PATH
    global MUTT_PATH
    global LP_PATH
    if config.has_option("general", "tiff2pdf"):
        TIFF2PDF_PATH = config.get("general", "tiff2pdf")
    if config.has_option("general", "mutt"):
        MUTT_PATH = config.get("general", "mutt")
    if config.has_option("general", "lp"):
        LP_PATH = config.get("general", "lp")

    # 3. create backends
    backends = {}
    for backend_prefix, backend_factory in _BACKENDS_FACTORY:
        for section in filter(lambda s: s.startswith(backend_prefix),
                              config.sections()):
            if backend_factory is None:
                logger.warning('Backends of type %s are not supported anymore: remove the backend %s from your xivo_fax.conf',
                               backend_prefix, section)
                continue
            backend_factory_args = dict(config.items(section))
            logger.debug("Creating backend, name %s, factory %s", section,
                         backend_factory)
            backends[section] = backend_factory(**backend_factory_args)
    logger.debug("Created %s backends", len(backends))

    # 4. creation destinations
    global DESTINATIONS
    DESTINATIONS = {}
    for section in filter(lambda s: s.startswith("dstnum_"), config.sections()):
        cur_destination = section[7:]  # 6 == len("dstnum_")
        cur_backend_ids = map(lambda s: s.strip(), config.get(section, "dest").split(","))
        cur_backends = map(lambda id_: backends[id_], cur_backend_ids)
        logger.debug('Creating destination, dstnum %s, backends %s', cur_destination,
                     cur_backend_ids)
        DESTINATIONS[cur_destination] = cur_backends
    logger.debug("Created %s destinations", len(DESTINATIONS))


agid.register(handle_fax, setup_handle_fax)
