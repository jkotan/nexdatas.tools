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
## \package nxstools tools for nxswriter
## \file nxscreate_tango_ds
# datasource creator

""" TANGO datasource creator """

import sys

from optparse import OptionParser

from nxstools.nxsdevicetools import checkServer
from nxstools.nxscreator import (TangoDSCreator, WrongParameterError)

PYTANGO = False
try:
    import PyTango
    PYTANGO = True
except:
    pass


## creates parser
def createParser():
    ## usage example
    usage = "usage: %prog [options]\n" \
        + "       nxscreate tangods [options]"
    ## option parser
    parser = OptionParser(usage=usage)

    parser.add_option("-p", "--device-prefix", type="string",
                      help="device prefix, i.e. exp_c",
                      dest="device", default="")
    parser.add_option("-f", "--first",
                      help="first index",
                      dest="first", default="1")
    parser.add_option("-l", "--last",
                      help="last index",
                      dest="last", default=None)

    parser.add_option("-a", "--attribute", type="string",
                      help="tango attribute name",
                      dest="attribute", default="Position")

    parser.add_option("-o", "--datasource-prefix", type="string",
                      help="datasource-prefix",
                      dest="datasource", default="TG_")

    parser.add_option("-d", "--directory", type="string",
                      help="output datasource directory",
                      dest="directory", default=".")
    parser.add_option("-x", "--file-prefix", type="string",
                      help="file prefix, i.e. counter",
                      dest="file", default="")
    parser.add_option("-s", "--host", type="string",
                      help="tango host name",
                      dest="host", default="localhost")
    parser.add_option("-t", "--port", type="string",
                      help="tango host port",
                      dest="port", default="10000")

    parser.add_option("-b", "--database", action="store_true",
                      default=False, dest="database",
                      help="store components in Configuration Server database")

    parser.add_option("-r", "--server", dest="server",
                      help="configuration server device name")
    return parser


## the main function
def main():

    parser = createParser()
    (options, args) = parser.parse_args()


    if len(args) == 0:
        parser.print_help()
        sys.exit(255)
    else:
        args = args[1:]

    if options.database and not options.server:
        if not PYTANGO:
            print >> sys.stderr, "CollCompCreator No PyTango installed\n"
            parser.print_help()
            sys.exit(255)

        options.server = checkServer()
        if not options.server:
            parser.print_help()
            print ""
            sys.exit(0)

    if options.database:
        print "CONFIG SERVER:", options.server
    else:
        print "OUTPUT DIRECTORY:", options.directory

    creator = TangoDSCreator(options, args)
    try:
        creator.create()
    except WrongParameterError as e:
        sys.stderr.write(str(e))
        parser.print_help()
        sys.exit(255)


if __name__ == "__main__":
    main()
