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

""" Command-line tool for ascess to the nexdatas configuration server """

import sys

import argcomplete
import argparse
from .nxsparser import ParserTools, TableTools

from .nxsdevicetools import (checkServer, listServers, openServer)


class ConfigServer(object):
    """ configuration server adapter
    """
    def __init__(self, device, nonewline=False):
        """ constructor

        :param device: device name of the configuration server
        :type device: :obj:`str`
        :param nonewline: if the output should not be separated
                          by the new line character
        :type nonewline: :obj:`bool`
        """
        #: (:obj:`str`) spliting character
        self.__char = " " if nonewline else "\n"
        #: (:class:`PyTango.DeviceProxy`) configuration server proxy
        self._cnfServer = openServer(device)
        self._cnfServer.Open()

    def _listCmd(self, ds, mandatory=False, private=False):
        """ lists the DB item names

        :param ds: flag set True for datasources
        :type ds: :obj:`bool`
        :param mandatory: flag set True for mandatory components
        :type mandatory: :obj:`bool`
        :param private: flag set True for components starting with '__'
        :type private: :obj:`bool`
        :returns: list op item names
        :rtype: :obj:`list` <:obj:`str`>
        """

        if ds:
            if not mandatory:
                return self._cnfServer.AvailableDataSources()
        else:
            if mandatory:
                return self._cnfServer.MandatoryComponents()
            elif private:
                return [cp for cp in self._cnfServer.AvailableComponents()
                        if cp.startswith("__")]
            else:
                return [cp for cp in self._cnfServer.AvailableComponents()
                        if not cp.startswith("__")]
        return []

    def _sourcesCmd(self, components, mandatory=False):
        """ lists datasources of the components

        :param components: given components
        :type components: :obj:`list` <:obj:`str`>
        :returns: list of datasource names
        :rtype: :obj:`list` <:obj:`str`>
        """
        cmps = self._cnfServer.AvailableComponents()
        result = []
        for component in components:
            if component not in cmps:
                sys.stderr.write("Error: Component '%s' not stored in "
                                 "the configuration server\n" % component)
                sys.stderr.flush()
                return []
        if not mandatory:
            for component in components:
                result.extend(self._cnfServer.ComponentDataSources(component))
        else:
            result = self._cnfServer.ComponentsDataSources(components)

        return result

    def _componentsCmd(self, components):
        """ lists components of the components

        :param components: given components
        :type components: :obj:`list` <:obj:`str`>
        :returns: list of component names
        :rtype: :obj:`list` <:obj:`str`>
        """
        cmps = self._cnfServer.AvailableComponents()
        result = []
        for component in components:
            if component not in cmps:
                sys.stderr.write("Error: Component '%s' not stored in "
                                 "the configuration server\n" % component)
                sys.stderr.flush()
                return []
        result = self._cnfServer.DependentComponents(components)

        return result

    def _variablesCmd(self, components, mandatory=False):
        """ lists variable of the components

        :param components: given components
        :type components: :obj:`list` <:obj:`str`>
        :returns: list of datasource names
        :rtype: :obj:`list` <:obj:`str`>
        """
        cmps = self._cnfServer.AvailableComponents()
        result = []
        for component in components:
            if component not in cmps:
                sys.stderr.write("Error: Component '%s' not stored in "
                                 "the configuration server\n" % component)
                sys.stderr.flush()
                return []
        if not mandatory:
            for component in components:
                result.extend(self._cnfServer.ComponentVariables(component))
        else:
            result = self._cnfServer.ComponentsVariables(components)

        return result

    def __getDataSources(self, name):
        """ provides datasources and its records for a given component

        :param name: given component or datasource
        :type name: :obj:`str`
        :returns: tuple with names and records
        :rtype: (:obj:`str` , :obj:`str`)
        """
        records = []
        names = []
        interNames = []
        xmlcp = self._cnfServer.Components([name])
        for xmlc in xmlcp:
            dslist = ParserTools.parseDataSources(xmlc)
            for ds in dslist:
                if ds["source_name"]:
                    interNames.append(ds["source_name"])
                if ds["source"]:
                    records.append(ds["source"])

            allNames = self._cnfServer.ComponentDataSources(name)
            for nm in allNames:
                if nm not in interNames:
                    names.append(nm)
        return (names, records)

    def _recordCmd(self, ds, name):
        """ lists datasources of the component

        :param ds: flag set True for datasources
        :type ds: :obj:`bool`
        :param name: given component or datasource
        :type name: :obj:`str`
        :returns: list of record names
        :rtype: :obj:`list` <:obj:`str`>
        """
        if not ds:
            cmps = self._cnfServer.AvailableComponents()
            if name not in cmps:
                sys.stderr.write("Error: Component '%s' not stored in "
                                 "the configuration server\n" % name)
                sys.stderr.flush()
                return []
            names, records = self.__getDataSources(name)
        else:
            names.append(name)

        dsrcs = self._cnfServer.AvailableDataSources()
        for nm in names:
            if nm not in dsrcs:
                sys.stderr.write("Error: Datasource '%s' not stored in "
                                 "the configuration server\n" % nm)
                sys.stderr.flush()
                return []

        xmls = self._cnfServer.DataSources(names)
        for xml in xmls:
            if xml:
                try:
                    rec = ParserTools.parseRecord(xml)
                    if rec:
                        records.append(rec)
                except:
                    sys.stderr.write(
                        "Error: Datasource '%s' cannot be parsed\n" % xml)
                    sys.stderr.write(str(sys.exc_info()[0]) + ": "
                                     + str(sys.exc_info()[1]) + '\n')
                    sys.stderr.flush()
                    return []
        return records

    def _showCmd(self, ds, args, mandatory=False):
        """ shows the DB items

        :param ds: flag set True for datasources
        :type ds: :obj:`bool`
        :param args: list of item names
        :type args: :obj:`list` <:obj:`str`>
        :param mandatory: flag set True for mandatory components
        :type mandatory: :obj:`bool`
        :returns: list of XML items
        :rtype: :obj:`list` <:obj:`str`>
        """
        if ds:
            dsrc = self._cnfServer.AvailableDataSources()
            for ar in args:
                if ar not in dsrc:
                    sys.stderr.write("Error: DataSource '%s' not stored in "
                                     "the configuration server\n" % ar)
                    sys.stderr.flush()
                    return []
            return self._cnfServer.DataSources(args)
        else:
            cmps = self._cnfServer.AvailableComponents()
            for ar in args:
                if ar not in cmps:
                    sys.stderr.write("Error: Component '%s' not stored in "
                                     "the configuration server\n" % ar)
                    sys.stderr.flush()
                    return []
            if mandatory:
                mand = list(self._cnfServer.MandatoryComponents())
                mand.extend(args)
                return self._cnfServer.Components(mand)
            else:
                return self._cnfServer.Components(args)
        return []

    def _getCmd(self, ds, args):
        """ provides final configuration

        :param ds: flag set True for datasources
        :type ds: :obj:`bool`
        :param args: list of item names
        :type args: :obj:`list` <:obj:`str`>
        :returns: XML configuration string
        :rtype: :obj:`str`
        """
        if ds:
            return ""
        else:
            cmps = self._cnfServer.AvailableComponents()
            for ar in args:
                if ar not in cmps:
                    sys.stderr.write(
                        "Error: Component '%s' not stored in "
                        "the configuration server\n" % ar)
                    sys.stderr.flush()
                    return ""
            self._cnfServer.CreateConfiguration(args)
            return self._cnfServer.XMLString
        return ""

    def __describeDataSources(self, args, headers=None):
        """ provides description of datasources

        :param args: list of item names
        :type args: :obj:`list` <:obj:`str`>
        :param headers: list of output parameters
        :type headers: :obj:`list` <:obj:`str`>
        :returns: list with description
        :rtype: :obj:`list` <:obj:`str`>
        """
        xmls = ""
        parameters = []
        description = []
        dss = self._cnfServer.AvailableDataSources()
        if not dss:
            sys.stderr.write(
                "\n'%s' does not have any datasources\n\n"
                % self._cnfServer.name())
            sys.stderr.flush()
            return ""
        for ar in args:
            if ar not in dss:
                sys.stderr.write(
                    "Error: DataSource '%s' not stored in "
                    "the configuration server\n" % ar)
                sys.stderr.flush()
                return ""
        headers = headers or ["source_type", "source"]
        if args:
            dsxmls = self._cnfServer.DataSources(args)
            for i, xmls in enumerate(dsxmls):
                parameters = ParserTools.parseDataSources(xmls)
                ttools = TableTools(parameters)
                ttools.title = "    DataSource: '%s'" % args[i]
                ttools.headers = headers
                description.extend(ttools.generateList())
        else:
            dsxmls = self._cnfServer.DataSources(dss)
            xmls = ParserTools.mergeDefinitions(dsxmls).strip()
            parameters.extend(ParserTools.parseDataSources(xmls))
            ttools = TableTools(parameters)
            headers = ["source_name"].extend(headers)
            if headers:
                ttools.headers = headers
            description.extend(ttools.generateList())

        if not description:
            sys.stderr.write(
                "\nHint: add datasource names as command arguments "
                "or -m for mandatory components \n\n")
            sys.stderr.flush()
            return ""
        return description

    def __describeComponents(self, args, headers=None, nonone=None,
                             private=False):
        """ provides description of components

        :param args: list of item names
        :type args: :obj:`list` <:obj:`str`>
        :param headers: list of output parameters
        :type headers: :obj:`list` <:obj:`str`>
        :param nonone: list of parameters which have to exist to be shown
        :type nonone: :obj:`list` <:obj:`str`>
        :param private: flag set True for components starting with '__'
        :type private: :obj:`bool`
        :returns: list with description
        :rtype: :obj:`list` <:obj:`str`>
        """
        xmls = ""
        parameters = []
        description = []
        cmps = self._cnfServer.AvailableComponents()
        if not cmps:
            sys.stderr.write(
                "\n'%s' does not have any components\n\n"
                % self._cnfServer.name())
            sys.stderr.flush()
            return ""
        for ar in args:
            if ar not in cmps:
                sys.stderr.write(
                    "Error: Component '%s' not stored in "
                    "the configuration server\n" % ar)
                sys.stderr.flush()
                return ""
        if not args:
            if private:
                args = [cp for cp in cmps if cp.startswith("__")]
            else:
                args = [cp for cp in cmps if not cp.startswith("__")]
        args = args or cmps
        if args:
            try:
                cpxmls = self._cnfServer.instantiatedComponents(args)
            except:
                cpxmls = []
                for ar in args:
                    try:
                        cpxmls.extend(
                            self._cnfServer.instantiatedComponents([ar]))
                    except:
                        cpxmls.extend(self._cnfServer.Components([ar]))
                        sys.stderr.write(
                            "Error: Component '%s' cannot be instantiated\n"
                            % ar)
                        sys.stderr.flush()

            for i, xmls in enumerate(cpxmls):
                parameters = ParserTools.parseFields(xmls)
                parameters.extend(ParserTools.parseLinks(xmls))
                ttools = TableTools(parameters, nonone)
                ttools.title = "    Component: '%s'" % args[i]
                if headers:
                    ttools.headers = headers
                description.extend(ttools.generateList())

        if not description:
            sys.stderr.write(
                "\nHint: add component names as command arguments "
                "or -m for mandatory components \n\n")
            sys.stderr.flush()
            return ""
        return description

    def __describeConfiguration(self, args, headers=None, nonone=None):
        """ provides description of final configuration

        :param args: list of item names
        :type args: :obj:`list` <:obj:`str`>
        :param headers: list of output parameters
        :type headers: :obj:`list` <:obj:`str`>
        :param nonone: list of parameters which have to exist to be shown
        :type nonone: :obj:`list` <:obj:`str`>
        :returns: list with description
        :rtype: :obj:`list` <:obj:`str`>
        """
        xmls = ""
        description = []
        cmps = self._cnfServer.AvailableComponents()
        if not cmps:
            sys.stderr.write(
                "\n'%s' does not have any components\n\n"
                % self._cnfServer.name())
            sys.stderr.flush()
            return ""
        for ar in args:
            if ar not in cmps:
                sys.stderr.write(
                    "Error: Component '%s' not stored in "
                    "the configuration server\n" % ar)
                sys.stderr.flush()
                return ""

        self._cnfServer.CreateConfiguration(args)
        xmls = str(self._cnfServer.XMLString).strip()
        if xmls:
            description.extend(ParserTools.parseFields(xmls))
            description.extend(ParserTools.parseLinks(xmls))
        if not description:
            sys.stderr.write(
                "\nHint: add components as command arguments "
                "or -m for mandatory components \n\n")
            sys.stderr.flush()
            return ""
        ttools = TableTools(description, nonone)
        if headers:
            ttools.headers = headers
        return ttools.generateList()

    def _describeCmd(self, ds, args, md, pr):
        """ provides description of configuration elements

        :param ds: flag set True for datasources
        :type ds: :obj:`bool`
        :param args: list of item names
        :type args: :obj:`list` <:obj:`str`>
        :param md: flag set True for mandatory components
        :type md: :obj:`bool`
        :param pr: flag set True for private components
        :type pr: :obj:`bool`
        :returns: list with description
        :rtype: :obj:`list` <:obj:`str`>

        """
        if ds:
            return self.__describeDataSources(args)
        elif not md:
            return self.__describeComponents(args, private=pr)
        else:
            return self.__describeConfiguration(args)

    def _infoCmd(self, ds, args, md, pr):
        """ Provides info for given elements

        :param ds: flag set True for datasources
        :type ds: :obj:`bool`
        :param args: list of item names
        :type args: :obj:`list` <:obj:`str`>
        :param md: flag set True for mandatory components
        :type md: :obj:`bool`
        :param pr: flag set True for private components
        :type pr: :obj:`bool`
        :returns: list with description
        :rtype: :obj:`list` <:obj:`str`>
        """

        cpheaders = [
            "source_name",
            "source_type",
            "nexus_type",
            "shape",
            "strategy",
            "source",
        ]
        nonone = ["source_name"]
        if ds:
            return self.__describeDataSources(args)
        elif not md:
            return self.__describeComponents(args, cpheaders, nonone, pr)
        else:
            return self.__describeConfiguration(args, cpheaders, nonone)

    def _geometryCmd(self, ds, args, md, pr):
        """ provides geometry info for given elements

        :param ds: flag set True for datasources
        :type ds: :obj:`bool`
        :param args: list of item names
        :type args: :obj:`list` <:obj:`str`>
        :param md: flag set True for mandatory components
        :type md: :obj:`bool`
        :param pr: flag set True for private components
        :type pr: :obj:`bool`
        :returns: list with description
        :rtype: :obj:`list` <:obj:`str`>
        """
        cpheaders = [
            "nexus_path",
            "source_name",
            "units",
            "trans_type",
            "trans_vector",
            "trans_offset",
            "depends_on",
        ]
        if ds:
            return []
        elif not md:
            return self.__describeComponents(args, cpheaders, private=pr)
        else:
            return self.__describeConfiguration(args, cpheaders)

    def _dataCmd(self, args):
        """ provides varaible values

        :param args: list of item names
        :type args: :obj:`list` <:obj:`str`>
        :returns: JSON with variables
        :rtype: :obj:`str`
        """
        if args and len(args) > 0 and args[0]:
            self._cnfServer.Variables = args[0]
        return [str(self._cnfServer.Variables)]

    def _mergeCmd(self, ds, args):
        """ provides merged components

        :param ds: flag set True for datasources
        :type ds: :obj:`bool`
        :param args: list of item names
        :type args: :obj:`list` <:obj:`str`>
        :returns: XML configuration string with merged components
        :rtype: :obj:`str`
        """
        if ds:
            return ""
        else:
            cmps = self._cnfServer.AvailableComponents()
            for ar in args:
                if ar not in cmps:
                    sys.stderr.write(
                        "Error: Component '%s' not stored "
                        "in the configuration server\n" % ar)
                    sys.stderr.flush()
                    return ""
            return self._cnfServer.Merge(args)
        return ""

    def performCommand(self, command, ds, args, mandatory=False,
                       private=False):
        """ performs requested command

        :param command: executed command: 'list', 'show', 'get',
                        'variables', 'sources', 'record', 'merge',
                        'components', 'data', 'describe', 'info', 'geometry'
        :type command: :obj:`str`
        :param ds: flag set True for datasources
        :type ds: :obj:`bool`
        :param args: list of item names
        :type args: :obj:`list` <:obj:`str`>
        :param mandatory: flag set True for mandatory components
        :type mandatory: :obj:`bool`
        :param private: flag set True for components starting with '__'
        :type private: :obj:`bool`
        :returns: resulting string
        :rtype: :obj:`str`

        """
        string = ""
        if command == 'list':
            string = self.__char.join(self._listCmd(ds, mandatory, private))
        elif command == 'show':
            string = self.__char.join(self._showCmd(ds, args, mandatory))
        elif command == 'get':
            string = self._getCmd(ds, args)
        elif command == 'merge':
            string = self._mergeCmd(ds, args)
        elif command == 'sources':
            string = self.__char.join(self._sourcesCmd(args, mandatory))
        elif command == 'components':
            string = self.__char.join(self._componentsCmd(args))
        elif command == 'variables':
            string = self.__char.join(self._variablesCmd(args, mandatory))
        elif command == 'data':
            string = self.__char.join(self._dataCmd(args))
        elif command == 'record':
            string = self.__char.join(self._recordCmd(ds, args[0]))
        elif command == 'describe':
            string = self.__char.join(self._describeCmd(
                ds, args, mandatory, private))
        elif command == 'info':
            string = self.__char.join(self._infoCmd(
                ds, args, mandatory, private))
        elif command == 'geometry':
            string = self.__char.join(self._geometryCmd(
                ds, args, mandatory, private))
        return string


class ErrorException(Exception):
    """ error parser exception """
    pass


class NXSConfigArgParser(argparse.ArgumentParser):
    """ Argument parser with error exception
    """

    #: (:obj:`list` <:obj:`str`>) nxsconfig sub-commands
    commands = ['list', 'show', 'get', 'variables', 'sources',
                'record', 'merge', 'components', 'data',
                'describe', 'info', 'geometry', 'servers']
    #: (:obj:`list` <:obj:`str`>) sub-commands with required argument
    argreq = ['record']
    #: (:obj:`list` <:obj:`str`>) sub-commands without private option
    noprivate = ['components', 'sources', 'variables', 'record', 'show',
                 'merge', 'get', 'data', 'merge']
    #: (:obj:`list` <:obj:`str`>) sub-commands without datasource option
    nods = ['get', 'merge', 'components', 'variables', 'data', 'servers',
            'info', 'geometry']
    #: (:obj:`list` <:obj:`str`>) sub-commands without mandatory option
    nomd = ['get', 'merge', 'components', 'data', 'record', 'servers']
    #: (:obj:`list` <:obj:`str`>) sub-commands without arguments
    noargs = ['server', 'list', 'data']

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

    @classmethod
    def _addargs(cls, parser, private=True, args=None, ds=True, md=True,
                 serverhelp=None):
        """ adds parser arguments

        :param parser: sub-parser instance
        :type parser: :class:`ArgParser`
        :param private: with private option
        :type private: :obj:`bool`
        :param args: narg string
        :type args: :obj:`str`
        :param ds: with datasources option
        :type ds: :obj:`bool`
        :param md: with mandatory option
        :type md: :obj:`bool`
        :param serverhelp: optional server help message
        :type serverhelp: :obj:`str`

        """

        parser.add_argument("-s", "--server", dest="server",
                            help=(
                                serverhelp
                                or "configuration server device name"))
        if ds:
            parser.add_argument("-d", "--datasources", action="store_true",
                                default=False, dest="datasources",
                                help="perform operation on datasources")
        if md:
            parser.add_argument("-m", "--mandatory", action="store_true",
                                default=False, dest="mandatory",
                                help="make use mandatory components")
        if private:
            parser.add_argument("-p", "--private", action="store_true",
                                default=False, dest="private",
                                help="make use private components,"
                                " i.e. starting with '__'")
        parser.add_argument("-n", "--no-newlines", action="store_true",
                            default=False, dest="nonewlines",
                            help="split result with space characters")

        if args:
            parser.add_argument('args', metavar='name', type=str, nargs=args,
                                help='names of components or datasources')

    def createParser(self):
        """ creates command-line parameters parser

        :returns: option parser
        :rtype: :class:`ArgParser`
        """

        description = "Command-line tool for reading NeXus configuration " \
                      + "from NXSConfigServer"

        #: (:obj:`str`) usage example
        hlp = {
            "list": "list names of available components (or datasources)",
            "show": "show components (or datasources) with given names",
            "get": "get full configuration of components (or datasources)",
            "merge": "get merged configuration of components (or datasources)",
            "sources": "get a list of component datasources",
            "components": "get a list of dependent components",
            "variables": "get a list of component variables",
            "data": "get/set values of component variables",
            "record": "get a list of datasource record names",
            "servers": "get a list of configuration servers from"
            + " the current tango host",
            "describe": "show all parameters of given components"
            + " (or datasources)",
            "info": "show source parameters of given components"
            + " (or datasources)",
            "geometry": "show transformation parameters of given components"
            + " (or datasources)",
        }

        self.description = description
        self.epilog = 'For more help:\n  nxsconfig <sub-command> -h'

        pars = {}
        subparsers = self.add_subparsers(
            help='sub-command help', dest="subparser")
        for cmd in self.commands:
            pars[cmd] = subparsers.add_parser(
                cmd, help='%s' % hlp[cmd], description=hlp[cmd])
            self._addargs(
                pars[cmd],
                cmd not in self.noprivate,
                None if cmd in self.noargs else '*',
                cmd not in self.nods,
                cmd not in self.nomd,
                "tango host or configuration server"
                if cmd == 'servers' else None
            )

        pars['data'].add_argument('args', metavar='name', type=str, nargs='?',
                                  help='data dictionary in json string')
        self.subparsers = pars
        return pars


def main():
    """ the main program function
    """
    #: pipe arguments
    pipe = []
    if not sys.stdin.isatty():
        #: system pipe
        pipe = sys.stdin.readlines()

    parser = NXSConfigArgParser(
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
        print("\n".join(listServers(options.server, 'NXSConfigServer')))
        return

    if not options.server:
        options.server = checkServer()

    if not options.server:
        pars[options.subparser].print_help()
        print("")
        sys.exit(255)

    #: command-line and pipe arguments
    parg = []
    if hasattr(options, "args"):
        if not isinstance(options.args, list):
            options.args = [options.args] if options.args else []
        parg = options.args or []
    if pipe:
        parg.extend([p.strip() for p in pipe])
        options.args[:] = parg

    if len(parg) < (
            1 if options.subparser in NXSConfigArgParser.argreq else 0):
        pars[options.subparser].print_help()
        return

    #: configuration server
    cnfserver = ConfigServer(options.server, options.nonewlines)

    #: result to print
    result = cnfserver.performCommand(
        options.subparser,
        options.datasources if hasattr(options, "datasources") else None,
        options.args if hasattr(options, "args") else None,
        options.mandatory if hasattr(options, "mandatory") else None,
        options.private if hasattr(options, "private") else None,
    )

    #: result to print
    if result.strip():
        print(result)


if __name__ == "__main__":
    main()
