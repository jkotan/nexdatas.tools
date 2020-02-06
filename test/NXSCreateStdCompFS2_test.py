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
# \file XMLConfigurator_test.py
# unittests for field Tags running Tango Server
#
import unittest
import sys
import shutil
import os


try:
    import NXSCreateStdCompFS_test
except Exception:
    from . import NXSCreateStdCompFS_test


if sys.version_info > (3,):
    unicode = str
    long = int


# test fixture
class NXSCreateStdCompFS2Test(
        NXSCreateStdCompFS_test.NXSCreateStdCompFSTest):

    # constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        NXSCreateStdCompFS_test.NXSCreateStdCompFSTest.__init__(
            self, methodName)

        self.directory = "my_test_nxs"
        self._dircreated = False
        self.flags = " -r testp09/testmcs/testr228  -d %s" % self.directory

    # test starter
    # \brief Common set up
    def setUp(self):
        NXSCreateStdCompFS_test.NXSCreateStdCompFSTest.setUp(self)
        if not os.path.isdir(self.directory):
            os.makedirs(self.directory)
            self._dircreated = True

    # test closer
    # \brief Common tear down
    def tearDown(self):
        NXSCreateStdCompFS_test.NXSCreateStdCompFSTest.tearDown(self)
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
                    ['<?xml version=\'1.0\' encoding=\'utf8\'?>\n'
                     '<definition>\n'
                     '  <group name="$var.entryname#\'scan\'$var.serialno" '
                     'type="NXentry">\n'
                     '    <group name="instrument" type="NXinstrument">\n'
                     '      <group name="testbeamstop1" type="NXbeam_stop">\n'
                     '\t<field name="description" type="NX_CHAR">\n'
                     '            <strategy mode="INIT" />circular</field>\n'
                     '        <field name="depends_on" type="NX_CHAR">'
                     'transformations/y<strategy mode="INIT" />\n'
                     '        </field>\n'
                     '        <group name="transformations" '
                     'type="NXtransformations">\n'
                     '          </group>\n'
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
                    ['<?xml version=\'1.0\' encoding=\'utf8\'?>\n'
                     '<definition>\n'
                     '  <group name="$var.entryname#\'scan\'$var.serialno" '
                     'type="NXentry">\n'
                     '    <group name="instrument" type="NXinstrument">\n'
                     '      <group name="testbeamstop2" type="NXbeam_stop">\n'
                     '\t<field name="description" type="NX_CHAR">\n'
                     '            <strategy mode="INIT" />circular</field>\n'
                     '        <field name="depends_on" type="NX_CHAR">'
                     'transformations/y<strategy mode="INIT" />\n'
                     '        </field>\n'
                     '        <group name="transformations" '
                     'type="NXtransformations">\n'
                     '          </group>\n'
                     '      </group>\n'
                     '    </group>\n'
                     '  </group>\n'
                     '</definition>'],
                    [],
                ],
            ],
        ]

        self.checkxmls(args)

    def test_stdcomp_absorber_file_prefix(self):
        """ test nxsccreate stdcomp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate stdcomp -t absorber -c absorber1 -x tst_ '
                 ' position mot01 '
                 ' %s' % self.flags).split(),
                [
                    ['tst_absorber1'],
                    ['tst_absorber1_foil', 'tst_absorber1_thickness']
                ],
                [
                    ['<?xml version=\'1.0\' encoding=\'utf8\'?>\n'
                     '<definition>\n'
                     '  <group name="$var.entryname#\'scan\'$var.serialno"'
                     ' type="NXentry">\n'
                     '    <group name="instrument" type="NXinstrument">\n'
                     '      <group name="absorber1" type="NXattenuator">\n'
                     '        <group name="collection" type="NXcollection">\n'
                     '          <field name="slidersin_position" '
                     'type="NX_FLOAT64" units="">\n'
                     '          <strategy mode="INIT" />'
                     '$datasources.mot01</field>\n'
                     '\t</group>\n'
                     '        </group>\n'
                     '    </group>\n'
                     '  </group>\n'
                     '</definition>'],
                    ['<?xml version=\'1.0\' encoding=\'utf8\'?>\n'
                     '<definition>\n'
                     '  <datasource name="absorber1_foil" type="PYEVAL">\n'
                     '    <result name="result">\n'
                     'import json\nfoillist = json.loads(\'["Ag", '
                     '"Ag", "Ag", "Ag", '
                     '"", "Al", "Al", '
                     '"Al", "Al"]\')\n'
                     'position = int(float(ds.mot01) + 0.5)\n'
                     'foil = []\nfor pos, mat in enumerate(foillist):\n'
                     '     foil.append(mat if pos &amp; position '
                     'else "")\n'
                     'ds.result = foil'
                     '\n    </result>\n'
                     ' $datasources.mot01</datasource>\n'
                     '</definition>',
                     '<?xml version=\'1.0\' encoding=\'utf8\'?>\n'
                     '<definition>\n'
                     '  <datasource name="absorber1_thickness"'
                     ' type="PYEVAL">\n'
                     '    <result name="result">\n'
                     'import json\n'
                     'thicknesslist = json.loads(\'['
                     '0.5, 0.05, 0.025, 0.0125, 0, 0.1, 0.3, 0.5, 1.0]\')\n'
                     'position = int(float(ds.mot01) + 0.5)\n'
                     'thickness = []\n'
                     'for pos, thick in enumerate(thicknesslist):\n'
                     '     thickness.append(thick if pos &amp; position '
                     'else 0.)\n'
                     'ds.result = thickness\n'
                     '    </result>\n'
                     ' $datasources.mot01</datasource>\n'
                     '</definition>'],
                ],
            ],
            [
                ('nxscreate stdcomp --type absorber --component absorber1 '
                 ' --file-prefix tst_ '
                 ' position mot01 '
                 ' y y '
                 ' attenfactor afactor '
                 ' foil myfoil '
                 ' thickness tkns '
                 ' foillist ["Ag","","Al"] '
                 ' thicknesslist  [0.5,0,1.0] '
                 ' distance 0.5 '
                 ' distanceoffset [0,1,2] '
                 ' dependstop distance '
                 ' transformations transformations '
                 ' %s' % self.flags).split(),
                [
                    ['tst_absorber1'],
                    ['tst_absorber1_foil', 'tst_absorber1_thickness']
                ],
                [
                    ['<?xml version=\'1.0\' encoding=\'utf8\'?>\n'
                     '<definition>\n'
                     '  <group name="$var.entryname#\'scan\'$var.serialno"'
                     ' type="NXentry">\n'
                     '    <group name="instrument" type="NXinstrument">\n'
                     '      <group name="absorber1" type="NXattenuator">\n'
                     '        <field name="type" type="NX_CHAR">\n'
                     '          <strategy mode="INIT" />$datasources.myfoil'
                     '<dimensions rank="1" />\n'
                     '\t</field>\n'
                     '        <field name="thickness" type="NX_CHAR">\n'
                     '          <strategy mode="INIT" />$datasources.tkns'
                     '<dimensions rank="1" />\n'
                     '\t</field>\n'
                     '        <field name="attenuator_transmission" '
                     'type="NX_FLOAT" units="">\n'
                     '          <strategy mode="INIT" />$datasources.afactor'
                     '</field>\n'
                     '\t<group name="collection" type="NXcollection">\n'
                     '          <field name="slidersin_position" '
                     'type="NX_FLOAT64" units="">\n'
                     '          <strategy mode="INIT" />$datasources.mot01'
                     '</field>\n'
                     '\t</group>\n'
                     '        <group name="transformations" '
                     'type="NXtransformations">\n'
                     '          <field depends_on="0.5" name="y" '
                     'type="NX_FLOAT64" units="mm">\n'
                     '            <strategy mode="INIT" />$datasources.y\n'
                     '\t    <attribute name="transformation_type" '
                     'type="NX_CHAR">translation<strategy mode="INIT" />\n'
                     '            </attribute>\n'
                     '            <attribute name="vector" type="NX_FLOAT64">'
                     '0 1 0\n'
                     '\t    <strategy mode="INIT" />\n'
                     '            <dimensions rank="1">\n'
                     '\t      <dim index="1" value="3" />\n'
                     '            </dimensions>\n'
                     '            </attribute>\n'
                     '          </field>\n'
                     '          <field name="" offset_units="m" '
                     'transformation_type="translation" type="NX_FLOAT64" '
                     'units="m">0.5<strategy mode="INIT" />\n'
                     '            <attribute name="vector" type="NX_FLOAT64">'
                     '0 0 1<dimensions rank="1">\n'
                     '                <dim index="1" value="3" />\n'
                     '              </dimensions>\n'
                     '              <strategy mode="INIT" />\n'
                     '            </attribute>\n'
                     '            <attribute name="offset" type="NX_FLOAT64">'
                     '[0,1,2]<dimensions rank="1">\n'
                     '                <dim index="1" value="3" />\n'
                     '              </dimensions>\n'
                     '              <strategy mode="INIT" />\n'
                     '            </attribute>\n'
                     '          </field>\n'
                     '        </group>\n'
                     '        <field name="depends_on" type="NX_CHAR">'
                     'transformations/distance<strategy mode="INIT" />\n'
                     '        </field>\n'
                     '      </group>\n'
                     '    </group>\n'
                     '  </group>\n'
                     '</definition>'],
                    ['<?xml version=\'1.0\' encoding=\'utf8\'?>\n'
                     '<definition>\n'
                     '  <datasource name="absorber1_foil" type="PYEVAL">\n'
                     '    <result name="result">\n'
                     'import json\n'
                     'foillist = json.loads(\'["Ag","","Al"]\')\n'
                     'position = int(float(ds.mot01) + 0.5)\n'
                     'foil = []\n'
                     'for pos, mat in enumerate(foillist):\n'
                     '     foil.append(mat if pos &amp; position else "")\n'
                     'ds.result = foil\n'
                     '    </result>\n'
                     ' $datasources.mot01</datasource>\n'
                     '</definition>',
                     '<?xml version=\'1.0\' encoding=\'utf8\'?>\n'
                     '<definition>\n'
                     '  <datasource'
                     ' name="absorber1_thickness" type="PYEVAL">\n'
                     '    <result name="result">\n'
                     'import json\n'
                     'thicknesslist = json.loads(\'[0.5,0,1.0]\')\n'
                     'position = int(float(ds.mot01) + 0.5)\n'
                     'thickness = []\n'
                     'for pos, thick in enumerate(thicknesslist):\n'
                     '     thickness.append('
                     'thick if pos &amp; position else 0.)\n'
                     'ds.result = thickness\n'
                     '    </result>\n'
                     ' $datasources.mot01</datasource>\n'
                     '</definition>'],
                ],
            ],
        ]

        self.checkxmls(args)


if __name__ == '__main__':
    unittest.main()
