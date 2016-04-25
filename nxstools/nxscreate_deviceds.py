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

""" TANGO datasources creator for devices """

import sys

from optparse import OptionParser

from nxstools.nxsdevicetools import (
    checkServer, getAttributes, getServerTangoHost)
from nxstools.nxscreator import DeviceDSCreator

PYTANGO = False
try:
    import PyTango
    PYTANGO = True
except:
    pass


def _createParser():
    """ creates parser
    """
    #: usage example
    usage = "usage: %prog deviceds [options] [dv_attr1 " \
        + "[dv_attr2 [dv_attr3 ...]]]\n " \
        + " e.g.\n" \
        + "       nxscreate deviceds  -v p09/pilatus/haso228k \n" \
        + "       nxscreate deviceds  -v p09/lambda2m/haso228k  -s haslambda -b \n" \
        + "       nxscreate deviceds  -v p09/pilatus300k/haso228k -b" \
        + " -o pilatus300k_ RoI Energy ExposureTime\n" \
        + "\n" \
        + " - without <dv_attr1>: datasources for all attributes are created\n" \
        + " - with -b: datasources are created" \
        + " in Configuration Server database\n" \
        + " - without -b: datasources are created" \
        + " on the local filesystem in -d <directory> \n" \
        + " - default: <directory> is '.' \n" \
        + "            <server> is taken from Tango DB\n" \
        + "            <datasource> is 'exp_mot' \n" \
        + "            <host>, <port> are taken from <server>\n"

    #: option parser
    parser = OptionParser(usage=usage)

    parser.add_option("-v", "--device", type="string",
                      help="device, i.e. p09/pilatus300k/01 (mandatory)",
                      dest="device", default="")

    parser.add_option("-o", "--datasource-prefix", type="string",
                      help="datasource-prefix",
                      dest="datasource", default="")

    parser.add_option("-d", "--directory", type="string",
                      help="output datasource directory",
                      dest="directory", default=".")
    parser.add_option("-x", "--file-prefix", type="string",
                      help="file prefix, i.e. counter",
                      dest="file", default="")
    parser.add_option("-s", "--host", type="string",
                      help="tango host name",
                      dest="host", default="")
    parser.add_option("-t", "--port", type="string",
                      help="tango host port",
                      dest="port", default="10000")

    parser.add_option("-b", "--database", action="store_true",
                      default=False, dest="database",
                      help="store components in Configuration Server database")

    parser.add_option("-n", "--no-group", action="store_true",
                      default=False, dest="nogroup",
                      help="don't create common group with a name of"
                      " datasource prefix")

    parser.add_option("-r", "--server", dest="server",
                      help="configuration server device name")
    return parser


def main():
    """ the main function
    """

    parser = _createParser()
    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        sys.exit(255)
    else:
        args = args[1:]

    if (options.database and not options.server) or \
       (not options.host and not options.server):
        if not PYTANGO:
            print >> sys.stderr, "nxscreate: No PyTango installed\n"
            parser.print_help()
            sys.exit(255)

        options.server = checkServer()
        if not options.server:
            parser.print_help()
            print ""
            sys.exit(0)

    if not options.host:
        if not PYTANGO:
            print >> sys.stderr, \
                "nxscreate: No Tango Host or PyTango installed\n"
            parser.print_help()
            sys.exit(255)
        hostport = getServerTangoHost(options.server)
        options.host, options.port = hostport.split(":")

    if options.database:
        print("CONFIG SERVER: %s" % options.server)
    else:
        print("OUTPUT DIRECTORY: %s" % options.directory)

    if not options.device.strip():
        parser.print_help()
        sys.exit(255)

    if args:
        aargs = list(args)
    else:
        if not PYTANGO:
            sys.stderr.write("CollCompCreator No PyTango installed\n")
            parser.print_help()
            sys.exit(255)
        aargs = getAttributes(options.device, options.host, options.port)

    creator = DeviceDSCreator(options, aargs)
    creator.create()


if __name__ == "__main__":
    main()
