#-------------------------------------------------------------------------------
#
# WPS 1.0 service proxy
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

try:
    from urllib.parse import urlparse
except ImportError:
    # Python 2 backward compatibility
    from urlparse import urlparse

import re
from .wps import WPS10Service
from .environment import JINJA2_ENVIRONMENT


RE_MATCH_JOB_ID = re.compile(
    r"^[0-9a-f]{8,8}-[0-9a-f]{4,4}-[0-9a-f]{4,4}-[0-9a-f]{4,4}-[0-9a-f]{12,12}$"
)


class ViresWPS10Service(WPS10Service):
    """ VirES specific WPS 1.0 service proxy class.
    This class implement additional VirES specific synchronous clean-up handler.

        wps = ViresWPS10Service(url, headers)

        Parameters:
            url     - service URL
            headers - optional dictionary of the HTTP headers sent with each
                      request
    """
    template_remove_job = JINJA2_ENVIRONMENT.get_template("vires_remove_job.xml")

    def _default_cleanup_handler(self, status_url):
        """ Remove asynchronous job using the VirES specific interface. """
        job_id = status_url_to_job_id(status_url)
        self.logger.debug("Removing VirES asynchronous job %s.", job_id)
        request = self.template_remove_job.render(job_id=job_id).encode('UTF-8')
        self.retrieve(request)


def status_url_to_job_id(status_url):
    """ Extract job id from a VirES WPS status URL. """
    for item in urlparse(status_url).path.split("/"):
        if RE_MATCH_JOB_ID.match(item):
            return item
    else:
        raise ValueError("Invalid status URL %r!" % status_url)
