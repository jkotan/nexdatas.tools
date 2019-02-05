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
import sys
import shutil
import os


try:
    import NXSCreateDeviceDSFSTest
except Exception:
    from . import NXSCreateDeviceDSFSTest


if sys.version_info > (3,):
    unicode = str
    long = int


# test fixture
class NXSCreateDeviceDSFS2Test(
        NXSCreateDeviceDSFSTest.NXSCreateDeviceDSFSTest):

    # constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        NXSCreateDeviceDSFSTest.NXSCreateDeviceDSFSTest.__init__(
            self, methodName)

        self.directory = "my_test_nxs"
        self._dircreated = False
        self.flags = " -d %s" % self.directory

    # test starter
    # \brief Common set up
    def setUp(self):
        NXSCreateDeviceDSFSTest.NXSCreateDeviceDSFSTest.setUp(self)
        if not os.path.isdir(self.directory):
            os.makedirs(self.directory)
            self._dircreated = True

    # test closer
    # \brief Common tear down
    def tearDown(self):
        NXSCreateDeviceDSFSTest.NXSCreateDeviceDSFSTest.tearDown(self)
        if self._dircreated:
            shutil.rmtree(self.directory)
            self._dircreated = False

    def test_deviceds_file_prefix(self):
        """ test nxsccreate deviceds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate deviceds -v test/pilatus/01 -x tst_ '
                 'TData TCounts TFileName  %s' % self.flags).split(),
                ['tst_tdata',
                 'tst_tcounts',
                 'tst_tfilename'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="tdata" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute" '
                    'name="test/pilatus/01" port="%s"/>\n'
                    '    <record name="TData"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="tcounts" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute" '
                    'name="test/pilatus/01" port="%s"/>\n'
                    '    <record name="TCounts"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="tfilename" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute" '
                    'name="test/pilatus/01" port="%s"/>\n'
                    '    <record name="TFileName"/>\n'
                    '  </datasource>\n'
                    '</definition>\n'
                ],
            ],
            [
                ('nxscreate deviceds -v test/pe/1 -x t2_ -s testpe_  '
                 'Data FilePrefix FileDir  %s'
                 % self.flags).split(),
                ['t2_testpe_fileprefix',
                 't2_testpe_filedir',
                 't2_testpe_data'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="testpe_fileprefix" type="TANGO">\n'
                    '    <device group="testpe_" hostname="%s" '
                    'member="attribute"'
                    ' name="test/pe/1" port="%s"/>\n'
                    '    <record name="FilePrefix"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="testpe_filedir" type="TANGO">\n'
                    '    <device group="testpe_" hostname="%s" '
                    'member="attribute"'
                    ' name="test/pe/1" port="%s"/>\n'
                    '    <record name="FileDir"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="testpe_data" type="TANGO">\n'
                    '    <device group="testpe_" hostname="%s" '
                    'member="attribute"'
                    ' name="test/pe/1" port="%s"/>\n'
                    '    <record name="Data"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
            [
                ('nxscreate deviceds -v test/lambda/1  LastImage FileName '
                 '--datasource-prefix test_lmb_  %s --file-prefix my_'
                 % self.flags).split(),
                ['my_test_lmb_lastimage',
                 'my_test_lmb_filename'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="test_lmb_lastimage" type="TANGO">\n'
                    '    <device group="test_lmb_" hostname="%s" '
                    'member="attribute"'
                    ' name="test/lambda/1" port="%s"/>\n'
                    '    <record name="LastImage"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="test_lmb_filename" type="TANGO">\n'
                    '    <device group="test_lmb_" hostname="%s" '
                    'member="attribute"'
                    ' name="test/lambda/1" port="%s"/>\n'
                    '    <record name="FileName"/>\n'
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

                    if er:
                        self.assertEqual(
                            "Info: NeXus hasn't been setup yet. \n\n", er)
                    else:
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

    def ttest_deviceds_file_prefix(self):
        """ test nxsccreate deviceds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate deviceds --device test/motor/ -x my_ '
                 '--datasource-prefix exp_mot -a Data  --last 3 %s'
                 % self.flags).split(),
                ['my_exp_mot01',
                 'my_exp_mot02',
                 'my_exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="exp_mot01" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/motor/01" port="%s"/>\n'
                    '    <record name="Data"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="exp_mot02" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/motor/02" port="%s"/>\n'
                    '    <record name="Data"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="exp_mot03" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/motor/03" port="%s"/>\n'
                    '    <record name="Data"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
            [
                ('nxscreate deviceds --device test/vm/ '
                 '--file-prefix test_exp_ '
                 ' --datasource-prefix mot -a Voltage '
                 '--first 2 --last 3 %s'
                 % self.flags).split(),
                ['test_exp_mot02',
                 'test_exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="mot02" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/vm/02" port="%s"/>\n'
                    '    <record name="Voltage"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="mot03" type="TANGO">\n'
                    '    <device hostname="%s" member="attribute"'
                    ' name="test/vm/03" port="%s"/>\n'
                    '    <record name="Voltage"/>\n'
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

                    if er:
                        self.assertEqual(
                            "Info: NeXus hasn't been setup yet. \n\n", er)
                    else:
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


if __name__ == '__main__':
    unittest.main()
