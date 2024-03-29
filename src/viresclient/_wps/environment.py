# -------------------------------------------------------------------------------
#
# Jinja2 environment initialization
#
# Author: Martin Paces <martin.paces@eox.at>
#
# -------------------------------------------------------------------------------
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
# -------------------------------------------------------------------------------

import json
from os.path import dirname, join

from jinja2 import Environment, FileSystemLoader


def wrap_as_cdata(content):
    """Wrap content by the XML CDATA element."""
    content = content.replace("]]>", "]]]]><![CDATA[>")
    return f"<![CDATA[{content}]]>"


_DIRNAME = dirname(__file__)
_TEMPLATESDIR = join(_DIRNAME, "templates")
JINJA2_ENVIRONMENT = Environment(loader=FileSystemLoader(_TEMPLATESDIR))
JINJA2_ENVIRONMENT.filters.update(
    d2s=lambda d: d.isoformat("T") + "Z",
    l2s=lambda l: ", ".join(str(v) for v in l),
    o2j=json.dumps,
    cdata=wrap_as_cdata,
)
