#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2016 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
from optparse import OptionParser


#: host name
hostname = socket.gethostname()


#: all SardanaHosts and DataBaseHosts should be known
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
                 'user': 'blume', 'dbname': 'nxsconfig'},
    'hastodt': {'beamline': 'p09', 'masterHost': 'hastodt',
                'user': 'kracht', 'dbname': 'nxsconfig'},
    'haso228k': {'beamline': 'p09', 'masterHost': 'haso228k',
                 'user': 'jkotan', 'dbname': 'nxsconfig'},
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
    'haspp11sardana': {'beamline': 'p11', 'masterHost': 'haspp11sardana',
                       'user': 'p11user', 'dbname': 'nxsconfig'},
    'haspp11user02': {'beamline': 'p11', 'masterHost': 'haspp11user02',
                      'user': 'p11user', 'dbname': 'nxsconfig'},
    'haspp21lab': {'beamline': 'p21', 'masterHost': 'haspp21lab',
                   'user': 'p21user', 'dbname': 'nxsconfig'},
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
    """ setup nxs servers
    """

    def __init__(self):
        """ constructor
        """
        try:
            self.db = PyTango.Database()
        except:
            print("Can't connect to tango database on %s" %
                  os.getenv('TANGO_HOST'))
            sys.exit(255)

        self.writer_name = None
        self.cserver_name = None
        self._psub = None

    def changeRecorderPath(self, path):
        """ adds a new recorder path

        :param path: new recorder path
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
        :param oldname: old property name
        :param newname: new property name
        :param scalss: server class name

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

    def restartServer(self, name, host=None):
        """ restarts server

        :param name: server name
        :param host: server host name
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
                            if '/' in name:
                                self.changeLevel(name, 4)
                            else:
                                self.changeLevel(svl, 4)
                        if started and svl in started:
                            if '/' in name:
                                cname = svl
                            else:
                                cname = svl.split('/')[0]
                            if cname == name:
                                adminproxy.DevStop(svl)
                                problems = True
                                sys.stdout.write("Restarting: %s" % svl)
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
                                print(" ")
                                if problems:
                                    print("%s was not restarted" % svl)
                                    print("Warning: Process with the server"
                                          "instance could be suspended")

    def changeLevel(self, name, level):
        """ change startup level

        :param name: server name
        :param level: new startup level
        """
        sinfo = self.db.get_server_info(name)
        if level > sinfo.level:
            sinfo.level = level
        self.db.put_server_info(sinfo)
        return True

    def startupServer(self, new, level, host, ctrl, device):
        """ starts the server up

        :param new: new server name
        :param level: startup level
        :param host: tango host name
        :param ctrl: control mode
        :param device: device name
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
                print("%s is working" % device)
            except:
                found = False
            cnt += 1
        return found

    def createDataWriter(self, beamline, masterHost):
        """ creates data writer

        :param beamline: beamline name
        :param materHost: master host of data writer
        """
        if not beamline:
            print("createDataWriter: no beamline given ")
            return 0
        if not masterHost:
            print("createDataWriter: no masterHost given ")
            return 0

        class_name = 'NXSDataWriter'
        server = class_name
        server_name = server + '/' + masterHost
        full_class_name = 'NXSDataWriter/' + masterHost
        self.writer_name = "%s/nxsdatawriter/%s" % (beamline, masterHost)
        if server_name not in self.db.get_server_list(server_name):
            print("createDataWriter: creating %s" % server_name)

            if server_name in self.db.get_server_list(server_name):
                print("createDataWriter: DB contains already %s" % server_name)
                return 0

            di = PyTango.DbDevInfo()
            di.name = self.writer_name
            di._class = class_name
            di.server = server_name

            self.db.add_device(di)
            self.db.put_device_property(self.writer_name,
                                        {'NumberOfThreads': 100})

        hostname = socket.gethostname()

        self.startupServer(full_class_name, 1, hostname, 1, self.writer_name)

        return 1

    def createConfigServer(self, beamline, masterHost, jsonsettings=None):
        """ creates configuration server

        :param beamline: beamline name
        :param materHost: master host of data writer
        :param jsonsettings: connection settings to DB in json
        """
        if not beamline:
            print("createConfigServer: no beamline given ")
            return 0
        if not masterHost:
            print("createConfigServer: no masterHost given ")
            return 0

        class_name = 'NXSConfigServer'
        server = class_name
        server_name = server + '/' + masterHost
        self.cserver_name = "%s/nxsconfigserver/%s" % (beamline, masterHost)
        if server_name not in self.db.get_server_list(server_name):
            print("createConfigServer: creating %s" % server_name)

            if server_name in self.db.get_server_list(server_name):
                print("createConfigServer: DB contains already %s"
                      % server_name)
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

        self.startupServer(server_name, 1, hostname, 1, self.cserver_name)

        dp = PyTango.DeviceProxy(self.cserver_name)
        if dp.state() != PyTango.DevState.ON:
            dp.Close()
        if jsonsettings:
            dp = PyTango.DeviceProxy(self.cserver_name)
            dp.JSONSettings = jsonsettings
        try:
            dp.Open()
        except:
            print("createConfigServer: "
                  "%s cannot connect the"
                  " database with JSONSettings: \n%s " % (
                      self.cserver_name, jsonsettings))
            print("try to change the settings")
            return 0

        return 1

    def createSelector(self, beamline, masterHost, writer=None, cserver=None):
        """ creates selector server

        :param beamline: beamline name
        :param materHost: master host of data writer
        :param writer: writer device name
        :param cserver: configuration server device name
        """
        if not beamline:
            print("createSelector: no beamline given ")
            return 0
        if not masterHost:
            print("createSelector: no masterHost given ")
            return 0
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
                return 0

            di = PyTango.DbDevInfo()
            di.name = device_name
            di._class = class_name
            di.server = server_name
            self.db.add_device(di)

        hostname = socket.gethostname()

        self.startupServer(full_class_name, 4, hostname, 1, device_name)

        if self.writer_name or self.cserver_name:
            dp = PyTango.DeviceProxy(device_name)
            if self.writer_name:
                dp.writerDevice = self.writer_name
            if self.writer_name:
                dp.configDevice = self.cserver_name

        return 1


def createParser(user):
    """ creates parser

    :param user: user name
    """
    if hostname in knownHosts.keys():
        usage = "\n\n %prog -x [-j <jsonsettings>]" + \
                " [<server_class1> <server_class2> ... ] " + \
                "\n\n %prog -r [<server_class1> <server_class2> ... ] " + \
                "\n\n %prog -p -n newname -o oldname " + \
                "[<server_class1> <server_class2> ... ] " + \
                "\n\n  (%s is known, -b %s, -m %s -u %s -d %s ) \n" % (
                    hostname,
                    knownHosts[hostname]['beamline'],
                    knownHosts[hostname]['masterHost'],
                    user,
                    knownHosts[hostname]['dbname'],
                )
    else:
        usage = "\n\n %prog -x -b <beamline> -m <masterHost> " + \
                "-u <local_user> -d <dbname> [-j jsonsettings] " + \
                " [<server_class1> <server_class2> ... ] " + \
                "\n\n %prog -r [<server_class1> <server_class2> ... ] "
    parser = OptionParser(usage=usage)
    parser.add_option("-b", "--beamline", action="store", type="string",
                      dest="beamline", help="name of the beamline")
    parser.add_option("-m", "--masterHost", action="store", type="string",
                      dest="masterHost", help="the host that stores the Mg")
    parser.add_option("-u", "--user", action="store", type="string",
                      dest="user", help="the local user")
    parser.add_option("-d", "--database", action="store", type="string",
                      dest="dbname", help="the database name")
    parser.add_option("-j", "--csjson", action="store", type="string",
                      dest="csjson",
                      help="JSONSettings for the configuration server")
    parser.add_option("-x", "--execute", action="store_true",
                      default=False, dest="execute",
                      help="setup servers action")
    parser.add_option("-o", "--oldname", action="store", type="string",
                      dest="oldname", help="old property name")
    parser.add_option("-n", "--newname", action="store", type="string",
                      dest="newname", help="new property name")
    parser.add_option("-r", "--restart", action="store_true",
                      default=False, dest="restart",
                      help="restart server(s) action")
    parser.add_option("-a", "--add-recorder-path", action="store",
                      type="string", dest="recpath",
                      help="add recorder path")
    parser.add_option("-p", "--move-prop", action="store_true",
                      default=False, dest="moveprop",
                      help="change property name")
    return parser


def main():
    """ the main function
    """
    local_user = None
    if os.path.isfile('/home/etc/local_user'):
        local_user = open('/home/etc/local_user').readline()
    elif hostname in knownHosts.keys():
        local_user = knownHosts["user"]

    parser = createParser(local_user)
    (options, args) = parser.parse_args()

    if not options.execute and not options.restart and not options.recpath \
       and not options.moveprop:
        parser.print_help()
        print("\n")
        sys.exit(255)

    if options.execute:
        if options.beamline is None:
            if hostname in knownHosts.keys():
                options.beamline = knownHosts[hostname]['beamline']
            else:
                parser.print_help()
                print("\n")
                sys.exit(255)
        if options.masterHost is None:
            if hostname in knownHosts.keys():
                options.masterHost = knownHosts[hostname]['masterHost']
            else:
                parser.print_help()
                sys.exit(255)

        if options.user is None:
            if hostname in knownHosts.keys():
                options.user = local_user
            else:
                parser.print_help()
                sys.exit(255)

        if options.dbname is None:
            if hostname in knownHosts.keys():
                options.dbname = knownHosts[hostname]['dbname']
            else:
                parser.print_help()
                sys.exit(255)

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

    if options.restart:
        setUp = SetUp()
        servers = args if args else [
            "NXSConfigServer", "NXSRecSelector", "NXSDataWriter"]
        for server in servers:
            setUp.restartServer(server)

    if options.recpath:
        setUp = SetUp()
        if setUp.changeRecorderPath(options.recpath):
            setUp.restartServer("MacroServer")

    if options.moveprop:
        if not options.newname or not options.oldname or not args:
            parser.print_help()
            sys.exit(255)
        servers = args or []
        setUp = SetUp()
        for server in servers:
            if setUp.changePropertyName(
                    server, options.oldname, options.newname):
                setUp.restartServer(server)


if __name__ == "__main__":
    main()
