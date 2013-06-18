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
## \file CollCompCreator.py
# datasource creator

from simpleXML import *

from optparse import OptionParser
from xml.dom.minidom import parse, parseString

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

## creates component file
# \param name device name
# \param directory output file directory
# \param fileprefix file name prefix
# \param collection collection group name
# \param strategy field strategy
# \param nexusType nexus Type of the field 
# \param units field units
def createComponent(name, directory, fileprefix, collection,
                    strategy, nexusType, units, links):
    df = XMLFile("%s/%s%s.xml" %(directory, fileprefix ,name))  
    en = NGroup(df, "entry", "NXentry")
    ins = NGroup(en, "instrument", "NXinstrument")
    col = NGroup(ins, collection, "NXcollection")
    f = NField(col, name, nexusType)
    f.setStrategy(strategy)

    if units.strip():
        f.setUnits(units.strip())

    if links:    
        f.setText("$datasources.%s" % name)
    else:
        sr = NDSource(f)
        sr.initClient(name, name)
    df.dump()



## the main function
def main():
    ## usage example
    usage = "usage: %prog [options] [name1] [name2]"
    ## option parser
    parser = OptionParser(usage=usage)

    parser.add_option("-p", "--device-prefix", type="string",
                      help="device prefix, i.e. exp_c",
                      dest="device", default="")
    parser.add_option("-f", "--first",
                      help="first index",
                      dest="first", default="1")
    parser.add_option("-l", "--last",
                      help="last index",
                      dest="last", default=None)

    parser.add_option("-d", "--directory", type="string",
                      help="output component directory",
                      dest="directory", default=".")
    parser.add_option("-x", "--file-prefix", type="string",
                      help="file prefix, i.e. counter",
                      dest="file", default="")

    parser.add_option("-c", "--collection", type="string",
                      help="collection name",
                      dest="collection", default="collection")


    parser.add_option("-s", "--strategy", type="string",
                      help="writing strategy, i.e. STEP, INIT, FINAL, POSTRUN",
                      dest="strategy", default="STEP")
    parser.add_option("-t", "--type", type="string",
                      help="nexus type of the field",
                      dest="type", default="NX_FLOAT")
    parser.add_option("-u", "--units", type="string",
                      help="nexus units of the field",
                      dest="units", default="")


    parser.add_option("-k","--links",  action="store_true",
                      default=False, dest="links", 
                      help="create datasource links")


    (options, args) = parser.parse_args()
    print "OUTPUT DIR:", options.directory



    aargs = []
    if options.device.strip():
        try:    
            first = int(options.first)
        except:
            print  >> sys.stderr, "InstCompCreater Invalid --first parameter\n"
            parser.print_help()
            sys.exit(255)


        try:    
            last = int(options.last)
        except:
            print  >> sys.stderr, "InstCompCreater Invalid --last parameter\n"
            parser.print_help()
            sys.exit(255)




        aargs = generateDeviceNames(options.device, first, last)
        
    args += aargs
    if not len(args):
        parser.print_help()
        sys.exit(255)

    for name in args:
        print "CREATING: %s%s.xml" % (options.file, name)
        createComponent(name, options.directory, options.file,
                        options.collection, 
                        options.strategy,
                        options.type,
                        options.units,
                        options.links)
    
        


if __name__ == "__main__":
    main()
