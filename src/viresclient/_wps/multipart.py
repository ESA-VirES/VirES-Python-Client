# -------------------------------------------------------------------------------
#
# multi-part request handling
#
# Author: Martin Paces <martin.paces@eox.at>
#
# -------------------------------------------------------------------------------
# Copyright (C) 2025 EOX IT Services GmbH
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
# -------------------------------------------------------------------------------

from io import BytesIO

CHUNK_SIZE = 64 * 1024  # 64kB chunk-size
SEEK_SET = 0
SEEK_END = 2
CRLF = b"\r\n"


def generate_multipart_request(parts, boundary, chunksize=CHUNK_SIZE):
    """Generate multi-part payload from the given parts (pairs of the part
    payload and header dictionaries) and boundary string.
    """
    for part, headers in parts:
        yield _get_part_head(boundary, part, headers)
        yield from _generate_part(part, chunksize=chunksize)
    yield _get_multipart_tail(boundary)


def get_multipart_request_size(parts, boundary):
    """Get byte-size of the multi-part payload for the given parts
    (pairs of the part payload and header dictionaries) and boundary string.
    """
    size = 0
    for part, headers in parts:
        size += len(_get_part_head(boundary, part, headers))
        size += _get_part_byte_size(part)
    size += len(_get_multipart_tail(boundary))
    return size


def _get_part_head(boundary, part, headers):
    headers = {
        **headers,
        "Content-Length": _get_part_byte_size(part),
    }

    def _generate_part_head():
        yield ""
        yield f"--{boundary}"
        for key, value in headers.items():
            yield f"{key}: {value}"
        yield ""
        yield ""

    return CRLF.join(s.encode("ascii") for s in _generate_part_head())


def _get_multipart_tail(boundary):
    def _generate_multipart_tail():
        yield ""
        yield f"--{boundary}--"
        yield ""

    return CRLF.join(s.encode("ascii") for s in _generate_multipart_tail())


def _get_part_byte_size(part):
    if isinstance(part, bytes):
        return len(part)
    # assuming seekable binary file-like object
    part.seek(0, SEEK_END)
    size = part.tell()
    part.seek(0, SEEK_SET)
    return size


def _generate_part(part, chunksize=CHUNK_SIZE):
    if isinstance(part, bytes):
        part = BytesIO(part)
    # assuming seekable binary file-like object
    part.seek(0, SEEK_SET)
    while True:
        chunk = part.read(chunksize)
        if not chunk:
            break
        yield chunk
