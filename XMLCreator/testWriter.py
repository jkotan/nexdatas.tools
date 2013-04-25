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
## \file testWriter.py
# example of simple writer







## the main function
def main(i):
    import sys, os
    import time
    from ndts import TangoDataWriter as TDW

    import sys, os
    import time
    import gc
    
    import PyTango
    if  len(sys.argv) < 3:
        print "usage: TangoDataWriter.py  <XMLfile>"
        return

    xmlf = sys.argv[1]
    if not os.path.exists(xmlf):
       return 

    sp = xmlf.split(".")
    print sp
    if sp[-1] == 'xml' :
        fname = ''.join(sp[0:-1])
    else:
        fname = xmlf
    fname = fname.strip() + ".h5"
    print "storing in ", fname 

    xml = open(xmlf, 'r').read()
    tdw.xmlSettings = xml
    
    print "########################################"
    print "loaded", i
    for l in open('/proc/self/status'):
        if l.startswith('VmSize'):
            print l.rstrip()
        if l.startswith('VmRSS'):
            print l.rstrip()
    print "########################################"


    tdw = TDW.TangoDataWriter("test.h5")
    tdw.numThreads = 1

    tdw.fileName = fname

    print "opening the H5 file"
    tdw.openNXFile()





    print "opening the data entry "
    tdw.openEntry()
            
    print "recording the H5 file" 
    tdw.record('{"data": {"emittance_x": 0.1},  "triggers":["trigger1", "trigger2"]  }') 
    print "sleeping for 1s"
    time.sleep(1)

    print "recording the H5 file"
    tdw.record('{"data": {"emittance_x": 0.3} }')
    print "sleeping for 1s"
    time.sleep(1)


    print "recording the H5 file"
    tdw.record('{"data": {"emittance_x": 0.3} }')
    print "sleeping for 1s"
    time.sleep(1)
     
    print "recording the H5 file"
    tdw.record('{"data": {"emittance_x": 0.6},  "triggers":["trigger1"]  }')
            

    print "sleeping for 1s"
    time.sleep(1)

    print "recording the H5 file"
    tdw.record('{"data": {"emittance_x": 0.5} }')

    print "sleeping for 1s"
    time.sleep(1)

    print "recording the H5 file"
    tdw.record('{"data": {"emittance_x": 0.1},  "triggers":["trigger2"]  }')


    print "closing the data entry "
    tdw.closeEntry()


    print "closing the H5 file"
    tdw.closeNXFile()

    del tdw
    
    gc.collect()
    del gc.garbage[:]
    print "########################################"
    print "cleared", i
    for l in open('/proc/self/status'):
        if l.startswith('VmSize'):
            print l.rstrip()
        if l.startswith('VmRSS'):
            print l.rstrip()
    print "########################################"


if __name__ == "__main__":
    for i in range(10):
        main(i)

            
                
            
            

