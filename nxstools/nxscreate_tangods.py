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

""" TANGO datasource creator """

import sys

from optparse import OptionParser

from nxstools.nxsdevicetools import checkServer, getServerTangoHost
from nxstools.nxscreator import (TangoDSCreator, WrongParameterError)

#: (:obj:`bool`) True if PyTango available
PYTANGO = False
try:
    import PyTango
    PYTANGO = True
except:
    pass


def _createParser():
    """ creates parser

    :returns: option parser
    :rtype: :class:`optparse.OptionParser`
    """
    #: usage example
    usage = "usage: %prog tangods [options]\n" \
        + " e.g.\n" \
        + "       nxscreate tangods -f1 -l2  -v p09/motor/exp. -s exp_mot \n" \
        + "       nxscreate tangods -f1 -l32  -v p02/motor/eh1a. -s exp_mot -b \n" \
        + "       nxscreate tangods -f1 -l32  -v p01/motor/oh1. -s exp_mot -b \n" \
        + "       nxscreate tangods -f1 -l8  -v pXX/slt/exp. -s slt_exp_ -u" \
        + " hasppXX.desy.de -b \n" \
        + "\n" \
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

    parser.add_option("-v", "--device-prefix", type="string",
                      help="device prefix, i.e. exp_c (mandatory)",
                      dest="device", default="")
    parser.add_option("-f", "--first",
                      help="first index (mandatory)",
                      dest="first", default="1")
    parser.add_option("-l", "--last",
                      help="last index (mandatory)",
                      dest="last", default=None)

    parser.add_option("-a", "--attribute", type="string",
                      help="tango attribute name",
                      dest="attribute", default="Position")

    parser.add_option("-s", "--datasource-prefix", type="string",
                      help="datasource-prefix "
                      "(useful for avoiding duplicated datasource names)",
                      dest="datasource", default="exp_mot")

    parser.add_option("-o", "--overwrite", action="store_true",
                      default=False, dest="overwrite",
                      help="overwrite existing datasources")
    parser.add_option("-d", "--directory", type="string",
                      help="output datasource directory",
                      dest="directory", default=".")
    parser.add_option("-x", "--file-prefix", type="string",
                      help="file prefix, i.e. counter",
                      dest="file", default="")
    parser.add_option("-u", "--host", type="string",
                      help="tango host name",
                      dest="host", default="")
    parser.add_option("-t", "--port", type="string",
                      help="tango host port",
                      dest="port", default="10000")

    parser.add_option("-b", "--database", action="store_true",
                      default=False, dest="database",
                      help="store datasources in "
                      "Configuration Server database")

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
