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
# import threading
import PyTango
# import json
from nxstools import nxscreate


try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


if sys.version_info > (3,):
    unicode = str
    long = int


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


# test fixture
class NXSCreateClientDSFSTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self.helperror = "Error: too few arguments\n"

        self.helpinfo = """usage: nxscreate [-h]
                 {clientds,tangods,deviceds,onlinecp,onlineds,poolds,stdcomp,comp,compare}
                 ...

 Command-line tool for creating NXSConfigServer configuration of Nexus Files

positional arguments:
  {clientds,tangods,deviceds,onlinecp,onlineds,poolds,stdcomp,comp,compare}
                        sub-command help
    clientds            create client datasources
    tangods             create tango datasources
    deviceds            create datasources for all device attributes
    onlinecp            create component from online.xml file
    onlineds            create datasources from online.xml file
    poolds              create datasources from sardana pool device
    stdcomp             create component from the standard templates
    comp                create simple components
    compare             compare two online.xml files

optional arguments:
  -h, --help            show this help message and exit

For more help:
  nxscreate <sub-command> -h

"""

        try:
            # random seed
            self.seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            import time
            # random seed
            self.seed = long(time.time() * 256)  # use fractional seconds

        self._rnd = random.Random(self.seed)

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        self.__args = '{"host":"localhost", "db":"nxsconfig", ' \
                      '"read_default_file":"/etc/my.cnf", "use_unicode":true}'

        # home = expanduser("~")

        self.directory = "."
        self.flags = ""

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

    # sets xmlconfiguration
    # \param xmlc configuration instance
    # \param xml xml configuration string
    def setXML(self, xmlc, xml):
        xmlc.XMLString = xml

    # gets xmlconfiguration
    # \param xmlc configuration instance
    # \returns xml configuration string
    def getXML(self, xmlc):
        return xmlc.XMLString

    # test starter
    # \brief Common set up
    def setUp(self):
        print("\nsetting up...")
        print("SEED = %s" % self.seed)

    # test closer
    # \brief Common tear down
    def tearDown(self):
        print("tearing down ...")

    def openConf(self):
        pass
        try:
            el = self.openConfig(self.__args)
        except Exception:
            el = self.openConfig(self.__args2)
        return el

    def dsexists(self, name):
        return os.path.isfile("%s/%s.ds.xml" % (self.directory, name))

    def cpexists(self, name):
        return os.path.isfile("%s/%s.xml" % (self.directory, name))

    def getds(self, name):
        fl = open("%s/%s.ds.xml" % (self.directory, name), 'r')
        xml = fl.read()
        fl.close()
        return xml

    def getcp(self, name):
        fl = open("%s/%s.xml" % (self.directory, name), 'r')
        xml = fl.read()
        fl.close()
        return xml

    def deleteds(self, name):
        os.remove("%s/%s.ds.xml" % (self.directory, name))

    def deletecp(self, name):
        os.remove("%s/%s.xml" % (self.directory, name))

    def runtest(self, argv):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = mystdout = StringIO()
        sys.stderr = mystderr = StringIO()

        old_argv = sys.argv
        sys.argv = argv
        nxscreate.main()
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

    # sets selection configuration
    # \param selectionc configuration instance
    # \param selection selection configuration string
    def setSelection(self, selectionc, selection):
        selectionc.selection = selection

    # gets selectionconfiguration
    # \param selectionc configuration instance
    # \returns selection configuration string
    def getSelection(self, selectionc):
        return selectionc.selection

    def test_clientds_simple(self):
        """ test nxsccreate clientds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate clientds starttimetest %s' % self.flags).split(),
                'starttimetest',
                """<?xml version="1.0" ?>
<definition>
  <datasource name="starttimetest" type="CLIENT">
    <record name="starttimetest"/>
  </datasource>
</definition>
"""
            ],
            [
                ('nxscreate clientds endtimetest %s' % self.flags).split(),
                'endtimetest',
                """<?xml version="1.0" ?>
<definition>
  <datasource name="endtimetest" type="CLIENT">
    <record name="endtimetest"/>
  </datasource>
</definition>
"""
            ],
            [
                ('nxscreate clientds wwwtest %s' % self.flags).split(),
                'wwwtest',
                """<?xml version="1.0" ?>
<definition>
  <datasource name="wwwtest" type="CLIENT">
    <record name="wwwtest"/>
  </datasource>
</definition>
"""
            ],
            [
                ('nxscreate clientds abstest %s' % self.flags).split(),
                'abstest',
                """<?xml version="1.0" ?>
<definition>
  <datasource name="abstest" type="CLIENT">
    <record name="abstest"/>
  </datasource>
</definition>
"""
            ],
        ]

        totest = []
        try:
            for arg in args:
                if not self.dsexists(arg[1]):
                    totest.append(arg[1])

                    vl, er = self.runtest(arg[0])

                    self.assertEqual('', er)
                    self.assertTrue(vl)
                    xml = self.getds(arg[1])
                    self.assertEqual(arg[2], xml)

                    self.deleteds(arg[1])
        finally:
            for arg in totest:
                if self.dsexists(arg[1]):
                    self.deleteds(arg[1])


if __name__ == '__main__':
    unittest.main()
