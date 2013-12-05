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
## \package ndtstools tools for ndts
## \file nxsdevicetools.py
# datasource creator

""" NDTS TANGO device tools """

import sys
import os
import time

from nxstools.nxsxml import XMLFile, NDSource

from optparse import OptionParser

PYTANGO = False
try:
    import PyTango
    PYTANGO = True
except:
    pass


## generates device names
# \param prefix device name prefix
# \param first first device index
# \param last last device index
# \returns device names
def generateDeviceNames(prefix, first, last):
    names = []
    if prefix.strip():
        for i in range (first, last+1):
            names.append(prefix + ("0" if len(str(i)) == 1 else "" ) 
                            + str(i))
    return names


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
    except (PyTango.DevFailed, PyTango.Except,  PyTango.DevError):
        found = True
            
    if found:
        sys.stderr.write(
            "Error: Cannot connect into the configuration server: %s\n"% device)
        sys.stderr.flush()
        sys.exit(0)

    while not found and cnt < 1000:
        if cnt > 1:
            time.sleep(0.01)
        try:
            if cnfServer.state() != PyTango.DevState.RUNNING:
                found = True
        except (PyTango.DevFailed, PyTango.Except,  PyTango.DevError):
            time.sleep(0.01)
            found = False
        cnt += 1
        
    if not found:
        sys.stderr.write("Error: Setting up %s takes to long\n"% device)
        sys.stderr.flush()
        sys.exit(0)

            
    cnfServer.Open()
    return cnfServer    



## stores datasources
# \param name datasource name
# \param xml datasource xml string
# \param server configuration server
def storeDataSource(name, xml, server):
    proxy = openServer(server)
    proxy.XMLString = str(xml)
    proxy.StoreDataSource(str(name))
    

## stores components
# \param name component name
# \param xml component xml string
# \param server configuration server
def storeComponent(name, xml, server):
    proxy = openServer(server)
    proxy.XMLString = str(xml)
    proxy.StoreComponent(str(name))

           
## provides XMLConfigServer device names
# \returns list of the XMLConfigServer device names
def getServers():
    try:
        db = PyTango.Database()
    except:
        sys.stderr.write(
            "Error: Cannot connect into the tango database " \
                + "on host: \n    %s \n "% os.environ['TANGO_HOST'])
        sys.stderr.flush()
        return ""
        
    servers = db.get_device_exported_for_class("XMLConfigServer").value_string
    return servers


## provides XMLConfigServer device name if only one or error in the other case
# \returns XMLConfigServer device name or empty string if error appears
def checkServer():
    servers = getServers()
    if not servers:
        sys.stderr.write(
            "Error: No XMLConfigServer on current host running. \n\n"
            +"    Please specify the server from the other host. \n\n")
        sys.stderr.flush()
        return ""
    if len(servers) > 1:
        sys.stderr.write(
            "Error: More than on XMLConfigServer " \
                + "on the current host running. \n\n" \
                + "    Please specify the server:" \
                + "\n        %s\n\n"% "\n        ".join(servers))
        sys.stderr.flush()
        return ""
    return servers[0]






if __name__ == "__main__":
    pass
