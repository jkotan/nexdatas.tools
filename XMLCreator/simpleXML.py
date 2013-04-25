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
## \file simpleXML.py
# creator of XML files

import PyTango 
import sys, os, time

from xml.dom.minidom import Document


## tag wrapper
class NTag(object):
    ## constructor
    # \param tagName tag name
    # \param parent parent tag element
    # \param nameAttr value of name attribute
    # \param typeAttr value of type attribute
    def __init__(self, parent, tagName, nameAttr="", typeAttr=""):
        ## XML minidom root
        self.root = parent.root
        ## tag element from minidom
        self.elem = self.root.createElement(tagName)
        parent.elem.appendChild(self.elem)

        if nameAttr != "" :
            self.elem.setAttribute("name", nameAttr)
        if typeAttr !=  "" :
            self.elem.setAttribute("type", typeAttr)

    ## adds tag attribute
    # \param name attribute name        
    # \param value attribute value        
    def addTagAttr(self, name, value):
        self.elem.setAttribute(name, value)

    ## sets tag content
    # \param text tag content
    def setText(self, text):
        ptext = self.root.createTextNode(text)
        self.elem.appendChild(ptext)


    ## adds tag content
    # \param text tag content
    def addText(self, text):
        ptext = self.root.createTextNode(text)
        self.elem.appendChild(ptext)


## Attribute tag wrapper    
class NAttr(NTag):
    ## constructor
    # \param parent parent tag element
    # \param nameAttr name attribute
    # \param typeAttr type attribute
    def __init__(self, parent, nameAttr, typeAttr=""):
        NTag.__init__(self, parent, "attribute", nameAttr, typeAttr)


    ## sets the attribute strategy
    # \param mode mode data writing, i.e. INIT, STEP, FINAL, POSTRUN
    # \param trigger for asynchronous writting, e.g. with different subentries
    # \param value label for postrun mode    
    def setStrategy(self,  mode = "STEP", trigger = None, value = None):
        ## strategy of data writing, i.e. INIT, STEP, FINAL, POSTRUN
        strategy = NTag(self, "strategy")
        if strategy:
            strategy.addTagAttr("mode", mode)
        if trigger:
            strategy.addTagAttr("trigger", trigger)    
	if value :
            strategy.setText(value)


## Group tag wrapper
class NGroup(NTag):
    ## constructor
    # \param parent parent tag element
    # \param nameAttr name attribute
    # \param typeAttr type attribute
    def __init__(self, parent, nameAttr, typeAttr=""):
        NTag.__init__(self, parent, "group", nameAttr, typeAttr)
        ## list of doc tag contents
        self._doc = []
        ## container with attribute tag wrappers
        self._gAttr = {}

    ## adds doc tag content
    # \param doc doc tag content    
    def addDoc(self, doc):
        self._doc.append(NTag(self, "doc"))
        self._doc[-1].addText(doc)


    ## adds attribute tag
    # \param attrName name attribute
    # \param attrType type attribute
    # \param attrValue content of the attribute tag
    def addAttr(self, attrName, attrType, attrValue=""):
        print attrName, attrType, attrValue
        at = NAttr(self, attrName, attrType)
        self._gAttr[attrName] = at
        if attrValue != "":
            at.setText(attrValue)
        return self._gAttr[attrName]
            

## Link tag wrapper
class NLink(NTag):
    ## constructor
    # \param parent parent tag element
    # \param nameAttr name attribute
    # \param gTarget target attribute
    def __init__(self, parent, nameAttr, gTarget):
        NTag.__init__(self, parent, "link", nameAttr)
        self.addTagAttr("target", gTarget)
        ## list of doc tag contents
        self._doc = []

    ## adds doc tag content
    # \param doc doc tag content    
    def addDoc(self, doc):
        self._doc.append(NTag(self, "doc"))
        self._doc[-1].addText(doc)


## Dimensions tag wrapper
class NDimensions(NTag):
    ## constructor
    # \param parent parent tag element
    # \param rankAttr  rank attribute
    def __init__(self, parent, rankAttr):
        NTag.__init__(self, parent, "dimensions")
        self.addTagAttr("rank", rankAttr)
        ## container with dim tag wrapper
        self.dims = {}
    ## adds dim tag 
    # \param indexAttr index attribute    
    # \param valueAttr value attribute
    def dim(self, indexAttr, valueAttr):
        self.dims[indexAttr] = NDim(self, indexAttr, valueAttr)
            
        
## Dim tag wrapper
class NDim(NTag):
    ## constructor
    # \param parent parent tag element
    # \param indexAttr index attribute    
    # \param valueAttr value attribute
    def __init__(self, parent, indexAttr, valueAttr):
        NTag.__init__(self, parent, "dim")
        self.addTagAttr("index", indexAttr)
        self.addTagAttr("value", valueAttr)
        

## Field tag wrapper
class NField(NTag):
    ## constructor
    # \param parent parent tag element
    # \param nameAttr name attribute
    # \param typeAttr type attribute
    def __init__(self, parent, nameAttr, typeAttr=""):
        NTag.__init__(self, parent, "field", nameAttr, typeAttr)

        ## list of doc tag contents
        self._doc = []
        ## container with attribute tag wrappers
        self._attr = {}
        

    ## sets the field strategu
    # \param mode mode data writing, i.e. INIT, STEP, FINAL, POSTRUN
    # \param trigger for asynchronous writting, e.g. with different subentries
    # \param value label for postrun mode    
    # \param grows growing dimension
    # \param compression flag if compression shuold be applied
    # \param rate compression rate
    # \param shuffle flag if compression shuffle
    def setStrategy(self,  mode = "STEP", trigger = None, value = None, grows = None, compression = False, rate = None , shuffle = None ):
        ## strategy of data writing, i.e. INIT, STEP, FINAL, POSTRUN
        strategy = NTag(self, "strategy")
        if strategy:
            strategy.addTagAttr("mode", mode)
        if grows:
            strategy.addTagAttr("grows", grows)    
        if trigger:
            strategy.addTagAttr("trigger", trigger)    
	if value :
            strategy.setText(value)
        if compression:
            strategy.addTagAttr("compression", "true")    
            if rate is not None:
                strategy.addTagAttr("rate", str(rate))    
            if shuffle is not None:
                strategy.addTagAttr("shuffle", "true" if shuffle  else "false")    


    ## sets the field unit
    # \param unitsAttr the field unit    
    def setUnits(self, unitsAttr):
        self.addTagAttr("units", unitsAttr)

    ## adds doc tag content
    # \param doc doc tag content    
    def addDoc(self, doc):
        self._doc.append(NTag(self, "doc"))
        self._doc[-1].addText(doc)

    ## adds attribute tag
    # \param attrName name attribute
    # \param attrType type attribute
    # \param attrValue content of the attribute tag
    def addAttr(self, attrName, attrType, attrValue=""):
        self._attr[attrName] = NAttr(self, attrName, attrType)
	if attrValue != '':
            self._attr[attrName].setText(attrValue)
        return self._attr[attrName]
            

## Source tag wrapper
class NDSource(NTag):
    ## constructor
    # \param parent parent tag element
    def __init__(self, parent):
        NTag.__init__(self, parent, "datasource")

        ## list of doc tag contents
        self._doc = []
            

    ## sets parameters of DataBase        
    # \param name name of datasource
    # \param dbname name of used DataBase
    # \param query database query
    # \param dbtype type of the database, i.e. MYSQL, PGSQL, ORACLE
    # \param format format of the query output, i.e. SCALAR, SPECTRUM, IMAGE
    # \param mycnf MYSQL config file
    # \param user database user name
    # \param passwd database user password
    # \param dsn DSN string to initialize ORACLE and PGSQL databases
    # \param mode mode for ORACLE databases, i.e. SYSDBA or SYSOPER        
    # \param host name of the host
    # \param port port number
    def initDBase(self, name, dbtype, query, dbname=None,  format=None,  mycnf=None,  user=None,  
              passwd=None,  dsn=None,  mode=None, host=None, port=None):
        self.addTagAttr("type", "DB")
        self.addTagAttr("name", name)
        da = NTag(self, "database")
        da.addTagAttr("dbtype", dbtype)


        if host:
            da.addTagAttr("hostname", host)
        if port:
            da.addTagAttr("port", port)
        if dbname:
            da.addTagAttr("dbname", dbname)
        if user:
            da.addTagAttr("user", user)
        if passwd:
            da.addTagAttr("passwd", passwd)
        if mycnf:
            da.addTagAttr("mycnf", mycnf)
        if mode:
            da.addTagAttr("mode", mode)
        if dsn:
            da.addText(dsn)
        

        da = NTag(self, "query")
        if format:
            da.addTagAttr("format", format)
        da.addText(query)

    ## sets paramters for Tango device
    # \param name name of datasource
    # \param device device name
    # \param memberType type of the data object, i.e. attribute,  property, command    
    # \param recordName name of the data object
    # \param host host name
    # \param port port
    # \param encoding encoding of DevEncoded data    
    def initTango(self, name, device, memberType, recordName, host=None, port=None, encoding = None):
        self.addTagAttr("type", "TANGO")
        self.addTagAttr("name", name)
        dv = NTag(self, "device")
        dv.addTagAttr("name", device)

        if memberType:
            dv.addTagAttr("member", memberType)
        if host:
            dv.addTagAttr("hostname", host)
        if port:
            dv.addTagAttr("port", port)
        if encoding:
            dv.addTagAttr("encoding", encoding)

        da = NTag(self, "record")
        da.addTagAttr("name", recordName)

    ## sets paramters for Client data
    # \param name name of datasource
    # \param recordName name of the data object
    def initClient(self, name, recordName):
        self.addTagAttr("type", "CLIENT")
        self.addTagAttr("name", name)
        da = NTag(self, "record")
        da.addTagAttr("name", recordName)
        

    ## sets paramters for Sardana data
    # \param name name of datasource
    # \param door sardana door
    # \param recordName name of the data object
    # \param host host name
    # \param port port
    def initSardana(self, name, door, recordName, host=None, port=None):
        self.addTagAttr("type", "SARDANA")
        self.addTagAttr("name", name)
        do = NTag(self, "door")
        do.addTagAttr("name", door)
        if host:
            do.addTagAttr("hostname", host)
        if port:
            do.addTagAttr("port", port)
        da = NTag(self, "record")
        da.addTagAttr("name", recordName)



        ## adds doc tag content
    # \param doc doc tag content
        def addDoc(self, doc):
            self._doc.append(NTag(self, "doc"))
            self._doc[-1].addText(doc)



## Tango device tag creator
class NDeviceGroup(NGroup):
    
        ## Tango types
    tTypes = ["DevVoid",
	      "DevBoolean",
	      "DevShort",
	      "DevLong",
	      "DevFloat",
	      "DevDouble",
	      "DevUShort",
	      "DevULong",
	      "DevString",
	      "DevVarCharArray",
	      "DevVarShortArray",
	      "DevVarLongArray",
	      "DevVarFloatArray",
	      "DevVarDoubleArray",
	      "DevVarUShortArray",
	      "DevVarULongArray",
	      "DevVarStringArray",
	      "DevVarLongStringArray",
	      "DevVarDoubleStringArray",
	      "DevState",
	      "ConstDevString",
	      "DevVarBooleanArray",
	      "DevUChar",
	      "DevLong64",
	      "DevULong64",
	      "DevVarLong64Array",
	      "DevVarULong64Array",
	      "DevInt",
	      "DevEncoded"]
    
        ## NeXuS types corresponding to the Tango types
    nTypes = ["NX_CHAR",
	      "NX_BOOLEAN",
	      "NX_INT32",
	      "NX_INT32",
	      "NX_FLOAT32",
	      "NX_FLOAT64",
	      "NX_UINT32",
	      "NX_UINT32",
	      "NX_CHAR",
	      "NX_CHAR",
	      "NX_INT32",
	      "NX_INT32",
	      "NX_FLOAT32",
	      "NX_FLOAT64",
	      "NX_UINT32",
	      "NX_UINT32",
	      "NX_CHAR",
	      "NX_CHAR",
	      "NX_CHAR",
	      "NX_CHAR",
	      "NX_CHAR",
	      "NX_BOOLEAN",
	      "NX_CHAR",
	      "NX_INT64",
	      "NX_UINT64",
	      "NX_INT64",
	      "NX_UINT64",
	      "NX_INT32",
	      "NX_CHAR"]
    
    ## constructor
    # \param parent parent tag element
    # \param deviceName tango device name
    # \param nameAttr name attribute
    # \param typeAttr type attribute
    # \param commands if we call the commands
    # \param blackAttrs list of excluded attributes
    def __init__(self, parent, deviceName, nameAttr, typeAttr="", commands=True, blackAttrs=[]):
        NGroup.__init__(self, parent, nameAttr, typeAttr)
        ## device proxy
        self._proxy = PyTango.DeviceProxy(deviceName)
        ## fields of the device
        self._fields = {}
        ## blacklist for Attributes
        self._blackAttrs = blackAttrs
        ## the device name
        self._deviceName = deviceName

        self._fetchProperties()    
        self._fetchAttributes()    
        if commands:        
            self._fetchCommands()
    

    ## fetches properties    
    # \brief It collects the device properties
    def _fetchProperties(self):    
        prop = self._proxy.get_property_list('*')
        print "PROP", prop
        for pr in prop:
            self.addAttr(pr, "NX_CHAR", str(self._proxy.get_property(pr)[pr][0]))
            if pr not in self._fields:
                self._fields[pr] = NField(self, pr, "NX_CHAR")
                self._fields[pr].setStrategy("STEP")
                sr = NDSource(self._fields[pr])
                sr.initTango(self._deviceName, self._deviceName, "property", pr, host="haso228k.desy.de", port="10000")

    ## fetches Attributes
    # \brief collects the device attributes
    def _fetchAttributes(self):    

                ## device attirbutes            
        attr = self._proxy.get_attribute_list()
        for at in attr:
            
            print at
            cf = self._proxy.attribute_query(at)
            print "QUERY"
            print cf
            print cf.name
            print cf.data_format
            print cf.standard_unit
            print cf.display_unit
            print cf.unit
            print self.tTypes[cf.data_type]
            print self.nTypes[cf.data_type]
            print cf.data_type
            
            
            if at not in self._fields and  at not in self._blackAttrs:
                self._fields[at] = NField(self, at, self.nTypes[cf.data_type])
                encoding = None
                if str(cf.data_format).split('.')[-1] == "SPECTRUM":
                    da = self._proxy.read_attribute(at)
                    d = NDimensions(self._fields[at], "1")
                    d.dim("1", str(da.dim_x))
                    if str(da.type) == 'DevEncoded':
                        encoding = 'VDEO'
                if str(cf.data_format).split('.')[-1] == "IMAGE":
                    da = self._proxy.read_attribute(at)
                    d = NDimensions(self._fields[at], "2")
                    d.dim("1", str(da.dim_x))
                    d.dim("2", str(da.dim_y))
                    if str(da.type) == 'DevEncoded':
                        encoding = 'VDEO'
                
                if cf.unit != 'No unit':
                    self._fields[at].setUnits(cf.unit)
                    self._fields[at].setUnits(cf.unit)
                  
                if cf.description != 'No description':
                    self._fields[at].addDoc(cf.description)
                self.addAttr('URL', "NX_CHAR", "tango://"+self._deviceName)

                self._fields[at].setStrategy("STEP")
                sr = NDSource(self._fields[at])
                sr.initTango(self._deviceName,self._deviceName, "attribute", at, host="haso228k.desy.de", port="10000", encoding = encoding)

#        print self._proxy.attribute_list_query()

    ## fetches commands
    # \brief It collects results of the device commands
    def _fetchCommands(self):    
                ## list of the device commands
        cmd = self._proxy.command_list_query()
        print "COMMANDS", cmd
        for cd in cmd:
            if str(cd.in_type).split(".")[-1] == "DevVoid" \
                    and str(cd.out_type).split(".")[-1] != "DevVoid" \
                    and str(cd.out_type).split(".")[-1] in self.tTypes \
                    and cd.cmd_name not in self._fields:
                self._fields[cd.cmd_name] = \
                    NField(self, cd.cmd_name, \
                           self.nTypes[self.tTypes.index(str(cd.out_type).split(".")[-1])])
                self._fields[cd.cmd_name].setStrategy("STEP")
                sr = NDSource(self._fields[cd.cmd_name])
                sr.initTango(self._deviceName, self._deviceName, "command", cd.cmd_name,\
                             host="haso228k.desy.de", port="10000")
                
                        
                
            
            
## XML file object
class XMLFile(object):
    ## constructor
    # \param fname XML file name
    def __init__(self, fname):
        ## XML file name
        self.fname = fname
        ## XML root instance
        self.root = Document()
        ## XML definition element
        self.elem = self.root.createElement("definition")
        self.root.appendChild(self.elem)
        
    ## prints pretty XML making use of minidom
    # \param etNode node 
    # \returns pretty XML string     
    def prettyPrint(self, etNode):
        return etNode.toprettyxml(indent="  ")


    ## dumps XML structure into the XML file
    # \brief It opens XML file, calls prettyPrint and closes the XML file
    def dump(self):
        myfile = open(self.fname, "w")
        myfile.write(self.prettyPrint(self.root))
        myfile.close()

    
 
        

## the main function
def main():
    ## handler to XML file
    df = XMLFile("test.xml")
    ## entry
    en = NGroup(df, "entry1", "NXentry")
    ## instrument
    ins = NGroup(en, "instrument", "NXinstrument")
    ##    NXsource
    src = NGroup(ins, "source", "NXsource")
    ## field
    f = NField(src, "distance", "NX_FLOAT")
    f.setUnits("m")
    f.setText("100.")


    f = NField(src, "single_mysql_record_string", "NX_CHAR")
    ## dimensions
    d = NDimensions(f, "1")
    d.dim("1", "1")
    ## source
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initDBase("single_mysql_record_string","MYSQL", "SELECT pid FROM device limit 1", "tango", "SPECTRUM", host="haso228k.desy.de")

    f = NField(src, "single_mysql_record_int", "NX_INT")
    ## dimensions
    d = NDimensions(f, "1")
    d.dim("1", "1")
    ## source
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initDBase( "single_mysql_record_int", "MYSQL", "SELECT pid FROM device limit 1", "tango", "SPECTRUM", host="haso228k.desy.de")


    f = NField(src, "mysql_record", "NX_CHAR")
    ## dimensions
    d = NDimensions(f, "2")
    d.dim("1", "151")
    d.dim("2", "2")
    ## source
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initDBase("mysql_record", "MYSQL", "SELECT name, pid FROM device limit 151", "tango", "IMAGE", host="haso228k.desy.de")


    f = NField(src, "pgsql_record", "NX_CHAR")
    ## dimensions
    d = NDimensions(f, "2")
    d.dim("1", "3")
    d.dim("2", "5")
    ## source
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initDBase("pgsql_record", "PGSQL", "SELECT * FROM weather limit 3", "mydb", "IMAGE")

 
    f = NField(src, "oracle_record", "NX_CHAR")
    ## dimensions
    d = NDimensions(f, "1")
    d.dim("1", "19")
    ## source
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initDBase("oracle_record", "ORACLE", "select * from (select * from telefonbuch) where ROWNUM <= 19", user='read', passwd='****', format="SPECTRUM", dsn='(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=dbsrv01.desy.de)(PORT=1521))(LOAD_BALANCE=yes)(CONNECT_DATA=(SERVER=DEDICATED)(SERVICE_NAME=desy_db.desy.de)(FAILOVER_MODE=(TYPE=NONE)(METHOD=BASIC)(RETRIES=180)(DELAY=5))))', host="haso228k.desy.de")
    f = NField(src, "type", "NX_CHAR")
    f.setText("Synchrotron X-ray Source")
    f = NField(src, "name", "NX_CHAR")
    f.setText("PETRA-III")
    a = f.addAttr("short_name", "NX_CHAR", "P3")
#    sr = NDSource(a)
#    sr.initClient("emittance_x", "emittance_x");
    f = NField(src, "probe", "NX_CHAR")
    f.setText("x-ray")
    f = NField(src, "power", "NX_FLOAT")
    f.setUnits("W")
    f.setText("1")
    f.setStrategy("INIT")
    sr = NDSource(f)
    sr.initTango("p09/motor/exp.01","p09/motor/exp.01", "attribute", "Position", host="haso228k.desy.de", port="10000")
    f = NField(src, "emittance_x", "NX_FLOAT")
    f.setUnits("nm rad")
    f.setText("0.2")
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initClient("emittance_x", "emittance_x");
    f = NField(src, "emittance_y", "NX_FLOAT")
    f.setUnits("nm rad")
    f.setText("0.2")
#    sr = NDSource(f, "STEP")
#    sr.initSardana("door1", "emittance_y", host="haso228k.desy.de", port="10000");
    f = NField(src, "sigma_x", "NX_FLOAT")
    f.setUnits("nm")
    f.setText("0.1")
    f = NField(src, "sigma_y", "NX_FLOAT")
    f.setUnits("nm")
    f.setText("0.1")
    f = NField(src, "flux", "NX_FLOAT")
    f.setUnits("s-1 cm-2")
    f.setText("0.1")
    f = NField(src, "energy", "NX_FLOAT")
    f.setUnits("GeV")
    f.setText("0.1")
    f = NField(src, "current", "NX_FLOAT")
    f.setUnits("A")
    f.setText("10")
    f = NField(src, "voltage", "NX_FLOAT")
    f.setUnits("V")
    f.setText("10")
    f = NField(src, "period", "NX_FLOAT")
    f.setUnits("microseconds")
    f.setText("1")
    f = NField(src, "target_material", "NX_CHAR")
    f.setText("C")

    ##       NXcrystal    
    cr = NGroup(ins, "crystal", "NXcrystal")
    f = NField(cr, "distance", "NX_FLOAT")
    f.setUnits("A")
    f.addDoc("Optimum diffracted wavelength")
    d = NDimensions(f, "1")
    d.dim("1", "10")
    f.setText("1 2 3 4 5 6 7 8 10 12")
        ##       NXdetector    
    de = NGroup(ins, "detector", "NXdetector")
    f = NField(de, "azimuthal_angle", "NX_FLOAT")
    f.setText("0.1")
    f = NField(de, "beam_center_x", "NX_FLOAT")
    f.setText("0.0001")
    f = NField(de, "beam_center_y", "NX_FLOAT")
    f.setText("-0.00012")
#    f = NField(de, "data", "NX_FLOAT")
    f = NField(de, "data", "NX_UINT32")
    d = NDimensions(f, "2")
#    d.dim("1", "100")
#    d.dim("2", "100")
    d.dim("1", "2")
    d.dim("2", "2")
    f.setStrategy("FINAL")
    sr = NDSource(f)
    sr.initTango("p09/tst/exp.01","p09/tst/exp.01", "attribute", "MyImageAttribute", host="haso228k.desy.de", port="10000")
    f = NField(de, "distance", "NX_FLOAT")
    f.setText("10.00012")
    f = NField(de, "polar_angle", "NX_FLOAT")
    f.addDoc(""" Optional rotation angle for the case when the powder diagram has been obtained
      through an omega-2theta scan like from a traditional single detector powder
      diffractometer""")
    d = NDimensions(f, "1")
    d.dim("1", "100")
    f.setText(" ".join([str(l) for l in range(100)]))
    f = NField(de, "rotation_angle", "NX_FLOAT")
    f.setText("0.0")
    f = NField(de, "x_pixel_size", "NX_FLOAT")
    f.setText("0.01")
    f = NField(de, "y_pixel_size", "NX_FLOAT")
    f.setText("0.01")
    f.setStrategy("FINAL")
    sr = NDSource(f)
    sr.initTango("p09/motor/exp.01","p09/motor/exp.01", "attribute", "Position", host="haso228k.desy.de", port="10000")


        ##    NXdata
    da = NGroup(en, "data", "NXdata")
    ## link
    l = NLink(da, "polar_angle", "/NXentry/NXinstrument/NXdetector/polar_angle")
    l.addDoc("Link to polar angle in /NXentry/NXinstrument/NXdetector")
    l = NLink(da, "data", "/NXentry/NXinstrument/NXdetector/data")
    l.addDoc("Link to data in /NXentry/NXinstrument/NXdetector")

    df.dump()

 

if __name__ == "__main__":
    main()

#  LocalWords:  usr
