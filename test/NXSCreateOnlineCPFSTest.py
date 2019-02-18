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
import nxstools
from nxstools import nxscreate
from nxstools import nxsdevicetools

try:
    import nxsextrasp00
except ImportError:
    from . import nxsextrasp00

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    import TestServerSetUp
except ImportError:
    from . import TestServerSetUp


if sys.version_info > (3,):
    unicode = str
    long = int


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


# test fixture
class NXSCreateOnlineCPFSTest(unittest.TestCase):

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
        # self.flags = " -d -r testp09/testmcs/testr228 "
        self.device = 'testp09/testmcs/testr228'

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

    def checkxmls(self, args, fname):
        """ check xmls of components and datasources
        """

        dstotest = []
        cptotest = []
        try:
            for arg in args:
                skip = False
                for cp in arg[1][0]:
                    if self.cpexists(cp):
                        skip = True
                for ds in arg[1][1]:
                    if self.dsexists(ds):
                        skip = True
                if not skip:
                    for ds in arg[1][1]:
                        dstotest.append(ds)
                    for cp in arg[1][0]:
                        cptotest.append(cp)

                    vl, er = self.runtest(arg[0])
                    # print(vl)
                    if er:
                        self.assertEqual(
                            "Info: NeXus hasn't been setup yet. \n\n", er)
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, ds in enumerate(arg[1][1]):
                        xml = self.getds(ds)
                        self.assertEqual(arg[2][1][i], xml)
                    for i, cp in enumerate(arg[1][0]):
                        xml = self.getcp(cp)
                        self.assertEqual(arg[2][0][i], xml)

                    for ds in arg[1][1]:
                        self.deleteds(ds)
                    for cp in arg[1][0]:
                        self.deletecp(cp)

        finally:
            os.remove(fname)
            for cp in cptotest:
                if self.cpexists(cp):
                    self.deletecp(cp)
            for ds in dstotest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def test_onlinecp_typelist_none(self):
        """ test nxsccreate stdcomp file system
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
                ('nxscreate onlinecp %s %s'
                 % (fname, self.flags)).split(),
            ],
        ]

        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        with open(fname, "w") as fl:
            fl.write(xml)
        try:
            for arg in args:
                vl, er = self.runtest(arg[0])

                if er:
                    self.assertTrue(er.startswith(
                        "Info: NeXus hasn't been setup yet. \n\n"))
                else:
                    self.assertEqual('', er)
                self.assertTrue(vl)
                lines = vl.split("\n")
                self.assertEqual(lines[-3], "POSSIBLE COMPONENTS: ")
                self.assertEqual(
                    lines[-2].split(),
                    [])
                self.assertEqual(lines[-1], "")
        finally:
            os.remove(fname)

    def test_onlinecp_typelist_single(self):
        """ test nxsccreate onlinecp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = '<?xml version="1.0"?>\n' \
              '<hw>\n' \
              '<device>\n' \
              '    <name>%s</name>\n' \
              '    <type>type_tango</type>\n' \
              '    <module>%s</module>\n' \
              '    <device>%s</device>\n' \
              '    <control>tango</control>\n' \
              '    <hostname>%s:%s</hostname>\n' \
              '</device>\n' \
              '</hw>\n'

        command = ('nxscreate onlinecp %s %s'
                   % (fname, self.flags)).split()

        args = [
            ['my_test_%s' % ky, "mytest/%s/00" % ky, vl, ky]
            for ky, vl in nxstools.xmltemplates.moduleTemplateFiles.items()
        ]

        try:
            for arg in args:
                ds = arg[0]
                dv = arg[1]
                attr = list(arg[2])
                module = arg[3]
                if os.path.isfile(fname):
                    raise Exception("Test file %s exists" % fname)
                with open(fname, "w") as fl:
                    fl.write(xml % (ds, module, dv, self.host, self.port))
                try:

                    skip = False
                    for el in attr:
                        if self.dsexists(
                                "%s_%s" % (ds, el.lower())
                                if el else ds):
                            skip = True
                    if not skip:

                        vl, er = self.runtest(command)

                        if er:
                            self.assertTrue(er.startswith(
                                "Info"))
                        else:
                            self.assertEqual('', er)
                        self.assertTrue(vl)
                        lines = vl.split("\n")
                        self.assertEqual(lines[-3], "POSSIBLE COMPONENTS: ")
                        self.assertEqual(
                            lines[-2].split(), [ds])
                finally:
                    os.remove(fname)
        finally:
            pass

    def test_onlinecp_typelist_multiple(self):
        """ test nxsccreate onlinecp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        startxml = '<?xml version="1.0"?>\n' \
                   '<hw>\n'

        dsxml = '<device>\n' \
                '    <name>%s</name>\n' \
                '    <type>type_tango</type>\n' \
                '    <module>%s</module>\n' \
                '    <device>%s</device>\n' \
                '    <control>tango</control>\n' \
                '    <hostname>%s:%s</hostname>\n'\
                '</device>\n'
        endxml = '</hw>\n'

        command = ('nxscreate onlinecp %s %s'
                   % (fname, self.flags)).split()

        args = [
            ['my_test_%s' % ky, "mytest/%s/00" % ky, vl, ky]
            for ky, vl in nxstools.xmltemplates.moduleTemplateFiles.items()
        ]
        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        with open(fname, "w") as fl:
            fl.write(startxml)
            for arg in args:
                ds = arg[0]
                dv = arg[1]
                module = arg[3]
                fl.write(dsxml % (ds, module, dv, self.host, self.port))
            fl.write(endxml)

        try:
            dss = [arg[0] for arg in args]
            vl, er = self.runtest(command)

            if er:
                self.assertTrue(er.startswith(
                    "Info"))
            else:
                self.assertEqual('', er)
            self.assertTrue(vl)
            lines = vl.split("\n")
            self.assertEqual(lines[-3], "POSSIBLE COMPONENTS: ")
            self.assertEqual(
                sorted(lines[-2].split()), sorted(dss))
        finally:
            os.remove(fname)

    def test_onlinecp_pilatus(self):
        """ test nxsccreate stdcomp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = """<?xml version="1.0"?>
<hw>
<device>
 <name>mypilatus</name>
 <type>type_tango</type>
 <module>pilatus</module>
 <device>p09/pilatus/exp.01</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_exp</controller>
 <channel>1</channel>
 <rootdevicename>p09/motor/exp</rootdevicename>
</device>
</hw>
"""
        args = [
            [
                ('nxscreate onlinecp -c mypilatus '
                 ' %s %s ' % (fname,  self.flags)).split(),
                [
                    ['mypilatus'],
                    [
                        'mypilatus_delaytime',
                        'mypilatus_description',
                        'mypilatus_exposureperiod',
                        'mypilatus_exposuretime',
                        'mypilatus_filedir',
                        'mypilatus_filepostfix',
                        'mypilatus_fileprefix',
                        'mypilatus_filestartnum_cb',
                        'mypilatus_filestartnum',
                        'mypilatus_lastimagetaken',
                        'mypilatus_nbexposures',
                        'mypilatus_nbframes',
                        'mypilatus_postrun'
                    ],
                ],
                [
                    ['<?xml version=\'1.0\'?>\n'
                     '<definition>\n'
                     '  <group type="NXentry" '
                     'name="$var.entryname#\'scan\'$var.serialno">\n'
                     '    <group type="NXinstrument" name="instrument">\n'
                     '      <group type="NXdetector" name="mypilatus">\n'
                     '        <field units="um" type="NX_FLOAT64" '
                     'name="x_pixel_size">172</field>\n'
                     '        <field units="um" type="NX_FLOAT64" '
                     'name="y_pixel_size">172</field>\n'
                     '        <field type="NX_CHAR" name="layout">area'
                     '</field>\n'
                     '        <field type="NX_CHAR" name="description">'
                     '$datasources.mypilatus_description'
                     '<strategy mode="INIT"/>\n'
                     '        </field>\n'
                     '        <group type="NXcollection" name="collection">\n'
                     '          <field units="s" type="NX_FLOAT64" '
                     'name="delay_time">\n'
                     '            <strategy mode="FINAL"/>'
                     '$datasources.mypilatus_delaytime</field>\n'
                     '          <field units="s" type="NX_FLOAT64" '
                     'name="exposure_period">\n'
                     '            <strategy mode="FINAL"/>'
                     '$datasources.mypilatus_exposureperiod</field>\n'
                     '          <field units="s" type="NX_FLOAT64" '
                     'name="exposure_time">\n'
                     '            <strategy mode="FINAL"/>'
                     '$datasources.mypilatus_exposuretime</field>\n'
                     '          <field type="NX_UINT64" name="nb_frames">\n'
                     '            <strategy mode="FINAL"/>'
                     '$datasources.mypilatus_nbframes</field>\n'
                     '          <field type="NX_UINT64" name="nb_exposures">\n'
                     '            <strategy mode="FINAL"/>'
                     '$datasources.mypilatus_nbexposures</field>\n'
                     '          <field type="NX_CHAR" name="postrun">'
                     '$datasources.mypilatus_postrun<strategy mode="FINAL"/>\n'
                     '          </field>\n'
                     '          <field type="NX_CHAR" name="file_dir">\n'
                     '            <strategy mode="FINAL"/>'
                     '$datasources.mypilatus_filedir</field>\n'
                     '          <field type="NX_CHAR" name="file_postfix">\n'
                     '            <strategy mode="FINAL"/>'
                     '$datasources.mypilatus_filepostfix</field>\n'
                     '          <field type="NX_CHAR" name="file_prefix">\n'
                     '            <strategy mode="FINAL"/>'
                     '$datasources.mypilatus_fileprefix</field>\n'
                     '          <field type="NX_CHAR" '
                     'name="last_image_taken">\n'
                     '            <strategy mode="FINAL"/>'
                     '$datasources.mypilatus_lastimagetaken</field>\n'
                     '          <field type="NX_UINT" '
                     'name="signal">1</field>\n'
                     '          <field type="NX_CHAR" '
                     'name="file_start_index_num">\n'
                     '            <strategy mode="STEP"/>'
                     '$datasources.mypilatus_filestartnum_cb</field>\n'
                     '        </group>\n'
                     '      </group>\n'
                     '    </group>\n'
                     '    <group type="NXdata" name="data">\n'
                     '      <link '
                     'target="$var.entryname#\'scan\'$var.serialno/'
                     'instrument/mypilatus/data" name="mypilatus"/>\n'
                     '    </group>\n'
                     '  </group>\n'
                     '</definition>\n'],
                    ['<?xml version="1.0" ?>\n'
                     '<definition>\n'
                     '  <datasource name="mypilatus_delaytime" type="TANGO">\n'
                     '    <device group="mypilatus_" hostname="haso000" '
                     'member="attribute" '
                     'name="p09/pilatus/exp.01" port="10000"/>\n'
                     '    <record name="DelayTime"/>\n'
                     '  </datasource>\n'
                     '</definition>\n'
                     '',
                     '<?xml version=\'1.0\'?>\n'
                     '<definition>\n'
                     '  <datasource type="PYEVAL" '
                     'name="mypilatus_description">\n'
                     '    <result name="result">\n'
                     'if "mypilatus_filestartnum" in commonblock:\n'
                     '    commonblock.pop("mypilatus_filestartnum")\n'
                     'ds.result = "mypilatus"</result>\n'
                     '  </datasource>\n'
                     '</definition>\n'
                     '',
                     '<?xml version="1.0" ?>\n'
                     '<definition>\n'
                     '  <datasource name="mypilatus_exposureperiod" '
                     'type="TANGO">\n'
                     '    <device group="mypilatus_" hostname="haso000" '
                     'member="attribute" name="p09/pilatus/exp.01" '
                     'port="10000"/>\n'
                     '    <record name="ExposurePeriod"/>\n'
                     '  </datasource>\n'
                     '</definition>\n'
                     '',
                     '<?xml version="1.0" ?>\n'
                     '<definition>\n'
                     '  <datasource name="mypilatus_exposuretime" '
                     'type="TANGO">\n'
                     '    <device group="mypilatus_" hostname="haso000" '
                     'member="attribute" name="p09/pilatus/exp.01" '
                     'port="10000"/>\n'
                     '    <record name="ExposureTime"/>\n'
                     '  </datasource>\n'
                     '</definition>\n'
                     '',
                     '<?xml version="1.0" ?>\n'
                     '<definition>\n'
                     '  <datasource name="mypilatus_filedir" '
                     'type="TANGO">\n'
                     '    <device group="mypilatus_" hostname="haso000" '
                     'member="attribute" name="p09/pilatus/exp.01" '
                     'port="10000"/>\n'
                     '    <record name="FileDir"/>\n'
                     '  </datasource>\n'
                     '</definition>\n'
                     '',
                     '<?xml version="1.0" ?>\n'
                     '<definition>\n'
                     '  <datasource name="mypilatus_filepostfix" '
                     'type="TANGO">\n'
                     '    <device group="mypilatus_" hostname="haso000" '
                     'member="attribute" name="p09/pilatus/exp.01" '
                     'port="10000"/>\n'
                     '    <record name="FilePostfix"/>\n'
                     '  </datasource>\n'
                     '</definition>\n'
                     '',
                     '<?xml version="1.0" ?>\n'
                     '<definition>\n'
                     '  <datasource name="mypilatus_fileprefix" '
                     'type="TANGO">\n'
                     '    <device group="mypilatus_" hostname="haso000" '
                     'member="attribute" name="p09/pilatus/exp.01" '
                     'port="10000"/>\n'
                     '    <record name="FilePrefix"/>\n'
                     '  </datasource>\n'
                     '</definition>\n'
                     '',
                     '<?xml version=\'1.0\'?>\n'
                     '<definition>\n'
                     '  <datasource type="PYEVAL" '
                     'name="mypilatus_filestartnum_cb">\n'
                     '    <result name="result">\n'
                     'if "mypilatus_filestartnum" not in commonblock:\n'
                     '    commonblock["mypilatus_filestartnum"] = '
                     'ds.mypilatus_filestartnum - ds.mypilatus_nbframes + 1\n'
                     'ds.result = ds.mypilatus_filestartnum - '
                     'ds.mypilatus_nbframes</result>\n'
                     ' $datasources.mypilatus_filestartnum\n'
                     ' $datasources.mypilatus_nbframes</datasource>\n'
                     '</definition>\n'
                     '',
                     '<?xml version="1.0" ?>\n'
                     '<definition>\n'
                     '  <datasource name="mypilatus_filestartnum" '
                     'type="TANGO">\n'
                     '    <device group="mypilatus_" hostname="haso000" '
                     'member="attribute" name="p09/pilatus/exp.01" '
                     'port="10000"/>\n'
                     '    <record name="FileStartNum"/>\n'
                     '  </datasource>\n'
                     '</definition>\n'
                     '',
                     '<?xml version="1.0" ?>\n'
                     '<definition>\n'
                     '  <datasource name="mypilatus_lastimagetaken" '
                     'type="TANGO">\n'
                     '    <device group="mypilatus_" hostname="haso000" '
                     'member="attribute" name="p09/pilatus/exp.01" '
                     'port="10000"/>\n'
                     '    <record name="LastImageTaken"/>\n'
                     '  </datasource>\n'
                     '</definition>\n'
                     '',
                     '<?xml version="1.0" ?>\n'
                     '<definition>\n'
                     '  <datasource name="mypilatus_nbexposures" '
                     'type="TANGO">\n'
                     '    <device group="mypilatus_" hostname="haso000" '
                     'member="attribute" name="p09/pilatus/exp.01" '
                     'port="10000"/>\n'
                     '    <record name="NbExposures"/>\n'
                     '  </datasource>\n'
                     '</definition>\n'
                     '',
                     '<?xml version="1.0" ?>\n'
                     '<definition>\n'
                     '  <datasource name="mypilatus_nbframes" '
                     'type="TANGO">\n'
                     '    <device group="mypilatus_" hostname="haso000" '
                     'member="attribute" name="p09/pilatus/exp.01" '
                     'port="10000"/>\n'
                     '    <record name="NbFrames"/>\n'
                     '  </datasource>\n'
                     '</definition>\n'
                     '',
                     '<?xml version=\'1.0\'?>\n'
                     '<definition>\n'
                     '  <datasource type="PYEVAL" name="mypilatus_postrun">\n'
                     '    <result name="result">\n'
                     'unixdir = (ds.mypilatus_filedir).replace("\\\\","/")\n'
                     'if len(unixdir)> 1 and unixdir[1] == ":":\n'
                     '    unixdir = "/data" + unixdir[2:]\n'
                     'if unixdir and unixdir[-1] == "/":\n'
                     '    unixdir = unixdir[:-1]\n'
                     'filestartnum = commonblock["mypilatus_filestartnum"] - '
                     '1\n'
                     'result = "" + unixdir + "/" + ds.mypilatus_fileprefix + '
                     '"%05d"\n'
                     'result += ds.mypilatus_filepostfix + ":"\n'
                     'filelastnumber = ds.mypilatus_filestartnum - 1\n'
                     'if "__root__" in commonblock.keys():\n'
                     '    root = commonblock["__root__"]\n'
                     '    if hasattr(root, "currentfileid") and '
                     'hasattr(root, "stepsperfile"):\n'
                     '        spf = root.stepsperfile\n'
                     '        cfid = root.currentfileid\n'
                     '        if spf > 0 and cfid > 0:\n'
                     '            nbframes = ds.mypilatus_nbframes\n'
                     '            filelastnumber = min(filestartnum + cfid * '
                     'nbframes * spf - 1, filelastnumber)\n'
                     '            filestartnum = filestartnum + (cfid - 1) * '
                     'nbframes * spf\n'
                     'result += str(filestartnum) + ":" +  '
                     'str(filelastnumber)\n'
                     'ds.result = result\n'
                     '</result>\n'
                     ' $datasources.mypilatus_filestartnum\n'
                     ' $datasources.mypilatus_filedir\n'
                     ' $datasources.mypilatus_nbframes\n'
                     ' $datasources.mypilatus_filepostfix\n'
                     ' $datasources.mypilatus_fileprefix</datasource>\n'
                     '</definition>\n'],
                ],
            ],
        ]
        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        with open(fname, "w") as fl:
            fl.write(xml)

        self.checkxmls(args, fname)


if __name__ == '__main__':
    unittest.main()
