#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2016 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
#

""" NeXus main metadata viewer """

import sys
import os
import time
import fnmatch

from .nxsparser import TableTools
from optparse import OptionParser
from .nxsfileparser import NXSFileParser

#: (:obj:`bool`) True if pni.io.nx.h5 available
PNIIO = False
try:
    import pni.io.nx.h5 as nx
    PNIIO = True
except:
    pass


def main():
    """ the main function
    """

    #: usage example
    usage = "usage: nxsinfo geometry <file_name>\n"\
        + "  e.g.: nxsinfo geometry saxs_ref1_02.nxs\n\n "\
        + "show geometry information for the nexus file" 

    #: option parser
    parser = OptionParser(usage=usage)
    parser.add_option(
        "-c", "--columns", type="string",
        help="names of column to be shown separated by commas "
        "without spaces. The possible names are: "
        "depends_on,dtype,full_path,nexus_path,nexus_type,shape,"
        "trans_type,trans_offset,trans_vector,units,value,",
        dest="headers", default="")
    parser.add_option(
        "-f", "--filters", type="string",
        help="full_path filters separated by commas "
        "without spaces. Default: "
        "*:NXtransformations/*,*/depends_on",
        dest="filters", default="")
    parser.add_option(
        "-v", "--values", type="string",
        help="field names which value should be stored separated by commas "
        "without spaces. Default: depends_on",
        dest="values", default="")

    (options, args) = parser.parse_args()

    if len(args) < 2:
        parser.print_help()
        sys.exit(255)
    else:
        args = args[1:]

    if not PNIIO:
        sys.stderr.write("nxsfileinfo: No pni.io.nx.h5 installed\n")
        parser.print_help()
        sys.exit(255)

    try:
        fl = nx.open_file(args[0])
    except:
        sys.stderr.write("nxsfileinfo: File '%s' cannot be opened\n" % args[0])
        parser.print_help()
        sys.exit(255)

    #: (:obj:`list`< :obj:`str`>)  full_path filters 
    filters = ["*:NXtransformations/*", "*/depends_on"]
    #: (:obj:`list`< :obj:`str`>)  column headers
    headers = ["nexus_path", "nexus_type", "units",
               "trans_type", "trans_vector", "trans_offset",
               "depends_on"]

    #: (:obj:`list`< :obj:`str`>)  field names which value should be stored
    values = ["depends_on"]
    
    if options.headers:
        headers = options.headers.split(',')
    if options.filters:
        filters = options.filters.split(',')
    if options.values:
        values = options.values.split(',')

    
    rt = fl.root()
    nxsparser = NXSFileParser(rt)
    nxsparser.filters = filters
    nxsparser.valuestostore = values
    nxsparser.parse()
    fl.close()
    
    description = []
    ttools = TableTools(nxsparser.description)
    ttools.title = "    file: '%s'" % args[0]
    ttools.headers = headers
    description.extend(ttools.generateList())
    print("\n".join(description))
    
    
if __name__ == "__main__":
    main()

