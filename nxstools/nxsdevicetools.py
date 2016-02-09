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
## \package nxstools tools for nxswriter
## \file nxsdevicetools.py
# datasource creator

""" NDTS TANGO device tools """

import sys
import os
import time


PYTANGO = False
try:
    import PyTango
    PYTANGO = True
except:
    pass

## attributes of device modules to acquire with elements:
#  'module': [<sardana_pool_attr>, <original_tango_attr>]
moduleAttributes = {
    'counter_tango': ['Value', 'Counts'],
    'dgg2': ['Value', 'SampleTime'],
    'mca_8701': ['Value', 'Data'],
    'mca_sis3302new': ['Value', 'Data'],
    'mca_sis3302': ['Value', 'Data'],
    'mythenroi': ['Value', None],
    'sis3302': ['Value', 'Data'],
    'sis3302roi': ['Value', None],
    'sis3610': ['Value', 'Value'],
    'sis3820': ['Value', 'Counts'],
    'tangoattributectctrl': ['Value', 'Counts'],
    'tip551': ['Value', 'Voltage'],
    'tip830': ['Value', 'Counts'],
    'vfcadc': ['Value', 'Counts'],
    'xmcd': ['Value', None],
}

motorModules = [
    'absbox', 'analyzerep01', 'tth', 'atto300', 'oms58', 'phaseretarder',
    'hexa', 'e6c', 'motor_tango'
    'lom', 'tm', 'cube', 'pie710', 'pie712', 'piezonv40', 'smaractmcs',
    'slt', 'bscryotempcontrolp01', 'omsvme58', 'am', 'vm', 'spk',
    'dcm_energy', 'elom', 'diffracmu', 'kohzu', 'tcpipmotor',
    'galil_dmc', 'pico8742', 'oxfcryo700ctrl', 'analyzer', 'nfpaxis',
    'smarpod', 'smchydra', 'mult', 'tip551', 'dcm_motor'
]

CTModules = [
    'random', 'mca8715roi', 'onedroi', 'sis3820', 'sis3302roi',
    'xmcd', 'vc', 'vfcadc', 'mythenroi', 'mhzdaqp01', 'petra', 'dgg2',
    'tangoattributectctrl'
]

ZeroDModules = ['tip830']

OneDModules = ['xia', 'sis3302', 'mca8701']

TwoDModules = ['lcxcamera', 'pco', 'marccd', 'limaccd', 'eigerpsi',
               'eigerdectris', 'perkinelmer', 'pilatus', 'lambda']

IORegModules = ['sis3610in', 'sis3610out']

for mn in motorModules:
    moduleAttributes[mn] = ['Position', 'Position']

for nm in CTModules + ZeroDModules + OneDModules:
    if nm not in moduleAttributes:
        moduleAttributes[nm] = ['Value', None]


## generates device names
# \param prefix device name prefix5
# \param first first device index
# \param last last device index
# \returns device names
def generateDeviceNames(prefix, first, last, minimal=False):
    names = []
    if prefix.strip():
        for i in range(first, last + 1):
            if not minimal:
                names.append(prefix + ("0" if len(str(i)) == 1 else "")
                             + str(i))
            else:
                names.append(prefix + str(i))
    return names


## provides a list of device attributes
# \param device tango device name
# \param host device host
# \param port device port
# \returns list of device attributes
def getAttributes(device, host=None, port=10000):
    if host:
        dp = PyTango.DeviceProxy("%s:%s/%s" % (host, port, device))
    else:
        dp = PyTango.DeviceProxy(device)
    attr = dp.attribute_list_query()
    return [at.name for at in attr if at.name not in ['State', 'Status']]


## opens connection to the configuration server
# \param configuration server device
# \returns configuration server proxy
def openServer(device):
    found = False
    cnt = 0
    ## spliting character
    try:
        ## configuration server proxy
        cnfServer = PyTango.DeviceProxy(device)
    except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
        found = True

    if found:
        sys.stderr.write(
            "Error: Cannot connect into the server: %s\n" % device)
        sys.stderr.flush()
        sys.exit(0)

    while not found and cnt < 1000:
        if cnt > 1:
            time.sleep(0.01)
        try:
            if cnfServer.state() != PyTango.DevState.RUNNING:
                found = True
        except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
            time.sleep(0.01)
            found = False
        cnt += 1

    if not found:
        sys.stderr.write("Error: Setting up %s takes to long\n" % device)
        sys.stderr.flush()
        sys.exit(0)

    return cnfServer


## stores datasources
# \param name datasource name
# \param xml datasource xml string
# \param server configuration server
def storeDataSource(name, xml, server):
    proxy = openServer(server)
    proxy.Open()
    proxy.XMLString = str(xml)
    proxy.StoreDataSource(str(name))


## gets datasource components
# \param server configuration server
# \returns dictionary with datasource components
def getDataSourceComponents(server):
    dscps = {}
    proxy = openServer(server)
    proxy.Open()
    acps = proxy.availableComponents()
    for cp in acps:
        try:
            dss = proxy.componentDataSources(cp)
            for ds in dss:
                if ds not in dscps:
                    dscps[ds] = []
                dscps[ds].append(cp)
        except Exception as e:
            sys.stderr.write(str(e))
            sys.stderr.write(
                "Error: Internal error of the %s component\n" % cp)
            sys.stderr.flush()
    return dscps


## stores components
# \param name component name
# \param xml component xml string
# \param server configuration server
def storeComponent(name, xml, server):
    proxy = openServer(server)
    proxy.Open()
    proxy.XMLString = str(xml)
    proxy.StoreComponent(str(name))


## provides server device names
# \param name server instance name
# \returns list of the server device names
def getServers(name='NXSConfigServer'):
    try:
        db = PyTango.Database()
    except:
        sys.stderr.write(
            "Error: Cannot connect into %s" % name
            + "on host: \n    %s \n " % os.environ['TANGO_HOST'])
        sys.stderr.flush()
        return ""

    servers = db.get_device_exported_for_class(name).value_string
    return servers


## prints server names
# \param name server instance name
def listServers(server, name='NXSConfigServer'):
    lserver = None
    if server and server.strip():
        lserver = server.split("/")[0]
    if lserver:
        lserver = lserver.strip()
    if lserver:
        if ":" not in lserver:
            lserver = lserver + ":10000"
        localtango = os.environ.get('TANGO_HOST')
        os.environ['TANGO_HOST'] = lserver

    lst = getServers(name)
    if lserver and localtango is not None:
        os.environ['TANGO_HOST'] = localtango
    return lst


## provides server device name if only one or error in the other case
# \returns server device name or empty string if error appears
def checkServer(name='NXSConfigServer'):
    servers = getServers(name)
    if not servers:
        sys.stderr.write(
            "Error: No required server on current host running. \n\n"
            + "    Please specify the server from the other host. \n\n")
        sys.stderr.flush()
        return ""
    if len(servers) > 1:
        sys.stderr.write(
            "Error: More than on %s " % name
            + "on the current host running. \n\n"
            + "    Please specify the server:"
            + "\n        %s\n\n" % "\n        ".join(servers))
        sys.stderr.flush()
        return ""
    return servers[0]


if __name__ == "__main__":
    pass
