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

NXSTOOLS_PATH = os.path.dirname(nxsdevicetools.__file__)
PYTANGO = False
try:
    import PyTango
    PYTANGO = True
except:
    pass


class CPExistsException(Exception):
    """ Component already exists exception
    """
    pass


class Device(object):
    """ device from online.xml
    """
    __slots__ = [
        'name', 'dtype', 'module', 'tdevice', 'hostname', 'sardananame',
        'sardanahostname', 'host', 'port', 'group', 'attribute']

    def __init__(self):
        #: device name
        self.name = None
        #: data type
        self.dtype = None
        #: device module
        self.module = None
        #: device type
        self.tdevice = None
        #: host name with port
        self.hostname = None
        #: sardana name with port
        self.sardananame = None
        #: sardana host name
        self.sardanahostname = None
        #: host without port
        self.host = None
        #: tango port
        self.port = None
        #: datasource tango group
        self.group = None
        #: attribute name
        self.attribute = None

    def splitHostPort(self):
        """ spilts host name from port
        """
        if self.hostname:
            self.host = self.hostname.split(":")[0]
            self.port = self.hostname.split(":")[1] \
                if len(self.hostname.split(":")) > 1 else None
        else:
            self.host = None
            self.port = None
            raise Exception("hostname not defined")

    def findAttribute(self, tangohost):
        """ sets attribute and datasource group of online.xml device

        :param tangohost: tango host
        """
        mhost = self.sardanahostname or tangohost
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
        """ sets sardana name

        :param tolower: If True name in lowercase
        """
        self.name = self.sardananame or self.name
        if tolower:
            self.name = self.name.lower()


class Creator(object):
    """ configuration server adapter
    """

    def __init__(self, options, args, printouts=True):
        """ constructor

        :param options:  command options
        :param args: command arguments
        :param printouts: if printout is enable
        """
        #: creator options
        self._options = options
        #: creator arguments
        self._args = args
        #: if printout is enable
        self._printouts = printouts

    @classmethod
    def _createTangoDataSource(
            cls, name, directory, fileprefix, server, device,
            attribute, host, port="10000", group=None):
        """ creates TANGO datasource file

        :param name: device name
        :param directory: output file directory
        :param fileprefix: file name prefix
        :param server: server name
        :param device: device name
        :param attribute: attribute name
        :param host: tango host name
        :param port: tango port
        :parma group: datasource tango group
        :returns: xml string
        """
        df = XMLFile("%s/%s%s.ds.xml" % (directory, fileprefix, name))
        sr = NDSource(df)
        sr.initTango(name, device, "attribute", attribute, host, port,
                     group=group)
        xml = df.prettyPrint()
        if server:
            storeDataSource(name, xml, server)
        elif directory is not None and fileprefix is not None:
            df.dump()
        return xml

    @classmethod
    def _createClientDataSource(
            cls, name, directory, fileprefix, server, dsname=None):
        """ creates CLIENT datasource file

        :param name: device name
        :param directory: output file directory
        :param fileprefix: file name prefix
        :param server: server name
        :param dsname: datasource name
        :returns: xml string
        """
        dname = name if not dsname else dsname
        df = XMLFile("%s/%s%s.ds.xml" % (directory, fileprefix, dname))
        print "%s/%s%s.ds.xml" % (directory, fileprefix, dname)
        sr = NDSource(df)
        sr.initClient(dname, name)
        xml = df.prettyPrint()
        if server:
            storeDataSource(dname, xml, server)
        elif directory is not None and fileprefix is not None:
            df.dump()
        return xml

    @classmethod
    def __patheval(cls, nexuspath):
        """ splits nexus path into list

        :param nexuspath: nexus path
        :returns: nexus path in lists of (name, NXtype)
        """
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
        """ create nexus node tree

        :param df: definition parent node
        :param nexuspath: nexus path
        :param name: name
        :param nexusType: nexus type
        :param strategy: strategy mode
        :param units: field units
        :param links: if create link
        :param chunk: chunk size
        """

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
                if link > 1:
                    NLink(data, name, npath)
                else:
                    NLink(data, fname, npath)

    @classmethod
    def _createComponent(cls, name, directory, fileprefix, nexuspath,
                         strategy, nexusType, units, links, server, chunk):
        """ creates component file

        :param name: datasource name
        :param directory: output file directory
        :param fileprefix: file name prefix
        :param nexuspath: nexus path
        :param strategy: field strategy
        :param nexusType: nexus Type of the field
        :param units: field units
        :param link: nxdata link
        :param server: configuration server
        :returns: component xml
        """
        defpath = '/entry$var.serialno:NXentry/instrument' \
                  + '/collection/%s' % (name)
        df = XMLFile("%s/%s%s.xml" % (directory, fileprefix, name))
        cls.__createTree(df, nexuspath or defpath, name, nexusType,
                         strategy, units, links, chunk)

        xml = df.prettyPrint()
        if server:
            storeComponent(name, xml, server)
        elif directory is not None and fileprefix is not None:
            df.dump()
        return xml

    @classmethod
    def _getText(cls, node):
        """ provides xml content of the node

        :param node: DOM node
        :returns: xml content string
        """
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
    def _getChildText(cls, parent, childname):
        """ provides text of child named by childname

        :param parent: parent node
        :param childname: child name
        :returns: text string
        """
        return cls._getText(
            parent.getElementsByTagName(childname)[0]) \
            if len(parent.getElementsByTagName(childname)) else None


class WrongParameterError(Exception):
    """ wrong parameter exception
    """
    pass


class ComponentCreator(Creator):
    """ component creator
    """

    def create(self):
        """ creates a component xml and stores it in DB or filesytem
        """
        aargs = []
        if self._options.device.strip():
            try:
                first = int(self._options.first)
            except:
                raise WrongParameterError(
                    "CollCompCreator Invalid --first parameter\n")

            try:
                last = int(self._options.last)
            except:
                raise WrongParameterError(
                    "CollCompCreator Invalid --last parameter\n")
            aargs = generateDeviceNames(self._options.device, first, last,
                                        self._options.minimal)

        self._args += aargs
        if not len(self._args):
            raise WrongParameterError("")

        for name in self._args:
            if not self._options.database:
                if self._printouts:
                    print("CREATING: %s%s.xml" % (self._options.file, name))
            else:
                if self._printouts:
                    print("STORING: %s" % (name))
            self._createComponent(
                name, self._options.directory,
                self._options.file,
                self._options.nexuspath,
                self._options.strategy,
                self._options.type,
                self._options.units,
                int(self._options.fieldlinks) + 2 * int(
                    self._options.sourcelinks),
                self._options.server if self._options.database else None,
                self._options.chunk)


class TangoDSCreator(Creator):
    """ tango datasource creator
    """

    def create(self):
        """ creates a tango datasource xml and stores it in DB or filesytem
        """
        dvargs = []
        dsargs = []
        if self._options.device.strip():
            try:
                first = int(self._options.first)
            except:
                raise WrongParameterError(
                    "ClientDSCreator: Invalid --first parameter\n")
            try:
                last = int(self._options.last)
            except:
                raise WrongParameterError(
                    "ClientDSCreator: Invalid --last parameter\n")

            dvargs = generateDeviceNames(self._options.device, first, last)
            dsargs = generateDeviceNames(self._options.datasource, first, last)

        if not dvargs or not len(dvargs):
            raise WrongParameterError("")

        for i in range(len(dvargs)):
            if not self._options.database:
                print "CREATING %s: %s%s.ds.xml" % (
                    dvargs[i], self._options.file, dsargs[i])
            else:
                print "STORING %s: %s" % (dvargs[i], dsargs[i])
            self._createTangoDataSource(
                dsargs[i], self._options.directory, self._options.file,
                self._options.server if self._options.database else None,
                dvargs[i],
                self._options.attribute,
                self._options.host,
                self._options.port)


class ClientDSCreator(Creator):
    """ client datasource creator
    """

    def create(self):
        """ creates a client datasource xml and stores it in DB or filesytem
        """
        dsargs = None
        aargs = []
        if self._options.device.strip():
            try:
                first = int(self._options.first)
            except:
                raise WrongParameterError(
                    "ClientDSCreator: Invalid --first parameter\n")
            try:
                last = int(self._options.last)
            except:
                raise WrongParameterError(
                    "ClientDSCreator: Invalid --last parameter\n")

            aargs = generateDeviceNames(self._options.device, first, last,
                                        self._options.minimal)
            if self._options.dsource:
                dsaargs = generateDeviceNames(
                    self._options.dsource, first, last)
                dsargs = list(self._args) + dsaargs

        self._args += aargs
        if not dsargs:
            dsargs = self._args
        if not len(self._args):
            raise WrongParameterError("")

        for i in range(len(self._args)):
            if not self._options.database:
                print("CREATING: %s%s.ds.xml" % (
                    self._options.file, dsargs[i]))
            else:
                print("STORING: %s" % (dsargs[i]))
            self._createClientDataSource(
                self._args[i], self._options.directory,
                self._options.file,
                self._options.server if self._options.database else None,
                dsargs[i])


class DeviceDSCreator(Creator):
    """ device datasource creator
    """

    def create(self):
        """ creates a tango datasources xml of given device
            and stores it in DB or filesytem
        """
        for at in self._args:
            dsname = "%s%s" % (self._options.datasource.lower(), at.lower())
            if not self._options.database:
                if self._printouts:
                    print("CREATING %s/%s: %s%s.ds.xml" % (
                        self._options.device, at, self._options.file, dsname))
            else:
                if self._printouts:
                    print("STORING %s/%s: %s" % (
                        self._options.device, at, dsname))
            self._createTangoDataSource(
                dsname, self._options.directory, self._options.file,
                self._options.server if self._options.database else None,
                self._options.device, at, self._options.host,
                self._options.port,
                self._options.datasource
                if not self._options.nogroup else None)


class OnlineDSCreator(Creator):
    """ datasource creator of all online.xml simple devices
    """

    def __init__(self, options, args, printouts=True):
        """ constructor

        :param options:  command options
        :param args: command arguments
        :param printouts: if printout is enable
        """
        Creator.__init__(self, options, args, printouts)
        #: datasource xml dictionary
        self.datasources = {}

    def _printAction(self, dv, dscps=None):
        """ prints out information about the performed action

        :param dv: online device object
        :param dscps: datasource components
        """
        if self._printouts:
            if hasattr(self._options, "directory") and \
               self._options.directory:
                print("CREATING %s: %s/%s%s.ds.xml" % (
                    dv.tdevice, self._options.directory,
                    self._options.file, dv.name))
            else:
                print("CREATING %s %s/%s %s" % (
                    dv.name + ":" + " " * (34 - len(dv.name)),
                    dv.hostname,
                    dv.tdevice + " " * (
                        60 - len(dv.tdevice) - len(dv.hostname)),
                    ",".join(dscps[dv.name])
                    if (dscps and dv.name in dscps and dscps[dv.name])
                    else ""))

    def create(self):
        """ creates datasources of all online.xml simple devices
        """
        self.createXMLs()
        server = self._options.server
        if not hasattr(self._options, "directory") or \
           not self._options.directory:
            for dsname, dsxml in self.datasources.items():
                storeDataSource(dsname, dsxml, server)
        else:
            for dsname, dsxml in self.datasources.items():
                myfile = open("%s/%s%s.ds.xml" % (
                    self._options.directory,
                    self._options.file, dsname), "w")
                myfile.write(dsxml)
                myfile.close()

    def createXMLs(self):
        """ creates datasource xmls of all online.xml simple devices
        """
        self.datasources = {}
        tangohost = getServerTangoHost(self._options.server)
        indom = parse(self._args[0])
        hw = indom.getElementsByTagName("hw")
        device = hw[0].firstChild
        dscps = {}
        if self._printouts and not hasattr(self._options, "directory") or \
           not self._options.directory:
            try:
                dscps = getDataSourceComponents(self._options.server)
            except Exception:
                dscps = {}

        while device:
            if device.nodeName == 'device':
                dv = Device()
                dv.name = self._getChildText(device, "name")
                dv.dtype = self._getChildText(device, "type")
                dv.module = self._getChildText(device, "module")
                dv.tdevice = self._getChildText(device, "device")
                dv.hostname = self._getChildText(device, "hostname")
                dv.sardananame = self._getChildText(device, "sardananame")
                dv.sardanahostname = self._getChildText(
                    device, "sardanahostname")
                try:
                    dv.splitHostPort()
                except:
                    if self._printouts:
                        print("ERROR %s: host for module %s of %s "
                              "type not defined"
                              % (dv.name, dv.module, dv.dtype))
                    device = device.nextSibling
                    continue
                dv.findAttribute(tangohost)
                if dv.attribute:
                    dv.setSardanaName(self._options.lower)
                    self._printAction(dv, dscps)
                    xml = self._createTangoDataSource(
                        dv.name, None, None, None,
                        dv.tdevice, dv.attribute, dv.host, dv.port, dv.group)
                    self.datasources[dv.name] = xml
                if (dv.module in moduleMultiAttributes.keys()) or (
                        dv.module == 'module_tango'
                        and len(dv.tdevice.split('/')) == 3
                        and dv.tdevice.split('/')[1]
                        in moduleMultiAttributes.keys()):
                    if dv.module == 'module_tango':
                        module = dv.tdevice.split('/')[1]
                    else:
                        module = dv.module
                    multattr = moduleMultiAttributes[module.lower()]
                    for at in multattr:
                        dsname = "%s_%s" % (dv.name.lower(), at.lower())
                        xml = self._createTangoDataSource(
                            dsname, None, None, None,
                            dv.tdevice, at, dv.host, dv.port,
                            "%s_" % (dv.name.lower()))
                        self.datasources[dsname] = xml
                        mdv = copy.copy(dv)
                        mdv.name = dsname
                        self._printAction(mdv, dscps)
                elif not dv.attribute:
                    if self._printouts:
                        print(
                            "SKIPPING %s:    module %s of %s type not defined"
                            % (dv.name, dv.module, dv.dtype))
            device = device.nextSibling


class OnlineCPCreator(Creator):
    """ component creator of all online.xml complex devices
    """

    def __init__(self, options, args, printouts=True):
        """ constructor

        :param options: command options
        :param args: command arguments
        :param printouts: if printout is enable
        """
        Creator.__init__(self, options, args, printouts)
        #: datasource xml dictionary
        self.datasources = {}
        #: component xml dictionary
        self.components = {}

    def _printAction(self, dv, dscps=None):
        """ prints out information about the performed action

        :param dv: online device object
        :param dscps: datasource components
        """
        if self._printouts:
            if hasattr(self._options, "directory") and \
               self._options.directory:
                print("CREATING %s: %s/%s%s.ds.xml" % (
                    dv.tdevice, self._options.directory, self._options.file,
                    dv.name))
            else:
                print("CREATING %s %s/%s %s" % (
                    dv.name + ":" + " " * (34 - len(dv.name)),
                    dv.hostname,
                    dv.tdevice + " " * (
                        60 - len(dv.tdevice) - len(dv.hostname)),
                    ",".join(dscps[dv.name])
                    if (dscps and dv.name in dscps and dscps[dv.name])
                    else ""))

    @classmethod
    def _getModuleName(cls, device):
        """ provides module name

        :param device: device name
        :returns: module name
        """
        if device.module.lower() in moduleMultiAttributes.keys():
            return device.module.lower()
        elif len(device.tdevice.split('/')) == 3:
            try:
                classname = findClassName(device.hostname, device.tdevice)
                if classname.lower() in moduleMultiAttributes.keys():
                    return classname.lower()
                if device.module.lower() == 'module_tango' \
                   and len(device.tdevice.split('/')) == 3 \
                   and device.tdevice.split('/')[1] \
                   in moduleMultiAttributes.keys():
                    return device.tdevice.split('/')[1].lower()
            except:
                return

    def listcomponents(self):
        """ provides a list of components with xml templates

        :returns: list of components with xml templates
        """
        indom = parse(self._args[0])
        hw = indom.getElementsByTagName("hw")
        device = hw[0].firstChild
        cpnames = set()

        while device:
            if device.nodeName == 'device':
                name = self._getChildText(device, "name")
                if self._options.lower:
                    name = name.lower()
                dv = Device()
                dv.name = name
                dv.dtype = self._getChildText(device, "type")
                dv.module = self._getChildText(device, "module")
                dv.tdevice = self._getChildText(device, "device")
                dv.hostname = self._getChildText(device, "hostname")
                dv.sardananame = self._getChildText(device, "sardananame")
                dv.sardanahostname = self._getChildText(
                    device, "sardanahostname")

                module = self._getModuleName(dv)
                if module:
                    if module.lower() in moduleTemplateFiles:
                        cpnames.add(dv.name)
            device = device.nextSibling
        return cpnames

    def create(self):
        """ creates components of all online.xml complex devices
        """
        cpname = self._options.component
        if not hasattr(self._options, "directory") or \
           not self._options.directory:
            server = self._options.server
            if not self._options.overwrite:
                try:
                    proxy = openServer(server)
                    proxy.Open()
                    acps = proxy.availableComponents()
                except:
                    raise Exception("Cannot connect to %s" % server)

                if cpname in acps or (
                        self._options.lower and cpname.lower() in acps):
                    raise CPExistsException(
                        "Component '%s' already exists." % cpname)

        self.createXMLs()
        server = self._options.server
        if not hasattr(self._options, "directory") or \
           not self._options.directory:
            for dsname, dsxml in self.datasources.items():
                storeDataSource(dsname, dsxml, server)
            for cpname, cpxml in self.components.items():
                storeComponent(cpname, cpxml, server)
        else:
            for dsname, dsxml in self.datasources.items():
                myfile = open("%s/%s%s.ds.xml" % (
                    self._options.directory,
                    self._options.file, dsname), "w")
                myfile.write(dsxml)
                myfile.close()
            for cpname, cpxml in self.components.items():
                myfile = open("%s/%s%s.xml" % (
                    self._options.directory,
                    self._options.file, cpname), "w")
                myfile.write(cpxml)
                myfile.close()

    def createXMLs(self):
        """ creates component xmls of all online.xml complex devices
        """
        self.datasources = {}
        self.components = {}
        indom = parse(self._args[0])
        hw = indom.getElementsByTagName("hw")
        device = hw[0].firstChild
        cpname = self._options.component

        while device:
            if device.nodeName == 'device':
                name = self._getChildText(device, "name")
                if self._options.lower:
                    name = name.lower()
                    cpname = cpname.lower()
                if name == cpname:
                    dv = Device()
                    dv.name = name
                    dv.dtype = self._getChildText(device, "type")
                    dv.module = self._getChildText(device, "module")
                    dv.tdevice = self._getChildText(device, "device")
                    dv.hostname = self._getChildText(device, "hostname")
                    dv.sardananame = self._getChildText(device, "sardananame")
                    dv.sardanahostname = self._getChildText(
                        device, "sardanahostname")

                    try:
                        dv.splitHostPort()
                    except:
                        if self._printouts:
                            print("ERROR %s: host for module %s of %s "
                                  "type not defined"
                                  % (dv.name, dv.module, dv.dtype))
                        device = device.nextSibling
                        continue
                    module = self._getModuleName(dv)
                    if module:
                        multattr = moduleMultiAttributes[module.lower()]
                        for at in multattr:
                            dsname = "%s_%s" % (dv.name.lower(), at.lower())
                            xml = self._createTangoDataSource(
                                dsname, None, None, None,
                                dv.tdevice, at, dv.host, dv.port,
                                "%s_" % (dv.name.lower()))
                            self.datasources[dsname] = xml
                            mdv = copy.copy(dv)
                            mdv.name = dsname
                            self._printAction(mdv)
                        if module.lower() in moduleTemplateFiles:
                            xmlfiles = moduleTemplateFiles[module.lower()]
                            for xmlfile in xmlfiles:
                                newname = self._replaceName(xmlfile, cpname)
                                with open(
                                        '%s/xmltemplates/%s' % (
                                            NXSTOOLS_PATH, xmlfile), "r"
                                ) as content_file:
                                    xmlcontent = content_file.read()
                                xml = xmlcontent.replace("$(name)", cpname)
                                mdv = copy.copy(dv)
                                mdv.name = newname
                                self._printAction(mdv)
                                if xmlfile.endswith(".ds.xml"):
                                    self.datasources[newname] = xml
                                else:
                                    self.components[newname] = xml

            device = device.nextSibling

    @classmethod
    def _replaceName(cls, filename, cpname):
        """ replaces name prefix of xml templates files

        :param filename: template filename
        :param cpname: output prefix
        :returns: output filename
        """
        if filename.endswith(".ds.xml"):
            filename = filename[:-7]
        elif filename.endswith(".xml"):
            filename = filename[:-4]
        sname = filename.split("_")
        sname[0] = cpname
        return "_".join(sname)


if __name__ == "__main__":
    pass
