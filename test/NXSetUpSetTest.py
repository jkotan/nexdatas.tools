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
# \package test nexdatas
# \file XMLConfiguratorTest.py
# unittests for field Tags running Tango Server
#
import unittest
import os
import sys
import random
import struct
import binascii
import time
import PyTango
from nxstools import nxsetup
import socket
import subprocess

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    import TestMacroServerSetUp
except Exception:
    from . import TestMacroServerSetUp

try:
    import TestPoolSetUp
except Exception as e:
    print(str(e))
    from . import TestPoolSetUp


try:
    import whichcraft
    WHICHCRAFT = True
except Exception:
    WHICHCRAFT = False

try:
    __import__("nxsconfigserver")
    if not WHICHCRAFT or whichcraft.which("NXSConfigServer"):
        CNFSRV = True
    else:
        CNFSRV = False
except Exception:
    CNFSRV = False

try:
    __import__("nxswriter")
    if not WHICHCRAFT or whichcraft.which("NXSDataWriter"):
        DTWRITER = True
    else:
        DTWRITER = False
except Exception:
    DTWRITER = False

try:
    __import__("nxsrecconfig")
    if not WHICHCRAFT or whichcraft.which("NXSRecSelector"):
        RECSEL = True
    else:
        RECSEL = False
except Exception:
    RECSEL = False


if sys.version_info > (3,):
    unicode = str
    long = int


class mytty(object):

    def __init__(self, underlying):
        #        underlying.encoding = 'cp437'
        self.__underlying = underlying

    def __getattr__(self, name):
        return getattr(self.__underlying, name)

    def isatty(self):
        return True


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

# from nxsconfigserver.XMLConfigurator  import XMLConfigurator
# from nxsconfigserver.Merger import Merger
# from nxsconfigserver.Errors import (
# NonregisteredDBRecordError, UndefinedTagError,
#                                    IncompatibleNodeError)
# import nxsconfigserver


def myinput(w, text):
    myio = os.fdopen(w, 'w')
    myio.write(text)

    # myio.close()


# test fixture
class NXSetUpSetTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self.helperror = "Error: too few arguments\n"

        self.helpinfo = """usage: nxsetup [-h]
               {set,restart,start,stop,move-prop,change-prop,add-recorder-path}
               ...

Command-line tool for setting up  NeXus Tango Servers

positional arguments:
  {set,restart,start,stop,move-prop,change-prop,add-recorder-path}
                        sub-command help
    set                 set up NXSConfigServer NXSDataWriter and
                        NXSRecSelector servers
    restart             restart tango server
    start               start tango server
    stop                stop tango server
    move-prop           change property name
    change-prop         change property value
    add-recorder-path   add-recorder-path into MacroServer(s) property

optional arguments:
  -h, --help            show this help message and exit

For more help:
  nxsetup <sub-command> -h
"""

        try:
            # random seed
            self.seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            import time
            # random seed
            self.seed = long(time.time() * 256)  # use fractional seconds

        self.__rnd = random.Random(self.seed)

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        self.__args = '{"host":"localhost", "db":"nxsconfig", ' \
                      '"read_default_file":"/etc/my.cnf", "use_unicode":true}'
        self.__cmps = []
        self.__ds = []
        self.__man = []
        self.children = ("record", "doc", "device", "database", "query",
                         "datasource", "result")

        from os.path import expanduser
        home = expanduser("~")
        self.__args2 = '{"host":"localhost", "db":"nxsconfig", ' \
                       '"read_default_file":"%s/.my.cnf", ' \
                       '"use_unicode":true}' % home
        # self._sv = ServerSetUp.ServerSetUp()
        self.db = PyTango.Database()
        self.tghost = self.db.get_db_host().split(".")[0]
        self.tgport = self.db.get_db_port()
        self.host = socket.gethostname()
        self._ms = TestMacroServerSetUp.TestMacroServerSetUp()
        self._pool = TestPoolSetUp.TestPoolSetUp()

    def checkDevice(self, dvname):

        found = False
        cnt = 0
        while not found and cnt < 1000:
            try:
                sys.stdout.write(".")
                dp = PyTango.DeviceProxy(dvname)
                time.sleep(0.01)
                dp.ping()
                if dp.state() == PyTango.DevState.ON:
                    found = True
                found = True
            except Exception as e:
                print("%s %s" % (self._sv.new_device_info_writer.name, e))
                found = False
            except Exception:
                found = False

            cnt += 1
        self.assertTrue(found)

    def stopServer(self, svname):
        svname, instance = svname.split("/")
        if sys.version_info > (3,):
            with subprocess.Popen(
                    "ps -ef | grep '%s %s' | grep -v grep" %
                    (svname, instance),
                    stdout=subprocess.PIPE, shell=True) as proc:

                pipe = proc.stdout
                res = str(pipe.read(), "utf8").split("\n")
                for r in res:
                    sr = r.split()
                    if len(sr) > 2:
                        subprocess.call(
                            "kill -9 %s" % sr[1], stderr=subprocess.PIPE,
                            shell=True)
                pipe.close()
        else:
            pipe = subprocess.Popen(
                "ps -ef | grep '%s %s' | grep -v grep" %
                (svname, instance),
                stdout=subprocess.PIPE, shell=True).stdout

            res = str(pipe.read()).split("\n")
            for r in res:
                sr = r.split()
                if len(sr) > 2:
                    subprocess.call(
                        "kill -9 %s" % sr[1], stderr=subprocess.PIPE,
                        shell=True)
            pipe.close()

        # HardKillServer does not work
        # admin = nxsetup.SetUp().getStarterName(self.host)
        # adp = PyTango.DeviceProxy(admin)
        # adp.UpdateServersInfo()
        # adp.HardKillServer(svname)

    def unregisterServer(self, svname, dvname):
        self.db.delete_device(dvname)
        self.db.delete_server(svname)

    # opens config server
    # \param args connection arguments
    # \returns NXSConfigServer instance
    def openConfig(self, args):

        found = False
        cnt = 0
        while not found and cnt < 1000:
            try:
                sys.stdout.write(".")
                xmlc = PyTango.DeviceProxy(
                    self._sv.new_device_info_writer.name)
                time.sleep(0.01)
                if xmlc.state() == PyTango.DevState.ON:
                    found = True
                found = True
            except Exception as e:
                print("%s %s" % (self._sv.new_device_info_writer.name, e))
                found = False
            except Exception:
                found = False

            cnt += 1

        if not found:
            raise Exception(
                "Cannot connect to %s"
                % self._sv.new_device_info_writer.name)

        if xmlc.state() == PyTango.DevState.ON:
            xmlc.JSONSettings = args
            xmlc.Open()
        version = xmlc.version
        vv = version.split('.')
        self.revision = long(vv[-1])
        self.version = ".".join(vv[0:3])
        self.label = ".".join(vv[3:-1])

        self.assertEqual(xmlc.state(), PyTango.DevState.OPEN)
        return xmlc

    # closes opens config server
    # \param xmlc XMLConfigurator instance
    def closeConfig(self, xmlc):
        self.assertEqual(xmlc.state(), PyTango.DevState.OPEN)

        xmlc.Close()
        self.assertEqual(xmlc.state(), PyTango.DevState.ON)

    # test starter
    # \brief Common set up
    def setUp(self):
        print("\nsetting up...")
        # self._sv.setUp()
        self._ms.setUp()
        self._pool.setUp()
        print("SEED = %s" % self.seed)

    # test closer
    # \brief Common tear down
    def tearDown(self):
        print("tearing down ...")
        # if self.__cmps:
        #     el = self.openConf()
        #     for cp in self.__cmps:
        #         el.deleteComponent(cp)
        #     el.close()
        # if self.__ds:
        #     el = self.openConf()
        #     for ds in self.__ds:
        #         el.deleteDataSource(ds)
        #     el.close()

        # if self.__man:
        #     el = self.openConf()
        #     el.setMandatoryComponents(self.__man)
        #     el.close()
        # self._sv.tearDown()
        self._pool.tearDown()
        self._ms.tearDown()

    def openConf(self):
        try:
            el = self.openConfig(self.__args)
        except Exception:
            el = self.openConfig(self.__args2)
        return el

    def runtest(self, argv):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = mystdout = StringIO()
        sys.stderr = mystderr = StringIO()

        old_argv = sys.argv
        sys.argv = argv
        nxsetup.main()
        sys.argv = old_argv

        sys.stdout = old_stdout
        sys.stderr = old_stderr
        vl = mystdout.getvalue()
        er = mystderr.getvalue()
        return vl, er

    def runtestexcept(self, argv, exception):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = mystdout = StringIO()
        sys.stderr = mystderr = StringIO()

        old_argv = sys.argv
        sys.argv = argv
        try:
            error = False
            nxsetup.main()
        except exception:
            error = True
        self.assertEqual(error, True)

        sys.argv = old_argv

        sys.stdout = old_stdout
        sys.stderr = old_stderr
        vl = mystdout.getvalue()
        er = mystderr.getvalue()
        return vl, er

    # Exception tester
    # \param exception expected exception
    # \param method called method
    # \param args list with method arguments
    # \param kwargs dictionary with method arguments
    def myAssertRaise(self, exception, method, *args, **kwargs):
        try:
            error = False
            method(*args, **kwargs)
        except Exception:
            error = True
        self.assertEqual(error, True)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_default(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        vl, er = self.runtestexcept(['nxsetup'], SystemExit)
        self.assertTrue(self.helpinfo in vl)
        self.assertEqual(self.helperror, er)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_help(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        helps = ['-h', '--help']
        for hl in helps:
            vl, er = self.runtestexcept(['nxsetup', hl], SystemExit)
            self.assertTrue(self.helpinfo in vl)
            self.assertEqual('', er)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            cnf = nxsetup.knownHosts[self.host]
        else:
            cnf = {'beamline': 'nxs',
                   'masterhost': '%s' % self.host,
                   'user': 'tango',
                   'dbname': 'nxsconfig'}

        cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
        dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
        rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
        cfdvname = "%s/nxsconfigserver/%s" % \
            (cnf['beamline'], cnf["masterhost"])
        dwdvname = "%s/nxsdatawriter/%s" % \
            (cnf['beamline'], cnf["masterhost"])
        rsdvname = "%s/nxsrecselector/%s" % \
            (cnf['beamline'], cnf["masterhost"])

        cfservers = self.db.get_server_list(cfsvname).value_string
        dwservers = self.db.get_server_list(dwsvname).value_string
        rsservers = self.db.get_server_list(rssvname).value_string

        dwdevices = self.db.get_device_exported_for_class(
            "NXSDataWriter").value_string
        cfdevices = self.db.get_device_exported_for_class(
            "NXSConfigServer").value_string
        rsdevices = self.db.get_device_exported_for_class(
            "NXSRecSelector").value_string
        skiptest = False
        if cfsvname in cfservers:
            skiptest = True
        if dwsvname in dwservers:
            skiptest = True
        if rssvname in rsservers:
            skiptest = True
        if cfdvname in cfdevices:
            skiptest = True
        if dwdvname in dwdevices:
            skiptest = True
        if rsdvname in rsdevices:
            skiptest = True

        skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL

        admin = nxsetup.SetUp().getStarterName(self.host)
        if not admin:
            skiptest = True

        commands = ['nxsetup set'.split()]
        for cmd in commands:
            if not skiptest:
                vl, er = self.runtest(cmd)
                self.assertEqual('', er)
                print(vl)
                print(er)
                cfservers = self.db.get_server_list(cfsvname).value_string
                dwservers = self.db.get_server_list(dwsvname).value_string
                rsservers = self.db.get_server_list(rssvname).value_string
                self.assertTrue(cfsvname in cfservers)
                self.assertTrue(dwsvname in dwservers)
                self.assertTrue(rssvname in rsservers)

                cfdevices = self.db.get_device_exported_for_class(
                    "NXSConfigServer").value_string
                dwdevices = self.db.get_device_exported_for_class(
                    "NXSDataWriter").value_string
                rsdevices = self.db.get_device_exported_for_class(
                    "NXSRecSelector").value_string
                self.assertTrue(cfdvname in cfdevices)
                self.assertTrue(dwdvname in dwdevices)
                self.assertTrue(rsdvname in rsdevices)
                self.checkDevice(cfdvname)
                self.checkDevice(dwdvname)
                self.checkDevice(rsdvname)
                self.stopServer(cfsvname)
                self.stopServer(dwsvname)
                self.stopServer(rssvname)
                self.unregisterServer(cfsvname, cfdvname)
                self.unregisterServer(dwsvname, dwdvname)
                self.unregisterServer(rssvname, rsdvname)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set_master_beamline(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            dfcnf = nxsetup.knownHosts[self.host]
        else:
            dfcnf = {'beamline': 'nxs',
                     'masterhost': '%s' % self.host,
                     'user': 'tango',
                     'dbname': 'nxsconfig'}

        cnfs = [dict(dfcnf) for _ in range(4)]

        cnfs[0]['beamline'] = 'testnxs'
        cnfs[0]['masterhost'] = 'haso000'
        cnfs[1]['beamline'] = 'testnxs2'
        cnfs[1]['masterhost'] = 'hasoo12'
        cnfs[2]['beamline'] = 'test2nxs'
        cnfs[2]['masterhost'] = 'hasoo12'
        cnfs[3]['beamline'] = 'testnxs3'
        cnfs[3]['masterhost'] = 'hasoo000'

        for cnf in cnfs:
            cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
            dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
            rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
            cfdvname = "%s/nxsconfigserver/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            dwdvname = "%s/nxsdatawriter/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            rsdvname = "%s/nxsrecselector/%s" % \
                (cnf['beamline'], cnf["masterhost"])

            cfservers = self.db.get_server_list(cfsvname).value_string
            dwservers = self.db.get_server_list(dwsvname).value_string
            rsservers = self.db.get_server_list(rssvname).value_string

            dwdevices = self.db.get_device_exported_for_class(
                "NXSDataWriter").value_string
            cfdevices = self.db.get_device_exported_for_class(
                "NXSConfigServer").value_string
            rsdevices = self.db.get_device_exported_for_class(
                "NXSRecSelector").value_string
            skiptest = False
            if cfsvname in cfservers:
                skiptest = True
            if dwsvname in dwservers:
                skiptest = True
            if rssvname in rsservers:
                skiptest = True
            if cfdvname in cfdevices:
                skiptest = True
            if dwdvname in dwdevices:
                skiptest = True
            if rsdvname in rsdevices:
                skiptest = True

            skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL

            admin = nxsetup.SetUp().getStarterName(self.host)
            if not admin:
                skiptest = True

            commands = [
                ('nxsetup set -b %s -m %s ' %
                 (cnf['beamline'], cnf['masterhost'])).split(),
                ('nxsetup set --beamline %s --masterhost %s ' %
                 (cnf['beamline'], cnf['masterhost'])).split(),
            ]
            for cmd in commands:
                if not skiptest:
                    vl, er = self.runtest(cmd)
                    self.assertEqual('', er)
                    self.assertTrue(vl)
                    cfservers = self.db.get_server_list(cfsvname).value_string
                    dwservers = self.db.get_server_list(dwsvname).value_string
                    rsservers = self.db.get_server_list(rssvname).value_string
                    self.assertTrue(cfsvname in cfservers)
                    self.assertTrue(dwsvname in dwservers)
                    self.assertTrue(rssvname in rsservers)

                    cfdevices = self.db.get_device_exported_for_class(
                        "NXSConfigServer").value_string
                    dwdevices = self.db.get_device_exported_for_class(
                        "NXSDataWriter").value_string
                    rsdevices = self.db.get_device_exported_for_class(
                        "NXSRecSelector").value_string
                    self.assertTrue(cfdvname in cfdevices)
                    self.assertTrue(dwdvname in dwdevices)
                    self.assertTrue(rsdvname in rsdevices)
                    self.checkDevice(cfdvname)
                    self.checkDevice(dwdvname)
                    self.checkDevice(rsdvname)
                    self.stopServer(cfsvname)
                    self.stopServer(dwsvname)
                    self.stopServer(rssvname)
                    self.unregisterServer(cfsvname, cfdvname)
                    self.unregisterServer(dwsvname, dwdvname)
                    self.unregisterServer(rssvname, rsdvname)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set_all(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            dfcnf = nxsetup.knownHosts[self.host]
        else:
            dfcnf = {'beamline': 'nxs',
                     'masterhost': '%s' % self.host,
                     'user': 'tango',
                     'dbname': 'nxsconfig'}

        cnfs = [dict(dfcnf) for _ in range(4)]

        cnfs[0]['beamline'] = 'testnxs'
        cnfs[0]['masterhost'] = 'haso000'
        cnfs[1]['beamline'] = 'testnxs2'
        cnfs[1]['masterhost'] = 'hasoo12'
        cnfs[2]['beamline'] = 'test2nxs'
        cnfs[2]['masterhost'] = 'hasoo12'
        cnfs[3]['beamline'] = 'testnxs3'
        cnfs[3]['masterhost'] = 'hasoo000'

        for cnf in cnfs:
            cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
            dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
            rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
            cfdvname = "%s/nxsconfigserver/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            dwdvname = "%s/nxsdatawriter/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            rsdvname = "%s/nxsrecselector/%s" % \
                (cnf['beamline'], cnf["masterhost"])

            cfservers = self.db.get_server_list(cfsvname).value_string
            dwservers = self.db.get_server_list(dwsvname).value_string
            rsservers = self.db.get_server_list(rssvname).value_string

            dwdevices = self.db.get_device_exported_for_class(
                "NXSDataWriter").value_string
            cfdevices = self.db.get_device_exported_for_class(
                "NXSConfigServer").value_string
            rsdevices = self.db.get_device_exported_for_class(
                "NXSRecSelector").value_string
            skiptest = False
            if cfsvname in cfservers:
                skiptest = True
            if dwsvname in dwservers:
                skiptest = True
            if rssvname in rsservers:
                skiptest = True
            if cfdvname in cfdevices:
                skiptest = True
            if dwdvname in dwdevices:
                skiptest = True
            if rsdvname in rsdevices:
                skiptest = True

            skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL

            admin = nxsetup.SetUp().getStarterName(self.host)
            if not admin:
                skiptest = True

            commands = [
                ('nxsetup set '
                 ' -b %s '
                 ' -m %s '
                 ' -u %s '
                 ' -d %s '
                 % (cnf['beamline'], cnf['masterhost'],
                    cnf['user'], cnf['dbname'])).split(),
                ('nxsetup set '
                 ' --beamline %s '
                 ' --masterhost %s '
                 ' --user %s '
                 ' --database %s '
                 % (cnf['beamline'], cnf['masterhost'],
                    cnf['user'], cnf['dbname'])).split(),
            ]
            for cmd in commands:
                if not skiptest:
                    vl, er = self.runtest(cmd)
                    self.assertEqual('', er)
                    self.assertTrue(vl)
                    cfservers = self.db.get_server_list(cfsvname).value_string
                    dwservers = self.db.get_server_list(dwsvname).value_string
                    rsservers = self.db.get_server_list(rssvname).value_string
                    self.assertTrue(cfsvname in cfservers)
                    self.assertTrue(dwsvname in dwservers)
                    self.assertTrue(rssvname in rsservers)

                    cfdevices = self.db.get_device_exported_for_class(
                        "NXSConfigServer").value_string
                    dwdevices = self.db.get_device_exported_for_class(
                        "NXSDataWriter").value_string
                    rsdevices = self.db.get_device_exported_for_class(
                        "NXSRecSelector").value_string
                    self.assertTrue(cfdvname in cfdevices)
                    self.assertTrue(dwdvname in dwdevices)
                    self.assertTrue(rsdvname in rsdevices)
                    self.checkDevice(cfdvname)
                    self.checkDevice(dwdvname)
                    self.checkDevice(rsdvname)
                    self.stopServer(cfsvname)
                    self.stopServer(dwsvname)
                    self.stopServer(rssvname)
                    self.unregisterServer(cfsvname, cfdvname)
                    self.unregisterServer(dwsvname, dwdvname)
                    self.unregisterServer(rssvname, rsdvname)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set_csjson(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            dfcnf = nxsetup.knownHosts[self.host]
        else:
            dfcnf = {'beamline': 'nxs',
                     'masterhost': '%s' % self.host,
                     'user': 'tango',
                     'dbname': 'nxsconfig'}

        cnfs = [dict(dfcnf) for _ in range(4)]

        cnfs[0]['beamline'] = 'testnxs'
        cnfs[0]['masterhost'] = 'haso000'
        cnfs[1]['beamline'] = 'testnxs2'
        cnfs[1]['masterhost'] = 'hasoo12'
        cnfs[2]['beamline'] = 'test2nxs'
        cnfs[2]['masterhost'] = 'hasoo12'
        cnfs[3]['beamline'] = 'testnxs3'
        cnfs[3]['masterhost'] = 'hasoo000'

        for cnf in cnfs:
            cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
            dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
            rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
            cfdvname = "%s/nxsconfigserver/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            dwdvname = "%s/nxsdatawriter/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            rsdvname = "%s/nxsrecselector/%s" % \
                (cnf['beamline'], cnf["masterhost"])

            cfservers = self.db.get_server_list(cfsvname).value_string
            dwservers = self.db.get_server_list(dwsvname).value_string
            rsservers = self.db.get_server_list(rssvname).value_string

            dwdevices = self.db.get_device_exported_for_class(
                "NXSDataWriter").value_string
            cfdevices = self.db.get_device_exported_for_class(
                "NXSConfigServer").value_string
            rsdevices = self.db.get_device_exported_for_class(
                "NXSRecSelector").value_string
            skiptest = False
            if cfsvname in cfservers:
                skiptest = True
            if dwsvname in dwservers:
                skiptest = True
            if rssvname in rsservers:
                skiptest = True
            if cfdvname in cfdevices:
                skiptest = True
            if dwdvname in dwdevices:
                skiptest = True
            if rsdvname in rsdevices:
                skiptest = True

            skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL

            admin = nxsetup.SetUp().getStarterName(self.host)
            if not admin:
                skiptest = True
            if not os.path.isfile("/home/%s/.my.cnf" % cnf['user']):
                skiptest = True
            csjson = '{"host":"localhost","db":"%s",' \
                     '"use_unicode":true,'\
                     '"read_default_file":"/home/%s/.my.cnf"}' % \
                     (cnf['dbname'], cnf['user'])
            commands = [
                ('nxsetup set '
                 ' -b %s '
                 ' -m %s '
                 ' -j %s '
                 % (cnf['beamline'], cnf['masterhost'], csjson)).split(),
                ('nxsetup set '
                 ' --beamline %s '
                 ' --masterhost %s '
                 ' --csjson %s '
                 % (cnf['beamline'], cnf['masterhost'], csjson)).split(),
            ]
            for cmd in commands:
                if not skiptest:
                    vl, er = self.runtest(cmd)
                    self.assertEqual('', er)
                    self.assertTrue(vl)
                    cfservers = self.db.get_server_list(cfsvname).value_string
                    dwservers = self.db.get_server_list(dwsvname).value_string
                    rsservers = self.db.get_server_list(rssvname).value_string
                    self.assertTrue(cfsvname in cfservers)
                    self.assertTrue(dwsvname in dwservers)
                    self.assertTrue(rssvname in rsservers)

                    cfdevices = self.db.get_device_exported_for_class(
                        "NXSConfigServer").value_string
                    dwdevices = self.db.get_device_exported_for_class(
                        "NXSDataWriter").value_string
                    rsdevices = self.db.get_device_exported_for_class(
                        "NXSRecSelector").value_string
                    self.assertTrue(cfdvname in cfdevices)
                    self.assertTrue(dwdvname in dwdevices)
                    self.assertTrue(rsdvname in rsdevices)
                    self.checkDevice(cfdvname)
                    self.checkDevice(dwdvname)
                    self.checkDevice(rsdvname)
                    self.stopServer(cfsvname)
                    self.stopServer(dwsvname)
                    self.stopServer(rssvname)
                    self.unregisterServer(cfsvname, cfdvname)
                    self.unregisterServer(dwsvname, dwdvname)
                    self.unregisterServer(rssvname, rsdvname)


if __name__ == '__main__':
    unittest.main()
