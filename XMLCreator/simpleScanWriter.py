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
## \file simpleScanWriter.py
# example of simple writer


import sys, os
import time

import random

from math import exp

from ndts import TangoDataWriter as TDW



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


    # Create a TDW object
    ## instance of TangoDataWriter
    tdw = TDW.TangoDataWriter("test.h5")

    tdw.numThreads = 1

    ## xml file name
#    xmlf = "../XMLExamples/test.xml"
    xmlf = "../XMLExamples/MNI.xml"

    print "usage: TangoDataWriter.py  <XMLfile1>  <XMLfile2>  ...  <XMLfileN>  <H5file>"

    ## No arguments
    argc = len(sys.argv)
    if argc > 2:
        tdw.fileName = sys.argv[argc-1]

    if argc > 1:
        print "opening the H5 file"
        tdw.openNXFile()



        for i in range(1, argc-1):
            xmlf = sys.argv[i]
        
            ## xml string    
            xml = open(xmlf, 'r').read()
            tdw.xmlSettings = xml

            print "opening the data entry "
            tdw.openEntry()
            
            print "recording the H5 file" 
            mca = str(nicePlot(2048, 10))

            tdw.record('{"data": {"exp_c01":0.1, "exp_c02":1.1, "p09/mca/exp.02":'\
                           + mca+ '  } }')
            
            
            print "sleeping for 1s"
            time.sleep(1)
            print "recording the H5 file"
            print "recording the H5 file" 
            mca = str(nicePlot(2048, 4))

            tdw.record('{"data": {"exp_c01":0.2, "exp_c02":1.3, "p09/mca/exp.02":'\
                           + mca+ '  } }')
            print "sleeping for 1s"
            time.sleep(1)
            print "recording the H5 file"
            mca = str(nicePlot(2048, 8))

            tdw.record('{"data": {"exp_c01":0.3, "exp_c02":1.4, "p09/mca/exp.02":'\
                           + mca+ '  } }')
            print "closing the data entry "
            tdw.closeEntry()


        print "closing the H5 file"
        tdw.closeNXFile()



if __name__ == "__main__":
    main()

            
                
            
            

