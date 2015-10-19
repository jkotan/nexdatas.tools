#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2015 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \package nexdatas nexdatas.tools
## \file nxsconfig.py
# Command-line tool for ascess to the nexdatas configuration server
#

""" Command-line tool for ascess to the nexdatas configuration server """

import sys

from optparse import OptionParser
from xml.dom.minidom import parseString

from .nxsdevicetools import (checkServer, listServers, openServer)


## configuration server adapter
class ConfigServer(object):
    ## constructor
    # \param device device name of configuration server
    # \param nonewline no newline flag
    def __init__(self, device, nonewline=False):
        ## spliting character
        self.__char = " " if nonewline else "\n"
        self.cnfServer = openServer(device)
        self.cnfServer.Open()

    ## provides  xml content of the node
    # \param node DOM node
    # \returns xml content string
    @classmethod
    def getText(cls, node):
        if not node:
            return
        xml = node.toxml()
        start = xml.find('>')
        end = xml.rfind('<')
        if start == -1 or end < start:
            return ""
        return xml[start + 1:end].replace("&lt;", "<").replace("&gt;", ">"). \
            replace("&quot;", "\"").replace("&amp;", "&")

    ## lists the DB item names
    # \param ds flag set True for datasources
    # \param mandatory flag set True for mandatory components
    # \returns list op item names
    def listCmd(self, ds, mandatory=False):
        if ds:
            if not mandatory:
                return self.cnfServer.AvailableDataSources()
        else:
            if mandatory:
                return self.cnfServer.MandatoryComponents()
            else:
                return self.cnfServer.AvailableComponents()
        return []

    ## lists datasources of the components
    # \param components given components
    # \returns list of datasource names
    def sourcesCmd(self, components, mandatory=False):
        cmps = self.cnfServer.AvailableComponents()
        result = []
        for component in components:
            if component not in cmps:
                sys.stderr.write("Error: Component %s not stored in "
                                 "the configuration server\n" % component)
                sys.stderr.flush()
                return []
        if not mandatory:
            for component in components:
                result.extend(self.cnfServer.ComponentDataSources(component))
        else:
            result = self.cnfServer.ComponentsDataSources(components)

        return result

    ## lists components of the components
    # \param components given components
    # \returns list of component names
    def componentsCmd(self, components):
        cmps = self.cnfServer.AvailableComponents()
        result = []
        for component in components:
            if component not in cmps:
                sys.stderr.write("Error: Component %s not stored in "
                                 "the configuration server\n" % component)
                sys.stderr.flush()
                return []
        result = self.cnfServer.DependentComponents(components)

        return result

    ## lists variable of the components
    # \param components given components
    # \returns list of datasource names
    def variablesCmd(self, components, mandatory=False):
        cmps = self.cnfServer.AvailableComponents()
        result = []
        for component in components:
            if component not in cmps:
                sys.stderr.write("Error: Component %s not stored in "
                                 "the configuration server\n" % component)
                sys.stderr.flush()
                return []
        if not mandatory:
            for component in components:
                result.extend(self.cnfServer.ComponentVariables(component))
        else:
            result = self.cnfServer.ComponentsVariables(components)

        return result

    ## fetches record name or query from datasource node
    # \param node datasource node
    # \returns record name or query
    @classmethod
    def getRecord(cls, node):
        withRec = ["CLIENT", "TANGO"]
        withQuery = ["DB"]
        if node.nodeName == 'datasource':
            dsource = node
        else:
            dsource = node.getElementsByTagName("datasource")[0] \
                if len(node.getElementsByTagName("datasource")) else None
        dstype = dsource.attributes["type"] \
            if dsource and dsource.hasAttribute("type") else None
        if dstype.value in withRec:
            rec = dsource.getElementsByTagName("record")[0] \
                if dsource and len(dsource.getElementsByTagName("record")) \
                else None
            rc = rec.attributes["name"] if rec.hasAttribute("name") else None
            if rc:
                return rc.value
        elif dstype.value in withQuery:
            query = cls.getText(dsource.getElementsByTagName("query")[0]) \
                if len(dsource.getElementsByTagName("query")) else None
            if query and query.strip():
                return query.strip()

    ## provides datasources and its records for a given component
    # \param name given component or datasource
    # \returns tuple with names and records
    def __getDataSources(self, name):
        records = []
        names = []
        interNames = []
        xmlcp = self.cnfServer.Components([name])
        for xmlc in xmlcp:
            indom = parseString(xmlc)
            dsources = indom.getElementsByTagName("datasource")
            for dsrc in dsources:
                dsname = dsrc.attributes["name"] \
                    if dsrc and dsrc.hasAttribute("name") else None
                if dsname and dsname.value:
                    interNames.append(dsname.value)
                    rec = self.getRecord(dsrc)
                    if rec:
                        records.append(rec)

            allNames = self.cnfServer.ComponentDataSources(name)
            for nm in allNames:
                if nm not in interNames:
                    names.append(nm)
        return (names, records)

    ## lists datasources of the component
    # \param ds flag set True for datasources
    # \param name given component or datasource
    # \returns list of record names
    def recordCmd(self, ds, name):
        if not ds:
            cmps = self.cnfServer.AvailableComponents()
            if name not in cmps:
                sys.stderr.write("Error: Component %s not stored in "
                                 "the configuration server\n" % name)
                sys.stderr.flush()
                return []
            names, records = self.__getDataSources(name)
        else:
            names.append(name)

        dsrcs = self.cnfServer.AvailableDataSources()
        for nm in names:
            if nm not in dsrcs:
                sys.stderr.write("Error: Datasource %s not stored in "
                                 "the configuration server\n" % nm)
                sys.stderr.flush()
                return []

        xmls = self.cnfServer.DataSources(names)
        for xml in xmls:
            if xml:
                try:
                    indom = parseString(xml)
                    rec = self.getRecord(indom)
                    if rec:
                        records.append(rec)

                except:
                    sys.stderr.write(
                        "Error: Datasource %s cannot be parsed\n" % xml)
                    sys.stderr.write(str(sys.exc_info()[0]) + ": "
                                     + str(sys.exc_info()[1]) + '\n')
                    sys.stderr.flush()
                    return []
        return records

    ## shows the DB items
    # \param ds flag set True for datasources
    # \param args list of item names
    # \param mandatory flag set True for mandatory components
    # \returns list of XML items
    def showCmd(self, ds, args, mandatory=False):
        if ds:
            dsrc = self.cnfServer.AvailableDataSources()
            for ar in args:
                if ar not in dsrc:
                    sys.stderr.write("Error: DataSource %s not stored in "
                                     "the configuration server\n" % ar)
                    sys.stderr.flush()
                    return []
            return self.cnfServer.DataSources(args)
        else:
            cmps = self.cnfServer.AvailableComponents()
            for ar in args:
                if ar not in cmps:
                    sys.stderr.write("Error: Component %s not stored in "
                                     "the configuration server\n" % ar)
                    sys.stderr.flush()
                    return []
            if mandatory:
                mand = list(self.cnfServer.MandatoryComponents())
                mand.extend(args)
                return self.cnfServer.Components(mand)
            else:
                return self.cnfServer.Components(args)
        return []

    ## Provides final configuration
    # \param ds flag set True for datasources
    # \param args list of item names
    # \returns XML configuration string
    def getCmd(self, ds, args):
        if ds:
            return ""
        else:
            cmps = self.cnfServer.AvailableComponents()
            for ar in args:
                if ar not in cmps:
                    sys.stderr.write(
                        "Error: Component %s not stored in "
                        "the configuration server\n" % ar)
                    sys.stderr.flush()
                    return ""
            self.cnfServer.CreateConfiguration(args)
            return self.cnfServer.XMLString
        return ""

    ## Provides varaible values
    # \param args list of item names
    # \returns JSON with variables
    def dataCmd(self, args):
        if len(args) > 0:
            self.cnfServer.Variables = args[0]
        return [str(self.cnfServer.Variables)]

    ## Provides merged components
    # \param ds flag set True for datasources
    # \param args list of item names
    # \returns XML configuration string with merged components
    def mergeCmd(self, ds, args):
        if ds:
            return ""
        else:
            cmps = self.cnfServer.AvailableComponents()
            for ar in args:
                if ar not in cmps:
                    sys.stderr.write(
                        "Error: Component %s not stored "
                        "in the configuration server\n" % ar)
                    sys.stderr.flush()
                    return ""
            return self.cnfServer.Merge(args)
        return ""

    ## perform requested command
    # \param command called command
    # \param ds flag set True for datasources
    # \param args list of item names
    # \param mandatory flag set True for mandatory components
    # \returns resulting string
    def performCommand(self, command, ds, args, mandatory=False):
        string = ""
        if command == 'list':
            string = self.__char.join(self.listCmd(ds, mandatory))
        elif command == 'show':
            string = self.__char.join(self.showCmd(ds, args, mandatory))
        elif command == 'get':
            string = self.getCmd(ds, args)
        elif command == 'merge':
            string = self.mergeCmd(ds, args)
        elif command == 'sources':
            string = self.__char.join(self.sourcesCmd(args, mandatory))
        elif command == 'components':
            string = self.__char.join(self.componentsCmd(args))
        elif command == 'variables':
            string = self.__char.join(self.variablesCmd(args, mandatory))
        elif command == 'data':
            string = self.__char.join(self.dataCmd(args))
        elif command == 'record':
            string = self.__char.join(self.recordCmd(ds, args[0]))
        return string


## creates command-line parameters parser
def createParser():
    ## usage example
    usage = "usage: nxsconfig <command> [-s <config_server>] " \
            + " [-d] [-m] [<name1>] [<name2>] [<name3>] ... \n" \
            + " e.g.: nxsconfig list -s p02/xmlconfigserver/exp.01 -d\n\n" \
            + "Commands: \n" \
            + "   list [-s <config_server>] [-m]  \n" \
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
            + " "

    ## option parser
    parser = OptionParser(usage=usage)
    parser.add_option("-s", "--server", dest="server",
                      help="configuration server device name")
    parser.add_option("-d", "--datasources", action="store_true",
                      default=False, dest="datasources",
                      help="perform operation on datasources")
    parser.add_option("-m", "--mandatory", action="store_true",
                      default=False, dest="mandatory",
                      help="make use mandatory components as well")
    parser.add_option("-n", "--no-newlines", action="store_true",
                      default=False, dest="nonewlines",
                      help="split result with space characters")

    return parser


## the main function
def main():
    ## pipe arguments
    pipe = []
    ## run options
    options = None
    if not sys.stdin.isatty():
        ## system pipe
        pipe = sys.stdin.readlines()

    commands = {'list': 0, 'show': 0, 'get': 0, 'variables': 0, 'sources': 0,
                'record': 1, 'merge': 0, 'components': 0, 'data': 0}

    parser = createParser()
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

    ## command-line and pipe arguments
    parg = args[1:]
    if pipe:
        parg.extend([p.strip() for p in pipe])

    if len(parg) < commands[args[0]]:
        parser.print_help()
        return

    ## configuration server
    cnfserver = ConfigServer(options.server, options.nonewlines)

    ## result to print
    result = cnfserver.performCommand(args[0], options.datasources,
                                      parg, options.mandatory)
    if result.strip():
        print(result)


if __name__ == "__main__":
    main()
