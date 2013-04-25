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

import random

from math import exp

import PyTango 


## creates spectrum plot with random Gaussians
# \param xlen data length 
# \param number of Gaussians  
# \returns list with the plot
def nicePlot(xlen=2048, nrGauss=5):
    pr = [ [ random.uniform(0.01,0.001), random.uniform(0,xlen), random.uniform(0.0,1.) ] \
               for i in range(nrGauss) ]
    return [ sum([pr[j][2]*exp(-pr[j][0]*(i-pr[j][1])**2) for j in range(len(pr)) ]) \
                 for i in range(xlen)]

## the main function    
def main():
    if  len(sys.argv) < 2:
        print "usage: simpleClient.py  <XMLfile>  <H5file>  <tangoServer>"
        
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

            dpx.TheXMLSettings = xml
            dpx.TheJSONRecord = '{"datasources":{"MCLIENT":"ndts.DataSources.ClientSource"}}'

            print "opening the entry"
            dpx.OpenEntry()

            print "recording the H5 file" 
            mca = str(nicePlot(2048, 10))

            dpx.record('{"data": {"exp_c01":0.1, "exp_c02":1.1, "p09/mca/exp.02":'\
                           + mca+ '  } }')
            
            print "sleeping for 1s"
            time.sleep(1)
            print "recording the H5 file"
            mca = str(nicePlot(2048, 4))

            dpx.record('{"data": {"exp_c01":0.2, "exp_c02":1.3, "p09/mca/exp.02":'\
                           + mca+ '  } }')

            print "sleeping for 1s"
            time.sleep(1)
            print "recording the H5 file"

            mca = str(nicePlot(2048, 20))
            dpx.record('{"data": {"exp_c01":0.3, "exp_c02":1.4, "p09/mca/exp.02":'\
                           + mca+ '  } }')

            print "closing the  entry"
            dpx.closeEntry()
            print "closing the H5 file"
            dpx.closeFile()



if __name__ == "__main__":
    main()

            
                
            
            


#  LocalWords:  nicePlot
