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
import shutil

try:
    import tango
except Exception:
    import PyTango as tango

# import nxstools
from nxstools import nxscreate

# try:
#     import nxsextrasp00
# except ImportError:
#     from . import nxsextrasp00


try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    from .checks import checkxmls
except Exception:
    from checks import checkxmls

# try:
#     import TestServerSetUp
# except ImportError:
#     from . import TestServerSetUp


if sys.version_info > (3,):
    unicode = str
    long = int


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


# test fixture
class NXSCreateSECoPCPFSTest(unittest.TestCase):

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

        self.__args = '{"db":"nxsconfig", ' \
                      '"read_default_file":"/etc/my.cnf", "use_unicode":true}'

        # home = expanduser("~")
        db = tango.Database()
        self.host = db.get_db_host().split(".")[0]
        self.port = db.get_db_port()
        self.directory = "."
        self.flags = "-d . "
        # self.flags = " -d -r testp09/testmcs/testr228 "
        self.device = 'testp09/testmcs/testr228'
        self.maxDiff = None

        self.secoplist = [
            # 'client_start_time',
            'myuni',
            'myuni_drv',
            'myuni_drv__interval',
            'myuni_drv__interval_time',
            'myuni_drv__maxcurrent',
            'myuni_drv__maxcurrent_time',
            'myuni_drv__move_limit',
            'myuni_drv__move_limit_time',
            'myuni_drv__safe_current',
            'myuni_drv__safe_current_time',
            'myuni_drv__speed',
            'myuni_drv__speed_time',
            'myuni_drv__tolerance',
            'myuni_drv__tolerance_time',
            'myuni_drv_pollinterval',
            'myuni_drv_pollinterval_time',
            'myuni_drv_status',
            'myuni_drv_status_time',
            'myuni_drv_target',
            'myuni_drv_target_time',
            'myuni_drv_time',
            'myuni_force',
            'myuni_force__adjusting',
            'myuni_force__adjusting_current',
            'myuni_force__adjusting_current_time',
            'myuni_force__adjusting_time',
            'myuni_force__current_step',
            'myuni_force__current_step_time',
            'myuni_force__filter_interval',
            'myuni_force__filter_interval_time',
            'myuni_force__force_offset',
            'myuni_force__force_offset_time',
            'myuni_force__high_pos',
            'myuni_force__high_pos_time',
            'myuni_force__hysteresis',
            'myuni_force__hysteresis_time',
            'myuni_force__limit',
            'myuni_force__limit_time',
            'myuni_force__low_pos',
            'myuni_force__low_pos_time',
            'myuni_force__pid_i',
            'myuni_force__pid_i_time',
            'myuni_force__safe_current',
            'myuni_force__safe_current_time',
            'myuni_force__safe_step',
            'myuni_force__safe_step_time',
            'myuni_force__slope',
            'myuni_force__slope_time',
            'myuni_force__tolerance',
            'myuni_force__tolerance_time',
            'myuni_force_pollinterval',
            'myuni_force_pollinterval_time',
            'myuni_force_status',
            'myuni_force_status_time',
            'myuni_force_target',
            'myuni_force_target_time',
            'myuni_force_time',
            'myuni_res',
            'myuni_res__jitter',
            'myuni_res__jitter_time',
            'myuni_res_pollinterval',
            'myuni_res_pollinterval_time',
            'myuni_res_status',
            'myuni_res_status_time',
            'myuni_res_time',
            'myuni_t',
            'myuni_t__abs',
            'myuni_t__abs_time',
            'myuni_t__calib',
            'myuni_t__calib_time',
            'myuni_t_status',
            'myuni_t_status_time',
            'myuni_t_time',
            'myuni_transducer',
            'myuni_transducer__friction',
            'myuni_transducer__friction_time',
            'myuni_transducer__hysteresis',
            'myuni_transducer__hysteresis_time',
            'myuni_transducer__jitter',
            'myuni_transducer__jitter_time',
            'myuni_transducer__offset',
            'myuni_transducer__offset_time',
            'myuni_transducer__slope',
            'myuni_transducer__slope_time',
            'myuni_transducer_pollinterval',
            'myuni_transducer_pollinterval_time',
            'myuni_transducer_status',
            'myuni_transducer_status_time',
            'myuni_transducer_time'
        ]

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
        with open("%s/%s.ds.xml" % (self.directory, name), 'r') as fl:
            xml = fl.read()
        return xml

    def getcp(self, name):
        with open("%s/%s.xml" % (self.directory, name), 'r') as fl:
            xml = fl.read()
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
                # print(arg[0], arg[1])
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

                    for cmd in arg[0]:
                        vl, er = self.runtest(cmd)
                        # print(vl)
                        # print(er)
                        if er:
                            self.assertTrue(er.startswith("Info: "))
                        else:
                            self.assertEqual('', er)
                        self.assertTrue(vl)

                        for i, ds in enumerate(arg[1][1]):
                            xml = self.getds(ds)
                            checkxmls(
                                self,
                                arg[2][1][i], xml)
                        for i, cp in enumerate(arg[1][0]):
                            xml = self.getcp(cp)
                            checkxmls(
                                self,
                                arg[2][0][i], xml)

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

    def test_secopcp_list_none(self):
        """ test nxsccreate stdcomp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.json' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = """{}"""
        args = [
            [
                ('nxscreate secopcp -l -j %s %s'
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

                # if er:
                #     self.assertTrue(er.startswith("Info: ")
                # else:
                #     self.assertEqual('', er)
                self.assertTrue(not vl)
        finally:
            os.remove(fname)

    def test_secopcp_list_mouldes(self):
        """ test nxsccreate stdcomp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.json' % (
            os.getcwd(), self.__class__.__name__, fun)

        args = [
            [
                ('nxscreate secopcp -l -j %s %s'
                 % (fname, self.flags)).split(),
            ],
        ]

        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        shutil.copy("test/files/secop.conf", fname)
        try:
            for arg in args:
                vl, er = self.runtest(arg[0])

                # if er:
                #     self.assertTrue(er.startswith("Info: "))
                # else:
                #     self.assertEqual('', er)
                lines = vl.split("\n")
                self.assertEqual(len(lines), 3)
                self.assertEqual(lines[-3], "MODULES:")
                self.assertEqual(
                    sorted(lines[-2].split()),
                    sorted(['force', 'drv', 'transducer', 'res', 'T']))
                self.assertEqual(
                    lines[-1].split(),
                    [])
        finally:
            os.remove(fname)

    def ttest_secopcp_create_old(self):
        """ test nxsccreate stdcomp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.json' % (
            os.getcwd(), self.__class__.__name__, fun)

        cname = "myuni"

        args = [
            [
                ('nxscreate secopcp -c %s -j %s %s'
                 % (cname, fname, self.flags)).split(),
            ],
        ]

        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        shutil.copy("test/files/secop.conf", fname)
        try:
            for arg in args:
                vl, er = self.runtest(arg[0])

                # if er:
                #     self.assertTrue(er.startswith("Info: "))
                # else:
                #     self.assertEqual('', er)
                lines = vl.split("\n")
                # print(lines[:10])
                self.assertEqual(len(lines), 135)
                self.assertEqual(lines[0], "OUTPUT DIRECTORY: .")
                self.assertEqual(len(lines), 135)
                ncst = sorted(
                    [ll for ll in lines[1:]
                     if ('client_start_time' not in ll and ll)])
                cst = sorted(
                    [ll for ll in lines[1:]
                     if 'client_start_time' in ll])
                self.assertEqual(len(cst), 44)
                self.assertEqual(len(set(cst)), 1)
                fmtstr = "CREATING '{name}' of secop in './{name}.ds.xml'"
                cfmtstr = "CREATING '{name}' of secop in './{name}.xml'"
                self.assertEqual(
                    list(set(cst))[0],
                    fmtstr.format(name='client_start_time'))
                self.assertEqual(len(ncst), 89)
                self.assertEqual(len(ncst), len(self.secoplist))
                for si, scn in enumerate(self.secoplist):
                    # print(scn, ncst[si])
                    if "_" in scn:
                        self.assertEqual(ncst[si], fmtstr.format(name=scn))
                    else:
                        self.assertEqual(ncst[si], cfmtstr.format(name=scn))

        finally:
            os.remove(fname)
            for scn in self.secoplist:
                pass
                # if "_" in scn:
                #     os.remove("%s.ds.xml" % scn)
                # else:
                #     os.remove("%s.xml" % scn)

    def test_secopcp_create(self):
        """ test nxsccreate stdcomp file system
        """

        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.json' % (
            os.getcwd(), self.__class__.__name__, fun)

        cname = "myuni"

        args = [
            [
                ('nxscreate secopcp -c %s -j %s %s'
                 % (cname, fname, self.flags)).split(),
            ],
        ]

        # if os.path.isfile(fname):
        #     raise Exception("Test file %s exists" % fname)
        shutil.copy("test/files/secop.conf", fname)

        dsl = ["client_start_time"]
        dsl.extend(self.secoplist[1:])
        args = [
            [
                [
                    ('nxscreate secopcp -c %s -j %s %s'
                     % (cname, fname, self.flags)).split(),
                ],
                [
                    [self.secoplist[0]],
                    dsl,
                ],
                [
                    [

                        '<?xml version=\'1.0\' encoding=\'utf8\'?>\n'
                        '<definition>\n'
                        '  <group name="$var.entryname#\'scan\'$var.serialno"'
                        ' type="NXentry">\n'
                        '    <group name="sample" type="NXsample">\n'
                        '      <group name="myuni" type="NXenvironment">\n'
                        '        <field name="name" type="NX_CHAR">[sim] '
                        'uniaxial pressure device<strategy mode="INIT"/>'
                        '</field>\n'
                        '        <field name="short_name" type="NX_CHAR">'
                        'uniax_sim.psi.ch<strategy mode="INIT"/></field>\n'
                        '        <field name="type" type="NX_CHAR">FRAPPY -'
                        ' The Python Framework for SECoP'
                        '<strategy mode="INIT"/></field>\n'
                        '        <field name="description" type="NX_CHAR">'
                        '2021.02<strategy mode="INIT"/></field>\n'
                        '        <group name="force" type="NXsensor">\n'
                        '          <field name="name" type="NX_CHAR">'
                        'uniax driver<strategy mode="INIT"/></field>\n'
                        '          <field name="model" type="NX_CHAR">'
                        'secop_psi.uniax.Uniax<strategy mode="INIT"/>'
                        '</field>\n'
                        '          <group name="parameters" '
                        'type="NXcollection">\n'
                        '            <group name="status" type="NXlog">\n'
                        '              <field name="value" type="NX_INT64">'
                        '$datasources.myuni_force_status'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force_status_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="pollinterval" type="NXlog">'
                        '\n'
                        '              <field name="value" type="NX_FLOAT64">'
                        '$datasources.myuni_force_pollinterval'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force_pollinterval_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time'
                        '<strategy mode="INIT"/></attribute>'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="minimal_value" '
                        'type="NX_FLOAT64">0.1<strategy mode="INIT"/>'
                        '</field>\n'
                        '              <field name="maximal_value" '
                        'type="NX_FLOAT64">120<strategy mode="INIT"/>'
                        '</field>\n'
                        '            </group>\n'
                        '            <group name="target" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="N">$datasources.myuni_force_target'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force_target_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_limit" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64"'
                        ' units="N">$datasources.myuni_force__limit'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force__limit_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '              <field name="maximal_value" '
                        'type="NX_FLOAT64" units="N">150'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_tolerance" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="N">$datasources.myuni_force__tolerance'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force__tolerance_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '              <field name="maximal_value" '
                        'type="NX_FLOAT64" units="N">10<strategy mode="INIT"/>'
                        '</field>\n'
                        '            </group>\n'
                        '            <group name="_slope" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="deg/N">$datasources.myuni_force__slope'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force__slope_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_pid_i" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64">'
                        '$datasources.myuni_force__pid_i'
                        '<strategy mode="INIT"/>'
                        '</field>\n'
                        '              <field name="time" type="NX_FLOAT64"'
                        ' units="s">$datasources.myuni_force__pid_i_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_filter_interval" '
                        'type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force__filter_interval'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force__filter_interval_'
                        'time<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '              <field name="maximal_value" '
                        'type="NX_FLOAT64" units="s">60<strategy mode="INIT"/>'
                        '</field>\n'
                        '            </group>\n'
                        '            <group name="_current_step" type="NXlog">'
                        '\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="deg">$datasources.myuni_force__current_step'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force__current_step_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_force_offset" type="NXlog">'
                        '\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="N">$datasources.myuni_force__force_offset'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force__force_offset_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_hysteresis" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="N">$datasources.myuni_force__hysteresis'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force__hysteresis_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '              <field name="maximal_value" '
                        'type="NX_FLOAT64" units="N">150'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_adjusting" type="NXlog">\n'
                        '              <field name="value" type="NX_BOOLEAN">'
                        '$datasources.myuni_force__adjusting'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force__adjusting_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_adjusting_current" '
                        'type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="A">$datasources.myuni_force__adjusting_current'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force__adjusting_current'
                        '_time<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '              <field name="maximal_value" '
                        'type="NX_FLOAT64" units="A">2.8'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_safe_step" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="deg">$datasources.myuni_force__safe_step'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force__safe_step_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time'
                        '<strategy mode="INIT"/></attribute>'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_safe_current" '
                        'type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="A">$datasources.myuni_force__safe_current'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force__safe_current_'
                        'time<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '              <field name="maximal_value" '
                        'type="NX_FLOAT64" units="A">2.8'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_low_pos" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="deg">$datasources.myuni_force__low_pos'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force__low_pos_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_high_pos" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="deg">$datasources.myuni_force__high_pos'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force__high_pos_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '          </group>\n'
                        '          <group name="value_log" type="NXlog">\n'
                        '            <field name="value" type="NX_FLOAT64" '
                        'units="N">$datasources.myuni_force'
                        '<strategy mode="INIT"/></field>\n'
                        '            <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_force_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '          </group>\n'
                        '          <link name="value" '
                        'target="/$var.entryname#\'scan\'$var.serialno/sample/'
                        'myuni/force/parameters/target/value"/>\n'
                        '        </group>\n'
                        '        <group name="drv" type="NXsensor">\n'
                        '          <field name="name" type="NX_CHAR">'
                        'simulated motor<strategy mode="INIT"/></field>\n'
                        '          <field name="model" type="NX_CHAR">'
                        'secop.simulation.SimBase_drv<strategy mode="INIT"/>'
                        '</field>\n'
                        '          <group name="parameters" '
                        'type="NXcollection">\n'
                        '            <group name="status" type="NXlog">\n'
                        '              <field name="value" type="NX_INT64">'
                        '$datasources.myuni_drv_status<strategy mode="INIT"/>'
                        '</field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_drv_status_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="pollinterval" type="NXlog">'
                        '\n'
                        '              <field name="value" type="NX_FLOAT64">'
                        '$datasources.myuni_drv_pollinterval'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_drv_pollinterval_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '              <field name="minimal_value" '
                        'type="NX_FLOAT64">0.1<strategy mode="INIT"/>'
                        '</field>\n'
                        '              <field name="maximal_value" '
                        'type="NX_FLOAT64">120<strategy mode="INIT"/>'
                        '</field>\n'
                        '            </group>\n'
                        '            <group name="target" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64"'
                        ' units="deg">$datasources.myuni_drv_target'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_drv_target_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute>'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_interval" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64">'
                        '$datasources.myuni_drv__interval'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_drv__interval_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '              <field name="maximal_value" '
                        'type="NX_FLOAT64">1<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_speed" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64">'
                        '$datasources.myuni_drv__speed<strategy mode="INIT"/>'
                        '</field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_drv__speed_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_safe_current" '
                        'type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64">'
                        '$datasources.myuni_drv__safe_current'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_drv__safe_current_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_move_limit" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64">'
                        '$datasources.myuni_drv__move_limit'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64"'
                        ' units="s">$datasources.myuni_drv__move_limit_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_maxcurrent" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64">'
                        '$datasources.myuni_drv__maxcurrent'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64"'
                        ' units="s">$datasources.myuni_drv__maxcurrent_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time'
                        '<strategy mode="INIT"/></attribute>'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_tolerance" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64">'
                        '$datasources.myuni_drv__tolerance'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64"'
                        ' units="s">$datasources.myuni_drv__tolerance_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time'
                        '<strategy mode="INIT"/></attribute>'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '          </group>\n'
                        '          <group name="value_log" type="NXlog">\n'
                        '            <field name="value" type="NX_FLOAT64" '
                        'units="deg" transformation_type="rotation">'
                        '$datasources.myuni_drv'
                        '<attribute name="vector" type="NX_FLOAT64">0 -1 0'
                        '<dimensions rank="1"><dim index="1" value="3"/>'
                        '</dimensions><strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_drv_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time'
                        '<strategy mode="INIT"/></attribute>'
                        '<strategy mode="INIT"/></field>\n'
                        '          </group>\n'
                        '          <link name="value" '
                        'target="/$var.entryname#\'scan\'$var.serialno/sample/'
                        'myuni/drv/parameters/target/value"/>\n'
                        '        </group>\n'
                        '        <group name="transducer" type="NXsensor">\n'
                        '          <field name="name" type="NX_CHAR">'
                        'simulated force<strategy mode="INIT"/></field>\n'
                        '          <field name="model" type="NX_CHAR">'
                        'secop_psi.simdpm.DPM3<strategy mode="INIT"/>'
                        '</field>\n'
                        '          <group name="parameters"'
                        ' type="NXcollection">\n'
                        '            <group name="status" type="NXlog">\n'
                        '              <field name="value" type="NX_INT64">'
                        '$datasources.myuni_transducer_status'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_transducer_status_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time'
                        '<strategy mode="INIT"/></attribute>'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="pollinterval" type="NXlog">'
                        '\n'
                        '              <field name="value" type="NX_FLOAT64">'
                        '$datasources.myuni_transducer_pollinterval'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64"'
                        ' units="s">$datasources.myuni_transducer_pollinterval'
                        '_time<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time'
                        '<strategy mode="INIT"/></attribute>'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="minimal_value" '
                        'type="NX_FLOAT64">0.1<strategy mode="INIT"/>'
                        '</field>\n'
                        '              <field name="maximal_value" '
                        'type="NX_FLOAT64">120<strategy mode="INIT"/>'
                        '</field>\n'
                        '            </group>\n'
                        '            <group name="_jitter" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="N">$datasources.myuni_transducer__jitter'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_transducer__jitter_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time'
                        '<strategy mode="INIT"/></attribute>'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_hysteresis" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="deg">$datasources.myuni_transducer__hysteresis'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">'
                        '$datasources.myuni_transducer__hysteresis_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time'
                        '<strategy mode="INIT"/></attribute>'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_friction" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64"'
                        ' units="N/deg">'
                        '$datasources.myuni_transducer__friction'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">'
                        '$datasources.myuni_transducer__friction_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_slope" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="N/deg">$datasources.myuni_transducer__slope'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_transducer__slope_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time'
                        '<strategy mode="INIT"/></attribute>'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_offset" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64" '
                        'units="N">'
                        '$datasources.myuni_transducer__offset'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_transducer__offset_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '          </group>\n'
                        '          <group name="value_log" type="NXlog">\n'
                        '            <field name="value" type="NX_FLOAT64" '
                        'units="N">$datasources.myuni_transducer'
                        '<strategy mode="INIT"/></field>\n'
                        '            <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_transducer_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '          </group>\n'
                        '        </group>\n'
                        '        <group name="res" type="NXsensor">\n'
                        '          <field name="name" type="NX_CHAR">'
                        'raw temperature sensor on the stick'
                        '<strategy mode="INIT"/></field>\n'
                        '          <field name="model" type="NX_CHAR">'
                        'secop.simulation.SimBase_res<strategy mode="INIT"/>'
                        '</field>\n'
                        '          <group name="parameters" '
                        'type="NXcollection">\n'
                        '            <group name="status" type="NXlog">\n'
                        '              <field name="value" type="NX_INT64">'
                        '$datasources.myuni_res_status<strategy mode="INIT"/>'
                        '</field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">'
                        '$datasources.myuni_res_status_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="pollinterval" type="NXlog">'
                        '\n'
                        '              <field name="value" type="NX_FLOAT64">'
                        '$datasources.myuni_res_pollinterval'
                        '<strategy mode="INIT"/></field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_res_pollinterval_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '              <field name="minimal_value" '
                        'type="NX_FLOAT64">0.1<strategy mode="INIT"/>'
                        '</field>\n'
                        '              <field name="maximal_value" '
                        'type="NX_FLOAT64">120<strategy mode="INIT"/>'
                        '</field>\n'
                        '            </group>\n'
                        '            <group name="_jitter" type="NXlog">\n'
                        '              <field name="value" type="NX_FLOAT64">'
                        '$datasources.myuni_res__jitter<strategy mode="INIT"/>'
                        '</field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_res__jitter_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time'
                        '<strategy mode="INIT"/></attribute>'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '          </group>\n'
                        '          <group name="value_log" type="NXlog">\n'
                        '            <field name="value" type="NX_FLOAT64" '
                        'units="Ohm">$datasources.myuni_res'
                        '<strategy mode="INIT"/></field>\n'
                        '            <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_res_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '          </group>\n'
                        '        </group>\n'
                        '        <group name="T" type="NXsensor">\n'
                        '          <field name="name" type="NX_CHAR">'
                        'temperature sensor_ soft calibration'
                        '<strategy mode="INIT"/></field>\n'
                        '          <field name="measurement" type="NX_CHAR">'
                        'temperature<strategy mode="INIT"/></field>\n'
                        '          <field name="model" type="NX_CHAR">'
                        'secop_psi.softcal.Sensor<strategy mode="INIT"/>'
                        '</field>\n'
                        '          <group name="parameters" '
                        'type="NXcollection">\n'
                        '            <group name="status" type="NXlog">\n'
                        '              <field name="value" type="NX_INT64">'
                        '$datasources.myuni_t_status<strategy mode="INIT"/>'
                        '</field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_t_status_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time'
                        '<strategy mode="INIT"/></attribute>'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_calib" type="NXlog">\n'
                        '              <field name="value" type="NX_CHAR">'
                        '$datasources.myuni_t__calib<strategy mode="INIT"/>'
                        '</field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_t__calib_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '            <group name="_abs" type="NXlog">\n'
                        '              <field name="value" type="NX_BOOLEAN">'
                        '$datasources.myuni_t__abs<strategy mode="INIT"/>'
                        '</field>\n'
                        '              <field name="time" type="NX_FLOAT64" '
                        'units="s">'
                        '$datasources.myuni_t__abs_time<attribute name="start"'
                        ' type="NX_DATE_TIME">$datasources.client_start_time'
                        '<strategy mode="INIT"/></attribute>'
                        '<strategy mode="INIT"/></field>\n'
                        '            </group>\n'
                        '          </group>\n'
                        '          <group name="value_log" type="NXlog">\n'
                        '            <field name="value" type="NX_FLOAT64" '
                        'units="K">$datasources.myuni_t<strategy mode="INIT"/>'
                        '</field>\n'
                        '            <field name="time" type="NX_FLOAT64" '
                        'units="s">$datasources.myuni_t_time'
                        '<attribute name="start" type="NX_DATE_TIME">'
                        '$datasources.client_start_time<strategy mode="INIT"/>'
                        '</attribute><strategy mode="INIT"/></field>\n'
                        '          </group>\n'
                        '        </group>\n'
                        '      </group>\n'
                        '      <group name="transformations" '
                        'type="NXtransformations">'
                        '        <link name="myuni_drv" '
                        'target="/$var.entryname#\'scan\'$var.serialno/sample'
                        '/myuni/drv/value_log/value"/>'
                        '      </group>'
                        '      <link name="temperature_env" '
                        'target="/$var.entryname#\'scan\'$var.serialno/sample/'
                        'myuni"/>\n'
                        '      <link name="temperature" '
                        'target="/$var.entryname#\'scan\'$var.serialno/sample/'
                        'myuni/T/value_log"/>\n'
                        '    </group>\n'
                        '  </group>\n'
                        '</definition>\n'
                     ],
                    [
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="CLIENT" name="client_start_time">'
                        '\n'
                        '    <record name="start_time"/>\n'
                        '    <doc>The start time is provided by the control '
                        'client.</doc>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" name="myuni_drv">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd("read drv:value", '
                        '"", "5000", "0.001", "myuni_drv", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv__interval">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read drv:_interval", "", "5000", "0.001", '
                        '"myuni_drv__interval", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv__interval_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd("read drv:_interval", '
                        '"", "5000", "0.001", "myuni_drv__interval", '
                        '[1, "t"], '
                        'commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv__maxcurrent">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read drv:_maxcurrent", "", "5000", "0.001", '
                        '"myuni_drv__maxcurrent", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv__maxcurrent_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read drv:_maxcurrent", "", "5000", "0.001", '
                        '"myuni_drv__maxcurrent", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv__move_limit">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read drv:_move_limit", "", "5000", "0.001", '
                        '"myuni_drv__move_limit", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv__move_limit_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read drv:_move_limit", "", "5000", "0.001", '
                        '"myuni_drv__move_limit", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv__safe_current">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read drv:_safe_current", "", "5000", "0.001", '
                        '"myuni_drv__safe_current", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv__safe_current_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read drv:_safe_current", "", "5000", "0.001", '
                        '"myuni_drv__safe_current", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" name="myuni_drv__speed">'
                        '\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read drv:_speed", "", "5000", "0.001", '
                        '"myuni_drv__speed", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv__speed_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read drv:_speed", "", "5000", "0.001", '
                        '"myuni_drv__speed", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv__tolerance">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read drv:_tolerance", "", "5000", "0.001", '
                        '"myuni_drv__tolerance", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv__tolerance_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read drv:_tolerance", "", "5000", "0.001", '
                        '"myuni_drv__tolerance", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv_pollinterval">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read drv:pollinterval", "", "5000", "0.001", '
                        '"myuni_drv_pollinterval", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv_pollinterval_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read drv:pollinterval", "", "5000", "0.001", '
                        '"myuni_drv_pollinterval", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" name="myuni_drv_status">'
                        '\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd("read drv:status",'
                        ' "", "5000", "0.001", "myuni_drv_status", [0,0], '
                        'commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv_status_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read drv:status", "", "5000", "0.001", '
                        '"myuni_drv_status", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" name="myuni_drv_target">'
                        '\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read drv:target", "", "5000", "0.001", '
                        '"myuni_drv_target", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_drv_target_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read drv:target", "", "5000", "0.001", '
                        '"myuni_drv_target", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" name="myuni_drv_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read drv:value", "", "5000", "0.001", '
                        '"myuni_drv", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" name="myuni_force">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:value", "", "5000", "0.001", '
                        '"myuni_force", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__adjusting">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:_adjusting", "", "5000", "0.001", '
                        '"myuni_force__adjusting", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__adjusting_current">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:_adjusting_current", "", "5000", '
                        '"0.001", "myuni_force__adjusting_current", [0], '
                        'commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__adjusting_current_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:_adjusting_current", "", "5000", '
                        '"0.001", "myuni_force__adjusting_current", '
                        '[1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__adjusting_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:_adjusting", "", "5000", "0.001", '
                        '"myuni_force__adjusting", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__current_step">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:_current_step", "", "5000", "0.001", '
                        '"myuni_force__current_step", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__current_step_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:_current_step", "", "5000", "0.001", '
                        '"myuni_force__current_step", [1, "t"], '
                        'commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__filter_interval">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:_filter_interval", "", "5000", "0.001",'
                        ' "myuni_force__filter_interval", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__filter_interval_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:_filter_interval", "", "5000", "0.001",'
                        ' "myuni_force__filter_interval", [1, "t"],'
                        ' commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__force_offset">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:_force_offset", "", "5000", "0.001", '
                        '"myuni_force__force_offset", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__force_offset_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:_force_offset", "", "5000", "0.001", '
                        '"myuni_force__force_offset", [1, "t"], '
                        'commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__high_pos">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:_high_pos", "", "5000", "0.001", '
                        '"myuni_force__high_pos", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__high_pos_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:_high_pos", "", "5000", "0.001", '
                        '"myuni_force__high_pos", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__hysteresis">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:_hysteresis", "", "5000", "0.001", '
                        '"myuni_force__hysteresis", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__hysteresis_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:_hysteresis", "", "5000", "0.001", '
                        '"myuni_force__hysteresis", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__limit">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:_limit", "", "5000", "0.001", '
                        '"myuni_force__limit", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__limit_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:_limit", "", "5000", "0.001", '
                        '"myuni_force__limit", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__low_pos">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:_low_pos", "", "5000", "0.001", '
                        '"myuni_force__low_pos", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__low_pos_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:_low_pos", "", "5000", "0.001", '
                        '"myuni_force__low_pos", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__pid_i">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:_pid_i", "", "5000", "0.001", '
                        '"myuni_force__pid_i", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__pid_i_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:_pid_i", "", "5000", "0.001", '
                        '"myuni_force__pid_i", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__safe_current">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:_safe_current", "", "5000", "0.001", '
                        '"myuni_force__safe_current", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__safe_current_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:_safe_current", "", "5000", "0.001", '
                        '"myuni_force__safe_current", [1, "t"], '
                        'commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__safe_step">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:_safe_step", "", "5000", "0.001", '
                        '"myuni_force__safe_step", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__safe_step_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:_safe_step", "", "5000", "0.001", '
                        '"myuni_force__safe_step", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__slope">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:_slope", "", "5000", "0.001", '
                        '"myuni_force__slope", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__slope_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:_slope", "", "5000", "0.001", '
                        '"myuni_force__slope", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__tolerance">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:_tolerance", "", "5000", "0.001", '
                        '"myuni_force__tolerance", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force__tolerance_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:_tolerance", "", "5000", "0.001", '
                        '"myuni_force__tolerance", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force_pollinterval">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:pollinterval", "", "5000", "0.001", '
                        '"myuni_force_pollinterval", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force_pollinterval_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:pollinterval", "", "5000", "0.001", '
                        '"myuni_force_pollinterval", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force_status">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:status", "", "5000", "0.001", '
                        '"myuni_force_status", [0,0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force_status_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read force:status", "", "5000", "0.001", '
                        '"myuni_force_status", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force_target">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read force:target", "", "5000", "0.001", '
                        '"myuni_force_target", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force_target_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd("read force:target", '
                        '"", "5000", "0.001", "myuni_force_target", '
                        '[1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_force_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd("read force:value", '
                        '"", "5000", "0.001", "myuni_force", [1, "t"], '
                        'commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" name="myuni_res">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read res:value", "", "5000", "0.001", '
                        '"myuni_res", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_res__jitter">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read res:_jitter", "", "5000", "0.001", '
                        '"myuni_res__jitter", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_res__jitter_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd("read res:_jitter", '
                        '"", "5000", "0.001", "myuni_res__jitter", '
                        '[1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_res_pollinterval">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read res:pollinterval", "", "5000", "0.001", '
                        '"myuni_res_pollinterval", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_res_pollinterval_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read res:pollinterval", "", "5000", "0.001", '
                        '"myuni_res_pollinterval", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_res_status">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read res:status", "", "5000", "0.001", '
                        '"myuni_res_status", [0,0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_res_status_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd("read res:status", '
                        '"", "5000", "0.001", "myuni_res_status", [1, "t"], '
                        'commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" name="myuni_res_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read res:value", "", "5000", "0.001", '
                        '"myuni_res", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" name="myuni_t">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read T:value", "", "5000", "0.001", "myuni_t", '
                        '[0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" name="myuni_t__abs">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd("read T:_abs", '
                        '"", "5000", "0.001", "myuni_t__abs", [0], '
                        'commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_t__abs_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd("read T:_abs", "", '
                        '"5000", "0.001", "myuni_t__abs", [1, "t"], '
                        'commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" name="myuni_t__calib">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read T:_calib", "", "5000", "0.001", '
                        '"myuni_t__calib", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_t__calib_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read T:_calib", "", "5000", "0.001", '
                        '"myuni_t__calib", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" name="myuni_t_status">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read T:status", "", "5000", "0.001", '
                        '"myuni_t_status", [0,0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_t_status_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read T:status", "", "5000", "0.001", '
                        '"myuni_t_status", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" name="myuni_t_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read T:value", "", "5000", "0.001", "myuni_t", '
                        '[1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read transducer:value", "", "5000", "0.001", '
                        '"myuni_transducer", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer__friction">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read transducer:_friction", "", "5000", "0.001", '
                        '"myuni_transducer__friction", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer__friction_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read transducer:_friction", "", "5000", "0.001", '
                        '"myuni_transducer__friction", [1, "t"], '
                        'commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer__hysteresis">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read transducer:_hysteresis", "", "5000", '
                        '"0.001", "myuni_transducer__hysteresis", [0], '
                        'commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer__hysteresis_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read transducer:_hysteresis", "", "5000", '
                        '"0.001", "myuni_transducer__hysteresis", '
                        '[1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer__jitter">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read transducer:_jitter", "", "5000", "0.001", '
                        '"myuni_transducer__jitter", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer__jitter_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read transducer:_jitter", "", "5000", "0.001", '
                        '"myuni_transducer__jitter", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer__offset">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read transducer:_offset", "", "5000", "0.001", '
                        '"myuni_transducer__offset", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer__offset_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read transducer:_offset", "", "5000", "0.001", '
                        '"myuni_transducer__offset", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer__slope">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read transducer:_slope", "", "5000", "0.001", '
                        '"myuni_transducer__slope", [0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer__slope_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read transducer:_slope", "", "5000", "0.001", '
                        '"myuni_transducer__slope", [1, "t"], '
                        'commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer_pollinterval">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read transducer:pollinterval", "", "5000", '
                        '"0.001", "myuni_transducer_pollinterval", [0], '
                        'commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer_pollinterval_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read transducer:pollinterval", "", "5000", '
                        '"0.001", "myuni_transducer_pollinterval", '
                        '[1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer_status">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'ds.result = secop.secop_group_cmd('
                        '"read transducer:status", "", "5000", "0.001", '
                        '"myuni_transducer_status", [0,0], commonblock)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer_status_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read transducer:status", "", "5000", "0.001", '
                        '"myuni_transducer_status", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock, ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n',
                        '<?xml version=\'1.0\'?>\n'
                        '<definition>\n'
                        '  <datasource type="PYEVAL" '
                        'name="myuni_transducer_time">\n'
                        '    <result name="result">\n'
                        'from nxstools.pyeval import secop\n'
                        'from nxstools.pyeval import timestamp\n'
                        'ctime = secop.secop_group_cmd('
                        '"read transducer:value", "", "5000", "0.001", '
                        '"myuni_transducer", [1, "t"], commonblock)\n'
                        'ds.result = timestamp.relative_timestamp('
                        'commonblock,'
                        ' ctime)\n'
                        '    </result>\n'
                        '  </datasource>\n'
                        '</definition>\n'
                     ],
                ],
            ],
        ]
        self.checkxmls(args, fname)


if __name__ == '__main__':
    unittest.main()
