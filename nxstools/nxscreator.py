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
## \package nexdatas nexdatas.tools
## \file nxscreator.py
# Command-line tool for creating to the nexdatas configuration server
#

""" Command-line tool for creating to the nexdatas configuration server """

import copy
import os

from xml.dom.minidom import parse
from nxstools import nxsdevicetools
from nxstools.nxsdevicetools import (
    storeDataSource, getDataSourceComponents, storeComponent,
    moduleAttributes, moduleMultiAttributes, motorModules,
    moduleTemplateFiles, generateDeviceNames, getServerTangoHost,
    openServer, findClassName)
from nxstools.nxsxml import (XMLFile, NDSource, NGroup, NField, NLink,
                             NDimensions)

NXSTOOLS_PATH= os.path.dirname(nxsdevicetools.__file__)
PYTANGO = False
try:
    import PyTango
    PYTANGO = True
except:
    pass


class Device(object):
    __slots__ = [
        'name', 'dtype', 'module', 'tdevice', 'hostname', 'sardananame',
        'sardanahostname', 'host', 'port', 'group', 'attribute']

    def __init__(self):
        self.name = None
        self.dtype = None
        self.module = None
        self.tdevice = None
        self.hostname = None
        self.sardananame = None
        self.sardanahostname = None
        self.host = None
        self.port = None
        self.group = None
        self.attribute = None

    def splitHostPort(self):
        if self.hostname:
            self.host = self.hostname.split(":")[0]
            self.port = self.hostname.split(":")[1] \
                if len(self.hostname.split(":")) > 1 else None
        else:
            self.host = None
            self.port = None
            raise Exception("hostname not defined")

    def findAttribute(self, localhost):
        mhost = self.sardanahostname or localhost
        self.group = None
        self.attribute = None
        # if module.lower() in motorModules:
        if self.module in motorModules:
            self.attribute = 'Position'
        elif self.dtype == 'stepping_motor':
            self.attribute = 'Position'
        elif PYTANGO and self.module in moduleAttributes:
            try:
                dp = PyTango.DeviceProxy(str("%s/%s" % (mhost, self.name)))
                mdevice = str(dp.name())

                sarattr = moduleAttributes[self.module][0]
                if not sarattr or \
                   sarattr not in dp.get_attribute_list():
                    raise Exception("Missing attribute: Value")
                self.hostname = mhost
                self.host = mhost.split(":")[0]
                if len(mhost.split(":")) > 1:
                    self.port = mhost.split(":")[1]

                self.tdevice = mdevice
                self.attribute = sarattr
                self.group = '__CLIENT__'
            except Exception:
                if moduleAttributes[self.module][1]:
                    self.attribute = moduleAttributes[self.module][1]
                    self.group = '__CLIENT__'

    def setSardanaName(self, tolower):
        self.name = self.sardananame or self.name
        if tolower:
            self.name = self.name.lower()


## configuration server adapter
class Creator(object):
    ## constructor
    # \param options  command options
    # \param args command arguments
    def __init__(self, options, args, printouts=True):
        self.options = options
        self.args = args
        self.printouts = printouts

    ## creates TANGO datasource file
    # \param name device name
    # \param directory output file directory
    # \param fileprefix file name prefix
    @classmethod
    def createTangoDataSource(
            cls, name, directory, fileprefix, server, device,
            attribute, host, port="10000", group=None):
        df = XMLFile("%s/%s%s.ds.xml" % (directory, fileprefix, name))
        sr = NDSource(df)
        sr.initTango(name, device, "attribute", attribute, host, port,
                     group=group)
        if server:
            xml = df.prettyPrint()
            storeDataSource(name, xml, server)
        else:
            df.dump()


    ## creates CLIENT datasource file
    # \param name device name
    # \param directory output file directory
    # \param fileprefix file name prefix
    @classmethod
    def createClientDataSource(
            cls, name, directory, fileprefix, server, dsname=None):
        dname = name if not dsname else dsname
        df = XMLFile("%s/%s%s.ds.xml" % (directory, fileprefix, dname))
        print "%s/%s%s.ds.xml" % (directory, fileprefix, dname)
        sr = NDSource(df)
        sr.initClient(dname, name)
        if server:
            xml = df.prettyPrint()
            storeDataSource(dname, xml, server)
        else:
            df.dump()

    @classmethod
    def __patheval(cls, nexuspath):
        pathlist = []
        spath = nexuspath.split("/")
        if spath:
            for sp in spath[:-1]:
                nlist = sp.split(":")
                if len(nlist) == 2:
                    if len(nlist[0]) == 0 and \
                       len(nlist[1]) > 2 and nlist[1].startswith("NX"):
                        pathlist.append((nlist[1][2:], nlist[1]))
                    else:
                        pathlist.append((nlist[0], nlist[1]))
                elif len(nlist) == 1 and nlist[0]:
                    if len(nlist[0]) > 2 and nlist[0].startswith("NX"):
                        pathlist.append((nlist[0][2:], nlist[0]))
                    else:
                        pathlist.append((nlist[0], "NX" + nlist[0]))

            pathlist.append((spath[-1], None))
        return pathlist

    @classmethod
    def __createTree(cls, df, nexuspath, name, nexusType,
                     strategy, units, link, chunk):

        pathlist = cls.__patheval(nexuspath)
        entry = None
        parent = df
        for path in pathlist[:-1]:
            child = NGroup(parent, path[0], path[1])
            if parent == df:
                entry = child
            parent = child
        if pathlist:
            fname = pathlist[-1][0] or name
            field = NField(parent, fname, nexusType)
            field.setStrategy(strategy)
            if units.strip():
                field.setUnits(units.strip())
            field.setText("$datasources.%s" % name)
            if chunk != 'SCALAR':
                if chunk == 'SPECTRUM':
                    NDimensions(field, "1")
                elif chunk == 'IMAGE':
                    NDimensions(field, "2")
            if link and entry:
                npath = (nexuspath + name) \
                    if nexuspath[-1] == '/' else nexuspath
                data = NGroup(entry, "data", "NXdata")
                NLink(data, fname, npath)

    ## creates component file
    # \param name datasource name
    # \param directory output file directory
    # \param fileprefix file name prefix
    # \param nexuspath nexus path
    # \param strategy field strategy
    # \param nexusType nexus Type of the field
    # \param units field units
    # \param link nxdata link
    # \param server configuration server
    @classmethod
    def createComponent(cls, name, directory, fileprefix, nexuspath,
                        strategy, nexusType, units, links, server, chunk):
        defpath = '/entry$var.serialno:NXentry/instrument' \
                  + '/collection/%s' % (name)
        df = XMLFile("%s/%s%s.xml" % (directory, fileprefix, name))
        cls.__createTree(df, nexuspath or defpath, name, nexusType,
                         strategy, units, links, chunk)

        if server:
            xml = df.prettyPrint()
            storeComponent(name, xml, server)
        else:
            df.dump()

    ## provides xml content of the node
    # \param node DOM node
    # \returns xml content string
    @classmethod
    def getText(cls, node):
        if not node:
            return
        xml = node.toxml()
        start = xml.find('>')
        end = xml.rfind('<')
        if start == -1 or end < start:
            return ""
        return xml[start + 1:end].replace("&lt;", "<").replace("&gt;", "<"). \
            replace("&quot;", "\"").replace("&amp;", "&")

    @classmethod
    def getChildText(cls, parent, childname):
        return cls.getText(
            parent.getElementsByTagName(childname)[0]) \
            if len(parent.getElementsByTagName(childname)) else None


class WrongParameterError(Exception):
    pass


class ComponentCreator(Creator):

    def create(self):
        aargs = []
        if self.options.device.strip():
            try:
                first = int(self.options.first)
            except:
                raise WrongParameterError(
                    "CollCompCreator Invalid --first parameter\n")

            try:
                last = int(self.options.last)
            except:
                raise WrongParameterError(
                    "CollCompCreator Invalid --last parameter\n")
            aargs = generateDeviceNames(self.options.device, first, last,
                                        self.options.minimal)

        self.args += aargs
        if not len(self.args):
            raise WrongParameterError("")

        for name in self.args:
            if not self.options.database:
                if self.printouts:
                    print("CREATING: %s%s.xml" % (self.options.file, name))
            else:
                if self.printouts:
                    print("STORING: %s" % (name))
            self.createComponent(
                name, self.options.directory,
                self.options.file,
                self.options.nexuspath,
                self.options.strategy,
                self.options.type,
                self.options.units,
                self.options.links,
                self.options.server if self.options.database else None,
                self.options.chunk)


class TangoDSCreator(Creator):

    def create(self):
        dvargs = []
        dsargs = []
        if self.options.device.strip():
            try:
                first = int(self.options.first)
            except:
                raise WrongParameterError(
                    "ClientDSCreator: Invalid --first parameter\n")
            try:
                last = int(self.options.last)
            except:
                raise WrongParameterError(
                    "ClientDSCreator: Invalid --last parameter\n")

            dvargs = generateDeviceNames(self.options.device, first, last)
            dsargs = generateDeviceNames(self.options.datasource, first, last)

        if not dvargs or not len(dvargs):
            raise WrongParameterError("")

        for i in range(len(dvargs)):
            if not self.options.database:
                print "CREATING %s: %s%s.ds.xml" % (
                    dvargs[i], self.options.file, dsargs[i])
            else:
                print "STORING %s: %s" % (dvargs[i], dsargs[i])
            self.createTangoDataSource(
                dsargs[i], self.options.directory, self.options.file,
                self.options.server if self.options.database else None,
                dvargs[i],
                self.options.attribute,
                self.options.host,
                self.options.port)


class ClientDSCreator(Creator):

    def create(self):
        dsargs = None
        aargs = []
        if self.options.device.strip():
            try:
                first = int(self.options.first)
            except:
                raise WrongParameterError(
                    "ClientDSCreator: Invalid --first parameter\n")
            try:
                last = int(self.options.last)
            except:
                raise WrongParameterError(
                    "ClientDSCreator: Invalid --last parameter\n")

            aargs = generateDeviceNames(self.options.device, first, last,
                                        self.options.minimal)
            if self.options.dsource:
                dsaargs = generateDeviceNames(
                    self.options.dsource, first, last)
                dsargs = list(self.args) + dsaargs

        self.args += aargs
        if not dsargs:
            dsargs = self.args
        if not len(self.args):
            raise WrongParameterError("")

        for i in range(len(self.args)):
            if not self.options.database:
                print("CREATING: %s%s.ds.xml" % (self.options.file, dsargs[i]))
            else:
                print("STORING: %s" % (dsargs[i]))
            self.createClientDataSource(
                self.args[i], self.options.directory, self.options.file,
                self.options.server if self.options.database else None,
                dsargs[i])


class DeviceDSCreator(Creator):

    def create(self):
        for at in self.args:
            dsname = "%s%s" % (self.options.datasource.lower(), at.lower())
            if not self.options.database:
                if self.printouts:
                    print("CREATING %s/%s: %s%s.ds.xml" % (
                        self.options.device, at, self.options.file, dsname))
            else:
                if self.printouts:
                    print("STORING %s/%s: %s" % (
                        self.options.device, at, dsname))
            self.createTangoDataSource(
                dsname, self.options.directory, self.options.file,
                self.options.server if self.options.database else None,
                self.options.device, at, self.options.host, self.options.port,
                self.options.datasource if not self.options.nogroup else None)




class OnlineDSCreator(Creator):

    def printAction(self, dv, dscps=None):
        if self.printouts:
            if not self.options.database:
                print("CREATING %s: %s%s.ds.xml" % (
                    dv.tdevice, self.options.file, dv.name))
            else:
                print("STORING %s %s/%s %s" % (
                    dv.name + ":" + " " * (34 - len(dv.name)),
                    dv.hostname,
                    dv.tdevice + " " * (
                        60 - len(dv.tdevice) - len(dv.hostname)),
                    ",".join(dscps[dv.name])
                    if (dscps and dv.name in dscps and dscps[dv.name])
                    else ""))

    def create(self):
        localhost = getServerTangoHost(self.options.server)
        indom = parse(self.args[0])
        hw = indom.getElementsByTagName("hw")
        device = hw[0].firstChild
        try:
            dscps = getDataSourceComponents(self.options.server)
        except Exception:
            dscps = {}

        while device:
            if device.nodeName == 'device':
                dv = Device()
                dv.name = self.getChildText(device, "name")
                dv.dtype = self.getChildText(device, "type")
                dv.module = self.getChildText(device, "module")
                dv.tdevice = self.getChildText(device, "device")
                dv.hostname = self.getChildText(device, "hostname")
                dv.sardananame = self.getChildText(device, "sardananame")
                dv.sardanahostname = self.getChildText(
                    device, "sardanahostname")

                try:
                    dv.splitHostPort()
                except:
                    if self.printouts:
                        print("ERROR %s: host for module %s of %s "
                              "type not defined"
                              % (dv.name, dv.module, dv.dtype))
                    device = device.nextSibling
                    continue
                dv.findAttribute(localhost)
                if dv.attribute:
                    dv.setSardanaName(self.options.lower)
                    self.printAction(dv, dscps)
                    self.createTangoDataSource(
                        dv.name, self.options.directory, self.options.file,
                        self.options.server if self.options.database else None,
                        dv.tdevice, dv.attribute, dv.host, dv.port, dv.group)
                if (dv.module in moduleMultiAttributes.keys()) or (
                        dv.module == 'module_tango'
                        and len(dv.tdevice.split('/')) == 3
                        and dv.tdevice.split('/')[1]
                        in moduleMultiAttributes.keys()):
                    if dv.module == 'module_tango':
                        module = dv.tdevice.split('/')[1]
                    else:
                        module = dv.module
                    multattr = moduleMultiAttributes[module]
                    for at in multattr:
                        dsname = "%s_%s" % (dv.name.lower(), at.lower())
                        self.createTangoDataSource(
                            dsname, self.options.directory, self.options.file,
                            self.options.server if self.options.database
                            else None,
                            dv.tdevice, at, dv.host, dv.port,
                            "%s_" % (dv.name.lower()))
                        mdv = copy.copy(dv)
                        mdv.name = dsname
                        self.printAction(mdv, dscps)
                elif not dv.attribute:
                    if self.printouts:
                        print(
                            "SKIPPING %s:    module %s of %s type not defined"
                            % (dv.name, dv.module, dv.dtype))

            elif device.nodeName == '#comment':
                if self.options.comments:
                    if self.printouts:
                        print("COMMENT:   '%s'" % (device.data.strip()))
            else:
                pass
            device = device.nextSibling

class OnlineCPCreator(Creator):

    def printAction(self, dv, dscps=None):
        if self.printouts:
            if not self.options.database:
                print("CREATING %s: %s%s.ds.xml" % (
                    dv.tdevice, self.options.file, dv.name))
            else:
                print("STORING %s %s/%s %s" % (
                    dv.name + ":" + " " * (34 - len(dv.name)),
                    dv.hostname,
                    dv.tdevice + " " * (
                        60 - len(dv.tdevice) - len(dv.hostname)),
                    ",".join(dscps[dv.name])
                    if (dscps and dv.name in dscps and dscps[dv.name])
                    else ""))

    def getModuleName(self, device):
        if device.module in moduleMultiAttributes.keys():
            return device.module
        elif len(device.tdevice.split('/')) == 3:
            classname = findClassName(device.hostname, device.tdevice)
            if classname.lower() in moduleMultiAttributes.keys():
                return classname.lower()
            if dv.module == 'module_tango' \
               and len(dv.tdevice.split('/')) == 3 \
               and dv.tdevice.split('/')[1] in moduleMultiAttributes.keys():
                return  dv.tdevice.split('/')[1]
        
    def create(self):
        localhost = getServerTangoHost(self.options.server)
        indom = parse(self.args[0])
        hw = indom.getElementsByTagName("hw")
        device = hw[0].firstChild
        cpname =  self.options.component
        server  = self.options.server if self.options.database else None    
        try:
            proxy = openServer(server)
            proxy.Open()
            acps = proxy.availableComponents()
        except:
            raise Exception("Cannot connect to %s" % server)

        if cpname in acps:
            raise Exception("Component '%s' already exists." % cpname)

        while device:
            if device.nodeName == 'device':
                name = self.getChildText(device, "name")
                if name == cpname:
                    dv = Device()
                    dv.name = name
                    dv.dtype = self.getChildText(device, "type")
                    dv.module = self.getChildText(device, "module")
                    dv.tdevice = self.getChildText(device, "device")
                    dv.hostname = self.getChildText(device, "hostname")
                    dv.sardananame = self.getChildText(device, "sardananame")
                    dv.sardanahostname = self.getChildText(
                        device, "sardanahostname")

                    module = self.getModuleName(dv)
                    if module:
                        multattr = moduleMultiAttributes[module]
                        for at in multattr:
                            dsname = "%s_%s" % (dv.name.lower(), at.lower())
                            self.createTangoDataSource(
                                dsname, self.options.directory, self.options.file,
                                server, dv.tdevice, at, dv.host, dv.port,
                                "%s_" % (dv.name.lower()))
                            mdv = copy.copy(dv)
                            mdv.name = dsname
                            self.printAction(mdv)
                        if module in moduleTemplateFiles:
                            xmlfiles = moduleTemplateFiles[module]
                            for xmlfile in xmlfiles:
                                 newname = self.replaceName(xmlfile, cpname)
                                 with open('%s/xmltemplates/%s' % (
                                         NXSTOOLS_PATH, xmlfile), "r") \
                                     as content_file:
                                     xmlcontent = content_file.read()
                                 xml = xmlcontent.replace("$(name)", cpname)
                                 mdv = copy.copy(dv)
                                 mdv.name = newname
                                 if xmlfile.endswith(".ds.xml"):
                                     self.printAction(mdv)
                                     storeDataSource(newname, xml, server)
                                 else:
                                     self.printAction(mdv)
                                     storeComponent(newname, xml, server)

            device = device.nextSibling

    @classmethod
    def replaceName(cls, filename, cpname):
        if filename.endswith(".ds.xml"):
            filename = filename[:-7]
        elif filename.endswith(".xml"):
            filename = filename[:-4]
        sname = filename.split("_")
        sname[0] = cpname
        return "_".join(sname)


if __name__ == "__main__":
    pass
