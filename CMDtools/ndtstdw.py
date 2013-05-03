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
## \package tools nexdatas.configserver
## \file ndtstdw.py
# Command-line tool for ascess to configuration server
#


import sys
import os
import time

from optparse import OptionParser
import PyTango


## configuration server adapter
class NexusServer(object):
    ## constructor
    # \param device device name of configuration server
    def __init__(self, device):
        found = False
        cnt = 0

        try:
            ## configuration server proxy
            self.tdwServer = PyTango.DeviceProxy(device)
        except Exception, e:
#            sys.stderr.write(str(e))
            found = True
            
        if found:
            sys.stderr.write("Error: Cannot connect into configuration server: %s\n"% device)
            sys.stderr.flush()
            sys.exit(0)

        while not found and cnt < 1000:
            if cnt > 1:
                time.sleep(0.01)
            try:
                if self.tdwServer.state() != PyTango.DevState.RUNNING:
                    found = True
            except Exception,e:
#                sys.stderr.write(str(e))
                time.sleep(0.01)
                found = False
            cnt +=1

        if not found:
            sys.stderr.write("Error: Setting up %s takes to long\n"% device)
            sys.stderr.flush()
            sys.exit(0)

            
    ## opens the h5 file
    # \param filename h5 file name        
    def openFile(self, filename):
        self.tdwServer.Init()
        self.tdwServer.FileName = str(filename)
        self.tdwServer.OpenFile()


    ## sets the global JSON data
    # \param jsondata global JSON data
    def setData(self, jsondata):
        self.tdwServer.TheJSONRecord = str(jsondata)

    ## opens an entry
    # \param xmlconfig xml configuration string
    def openEntry(self, xmlconfig):
        self.tdwServer.TheXMLSettings = str(xmlconfig)
        self.tdwServer.OpenEntry()

    ## records one step
    # \param jsondata step JSON data
    def record(self, jsondata):
        self.tdwServer.Record(jsondata)


    ## closes the entry
    def closeEntry(self):
        self.tdwServer.CloseEntry()

    ## closes the file
    def closeFile(self):
        self.tdwServer.CloseFile()
        



    ## perform requested command
    # \param command called command
    # \param args list of item names
    def performCommand(self, command, args):
#    commands = ['openfile','openentry','setdata','record','closeentry','closefile'] 
       if command == 'openfile':
            return self.openFile(args[0]) 
       if command == 'setdata':
            return self.setData(args[0].strip()) 
       if command == 'openentry':
            return self.openEntry(args[0].strip()) 
       if command == 'record':
            return self.record(args[0].strip()) 
       if command == 'closefile':
            return self.closeFile() 
       if command == 'closeentry':
            return self.closeEntry() 


           
## provides TangoDataServer device names
# \returns list of the TangoDataServer device names
def getServers():
    try:
        db=PyTango.Database()
    except:
        sys.stderr.write(
            "Error: Cannot connect into the tango database on host: \n    %s \n "% os.environ['TANGO_HOST'])
        sys.stderr.flush()
        return ""
    servers = db.get_device_exported_for_class("TangoDataServer").value_string
    return servers

## provides TangoDataServer device name if only one or error in the other case
# \returns TangoDataServer device name or empty string if error appears
def checkServer():
    servers = getServers()
    if not servers:
        sys.stderr.write(
            "Error: No TangoDataServer on current host running. \n\n"
            +"    Please specify the server from the other host. \n\n")
        sys.stderr.flush()
        return ""
    if len(servers) > 1:
        sys.stderr.write(
            "Error: More than on TangoDataServer on current host running. \n\n"
            +"    Please specify the server:\n        %s\n\n"% "\n        ".join(servers))
        sys.stderr.flush()
        return ""
    return servers[0]


            
## the main function
def main():
    
    
    ## pipe arguments
    pipe = ""
    if not sys.stdin.isatty():
        pp = sys.stdin.readlines()
        ## system pipe 
        pipe = "".join(pp)
        

    commands = {'openfile':1,'openentry':0,'setdata':1,'record':1,'closeentry':0,'closefile':0}
#    commands = ['openfile','openentry','setdata','record','closeentry','closefile']
    ## run options
    options = None
    ## usage example
    usage = "usage: %prog <command> [-s <nexus_server>] "\
            +" [<arg1> [<arg2>  ...]] \n"\
            +" e.g.: %prog openfile -s p02/tangodataserver/exp.01  $HOME/myfile.h5 \n\n"\
            + "Commands: \n"\
            + "   openfile [-s <nexus_server>]  <file_name> \n"\
            + "          open new H5 file\n"\
            + "   setdata [-s <nexus_server>] <json_data_string>  \n"\
            + "          assign global JSON data\n"\
            + "   openentry [-s <nexus_server>] <xml_config>  \n"\
            + "          create new entry\n"\
            + "   record [-s <nexus_server>]  <json_data_string>  \n"\
            + "          record one step with step JSON data \n"\
            + "   closeentry [-s <nexus_server>]   \n"\
            + "          close the current entry \n"\
            + "   closefile [-s <nexus_server>]  \n"\
            + "          close the current file \n"\
            + "   servers [-s <nexus_server/host>] \n"\
            + "          get lists of tango data servers from the current tango host\n"\
            + " "

    ## option parser
    parser = OptionParser(usage=usage)
    parser.add_option("-s","--server", dest="server", 
                      help="configuration server device name")

    (options, args) = parser.parse_args()

#    print "ARGs", args

    if args and args[0] == 'servers':
        server = None
        if options.server and options.server.strip():
            server  = options.server.split("/")[0]
        if server: 
            server = server.strip()
        if server: 
            if not ":" in server:
                server = server +":10000"
            localtango = os.environ['TANGO_HOST']
            os.environ['TANGO_HOST'] = server
            
        print "\n".join(getServers())
        if server:
            os.environ['TANGO_HOST'] = localtango 
        return

    if not options.server:
        options.server = checkServer()

    if not args or args[0] not in commands or not options.server :
        parser.print_help()
        print ""
        sys.exit(0)


    ## configuration server     
    tdwserver = NexusServer(options.server)
    
    ## command-line and pipe arguments
    parg = args[1:]
    if pipe:
        parg.append(pipe)

#    for r in parg:     
#        print "##" , r    
    if len(parg) < commands[args[0]]:
        print "CMD", args[0], len(parg)
        parser.print_help()
        print ""
        sys.exit(0)

    ## result to print
    result = tdwserver.performCommand(args[0], parg)
    if result and str(result).strip():
        print result



if __name__ == "__main__":
    main()
