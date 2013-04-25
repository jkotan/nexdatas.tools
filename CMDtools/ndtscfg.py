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
## \file ndtscfg.py
# Command-line tool for ascess to configuration server
#


import sys
import os
import time

from optparse import OptionParser
import PyTango


## configuration server adapter
class ConfigServer(object):
    ## constructor
    # \param device device name of configuration server
    # \param nonewline no newline flag
    def __init__(self, device, nonewline=False):
        found = False
        cnt = 0
        ## spliting character
        self.__char = " " if nonewline else "\n"
        
        try:
            ## configuration server proxy
            self.cnfServer = PyTango.DeviceProxy(device)
        except Exception, e:
#            sys.stderr.write(str(e))
            found = True
            
        if found:
            sys.stderr.write("Error: Cannot connect into configuration server: %s\n"% device)
            sys.stderr.flush()
            sys.exit(255)

        while not found and cnt < 1000:
            if cnt > 1:
                time.sleep(0.01)
            try:
                if self.cnfServer.state() != PyTango.DevState.RUNNING:
                    found = True
            except Exception,e:
#                sys.stderr.write(str(e))
                time.sleep(0.01)
                found = False
            cnt +=1

        if not found:
            sys.stderr.write("Error: Setting up %s takes to long\n"% device)
            sys.stderr.flush()
            sys.exit(255)

            
        if self.cnfServer.state() != PyTango.DevState.OPEN:
#            self.cnfServer.Init()
            self.cnfServer.Open()

    ## lists the DB item names
    # \param ds flag set True for datasources
    # \param mandatory flag set True for mandatory components        
    def listCmd(self, ds, mandatory=False):
        if ds:
            if not mandatory:
                return self.cnfServer.AvailableDataSources()
        else:
            if mandatory:
                return self.cnfServer.MandatoryComponents()
            else:
                return self.cnfServer.AvailableComponents()
        return []    


    ## shows the DB items
    # \param ds flag set True for datasources
    # \param args list of item names
    # \param mandatory flag set True for mandatory components        
    def showCmd(self, ds, args, mandatory=False):
        if ds:
            dsrc = self.cnfServer.AvailableDataSources()
            for ar in args:
                if ar not in dsrc:
                    sys.stderr.write("Error: DataSource %s not stored in configuration server\n"% ar)
                    sys.stderr.flush()
                    return []
            return self.cnfServer.DataSources(args)
        else:
            cmps = self.cnfServer.AvailableComponents()
            for ar in args:
                if ar not in cmps:
                    sys.stderr.write("Error: Component %s not stored in configuration server\n"% ar)
                    sys.stderr.flush()
                    return []
            if mandatory:
                mand =  list(self.cnfServer.MandatoryComponents())
                mand.extend(args)    
                return self.cnfServer.Components(mand)
            else:
                return self.cnfServer.Components(args)
        return []    


    ## Provides final configuration
    # \param ds flag set True for datasources
    # \param args list of item names
    def getCmd(self, ds, args):
        if ds:
            return ""
        else:
            cmps = self.cnfServer.AvailableComponents()
            for ar in args:
                if ar not in cmps:
                    sys.stderr.write(
                        "Error: Component %s not stored in configuration server\n"% ar)
                    sys.stderr.flush()
                    return ""
            self.cnfServer.CreateConfiguration(args)
            return self.cnfServer.XMLString
        return ""    


    ## perform requested command
    # \param command called command
    # \param ds flag set True for datasources
    # \param args list of item names
    # \param mandatory flag set True for mandatory components        
    def performCommand(self, command, ds, args, mandatory=False):
        if command == 'list':
            return  self.__char.join(self.listCmd(ds, mandatory)) 
        if command == 'show':
            return  self.__char.join(self.showCmd(ds, args, mandatory)) 
        if command == 'get':
            return  self.getCmd(ds, args) 
            
## the main function
def main():
    
    
    ## pipe arguments
    pipe = []
    if not sys.stdin.isatty():
        ## system pipe 
        pipe = sys.stdin.readlines()

    commands = ['list','show','get']
    ## run options
    options = None
    ## usage example
    usage = "usage: %prog <command> -s <config_server> "\
            +" [-d] [-m] [name1] [name2] [name3] ... \n"\
            +" e.g.: %prog list -s p02/xmlconfigserver/exp.01 -d\n\n"\
            + "Commands: \n"\
            + "   list -s <config_server>   \n"\
            + "          list names of available components\n"\
            + "   list -s <config_server> -d  \n"\
            + "          list names of available datasources\n"\
            + "   show -s <config_server>  name1 name2 ...  \n"\
            + "          show components with given names \n"\
            + "   show -s <config_server> -d name1 name2 ...  \n"\
            + "          show datasources with given names \n"\
            + "   get -s <config_server>  name1 name2 ...  \n"\
            + "          get merged configuration of components \n"\
            + " "

    ## option parser
    parser = OptionParser(usage=usage)
    parser.add_option("-s","--server", dest="server", 
                      help="configuration server device name")
    parser.add_option("-d","--datasources",  action="store_true",
                      default=False, dest="datasources", 
                      help="perform operation on datasources")
    parser.add_option("-m","--mandatory",  action="store_true",
                      default=False, dest="mandatory", 
                      help="make use mandatory components as well")
    parser.add_option("-n","--no-newlines",  action="store_true",
                      default=False, dest="nonewlines", 
                      help="split result with spaces")

    (options, args) = parser.parse_args()

    if not args or args[0] not in commands or not options.server :
        parser.print_help()
        print ""
        sys.exit(255)


    ## configuration server     
    cnfserver = ConfigServer(options.server, options.nonewlines)
    
    ## command-line and pipe arguments
    parg = args[1:]
    if pipe:
        parg.extend([p.strip() for p in pipe ])



    ## result to print
    result = cnfserver.performCommand(args[0], options.datasources, 
                                      parg, options.mandatory)
    if result.strip():
        print result



if __name__ == "__main__":
    main()
