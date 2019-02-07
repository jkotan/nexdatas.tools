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
class NXSCreateOnlineDSFSTest(unittest.TestCase):

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
        self.flags = "-d . "

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

    def test_onlineds_stepping_motor(self):
        """ test nxsccreate onlineds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = """<?xml version="1.0"?>
<hw>
<device>
 <name>my_exp_mot01</name>
 <type>stepping_motor</type>
 <module>oms58</module>
 <device>p09/motor/exp.01</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_exp</controller>
 <channel>1</channel>
 <rootdevicename>p09/motor/exp</rootdevicename>
</device>
<device>
 <name>my_exp_mot02</name>
 <type>stepping_motor</type>
 <module>oms58</module>
 <device>p09/motor/exp.02</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_exp</controller>
 <channel>2</channel>
 <rootdevicename>p09/motor/exp</rootdevicename>
</device>
<device>
 <name>my_exp_mot03</name>
 <type>stepping_motor</type>
 <module>oms58</module>
 <device>p09/motor/exp.03</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_exp</controller>
 <channel>3</channel>
 <rootdevicename>p09/motor/exp</rootdevicename>
</device>
</hw>
"""

        args = [
            [
                ('nxscreate onlineds %s %s'
                 % (fname, self.flags)).split(),
                ['my_exp_mot01',
                 'my_exp_mot02',
                 'my_exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot01" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/motor/exp.01" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot02" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/motor/exp.02" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot03" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/motor/exp.03" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
        ]

        totest = []
        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        with open(fname, "w") as fl:
            fl.write(xml)
        try:
            for arg in args:
                skip = False
                for ds in arg[1]:
                    if self.dsexists(ds):
                        skip = True
                if not skip:
                    for ds in arg[1]:
                        totest.append(ds)

                    vl, er = self.runtest(arg[0])

                    if er:
                        self.assertTrue(er.startswith(
                            "Info"))
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, ds in enumerate(arg[1]):
                        xml = self.getds(ds)
                        self.assertEqual(
                            arg[2][i], xml)

                    for ds in arg[1]:
                        self.deleteds(ds)
        finally:
            os.remove(fname)
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)


if __name__ == '__main__':
    unittest.main()
