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

import argcomplete
import argparse

from .nxsdevicetools import (checkServer, listServers, openServer)


class NexusServer(object):
    """ configuration server adapter
    """

    def __init__(self, device):
        """ constructor

        :param device: device name of configuration server
        :type device: :obj:`str`
        """
        #: (:class:`PyTango.DeviceProxy`) NeXus writer device proxy
        self.tdwServer = openServer(device)

    def openFile(self, filename):
        """ opens the h5 file

        :param filename: h5 file name
        :type filename: :obj:`str`
        """
        self.tdwServer.Init()
        self.tdwServer.FileName = str(filename)
        self.tdwServer.OpenFile()

    def setData(self, jsondata):
        """ sets the global JSON data

        :param jsondata: global JSON data
        :type jsondata: :obj:`str`
        """
        self.tdwServer.JSONRecord = str(jsondata)

    def openEntry(self, xmlconfig):
        """ opens an entry

        :param xmlconfig: xml configuration string
        :type xmlconfig: :obj:`str`
        """
        self.tdwServer.XMLSettings = str(xmlconfig)
        self.tdwServer.OpenEntry()

    def record(self, jsondata):
        """ records one step

        :param jsondata: step JSON data
        :type jsondata: :obj:`str`
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
        :type command: :obj:`str`
        :param args: list of item names
        :type args: :obj:`list` <:obj:`str`>
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

class ErrorException(Exception):
    """ error parser exception """
    pass


class NXSDataArgParser(argparse.ArgumentParser):
    """ Argument parser with error exception
    """

    #: (:obj:`list` <:obj:`str`>) nxsdata sub-commands
    commands = ['openfile', 'openentry', 'setdata', 'record',
                'closeentry', 'closefile']
    #: (:obj:`list` <:obj:`str`>) sub-commands with required argument
    argreq = ['openfile', 'setdata', 'record' ]
    #: (:obj:`list` <:obj:`str`>) sub-commands without arguments
    noargs = ['server', 'closeentry', 'closefile']

    def __init__(self, **kwargs):
        """ constructor 
        
        :param kwargs: :class:`argparse.ArgumentParser`
                       parameter dictionary 
        :type kwargs: :obj: `dict` <:obj:`str`, `any`>
        """
        argparse.ArgumentParser.__init__(self, **kwargs)
        self.subparsers = {}

    def error(self, message):
        """ error handler

        :param message: error message
        :type message: :obj:`str`
        """
        raise ErrorException(message)




    def createParser(self):
        """ creates command-line parameters parser

        :returns: option parser
        :rtype: :class:`NXSDataArgParser`
        """
        #: usage example
        description  = "Command-line tool for writing NeXus files with NXSDataWriter"
        #    \
        #            + " e.g.: nxsdata openfile -s p02/tangodataserver/exp.01  " \
        #            + "/user/data/myfile.h5"

        hlp = {
            "openfile": "open a new H5 file",
            "setdata": "assign global JSON data",
            "openentry": "create new entry",
            "record": "record one step with step JSON data",
            "closeentry": "close the current entry",
            "closefile": "close the current file",
            "servers": "get lists of tango data servers from "
            "the current tango host",
        }

        self.description = description
        self.epilog = 'For more help:\n  nxsdata <sub-command> -h'

        pars = {}
        subparsers = self.add_subparsers(
            help='sub-command help', dest="subparser")


        for cmd in self.commands:
            pars[cmd] = subparsers.add_parser(
                cmd, help='%s' % hlp[cmd], description=hlp[cmd])

            pars[cmd].add_argument(
                "-s", "--server", dest="server",
                help=("tango host or writer server" if cmd=='servers' else
                      "writer server device name")
            )

        pars['openfile'].add_argument('args', metavar='file_name', type=str, nargs='?',
                                  help='new newxus file name')
        pars['openentry'].add_argument('args', metavar='xml_config', type=str, nargs='?',
                                  help='nexus writer configuration string')
        pars['setdata'].add_argument('args', metavar='json_data_string', type=str, nargs='?',
                                  help='json data string')
        pars['record'].add_argument('args', metavar='json_data_string', type=str, nargs='?',
                                  help='json data string')
        self.subparsers = pars
        return pars


def main():
    """ the main function
    """

    #: pipe arguments
    pipe = ""
    if not sys.stdin.isatty():
        pp = sys.stdin.readlines()
        #: system pipe
        pipe = "".join(pp)

    parser = NXSDataArgParser(
        formatter_class=argparse.RawDescriptionHelpFormatter)
    pars = parser.createParser()

    argcomplete.autocomplete(parser)

    try:
        options = parser.parse_args()
    except ErrorException as e:
        sys.stderr.write("Error: %s\n" % str(e))
        sys.stderr.flush()
        parser.print_help()
        print("")
        sys.exit(255)

    if options.subparser == 'servers':
        print("\n".join(listServers(options.server, 'NXSDataWriter')))
        return

    if not options.server:
        options.server = checkServer('NXSDataWriter')

    if not options.server:
        pars[options.subparser].print_help()
        print("")
        sys.exit(255)

    #: configuration server
    tdwserver = NexusServer(options.server)

    #: command-line and pipe arguments
    parg = []
    if hasattr(options, "args"):
        print type(options.args), options.args
        parg = [options.args]  if options.args else []
    if pipe:
        parg.append(pipe)

    if len(parg) < (1 if options.subparser in NXSDataArgParser.argreq else 0):
        pars[options.subparser].print_help()
        return

    #: result to print
    result = tdwserver.performCommand(options.subparser, parg)
    if result and str(result).strip():
        print result


if __name__ == "__main__":
    main()
