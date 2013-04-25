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
# \package  ndtstools tools for ndts
## \file simpleClient2.py
# second example of simple client

import sys, os
import time

import PyTango 

## the main function
def main():
    argc = len(sys.argv)

    if  argc < 4:
        print "usage: simpleClient.py   <XMLfile1>  <XMLfile2>  ...  <XMLfileN>  <H5file>  <device_name e.g. p09/tdw/r228>"
        
    else:
        xmlf = sys.argv[1]
        if os.path.exists(xmlf):
                
            fname = sys.argv[argc-2]
            print fname

            print "storing in ", fname 
    
#            device = "p09/tdw/r228"
            device = sys.argv[argc-1]
            
            dpx = PyTango.DeviceProxy(device)
            dpx.set_timeout_millis(25000)
            
            dpx.Init()

            print " Connected to: ", device


            dpx.FileName = fname

            print "opening the H5 file"
            dpx.OpenFile()


            
            for i in range(1, argc-2):
                xmlf = sys.argv[i]
                
                xml = open(xmlf, 'r').read()

                dpx.TheXMLSettings = xml
                
                print "opening the entry"
                dpx.OpenEntry()
                
                print "recording the H5 file"
                dpx.record('{"data": {"emittance_x": 0.1} }')
                
                print "sleeping for 1s"
                time.sleep(1)
                print "recording the H5 file"
                dpx.record('{"data": {"emittance_x": 0.3} }')
                print "sleeping for 1s"
                time.sleep(1)
                print "recording the H5 file"
                dpx.record('{"data": {"emittance_x": 0.2} }')
                print "closing the  entry"
                dpx.closeEntry()

            print "closing the H5 file"
            dpx.closeFile()



if __name__ == "__main__":
    main()

            
                
            
            

