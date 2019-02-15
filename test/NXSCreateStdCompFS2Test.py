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
    import NXSCreateStdCompFSTest
except Exception:
    from . import NXSCreateStdCompFSTest


if sys.version_info > (3,):
    unicode = str
    long = int


# test fixture
class NXSCreateStdCompFS2Test(
        NXSCreateStdCompFSTest.NXSCreateStdCompFSTest):

    # constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        NXSCreateStdCompFSTest.NXSCreateStdCompFSTest.__init__(
            self, methodName)

        self.directory = "my_test_nxs"
        self._dircreated = False
        self.flags = " -d %s" % self.directory

    # test starter
    # \brief Common set up
    def setUp(self):
        NXSCreateStdCompFSTest.NXSCreateStdCompFSTest.setUp(self)
        if not os.path.isdir(self.directory):
            os.makedirs(self.directory)
            self._dircreated = True

    # test closer
    # \brief Common tear down
    def tearDown(self):
        NXSCreateStdCompFSTest.NXSCreateStdCompFSTest.tearDown(self)
        if self._dircreated:
            shutil.rmtree(self.directory)
            self._dircreated = False

    def test_stdcomp_beamstop_fileprefix(self):
        """ test nxsccreate stdcomp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate stdcomp  -x test_ -t beamstop -c testbeamstop1 '
                 '%s' % self.flags).split(),
                [
                    ['test_testbeamstop1'],
                    []
                ],
                [
                    ['<?xml version="1.0" ?><definition>\n'
                     '  <group name="$var.entryname#\'scan\'$var.serialno" '
                     'type="NXentry">\n'
                     '    <group name="instrument" type="NXinstrument">\n'
                     '      <group name="testbeamstop1" type="NXbeam_stop">\n'
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
                     '</definition>'],
                    [],
                ],
            ],
            [
                ('nxscreate stdcomp  --file-prefix test_ --type beamstop '
                 '--component testbeamstop2 %s' %
                 self.flags).split(),
                [
                    ['test_testbeamstop2'],
                    []
                ],
                [
                    ['<?xml version="1.0" ?><definition>\n'
                     '  <group name="$var.entryname#\'scan\'$var.serialno" '
                     'type="NXentry">\n'
                     '    <group name="instrument" type="NXinstrument">\n'
                     '      <group name="testbeamstop2" type="NXbeam_stop">\n'
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
                     '</definition>'],
                    [],
                ],
            ],
        ]

        self.checkxmls(args)


if __name__ == '__main__':
    unittest.main()
