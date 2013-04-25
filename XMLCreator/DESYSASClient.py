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
## \file simpleScanClient.py
# example of simple client


import sys, os
import time
from datetime import datetime
from pytz import timezone
import pytz


import random

from math import exp

import PyTango 



## the main function    
def main():
    if  len(sys.argv) < 2:
        print "usage: DESYTOMOClient.py  <XMLfile>  <H5file>  <tangoServer>"
        
    else:
        xmlf = sys.argv[1]
        if os.path.exists(xmlf):


            if len(sys.argv) > 2:
                
                fname = sys.argv[2]
                print fname
            else:
                sp = xmlf.split(".")
                print sp
                if sp[-1] == 'xml' :
                    fname = ''.join(sp[0:-1])
                else:
                    fname = xmlf
                fname = fname.strip() + ".h5"
            print "storing in ", fname 
    
            device = "p09/tdw/r228"
            if len(sys.argv)>3:
                device = sys.argv[3]
            
            dpx = PyTango.DeviceProxy(device)
            print " Connected to: ", device
            dpx.Init()
    
            xml = open(xmlf, 'r').read()


            dpx.FileName = fname

            print "opening the H5 file"
            dpx.OpenFile()

            amsterdam = timezone('Europe/Amsterdam')
            fmt = '%Y-%m-%dT%H:%M:%S.%f%z'
            starttime = amsterdam.localize(datetime.now())


            dpx.TheXMLSettings = xml
            theString = '{"data": {'\
                +' "sample_name":"test sample 1",'\
                +' "start_time":"'+  str(starttime.strftime(fmt)) + '"' \
                +'}  }'
                #                +' "start_time":"2012-11-14T14:05:23.2344-0200"' \
  
            dpx.TheJSONRecord =theString 

            print "opening the entry"
            dpx.OpenEntry()

            steps = 24
            for i in range(steps):
                dpx.record('{}')
                time.sleep(0.1)
                



            endtime = amsterdam.localize(datetime.now())

            theString = '{"data": {'\
                +' "end_time":"'+  str(endtime.strftime(fmt)) + '"' \
                +', "counts":"'+  str(steps) + '"' \
                +'}  }'

#                +' "end_time":"2012-11-14T17:15:23.4567-0200" '\
 
            dpx.TheJSONRecord =theString 

# monitor_counter
# sample_rotation
# sample_x_translation
# sample_y_translation
# sample_z_translation


            print "closing the  entry"
            dpx.closeEntry()
            print "closing the H5 file"
            dpx.closeFile()



if __name__ == "__main__":
    main()

            
                
            
            


#  LocalWords:  nicePlot
