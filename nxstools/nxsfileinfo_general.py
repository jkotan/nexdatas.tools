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

""" NeXus main metadata viewer """

import sys
import os
import time

from optparse import OptionParser

from .nxsparser import TableTools

#: (:obj:`bool`) True if pni.io.nx.h5 available
PNIIO = False
try:
    import pni.io.nx.h5 as nx
    PNIIO = True
except:
    pass


def parseentry(entry, description, keyvalue):
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
                            key: "Instrument  short name:",
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
                pname = "%s [%s]" % (pname, scommand)
            description.append({key: "Program:", value: pname})


def show(root):
    """ show general informations

    :param root: nexus root node
    :type root: :class:`pni.io.nx.h5.nxroot`
    """

    description = []

    attr = root.attributes

    names = [at.name for at in attr]
    fname = (attr["file_name"][...] if "file_name" in names else " ") or " "
    headers = ["File name:", fname]

    for en in root:
        parseentry(en, description, headers)
    ttools = TableTools(description)
    ttools.title = ""
    ttools.headers = headers
    description[:] = ttools.generateList()

    if len(description) > 4:
        print "=" * len(description[4])
    print("\n".join(description).strip())
    print "=" * len(description[4])


def main():
    """ the main function
    """

    #: usage example
    usage = "usage: nxsfileinfo general <nexus_file_name>\n"\
        + "  e.g.: nxsfileinfo general saxs_ref1_02.nxs \n\n" \
        + " show general information for the nexus file"

    #: option parser
    parser = OptionParser(usage=usage)

    (options, args) = parser.parse_args()

    if len(args) < 2:
        parser.print_help()
        sys.exit(255)
    else:
        args = args[1:]

    if not PNIIO:
        sys.stderr.write("nxsfileinfo: No pni.io.nx.h5 installed\n")
        parser.print_help()
        sys.exit(255)

    try:
        fl = nx.open_file(args[0])
    except:
        sys.stderr.write("nxsfileinfo: File '%s' cannot be opened\n" % args[0])
        parser.print_help()
        sys.exit(255)

    rt = fl.root()
    description = []
    show(rt)
    fl.close()

if __name__ == "__main__":
    main()
