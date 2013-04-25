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

import os, shutil, sys
from distutils.core import setup
from distutils.command.build import build
from distutils.command.clean import clean


## reading a file
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()



## metadata for distutils
SETUPDATA=dict(
    name = "nexdatas.tools",
    version = "1.0.0",
    author = "Jan Kotanski, Eugen Wintersberger , Halil Pasic",
    author_email = "jankotan@gmail.com, eugen.wintersberger@gmail.com, halil.pasic@gmail.com",
    maintainer = "Jan Kotanski, Eugen Wintersberger , Halil Pasic",
    maintainer_email = "jankotan@gmail.com, eugen.wintersberger@gmail.com, halil.pasic@gmail.com",
    description = ("Configuration tool  for creating components"),
    license = "GNU GENERAL PUBLIC LICENSE, version 3",
    keywords = "configuration writer Tango component nexus data",
    url = "http://code.google.com/p/nexdatas/",
    platforms= ("Linux"),
    packages=[ ],
#    data_files = datas,
    scripts = [
        'CMDtools/ndtscfg_get.py',
        'CMDtools/ndtscfg_list.py',
        'CMDtools/ndtscfg_show.py',
        'CMDtools/ndtscfg_sources.py',
        'CMDtools/ndtscfg_servers.py',
        'CMDtools/ndtscfg.py',
        'CMDtools/ndtstdw_servers.py',
        'CMDtools/ndtstdw_openfile.py',
        'CMDtools/ndtstdw_setdata.py',
        'CMDtools/ndtstdw_openentry.py',
        'CMDtools/ndtstdw_record.py',
        'CMDtools/ndtstdw_closeentry.py',
        'CMDtools/ndtstdw_closefile.py',
        'CMDtools/ndtstdw.py'],
#    package_data={'ndts': ['TDS']},
#    long_description= read('README'),
)

## the main function
def main():
    setup(**SETUPDATA)
        
if __name__ == '__main__':
    main()
