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
#

""" Set Up NeXus Tango Servers"""

import socket
import PyTango
import os
import sys
import time
import json
import argparse

from nxstools.nxsargparser import (Runner, NXSArgParser, ErrorException)

#: (:obj:`str`) host name
_hostname = socket.gethostname()


#: (:obj:`dict` <:obj:`dict` <:obj:`str` , :obj:`str` > > )
#:    all SardanaHosts and DataBaseHosts should be known
knownHosts = {
    'hasdelay': {'beamline': 'delay', 'masterHost': 'hasdelay',
                 'user': 'delayusr', 'dbname': 'nxsconfig'},
    'hasmfmc': {'beamline': 'fmc', 'masterHost': 'hasmfmc',
                'user': 'delayusr', 'dbname': 'nxsconfig'},
    'hasmlqj': {'beamline': 'lqj', 'masterHost': 'hasmlqj',
                'user': 'lqjuser', 'dbname': 'nxsconfig'},
    'haso111n': {'beamline': 'p09', 'masterHost': 'haso111n',
                 'user': 'tnunez', 'dbname': 'nxsconfig'},
    'haso111tb': {'beamline': 'p09', 'masterHost': 'haso111tb',
                  'user': 'tnunez', 'dbname': 'nxsconfig'},
    'haso113b': {'beamline': 'p09', 'masterHost': 'haso113b',
                 'user': 'blume', 'dbname': 'nxsconfig'},
    'haso113u': {'beamline': 'p09', 'masterHost': 'haso113u',
                 'user': 'kracht', 'dbname': 'nxsconfig'},
    'hastodt': {'beamline': 'p09', 'masterHost': 'hastodt',
                'user': 'kracht', 'dbname': 'nxsconfig'},
    'haso228k': {'beamline': 'p09', 'masterHost': 'haso228k',
                 'user': 'jkotan', 'dbname': 'nxsconfig'},
    'haso224w': {'beamline': 'p02', 'masterHost': 'haso224w',
                 'user': 'wharmby', 'dbname': 'nxsconfig'},
    'haso213p': {'beamline': 'p22', 'masterHost': 'haso213p',
                 'user': 'spiec', 'dbname': 'nxsconfig'},
    'has6117b': {'beamline': 'p02', 'masterHost': 'has6117b',
                 'user': 'p02user', 'dbname': 'nxsconfig'},
    'haspecsicl4': {'beamline': 'p02', 'masterHost': 'haspecsicl4',
                    'user': 'lacluser', 'dbname': 'nxsconfig'},
    'haspp01eh1': {'beamline': 'p01', 'masterHost': 'haspp01eh1',
                   'user': 'p01user', 'dbname': 'nxsconfig'},
    'haspp01eh2': {'beamline': 'p01', 'masterHost': 'haspp01eh2',
                   'user': 'p01user', 'dbname': 'nxsconfig'},
    'haspp01eh3': {'beamline': 'p01', 'masterHost': 'haspp01eh3',
                   'user': 'p01user', 'dbname': 'nxsconfig'},
    'haspp02ch1a': {'beamline': 'p02', 'masterHost': 'haspp02ch1a',
                    'user': 'p02user', 'dbname': 'nxsconfig'},
    'haspp02ch1': {'beamline': 'p02', 'masterHost': 'haspp02ch1',
                   'user': 'p02user', 'dbname': 'nxsconfig'},
    'haspp02ch2': {'beamline': 'p02', 'masterHost': 'haspp02ch2',
                   'user': 'p02user', 'dbname': 'nxsconfig'},
    'haspp03': {'beamline': 'p03', 'masterHost': 'haspp03',
                'user': 'p03user', 'dbname': 'nxsconfig'},
    'haspp03nano': {'beamline': 'p03nano', 'masterHost': 'haspp03nano',
                    'user': 'p03nano', 'dbname': 'nxsconfig'},
    'haspp04exp1': {'beamline': 'p04', 'masterHost': 'haspp04exp1',
                    'user': 'p04user', 'dbname': 'nxsconfig'},
    'haspp04exp2': {'beamline': 'p04', 'masterHost': 'haspp04exp2',
                    'user': 'p04user', 'dbname': 'nxsconfig'},
    'haspp06ctrl': {'beamline': 'p06', 'masterHost': 'haspp06ctrl',
                    'user': 'p06user', 'dbname': 'nxsconfig'},
    'haspp06nc1': {'beamline': 'p06', 'masterHost': 'haspp06nc1',
                   'user': 'p06user', 'dbname': 'nxsconfig'},
    'haspp06mc01': {'beamline': 'p06', 'masterHost': 'haspp06mc01',
                    'user': 'p06user', 'dbname': 'nxsconfig'},
    'hasp029rack': {'beamline': 'p06', 'masterHost': 'hasp029rack',
                    'user': 'p06user', 'dbname': 'nxsconfig'},
    'haspp07eh2': {'beamline': 'p07', 'masterHost': 'haspp07eh2',
                   'user': 'p07user', 'dbname': 'nxsconfig'},
    'haspp08': {'beamline': 'p08', 'masterHost': 'haspp08',
                'user': 'p08user', 'dbname': 'nxsconfig'},
    'haspp09': {'beamline': 'p09', 'masterHost': 'haspp09',
                'user': 'p09user', 'dbname': 'nxsconfig'},
    'haspp09mag': {'beamline': 'p09', 'masterHost': 'haspp09mag',
                   'user': 'p09user', 'dbname': 'nxsconfig'},
    'haspp09dif': {'beamline': 'p09', 'masterHost': 'haspp09dif',
                   'user': 'p09user', 'dbname': 'nxsconfig'},
    'haspp09haxps': {'beamline': 'p09', 'masterHost': 'haspp09maxps',
                     'user': 'p09haxps', 'dbname': 'nxsconfig'},
    'haspp10e1': {'beamline': 'p10', 'masterHost': 'haspp10e1',
                  'user': 'p10user', 'dbname': 'nxsconfig'},
    'haspp10e2': {'beamline': 'p10', 'masterHost': 'haspp10e2',
                  'user': 'p10user', 'dbname': 'nxsconfig'},
    'haspp10lcx': {'beamline': 'p10', 'masterHost': 'haspp10lcx',
                   'user': 'p10user', 'dbname': 'nxsconfig'},
    'haspp10lab': {'beamline': 'p10', 'masterHost': 'haspp10lab',
                   'user': 'p10user', 'dbname': 'nxsconfig'},
    'haspp11oh': {'beamline': 'p11', 'masterHost': 'haspp11oh',
                  'user': 'p11user', 'dbname': 'nxsconfig'},
    'haspp11sardana': {'beamline': 'p11',
                       'masterHost': 'haspp11sardana',
                       'user': 'p11user', 'dbname': 'nxsconfig'},
    'haspp11user02': {'beamline': 'p11', 'masterHost': 'haspp11user02',
                      'user': 'p11user', 'dbname': 'nxsconfig'},
    'haspp21eh3': {'beamline': 'p21', 'masterHost': 'hasep21eh3',
                   'user': 'p21user', 'dbname': 'nxsconfig'},
    'haspp212oh': {'beamline': 'p21', 'masterHost': 'hasep212oh',
                   'user': 'p21user', 'dbname': 'nxsconfig'},
    'haspp21lab': {'beamline': 'p21', 'masterHost': 'haspp21lab',
                   'user': 'p21user', 'dbname': 'nxsconfig'},
    'hasep211eh': {'beamline': 'p211', 'masterHost': 'hasep211eh',
                   'user': 'p211user', 'dbname': 'nxsconfig'},
    'hasep23dev': {'beamline': 'p23', 'masterHost': 'hasep23dev',
                   'user': 'p23user', 'dbname': 'nxsconfig'},
    'hasep23eh': {'beamline': 'p23', 'masterHost': 'hasep23eh',
                  'user': 'p23user', 'dbname': 'nxsconfig'},
    'hasep24': {'beamline': 'p24', 'masterHost': 'hasep24',
                'user': 'p24user', 'dbname': 'nxsconfig'},
    'hasep24eh1': {'beamline': 'p24', 'masterHost': 'hasep24eh1',
                   'user': 'p24user', 'dbname': 'nxsconfig'},
    'haso107klx': {'beamline': 'p09', 'masterHost': 'haso107klx',
                   'user': 'kracht', 'dbname': 'nxsconfig'},
    'haso107d1': {'beamline': 'p09', 'masterHost': 'haso107d1',
                  'user': 'kracht', 'dbname': 'nxsconfig'},
    'hascmexp': {'beamline': 'cmexp', 'masterHost': 'hascmexp',
                 'user': 'cmexp', 'dbname': 'nxsconfig'},
    'hasnp64': {'beamline': 'p64', 'masterHost': 'hasnp64',
                'user': 'p64user', 'dbname': 'nxsconfig'},
    'hasnp64oh': {'beamline': 'p64', 'masterHost': 'hasnp64oh',
                  'user': 'p64user', 'dbname': 'nxsconfig'},
    'hasnp65': {'beamline': 'p65', 'masterHost': 'hasnp65',
                'user': 'p65user', 'dbname': 'nxsconfig'},
    'hasnp66': {'beamline': 'p66', 'masterHost': 'hasnp66',
                'user': 'p66user', 'dbname': 'nxsconfig'},
    'hzgpp07eh1': {'beamline': 'p07', 'masterHost': 'hzgpp07eh1',
                   'user': 'p07user', 'dbname': 'nxsconfig'},
    'hzgpp07eh3': {'beamline': 'p07', 'masterHost': 'hzgpp07eh3',
                   'user': 'p07user', 'dbname': 'nxsconfig'},
    'hzgpp07eh4': {'beamline': 'p07', 'masterHost': 'hzgpp07eh4',
                   'user': 'p07user', 'dbname': 'nxsconfig'},
}


class SetUp(object):

    """ setup NXSDataWriter, NXSConfigServer and NXSRecSelector Tango servers
    """

    def __init__(self):
        """ constructor
        """
        try:
            #: (:class:`PyTango.Database`) tango database server
            self.db = PyTango.Database()
        except:
            print("Can't connect to tango database on %s" %
                  os.getenv('TANGO_HOST'))
            sys.exit(255)

        #: (:obj:`str`) NeXus writer device name
        self.writer_name = None
        #: (:obj:`str`) NeXus config server device name
        self.cserver_name = None

    def changeRecorderPath(self, path):
        """ adds a new recorder path

        :param path: new recorder path
        :type path: :obj:`str`
        :returns: True if record path was added
        :rtype: :obj:`bool`
        """
        res = False
        if not os.path.isdir(path):
            return res
        mss = self.db.get_server_list("MacroServer/*").value_string
        for ms in mss:
            devserv = self.db.get_device_class_list(ms).value_string
            dev = devserv[0::2]
            serv = devserv[1::2]
            for idx, ser in enumerate(serv):
                if ser == 'MacroServer':
                    if dev[idx]:
                        recorderpaths = self.db.get_device_property(
                            dev[idx], "RecorderPath")["RecorderPath"]
                        if recorderpaths:
                            recorderpaths = [p for p in recorderpaths if p]
                        else:
                            recorderpaths = []
                        if path not in recorderpaths:
                            recorderpaths.append(path)
                            self.db.put_device_property(
                                dev[idx],
                                {"RecorderPath": recorderpaths})
                            res = True
        time.sleep(0.2)
        return res

    def changePropertyName(self, server, oldname, newname, sclass=None):
        """ changes property name

        :param server: server name
        :type server: :obj:`str`
        :param oldname: old property name
        :type oldname: :obj:`str`
        :param newname: new property name
        :type newname: :obj:`str`
        :param sclass: server class name
        :type sclass: :obj:`str`
        :returns: True if property name was changed
        :rtype: :obj:`bool`

        """
        sclass = sclass or server
        res = False
        mss = self.db.get_server_list("%s/*" % server).value_string
        for ms in mss:
            devserv = self.db.get_device_class_list(ms).value_string
            dev = devserv[0::2]
            serv = devserv[1::2]
            for idx, ser in enumerate(serv):
                if ser == sclass:
                    if dev[idx]:
                        if not self.db.get_device_property(
                                dev[idx], newname)[newname]:
                            oldprop = self.db.get_device_property(
                                dev[idx], oldname)[oldname]
                            if oldprop:
                                oldprop = [p for p in oldprop if p]
                                self.db.put_device_property(
                                    dev[idx],
                                    {newname: oldprop})
                                self.db.delete_device_property(
                                    dev[idx], oldname)
                                res = True
        time.sleep(0.2)
        return res

    def changePropertyValue(self, server, newname, newvalue, sclass=None):
        """ changes/sets property value

        :param server: server name
        :type server: :obj:`str`
        :param newvalue: new property value
        :type newvalue: :obj:`str`
        :param newname: new property name
        :type newname: :obj:`str`
        :param sclass: server class name
        :type sclass: :obj:`str`
        :returns: True if property name was changed
        :rtype: :obj:`bool`

        """
        if "/" in server:
            sclass = sclass or server.split("/")[0]
            fserver = server
        else:
            sclass = sclass or server
            fserver = "%s/*" % server
        res = False
        value = json.loads(newvalue)
        mss = self.db.get_server_list(fserver).value_string
        for ms in mss:
            devserv = self.db.get_device_class_list(ms).value_string
            dev = devserv[0::2]
            serv = devserv[1::2]
            for idx, ser in enumerate(serv):
                if ser == sclass:
                    if dev[idx]:
                        if value:
                            value = [p for p in value if p]
                            self.db.put_device_property(
                                dev[idx],
                                {newname: value})
                            res = True
        time.sleep(0.2)
        return res

    def restartServer(self, name, host=None, level=None, restart=True):
        """ restarts server

        :param name: server name
        :type name: :obj:`str`
        :param host: server host name
        :type host: :obj:`str`
        :param level: start up level
        :type level: :obj:`int`
        :param restart:  if server should be restarted
        :type restart: :obj:`bool`
        """
        if name:
            if not host:
                host = socket.gethostname()
            admin = self.db.get_device_exported(
                'tango/admin/' + host).value_string
            if admin:
                servers = None
                started = None
                try:
                    adminproxy = PyTango.DeviceProxy(admin[0])
                    servers = adminproxy.read_attribute('Servers')
                    started = adminproxy.command_inout(
                        "DevGetRunningServers", True)
                except:
                    pass
                if servers and hasattr(servers, "value") \
                        and servers.value:
                    for vl in servers.value:
                        svl = vl.split('\t')[0]
                        if name.startswith("NXSRecSelector") \
                                and svl.startswith("NXSRecSelector"):
                            self._changeLevel(svl, 4)
                        if (started and svl in started) or not restart:
                            if '/' in name:
                                cname = svl
                            else:
                                cname = svl.split('/')[0]
                            if cname == name:
                                if level is not None:
                                    self._changeLevel(
                                        svl, level, tohigher=False)
                                if started and svl in started:
                                    adminproxy.DevStop(svl)
                                    sys.stdout.write("Restarting: %s" % svl)
                                else:
                                    sys.stdout.write("Starting: %s" % svl)
                                problems = True
                                counter = 0
                                while problems and counter < 100:
                                    try:
                                        sys.stdout.write('.')
                                        sys.stdout.flush()
                                        adminproxy.DevStart(svl)
                                        problems = False
                                    except:
                                        counter += 1
                                        time.sleep(0.2)
                                counter = 0
                                problems = True
                                while problems and counter < 100:
                                    try:
                                        sys.stdout.write('.')
                                        sys.stdout.flush()
                                        rsvs = adminproxy.RunningServers
                                        if svl in rsvs:
                                            problems = False
                                        else:
                                            time.sleep(0.2)
                                    except:
                                        time.sleep(0.2)
                                    finally:
                                        counter += 1
                                print(" ")
                                if problems:
                                    print("%s was not restarted" % svl)
                                    print("Warning: Process with the server"
                                          "instance could be suspended")

    def stopServer(self, name, host=None):
        """ restarts server

        :param name: server name
        :type name: :obj:`str`
        :param host: server host name
        :type host: :obj:`str`
        """
        if name:
            if not host:
                host = socket.gethostname()
            admin = self.db.get_device_exported(
                'tango/admin/' + host).value_string
            if admin:
                servers = None
                started = None
                try:
                    adminproxy = PyTango.DeviceProxy(admin[0])
                    servers = adminproxy.read_attribute('Servers')
                    started = adminproxy.command_inout(
                        "DevGetRunningServers", True)
                except:
                    pass
                if servers and hasattr(servers, "value") \
                        and servers.value:
                    for vl in servers.value:
                        svl = vl.split('\t')[0]
                        if started and svl in started:
                            if '/' in name:
                                cname = svl
                            else:
                                cname = svl.split('/')[0]
                            if cname == name:
                                if started and svl in started:
                                    adminproxy.DevStop(svl)
                                    sys.stdout.write("Stopping: %s" % svl)
                                problems = True
                                counter = 0
                                while problems and counter < 100:
                                    try:
                                        sys.stdout.write('.')
                                        sys.stdout.flush()
                                        rsvs = adminproxy.RunningServers
                                        if svl not in rsvs:
                                            problems = False
                                        else:
                                            time.sleep(0.2)
                                    except:
                                        time.sleep(0.2)
                                    finally:
                                        counter += 1
                                print(" ")
                                if problems:
                                    print("%s was not stopped" % svl)
                                    print("Warning: Process with the server"
                                          "instance could be suspended")

    def _changeLevel(self, name, level, tohigher=True):
        """ change startup level

        :param name: server name
        :type name: :obj:`str`
        :param level: new startup level
        :type level: :obj:`int`
        :returns: True if level was changed
        :rtype: :obj:`bool`
        """
        sinfo = self.db.get_server_info(name)
        if not tohigher or level > sinfo.level:
            sinfo.level = level
        self.db.put_server_info(sinfo)
        return True

    def _startupServer(self, new, level, host, ctrl, device):
        """ starts the server up

        :param new: new server name
        :type new: :obj:`str`
        :param level: startup level
        :type level: :obj:`int`
        :param host: tango host name
        :type host: :obj:`str`
        :param ctrl: control mode
        :type ctrl: :obj:`str`
        :param device: device name
        :type device: :obj:`str`
        :returns: True if server was started up
        :rtype: :obj:`bool`
        """
        server = self.db.get_server_class_list(new)
        if len(server) == 0:
            sys.stderr.write('Server ' + new.split('/')[0]
                             + ' not defined in database\n')
            return False

        adminproxy = PyTango.DeviceProxy('tango/admin/' + host)
        startdspaths = self.db.get_device_property(
            'tango/admin/' + host,
            "StartDsPath")["StartDsPath"]
        if '/usr/bin' not in startdspaths:
            if startdspaths:
                startdspaths = [p for p in startdspaths if p]
            else:
                startdspaths = []
            startdspaths.append('/usr/bin')
            self.db.put_device_property(
                'tango/admin/' + host, {"StartDsPath": startdspaths})
            adminproxy.Init()

        sinfo = self.db.get_server_info(new)
        sinfo.name = new
        sinfo.host = host
        sinfo.mode = ctrl
        sinfo.level = level
        self.db.put_server_info(sinfo)
        running = adminproxy.DevGetRunningServers(True)
        if new not in running:
            adminproxy.DevStart(new)
        adminproxy.UpdateServersInfo()

        sys.stdout.write("waiting for server")

        found = False
        cnt = 0
        while not found and cnt < 1000:
            try:
                sys.stdout.write(".")
                dp = PyTango.DeviceProxy(device)
                time.sleep(0.01)
                dp.ping()
                found = True
                print(" %s is working" % device)
            except:
                found = False
            cnt += 1
        return found

    def createDataWriter(self, beamline, masterHost):
        """ creates data writer

        :param beamline: beamline name
        :type beamline: :obj:`str`
        :param masterHost: master host of data writer
        :type masterHost: :obj:`str`
        :returns: True if server was created
        :rtype: :obj:`bool`
        """
        if not beamline:
            print("createDataWriter: no beamline given ")
            return False
        if not masterHost:
            print("createDataWriter: no masterHost given ")
            return False

        class_name = 'NXSDataWriter'
        server = class_name
        server_name = server + '/' + masterHost
        full_class_name = 'NXSDataWriter/' + masterHost
        self.writer_name = "%s/nxsdatawriter/%s" % (beamline, masterHost)
        if server_name not in self.db.get_server_list(server_name):
            print("createDataWriter: creating %s" % server_name)

            if server_name in self.db.get_server_list(server_name):
                print("createDataWriter: DB contains already %s" % server_name)
                return False

            di = PyTango.DbDevInfo()
            di.name = self.writer_name
            di._class = class_name
            di.server = server_name

            self.db.add_device(di)
            self.db.put_device_property(self.writer_name,
                                        {'NumberOfThreads': 100})

        elif (self.writer_name not in
              self.db.get_device_class_list(server_name).value_string):
            print("\ncreateDataWriter: %s already exists. "
                  "To change its device name please remove it." % server_name)
            return False

        hostname = socket.gethostname()

        self._startupServer(full_class_name, 1, hostname, 1, self.writer_name)

        return True

    def createConfigServer(self, beamline, masterHost, jsonsettings=None):
        """ creates configuration server

        :param beamline: beamline name
        :type beamline: :obj:`str`
        :param masterHost: master host of data writer
        :type masterHost: :obj:`str`
        :param jsonsettings: connection settings to DB in json
        :type jsonsettings: :obj:`str`
        :returns: True if server was created
        :rtype: :obj:`bool`
        """
        if not beamline:
            print("createConfigServer: no beamline given ")
            return False
        if not masterHost:
            print("createConfigServer: no masterHost given ")
            return False

        class_name = 'NXSConfigServer'
        server = class_name
        server_name = server + '/' + masterHost
        self.cserver_name = "%s/nxsconfigserver/%s" % (beamline, masterHost)
        if server_name not in self.db.get_server_list(server_name):
            print("createConfigServer: creating %s" % server_name)

            if server_name in self.db.get_server_list(server_name):
                print("createConfigServer: DB contains already %s"
                      % server_name)
                return False

            di = PyTango.DbDevInfo()
            di.name = self.cserver_name
            di._class = class_name
            di.server = server_name

            self.db.add_device(di)
            self.db.put_device_property(
                self.cserver_name, {'VersionLabel': '%s@%s' % (
                    beamline.upper(), masterHost.upper())})
        elif (self.cserver_name not in
              self.db.get_device_class_list(server_name).value_string):
            print("\ncreateConfigServer: %s already exists. "
                  "To change its device name please remove it." % server_name)
            return False

        hostname = self.db.get_db_host().split(".")[0]

        self._startupServer(server_name, 1, hostname, 1, self.cserver_name)

        dp = PyTango.DeviceProxy(self.cserver_name)
        if dp.state() != PyTango.DevState.ON:
            dp.Close()
        if jsonsettings:
            dp = PyTango.DeviceProxy(self.cserver_name)
            dp.JSONSettings = jsonsettings
        try:
            dp.Open()
        except:
            try:
                jsettings = json.loads(jsonsettings)
                jsettings['read_default_file'] = \
                    '/var/lib/nxsconfigserver/.my.cnf'
                dp.JSONSettings = str(json.dumps(jsettings))
                dp.Open()
            except:
                try:
                    jsettings['read_default_file'] = \
                        '/var/lib/nxsconfigserver/.my.cnf'
                    dp.JSONSettings = str(json.dumps(jsettings))
                    dp.Open()
                except:
                    print("createConfigServer: "
                          "%s cannot connect the"
                          " database with JSONSettings: \n%s " % (
                              self.cserver_name, jsonsettings))
                    print("try to change the settings")
                    return False

        return True

    def createSelector(self, beamline, masterHost, writer=None, cserver=None):
        """ creates selector server

        :param beamline: beamline name
        :type beamline: :obj:`str`
        :param masterHost: master host of data writer
        :type masterHost: :obj:`str`
        :param writer: writer device name
        :type writer: :obj:`str`
        :param cserver: configuration server device name
        :type cserver: :obj:`str`
        :returns: True if server was created
        :rtype: :obj:`bool`
        """
        if not beamline:
            print("createSelector: no beamline given ")
            return False
        if not masterHost:
            print("createSelector: no masterHost given ")
            return False
        if writer:
            self.writer_name = writer
        if cserver:
            self.cserver_name = cserver

        class_name = 'NXSRecSelector'
        server = class_name
        server_name = server + '/' + masterHost
        full_class_name = 'NXSRecSelector/' + masterHost
        device_name = "%s/nxsrecselector/%s" % (beamline, masterHost)
        if server_name not in self.db.get_server_list(server_name):
            print("createSelector: creating %s" % server_name)

            if server_name in self.db.get_server_list(server_name):
                print("createSelector: DB contains already %s" % server_name)
                return False

            di = PyTango.DbDevInfo()
            di.name = device_name
            di._class = class_name
            di.server = server_name
            self.db.add_device(di)

        elif (device_name not in
              self.db.get_device_class_list(server_name).value_string):
            print("\ncreateSelector: %s already exists. "
                  "To change its device name please remove it." % server_name)
            return False

        hostname = socket.gethostname()

        self._startupServer(full_class_name, 4, hostname, 1, device_name)

        if self.writer_name or self.cserver_name:
            dp = PyTango.DeviceProxy(device_name)
            if self.cserver_name:
                dp.configDevice = self.cserver_name
            if self.writer_name:
                dp.writerDevice = self.writer_name

        return True


class Set(Runner):

    """ set runner"""

    #: (:obj:`str`) command description
    description = "set up NXSConfigServer NXSDataWriter " \
                  + "and NXSRecSelector servers"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxsetup set\n" \
        + "       nxsetup set -b p09 -m haso228 -u p09user " \
        + "-d nxsconfig NXSConfigServer\n" \
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            "-b", "--beamline", action="store",
            dest="beamline", help="name of the beamline"
            " ( default: 'nxs' )")
        parser.add_argument(
            "-m", "--masterHost", action="store",
            dest="masterHost", help="the host that stores the Mg"
            " ( default: <localhost> )")
        parser.add_argument(
            "-u", "--user", action="store",
            dest="user", help="the local user"
            " ( default: 'tango' )")
        parser.add_argument(
            "-d", "--database", action="store",
            dest="dbname", help="the database name"
            "  ( default: 'nxsconfig')")
        parser.add_argument(
            "-j", "--csjson", action="store",
            dest="csjson",
            help="JSONSettings for the configuration server. "
            "( default: '{\"host\": \"localhost\",\"db\": <DBNAME>,"
            " \"use_unicode\": true',"
            " \"read_default_file\": <MY_CNF_FILE>}'"
            "  where <MY_CNF_FILE> stays for"
            " \"/home/<USER>/.my.cnf\""
            " or \"/var/lib/nxsconfigserver/.my.cnf\" )")
        parser.add_argument(
            'args', metavar='server_name',
            type=str, nargs='*',
            help='server names, e.g.: NXSRecSelector NXSDataWriter/TDW1')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        local_user = None
        args = options.args or []
        if os.path.isfile('/home/etc/local_user'):
            local_user = open('/home/etc/local_user').readline()
        elif _hostname in knownHosts.keys():
            local_user = knownHosts["user"]

        if options.beamline is None:
            if _hostname in knownHosts.keys():
                options.beamline = knownHosts[_hostname]['beamline']
            else:
                options.beamline = 'nxs'

        if options.masterHost is None:
            if _hostname in knownHosts.keys():
                options.masterHost = knownHosts[_hostname]['masterHost']
            else:
                options.masterHost = _hostname

        if options.user is None:
            if local_user:
                options.user = local_user
            else:
                options.user = 'tango'

        if options.dbname is None:
            if _hostname in knownHosts.keys():
                options.dbname = knownHosts[_hostname]['dbname']
            else:
                options.dbname = 'nxsconfig'

        print("\noptions are set to:  -b %s -m %s -u %s -d %s \n" % (
            options.beamline,
            options.masterHost,
            options.user,
            options.dbname,
        ))

        setUp = SetUp()

        if not args or "NXSDataWriter" in args:
            if not setUp.createDataWriter(
                    beamline=options.beamline,
                    masterHost=options.masterHost):
                print("startup failed to create the nexus data writer")
                sys.exit(255)

        if options.csjson:
            jsonsettings = options.csjson
        else:
            jsonsettings = '{"host":"localhost","db":"%s",' % options.dbname \
                + ' "read_default_file":"/home/%s/.my.cnf",' % options.user \
                + ' "use_unicode":true}'

        if not args or "NXSConfigServer" in args:
            if not setUp.createConfigServer(
                    beamline=options.beamline,
                    masterHost=options.masterHost,
                    jsonsettings=jsonsettings):
                print("startup failed to create the nexus config server")
                sys.exit(255)

        if not args or "NXSRecSelector" in args:
            if not setUp.createSelector(
                    beamline=options.beamline,
                    masterHost=options.masterHost):
                print("startup failed to create the nexus selector server")
                sys.exit(255)


class Start(Runner):

    """ start runner"""

    #: (:obj:`str`) command description
    description = "start tango server"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxsetup start Pool/haso228 -l 2\n" \
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            "-l", "--level", action="store", type=int, default=-1,
            dest="level", help="startup level")
        parser.add_argument(
            'args', metavar='server_name',
            type=str, nargs='*',
            help='server names, e.g.: NXSRecSelector NXSDataWriter/TDW1')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        args = options.args or []
        setUp = SetUp()
        servers = args if args else [
            "NXSConfigServer", "NXSRecSelector", "NXSDataWriter"]
        for server in servers:
            setUp.restartServer(
                server,
                level=(options.level if options.level > -1 else None),
                restart=False)


class MoveProp(Runner):

    """ move-prop runner"""

    #: (:obj:`str`) command description
    description = "change property name"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxsetup move-prop -n DefaultPreselectedComponents" \
        + " -o DefaultAutomaticComponents NXSRecSelector\n" \
        + "       nxsetup move-prop -t -n DefaultPreselectedComponents " \
        + " -o DefaultAutomaticComponents NXSRecSelector\n" \
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            "-n", "--newname", action="store",
            dest="newname", help="(new) property name")
        parser.add_argument(
            "-o", "--oldname", action="store",
            dest="oldname", help="old property name")
        parser.add_argument(
            "-t", "--postpone", action="store_true",
            default=False, dest="postpone",
            help="do not restart the server")
        parser.add_argument(
            'args', metavar='server_name',
            type=str, nargs='*',
            help='server names, e.g.: NXSRecSelector NXSDataWriter/TDW1')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        parser = self._parser
        args = options.args or []
        if not options.newname or not options.oldname or not args:
            parser.print_help()
            sys.exit(255)
        servers = args or []
        setUp = SetUp()
        for server in servers:
            if setUp.changePropertyName(
                    server, options.oldname, options.newname):
                if not options.postpone:
                    setUp.restartServer(server)


class ChangeProp(Runner):

    """ change-prop runner"""

    #: (:obj:`str`) command description
    description = "change property value"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxsetup change-prop -n ClientRecordKeys -t -w " \
        + "\"[\\\"phoibos_scan_command\\\",\\\"phoibos_scan_comment\\\"]\" " \
        + "NXSRecSelector/r228\n" \
        + "       nxsetup change-prop -n DefaultPreselectedComponents -w " \
        + "\"[\\\"pinhole1\\\",\\\"slit2\\\"]\" NXSRecSelector/r228\n" \
        + "       nxsetup change-prop -n StartDsPath -w " \
        + "\"[\\\"/usr/bin\\\",\\\"/usr/lib/tango\\\"]\" Starter\n" \
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            "-n", "--newname", action="store",
            dest="newname", help="(new) property name")
        parser.add_argument(
            "-w", "--propvalue", action="store",
            dest="propvalue", help="new property value")
        parser.add_argument(
            "-t", "--postpone", action="store_true",
            default=False, dest="postpone",
            help="do not restart the server")
        parser.add_argument(
            'args', metavar='server_name',
            type=str, nargs='*',
            help='server names, e.g.: NXSRecSelector NXSDataWriter/TDW1')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        parser = self._parser
        args = options.args or []
        if not options.newname or not options.propvalue or not args:
            parser.print_help()
            sys.exit(255)
        servers = args or []
        setUp = SetUp()
        for server in servers:
            if setUp.changePropertyValue(
                    server, options.newname, options.propvalue):
                if not options.postpone:
                    setUp.restartServer(server)


class AddRecorderPath(Runner):

    """ add-recorder-path runner"""

    #: (:obj:`str`) command description
    description = "add-recorder-path into MacroServer(s) property"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxsetup add-recorder-path "\
        + "/usr/share/pyshared/sardananxsrecorder\n" \
        + "       nxsetup add-recorder-path -t "\
        + "/usr/share/pyshared/sardananxsrecorder\n" \
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            "-t", "--postpone", action="store_true",
            default=False, dest="postpone",
            help="do not restart the server")

    def postauto(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            'recpath', metavar='recorder_path',
            type=str, nargs=1,
            help='sardana recorder path')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        setUp = SetUp()
        if setUp.changeRecorderPath(options.recpath[0]):
            if not options.postpone:
                setUp.restartServer("MacroServer")


class Restart(Runner):

    """ restart runner"""

    #: (:obj:`str`) command description
    description = "restart tango server"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxsetup restart Pool/haso228 -l 2\n" \
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            "-l", "--level", action="store", type=int, default=-1,
            dest="level", help="startup level")
        parser.add_argument(
            'args', metavar='server_name',
            type=str, nargs='*',
            help='server names, e.g.: NXSRecSelector NXSDataWriter/TDW1')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        args = options.args or []
        setUp = SetUp()
        servers = args if args else [
            "NXSConfigServer", "NXSRecSelector", "NXSDataWriter"]
        for server in servers:
            setUp.restartServer(
                server, level=(options.level if options.level > -1 else None))


class Stop(Runner):

    """ Stop runner"""

    #: (:obj:`str`) command description
    description = "stop tango server"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxsetup stop Pool/haso228 \n" \
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            'args', metavar='server_name',
            type=str, nargs='*',
            help='server names, e.g.: NXSRecSelector NXSDataWriter/TDW1')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        args = options.args or []
        setUp = SetUp()
        servers = args if args else [
            "NXSConfigServer", "NXSRecSelector", "NXSDataWriter"]
        for server in servers:
            setUp.stopServer(server)


def _supportoldcommands():
    """ replace the old command names to the new ones
    """

    oldnew = {
        '-x': 'set',
        '--execute': 'set',
        '-r': 'restart',
        '--restart': 'restart',
        '-s': 'start',
        '--start': 'start',
        '-p': 'move-prop',
        '--move-prop': 'move-prop',
        '-c': 'change-prop',
        '--change-prop': 'change-prop',
        '-a': 'add-recorder-path',
        '--add-recorder-path': 'add-recorder-path',
    }

    if sys.argv and len(sys.argv) > 1:
        if sys.argv[1] in oldnew.keys():
            sys.argv[1] = oldnew[sys.argv[1]]


def main():
    """ the main program function
    """
    description = "Command-line tool for setting up  NeXus Tango Servers"

    _supportoldcommands()

    epilog = 'For more help:\n  nxscreate <sub-command> -h'
    if _hostname in knownHosts.keys():
        local_user = None
        if os.path.isfile('/home/etc/local_user'):
            local_user = open('/home/etc/local_user').readline()
        elif _hostname in knownHosts.keys():
            local_user = knownHosts["user"]
        epilog += "\n\n  (%s is known: -b %s -m %s -u %s -d %s )" % (
            _hostname,
            knownHosts[_hostname]['beamline'],
            knownHosts[_hostname]['masterHost'],
            local_user,
            knownHosts[_hostname]['dbname']
        )

    parser = NXSArgParser(
        description=description, epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.cmdrunners = [
        ('set', Set),
        ('restart', Restart),
        ('start', Start),
        ('stop', Stop),
        ('move-prop', MoveProp),
        ('change-prop', ChangeProp),
        ('add-recorder-path', AddRecorderPath),
    ]
    runners = parser.createSubParsers()

    try:
        options = parser.parse_args()
    except ErrorException as e:
        sys.stderr.write("Error: %s\n" % str(e))
        sys.stderr.flush()
        parser.print_help()
        print("")
        sys.exit(255)

    runners[options.subparser].run(options)


if __name__ == "__main__":
    main()
