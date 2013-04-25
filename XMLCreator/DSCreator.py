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
## \file simpleXMLScan.py
# test of XML file creator

from simpleXML import *

from optparse import OptionParser
from xml.dom.minidom import parse, parseString


## provides xml content of the node
# \param node DOM node
# \returns xml content string
def getText(node):
    if not node:
        return 
    xml = node.toxml() 
    start = xml.find('>')
    end = xml.rfind('<')
    if start == -1 or end < start:
        return ""
    return xml[start + 1:end].replace("&lt;","<").replace("&gt;","<").replace("&amp;","&")


## the main function
def main():
    ## usage example
    usage = "usage: %prog [options] inputFile"
    ## option parser
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--directory", type="string",
                      help="output directory where datasources will be stored",
                      dest="dir", default=".")

    (options, args) = parser.parse_args()
    if not len(args):
        parser.print_help()
        sys.exit(255)
    print "INPUT:", args
    print "OUTPUT DIR:", options.dir


    indom = parse(args[0])
    hw= indom.getElementsByTagName("hw")
    device = hw[0].firstChild

    while device:
        if device.nodeName =='device':
            name = getText(device.getElementsByTagName("name")[0]) \
                if len(device.getElementsByTagName("name")) else None
            dtype = getText(device.getElementsByTagName("type")[0]) \
                if len(device.getElementsByTagName("type")) else None     
            module = getText(device.getElementsByTagName("module")[0]) \
                if len(device.getElementsByTagName("module")) else None
            tdevice = getText(device.getElementsByTagName("device")[0]) \
                if len(device.getElementsByTagName("device")) else None
            hostname = getText(device.getElementsByTagName("hostname")[0]) \
                if len(device.getElementsByTagName("hostname")) else None
            pool = getText(device.getElementsByTagName("pool")[0]) \
                if len(device.getElementsByTagName("pool")) else None
            controller = getText(device.getElementsByTagName("controller")[0]) \
                if len(device.getElementsByTagName("controller")) else None
            channel = getText(device.getElementsByTagName("channel")[0]) \
                if len(device.getElementsByTagName("channel")) else None
            rootdevicename = getText(device.getElementsByTagName("rootdevicename")[0]) \
                if len(device.getElementsByTagName("rootdevicename")) else None
            comment = device.getElementsByTagName("#comment")

            host = hostname.split(":")[0]
            port = hostname.split(":")[1] if len(hostname.split(":")) >1 else None
                

            print name, dtype,module, tdevice, host, port,pool,controller,channel,rootdevicename

            encoding = None
            if tdevice.find("eurotherm") != -1:
                record = "Temperature"
            elif tdevice.find("mca") != -1:
                record = "Data"
            elif name.find("adc_tk") != -1:
                record = "Value"
            elif name.find("dac_tk") != -1:
                record = "Voltage"
            else:
                record = None


            if pool and record:
                if record:    
                    df = XMLFile("%s/%s.ds.xml" %(options.dir, name))
                    sr = NDSource(df)
                    sr.initTango(name, tdevice, "attribute", record,host, port, encoding)
                    df.dump()
            elif pool:        
                df = XMLFile("%s/%s.ds.xml" %(options.dir, name))
                sr = NDSource(df)
                sr.initClient(name, tdevice)
                df.dump()
            elif record:    
                df = XMLFile("%s/%s.ds.xml" %(options.dir, name))
                sr = NDSource(df)
                sr.initTango(name, tdevice, "attribute", record,host, port, encoding)
                df.dump()
            else:                
                print "WARNING: No record source for ", name ,tdevice 
            if comment:
                print "##", [device.data.strip() for c in comment]
                
            df.dump()
        elif device.nodeName =='#comment':
            print "COMMENT:",  "'%s'" % device.data.strip()
        else:
#            print "TEXT:", device.nodeName, "'", device.data.strip(),"'"
            pass
        device = device.nextSibling
        
        


if __name__ == "__main__":
    main()
