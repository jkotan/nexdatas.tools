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

from optparse import OptionParser
from .nxsparser import ParserTools, TableTools

from .nxsdevicetools import (checkServer, listServers, openServer)


##
class ConfigServer(object):
    """ configuration server adapter
    """
    def __init__(self, device, nonewline=False):
        """ constructor

        :param device: device name of the configuration server
        :param nonewline: if the output should not be separated
                          by the new line character
        """
        #: spliting character
        self.__char = " " if nonewline else "\n"
        #: configuration server proxy
        self._cnfServer = openServer(device)
        self._cnfServer.Open()

    def _listCmd(self, ds, mandatory=False, private=False):
        """ lists the DB item names

        :param ds: flag set True for datasources
        :param mandatory: flag set True for mandatory components
        :param private: flag set True for components starting with '__'
        :returns: list op item names

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
        :returns: list of datasource names
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
        :returns: list of component names
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
        :returns: list of datasource names
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
        :returns: tuple with names and records
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
        :param name: given component or datasource
        :returns: list of record names
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
        :param args: list of item names
        :param mandatory: flag set True for mandatory components
        :returns: list of XML items
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
        :param args: list of item names
        :returns: XML configuration string
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
        :param headers: list of output parameters
        :returns: list with description
        """
        xmls = ""
        parameters = []
        description = []
        dss = self._cnfServer.AvailableDataSources()
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
            xmls = ParserTools.addDefinitions(dsxmls).strip()
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
        :param headers: list of output parameters
        :param nonone: list of parameters which have to exist to be shown
        :param private: flag set True for components starting with '__'
        :returns: list with description
        """
        xmls = ""
        parameters = []
        description = []
        cmps = self._cnfServer.AvailableComponents()
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
        :param headers: list of output parameters
        :param nonone: list of parameters which have to exist to be shown
        :returns: list with description
        """
        xmls = ""
        description = []
        cmps = self._cnfServer.AvailableComponents()
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
        :param args: list of item names
        :param md: flag set True for mandatory components
        :param pr: flag set True for private components
        :returns: list with description

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
        :param args: list of item names
        :param md: flag set True for mandatory components
        :param pr: flag set True for private components
        :returns: list with description
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
        :param args: list of item names
        :param md: flag set True for mandatory components
        :param pr: flag set True for private components
        :returns: list with description
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
        :returns: JSON with variables
        """
        if len(args) > 0:
            self._cnfServer.Variables = args[0]
        return [str(self._cnfServer.Variables)]

    def _mergeCmd(self, ds, args):
        """ provides merged components

        :param ds: flag set True for datasources
        :param args: list of item names
        :returns: XML configuration string with merged components
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
        :param ds: flag set True for datasources
        :param args: list of item names
        :param mandatory: flag set True for mandatory components
        :param private: flag set True for components starting with '__'
        :returns: resulting string

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


def _createParser():
    """ creates command-line parameters parser
    """
    #: usage example
    usage = "usage: nxsconfig <command> [-s <config_server>] " \
            + " [-d] [-m] [<name1>] [<name2>] [<name3>] ... \n" \
            + " e.g.: nxsconfig list -s p02/xmlconfigserver/exp.01 -d\n\n" \
            + "Commands: \n" \
            + "   list [-s <config_server>] [-m | -p] \n" \
            + "          list names of available components\n" \
            + "   list -d [-s <config_server>] \n" \
            + "          list names of available datasources\n" \
            + "   show [-s <config_server>] [-m] component_name1 " \
            + "component_name2 ...  \n" \
            + "          show components with given names \n" \
            + "   show -d [-s <config_server>] dsource_name1 "  \
            + "dsource_name2 ...  \n" \
            + "          show datasources with given names \n" \
            + "   get [-s <config_server>]  [-m] component_name1 " \
            + "component_name2 ...  \n" \
            + "          get merged configuration of components \n" \
            + "   sources [-s <config_server>] [-m] component_name1 " \
            + "component_name2 ... \n" \
            + "          get a list of component datasources \n" \
            + "   components [-s <config_server>] component_name1 " \
            + "component_name2 ... \n" \
            + "          get a list of dependent components \n" \
            + "   variables [-s <config_server>] [-m] component_name1 " \
            + "component_name2 ... \n" \
            + "          get a list of component variables \n" \
            + "   data [-s <config_server>] json_data \n" \
            + "          set values of component variables \n" \
            + "   record [-s <config_server>]  component_name1  \n" \
            + "          get a list of datasource record names " \
            + "from component\n" \
            + "   record -d [-s <config_server>] datasource_name1  \n" \
            + "          get a list of datasource record names   \n" \
            + "   servers [-s <config_server/host>] \n" \
            + "          get lists of configuration servers from " \
            + "the current tango host\n"\
            + "   describe [-s <config_server>] [-m | -p] component_name1 " \
            + "component_name2 ...  \n" \
            + "          show all parameters of given components \n" \
            + "   describe|info -d [-s <config_server>] dsource_name1 "  \
            + "dsource_name2 ...  \n" \
            + "          show all parameters of given datasources \n" \
            + "   info [-s <config_server>] [-m | -p] component_name1 " \
            + "component_name2 ...  \n" \
            + "          show source parameters of given components \n" \
            + "   geometry [-s <config_server>] [-m | -p] component_name1 " \
            + "component_name2 ...  \n" \
            + "          show transformation parameters " \
            + "of given components \n"

    #: option parser
    parser = OptionParser(usage=usage)
    parser.add_option("-s", "--server", dest="server",
                      help="configuration server device name")
    parser.add_option("-d", "--datasources", action="store_true",
                      default=False, dest="datasources",
                      help="perform operation on datasources")
    parser.add_option("-m", "--mandatory", action="store_true",
                      default=False, dest="mandatory",
                      help="make use mandatory components")
    parser.add_option("-p", "--private", action="store_true",
                      default=False, dest="private",
                      help="make use private components,"
                      " i.e. starting with '__'")
    parser.add_option("-n", "--no-newlines", action="store_true",
                      default=False, dest="nonewlines",
                      help="split result with space characters")

    return parser


def main():
    """ the main program function
    """
    #: pipe arguments
    pipe = []
    #: run options
    options = None
    if not sys.stdin.isatty():
        #: system pipe
        pipe = sys.stdin.readlines()

    commands = {'list': 0, 'show': 0, 'get': 0, 'variables': 0, 'sources': 0,
                'record': 1, 'merge': 0, 'components': 0, 'data': 0,
                'describe': 0, 'info': 0, 'geometry': 0}

    parser = _createParser()
    (options, args) = parser.parse_args()

    if args and args[0] == 'servers':
        print("\n".join(listServers(options.server, 'NXSConfigServer')))
        return

    if not options.server:
        options.server = checkServer()

    if not args or args[0] not in commands or not options.server:
        parser.print_help()
        print("")
        sys.exit(0)

    #: command-line and pipe arguments
    parg = args[1:]
    if pipe:
        parg.extend([p.strip() for p in pipe])

    if len(parg) < commands[args[0]]:
        parser.print_help()
        return

    #: configuration server
    cnfserver = ConfigServer(options.server, options.nonewlines)

    #: result to print
    result = cnfserver.performCommand(
        args[0], options.datasources, parg,
        options.mandatory, options.private)
    if result.strip():
        print(result)


if __name__ == "__main__":
    main()
