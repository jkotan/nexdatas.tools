#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2015 DESY, Jan Kotanski <jkotan@mail.desy.de>
#
#    nexdatas is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    nexdatas is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with nexdatas.  If not, see <http://www.gnu.org/licenses/>.
## \package nexdatas.tools nexdatas
## \file setup.py
# GUI to create the XML components

""" setup.py for command-line tools """

import os
from distutils.core import setup


## reading a file
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

PKG = "nxstools"
IPKG = __import__(PKG)

## metadata for distutils
SETUPDATA = dict(
    name="nexdatas.tools",
    version=IPKG.__version__,
    author="Jan Kotanski, Eugen Wintersberger , Halil Pasic",
    author_email="jankotan@gmail.com, eugen.wintersberger@gmail.com, "
    + "halil.pasic@gmail.com",
    maintainer="Jan Kotanski, Eugen Wintersberger , Halil Pasic",
    maintainer_email="jankotan@gmail.com, eugen.wintersberger@gmail.com, "
    + "halil.pasic@gmail.com",
    description=("Configuration tool  for creating components"),
    license="GNU GENERAL PUBLIC LICENSE, version 3",
    keywords="configuration writer Tango component nexus data",
    url="http://github.com/jkotan/nexdatas/",
    platforms=("Linux"),
    packages=["nxstools"],
    #    data_files = datas,
    scripts=[
        'ndtsconfig_get',
        'ndtsconfig_list',
        'ndtsconfig_show',
        'ndtsconfig_sources',
        'ndtsconfig_variables',
        'ndtsconfig_components',
        'ndtsconfig_merge',
        'ndtsconfig_servers',
        'ndtsconfig_record',
        'nxsconfig',
        'ndtsdata_servers',
        'ndtsdata_openfile',
        'ndtsdata_setdata',
        'ndtsdata_openentry',
        'ndtsdata_record',
        'ndtsdata_closeentry',
        'ndtsdata_closefile',
        'nxsdata',
        'ndtscreate_clientds',
        'ndtscreate_tangods',
        'ndtscreate_deviceds',
        'ndtscreate_dsonline',
        'ndtscreate_onlineds',
        'ndtscreate_comp',
        'nxscreate',
        'nxsetup',
        ],
    long_description=read('README')
)


## the main function
def main():
    setup(**SETUPDATA)


if __name__ == '__main__':
    main()
