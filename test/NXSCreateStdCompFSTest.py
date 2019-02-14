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
# import time
# import threading
import PyTango
# import json
from nxstools import nxscreate
from nxstools.xmltemplates import standardComponentVariables

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
class NXSCreateStdCompFSTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

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
        db = PyTango.Database()
        self.host = db.get_db_host().split(".")[0]
        self.port = db.get_db_port()
        self.directory = "."
        self.flags = ""

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

    def runtestexcept(self, argv, exception):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = mystdout = StringIO()
        sys.stderr = mystderr = StringIO()

        old_argv = sys.argv
        sys.argv = argv
        try:
            error = False
            nxscreate.main()
            etxt = None
        except exception as e:
            error = True
            etxt = str(e)
        self.assertEqual(error, True)

        sys.argv = old_argv

        sys.stdout = old_stdout
        sys.stderr = old_stderr
        vl = mystdout.getvalue()
        er = mystderr.getvalue()
        return vl, er, etxt

    # Exception tester
    # \param exception expected exception
    # \param method called method
    # \param args list with method arguments
    # \param kwargs dictionary with method arguments
    def myAssertRaise(self, exception, method, *args, **kwargs):
        try:
            error = False
            method(*args, **kwargs)
        except exception:
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

    def test_stdcomp_typelist(self):
        """ test nxsccreate stdcomp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate stdcomp %s' % self.flags).split(),
            ],
        ]

        try:
            for arg in args:
                vl, er = self.runtest(arg[0])

                self.assertEqual('', er)
                self.assertTrue(vl)
                lines = vl.split("\n")
                self.assertEqual(lines[-3], "POSSIBLE COMPONENT TYPES: ")
                self.assertEqual(
                    lines[-2].split(),
                    ["absorber", "beamstop", "beamtimeid", "chcut",
                     "collect2", "collect3", "common2", "common3",
                     "datasignal", "dcm", "default", "defaultinstrument",
                     "defaultsample", "empty", "keithley", "maia",
                     "maiadimension", "maiaflux", "pinhole",
                     "pointdet", "qbpm", "samplehkl", "slit",
                     "source", "undulator"])
                self.assertEqual(lines[-1], "")
        finally:
            pass

    def test_stdcomp_type_parameters(self):
        """ test nxsccreate stdcomp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        types = ["absorber", "beamstop", "beamtimeid", "chcut",
                 "collect2", "collect3", "common2", "common3",
                 "datasignal", "dcm", "default", "defaultinstrument",
                 "defaultsample", "empty", "keithley", "maia",
                 "maiadimension", "maiaflux", "pinhole",
                 "pointdet", "qbpm", "samplehkl", "slit",
                 "source", "undulator"]
        args = [
                ('nxscreate stdcomp %s -t ' % self.flags).split(),
                ('nxscreate stdcomp %s --type ' % self.flags).split(),
        ]

        try:
            for tp in types:
                for arg in args:
                    cmd = list(arg)
                    cmd.append(tp)
                    vl, er = self.runtest(cmd)

                    self.assertEqual('', er)
                    self.assertTrue(vl)

                    lines = vl.split("\n")
                    self.assertEqual(lines[0], "")
                    self.assertEqual(lines[-1], "")
                    self.assertEqual(lines[1], "COMPONENT VARIABLES:")
                    var = lines[2:-1]

                    self.assertEqual(
                        len(var),
                        len([st for st in standardComponentVariables[tp].keys()
                             if not st.startswith("__")]))
                    for vr in var:
                        vname = vr.split()[0]
                        self.assertTrue(
                             vname in standardComponentVariables[tp].keys())
                        self.assertTrue(
                            standardComponentVariables[tp][vname]['doc'] in vr)
                        default = \
                            standardComponentVariables[tp][vname]['default']
                        if default is None:
                            default = 'None'
                        self.assertTrue(
                            vr.endswith(" [default: '%s']" % default))
        finally:
            pass

    def test_stdcomp_missing_parameters(self):
        """ test nxsccreate stdcomp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        types = [
            "absorber",
            # "beamstop",
            # "beamtimeid",
            # "chcut",
            "collect2",
            "collect3",
            "common2",
            "common3",
            # "datasignal",
            # "dcm",
            # "default",
            # "defaultinstrument",
            # "defaultsample",
            # "empty",
            # "keithley",
            # "maia",
            # "maiadimension",
            # "maiaflux",
            # "pinhole",
            # "pointdet",
            "qbpm",
            # "samplehkl",
            # "slit",
            # "source",
            # "undulator"
        ]

        args = [
            ('nxscreate stdcomp %s -c cptest -t ' % self.flags).split(),
            ('nxscreate stdcomp %s --component cptest --type '
             % self.flags).split(),
        ]

        totest = []
        try:
            for tp in types:
                for arg in args:
                    cp = "cptest"
                    skip = False
                    if self.cpexists(cp):
                        skip = True
                    if not skip:
                        for cp in arg[1]:
                            totest.append(cp)

                        cmd = list(arg)
                        cmd.append(tp)
                        # print(tp)
                        vl, er, txt = self.runtestexcept(cmd, Exception)

                        self.assertEqual('', er)
                        self.assertTrue(vl)
                        # print(txt)
                        lines = vl.split("\n")
                        # self.assertEqual(lines[0], "OUTPUT DIR: .")
                        self.assertEqual(lines[-1], "")
                        self.assertTrue(lines[1].startswith("MISSING"))
                        # print(vl)
                        if self.cpexists(cp):
                            self.deletecp(cp)
        finally:
            for cp in totest:
                if self.cpexists(cp):
                    self.deletecp(cp)

    def test_stdcomp_beamstop(self):
        """ test nxsccreate stdcomp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate stdcomp -t beamstop -c testbeamstop %s' %
                 self.flags).split(),
                'testbeamstop',
                '<?xml version="1.0" ?><definition>\n'
                '  <group name="$var.entryname#\'scan\'$var.serialno" '
                'type="NXentry">\n'
                '    <group name="instrument" type="NXinstrument">\n'
                '      <group name="testbeamstop" type="NXbeam_stop">\n'
                '\t<field name="description" type="NX_CHAR">\n'
                '            <strategy mode="INIT"/>circular</field>\n'
                '        <field name="depends_on" type="NX_CHAR">'
                'transformations/y<strategy mode="INIT"/>\n'
                '        </field>\n'
                '        <group name="transformations" '
                'type="NXtransformations">\n'
                '        </group>\n'
                '      </group>\n'
                '    </group>\n'
                '  </group>\n'
                '</definition>'
            ],
            [
                ('nxscreate stdcomp --type beamstop '
                 '--component testbeamstop %s' %
                 self.flags).split(),
                'testbeamstop',
                '<?xml version="1.0" ?><definition>\n'
                '  <group name="$var.entryname#\'scan\'$var.serialno" '
                'type="NXentry">\n'
                '    <group name="instrument" type="NXinstrument">\n'
                '      <group name="testbeamstop" type="NXbeam_stop">\n'
                '\t<field name="description" type="NX_CHAR">\n'
                '            <strategy mode="INIT"/>circular</field>\n'
                '        <field name="depends_on" type="NX_CHAR">'
                'transformations/y<strategy mode="INIT"/>\n'
                '        </field>\n'
                '        <group name="transformations" '
                'type="NXtransformations">\n'
                '        </group>\n'
                '      </group>\n'
                '    </group>\n'
                '  </group>\n'
                '</definition>'
            ],
        ]

        totest = []
        try:
            for arg in args:
                if not self.cpexists(arg[1]):
                    totest.append(arg[1])

                    vl, er = self.runtest(arg[0])

                    self.assertEqual('', er)
                    self.assertTrue(vl)
                    xml = self.getcp(arg[1])
                    self.assertEqual(arg[2], xml)

                    self.deletecp(arg[1])
        finally:
            for cp in totest:
                if self.cpexists(cp):
                    self.deletecp(cp)


if __name__ == '__main__':
    unittest.main()
