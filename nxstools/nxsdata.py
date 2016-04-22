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

""" Command-line tool to ascess to Tango Data Server"""

import sys

from optparse import OptionParser

from .nxsdevicetools import (checkServer, listServers, openServer)


class NexusServer(object):
    """ configuration server adapter
    """

    def __init__(self, device):
        """ constructor

        :param device: device name of configuration server
        """
        self.tdwServer = openServer(device)

    def openFile(self, filename):
        """ opens the h5 file

        :param filename: h5 file name
        """
        self.tdwServer.Init()
        self.tdwServer.FileName = str(filename)
        self.tdwServer.OpenFile()

    def setData(self, jsondata):
        """ sets the global JSON data

        :param jsondata: global JSON data
        """
        self.tdwServer.JSONRecord = str(jsondata)

    def openEntry(self, xmlconfig):
        """ opens an entry

        :param xmlconfig: xml configuration string
        """
        self.tdwServer.XMLSettings = str(xmlconfig)
        self.tdwServer.OpenEntry()

    def record(self, jsondata):
        """ records one step

        :param jsondata: step JSON data
        """
        self.tdwServer.Record(jsondata)

    def closeEntry(self):
        """ closes the entry
        """
        self.tdwServer.CloseEntry()

    def closeFile(self):
        """ closes the file

        """
        self.tdwServer.CloseFile()

    def performCommand(self, command, args):
        """ perform requested command

        :param command: called command
        :param args: list of item names
        """
        if command == 'openfile':
            return self.openFile(args[0])
        if command == 'setdata':
            return self.setData(args[0].strip())
        if command == 'openentry':
            return self.openEntry(args[0].strip())
        if command == 'record':
            return self.record(args[0].strip())
        if command == 'closefile':
            return self.closeFile()
        if command == 'closeentry':
            return self.closeEntry()


def _createParser():
    """ creates command-line parameters parser
    """
    #: usage example
    usage = "usage: nxsdata <command> [-s <nexus_server>] " \
            + " [<arg1> [<arg2>  ...]] \n" \
            + " e.g.: nxsdata openfile -s p02/tangodataserver/exp.01  " \
            + "$HOME/myfile.h5 \n\n" \
            + "Commands: \n" \
            + "   openfile [-s <nexus_server>]  <file_name> \n" \
            + "          open new H5 file\n" \
            + "   setdata [-s <nexus_server>] <json_data_string>  \n" \
            + "          assign global JSON data\n" \
            + "   openentry [-s <nexus_server>] <xml_config>  \n" \
            + "          create new entry\n"\
            + "   record [-s <nexus_server>]  <json_data_string>  \n" \
            + "          record one step with step JSON data \n" \
            + "   closeentry [-s <nexus_server>]   \n" \
            + "          close the current entry \n" \
            + "   closefile [-s <nexus_server>]  \n" \
            + "          close the current file \n" \
            + "   servers [-s <nexus_server/host>] \n" \
            + "          get lists of tango data servers from " \
            + "the current tango host\n" \
            + " "

    #: option parser
    parser = OptionParser(usage=usage)
    parser.add_option("-s", "--server", dest="server",
                      help="tango data server device name")

    return parser


def main():
    """ the main function
    """

    #: pipe arguments
    pipe = ""
    if not sys.stdin.isatty():
        pp = sys.stdin.readlines()
        #: system pipe
        pipe = "".join(pp)

    commands = {'openfile': 1, 'openentry': 0, 'setdata': 1, 'record': 1,
                'closeentry': 0, 'closefile': 0}
    #: run options
    options = None
    parser = _createParser()
    (options, args) = parser.parse_args()

    if args and args[0] == 'servers':
        print "\n".join(listServers(options.server, 'NXSDataWriter'))
        return

    if not options.server:
        options.server = checkServer('NXSDataWriter')

    if not args or args[0] not in commands or not options.server:
        parser.print_help()
        print ""
        sys.exit(0)

    #: configuration server
    tdwserver = NexusServer(options.server)

    #: command-line and pipe arguments
    parg = args[1:]
    if pipe:
        parg.append(pipe)

    if len(parg) < commands[args[0]]:
        print "CMD", args[0], len(parg)
        parser.print_help()
        print ""
        sys.exit(0)

    #: result to print
    result = tdwserver.performCommand(args[0], parg)
    if result and str(result).strip():
        print result


if __name__ == "__main__":
    main()
