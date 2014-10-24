#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2013 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \package nexdatas nexdatas.tools
## \file nxsdata.py
# Command-line tool to ascess to  Tango Data Server
#
""" Set Up NeXus Tango Servers"""

import socket
import PyTango
import os
import sys
import subprocess
import time


class SetUp(object):

    def __init__(self):
        try:
            self.db = PyTango.Database()
        except:
            print "Can't connect to tango database on", \
                os.getenv('TANGO_HOST')
            sys.exit(255)

        self.server_ctrl_name = None
        if os.path.isfile('/usr/lib/tango/fsectools/server_ctrl.py'):
            self.server_ctrl_name = '/usr/lib/tango/fsectools/server_ctrl.py'
        elif os.path.isfile('/usr/local/sbin/server_ctrl.py'):
            self.server_ctrl_name = '/usr/local/sbin/server_ctrl.py'
        else:
            print "startup: failed to find server_ctrl.py"
        self.writer_name = None
        self.cserver_name = None
        self._psub = None

    def startupServer(self, klass, instance, device):
        self._psub = subprocess.call(
            "%s %s &" % (klass, instance),
            stdout=None, stderr=None, shell=True)
        print "waiting for server",

        found = False
        cnt = 0
        while not found and cnt < 1000:
            try:
                print "\b.",
                dp = PyTango.DeviceProxy(device)
                time.sleep(0.01)
                if dp.state() == PyTango.DevState.ON:
                    found = True
            except:
                found = False
            cnt += 1
        print ""

    def createDataWriter(self, beamline, masterHost):
        """Create DataWriter """
        if not beamline:
            print "createDataWriter: no beamline given "
            return 0
        if not masterHost:
            print "createDataWriter: no masterHost given "
            return 0

        class_name = 'NXSDataWriter'
        server = class_name
        server_name = server + '/' + masterHost
        full_class_name = 'NXSDataWriter/' + masterHost
        self.writer_name = "%s/nxsdatawriter/%s" % (beamline, masterHost)
        if not server_name in self.db.get_server_list(server_name):
            print "createDataWriter: creating " + server_name

            if server_name in self.db.get_server_list(server_name):
                print "createDataWriter: DB contains already " + server_name
                return 0

            di = PyTango.DbDevInfo()
            di.name = self.writer_name
            di._class = class_name
            di.server = server_name

            self.db.add_device(di)
            self.db.put_device_property(self.writer_name,
                                        {'NumberOfThreads': 100})

        hostname = socket.gethostname()

        if self.server_ctrl_name:
            com = self.server_ctrl_name + " -n " + full_class_name + \
                " --mach=" + hostname + " --add -l 1"
            print "createDataWriter: ", com
            if os.system(com):
                print "createDataWriter failed to add the NXSDataWriter" \
                    " to the starter"
                sys.exit(255)

            com = self.server_ctrl_name + " -n " + full_class_name + " -s" \
                + " -t " + hostname
            print "createDataWriter: ", com
            if os.system(com):
                print "createDataWriter failed to start the NXSDataWriter"
                sys.exit(255)
        else:
            self.startupServer(class_name, hostname, self.writer_name)
        return 1

    def createConfigServer(self, beamline, masterHost, user,
                           jsonsettings=None):
        """Create DataWriter """
        if not beamline:
            print "createConfigServer: no beamline given "
            return 0
        if not masterHost:
            print "createConfigServer: no masterHost given "
            return 0

        class_name = 'NXSConfigServer'
        server = class_name
        server_name = server + '/' + masterHost
        self.cserver_name = "%s/nxsconfigserver/%s" % (beamline, masterHost)
        if not server_name in self.db.get_server_list(server_name):
            print "createConfigServer: creating " + server_name

            if server_name in self.db.get_server_list(server_name):
                print "createConfigServer: DB contains already " + server_name
                return 0

            di = PyTango.DbDevInfo()
            di.name = self.cserver_name
            di._class = class_name
            di.server = server_name

            self.db.add_device(di)
            self.db.put_device_property(
                self.cserver_name, {'VersionLabel': '%s@%s' % (
                        beamline.upper(), masterHost.upper())})

        hostname = self.db.get_db_host().split(".")[0]

        if self.server_ctrl_name:
            com = self.server_ctrl_name + " -n " + server_name + \
                " --mach=" + hostname + " --add -l 1"
            print "createConfigServer: ", com
            if os.system(com):
                print "createConfigServer failed to add the NXSConfigServer" \
                    " to the starter"
                sys.exit(255)

            com = self.server_ctrl_name + " -n " + server_name + " -s" \
                + " -t " + hostname
            print "createConfigServer: ", com
            if os.system(com):
                print "createConfigServer failed to start the NXSConfigServer"
                sys.exit(255)
        else:
            self.startupServer(class_name, hostname, self.cserver_name)

        dp = PyTango.DeviceProxy(self.cserver_name)
        if dp.state() != PyTango.DevState.ON:
            dp.Close()
        if jsonsettings:
            dp = PyTango.DeviceProxy(self.cserver_name)
        elif self.server_ctrl_name:
            dp.JSONSettings = '{"host":"localhost","db":"nxsconfig",' \
                + ' "read_default_file":"/home/%s/.my.cnf",' % user \
                + ' "use_unicode":true}'
        dp.Open()

        return 1

    def createSelector(self, beamline, masterHost, writer=None, cserver=None):
        """Create Selector Server """
        if not beamline:
            print "createSelector: no beamline given "
            return 0
        if not masterHost:
            print "createSelector: no masterHost given "
            return 0
        if writer:
            self.writer_name = writer
        if cserver:
            self.cserver_name = cserver

        class_name = 'NXSRecSelector'
        server = class_name
        server_name = server + '/' + masterHost
        full_class_name = 'NXSRecSelector/' + masterHost
        if not server_name in self.db.get_server_list(server_name):
            print "createSelector: creating " + server_name

            device_name = "%s/nxsrecselector/%s" % (beamline, masterHost)
            if server_name in self.db.get_server_list(server_name):
                print "createSelector: DB contains already " + server_name
                return 0

            di = PyTango.DbDevInfo()
            di.name = device_name
            di._class = class_name
            di.server = server_name
            self.db.add_device(di)

        hostname = socket.gethostname()

        if self.server_ctrl_name:
            com = self.server_ctrl_name + " -n " + full_class_name + \
                " --mach=" + hostname + " --add -l 1"
            print "createSelector: ", com
            if os.system(com):
                print "createSelector failed to add the NXSRecSelector" \
                    " to the starter"
                sys.exit(255)

            com = self.server_ctrl_name + " -n " + full_class_name + " -s" \
                + " -t " + hostname
            print "createSelector: ", com
            if os.system(com):
                print "createSelector failed to start the NXSRecSelector"
                sys.exit(255)
        else:
            self.startupServer(class_name, hostname, device_name)

        if self.writer_name or self.cserver_name:
            dp = PyTango.DeviceProxy(device_name)
            if self.writer_name:
                dp.writerDevice = self.writer_name
            if self.writer_name:
                dp.configDevice = self.cserver_name

        return 1
