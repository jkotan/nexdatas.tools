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

#: (:obj:`bool`) True if pni.io.nx.h5 available
PNIIO = False
try:
    import pni.io.nx.h5 as nx
    PNIIO = True
except:
    pass


def show(root):
    """ show general informations

    :param root: nexus root node
    :type root: :class:`pni.io.nx.h5.nxroot`
    """

    print("=" * 80)
    print("File name:              %s" % root.attributes["file_name"][...])

    for en in root:
        at = None
        try:
            at = en.attributes["NX_class"]
        except:
            pass
        if at and at[...] == 'NXentry':
            print("-"*80)
            print("Scan entry:             %s" % en.name)
            print("-" * 80)
            print("Title:                  %s" % en.open("title").read())
            print("Experiment identifier:  %s" %
                  en.open("experiment_identifier").read())
            for ins in en:
                if isinstance(ins, nx._nxh5.nxgroup):
                    iat = ins.attributes["NX_class"]
                    if iat and iat[...] == 'NXinstrument':
                        print("Instrument name:        %s" %
                              ins.open("name").read())
                        print("Instrument short name:  %s" %
                              ins.open("name").attributes["short_name"][...])
                        for sr in ins:
                            if isinstance(sr, nx._nxh5.nxgroup):
                                sat = sr.attributes["NX_class"]
                                if sat and sat[...] == 'NXsource':
                                    print("Source name:            %s" %
                                          sr.open("name").read())
                                    print("Source short name:      %s" %
                                          sr.open("name").attributes[
                                              "short_name"][...])
                    elif iat and iat[...] == 'NXsample':
                        print("Sample name:            %s" %
                              ins.open("name").read())
                        print("Sample formula:         %s" %
                              ins.open("chemical_formula").read())
            print("Start time:             %s" % en.open("start_time").read())
            print("End time:               %s" % en.open("end_time").read())
            if "program_name" in en.names():
                pn = en.open("program_name")
                pname = pn.read()
                attr = pn.attributes
                names = [at.name for at in attr]
                if "scan_command" in names:
                    scommand = attr["scan_command"][...]
                    pname = "%s [%s]" % (pname, scommand)
                print("Program:                %s" % pname)
    print("=" * 80)


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
    show(rt)
    fl.close()

if __name__ == "__main__":
    main()
