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

        self.myuni = (
            '<?xml version=\'1.0\' encoding=\'utf8\'?>\n'
            '<definition>\n'
            '  <group name="$var.entryname#\'scan\'$var.serialno"'
            ' type="NXentry">\n'
            '    <group name="sample" type="NXsample">\n'
            '      <group name="{cpname}" type="{nodegroup}">\n'
            '        <field name="name" type="NX_CHAR">'
            'uniax_sim.psi.ch<strategy mode="INIT"/>'
            '</field>\n'
            '        <field name="short_name" type="NX_CHAR">'
            '{cpname}<strategy mode="INIT"/></field>\n'
            '        <field name="type" type="NX_CHAR">FRAPPY -'
            ' The Python Framework for SECoP (2021.02)'
            '<strategy mode="INIT"/></field>\n'
            '        <field name="description" type="NX_CHAR">'
            '[sim] '
            'uniaxial pressure device<strategy mode="INIT"/></field>\n'
            '        <group name="force" type="NXsensor">\n'
            '          <field name="name" type="NX_CHAR">'
            'force<strategy mode="INIT"/></field>\n'
            '          <field name="description" type="NX_CHAR">'
            'uniax driver<strategy mode="INIT"/></field>\n'
            '          <field name="model" type="NX_CHAR">'
            'secop_psi.uniax.Uniax<strategy mode="INIT"/>'
            '</field>\n'
            '          <group name="parameters" '
            'type="NXcollection">\n'
            '            <group name="status" type="NXlog">\n'
            '              <field name="value" type="NX_INT64">'
            '$datasources.{cpname}_force_status'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force_status_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="pollinterval" type="NXlog">'
            '\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_force_pollinterval'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force_pollinterval_time'
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
            'units="N">$datasources.{cpname}_force_target'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force_target_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_limit" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64"'
            ' units="N">$datasources.{cpname}_force__limit'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force__limit_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '              <field name="maximal_value" '
            'type="NX_FLOAT64" units="N">150'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_tolerance" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="N">$datasources.{cpname}_force__tolerance'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force__tolerance_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '              <field name="maximal_value" '
            'type="NX_FLOAT64" units="N">10<strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '            <group name="_slope" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="deg/N">$datasources.{cpname}_force__slope'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force__slope_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_pid_i" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_force__pid_i'
            '<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64"'
            ' units="s">$datasources.{cpname}_force__pid_i_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_filter_interval" '
            'type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force__filter_interval'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force__filter_interval_'
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
            'units="deg">$datasources.{cpname}_force__current_step'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force__current_step_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_force_offset" type="NXlog">'
            '\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="N">$datasources.{cpname}_force__force_offset'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force__force_offset_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_hysteresis" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="N">$datasources.{cpname}_force__hysteresis'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force__hysteresis_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '              <field name="maximal_value" '
            'type="NX_FLOAT64" units="N">150'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_adjusting" type="NXlog">\n'
            '              <field name="value" type="NX_BOOLEAN">'
            '$datasources.{cpname}_force__adjusting'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force__adjusting_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_adjusting_current" '
            'type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="A">$datasources.{cpname}_force__adjusting_current'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force__adjusting_current'
            '_time<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '              <field name="maximal_value" '
            'type="NX_FLOAT64" units="A">2.8'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_safe_step" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="deg">$datasources.{cpname}_force__safe_step'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force__safe_step_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute>'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_safe_current" '
            'type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="A">$datasources.{cpname}_force__safe_current'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force__safe_current_'
            'time<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '              <field name="maximal_value" '
            'type="NX_FLOAT64" units="A">2.8'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_low_pos" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="deg">$datasources.{cpname}_force__low_pos'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force__low_pos_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_high_pos" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="deg">$datasources.{cpname}_force__high_pos'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force__high_pos_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '          </group>\n'
            '          <group name="value_log" type="NXlog">\n'
            '            <field name="value" type="NX_FLOAT64" '
            'units="N">$datasources.{cpname}_force'
            '<strategy mode="INIT"/></field>\n'
            '            <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_force_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '          </group>\n'
            '          <link name="value" '
            'target="/$var.entryname#\'scan\'$var.serialno/sample/'
            '{cpname}/force/parameters/target/value"/>\n'
            '        </group>\n'
            '        <group name="drv" type="NXsensor">\n'
            '          <field name="name" type="NX_CHAR">'
            'drv<strategy mode="INIT"/></field>\n'
            '          <field name="description" type="NX_CHAR">'
            'simulated motor<strategy mode="INIT"/></field>\n'
            '          <field name="model" type="NX_CHAR">'
            'secop.simulation.SimBase_drv<strategy mode="INIT"/>'
            '</field>\n'
            '          <group name="parameters" '
            'type="NXcollection">\n'
            '            <group name="status" type="NXlog">\n'
            '              <field name="value" type="NX_INT64">'
            '$datasources.{cpname}_drv_status<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_drv_status_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="pollinterval" type="NXlog">'
            '\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_drv_pollinterval'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_drv_pollinterval_time'
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
            ' units="deg">$datasources.{cpname}_drv_target'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_drv_target_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute>'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_interval" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_drv__interval'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_drv__interval_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '              <field name="maximal_value" '
            'type="NX_FLOAT64">1<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_speed" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_drv__speed<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_drv__speed_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_safe_current" '
            'type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_drv__safe_current'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_drv__safe_current_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_move_limit" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_drv__move_limit'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64"'
            ' units="s">$datasources.{cpname}_drv__move_limit_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_maxcurrent" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_drv__maxcurrent'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64"'
            ' units="s">$datasources.{cpname}_drv__maxcurrent_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute>'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_tolerance" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_drv__tolerance'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64"'
            ' units="s">$datasources.{cpname}_drv__tolerance_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute>'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '          </group>\n'
            '          <group name="value_log" type="NXlog">\n'
            '            <field name="value" type="NX_FLOAT64" '
            'units="deg" transformation_type="rotation">'
            '$datasources.{cpname}_drv'
            '<attribute name="vector" type="NX_FLOAT64">0 1 0'
            '<dimensions rank="1"><dim index="1" value="3"/>'
            '</dimensions><strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_drv_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute>'
            '<strategy mode="INIT"/></field>\n'
            '          </group>\n'
            '          <link name="value" '
            'target="/$var.entryname#\'scan\'$var.serialno/sample/'
            '{cpname}/drv/parameters/target/value"/>\n'
            '        </group>\n'
            '        <group name="transducer" type="NXsensor">\n'
            '          <field name="name" type="NX_CHAR">'
            'transducer<strategy mode="INIT"/></field>\n'
            '          <field name="description" type="NX_CHAR">'
            'simulated force<strategy mode="INIT"/></field>\n'
            '          <field name="model" type="NX_CHAR">'
            'secop_psi.simdpm.DPM3<strategy mode="INIT"/>'
            '</field>\n'
            '          <group name="parameters"'
            ' type="NXcollection">\n'
            '            <group name="status" type="NXlog">\n'
            '              <field name="value" type="NX_INT64">'
            '$datasources.{cpname}_transducer_status'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_transducer_status_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute>'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="pollinterval" type="NXlog">'
            '\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_transducer_pollinterval'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64"'
            ' units="s">$datasources.{cpname}_transducer_pollinterval'
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
            'units="N">$datasources.{cpname}_transducer__jitter'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_transducer__jitter_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute>'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_hysteresis" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="deg">$datasources.{cpname}_transducer__hysteresis'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">'
            '$datasources.{cpname}_transducer__hysteresis_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute>'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_friction" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64"'
            ' units="N/deg">'
            '$datasources.{cpname}_transducer__friction'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">'
            '$datasources.{cpname}_transducer__friction_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_slope" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="N/deg">$datasources.{cpname}_transducer__slope'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_transducer__slope_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute>'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_offset" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="N">'
            '$datasources.{cpname}_transducer__offset'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_transducer__offset_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '          </group>\n'
            '          <group name="value_log" type="NXlog">\n'
            '            <field name="value" type="NX_FLOAT64" '
            'units="N">$datasources.{cpname}_transducer'
            '<strategy mode="INIT"/></field>\n'
            '            <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_transducer_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '          </group>\n'
            '        </group>\n'
            '        <group name="res" type="NXsensor">\n'
            '          <field name="name" type="NX_CHAR">res'
            '<strategy mode="INIT"/></field>\n'
            '          <field name="description" type="NX_CHAR">'
            'raw temperature sensor on the stick'
            '<strategy mode="INIT"/></field>\n'
            '          <field name="model" type="NX_CHAR">'
            'secop.simulation.SimBase_res<strategy mode="INIT"/>'
            '</field>\n'
            '          <group name="parameters" '
            'type="NXcollection">\n'
            '            <group name="status" type="NXlog">\n'
            '              <field name="value" type="NX_INT64">'
            '$datasources.{cpname}_res_status<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">'
            '$datasources.{cpname}_res_status_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="pollinterval" type="NXlog">'
            '\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_res_pollinterval'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_res_pollinterval_time'
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
            '$datasources.{cpname}_res__jitter<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_res__jitter_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute>'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '          </group>\n'
            '          <group name="value_log" type="NXlog">\n'
            '            <field name="value" type="NX_FLOAT64" '
            'units="Ohm">$datasources.{cpname}_res'
            '<strategy mode="INIT"/></field>\n'
            '            <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_res_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '          </group>\n'
            '        </group>\n'
            '        <group name="T" type="NXsensor">\n'
            '          <field name="name" type="NX_CHAR">T'
            '<strategy mode="INIT"/></field>\n'
            '          <field name="description" type="NX_CHAR">'
            'temperature sensor, soft calibration'
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
            '$datasources.{cpname}_t_status<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_t_status_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute>'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_calib" type="NXlog">\n'
            '              <field name="value" type="NX_CHAR">'
            '$datasources.{cpname}_t__calib<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_t__calib_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_abs" type="NXlog">\n'
            '              <field name="value" type="NX_BOOLEAN">'
            '$datasources.{cpname}_t__abs<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" '
            'units="s">'
            '$datasources.{cpname}_t__abs_time<attribute name="start"'
            ' type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute>'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '          </group>\n'
            '          <group name="value_log" type="NXlog">\n'
            '            <field name="value" type="NX_FLOAT64" '
            'units="K">$datasources.{cpname}_t<strategy mode="INIT"/>'
            '</field>\n'
            '            <field name="time" type="NX_FLOAT64" '
            'units="s">$datasources.{cpname}_t_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '          </group>\n'
            '        </group>\n'
            '      </group>\n'
            '      <group name="transformations" '
            'type="NXtransformations">\n'
            '        <link name="{cpname}_drv" '
            'target="/$var.entryname#\'scan\'$var.serialno/sample/'
            '{cpname}/drv/value_log/value"/>\n'
            '      </group>\n'
            '      <group name="temperature_env" '
            'type="NXenvironment">\n'
            '        <link name="T" '
            'target="/$var.entryname#\'scan\'$var.serialno/'
            'sample/{cpname}/T"/>\n'
            '        <link name="description" '
            'target="/$var.entryname#\'scan\'$var.serialno/'
            'sample/{cpname}/description"/>\n'
            '        <link name="name" '
            'target="/$var.entryname#\'scan\'$var.serialno/'
            'sample/{cpname}/name"/>\n'
            '        <link name="short_name" '
            'target="/$var.entryname#\'scan\'$var.serialno/'
            'sample/{cpname}/short_name"/>\n'
            '        <link name="type" '
            'target="/$var.entryname#\'scan\'$var.serialno/'
            'sample/{cpname}/type"/>\n'
            '      </group>\n'
            '      <link name="temperature" '
            'target="/$var.entryname#\'scan\'$var.serialno/'
            'sample/{cpname}/T/value_log"/>\n'
            '    </group>\n'
            '  </group>\n'
            '</definition>\n'
        )
        self.myuni2 = (
            '<?xml version=\'1.0\' encoding=\'utf8\'?>\n'
            '<definition>\n'
            '  <group name="$var.entryname#\'scan\'$var.serialno" '
            'type="NXentry">\n'
            '    <group name="sample" type="NXsample">\n'
            '      <group name="temperature_env" type="NXenvironment">\n'
            '        <link name="T" target="/$var.entryname#\'scan\''
            '$var.serialno/instrument/{cpname}/T"/>\n'
            '        <link name="description" target="/$var.entryname#\'scan\''
            '$var.serialno/instrument/{cpname}/description"/>\n'
            '        <link name="name" target="/$var.entryname#\'scan\''
            '$var.serialno/instrument/{cpname}/name"/>\n'
            '        <link name="short_name" target="/$var.entryname#\'scan\''
            '$var.serialno/instrument/{cpname}/short_name"/>\n'
            '        <link name="type" target="/$var.entryname#\'scan\''
            '$var.serialno/instrument/{cpname}/type"/>\n'
            '      </group>\n'
            '      <link name="temperature" target="/$var.entryname#\'scan\''
            '$var.serialno/instrument/{cpname}/T/value_log"/>\n'
            '      <group name="transformations" type="NXtransformations">\n'
            '        <link name="{cpname}_drv" target="/$var.entryname#\''
            'scan\'$var.serialno/instrument/{cpname}/drv/value_log/value"/>\n'
            '      </group>\n'
            '    </group>\n'
            '    <group name="instrument" type="NXinstrument">\n'
            '      <group name="{cpname}" type="{nodegroup}">\n'
            '        <field name="name" type="NX_CHAR">uniax_sim.psi.ch'
            '<strategy mode="INIT"/></field>\n'
            '        <field name="short_name" type="NX_CHAR">{cpname}'
            '<strategy mode="INIT"/></field>\n'
            '        <field name="type" type="NX_CHAR">FRAPPY - The Python '
            'Framework for SECoP (2021.02)<strategy mode="INIT"/></field>\n'
            '        <field name="description" type="NX_CHAR">[sim] uniaxial '
            'pressure device<strategy mode="INIT"/></field>\n'
            '        <group name="force" type="NXsensor">\n'
            '          <field name="name" type="NX_CHAR">force'
            '<strategy mode="INIT"/></field>\n'
            '          <field name="description" type="NX_CHAR">uniax driver'
            '<strategy mode="INIT"/></field>\n'
            '          <field name="model" type="NX_CHAR">'
            'secop_psi.uniax.Uniax<strategy mode="INIT"/></field>\n'
            '          <group name="parameters" type="NXcollection">\n'
            '            <group name="status" type="NXlog">\n'
            '              <field name="value" type="NX_INT64">'
            '$datasources.{cpname}_force_status<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force_status_time<attribute name="start" '
            'type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '            <group name="pollinterval" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_force_pollinterval<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force_pollinterval_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '              <field name="minimal_value" type="NX_FLOAT64">'
            '0.1<strategy mode="INIT"/></field>\n'
            '              <field name="maximal_value" type="NX_FLOAT64">'
            '120<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="target" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="N">'
            '$datasources.{cpname}_force_target<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force_target_time<attribute name="start" '
            'type="NX_DATE_TIME">$datasources.client_start_time<strategy '
            'mode="INIT"/></attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_limit" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="N">'
            '$datasources.{cpname}_force__limit<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__limit_time<attribute name="start" '
            'type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="maximal_value" type="NX_FLOAT64" '
            'units="N">150<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_tolerance" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="N">'
            '$datasources.{cpname}_force__tolerance<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__tolerance_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '              <field name="maximal_value" type="NX_FLOAT64" '
            'units="N">10<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_slope" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="deg/N">$datasources.{cpname}_force__slope'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__slope_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '            <group name="_pid_i" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_force__pid_i<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__pid_i_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_filter_interval" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__filter_interval'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__filter_interval_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '              <field name="maximal_value" type="NX_FLOAT64" '
            'units="s">60<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_current_step" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="deg">'
            '$datasources.{cpname}_force__current_step<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__current_step_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_force_offset" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="N">'
            '$datasources.{cpname}_force__force_offset<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__force_offset_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '            <group name="_hysteresis" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="N">'
            '$datasources.{cpname}_force__hysteresis<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__hysteresis_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="maximal_value" type="NX_FLOAT64" '
            'units="N">150<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_adjusting" type="NXlog">\n'
            '              <field name="value" type="NX_BOOLEAN">'
            '$datasources.{cpname}_force__adjusting<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__adjusting_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_adjusting_current" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="A">'
            '$datasources.{cpname}_force__adjusting_current'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__adjusting_current_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '              <field name="maximal_value" type="NX_FLOAT64" '
            'units="A">2.8<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_safe_step" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="deg">'
            '$datasources.{cpname}_force__safe_step<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__safe_step_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_safe_current" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="A">'
            '$datasources.{cpname}_force__safe_current<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__safe_current_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="maximal_value" type="NX_FLOAT64" '
            'units="A">2.8<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_low_pos" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="deg">'
            '$datasources.{cpname}_force__low_pos<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__low_pos_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '            <group name="_high_pos" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="deg">'
            '$datasources.{cpname}_force__high_pos<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force__high_pos_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_'
            'start_time<strategy mode="INIT"/></attribute><strategy '
            'mode="INIT"/></field>\n'
            '            </group>\n'
            '          </group>\n'
            '          <group name="value_log" type="NXlog">\n'
            '            <field name="value" type="NX_FLOAT64" units="N">'
            '$datasources.{cpname}_force<strategy mode="INIT"/></field>\n'
            '            <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_force_time<attribute name="start" '
            'type="NX_DATE_TIME">$datasources.client_start_time<strategy '
            'mode="INIT"/></attribute><strategy mode="INIT"/></field>\n'
            '          </group>\n'
            '          <link name="value" target="/$var.entryname#\'scan\''
            '$var.serialno/instrument/{cpname}/force/'
            'parameters/target/value"/>\n'
            '        </group>\n'
            '        <group name="drv" type="NXsensor">\n'
            '          <field name="name" type="NX_CHAR">drv'
            '<strategy mode="INIT"/></field>\n'
            '          <field name="description" type="NX_CHAR">'
            'simulated motor'
            '<strategy mode="INIT"/></field>\n'
            '          <field name="model" type="NX_CHAR">'
            'secop.simulation.SimBase_drv<strategy mode="INIT"/></field>\n'
            '          <group name="parameters" type="NXcollection">\n'
            '            <group name="status" type="NXlog">\n'
            '              <field name="value" type="NX_INT64">'
            '$datasources.{cpname}_drv_status<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_drv_status_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="pollinterval" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_drv_pollinterval<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_drv_pollinterval_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="minimal_value" type="NX_FLOAT64">0.1'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="maximal_value" type="NX_FLOAT64">120'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="target" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="deg">'
            '$datasources.{cpname}_drv_target<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_drv_target_time<attribute name="start" '
            'type="NX_DATE_TIME">$datasources.client_start_time<strategy '
            'mode="INIT"/></attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_interval" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_drv__interval<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_drv__interval_time<attribute name="start"'
            ' type="NX_DATE_TIME">$datasources.client_start_time<strategy '
            'mode="INIT"/></attribute><strategy mode="INIT"/></field>\n'
            '              <field name="maximal_value" type="NX_FLOAT64">1'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_speed" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_drv__speed<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_drv__speed_time<attribute name="start" '
            'type="NX_DATE_TIME">$datasources.client_start_time<strategy '
            'mode="INIT"/></attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_safe_current" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_drv__safe_current<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_drv__safe_current_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '            <group name="_move_limit" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_drv__move_limit<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_drv__move_limit_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '            <group name="_maxcurrent" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_drv__maxcurrent<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_drv__maxcurrent_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '            <group name="_tolerance" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_drv__tolerance<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_drv__tolerance_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '          </group>\n'
            '          <group name="value_log" type="NXlog">\n'
            '            <field name="value" type="NX_FLOAT64" units="deg" '
            'transformation_type="rotation">$datasources.{cpname}_drv'
            '<attribute name="vector" type="NX_FLOAT64">0 1 0<dimensions '
            'rank="1"><dim index="1" value="3"/></dimensions><strategy '
            'mode="INIT"/></attribute><strategy mode="INIT"/></field>\n'
            '            <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_drv_time<attribute name="start" '
            'type="NX_DATE_TIME">$datasources.client_start_time<strategy '
            'mode="INIT"/></attribute><strategy mode="INIT"/></field>\n'
            '          </group>\n'
            '          <link name="value" target="/$var.entryname#\'scan\''
            '$var.serialno/instrument/{cpname}/drv/parameters/target/value"/>'
            '\n'
            '        </group>\n'
            '        <group name="transducer" type="NXsensor">\n'
            '          <field name="name" type="NX_CHAR">transducer'
            '<strategy mode="INIT"/></field>\n'
            '          <field name="description" type="NX_CHAR">'
            'simulated force'
            '<strategy mode="INIT"/></field>\n'
            '          <field name="model" type="NX_CHAR">'
            'secop_psi.simdpm.DPM3<strategy mode="INIT"/></field>\n'
            '          <group name="parameters" type="NXcollection">\n'
            '            <group name="status" type="NXlog">\n'
            '              <field name="value" type="NX_INT64">'
            '$datasources.{cpname}_transducer_status<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_transducer_status_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '            <group name="pollinterval" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_transducer_pollinterval<strategy '
            'mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_transducer_pollinterval_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '              <field name="minimal_value" type="NX_FLOAT64">0.1'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="maximal_value" type="NX_FLOAT64">120'
            '<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_jitter" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="N">'
            '$datasources.{cpname}_transducer__jitter<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_transducer__jitter_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '            <group name="_hysteresis" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="deg">'
            '$datasources.{cpname}_transducer__hysteresis'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_transducer__hysteresis_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_friction" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="N/deg">$datasources.{cpname}_transducer__friction'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_transducer__friction_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_slope" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" '
            'units="N/deg">$datasources.{cpname}_transducer__slope'
            '<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_transducer__slope_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_offset" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64" units="N">'
            '$datasources.{cpname}_transducer__offset<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_transducer__offset_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '          </group>\n'
            '          <group name="value_log" type="NXlog">\n'
            '            <field name="value" type="NX_FLOAT64" units="N">'
            '$datasources.{cpname}_transducer<strategy mode="INIT"/></field>\n'
            '            <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_transducer_time<attribute name="start" '
            'type="NX_DATE_TIME">$datasources.client_start_time<strategy '
            'mode="INIT"/></attribute><strategy mode="INIT"/></field>\n'
            '          </group>\n'
            '        </group>\n'
            '        <group name="res" type="NXsensor">\n'
            '          <field name="name" type="NX_CHAR">res'
            '<strategy mode="INIT"/>'
            '</field>\n'
            '          <field name="description" type="NX_CHAR">'
            'raw temperature sensor on the stick<strategy mode="INIT"/>'
            '</field>\n'
            '          <field name="model" type="NX_CHAR">'
            'secop.simulation.SimBase_res<strategy mode="INIT"/></field>\n'
            '          <group name="parameters" type="NXcollection">\n'
            '            <group name="status" type="NXlog">\n'
            '              <field name="value" type="NX_INT64">'
            '$datasources.{cpname}_res_status<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_res_status_time<attribute name="start" '
            'type="NX_DATE_TIME">$datasources.client_start_time<strategy '
            'mode="INIT"/></attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="pollinterval" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_res_pollinterval<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_res_pollinterval_time<attribute '
            'name="start" type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="minimal_value" type="NX_FLOAT64">'
            '0.1<strategy mode="INIT"/></field>\n'
            '              <field name="maximal_value" type="NX_FLOAT64">'
            '120<strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '            <group name="_jitter" type="NXlog">\n'
            '              <field name="value" type="NX_FLOAT64">'
            '$datasources.{cpname}_res__jitter<strategy mode="INIT"/>'
            '</field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_res__jitter_time'
            '<attribute name="start" type="NX_DATE_TIME">'
            '$datasources.client_start_time<strategy mode="INIT"/>'
            '</attribute><strategy mode="INIT"/></field>\n'
            '            </group>\n'
            '          </group>\n'
            '          <group name="value_log" type="NXlog">\n'
            '            <field name="value" type="NX_FLOAT64" units="Ohm">'
            '$datasources.{cpname}_res<strategy mode="INIT"/></field>\n'
            '            <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_res_time<attribute name="start" '
            'type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '          </group>\n'
            '        </group>\n'
            '        <group name="T" type="NXsensor">\n'
            '          <field name="name" type="NX_CHAR">'
            'T<strategy mode="INIT"/>'
            '</field>\n'
            '          <field name="description" type="NX_CHAR">'
            'temperature sensor, soft calibration<strategy mode="INIT"/>'
            '</field>\n'
            '          <field name="measurement" type="NX_CHAR">temperature'
            '<strategy mode="INIT"/></field>\n'
            '          <field name="model" type="NX_CHAR">'
            'secop_psi.softcal.Sensor<strategy mode="INIT"/></field>\n'
            '          <group name="parameters" type="NXcollection">\n'
            '            <group name="status" type="NXlog">\n'
            '              <field name="value" type="NX_INT64">'
            '$datasources.{cpname}_t_status<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_t_status_time<attribute name="start" '
            'type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '            <group name="_calib" type="NXlog">\n'
            '              <field name="value" type="NX_CHAR">'
            '$datasources.{cpname}_t__calib<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_t__calib_time<attribute name="start" '
            'type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '            <group name="_abs" type="NXlog">\n'
            '              <field name="value" type="NX_BOOLEAN">'
            '$datasources.{cpname}_t__abs<strategy mode="INIT"/></field>\n'
            '              <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_t__abs_time<attribute name="start" '
            'type="NX_DATE_TIME">$datasources.client_start_time'
            '<strategy mode="INIT"/></attribute><strategy mode="INIT"/>'
            '</field>\n'
            '            </group>\n'
            '          </group>\n'
            '          <group name="value_log" type="NXlog">\n'
            '            <field name="value" type="NX_FLOAT64" units="K">'
            '$datasources.{cpname}_t<strategy mode="INIT"/></field>\n'
            '            <field name="time" type="NX_FLOAT64" units="s">'
            '$datasources.{cpname}_t_time<attribute name="start" '
            'type="NX_DATE_TIME">$datasources.client_start_time<strategy '
            'mode="INIT"/></attribute><strategy mode="INIT"/></field>\n'
            '          </group>\n'
            '        </group>\n'
            '      </group>\n'
            '    </group>\n'
            '  </group>\n'
            '</definition>\n'
            )

        self.myunids = [
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
            '  <datasource type="PYEVAL" name="{cpname}_drv">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd("read drv:value", '
            '"", "5000", "0.001", "{cpname}_drv", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_drv__interval">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read drv:_interval", "", "5000", "0.001", '
            '"{cpname}_drv__interval", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_drv__interval_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd("read drv:_interval", '
            '"", "5000", "0.001", "{cpname}_drv__interval", '
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
            'name="{cpname}_drv__maxcurrent">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read drv:_maxcurrent", "", "5000", "0.001", '
            '"{cpname}_drv__maxcurrent", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_drv__maxcurrent_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read drv:_maxcurrent", "", "5000", "0.001", '
            '"{cpname}_drv__maxcurrent", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_drv__move_limit">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read drv:_move_limit", "", "5000", "0.001", '
            '"{cpname}_drv__move_limit", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_drv__move_limit_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read drv:_move_limit", "", "5000", "0.001", '
            '"{cpname}_drv__move_limit", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_drv__safe_current">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read drv:_safe_current", "", "5000", "0.001", '
            '"{cpname}_drv__safe_current", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_drv__safe_current_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read drv:_safe_current", "", "5000", "0.001", '
            '"{cpname}_drv__safe_current", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" name="{cpname}_drv__speed">'
            '\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read drv:_speed", "", "5000", "0.001", '
            '"{cpname}_drv__speed", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_drv__speed_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read drv:_speed", "", "5000", "0.001", '
            '"{cpname}_drv__speed", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_drv__tolerance">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read drv:_tolerance", "", "5000", "0.001", '
            '"{cpname}_drv__tolerance", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_drv__tolerance_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read drv:_tolerance", "", "5000", "0.001", '
            '"{cpname}_drv__tolerance", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_drv_pollinterval">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read drv:pollinterval", "", "5000", "0.001", '
            '"{cpname}_drv_pollinterval", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_drv_pollinterval_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read drv:pollinterval", "", "5000", "0.001", '
            '"{cpname}_drv_pollinterval", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" name="{cpname}_drv_status">'
            '\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd("read drv:status",'
            ' "", "5000", "0.001", "{cpname}_drv_status", [0,0], '
            'commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_drv_status_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read drv:status", "", "5000", "0.001", '
            '"{cpname}_drv_status", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" name="{cpname}_drv_target">'
            '\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read drv:target", "", "5000", "0.001", '
            '"{cpname}_drv_target", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_drv_target_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read drv:target", "", "5000", "0.001", '
            '"{cpname}_drv_target", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" name="{cpname}_drv_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read drv:value", "", "5000", "0.001", '
            '"{cpname}_drv", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" name="{cpname}_force">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:value", "", "5000", "0.001", '
            '"{cpname}_force", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__adjusting">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:_adjusting", "", "5000", "0.001", '
            '"{cpname}_force__adjusting", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__adjusting_current">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:_adjusting_current", "", "5000", '
            '"0.001", "{cpname}_force__adjusting_current", [0], '
            'commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__adjusting_current_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:_adjusting_current", "", "5000", '
            '"0.001", "{cpname}_force__adjusting_current", '
            '[1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__adjusting_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:_adjusting", "", "5000", "0.001", '
            '"{cpname}_force__adjusting", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__current_step">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:_current_step", "", "5000", "0.001", '
            '"{cpname}_force__current_step", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__current_step_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:_current_step", "", "5000", "0.001", '
            '"{cpname}_force__current_step", [1, "t"], '
            'commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__filter_interval">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:_filter_interval", "", "5000", "0.001",'
            ' "{cpname}_force__filter_interval", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__filter_interval_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:_filter_interval", "", "5000", "0.001",'
            ' "{cpname}_force__filter_interval", [1, "t"],'
            ' commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__force_offset">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:_force_offset", "", "5000", "0.001", '
            '"{cpname}_force__force_offset", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__force_offset_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:_force_offset", "", "5000", "0.001", '
            '"{cpname}_force__force_offset", [1, "t"], '
            'commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__high_pos">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:_high_pos", "", "5000", "0.001", '
            '"{cpname}_force__high_pos", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__high_pos_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:_high_pos", "", "5000", "0.001", '
            '"{cpname}_force__high_pos", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__hysteresis">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:_hysteresis", "", "5000", "0.001", '
            '"{cpname}_force__hysteresis", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__hysteresis_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:_hysteresis", "", "5000", "0.001", '
            '"{cpname}_force__hysteresis", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__limit">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:_limit", "", "5000", "0.001", '
            '"{cpname}_force__limit", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__limit_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:_limit", "", "5000", "0.001", '
            '"{cpname}_force__limit", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__low_pos">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:_low_pos", "", "5000", "0.001", '
            '"{cpname}_force__low_pos", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__low_pos_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:_low_pos", "", "5000", "0.001", '
            '"{cpname}_force__low_pos", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__pid_i">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:_pid_i", "", "5000", "0.001", '
            '"{cpname}_force__pid_i", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__pid_i_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:_pid_i", "", "5000", "0.001", '
            '"{cpname}_force__pid_i", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__safe_current">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:_safe_current", "", "5000", "0.001", '
            '"{cpname}_force__safe_current", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__safe_current_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:_safe_current", "", "5000", "0.001", '
            '"{cpname}_force__safe_current", [1, "t"], '
            'commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__safe_step">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:_safe_step", "", "5000", "0.001", '
            '"{cpname}_force__safe_step", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__safe_step_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:_safe_step", "", "5000", "0.001", '
            '"{cpname}_force__safe_step", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__slope">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:_slope", "", "5000", "0.001", '
            '"{cpname}_force__slope", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__slope_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:_slope", "", "5000", "0.001", '
            '"{cpname}_force__slope", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__tolerance">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:_tolerance", "", "5000", "0.001", '
            '"{cpname}_force__tolerance", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force__tolerance_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:_tolerance", "", "5000", "0.001", '
            '"{cpname}_force__tolerance", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force_pollinterval">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:pollinterval", "", "5000", "0.001", '
            '"{cpname}_force_pollinterval", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force_pollinterval_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:pollinterval", "", "5000", "0.001", '
            '"{cpname}_force_pollinterval", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force_status">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:status", "", "5000", "0.001", '
            '"{cpname}_force_status", [0,0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force_status_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read force:status", "", "5000", "0.001", '
            '"{cpname}_force_status", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force_target">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read force:target", "", "5000", "0.001", '
            '"{cpname}_force_target", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force_target_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd("read force:target", '
            '"", "5000", "0.001", "{cpname}_force_target", '
            '[1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_force_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd("read force:value", '
            '"", "5000", "0.001", "{cpname}_force", [1, "t"], '
            'commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" name="{cpname}_res">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read res:value", "", "5000", "0.001", '
            '"{cpname}_res", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_res__jitter">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read res:_jitter", "", "5000", "0.001", '
            '"{cpname}_res__jitter", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_res__jitter_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd("read res:_jitter", '
            '"", "5000", "0.001", "{cpname}_res__jitter", '
            '[1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_res_pollinterval">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read res:pollinterval", "", "5000", "0.001", '
            '"{cpname}_res_pollinterval", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_res_pollinterval_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read res:pollinterval", "", "5000", "0.001", '
            '"{cpname}_res_pollinterval", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_res_status">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read res:status", "", "5000", "0.001", '
            '"{cpname}_res_status", [0,0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_res_status_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd("read res:status", '
            '"", "5000", "0.001", "{cpname}_res_status", [1, "t"], '
            'commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" name="{cpname}_res_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read res:value", "", "5000", "0.001", '
            '"{cpname}_res", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" name="{cpname}_t">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read T:value", "", "5000", "0.001", "{cpname}_t", '
            '[0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" name="{cpname}_t__abs">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd("read T:_abs", '
            '"", "5000", "0.001", "{cpname}_t__abs", [0], '
            'commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_t__abs_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd("read T:_abs", "", '
            '"5000", "0.001", "{cpname}_t__abs", [1, "t"], '
            'commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" name="{cpname}_t__calib">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read T:_calib", "", "5000", "0.001", '
            '"{cpname}_t__calib", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_t__calib_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read T:_calib", "", "5000", "0.001", '
            '"{cpname}_t__calib", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" name="{cpname}_t_status">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read T:status", "", "5000", "0.001", '
            '"{cpname}_t_status", [0,0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_t_status_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read T:status", "", "5000", "0.001", '
            '"{cpname}_t_status", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" name="{cpname}_t_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read T:value", "", "5000", "0.001", "{cpname}_t", '
            '[1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read transducer:value", "", "5000", "0.001", '
            '"{cpname}_transducer", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer__friction">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read transducer:_friction", "", "5000", "0.001", '
            '"{cpname}_transducer__friction", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer__friction_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read transducer:_friction", "", "5000", "0.001", '
            '"{cpname}_transducer__friction", [1, "t"], '
            'commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer__hysteresis">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read transducer:_hysteresis", "", "5000", '
            '"0.001", "{cpname}_transducer__hysteresis", [0], '
            'commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer__hysteresis_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read transducer:_hysteresis", "", "5000", '
            '"0.001", "{cpname}_transducer__hysteresis", '
            '[1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer__jitter">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read transducer:_jitter", "", "5000", "0.001", '
            '"{cpname}_transducer__jitter", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer__jitter_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read transducer:_jitter", "", "5000", "0.001", '
            '"{cpname}_transducer__jitter", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer__offset">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read transducer:_offset", "", "5000", "0.001", '
            '"{cpname}_transducer__offset", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer__offset_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read transducer:_offset", "", "5000", "0.001", '
            '"{cpname}_transducer__offset", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer__slope">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read transducer:_slope", "", "5000", "0.001", '
            '"{cpname}_transducer__slope", [0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer__slope_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read transducer:_slope", "", "5000", "0.001", '
            '"{cpname}_transducer__slope", [1, "t"], '
            'commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer_pollinterval">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read transducer:pollinterval", "", "5000", '
            '"0.001", "{cpname}_transducer_pollinterval", [0], '
            'commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer_pollinterval_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read transducer:pollinterval", "", "5000", '
            '"0.001", "{cpname}_transducer_pollinterval", '
            '[1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer_status">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'ds.result = secop.secop_group_cmd('
            '"read transducer:status", "", "5000", "0.001", '
            '"{cpname}_transducer_status", [0,0], commonblock)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer_status_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read transducer:status", "", "5000", "0.001", '
            '"{cpname}_transducer_status", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock, ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n',
            '<?xml version=\'1.0\'?>\n'
            '<definition>\n'
            '  <datasource type="PYEVAL" '
            'name="{cpname}_transducer_time">\n'
            '    <result name="result">\n'
            'from nxstools.pyeval import secop\n'
            'from nxstools.pyeval import timestamp\n'
            'ctime = secop.secop_group_cmd('
            '"read transducer:value", "", "5000", "0.001", '
            '"{cpname}_transducer", [1, "t"], commonblock)\n'
            'ds.result = timestamp.relative_timestamp('
            'commonblock,'
            ' ctime)\n'
            '    </result>\n'
            '  </datasource>\n'
            '</definition>\n'
        ]

        self.secoplist = [
            # 'client_start_time',
            '{cpname}',
            '{cpname}_drv',
            '{cpname}_drv__interval',
            '{cpname}_drv__interval_time',
            '{cpname}_drv__maxcurrent',
            '{cpname}_drv__maxcurrent_time',
            '{cpname}_drv__move_limit',
            '{cpname}_drv__move_limit_time',
            '{cpname}_drv__safe_current',
            '{cpname}_drv__safe_current_time',
            '{cpname}_drv__speed',
            '{cpname}_drv__speed_time',
            '{cpname}_drv__tolerance',
            '{cpname}_drv__tolerance_time',
            '{cpname}_drv_pollinterval',
            '{cpname}_drv_pollinterval_time',
            '{cpname}_drv_status',
            '{cpname}_drv_status_time',
            '{cpname}_drv_target',
            '{cpname}_drv_target_time',
            '{cpname}_drv_time',
            '{cpname}_force',
            '{cpname}_force__adjusting',
            '{cpname}_force__adjusting_current',
            '{cpname}_force__adjusting_current_time',
            '{cpname}_force__adjusting_time',
            '{cpname}_force__current_step',
            '{cpname}_force__current_step_time',
            '{cpname}_force__filter_interval',
            '{cpname}_force__filter_interval_time',
            '{cpname}_force__force_offset',
            '{cpname}_force__force_offset_time',
            '{cpname}_force__high_pos',
            '{cpname}_force__high_pos_time',
            '{cpname}_force__hysteresis',
            '{cpname}_force__hysteresis_time',
            '{cpname}_force__limit',
            '{cpname}_force__limit_time',
            '{cpname}_force__low_pos',
            '{cpname}_force__low_pos_time',
            '{cpname}_force__pid_i',
            '{cpname}_force__pid_i_time',
            '{cpname}_force__safe_current',
            '{cpname}_force__safe_current_time',
            '{cpname}_force__safe_step',
            '{cpname}_force__safe_step_time',
            '{cpname}_force__slope',
            '{cpname}_force__slope_time',
            '{cpname}_force__tolerance',
            '{cpname}_force__tolerance_time',
            '{cpname}_force_pollinterval',
            '{cpname}_force_pollinterval_time',
            '{cpname}_force_status',
            '{cpname}_force_status_time',
            '{cpname}_force_target',
            '{cpname}_force_target_time',
            '{cpname}_force_time',
            '{cpname}_res',
            '{cpname}_res__jitter',
            '{cpname}_res__jitter_time',
            '{cpname}_res_pollinterval',
            '{cpname}_res_pollinterval_time',
            '{cpname}_res_status',
            '{cpname}_res_status_time',
            '{cpname}_res_time',
            '{cpname}_t',
            '{cpname}_t__abs',
            '{cpname}_t__abs_time',
            '{cpname}_t__calib',
            '{cpname}_t__calib_time',
            '{cpname}_t_status',
            '{cpname}_t_status_time',
            '{cpname}_t_time',
            '{cpname}_transducer',
            '{cpname}_transducer__friction',
            '{cpname}_transducer__friction_time',
            '{cpname}_transducer__hysteresis',
            '{cpname}_transducer__hysteresis_time',
            '{cpname}_transducer__jitter',
            '{cpname}_transducer__jitter_time',
            '{cpname}_transducer__offset',
            '{cpname}_transducer__offset_time',
            '{cpname}_transducer__slope',
            '{cpname}_transducer__slope_time',
            '{cpname}_transducer_pollinterval',
            '{cpname}_transducer_pollinterval_time',
            '{cpname}_transducer_status',
            '{cpname}_transducer_status_time',
            '{cpname}_transducer_time'
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
                ('nxscreate secopcp --list --json-file %s %s'
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
                ('nxscreate secopcp --list --json-file %s %s'
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
        secoplist = [cc.format(cpname=cname) for cc in self.secoplist]

        args = [
            [
                ('nxscreate secopcp -c %s -j %s %s'
                 % (cname, fname, self.flags)).split(),
                ('nxscreate secopcp --component %s --json-file %s %s'
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
                self.assertEqual(len(ncst), len(secoplist))
                for si, scn in enumerate(secoplist):
                    # print(scn, ncst[si])
                    if "_" in scn:
                        self.assertEqual(ncst[si], fmtstr.format(name=scn))
                    else:
                        self.assertEqual(ncst[si], cfmtstr.format(name=scn))

        finally:
            os.remove(fname)
            for scn in secoplist:
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

        shutil.copy("test/files/secop.conf", fname)

        dsl = ["client_start_time"]
        dsl.extend(self.secoplist[1:])
        args = [
            [
                [
                    ('nxscreate secopcp -c %s -j %s %s'
                     % (cname, fname, self.flags)).split(),
                    ('nxscreate secopcp --component %s --json-file %s %s'
                     % (cname, fname, self.flags)).split(),
                ],
                [
                    [self.secoplist[0].format(cpname=cname)],
                    [ds.format(cpname=cname) for ds in dsl]
                ],
                [
                    [
                        self.myuni.format(nodegroup="NXenvironment",
                                          cpname=cname)
                    ],
                    [ds.format(cpname=cname) for ds in self.myunids]
                ],
            ],
        ]
        self.checkxmls(args, fname)

    def test_secopcp_create_nii(self):
        """ test nxsccreate stdcomp file system
        """

        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.json' % (
            os.getcwd(), self.__class__.__name__, fun)

        cname = "myuni"

        shutil.copy("test/files/secop.conf", fname)

        dsl = ["client_start_time"]
        dsl.extend(self.secoplist[1:])
        args = [
            [
                [
                    ('nxscreate secopcp --node-in-instrument -c %s -j %s %s'
                     % (cname, fname, self.flags)).split(),
                    ('nxscreate secopcp -w --component %s --json-file %s %s'
                     % (cname, fname, self.flags)).split(),
                ],
                [
                    [self.secoplist[0].format(cpname=cname)],
                    [ds.format(cpname=cname) for ds in dsl]
                ],
                [
                    [
                        self.myuni2.format(nodegroup="NXenvironment",
                                           cpname=cname)
                    ],
                    [ds.format(cpname=cname) for ds in self.myunids]
                ],
            ],
        ]
        self.checkxmls(args, fname)

    def test_secopcp_create_strict(self):
        """ test nxsccreate stdcomp file system
        """

        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.json' % (
            os.getcwd(), self.__class__.__name__, fun)

        cname = "myuni"

        shutil.copy("test/files/secop.conf", fname)

        dsl = ["client_start_time"]
        dsl.extend(self.secoplist[1:])
        args = [
            [
                [
                    ('nxscreate secopcp  -q -c %s -j %s %s'
                     % (cname, fname, self.flags)).split(),
                    ('nxscreate secopcp --strict --component %s '
                     '--json-file %s %s'
                     % (cname, fname, self.flags)).split(),
                ],
                [
                    [self.secoplist[0].format(cpname=cname)],
                    [ds.format(cpname=cname) for ds in dsl]
                ],
                [
                    [
                        self.myuni.format(nodegroup="NXcollection",
                                          cpname=cname)
                    ],
                    [ds.format(cpname=cname) for ds in self.myunids]
                ],
            ],
        ]
        self.checkxmls(args, fname)

    def test_secopcp_create_def(self):
        """ test nxsccreate stdcomp file system
        """

        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.json' % (
            os.getcwd(), self.__class__.__name__, fun)

        cname = "uniax_sim"

        shutil.copy("test/files/secop.conf", fname)

        dsl = ["client_start_time"]
        dsl.extend(self.secoplist[1:])
        args = [
            [
                [
                    ('nxscreate secopcp --node-in-instrument -j %s %s'
                     % (fname, self.flags)).split(),
                    ('nxscreate secopcp -w --json-file %s %s'
                     % (fname, self.flags)).split(),
                ],
                [
                    [self.secoplist[0].format(cpname=cname)],
                    [ds.format(cpname=cname) for ds in dsl]
                ],
                [
                    [
                        self.myuni2.format(nodegroup="NXenvironment",
                                           cpname=cname)
                    ],
                    [ds.format(cpname=cname) for ds in self.myunids]
                ],
            ],
        ]
        self.checkxmls(args, fname)


if __name__ == '__main__':
    unittest.main()
