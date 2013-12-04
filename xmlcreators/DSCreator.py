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
## \file DSCreator.py
# datasource creator

from nxsxml import *

from optparse import OptionParser
from xml.dom.minidom import parse, parseString
try:
    import PyTango
except:
    sys.stderr.write("Warning: No PyTango installed")
    sys.stderr.flush()
    


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
    return xml[start + 1:end].replace("&lt;","<").replace("&gt;","<").replace("&quot;","\"").replace("&amp;","&")


## \provides DataBase instance
# \param server database host name
def getDB(server=None):
    if server:
        if not ":" in server:
            server = server +":10000"
        localtango = os.environ['TANGO_HOST']
        os.environ['TANGO_HOST'] = server

    ## tango DataBase
    db = PyTango.Database()
            
    if server and localtango:
        os.environ['TANGO_HOST'] = localtango 
        
    return db    


## the main function
def main():
    ## usage example
    usage = "usage: %prog [options] inputFile"
    ## option parser
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--directory", type="string",
                      help="output directory where datasources will be stored",
                      dest="dir", default=".")
    parser.add_option("-s","--server", dest="server", 
                      help="Server host name with the TANGO database")
    parser.add_option("-c","--comments",  action="store_true",
                      default=False, dest="comments", 
                      help="print xml comments")

    (options, args) = parser.parse_args()
    if not len(args):
        parser.print_help()
        sys.exit(255)
    print "INPUT:", args
    print "OUTPUT DIR:", options.dir


    server = None
    if options.server and options.server.strip():
        server = options.server.strip()
    db = getDB(server)
    
    
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

            df = None    
            sdevice = None    
            if pool and record:
                if record:    
                    df = XMLFile("%s/%s.ds.xml" %(options.dir, name))
                    sr = NDSource(df)
                    sr.initTango(name, tdevice, "attribute", record,host, port, encoding)
                    df.dump()
            elif pool:        
                df = XMLFile("%s/%s.ds.xml" %(options.dir, name))
                sr = NDSource(df)
                #
                # use the sardana names 
                #
                try:
                    sdevice = db.get_device_alias( str(name))
                    sr.initClient(name, sdevice)
                    df.dump()
                except:
                    sys.stderr.write("Error: Cannot read %s from the Tango database\n"% name)
                    sys.stderr.flush()
            elif record:    
                df = XMLFile("%s/%s.ds.xml" %(options.dir, name))
                sr = NDSource(df)
                sr.initTango(name, tdevice, "attribute", record, host, port, encoding)
                df.dump()
            else:                
                sys.stderr.write("Error: No record source for %s %s\n" %  ( name ,tdevice) )
                sys.stderr.flush()
            if comment:
                print "##", [device.data.strip() for c in comment]
                
            print name, dtype,module, tdevice, host, port,pool,controller,channel,rootdevicename,sdevice
            if df:
                df.dump()
        elif device.nodeName =='#comment':
            if options.comments:
                print "COMMENT:",  "'%s'" % device.data.strip()
        else:
#            print "TEXT:", device.nodeName, "'", device.data.strip(),"'"
            pass
        device = device.nextSibling
        


if __name__ == "__main__":
    main()
