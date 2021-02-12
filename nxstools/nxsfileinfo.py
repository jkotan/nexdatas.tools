#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2018 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
from . import filewriter


WRITERS = {}
try:
    from . import h5pywriter
    WRITERS["h5py"] = h5pywriter
except Exception:
    pass

try:
    from . import h5cppwriter
    WRITERS["h5cpp"] = h5cppwriter
except Exception:
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

    def create(self):
        """ creates parser

        """
        self._parser.add_argument(
            "--h5py", action="store_true",
            default=False, dest="h5py",
            help="use h5py module as a nexus reader")
        self._parser.add_argument(
            "--h5cpp", action="store_true",
            default=False, dest="h5cpp",
            help="use h5cpp module as a nexus reader")

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
        if options.h5cpp:
            writer = "h5cpp"
        elif options.h5py:
            writer = "h5py"
        elif "h5cpp" in WRITERS.keys():
            writer = "h5cpp"
        else:
            writer = "h5py"
        if (options.h5py and options.h5cpp) or \
           writer not in WRITERS.keys():
            sys.stderr.write("nxsfileinfo: Writer '%s' cannot be opened\n"
                             % writer)
            sys.stderr.flush()
            self._parser.print_help()
            sys.exit(255)
        wrmodule = WRITERS[writer.lower()]
        try:
            fl = filewriter.open_file(
                options.args[0], readonly=True,
                writer=wrmodule)
        except Exception:
            sys.stderr.write("nxsfileinfo: File '%s' cannot be opened\n"
                             % options.args[0])
            sys.stderr.flush()
            self._parser.print_help()
            sys.exit(255)

        root = fl.root()
        self.show(root)
        fl.close()

    @classmethod
    def parseentry(cls, entry, description):
        """ parse entry of nexus file

        :param entry: nexus entry node
        :type entry: :class:`filewriter.FTGroup`
        :param description: dict description list
        :type description: :obj:`list` <:obj:`dict` <:obj:`str`, `any` > >
        :return: (key, value) name pair of table headers
        :rtype: [:obj:`str`, :obj:`str`]

        """
        key = "A"
        value = "B"
        at = None
        try:
            at = entry.attributes["NX_class"]
        except Exception:
            pass
        if at and filewriter.first(at.read()) == 'NXentry':
            # description.append(None)
            # value = filewriter.first(value)
            key = "Scan entry:"
            value = entry.name
            # description.append({key: "Scan entry:", value: entry.name})
            # description.append(None)
            try:
                vl = filewriter.first(entry.open("title").read())
                description.append(
                    {key: "Title:", value: vl})
            except Exception:
                sys.stderr.write("nxsfileinfo: title cannot be found\n")
                sys.stderr.flush()
            try:
                vl = filewriter.first(
                    entry.open("experiment_identifier").read())
                description.append(
                    {key: "Experiment identifier:",
                     value: vl})
            except Exception:
                sys.stderr.write(
                    "nxsfileinfo: experiment identifier cannot be found\n")
                sys.stderr.flush()
            for ins in entry:
                if isinstance(ins, filewriter.FTGroup):
                    iat = ins.attributes["NX_class"]
                    if iat and filewriter.first(iat.read()) == 'NXinstrument':
                        try:
                            vl = filewriter.first(ins.open("name").read())
                            description.append({
                                key: "Instrument name:",
                                value: vl})
                        except Exception:
                            sys.stderr.write(
                                "nxsfileinfo: instrument name cannot "
                                "be found\n")
                            sys.stderr.flush()
                        try:
                            vl = filewriter.first(
                                ins.open("name").attributes[
                                    "short_name"].read())
                            description.append({
                                key: "Instrument short name:",
                                value: vl
                            })
                        except Exception:
                            sys.stderr.write(
                                "nxsfileinfo: instrument short name cannot"
                                " be found\n")
                            sys.stderr.flush()

                        for sr in ins:
                            if isinstance(sr, filewriter.FTGroup):
                                sat = sr.attributes["NX_class"]
                                if sat and filewriter.first(sat.read()) \
                                   == 'NXsource':
                                    try:
                                        vl = filewriter.first(
                                            sr.open("name").read())
                                        description.append({
                                            key: "Source name:",
                                            value: vl})
                                    except Exception:
                                        sys.stderr.write(
                                            "nxsfileinfo: source name"
                                            " cannot be found\n")
                                        sys.stderr.flush()
                                    try:
                                        vl = filewriter.first(
                                            sr.open("name").attributes[
                                                "short_name"].read())
                                        description.append({
                                            key: "Source short name:",
                                            value: vl})
                                    except Exception:
                                        sys.stderr.write(
                                            "nxsfileinfo: source short name"
                                            " cannot be found\n")
                                        sys.stderr.flush()
                    elif iat and filewriter.first(iat.read()) == 'NXsample':
                        try:
                            vl = filewriter.first(ins.open("name").read())
                            description.append({
                                key: "Sample name:",
                                value: vl})
                        except Exception:
                            sys.stderr.write(
                                "nxsfileinfo: sample name cannot be found\n")
                            sys.stderr.flush()
                        try:
                            vl = filewriter.first(
                                ins.open("chemical_formula").read())
                            description.append({
                                key: "Sample formula:",
                                value: vl})
                        except Exception:
                            sys.stderr.write(
                                "nxsfileinfo: sample formula cannot"
                                " be found\n")
                            sys.stderr.flush()
            try:
                vl = filewriter.first(entry.open("start_time").read())
                description.append({key: "Start time:", value: vl})
            except Exception:
                sys.stderr.write("nxsfileinfo: start time cannot be found\n")
                sys.stderr.flush()
            try:
                vl = filewriter.first(entry.open("end_time").read())
                description.append({key: "End time:",
                                    value: vl})
            except Exception:
                sys.stderr.write("nxsfileinfo: end time cannot be found\n")
                sys.stderr.flush()
            if "program_name" in entry.names():
                pn = entry.open("program_name")
                pname = filewriter.first(pn.read())
                attr = pn.attributes
                names = [att.name for att in attr]
                if "scan_command" in names:
                    scommand = filewriter.first(attr["scan_command"].read())
                    pname = "%s (%s)" % (pname, scommand)
                description.append({key: "Program:", value: pname})
        return [key, value]

    def show(self, root):
        """ show general informations

        :param root: nexus file root
        :type root: class:`filewriter.FTGroup`
        """

        description = []

        attr = root.attributes

        names = [at.name for at in attr]
        fname = filewriter.first(
            (attr["file_name"].read()
             if "file_name" in names else " ") or " ")
        title = "File name: '%s'" % fname

        print("")
        for en in root:
            description = []
            headers = self.parseentry(en, description)
            ttools = TableTools(description)
            ttools.title = title
            ttools.headers = headers
            rstdescription = ttools.generateList()
            title = ""
            print("\n".join(rstdescription).strip())
            print("")


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
            "depends_on, dtype, full_path, nexus_path, nexus_type, shape,"
            " source, source_name, source_type, strategy, trans_type, "
            "trans_offset, trans_vector, units, value",
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
        self._parser.add_argument(
            "--h5py", action="store_true",
            default=False, dest="h5py",
            help="use h5py module as a nexus reader")
        self._parser.add_argument(
            "--h5cpp", action="store_true",
            default=False, dest="h5cpp",
            help="use h5cpp module as a nexus reader")

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
        if options.h5cpp:
            writer = "h5cpp"
        elif options.h5py:
            writer = "h5py"
        elif "h5cpp" in WRITERS.keys():
            writer = "h5cpp"
        else:
            writer = "h5py"
        if (options.h5cpp and options.h5py) or writer not in WRITERS.keys():
            sys.stderr.write("nxsfileinfo: Writer '%s' cannot be opened\n"
                             % writer)
            sys.stderr.flush()
            self._parser.print_help()
            sys.exit(255)
        wrmodule = WRITERS[writer.lower()]
        try:
            fl = filewriter.open_file(
                options.args[0], readonly=True,
                writer=wrmodule)
        except Exception:
            sys.stderr.write("nxsfileinfo: File '%s' cannot be opened\n"
                             % options.args[0])
            sys.stderr.flush()
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
        :type root: class:`filewriter.FTGroup`
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
        ttools.title = "File name: '%s'" % options.args[0]
        ttools.headers = headers
        description.extend(ttools.generateList())
        print("\n".join(description))


def main():
    """ the main program function
    """

    description = "Command-line tool for showing meta data" \
                  + " from Nexus Files"

    epilog = 'For more help:\n  nxsfileinfo <sub-command> -h'
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

    if options.subparser is None:
        sys.stderr.write(
            "Error: %s\n" % str("too few arguments"))
        sys.stderr.flush()
        parser.print_help()
        print("")
        sys.exit(255)

    result = runners[options.subparser].run(options)
    if result and str(result).strip():
        print(result)


if __name__ == "__main__":
    main()
