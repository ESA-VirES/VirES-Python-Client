#-------------------------------------------------------------------------------
#
# logging utilities
#
# Author: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

from logging import StreamHandler, Formatter, INFO
from datetime import datetime

DEFAULT_LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
DEFAULT_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def set_stream_handler(logger, level=INFO, log_format=None, time_format=None):
    """ Set stream handler to the given logger. """
    formatter = FormatterUTC(
        log_format or DEFAULT_LOG_FORMAT,
        time_format or DEFAULT_TIME_FORMAT,
    )
    handler = StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(min(level, logger.level))


class FormatterUTC(Formatter):
    """" Custom log formatter class printing UTC timestamps with microsecond
    precision.

    The formatter uses 'datetime.datetime.strftime' method
    rather then 'time.strftime` used by the default formatter.
    """
    converter = datetime.utcfromtimestamp

    def formatTime(self, record, datefmt=None):
        dts = self.converter(record.created)
        return dts.strftime(datefmt) if datefmt else dts.isoformat(" ")

#    def format(self, record):
#        record.msg = record.msg.encode('unicode_escape')
#        return Formatter.format(self, record)
