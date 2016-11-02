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

import os
import sys
import time
import fnmatch
import argparse
import argcomplete

from .nxsparser import TableTools
from optparse import OptionParser
from .nxsfileparser import NXSFileParser


#: (:obj:`bool`) True if pni.io.nx.h5 available
PNIIO = False
try:
    import pni.io.nx.h5 as nx
    PNIIO = True
except:
    pass


class General(object):

    def __init__(self, root, options):
        """ constructor

        :param root: nexus root node
        :type root: :class:`pni.io.nx.h5.nxroot`
        :param root: parser options
        :type root: :class:`argparse.Namespace`
        """    
        self.__root = root
        self.__options = options
        

    def parseentry(self, entry, description, keyvalue):
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
                                "nxsfileinfo: instrument name cannot be found\n")
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
                                "nxsfileinfo: sample formula cannot be found\n")
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


    def show(self):
        """ show general informations
        """

        description = []

        attr = self.__root.attributes

        names = [at.name for at in attr]
        fname = (attr["file_name"][...] if "file_name" in names else " ") or " "
        headers = ["File name:", fname]

        for en in self.__root:
            self.parseentry(en, description, headers)
        ttools = TableTools(description)
        ttools.title = ""
        ttools.headers = headers
        description[:] = ttools.generateList()

        if len(description) > 4:
            print "=" * len(description[4])
        print("\n".join(description).strip())
        print "=" * len(description[4])



class Field(object):

    def __init__(self, root, options):
        """ constructor

        :param root: nexus root node
        :type root: :class:`pni.io.nx.h5.nxroot`
        :param root: parser options
        :type root: :class:`argparse.Namespace`
        """    
        self.__root = root
        self.__options = options
                
    def show(self):
        """ the main function

        """

        #: usage example
        usage = "usage: nxsinfo field <file_name>\n"\
            + "  e.g.: nxsinfo field saxs_ref1_02.nxs\n\n "\
            + "show field information for the nexus file"

        #: (:obj:`list`< :obj:`str`>)  parameters which have to exists to be shown
        toshow = None

        #: (:obj:`list`< :obj:`str`>)  full_path filters
        filters = []

        #: (:obj:`list`< :obj:`str`>)  column headers
        headers = ["nexus_path", "source_name", "units", "dtype", "shape", "value"]
        if self.__options.geometry:
            filters = ["*:NXtransformations/*", "*/depends_on"]
            headers = ["nexus_path", "source_name", "units",
                       "trans_type", "trans_vector", "trans_offset",
                       "depends_on"]
        if self.__options.source:
            headers = ["source_name", "nexus_type", "shape", "strategy",
                       "source"]
            toshow = ["source_name"]
        #: (:obj:`list`< :obj:`str`>)  field names which value should be stored
        values = ["depends_on"]

        if self.__options.headers:
            headers = self.__options.headers.split(',')
        if self.__options.filters:
            filters = self.__options.filters.split(',')
        if self.__options.values:
            values = self.__options.values.split(',')

        nxsparser = NXSFileParser(self.__root)
        nxsparser.filters = filters
        nxsparser.valuestostore = values
        nxsparser.parse()

        description = []
        ttools = TableTools(nxsparser.description, toshow)
        ttools.title = "    file: '%s'" % self.__options.args[0]
        ttools.headers = headers
        description.extend(ttools.generateList())
        print("\n".join(description))


class ErrorException(Exception):
    """ error parser exception """
    pass


class NXSFileInfoArgParser(argparse.ArgumentParser):
    """ Argument parser with error exception
    """

    #: (:obj:`list` <:obj:`str`>) nxsfileinfo sub-commands
    commands = ['general', 'field']

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
        :rtype: :class:`NXSFileInfoArgParser`
        """
        #: usage example
        description  = " Command-line tool for showing meta data from Nexus Files"
        #    \
        #            + " e.g.: nxsdata openfile -s p02/tangodataserver/exp.01  " \
        #            + "/user/data/myfile.h5"

        hlp = {
            "general": "show general information for the nexus file",
            "field": "show field information for the nexus file",
        }

        self.description = description
        self.epilog = 'For more help:\n  nxsfileinfo <sub-command> -h'

        pars = {}
        subparsers = self.add_subparsers(
            help='sub-command help', dest="subparser")


        for cmd in self.commands:
            pars[cmd] = subparsers.add_parser(
                cmd, help='%s' % hlp[cmd], description=hlp[cmd])

        pars['field'].add_argument(
            "-c", "--columns",
            help="names of column to be shown (separated by commas "
            "without spaces). The possible names are: "
            "depends_on,dtype,full_path,nexus_path,nexus_type,shape,"
            "source,source_name,source_type,strategy,trans_type,trans_offset,"
            "trans_vector,units,value",
            dest="headers", default="")
        pars['field'].add_argument(
            "-f", "--filters",
            help="full_path filters (separated by commas "
            "without spaces). Default: '*'. E.g. '*:NXsample/*'",
            dest="filters", default="")
        pars['field'].add_argument(
            "-v", "--values",
            help="field names which value should be stored (separated by commas "
            "without spaces). Default: depends_on",
            dest="values", default="")
        pars['field'].add_argument(
            "-g", "--geometry", action="store_true",
            default=False, dest="geometry",
            help="perform geometry full_path filters, i.e."
            "*:NXtransformations/*,*/depends_on. "
            "It works only when  -f is not defined")
        pars['field'].add_argument(
            "-s", "--source", action="store_true",
            default=False, dest="source",
            help="show datasource parameters")

        argcomplete.autocomplete(self)
        for cmd in self.commands:
            pars[cmd].add_argument('args', metavar='nexus_file',
                                   type=str, nargs=1,
                                   help='new nexus file name')

        self.subparsers = pars
        return pars




def main():
    """ the main program function
    """

    parser = NXSFileInfoArgParser(
        formatter_class=argparse.RawDescriptionHelpFormatter)
    pars = parser.createParser()


    try:
        options = parser.parse_args()
    except ErrorException as e:
        sys.stderr.write("Error: %s\n" % str(e))
        sys.stderr.flush()
        parser.print_help()
        print("")
        sys.exit(255)

    if not PNIIO:
        sys.stderr.write("nxsfileinfo: No pni.io.nx.h5 installed\n")
        parser.print_help()
        sys.exit(255)

    try:
        fl = nx.open_file(options.args[0])
    except:
        sys.stderr.write("nxsfileinfo: File '%s' cannot be opened\n" % options.args[0])
        parser.print_help()
        sys.exit(255)

    rt = fl.root()

    cmdclasses = {"general" : General, "field": Field}

    fileparser = cmdclasses[options.subparser](rt, options)
    fileparser.show()

    fl.close()


if __name__ == "__main__":
    main()
