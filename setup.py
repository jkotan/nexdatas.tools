#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2013 DESY, Jan Kotanski <jkotan@mail.desy.de>
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



## metadata for distutils
SETUPDATA = dict(
    name = "nexdatas.tools",
    version = "1.2.0",
    author = "Jan Kotanski, Eugen Wintersberger , Halil Pasic",
    author_email = "jankotan@gmail.com, eugen.wintersberger@gmail.com, " \
        + "halil.pasic@gmail.com",
    maintainer = "Jan Kotanski, Eugen Wintersberger , Halil Pasic",
    maintainer_email = "jankotan@gmail.com, eugen.wintersberger@gmail.com, " \
        + "halil.pasic@gmail.com",
    description = ("Configuration tool  for creating components"),
    license = "GNU GENERAL PUBLIC LICENSE, version 3",
    keywords = "configuration writer Tango component nexus data",
    url = "http://code.google.com/p/nexdatas/",
    platforms = ("Linux"),
    package_dir = {"":"nxstools"},
    py_modules = ["nxsxml","nxsconfig", "nxsdata"],
    # packages = [ ],
    #    data_files = datas,
    scripts = [
        'nxstools/nxscreate_tango_ds',
        'nxstools/nxscreate_client_ds',
        'nxstools/nxscreate_ds_online',
        'nxstools/nxscreate_comp',
        'nxstools/nxsconfig_get',
        'nxstools/nxsconfig_list',
        'nxstools/nxsconfig_show',
        'nxstools/nxsconfig_sources',
        'nxstools/nxsconfig_variables',
        'nxstools/nxsconfig_components',
        'nxstools/nxsconfig_merge',
        'nxstools/nxsconfig_servers',
        'nxstools/nxsconfig_record',
        'nxstools/nxsconfig',
        'nxstools/nxsdata_servers',
        'nxstools/nxsdata_openfile',
        'nxstools/nxsdata_setdata',
        'nxstools/nxsdata_openentry',
        'nxstools/nxsdata_record',
        'nxstools/nxsdata_closeentry',
        'nxstools/nxsdata_closefile',
        'nxstools/nxsdata',
        ],
)





## the main function
def main():
    setup(**SETUPDATA)
        
if __name__ == '__main__':
    main()
