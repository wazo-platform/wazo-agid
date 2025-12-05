# Copyright 2004-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

# Modifications by Proformatique from pyst-0.2:
#     - AGI._quote does escaping
#     - small optimization in AGI.send_command()
#     - removed stderr
#     - removed double quoting from database_get()
#     - replaced a reference to old style ListType with a call to isinstance(..., list)

# Adapted for FastAGI by Proformatique :
#     - replaced references to sys.std{in,out} to custom file objects.
#     - added args attribute to replace sys.argv.
#     - added Fast prefix for coherency.

from __future__ import annotations

import pprint
import re
from typing import TYPE_CHECKING, Any, BinaryIO, NoReturn

if TYPE_CHECKING:
    from typing import Literal


DigitList = list[str | int] | str
ResultDict = dict[str, tuple[str, str]]

DEFAULT_TIMEOUT = 2000  # 2sec timeout used as default for functions that take timeouts
DEFAULT_RECORD = 20000  # 20sec record time

re_code = re.compile(r'(^\d*)\s*(.*)')
re_kv = re.compile(r'(?P<key>\w+)=(?P<value>[^\s]+)\s*(?:\((?P<data>.*)\))*')

__all__ = [
    'FastAGIException',
    'FastAGIError',
    'FastAGIUnknownError',
    'FastAGIAppError',
    'FastAGIHangup',
    'FastAGISIGPIPEHangup',
    'FastAGIResultHangup',
    'FastAGIDBError',
    'FastAGIUsageError',
    'FastAGIInvalidCommand',
    'FastAGI',
]


class FastAGIException(Exception):
    pass


class FastAGIError(FastAGIException):
    pass


class FastAGIUnknownError(FastAGIError):
    pass


class FastAGIAppError(FastAGIError):
    pass


# there are several types of hangups we can detect
# they all are derived from FastAGIHangup
class FastAGIHangup(FastAGIAppError):
    pass


class FastAGISIGPIPEHangup(FastAGIHangup):
    pass


class FastAGIResultHangup(FastAGIHangup):
    pass


class FastAGIDBError(FastAGIAppError):
    pass


class FastAGIUsageError(FastAGIError):
    pass


class FastAGIInvalidCommand(FastAGIError):
    pass


class FastAGIDialPlanBreak(FastAGIException):
    pass


class FastAGI:
    """
    This class encapsulates communication between Asterisk and a python
    program (typically a daemon).
    It handles encoding commands to Asterisk and parsing responses from
    Asterisk.
    """

    def __init__(self, inf: BinaryIO, outf: BinaryIO, config: dict[str, Any]) -> None:
        self.inf = inf
        self.outf = outf
        self.config = config

        self._got_sighup = False
        self.env: dict[str, str] = {}
        self._get_agi_env()
        self.args: list[str] = []
        self._get_agi_args()

    def _get_agi_env(self) -> None:
        while 1:
            line = self.inf.readline().strip().decode('utf8')
            if line == '':
                # blank line signals end
                break
            key_data = line.split(':', 1)
            key = key_data[0].strip()
            if key:
                if len(key_data) > 1:
                    self.env[key] = key_data[1].strip()
                else:
                    self.env[key] = ""

    def _get_agi_args(self) -> None:
        i = 1
        while f"agi_arg_{i:d}" in self.env:
            self.args.append(self.env[f"agi_arg_{i:d}"])
            i += 1

    @staticmethod
    def _quote(string: str | int | bytes | None) -> str:
        if string is None:
            string = ''
        elif isinstance(string, bytes):
            string = string.decode('utf8')
        elif not isinstance(string, str):
            string = str(string)

        return '"{}"'.format(
            string.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
        )

    @staticmethod
    def dp_break(message: str | Exception) -> NoReturn:
        raise FastAGIDialPlanBreak(
            str(message) if isinstance(message, Exception) else message
        )

    def execute(self, command: str, *args: str | int) -> ResultDict:
        try:
            self.send_command(command, *args)
            return self.get_result()
        except OSError as e:
            if e.errno == 32:
                # Broken Pipe * let us go
                raise FastAGISIGPIPEHangup("Received SIGPIPE")
            else:
                raise

    def send_command(self, command: str, *args: str | int) -> None:
        """Send a command to Asterisk"""
        command = ' '.join([command.strip()] + list(map(str, args))).strip() + "\n"
        self.outf.write(command.encode('utf8'))
        self.outf.flush()

    def fail(self) -> None:
        """Force Asterisk to change the result state of the AGI to
        AGI_RESULT_FAILURE so that it will abort the AGI.
        This function catches internal EPIPE IOError and does not report them
        in any way.
        """
        try:
            self.send_command("failure to have pure code")
        except OSError as e:
            if e.errno != 32:
                raise

    def get_result(self) -> ResultDict:
        """Read the result of a command from Asterisk"""
        code = 0
        response = ''
        result = {'result': ('', '')}
        line = self.inf.readline().strip().decode('utf8')
        m = re_code.search(line)
        if m:
            code = int(m.group(1))
            response = m.group(2)

        if code == 200:
            for key, value, data in re_kv.findall(response):
                result[key] = (value, data)

                # If user hangs up... we get 'hangup' in the data
                if data == 'hangup':
                    raise FastAGIResultHangup("User hungup during execution")

                if key == 'result' and value == '-1':
                    raise FastAGIAppError("Error executing application, or hangup")
            return result
        if code == 510:
            raise FastAGIInvalidCommand(response)
        if code == 520:
            usage = [line]
            line = self.inf.readline().strip().decode('utf8')
            while line[:3] != '520':
                usage.append(line)
                line = self.inf.readline().strip().decode('utf8')
            usage.append(line)
            raise FastAGIUsageError('{}\n'.format('\n'.join(usage)))

        raise FastAGIUnknownError(code, 'Unhandled code or undefined response')

    def _process_digit_list(self, digits: DigitList) -> str:
        if isinstance(digits, list):
            digits = ''.join(map(str, digits))
        return self._quote(digits)

    def answer(self) -> None:
        """
        Answer channel if not already in answered state.
        """
        self.execute('ANSWER')['result'][0]

    @staticmethod
    def code_to_char(code: str) -> str:
        """
        Return chr(int(code))
        Raise FastAGIError on error
        """
        if code == '0':
            return ''
        try:
            return chr(int(code))
        except (TypeError, ValueError):
            raise FastAGIError(f'Unable to convert result to char: {code}')

    def wait_for_digit(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """
        Waits for up to 'timeout' milliseconds for a channel to receive a DTMF
        digit.  Returns digit dialed
        Throws FastAGIError on channel failure
        """
        res = self.execute('WAIT FOR DIGIT', timeout)['result'][0]
        return self.code_to_char(res)

    def send_text(self, text=''):
        """
        Sends the given text on a channel.  Most channels do not support the
        transmission of text.
        Throws FastAGIError on error/hangup
        """
        self.execute('SEND TEXT', self._quote(text))['result'][0]

    def receive_char(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """
        Receives a character of text on a channel.  Specify timeout to be the
        maximum time to wait for input in milliseconds, or 0 for infinite. Most channels
        do not support the reception of text.
        """
        res = self.execute('RECEIVE CHAR', timeout)['result'][0]
        return self.code_to_char(res)

    def tdd_mode(self, mode: Literal['off', 'on'] = 'off') -> None:
        """
        Enable/Disable TDD transmission/reception on a channel.
        Throws FastAGIAppError if channel is not TDD-capable.
        """
        res = self.execute('TDD MODE', mode)['result'][0]
        if res == '0':
            raise FastAGIAppError('Channel %s is not TDD-capable')

    def stream_file(
        self, filename: str, escape_digits: DigitList = '', sample_offset: int = 0
    ) -> str:
        """
        Send the given file, allowing playback to be interrupted by the given digits, if any.
        If sample offset is provided then the audio will seek to sample
        offset before play starts.  Returns  digit if one was pressed.
        Throws FastAGIError if the channel was disconnected.  Remember, the file
        extension must not be included in the filename.
        """
        escape_digits = self._process_digit_list(escape_digits)
        response = self.execute('STREAM FILE', filename, escape_digits, sample_offset)
        res = response['result'][0]
        return self.code_to_char(res)

    def control_stream_file(
        self,
        filename: str,
        escape_digits: DigitList = '',
        skipms: int = 3_000,
        fwd: str = '',
        rew: str = '',
        pause: str = '',
    ) -> str:
        """
        Send the given file, allowing playback to be interrupted by the given digits, if any.
        If sample offset is provided then the audio will seek to sample
        offset before play starts.  Returns  digit if one was pressed.
        Throws FastAGIError if the channel was disconnected.  Remember, the file
        extension must not be included in the filename.
        """
        escape_digits = self._process_digit_list(escape_digits)
        response = self.execute(
            'CONTROL STREAM FILE',
            self._quote(filename),
            escape_digits,
            self._quote(skipms),
            self._quote(fwd),
            self._quote(rew),
            self._quote(pause),
        )
        res = response['result'][0]
        return self.code_to_char(res)

    def send_image(self, filename: str) -> None:
        """
        Sends the given image on a channel.  Most channels do not support the
        transmission of images.   Image names should not include extensions.
        Throws FastAGIError on channel failure
        """
        res = self.execute('SEND IMAGE', filename)['result'][0]
        if res != '0':
            raise FastAGIAppError(
                f'Channel failure on channel {self.env.get("agi_channel", "UNKNOWN")}'
            )

    def say_digits(self, digits: DigitList, escape_digits: DigitList = '') -> str:
        """
        Say a given digit string, returning early if any of the given DTMF digits
        are received on the channel.
        Throws FastAGIError on channel failure
        """
        digits = self._process_digit_list(digits)
        escape_digits = self._process_digit_list(escape_digits)
        res = self.execute('SAY DIGITS', digits, escape_digits)['result'][0]
        return self.code_to_char(res)

    def say_number(
        self, number: str, escape_digits: DigitList = '', gender: str = ''
    ) -> str:
        """
        Say a given digit string, returning early if any of the given DTMF digits
        are received on the channel.
        Throws FastAGIError on channel failure
        """
        number = self._process_digit_list(number)
        escape_digits = self._process_digit_list(escape_digits)
        res = self.execute('SAY NUMBER', number, escape_digits, gender)['result'][0]
        return self.code_to_char(res)

    def say_alpha(self, characters: str, escape_digits: DigitList = '') -> str:
        """
        Say a given character string, returning early if any of the given DTMF
        digits are received on the channel.
        Throws FastAGIError on channel failure
        """
        characters = self._process_digit_list(characters)
        escape_digits = self._process_digit_list(escape_digits)
        res = self.execute('SAY ALPHA', characters, escape_digits)['result'][0]
        return self.code_to_char(res)

    def say_phonetic(self, characters: str, escape_digits: DigitList = '') -> str:
        """
        Phonetically say a given character string, returning early if any of
        the given DTMF digits are received on the channel.
        Throws FastAGIError on channel failure
        """
        characters = self._process_digit_list(characters)
        escape_digits = self._process_digit_list(escape_digits)
        res = self.execute('SAY PHONETIC', characters, escape_digits)['result'][0]
        return self.code_to_char(res)

    def say_date(self, seconds: str | int, escape_digits: DigitList = '') -> str:
        """
        Say a given date, returning early if any of the given DTMF digits are
        pressed.  The date should be in seconds since the UNIX Epoch (Jan 1, 1970 00:00:00)
        """
        escape_digits = self._process_digit_list(escape_digits)
        res = self.execute('SAY DATE', seconds, escape_digits)['result'][0]
        return self.code_to_char(res)

    def say_time(self, seconds: str | int, escape_digits: DigitList = '') -> str:
        """
        Say a given time, returning early if any of the given DTMF digits are
        pressed.  The time should be in seconds since the UNIX Epoch (Jan 1, 1970 00:00:00)
        """
        escape_digits = self._process_digit_list(escape_digits)
        res = self.execute('SAY TIME', seconds, escape_digits)['result'][0]
        return self.code_to_char(res)

    def say_datetime(
        self,
        seconds: int | str,
        escape_digits: DigitList = '',
        format: str = '',
        zone: str = '',
    ) -> str:
        """
        Say a given date in the format specified (see voicemail.conf), returning
        early if any of the given DTMF digits are pressed.  The date should be
        in seconds since the UNIX Epoch (Jan 1, 1970 00:00:00).
        """
        escape_digits = self._process_digit_list(escape_digits)
        if format:
            format = self._quote(format)
        res = self.execute('SAY DATETIME', seconds, escape_digits, format, zone)[
            'result'
        ][0]
        return self.code_to_char(res)

    def get_data(
        self, filename: str, timeout: int = DEFAULT_TIMEOUT, max_digits: int = 255
    ) -> str:
        """
        Stream the given file and receive dialed digits
        """
        result = self.execute('GET DATA', filename, timeout, max_digits)
        res, _ = result['result']
        return res

    def get_option(
        self, filename: str, escape_digits: DigitList = '', timeout: int = 0
    ) -> str:
        """
        Send the given file, allowing playback to be interrupted by the given digits, if any.
        Returns  digit if one was pressed.
        Throws FastAGIError if the channel was disconnected.  Remember, the file
        extension must not be included in the filename.
        """
        escape_digits = self._process_digit_list(escape_digits)
        if timeout:
            response = self.execute('GET OPTION', filename, escape_digits, timeout)
        else:
            response = self.execute('GET OPTION', filename, escape_digits)

        res = response['result'][0]
        return self.code_to_char(res)

    def set_context(self, context: str) -> None:
        """
        Sets the context for continuation upon exiting the application.
        No error appears to be produced.  Does not set exten or priority
        Use at your own risk.  Ensure that you specify a valid context.
        """
        self.execute('SET CONTEXT', context)

    def set_extension(self, extension: str) -> None:
        """
        Sets the extension for continuation upon exiting the application.
        No error appears to be produced.  Does not set context or priority
        Use at your own risk.  Ensure that you specify a valid extension.
        """
        self.execute('SET EXTENSION', extension)

    def set_priority(self, priority: str) -> None:
        """
        Sets the priority for continuation upon exiting the application.
        No error appears to be produced.  Does not set exten or context
        Use at your own risk.  Ensure that you specify a valid priority.
        """
        self.execute('set priority', priority)

    def goto_on_exit(
        self, context: str = '', extension: str = '', priority: str = ''
    ) -> None:
        context = context or self.env['agi_context']
        extension = extension or self.env['agi_extension']
        priority = priority or self.env['agi_priority']
        self.set_context(context)
        self.set_extension(extension)
        self.set_priority(priority)

    def record_file(
        self,
        filename: str,
        format: str = 'gsm',
        escape_digits: str = '#',
        timeout: int = DEFAULT_RECORD,
        offset: int = 0,
        beep: str = 'beep',
    ) -> str:
        """
        Record to a file until a given dtmf digit in the sequence is received
        The format will specify what kind of file will be recorded.  The timeout
        is the maximum record time in milliseconds, or -1 for no timeout. Offset
        samples is optional, and if provided will seek to the offset without
        exceeding the end of the file
        """
        escape_digits = self._process_digit_list(escape_digits)
        res = self.execute(
            'RECORD FILE',
            self._quote(filename),
            format,
            escape_digits,
            timeout,
            offset,
            beep,
        )['result'][0]
        return self.code_to_char(res)

    def set_autohangup(self, secs: str | int) -> None:
        """
        Cause the channel to automatically hangup at <time> seconds in the
        future.  Of course, it can be hung up before then as well.   Setting to
        0 will cause the auto-hangup feature to be disabled on this channel.
        """
        self.execute('SET AUTOHANGUP', secs)

    def hangup(self, channel: str = '') -> None:
        """
        Hangs up the specified channel.
        If no channel name is given, hangs up the current channel
        """
        self.execute('HANGUP', channel)

    def appexec(self, application: str, options: str = '') -> str:
        """
        Executes <application> with given <options>.
        Returns whatever the application returns, or -2 on failure to find
        application
        """
        result = self.execute('EXEC', application, self._quote(options))
        res = result['result'][0]
        if res == '-2':
            raise FastAGIAppError(f'Unable to find application: {application}')
        return res

    def set_callerid(self, number: str) -> None:
        """
        Changes the caller id of the current channel.
        """
        self.execute('SET CALLERID', self._quote(number))

    def channel_status(self, channel: str = '') -> int:
        """
        Returns the status of the specified channel.  If no channel name is
        given the returns the status of the current channel.

        Return values:
        0 Channel is down and available
        1 Channel is down, but reserved
        2 Channel is off hook
        3 Digits (or equivalent) have been dialed
        4 Line is ringing
        5 Remote end is ringing
        6 Line is up
        7 Line is busy
        """
        try:
            result = self.execute('CHANNEL STATUS', channel)
        except FastAGIHangup:
            raise
        except FastAGIAppError:
            result = {'result': ('-1', '')}

        return int(result['result'][0])

    def set_variable(self, name: str, value: str | int) -> None:
        """Set a channel variable."""
        self.execute('SET VARIABLE', self._quote(name), self._quote(value))

    def get_variable(self, name: str) -> str:
        """Get a channel variable.

        This function returns the value of the indicated channel variable.  If
        the variable is not set, an empty string is returned.
        """
        try:
            result = self.execute('GET VARIABLE', self._quote(name))
        except FastAGIResultHangup:
            result = {'result': ('1', 'hangup')}

        return result['result'][1]

    def get_full_variable(self, name: str, channel: str | None = None):
        """Get a channel variable.

        This function returns the value of the indicated channel variable.  If
        the variable is not set, an empty string is returned.
        """
        try:
            if channel:
                result = self.execute(
                    'GET FULL VARIABLE', self._quote(name), self._quote(channel)
                )
            else:
                result = self.execute('GET FULL VARIABLE', self._quote(name))
        except FastAGIResultHangup:
            result = {'result': ('1', 'hangup')}

        return result['result'][1]

    def verbose(self, message: str | Exception, level: int = 1) -> None:
        """
        Sends <message> to the console via verbose message system.
        <level> is the the verbose level (1-4)
        """
        if isinstance(message, Exception):
            message = str(message)
        self.execute('VERBOSE', self._quote(message), level)

    def database_get(self, family: str, key: str) -> str:
        """
        Retrieves an entry in the Asterisk database for a given family and key.
        Returns 0 if <key> is not set.  Returns 1 if <key>
        is set and returns the variable in parentheses
        example return code: 200 result=1 (testvariable)
        """
        result = self.execute('DATABASE GET', self._quote(family), self._quote(key))
        res, value = result['result']
        if res == '0':
            raise FastAGIDBError(
                f'Key not found in database: family={family}, key={key}'
            )
        if res == '1':
            return value
        raise FastAGIError(
            f'Unknown exception for : family={family}, key={key}, result={pprint.pformat(result)}'
        )

    def database_put(self, family: str, key: str, value: str) -> None:
        """
        Adds or updates an entry in the Asterisk database for a
        given family, key, and value.
        """
        result = self.execute(
            'DATABASE PUT', self._quote(family), self._quote(key), self._quote(value)
        )
        res, value = result['result']
        if res == '0':
            raise FastAGIDBError(
                f'Unable to put value in database: family={family}, key={key}, value={value}'
            )

    def database_del(self, family: str, key: str) -> None:
        """
        Deletes an entry in the Asterisk database for a
        given family and key.
        """
        result = self.execute('DATABASE DEL', self._quote(family), self._quote(key))
        res, _ = result['result']
        if res == '0':
            raise FastAGIDBError(
                f'Unable to delete from database: family={family}, key={key}'
            )

    def database_deltree(self, family: str, key: str = '') -> None:
        """
        Deletes a family or specific keytree with in a family
        in the Asterisk database.
        """
        result = self.execute('DATABASE DELTREE', self._quote(family), self._quote(key))
        res, _ = result['result']
        if res == '0':
            raise FastAGIDBError(
                f'Unable to delete tree from database: family={family}, key={key}'
            )

    def noop(self) -> None:
        """
        Does nothing
        """
        self.execute('NOOP')
