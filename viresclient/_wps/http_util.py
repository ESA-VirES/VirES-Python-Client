#-------------------------------------------------------------------------------
#
# http utilities
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

from base64 import standard_b64encode


def encode_no_auth(**kwargs):
    """ Dummy encoder.  """
    return {}


def encode_basic_auth(username, password, **kwargs):
    """ Encode username and password as the basic HTTP access authentication
    header.
    """
    return {
        b"Authorization": b"Basic " + standard_b64encode(
            ("%s:%s" % (username, password)).encode("UTF-8")
        )
    }


def encode_token_auth(token, **kwargs):
    """ Encode token as the bearer authentication header.
    """
    # NOTE: Only ASCII characters are allowed in HTTP headers.
    return {
        b"Authorization": b"Bearer " + token.encode("ascii")
    }
