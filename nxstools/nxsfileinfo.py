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

""" Command-line tool for showing meta data from Nexus Files"""

import sys
import argparse

from .nxsparser import TableTools
from .nxsfileparser import NXSFileParser
from .nxsargparser import (Runner, NXSArgParser, ErrorException)


#: (:obj:`bool`) True if pni.io.nx.h5 available
PNIIO = False
try:
    import pni.io.nx.h5 as nx
    PNIIO = True
except:
    pass


class General(Runner):
    """ General runner"""

    #: (:obj:`str`) command description
    description = "show general information for the nexus file"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxsfileinfo general /user/data/myfile.nxs\n" \
        + "\n"

    def postauto(self):
        """ parser creator after autocomplete run """
        self._parser.add_argument(
            'args', metavar='nexus_file', type=str, nargs=1,
            help='new nexus file name')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :returns: output information
        :rtype: :obj:`str`
        """
        try:
            fl = nx.open_file(options.args[0])
        except:
            sys.stderr.write("nxsfileinfo: File '%s' cannot be opened\n"
                             % options.args[0])
            self._parser.print_help()
            sys.exit(255)

        root = fl.root()
        self.show(root)
        fl.close()

    @classmethod
    def parseentry(cls, entry, description, keyvalue):
        """ parse entry of nexus file

        :param entry: nexus entry node
        :type entry: :class:`pni.io.nx.h5.nxgroup`
        :param description: dict description list
        :type description: :obj:`list` <:obj:`dict` <:obj:`str`, `any` > >
        :param keyvalue: (key, value) name pair of table headers
        :type keyvalue: [:obj:`str`, :obj:`str`]

        """
        key, value = keyvalue
        at = None
        try:
            at = entry.attributes["NX_class"]
        except:
            pass
        if at and at[...] == 'NXentry':
            description.append({key: "Scan entry:", value: entry.name})
            description.append(None)
            try:
                description.append(
                    {key: "Title:", value: entry.open("title")[...]})
            except:
                sys.stderr.write("nxsfileinfo: title cannot be found\n")
            try:
                description.append(
                    {key: "Experiment identifier:",
                     value: entry.open("experiment_identifier")[...]})
            except:
                sys.stderr.write(
                    "nxsfileinfo: experiment identifier cannot be found\n")
            for ins in entry:
                if isinstance(ins, nx._nxh5.nxgroup):
                    iat = ins.attributes["NX_class"]
                    if iat and iat[...] == 'NXinstrument':
                        try:
                            description.append({
                                key: "Instrument name:",
                                value: ins.open("name")[...]})
                        except:
                            sys.stderr.write(
                                "nxsfileinfo: instrument name cannot "
                                "be found\n")
                        try:
                            description.append({
                                key: "Instrument short name:",
                                value:
                                ins.open("name").attributes["short_name"][...]
                            })
                        except:
                            sys.stderr.write(
                                "nxsfileinfo: instrument short name cannot"
                                " be found\n")

                        for sr in ins:
                            if isinstance(sr, nx._nxh5.nxgroup):
                                sat = sr.attributes["NX_class"]
                                if sat and sat[...] == 'NXsource':
                                    try:
                                        description.append({
                                            key: "Source name:",
                                            value: sr.open("name")[...]})
                                    except:
                                        sys.stderr.write(
                                            "nxsfileinfo: source name"
                                            " cannot be found\n")
                                    try:
                                        description.append({
                                            key: "Source short name:",
                                            value: sr.open("name").attributes[
                                                "short_name"][...]})
                                    except:
                                        sys.stderr.write(
                                            "nxsfileinfo: source short name"
                                            " cannot be found\n")
                    elif iat and iat[...] == 'NXsample':
                        try:
                            description.append({
                                key: "Sample name:",
                                value: ins.open("name")[...]})
                        except:
                            sys.stderr.write(
                                "nxsfileinfo: sample name cannot be found\n")
                        try:
                            description.append({
                                key: "Sample formula:",
                                value: ins.open("chemical_formula")[...]})
                        except:
                            sys.stderr.write(
                                "nxsfileinfo: sample formula cannot"
                                " be found\n")
            try:
                description.append({key: "Start time:",
                                    value: entry.open("start_time")[...]})
            except:
                sys.stderr.write("nxsfileinfo: start time cannot be found\n")
            try:
                description.append({key: "End time:",
                                    value: entry.open("end_time")[...]})
            except:
                sys.stderr.write("nxsfileinfo: end time cannot be found\n")
            if "program_name" in entry.names():
                pn = entry.open("program_name")
                pname = pn.read()
                attr = pn.attributes
                names = [at.name for at in attr]
                if "scan_command" in names:
                    scommand = attr["scan_command"][...]
                    pname = "%s (%s)" % (pname, scommand)
                description.append({key: "Program:", value: pname})

    def show(self, root):
        """ show general informations

        :param root: nexus file root
        :type root: class:`pni.io.nx.h5.nxroot`
        """

        description = []

        attr = root.attributes

        names = [at.name for at in attr]
        fname = (attr["file_name"][...]
                 if "file_name" in names else " ") or " "
        headers = ["File name:", fname]

        for en in root:
            self.parseentry(en, description, headers)
        ttools = TableTools(description)
        ttools.title = ""
        ttools.headers = headers
        description[:] = ttools.generateList()

        if len(description) > 4:
            print "=" * len(description[4])
        print("\n".join(description).strip())
        print "=" * len(description[4])


class Field(Runner):
    """ Field runner"""

    #: (:obj:`str`) command description
    description = "show field information for the nexus file"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxsfileinfo field /user/data/myfile.nxs\n" \
        + "       nxsfileinfo field /user/data/myfile.nxs -g\n" \
        + "       nxsfileinfo field /user/data/myfile.nxs -s\n" \
        + "\n"

    def create(self):
        """ creates parser

        """
        self._parser.add_argument(
            "-c", "--columns",
            help="names of column to be shown (separated by commas "
            "without spaces). The possible names are: "
            "depends_on,dtype,full_path,nexus_path,nexus_type,shape,"
            "source,source_name,source_type,strategy,trans_type,trans_offset,"
            "trans_vector,units,value",
            dest="headers", default="")
        self._parser.add_argument(
            "-f", "--filters",
            help="full_path filters (separated by commas "
            "without spaces). Default: '*'. E.g. '*:NXsample/*'",
            dest="filters", default="")
        self._parser.add_argument(
            "-v", "--values",
            help="field names which value should be stored"
            " (separated by commas "
            "without spaces). Default: depends_on",
            dest="values", default="")
        self._parser.add_argument(
            "-g", "--geometry", action="store_true",
            default=False, dest="geometry",
            help="perform geometry full_path filters, i.e."
            "*:NXtransformations/*,*/depends_on. "
            "It works only when  -f is not defined")
        self._parser.add_argument(
            "-s", "--source", action="store_true",
            default=False, dest="source",
            help="show datasource parameters")

    def postauto(self):
        """ parser creator after autocomplete run """
        self._parser.add_argument(
            'args', metavar='nexus_file', type=str, nargs=1,
            help='new nexus file name')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :returns: output information
        :rtype: :obj:`str`
        """
        try:
            fl = nx.open_file(options.args[0])
        except:
            sys.stderr.write("nxsfileinfo: File '%s' cannot be opened\n"
                             % options.args[0])
            self._parser.print_help()
            sys.exit(255)

        root = fl.root()
        self.show(root, options)
        fl.close()

    def show(self, root, options):
        """ the main function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :param root: nexus file root
        :type root: class:`pni.io.nx.h5.nxroot`
        """
        #: (:obj:`list`< :obj:`str`>)   \
        #     parameters which have to exists to be shown
        toshow = None

        #: (:obj:`list`< :obj:`str`>)  full_path filters
        filters = []

        #: (:obj:`list`< :obj:`str`>)  column headers
        headers = ["nexus_path", "source_name", "units",
                   "dtype", "shape", "value"]
        if options.geometry:
            filters = ["*:NXtransformations/*", "*/depends_on"]
            headers = ["nexus_path", "source_name", "units",
                       "trans_type", "trans_vector", "trans_offset",
                       "depends_on"]
        if options.source:
            headers = ["source_name", "nexus_type", "shape", "strategy",
                       "source"]
            toshow = ["source_name"]
        #: (:obj:`list`< :obj:`str`>)  field names which value should be stored
        values = ["depends_on"]

        if options.headers:
            headers = options.headers.split(',')
        if options.filters:
            filters = options.filters.split(',')
        if options.values:
            values = options.values.split(',')

        nxsparser = NXSFileParser(root)
        nxsparser.filters = filters
        nxsparser.valuestostore = values
        nxsparser.parse()

        description = []
        ttools = TableTools(nxsparser.description, toshow)
        ttools.title = "    file: '%s'" % options.args[0]
        ttools.headers = headers
        description.extend(ttools.generateList())
        print("\n".join(description))


def main():
    """ the main program function
    """

    description = "Command-line tool for showing meta data" \
                  + " from Nexus Files"

    epilog = 'For more help:\n  nxsfileinfo <sub-command> -h'
    epilog = 'For more help:\n  nxsconfig <sub-command> -h'
    parser = NXSArgParser(
        description=description, epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.cmdrunners = [('field', Field),
                         ('general', General)]
    runners = parser.createSubParsers()

    try:
        options = parser.parse_args()
    except ErrorException as e:
        sys.stderr.write("Error: %s\n" % str(e))
        sys.stderr.flush()
        parser.print_help()
        print("")
        sys.exit(255)

    result = runners[options.subparser].run(options)
    if result and str(result).strip():
        print(result)


if __name__ == "__main__":
    main()
