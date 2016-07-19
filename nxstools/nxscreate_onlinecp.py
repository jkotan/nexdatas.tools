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

""" component creator from online files """

import sys
import os

from nxstools.nxsdevicetools import checkServer
from nxstools.nxscreator import OnlineCPCreator, CPExistsException

PYTANGO = False
try:
    import PyTango
    PYTANGO = True
except:
    pass

from optparse import OptionParser


def main():
    """ the main function
    """
    #: usage example
    usage = "usage: %prog onlinecp [options] [<inputFile>]\n" \
        + " e.g.\n" \
        + "       nxscreate onlinecp  \n" \
        + "       nxscreate onlinecp -c pilatus \n" \
        + "       nxscreate onlinecp -c lambda -d /home/user/xmldir/ \n\n" \
        + " - without '-c <component>': show a list of possible components\n" \
        + " - without '-d <dircetory>:  components are created in " \
        + "Configuration Server database\n" \
        + " - with -d <directory>: components are created" \
        + " on the local filesystem\n" \
        + " - default: <inputFile> is '/online_dir/online.xml' \n" \
        + "            <server> is taken from Tango DB\n"

    #: option parser
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--component", type="string",
                      help="component name" +
                      "related to the device name from <inputFile>",
                      dest="component", default="")
    parser.add_option("-r", "--server", dest="server",
                      help="configuration server device name")
    parser.add_option("-n", "--nolower", action="store_false",
                      default=True, dest="lower",
                      help="do not change aliases into lower case")
    parser.add_option("-o", "--overwrite", action="store_true",
                      default=False, dest="overwrite",
                      help="overwrite existing component")
    parser.add_option("-d", "--directory", type="string",
                      help="output directory where datasources will be stored."
                      " If it is not set components are stored in "
                      "Configuration Server database",
                      dest="directory", default="")
    parser.add_option("-x", "--file-prefix", type="string",
                      help="file prefix, i.e. counter",
                      dest="file", default="")
    parser.add_option("-p", "--xml-package", dest="xmlpackage",
                      help="xml template package")

    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        sys.exit(255)
    else:
        args = args[1:]

    if not PYTANGO:
        sys.stderr.write("nxscreate: No PyTango installed\n")
        parser.print_help()
        sys.exit(255)

    if not options.server:
        options.server = checkServer()
        if not options.server:
            parser.print_help()
            print("")
            sys.exit(0)
    if not len(args) and os.path.isfile('/online_dir/online.xml'):
        args = ['/online_dir/online.xml']

    if not len(args):
        parser.print_help()
        sys.exit(255)

    print("INPUT: %s" % args[0])
    if options.directory:
        print("OUTPUT DIR: %s" % options.directory)
    else:
        print("SERVER: %s" % options.server)

    creator = OnlineCPCreator(options, args)
    if options.component:
        try:
            creator.create()
        except CPExistsException as e:
            print(str(e))
    else:
        lst = creator.listcomponents()
        print("\nPOSSIBLE COMPONENTS: \n   %s" % " ".join(list(lst)))


if __name__ == "__main__":
    main()
