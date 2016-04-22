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

""" component creator """

import sys

from optparse import OptionParser
from nxstools.nxsdevicetools import checkServer
from nxstools.nxscreator import (ComponentCreator, WrongParameterError)


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
    usage = "usage: %prog [options] [name1] [name2]\n" \
        + "       nxscreate comp [options] [name1] [name2]\n"
    #: option parser
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

    parser.add_option("-d", "--directory", type="string",
                      help="output component directory",
                      dest="directory", default=".")
    parser.add_option("-x", "--file-prefix", type="string",
                      help="file prefix, i.e. counter",
                      dest="file", default="")

    parser.add_option("-n", "--nexuspath", type="string",
                      help="nexus path with field name",
                      dest="nexuspath", default="")

    parser.add_option("-s", "--strategy", type="string",
                      help="writing strategy, i.e. "
                      "STEP, INIT, FINAL, POSTRUN",
                      dest="strategy", default="STEP")
    parser.add_option("-t", "--type", type="string",
                      help="nexus type of the field",
                      dest="type", default="NX_FLOAT")
    parser.add_option("-u", "--units", type="string",
                      help="nexus units of the field",
                      dest="units", default="")

    parser.add_option("-k", "--links", action="store_true",
                      default=False, dest="fieldlinks",
                      help="create links with field name")

    parser.add_option("-i", "--source-links", action="store_true",
                      default=False, dest="sourcelinks",
                      help="create links with datasource name")

    parser.add_option("-b", "--database", action="store_true",
                      default=False, dest="database",
                      help="store components in Configuration Server database")

    parser.add_option("-r", "--server", dest="server",
                      help="configuration server device name")

    parser.add_option("-c", "--chunk", dest="chunk",
                      default="SCALAR", help="chunk format, "
                      "i.e. SCALAR, SPECTRUM, IMAGE")

    parser.add_option("-m", "--minimal_device", action="store_true",
                      default=False, dest="minimal",
                      help="device name without first '0'")

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

    if options.database and not options.server:
        if not PYTANGO:
            sys.stderr.write("CollCompCreator No PyTango installed\n")
            parser.print_help()
            sys.exit(255)

        options.server = checkServer()
        if not options.server:
            parser.print_help()
            print("")
            sys.exit(0)

    if options.database:
        print("CONFIG SERVER: %s" % options.server)
    else:
        print("OUTPUT DIRECTORY: %s" % options.directory)

    creator = ComponentCreator(options, args)
    try:
        creator.create()
    except WrongParameterError as e:
        sys.stderr.write(str(e))
        parser.print_help()
        sys.exit(255)

if __name__ == "__main__":
    main()
