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

"""Command-line tool for creating NXSConfigServer configuration of Nexus Files
"""

import os
import sys
import argparse


from nxstools.nxsargparser import (Runner, NXSArgParser, ErrorException)
from nxstools.nxsdevicetools import (
    checkServer, getAttributes, getServerTangoHost)
from nxstools.nxscreator import (
    TangoDSCreator, ClientDSCreator, WrongParameterError,
    DeviceDSCreator, OnlineDSCreator, OnlineCPCreator, CPExistsException,
    DSExistsException,
    StandardCPCreator, ComponentCreator, CompareOnlineDS, PoolDSCreator)


#: (:obj:`bool`) True if PyTango available
PYTANGO = False
try:
    __import__("PyTango")
    PYTANGO = True
except Exception:
    pass


class TangoDS(Runner):

    """ tangods runner"""

    #: (:obj:`str`) command description
    description = "create tango datasources"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * with -b: datasources are created" \
        + " in Configuration Server database\n" \
        + " * without -b: datasources are created" \
        + " on the local filesystem in -d <directory> \n" \
        + " * default: <directory> is '.' \n" \
        + "            <server> is taken from Tango DB\n" \
        + "            <datasource> is 'exp_mot' \n" \
        + "            <host>, <port> are taken from <server>\n" \
        + " examples:\n" \
        + "       nxscreate tangods -f1 -l2 -v p09/motor/exp. -s exp_mot \n" \
        + "       nxscreate tangods -f1 -l32 -v p02/motor/eh1a. -s exp_mot" \
        + "-b \n" \
        + "       nxscreate tangods -f1 -l32 -v p01/motor/oh1. " \
        + "-s exp_mot -b\n" \
        + "       nxscreate tangods -v petra/globals/keyword " \
        + "-s source_current -u haso228 -t 10000 \\ \n "\
        + "                        -a BeamCurrent " \
        + "-b -r p09/nxsconfigserver/haso228 -o -g __CLIENT__\n" \
        + "       nxscreate tangods -f1 -l8  -v pXX/slt/exp. -s slt_exp_ -u" \
        + " hasppXX.desy.de -b \n" \
        + "\n"

    def create(self):
        """ creates parser

        """
        parser = self._parser
        parser.add_argument(
            "-v", "--device-prefix",
            help="device prefix, i.e. exp_c (mandatory)",
            dest="device", default="")
        parser.add_argument(
            "-f", "--first", help="first index",
            dest="first", default="1")
        parser.add_argument(
            "-l", "--last",
            help="last index",
            dest="last", default=None)

        parser.add_argument(
            "-a", "--attribute",
            help="tango attribute name",
            dest="attribute", default="Position")

        parser.add_argument(
            "-s", "--datasource-prefix",
            help="datasource-prefix "
            "(useful for avoiding duplicated datasource names)",
            dest="datasource", default="exp_mot")

        parser.add_argument(
            "-o", "--overwrite", action="store_true",
            default=False, dest="overwrite",
            help="overwrite existing datasources")
        parser.add_argument(
            "-d", "--directory",
            help="output datasource directory",
            dest="directory", default=".")
        parser.add_argument(
            "-x", "--file-prefix",
            help="file prefix, i.e. counter",
            dest="file", default="")
        parser.add_argument(
            "-u", "--host",
            help="tango host name",
            dest="host", default="")
        parser.add_argument(
            "-t", "--port",
            help="tango host port",
            dest="port", default="10000")

        parser.add_argument(
            "-b", "--database", action="store_true",
            default=False, dest="database",
            help="store datasources in "
            "Configuration Server database")
        parser.add_argument(
            "-g", "--group",
            help="device group name",
            dest="group", default="")
        parser.add_argument(
            "-e", "--elementtype",
            help="element type, i.e. attribute, property or command",
            dest="elementtype", default="attribute")

        parser.add_argument(
            "-r", "--server", dest="server",
            help="configuration server device name")
        return parser

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """

        parser = self._parser
        if (options.database and not options.server) or \
           (not options.host and not options.server):
            if not PYTANGO:
                sys.stderr.write("Info: No PyTango installed\n")
                sys.stderr.flush()
                sys.exit(255)
            options.server = checkServer()
            if options.database and not options.server:
                parser.print_help()
                sys.exit(0)

        if not options.host:
            if not PYTANGO:
                sys.stderr.write(
                    "Info: No Tango Host or PyTango installed\n")
                sys.stderr.flush()
                sys.exit(255)
            hostport = getServerTangoHost(options.server)
            options.host, options.port = hostport.split(":")

        if options.database:
            print("CONFIG SERVER: %s" % str(options.server))
        else:
            print("OUTPUT DIRECTORY: %s" % str(options.directory))

        creator = TangoDSCreator(options, [])
        try:
            creator.create()
        except WrongParameterError as e:
            sys.stderr.write(str(e))
            sys.stderr.flush()
            parser.print_help()
            sys.exit(255)


class DeviceDS(Runner):

    """ deviceds runner"""
    #: (:obj:`str`) command description
    description = "create datasources for all device attributes"
    #: (:obj:`str`) command epilog
    epilog = "" \
             + " * without <dv_attr1>: datasources for all" \
             + " attributes are created\n" \
             + " * with -b: datasources are created" \
             + " in Configuration Server database\n" \
             + " * without -b: datasources are created" \
             + " on the local filesystem in -d <directory> \n" \
             + " * default: <directory> is '.' \n" \
             + "            <server> is taken from Tango DB\n" \
             + "            <datasource> is 'exp_mot' \n" \
             + "            <host>, <port> are taken from <server>\n" \
             + " examples:\n" \
             + "       nxscreate deviceds  -v p09/pilatus/haso228k \n" \
             + "       nxscreate deviceds  -v p09/lambda2m/haso228k -u" \
             + "haslambda -b \n" \
             + "       nxscreate deviceds  -v p09/pilatus300k/haso228k -b" \
             + " -s pilatus300k_ RoI Energy ExposureTime\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument("-v", "--device",
                            help="device, i.e. p09/pilatus300k/01 (mandatory)",
                            dest="device", default="")
        parser.add_argument("-s", "--datasource-prefix",
                            help="datasource-prefix"
                            " (useful for avoiding duplicated"
                            " datasource names)",
                            dest="datasource", default="")

        parser.add_argument("-o", "--overwrite", action="store_true",
                            default=False, dest="overwrite",
                            help="overwrite existing datasources")
        parser.add_argument("-d", "--directory",
                            help="output datasource directory",
                            dest="directory", default=".")
        parser.add_argument("-x", "--file-prefix",
                            help="file prefix, i.e. counter",
                            dest="file", default="")
        parser.add_argument("-u", "--host",
                            help="tango host name",
                            dest="host", default="")
        parser.add_argument("-t", "--port",
                            help="tango host port",
                            dest="port", default="10000")

        parser.add_argument("-b", "--database", action="store_true",
                            default=False, dest="database",
                            help="store components in Configuration"
                            " Server database")

        parser.add_argument("-n", "--no-group", action="store_true",
                            default=False, dest="nogroup",
                            help="don't create common group with a name of"
                            " datasource prefix")

        parser.add_argument("-r", "--server", dest="server",
                            help="configuration server device name")

        parser.add_argument('args', metavar='attribute_name',
                            type=str, nargs='*',
                            help='attribute names of the tango device')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """

        parser = self._parser
        if (options.database and not options.server) or \
           (not options.host and not options.server):
            if not PYTANGO:
                sys.stderr.write("Info: No PyTango installed\n")
                sys.stderr.flush()
                sys.exit(255)

            options.server = checkServer()
            if options.database and not options.server:
                parser.print_help()
                sys.exit(0)

        if not options.host:
            if not PYTANGO:
                sys.stderr.write("Info: No Tango Host or PyTango installed\n")
                sys.stderr.flush()
                sys.exit(255)
            hostport = getServerTangoHost(options.server)
            options.host, options.port = hostport.split(":")

        if options.database:
            print("CONFIG SERVER: %s" % options.server)
        else:
            print("OUTPUT DIRECTORY: %s" % options.directory)

        if not options.device.strip():
            parser.print_help()
            sys.exit(255)

        if options.args:
            aargs = list(options.args)
        else:
            if not PYTANGO:
                sys.stderr.write("CollCompCreator No PyTango installed\n")
                sys.stderr.flush()
                parser.print_help()
                sys.exit(255)
            aargs = getAttributes(options.device, options.host, options.port)

        creator = DeviceDSCreator(options, aargs)
        creator.create()


class OnlineDS(Runner):

    """ onlineds runner"""

    #: (:obj:`str`) command description
    description = "create datasources from online.xml file"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * with -b: datasources are created" \
        + " in Configuration Server database\n" \
        + " * with -d <directory>: datasources are created" \
        + " on the local filesystem\n" \
        + " * without -b or -d <directory>: run in the test mode\n" \
        + " * default: <inputFile> is '/online_dir/online.xml' \n" \
        + "            <server> is taken from Tango DB\n\n" \
        + " `onlineds` overwrites existing datasources\n\n" \
        + " examples:\n" \
        + "       nxscreate onlineds -b  \n" \
        + "       nxscreate onlineds -b -t \n" \
        + "       nxscreate onlineds -d /home/user/xmldir \n" \
        + "       nxscreate onlineds \n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument("-b", "--database", action="store_true",
                            default=False, dest="database",
                            help="store components in"
                            " Configuration Server database")
        parser.add_argument("-t", "--noclientlike", action="store_false",
                            default=True, dest="clientlike",
                            help="set motor tango datasources to "
                            "be no __CLIENT__ like, i.e. pure tango-like")
        parser.add_argument("-d", "--directory",
                            help="output directory where"
                            " datasources will be saved",
                            dest="directory", default="")
        parser.add_argument("-n", "--nolower", action="store_false",
                            default=True, dest="lower",
                            help="do not change aliases into lower case")
        parser.add_argument("-r", "--server", dest="server",
                            help="configuration server device name")
        parser.add_argument("-x", "--file-prefix",
                            help="file prefix, i.e. counter",
                            dest="file", default="")
        parser.add_argument("-e", "--external",
                            help="external configuration server",
                            dest="external", default="")
        parser.add_argument("-p", "--xml-package", dest="xmlpackage",
                            help="xml template package")
        parser.add_argument("-c", "--clientlike", action="store_true",
                            default=False, dest="oldclientlike",
                            help="set motor tango datasources to "
                            "be __CLIENT__ like (deprecated)")
        parser.add_argument("--verbose", action="store_true",
                            default=False, dest="verbose",
                            help="printout verbose mode")

    def postauto(self):
        """ creates parser
        """
        self._parser.add_argument('args', metavar='online_file',
                                  type=str, nargs='?',
                                  help='online.xml file')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """

        parser = self._parser
        if not PYTANGO:
            sys.stderr.write("Info: No PyTango installed\n")
            sys.stderr.flush()
            sys.exit(255)

        if not options.server:
            options.server = checkServer()
            if not options.server and options.database:
                parser.print_help()
                sys.exit(0)
        args = [options.args] if options.args else []
        if not len(args) and os.path.isfile('/online_dir/online.xml'):
            args = ['/online_dir/online.xml']

        if not len(args):
            parser.print_help()
            sys.exit(255)

        print("INPUT: %s" % args)
        if options.directory:
            print("OUTPUT DIR: %s" % options.directory)
        elif options.database:
            print("SERVER: %s" % options.server)
        else:
            print("TEST MODE: %s" % options.server)

        creator = OnlineDSCreator(options, args)
        creator.create()


class PoolDS(Runner):

    """ poolds runner"""

    #: (:obj:`str`) command description
    description = "create datasources from sardana pool device"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * with -b: datasources are created" \
        + " in Configuration Server database\n" \
        + " * with -d <directory>: datasources are created" \
        + " on the local filesystem\n" \
        + " * without -b or -d <directory>: run in the test mode\n" \
        + " * default: <channel> is 'ALL' \n" \
        + "            <server> is taken from Tango DB\n\n" \
        + "            <pool> is taken from Tango DB\n\n" \
        + " `poolds` overwrites existing datasources\n\n" \
        + " examples:\n" \
        + "       nxscreate poolds -b  \n" \
        + "       nxscreate poolds -b -t \n" \
        + "       nxscreate poolds -d -p p09/pool/haso228 \n" \
        + "       nxscreate poolds -b Motor CTExpChannel \n" \
        + "       nxscreate poolds -b mot01 mot03 \n" \
        + "       nxscreate poolds \n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument("-b", "--database", action="store_true",
                            default=False, dest="database",
                            help="store components in"
                            " Configuration Server database")
        parser.add_argument("-t", "--noclientlike", action="store_false",
                            default=True, dest="clientlike",
                            help="set motor tango datasources to "
                            "be no __CLIENT__ like, i.e. pure tango-like")
        parser.add_argument("-d", "--directory",
                            help="output directory where"
                            " datasources will be saved",
                            dest="directory", default="")
        parser.add_argument("-n", "--nolower", action="store_false",
                            default=True, dest="lower",
                            help="do not change aliases into lower case")
        parser.add_argument("-r", "--server", dest="server",
                            help="configuration server device name")
        parser.add_argument("-x", "--file-prefix",
                            help="file prefix, i.e. counter",
                            dest="file", default="")
        parser.add_argument("-p", "--pool",
                            help="sardana pool device name",
                            dest="pool", default="")

    def postauto(self):
        """ creates parser
        """
        self._parser.add_argument('args', metavar='channel',
                                  type=str, nargs='*',
                                  help='sardana pool channel types '
                                  'or name of aliases, '
                                  'e.g. Motor CTExpChannel ZeroDExpChannel '
                                  'OneDExpChannel TwoDExpChannel '
                                  ' PseudoMotor PseudoCounter ALL')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """

        parser = self._parser
        if not PYTANGO:
            sys.stderr.write("Info: No PyTango installed\n")
            sys.stderr.flush()
            sys.exit(255)
        if not options.server:
            options.server = checkServer()
            if options.database and not options.server:
                parser.print_help()
                sys.exit(0)

        if not options.pool:
            options.pool = checkServer("Pool")
            if not options.pool:
                parser.print_help()
                sys.exit(0)
        args = options.args

        print("INPUT: %s" % args)
        if options.directory:
            print("OUTPUT DIR: %s" % options.directory)
        elif options.database:
            print("SERVER: %s" % options.server)
        else:
            print("TEST MODE: %s" % options.server)

        creator = PoolDSCreator(options, args)
        creator.create()


class Compare(Runner):

    """ compare runner"""

    #: (:obj:`str`) command description
    description = "compare two online.xml files"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * default: second file <online_file> is " \
        + "'/online_dir/online.xml' \n" \
        + "            if only file is given\n\n" \
        + " examples:\n" \
        + "       nxscreate onlineds /online_dir/online.xml online.xml \n" \
        + "       nxscreate compare online.xml \n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument("-n", "--nolower", action="store_false",
                            default=True, dest="lower",
                            help="do not change aliases into lower case")

    def postauto(self):
        """ creates parser
        """
        self._parser.add_argument('args', metavar='online_file',
                                  type=str, nargs='+',
                                  help='online.xml files')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        args = options.args if options.args else []
        parser = self._parser

        if len(args) == 1 and os.path.isfile('/online_dir/online.xml'):
            args.append('/online_dir/online.xml')

        if len(args) == 1:
            parser.print_help()
            sys.exit(255)

        creator = CompareOnlineDS(options, args)
        creator.compare()


class OnlineCP(Runner):

    """ onlinecp runner"""
    #: (:obj:`str`) command description
    description = "create component from online.xml file"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * without '-c <component>': show a list of possible components\n" \
        + " * with -b: datasources are created" \
        + " in Configuration Server database\n" \
        + " * without -b: datasources are created" \
        + " on the local filesystem in -d <directory> \n" \
        + " * default: <directory> is '.' \n" \
        + " * default: <inputFile> is '/online_dir/online.xml' \n" \
        + "            <server> is taken from Tango DB\n" \
        + " examples:\n" \
        + "       nxscreate onlinecp  \n" \
        + "       nxscreate onlinecp -c pilatus -b \n" \
        + "       nxscreate onlinecp -c lambda -d /home/user/xmldir/ \n\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument("-c", "--component",
                            help="component name" +
                            "related to the device name from <inputFile>",
                            dest="component", default="")
        parser.add_argument("-b", "--database", action="store_true",
                            default=False, dest="database",
                            help="store components in"
                            "Configuration Server database")
        parser.add_argument("-r", "--server", dest="server",
                            help="configuration server device name")
        parser.add_argument("-n", "--nolower", action="store_false",
                            default=True, dest="lower",
                            help="do not change aliases into lower case")
        parser.add_argument("-o", "--overwrite", action="store_true",
                            default=False, dest="overwrite",
                            help="overwrite existing component")
        parser.add_argument("-d", "--directory",
                            help="output datasource directory",
                            dest="directory", default=".")
        parser.add_argument("-x", "--file-prefix",
                            help="file prefix, i.e. counter",
                            dest="file", default="")
        parser.add_argument("-e", "--external",
                            help="external configuration server",
                            dest="external", default="")
        parser.add_argument("-p", "--xml-package", dest="xmlpackage",
                            help="xml template package")
        parser.add_argument("-y", "--entryname", dest="entryname",
                            help="entry group name (prefix)", default="scan")
        parser.add_argument("-i", "--insname", dest="insname",
                            help="instrument group name", default="instrument")

    def postauto(self):
        """ creates parser
        """
        self._parser.add_argument('args', metavar='online_file',
                                  type=str, nargs='?',
                                  help='online.xml file')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """

        parser = self._parser
        if not PYTANGO:
            sys.stderr.write("Info: No PyTango installed\n")
            sys.stderr.flush()
            sys.exit(255)

        if not options.server:
            options.server = checkServer()
            if not options.server and options.database:
                parser.print_help()
                sys.exit(0)

        args = [options.args] if options.args else []
        if not len(args) and os.path.isfile('/online_dir/online.xml'):
            args = ['/online_dir/online.xml']

        if not len(args):
            parser.print_help()
            sys.exit(255)

        print("INPUT: %s" % args[0])
        if options.database:
            print("SERVER: %s" % options.server)
        else:
            print("OUTPUT DIR: %s" % options.directory)

        creator = OnlineCPCreator(options, args)
        if options.component:
            try:
                creator.create()
            except CPExistsException as e:
                print(str(e))
                sys.exit(255)
        else:
            lst = creator.listcomponents()
            print("\nPOSSIBLE COMPONENTS: \n   %s" % " ".join(list(lst)))


class StdComp(Runner):

    """  stdcomp runner"""

    #: (:obj:`str`) command description
    description = "create component from the standard templates"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * without '-t <type>': show a list of possible" \
        + " component types\n" \
        + " * with '-t <type>  and without -c <component>:" \
        + " show a list of component variables " \
        + "for the given component type\n" \
        + " * with -b: datasources are created" \
        + " in Configuration Server database\n" \
        + " * without -b: datasources are created" \
        + " on the local filesystem in -d <directory> \n" \
        + " * default: <directory> is '.' \n" \
        + " * [name1 value1 [name2 value2] ...] sequence" \
        + "  defines component variable values \n" \
        + " examples:\n" \
        + "       nxscreate stdcomp  \n" \
        + "       nxscreate stdcomp -t source \n" \
        + "       nxscreate stdcomp -t default -c default -m -b\n" \
        + "       nxscreate stdcomp -t slit -c front_slit1 -b" \
        + " xgap slt1x ygap slt1y\n\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument("-c", "--component",
                            help="component name",
                            dest="component", default="")
        parser.add_argument("-t", "--type",
                            help="component type",
                            dest="cptype", default="")
        parser.add_argument("-r", "--server", dest="server",
                            help="configuration server device name")
        parser.add_argument("-p", "--xml-package", dest="xmlpackage",
                            help="xml template package")
        parser.add_argument("-n", "--nolower", action="store_false",
                            default=True, dest="lower",
                            help="do not change aliases into lower case")
        parser.add_argument("-o", "--overwrite", action="store_true",
                            default=False, dest="overwrite",
                            help="overwrite existing component")
        parser.add_argument("-b", "--database", action="store_true",
                            default=False, dest="database",
                            help="store components in"
                            "Configuration Server database")
        parser.add_argument("-d", "--directory",
                            help="output datasource directory",
                            dest="directory", default=".")
        parser.add_argument("-m", "--mandatory", action="store_true",
                            default=False, dest="mandatory",
                            help="set the component as mandatory")
        parser.add_argument("-e", "--external",
                            help="external configuration server",
                            dest="external", default="")
        parser.add_argument("-x", "--file-prefix",
                            help="file prefix, i.e. counter",
                            dest="file", default="")
        parser.add_argument("-y", "--entryname", dest="entryname",
                            help="entry group name (prefix)", default="scan")
        parser.add_argument("-i", "--insname", dest="insname",
                            help="instrument group name", default="instrument")
        parser.add_argument('args', metavar='key value',
                            type=str, nargs='*',
                            help='pairs of (key value) for template variables')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        parser = self._parser
        if not PYTANGO:
            sys.stderr.write("Info: No PyTango installed\n")
            parser.print_help()
            sys.exit(255)

        args = options.args or []

        creator = StandardCPCreator(options, args)
        if options.component and options.cptype:
            if not options.server:
                options.server = checkServer()
                if not options.server and options.database:
                    parser.print_help()
                    sys.exit(0)
            if options.database:
                print("SERVER: %s" % options.server)
            else:
                print("OUTPUT DIR: %s" % options.directory)

            try:
                creator.create()
            except CPExistsException as e:
                print(str(e))
                sys.exit(255)
            except DSExistsException as e:
                print(str(e))
                sys.exit(255)
        elif options.cptype:
            dct = creator.listcomponentvariables()
            print("\nCOMPONENT VARIABLES:")
            for var in sorted(dct.keys()):
                desc = dct[var]
                if not var.startswith('__') and not var.endswith('__'):
                    print("  %s - %s [default: '%s']"
                          % (var, desc['doc'], desc['default']))
        else:
            parser.print_help()
            print("")
            lst = sorted(creator.listcomponenttypes())
            print("\nPOSSIBLE COMPONENT TYPES: \n   %s" % " ".join(lst))


class Comp(Runner):

    """ comp runner"""
    #: (:obj:`str`) command description
    description = "create simple components"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " * with -b: components are created (without datasources)" \
        + " in Configuration Server database\n" \
        + " * without -b: components are created (without datasources)" \
        + " on the local filesystem in -d <directory> \n" \
        + " * default: <directory> is '.' \n" \
        + "            <server> is taken from Tango DB\n" \
        + "            <strategy> is step\n" \
        + "            <type> is NX_FLOAT\n" \
        + "            <chunk> is SCALAR\n" \
        + "            <nexuspath> is " \
        + "\"/\\$var.entryname#'scan'\\$var.serialno:NXentry" \
        + "/instrument/collection/\"\n" \
        + " examples:\n" \
        + "       nxscreate comp counter \n" \
        + "       nxscreate comp -f1 -l -v exp_c01 -b \n" \
        + "       nxscreate comp lambda -d /home/user/xmldir/ \n" \
        + "       nxscreate comp -n " \
        + "\"/\\$var.entryname#'scan'\\$var.serialno:NXentry/instrument/" \
        + "sis3302:NXdetector/collection:NXcollection/\" " \
        + "-v sis3302_1_roi -f1 -l4 " \
        + " -g STEP -t NX_FLOAT64 -k -b -m \n" \
        + "       nxscreate comp -n " \
        + "\"/\\$var.entryname#'scan'\\$var.serialno:NXentry/instrument/" \
        + "eh1_mca01:NXdetector/data\" eh1_mca01 -g STEP -t NX_FLOAT64" \
        + " -i -b -c SPECTRUM\n" \
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            "-v", "--device-prefix", help="device prefix, i.e. exp_c",
            dest="device", default="")
        parser.add_argument(
            "-f", "--first", help="first index",
            dest="first", default="1")
        parser.add_argument(
            "-l", "--last", help="last index",
            dest="last", default=None)
        parser.add_argument(
            "-o", "--overwrite", action="store_true",
            default=False, dest="overwrite",
            help="overwrite existing components")
        parser.add_argument(
            "-a", "--can-fail", action="store_true",
            default=False, dest="canfail",
            help="can fail strategy flag")
        parser.add_argument(
            "-d", "--directory",
            help="output component directory",
            dest="directory", default=".")
        parser.add_argument(
            "-x", "--file-prefix",
            help="file prefix, i.e. counter",
            dest="file", default="")

        parser.add_argument(
            "-n", "--nexuspath",
            help="nexus path with field name",
            dest="nexuspath", default="")

        parser.add_argument(
            "-g", "--strategy",
            help="writing strategy, i.e. "
            "STEP, INIT, FINAL, POSTRUN",
            dest="strategy", default="STEP")
        parser.add_argument(
            "-s", "--datasource-prefix",
            help="datasource-prefix or datasourcename",
            dest="datasource", default="")
        parser.add_argument(
            "-t", "--type",
            help="nexus type of the field",
            dest="type", default="NX_FLOAT")
        parser.add_argument(
            "-u", "--units",
            help="nexus units of the field",
            dest="units", default="")

        parser.add_argument(
            "-k", "--links", action="store_true",
            default=False, dest="fieldlinks",
            help="create links with field name")

        parser.add_argument(
            "-i", "--source-links", action="store_true",
            default=False, dest="sourcelinks",
            help="create links with datasource name")

        parser.add_argument(
            "-b", "--database", action="store_true",
            default=False, dest="database",
            help="store components in "
            "Configuration Server database")

        parser.add_argument(
            "-r", "--server", dest="server",
            help="configuration server device name")

        parser.add_argument(
            "-c", "--chunk", dest="chunk",
            default="SCALAR", help="chunk format, "
            "i.e. SCALAR, SPECTRUM, IMAGE")

        parser.add_argument(
            "-m", "--minimal-device", action="store_true",
            default=False, dest="minimal",
            help="device name without first '0'")

        parser.add_argument(
            'args', metavar='component_name',
            type=str, nargs='*',
            help='component names to be created')

        return parser

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        args = options.args or []
        parser = self._parser
        if options.database and not options.server:
            if not PYTANGO:
                sys.stderr.write("Info: No PyTango installed\n")
                sys.stderr.flush()
                sys.exit(255)

            options.server = checkServer()
            if not options.server:
                parser.print_help()
                sys.exit(0)

        if options.database:
            print("CONFIG SERVER: %s" % options.server)
        else:
            print("OUTPUT DIRECTORY: %s" % options.directory)

        creator = ComponentCreator(options, args)
        try:
            creator.create()
        except WrongParameterError as e:
            sys.stderr.write(str(e))
            sys.stderr.flush()
            parser.print_help()
            sys.exit(255)


class ClientDS(Runner):

    """ clientds runner"""
    #: (:obj:`str`) command description
    description = "create client datasources"

    #: (:obj:`str`) command epilog
    epilog = "" \
             + "\n" \
             + " * with -b: datasources are created" \
             + " in Configuration Server database\n" \
             + " * without -b: datasources are created" \
             + " on the local filesystem in -d <directory> \n" \
             + " * default: <directory> is '.' \n" \
             + "            <server> is taken from Tango DB\n" \
             + " examples:\n" \
             + "       nxscreate clientds starttime -b  \n" \
             + "       nxscreate clientds title -d /home/user/xmldir \n" \
             + "       nxscreate clientds -v exp_c -f1 -l4 -b  \n" \
             + "       nxscreate clientds -v " \
             + "hasppXX:10000/expchan/vfcadc_exp/" \
             + " -f1 -l8  -m -b -s exp_vfc\n"

    def create(self):
        """ parser creator
        """
        parser = self._parser
        parser.add_argument("-v", "--device-prefix",
                            help="device prefix, i.e. exp_c "
                            "(mandatory w/o <name1>)",
                            dest="device", default="")
        parser.add_argument("-f", "--first",
                            help="first index (mandatory w/o <name1>)",
                            dest="first", default="1")
        parser.add_argument("-l", "--last",
                            help="last index (mandatory w/o <name1>)",
                            dest="last", default=None)

        parser.add_argument("-o", "--overwrite", action="store_true",
                            default=False, dest="overwrite",
                            help="overwrite existing datasources")
        parser.add_argument("-d", "--directory",
                            help="output datasource directory",
                            dest="directory", default=".")
        parser.add_argument("-x", "--file-prefix",
                            help="file prefix, i.e. counter",
                            dest="file", default="")

        parser.add_argument("-s", "--datasource-prefix",
                            help="datasource prefix, i.e. counter"
                            " (useful for avoiding duplicated "
                            "datasource names)",
                            dest="dsource", default="")

        parser.add_argument("-b", "--database", action="store_true",
                            default=False, dest="database",
                            help="store datasources in "
                            "Configuration Server database")
        parser.add_argument("-m", "--minimal-device", action="store_true",
                            default=False, dest="minimal",
                            help="device name without first '0'")

        parser.add_argument("-r", "--server", dest="server",
                            help="configuration server device name")

        parser.add_argument('args', metavar='device_name',
                            type=str, nargs='*',
                            help='device names to create')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """

        parser = self._parser
        if options.database and not options.server:
            if not PYTANGO:
                sys.stderr.write("Info: No PyTango installed\n")
                sys.stderr.flush()
                sys.exit(255)

            options.server = checkServer()
            if not options.server:
                parser.print_help()
                sys.exit(0)

        if options.database:
            print("CONFIG SERVER: %s" % options.server)
        else:
            print("OUTPUT DIRECTORY: %s" % options.directory)

        creator = ClientDSCreator(options, options.args or [])
        try:
            creator.create()
        except WrongParameterError as e:
            sys.stderr.write(str(e))
            sys.stderr.flush()
            parser.print_help()
            sys.exit(255)


def main():
    """ the main program function
    """
    description = " Command-line tool for creating NXSConfigServer" \
                  + " configuration of Nexus Files"

    epilog = 'For more help:\n  nxscreate <sub-command> -h'
    parser = NXSArgParser(
        description=description, epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.cmdrunners = [('clientds', ClientDS),
                         ('tangods', TangoDS),
                         ('deviceds', DeviceDS),
                         ('onlinecp', OnlineCP),
                         ('onlineds', OnlineDS),
                         ('poolds', PoolDS),
                         ('stdcomp', StdComp),
                         ('comp', Comp),
                         ('compare', Compare)]
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

    runners[options.subparser].run(options)


if __name__ == "__main__":
    main()
