#-------------------------------------------------------------------------------
#
# viresclient package setup
#
# Project: VirES-Python-Client
# Authors: Ashley Smith <ashley.smith@ed.ac.uk>
#          Martin Paces <martin.paces@eox.at>
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

import os
from setuptools import setup, find_packages

with open('viresclient/__init__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            continue


# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='viresclient',
    version=version,
    license='EOX licence (MIT style)',
    description='A Python client for interacting with a VirES server',
    long_description=read('README.rst'),
    author='Ashley Smith',
    author_email='ashley.smith@ed.ac.uk',
    url='https://github.com/ESA-VirES/VirES-Python-Client',
    packages=find_packages(),
    scripts=[],
    package_data={
        'viresclient': [
            '_wps/templates/*'
        ],
    },
    install_requires=['Jinja2>=2.10, <3.0.0',
                      'pandas>=0.18;python_version>="3.5.0"',
                      'pandas<0.21;python_version<"3.5.0"',
                      'cdflib==0.3.9',
                      'tables>=3.4.4, <4.0.0',
                      'tqdm>=4.23.0, <5.0.0',
                      'xarray>=0.10.0, <0.12.0'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest']
)
