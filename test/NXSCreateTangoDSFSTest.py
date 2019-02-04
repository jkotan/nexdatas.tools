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
class NXSCreateTangoDSFSTest(unittest.TestCase):

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

    def test_tangods_first_last(self):
        """ test nxsccreate tangods file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate tangods -v test/motor/  -l3 %s'
                 % self.flags).split(),
                ['exp_mot01',
                 'exp_mot02',
                 'exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="exp_mot01" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute" '
                    'name="test/motor/01" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="exp_mot02" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute" '
                    'name="test/motor/02" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="exp_mot03" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute" '
                    'name="test/motor/03" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n'
                ],
            ],
            [
                ('nxscreate tangods -v test/motor/  -s my_exp_mot  -l3 %s'
                 % self.flags).split(),
                ['my_exp_mot01',
                 'my_exp_mot02',
                 'my_exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot01" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/motor/01" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot02" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/motor/02" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot03" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/motor/03" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
            [
                ('nxscreate tangods -v test/vm/  -s test_exp_mot -f2 -l3 %s'
                 % self.flags).split(),
                ['test_exp_mot02',
                 'test_exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="test_exp_mot02" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/vm/02" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="test_exp_mot03" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/vm/03" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
        ]

        totest = []
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

                    self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, ds in enumerate(arg[1]):
                        xml = self.getds(ds)
                        self.assertEqual(
                            arg[2][i] % (self.host, self.port), xml)

                    for ds in arg[1]:
                        self.deleteds(ds)
        finally:
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def test_tangods_first_last_fn(self):
        """ test nxsccreate tangods file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate tangods --device test/motor/  --last 3 %s'
                 % self.flags).split(),
                ['exp_mot01',
                 'exp_mot02',
                 'exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="exp_mot01" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute" '
                    'name="test/motor/01" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="exp_mot02" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute" '
                    'name="test/motor/02" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="exp_mot03" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute" '
                    'name="test/motor/03" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n'
                ],
            ],
            [
                ('nxscreate tangods --device test/motor/ '
                 '--datasource-prefix  my_exp_mot  --last 3 %s'
                 % self.flags).split(),
                ['my_exp_mot01',
                 'my_exp_mot02',
                 'my_exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot01" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/motor/01" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot02" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/motor/02" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot03" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/motor/03" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
            [
                ('nxscreate tangods --device test/vm/'
                 ' --datasource-prefix  test_exp_mot --first 2 --last 3 %s'
                 % self.flags).split(),
                ['test_exp_mot02',
                 'test_exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="test_exp_mot02" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/vm/02" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="test_exp_mot03" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/vm/03" port="%s"/>\n'
                    '    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
        ]

        totest = []
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

                    self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, ds in enumerate(arg[1]):
                        xml = self.getds(ds)
                        self.assertEqual(
                            arg[2][i] % (self.host, self.port), xml)

                    for ds in arg[1]:
                        self.deleteds(ds)
        finally:
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def ttest_tangods_minimal(self):
        """ test nxsccreate tangods file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate tangods -v test_exp_cc  -m -f3 -l5 %s'
                 % self.flags).split(),
                ['test_exp_cc3',
                 'test_exp_cc4',
                 'test_exp_cc5'],
                [
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_cc3" type="CLIENT">
    <record name="test_exp_cc3"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_cc4" type="CLIENT">
    <record name="test_exp_cc4"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_cc5" type="CLIENT">
    <record name="test_exp_cc5"/>
  </datasource>
</definition>
""",
                ],
            ],
            [
                ('nxscreate tangods -v test_exp_dd '
                 '--minimal-device --first 3 --last 4 %s'
                 % self.flags).split(),
                ['test_exp_dd3',
                 'test_exp_dd4'],
                [
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_dd3" type="CLIENT">
    <record name="test_exp_dd3"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_dd4" type="CLIENT">
    <record name="test_exp_dd4"/>
  </datasource>
</definition>
""",
                ],
            ],
        ]

        totest = []
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

                    self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, ds in enumerate(arg[1]):
                        xml = self.getds(ds)
                        self.assertEqual(arg[2][i], xml)

                    for ds in arg[1]:
                        self.deleteds(ds)
        finally:
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def ttest_tangods_source_prefix(self):
        """ test nxsccreate tangods file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate tangods -v testcounter -s test_exp_vc  -f3 -l5 %s'
                 % self.flags).split(),
                ['test_exp_vc03',
                 'test_exp_vc04',
                 'test_exp_vc05'],
                [
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_vc03" type="CLIENT">
    <record name="testcounter03"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_vc04" type="CLIENT">
    <record name="testcounter04"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_vc05" type="CLIENT">
    <record name="testcounter05"/>
  </datasource>
</definition>
""",
                ],
            ],
            [
                ('nxscreate tangods --device testdec '
                 '--datasource-prefix test_exp_d '
                 '--first 3 --last 4 %s'
                 % self.flags).split(),
                ['test_exp_d03',
                 'test_exp_d04'],
                [
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_d03" type="CLIENT">
    <record name="testdec03"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_d04" type="CLIENT">
    <record name="testdec04"/>
  </datasource>
</definition>
""",
                ],
            ],
        ]

        totest = []
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

                    self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, ds in enumerate(arg[1]):
                        xml = self.getds(ds)
                        self.assertEqual(arg[2][i], xml)

                    for ds in arg[1]:
                        self.deleteds(ds)
        finally:
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def ttest_tangods_overwrite_false(self):
        """ test nxsccreate tangods file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate tangods -v testcounter -s test_exp_vc  -f3 -l5 %s'
                 % self.flags).split(),
                ['test_exp_vc03',
                 'test_exp_vc04',
                 'test_exp_vc05'],
                [
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_vc03" type="CLIENT">
    <record name="testcounter03"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_vc04" type="CLIENT">
    <record name="testcounter04"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_vc05" type="CLIENT">
    <record name="testcounter05"/>
  </datasource>
</definition>
""",
                ],
                ('nxscreate tangods -v test2counter -s test_exp_vc -f3 -l5 %s'
                 % self.flags).split(),
            ],
            [
                ('nxscreate tangods --device testdec '
                 '--datasource-prefix test_exp_d '
                 '--first 3 --last 4 %s'
                 % self.flags).split(),
                ['test_exp_d03',
                 'test_exp_d04'],
                [
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_d03" type="CLIENT">
    <record name="testdec03"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_d04" type="CLIENT">
    <record name="testdec04"/>
  </datasource>
</definition>
""",
                ],
                ('nxscreate tangods --device test2dec '
                 '--datasource-prefix test_exp_d '
                 '--first 3 --last 4 %s'
                 % self.flags).split(),
            ],
        ]

        totest = []
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

                    self.assertEqual('', er)
                    self.assertTrue(vl)
                    vl, er = self.runtestexcept(arg[3], Exception)

                    self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, ds in enumerate(arg[1]):
                        xml = self.getds(ds)
                        self.assertEqual(arg[2][i], xml)

                    for ds in arg[1]:
                        self.deleteds(ds)
        finally:
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def ttest_tangods_overwrite_true(self):
        """ test nxsccreate tangods file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate tangods -v testcounter -s test_exp_vc  -f3 -l5 %s'
                 % self.flags).split(),
                ['test_exp_vc03',
                 'test_exp_vc04',
                 'test_exp_vc05'],
                [
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_vc03" type="CLIENT">
    <record name="testcounter03"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_vc04" type="CLIENT">
    <record name="testcounter04"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_vc05" type="CLIENT">
    <record name="testcounter05"/>
  </datasource>
</definition>
""",
                ],
                ('nxscreate tangods -v test2counter -o -s test_exp_vc '
                 ' -f3 -l5 %s' % self.flags).split(),
                [
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_vc03" type="CLIENT">
    <record name="test2counter03"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_vc04" type="CLIENT">
    <record name="test2counter04"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_vc05" type="CLIENT">
    <record name="test2counter05"/>
  </datasource>
</definition>
""",
                ],
            ],
            [
                ('nxscreate tangods --device testdec '
                 '--datasource-prefix test_exp_d '
                 '--first 3 --last 4 %s'
                 % self.flags).split(),
                ['test_exp_d03',
                 'test_exp_d04'],
                [
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_d03" type="CLIENT">
    <record name="testdec03"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_d04" type="CLIENT">
    <record name="testdec04"/>
  </datasource>
</definition>
""",
                ],
                ('nxscreate tangods --device test2dec --overwrite '
                 '--datasource-prefix test_exp_d '
                 '--first 3 --last 4 %s'
                 % self.flags).split(),
                [
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_d03" type="CLIENT">
    <record name="test2dec03"/>
  </datasource>
</definition>
""",
                    """<?xml version="1.0" ?>
<definition>
  <datasource name="test_exp_d04" type="CLIENT">
    <record name="test2dec04"/>
  </datasource>
</definition>
""",
                ],
            ],
        ]

        totest = []
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

                    self.assertEqual('', er)
                    self.assertTrue(vl)
                    vl, er = self.runtest(arg[3])

                    self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, ds in enumerate(arg[1]):
                        xml = self.getds(ds)
                        self.assertEqual(arg[4][i], xml)

                    for ds in arg[1]:
                        self.deleteds(ds)
        finally:
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)


if __name__ == '__main__':
    unittest.main()
