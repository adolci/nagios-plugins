#!/usr/bin/env python
#  coding=utf-8
#  vim:ts=4:sts=4:sw=4:et
#
#  Author: Hari Sekhon
#  Date: 2017-08-30 14:52:43 +0200 (Wed, 30 Aug 2017)
#
#  https://github.com/harisekhon/nagios-plugins
#
#  License: see accompanying Hari Sekhon LICENSE file
#
#  If you're using my code you're welcome to connect with me on LinkedIn
#  and optionally send me feedback to help steer this or other code I publish
#
#  https://www.linkedin.com/in/harisekhon
#

"""

Nagios Plugin to check a docker image has the expected ID checksum

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import sys
import subprocess
import traceback
srcdir = os.path.abspath(os.path.dirname(__file__))
libdir = os.path.join(srcdir, 'pylib')
sys.path.append(libdir)
try:
    # pylint: disable=wrong-import-position
    from harisekhon.utils import log, CriticalError, UnknownError
    from harisekhon import NagiosPlugin
except ImportError as _:
    print(traceback.format_exc(), end='')
    sys.exit(4)

__author__ = 'Hari Sekhon'
__version__ = '0.1'


class CheckDockerImageChecksum(NagiosPlugin):

    def __init__(self):
        # Python 2.x
        super(CheckDockerImageChecksum, self).__init__()
        # Python 3.x
        # super().__init__()
        self.ok()
        self.msg = 'docker msg not defined'

    def add_options(self):
        self.add_opt('-d', '--docker-image', help='Docker image, in form of <repository>:<tag>')
        self.add_opt('-i', '--id', help='Docker image ID to expect docker image to have')

    def run(self):
        self.no_args()
        docker_image = self.get_opt('docker_image')
        expected_id = self.get_opt('id')
        process = subprocess.Popen(['docker', 'images', '{repo}'.format(repo=docker_image)],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        (stdout, stderr) = process.communicate()
        exitcode = process.returncode
        log.debug('stdout:\n%s', stdout)
        log.debug('stderr:\n%s', stderr)
        log.debug('exitcode: %s', exitcode)
        if stderr:
            raise UnknownError(stderr)
        if exitcode != 0:
            raise UnknownError("exit code returned was '{0}': {1} {2}".format(exitcode, stdout, stderr))
        if not stdout:
            raise UnknownError('no output from docker images command!')
        output = [_ for _ in stdout.split('\n') if _]
        if len(output) < 2:
            raise CriticalError("docker image '{repo}' not found!".format(repo=docker_image))
        header_line = output[0]
        image_header = header_line[48:60].strip()
        if image_header != 'IMAGE ID':
            raise UnknownError("3rd column in header '{0}' is not 'IMAGE ID' as expected, parsing failed!"\
                               .format(image_header))
        _id = output[1][48:60].strip()
        self.msg = "docker image '{repo}' id '{id}'".format(repo=docker_image, id=_id)
        if not expected_id:
            return
        if not re.match(r'sha\d+:\w+', _id):
            raise UnknownError("{msg} not in sha format as expected!".format(msg=self.msg))
        if _id != expected_id:
            self.critical()
            self.msg += " (expected '{0}')".format(expected_id)


if __name__ == '__main__':
    CheckDockerImageChecksum().main()
