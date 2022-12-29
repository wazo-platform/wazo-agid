# Copyright 2006-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
import os
import subprocess
import ftplib

from configparser import RawConfigParser
from typing import Callable

from psycopg2.extras import DictCursor

from wazo_agid import agid
from wazo_agid.fastagi import FastAGI

logger = logging.getLogger(__name__)
Backend = Callable[[str, str, list], None]

CONFIG_FILE = "/etc/xivo/asterisk/xivo_fax.conf"
TIFF2PDF_PATH = "/usr/bin/tiff2pdf"
MUTT_PATH = "/usr/bin/mutt"
LP_PATH = "/usr/bin/lp"
DESTINATIONS: dict[str, list[Backend]] = {}


def _pdffile_from_file(file_name: str) -> str:
    return file_name.rsplit(".", 1)[0] + ".pdf"


def _convert_tiff_to_pdf(tiff_file: str, pdf_file: str | None = None) -> str:
    # Convert tiff_file into pdf_file and return the name of the pdf file.
    if pdf_file is None:
        pdf_file = _pdffile_from_file(tiff_file)
    try:
        subprocess.check_output(
            [TIFF2PDF_PATH, "-o", pdf_file, tiff_file],
            close_fds=True,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        logger.error('Command: "%s"', e.cmd)
        logger.error('Command output: "%s"', e.output)
        raise
    return pdf_file


# A backend is a callable object taking 3 arguments, in this order:
#   faxfile -- the path to the fax file (in TIFF format)
#   dstnum -- the content of the XIVO_DSTNUM dialplan variable
#   args -- args specific to the backend
def _new_mail_backend(
    subject: str, content_file: str, email_from: str, email_realname: str = 'Wazo Fax'
) -> Backend:
    # Return a backend taking one additional argument, an email address,
    # which sends the fax file as a pdf to the given email address when
    # called.
    with open(content_file, 'r') as f:
        content = f.read()

    def aux(faxfile: str, dstnum: str, args: list[str]) -> None:
        # args[0] is the email address to send the fax to
        email = args[0]
        if not email:
            raise ValueError(f"Invalid email value: {email}")

        pdffile = _convert_tiff_to_pdf(faxfile)
        try:
            format_dict = {"dstnum": dstnum}
            p = subprocess.Popen(
                [
                    MUTT_PATH,
                    "-e",
                    "set copy=no",
                    "-e",
                    f"set from={email_from}",
                    "-e",
                    f"set realname='{email_realname}'",
                    "-e",
                    "set use_from=yes",
                    "-s",
                    subject % format_dict,
                    "-a",
                    pdffile,
                    "--",
                    email,
                ],
                stdin=subprocess.PIPE,
                close_fds=True,
            )
            p.communicate((content % format_dict).encode('utf8'))
            if p.returncode:
                raise Exception(f"mutt exit code was {p.returncode}")
        finally:
            try:
                os.remove(pdffile)
            except OSError as e:
                logger.info("Could not remove pdffile %s: %s", pdffile, e)

    return aux


def _new_printer_backend(
    name: str | None = None, convert_to_pdf: str | None = None
) -> Backend:
    # Return a backend taking no additional argument, which prints the fax
    # to the given printer when called.
    # Note that if name is None, it uses the default printer.
    convert_to_pdf = _convert_config_value_to_bool(
        convert_to_pdf, True, 'convert_to_pdf'
    )

    def aux(faxfile: str, dstnum: str, args: list[str]) -> None:
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
                except OSError as e:
                    logger.info('Could not remove pdffile %s: %s', pdffile, e)

    return aux


def _convert_config_value_to_bool(
    config_value: str | None, default: bool, param_name: str
) -> bool:
    if config_value is None:
        return default
    elif config_value == '0':
        return False
    elif config_value == '1':
        return True
    else:
        logger.warning('invalid param %s: %r', param_name, config_value)
        return default


def _new_ftp_backend(
    host: str,
    username: str,
    password: str,
    port: int = 21,
    directory: str | None = None,
    convert_to_pdf: str | None = None,
) -> Backend:
    # Return a backend taking no argument, which transfers the fax,
    # in its original format, to the given FTP server when called.
    # Note that a connection is made every time the backend is called.
    convert_to_pdf = _convert_config_value_to_bool(
        convert_to_pdf, True, 'convert_to_pdf'
    )
    port = int(port)

    def aux(faxfile: str, dstnum: str, args: list[str]) -> None:
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
                    stor_command = f"STOR {os.path.basename(filename)}"
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


def _do_handle_fax(fax_file: str, dstnum: str, args: list[str]) -> None:
    logger.info('Handling fax for destination %s', dstnum)
    if not fax_file:
        raise ValueError(f"Invalid faxfile value: {fax_file}")
    if not dstnum:
        raise ValueError(f"Invalid dstnum value: {dstnum}")

    if dstnum in DESTINATIONS:
        logger.debug("Using backends for destination %s", dstnum)
        backends = DESTINATIONS[dstnum]
    else:
        if "default" in DESTINATIONS:
            logger.debug("Using backends for destination default")
            backends = DESTINATIONS["default"]
        else:
            raise ValueError(f"No backends associated with dstnum {dstnum}")

    for backend in backends:
        try:
            backend(fax_file, dstnum, args)
        except Exception:
            logger.error("Fax backend %s failed to handle fax", backend, exc_info=True)
            raise

    try:
        os.remove(fax_file)
    except OSError as e:
        logger.info("Could not remove faxfile %s: %s", fax_file, e)


def handle_fax(agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
    try:
        faxfile = args[0]
        dstnum = agi.get_variable("XIVO_DSTNUM")
        _do_handle_fax(faxfile, dstnum, args[1:])
    except Exception as e:
        agi.dp_break(e)


_BACKENDS_FACTORY = [
    ("mail", _new_mail_backend),
    ("printer", _new_printer_backend),
    ("ftp", _new_ftp_backend),
]


def setup_handle_fax(cursor: DictCursor) -> None:
    # Raise an error if a backend creation failed, etc.
    # 1. read config
    config = RawConfigParser()
    with open(CONFIG_FILE) as f:
        config.read_file(f)

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
    backends: dict[str, Backend] = {}
    for backend_prefix, backend_factory in _BACKENDS_FACTORY:
        for section in [s for s in config.sections() if s.startswith(backend_prefix)]:
            backend_factory_args = dict(config.items(section))
            logger.debug(
                "Creating backend, name %s, factory %s", section, backend_factory
            )
            backends[section] = backend_factory(**backend_factory_args)
    logger.debug("Created %s backends", len(backends))

    # 4. creation destinations
    global DESTINATIONS
    DESTINATIONS = {}
    for section in [s for s in config.sections() if s.startswith("dstnum_")]:
        cur_destination = section[7:]  # 6 == len("dstnum_")
        cur_backend_ids = [s.strip() for s in config.get(section, "dest").split(",")]
        cur_backends = _build_backends_list(backends, cur_backend_ids, cur_destination)
        logger.debug(
            'Creating destination, dstnum %s, backends %s',
            cur_destination,
            cur_backend_ids,
        )
        DESTINATIONS[cur_destination] = cur_backends
    logger.debug("Created %s destinations", len(DESTINATIONS))


def _build_backends_list(
    available_backends: dict[str, Backend], backend_ids: list[str], destination: str
) -> list[Backend]:
    backends = []
    for backend_id in backend_ids:
        if backend_id in available_backends:
            backends.append(available_backends[backend_id])
        else:
            logger.warning(
                'Destination %s is referencing unknown backend "%s" in xivo_fax.conf',
                destination,
                backend_id,
            )
    return backends


agid.register(handle_fax, setup_handle_fax)
