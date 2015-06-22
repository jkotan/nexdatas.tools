#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2015 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \package nxstools tools for nxswriter
## \file nxsxml.py
# creator of XML files

"""  Creator of XML configuration files """


import PyTango

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

        if nameAttr != "":
            self.elem.setAttribute("name", nameAttr)
        if typeAttr != "":
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
    def setStrategy(self, mode="STEP", trigger=None, value=None):
        ## strategy of data writing, i.e. INIT, STEP, FINAL, POSTRUN
        strategy = NTag(self, "strategy")
        if strategy:
            strategy.addTagAttr("mode", mode)
        if trigger:
            strategy.addTagAttr("trigger", trigger)
        if value:
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
    def setStrategy(self,  mode="STEP", trigger=None, value=None,
                    grows=None, compression=False, rate=None,
                    shuffle=None):
        ## strategy of data writing, i.e. INIT, STEP, FINAL, POSTRUN
        strategy = NTag(self, "strategy")
        if strategy:
            strategy.addTagAttr("mode", mode)
        if grows:
            strategy.addTagAttr("grows", grows)
        if trigger:
            strategy.addTagAttr("trigger", trigger)
        if value:
            strategy.setText(value)
        if compression:
            strategy.addTagAttr("compression", "true")
            if rate is not None:
                strategy.addTagAttr("rate", str(rate))
            if shuffle is not None:
                strategy.addTagAttr(
                    "shuffle",
                    "true" if shuffle else "false")

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
    # \param rank rank of the query output, i.e. SCALAR, SPECTRUM, IMAGE
    # \param mycnf MYSQL config file
    # \param user database user name
    # \param passwd database user password
    # \param dsn DSN string to initialize ORACLE and PGSQL databases
    # \param mode mode for ORACLE databases, i.e. SYSDBA or SYSOPER
    # \param host name of the host
    # \param port port number
    def initDBase(self, name, dbtype, query, dbname=None,  rank=None,
                  mycnf=None,  user=None,
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
        if rank:
            da.addTagAttr("format", rank)
        da.addText(query)

    ## sets paramters for Tango device
    # \param name name of datasource
    # \param device device name
    # \param memberType type of the data object, i.e. attribute,
    #      property, command
    # \param recordName name of the data object
    # \param host host name
    # \param port port
    # \param encoding encoding of DevEncoded data
    def initTango(self, name, device, memberType, recordName, host=None,
                  port=None, encoding=None, group=None):
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
        if group:
            dv.addTagAttr("group", group)

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
    def __init__(self, parent, deviceName, nameAttr, typeAttr="",
                 commands=True, blackAttrs=None):
        NGroup.__init__(self, parent, nameAttr, typeAttr)
        ## device proxy
        self._proxy = PyTango.DeviceProxy(deviceName)
        ## fields of the device
        self._fields = {}
        ## blacklist for Attributes
        self._blackAttrs = blackAttrs if blackAttrs else []
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
            self.addAttr(pr, "NX_CHAR",
                         str(self._proxy.get_property(pr)[pr][0]))
            if pr not in self._fields:
                self._fields[pr] = NField(self, pr, "NX_CHAR")
                self._fields[pr].setStrategy("STEP")
                sr = NDSource(self._fields[pr])
                sr.initTango(
                    self._deviceName, self._deviceName, "property",
                    pr, host="haso228k.desy.de", port="10000")

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

            if at not in self._fields and at not in self._blackAttrs:
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
                self.addAttr('URL', "NX_CHAR", "tango://" + self._deviceName)

                self._fields[at].setStrategy("STEP")
                sr = NDSource(self._fields[at])
                sr.initTango(self._deviceName, self._deviceName, "attribute",
                             at, host="haso228k.desy.de", port="10000",
                             encoding=encoding)

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
                    NField(self, cd.cmd_name,
                           self.nTypes[self.tTypes.index(
                                str(cd.out_type).split(".")[-1])])
                self._fields[cd.cmd_name].setStrategy("STEP")
                sr = NDSource(self._fields[cd.cmd_name])
                sr.initTango(self._deviceName, self._deviceName,
                             "command", cd.cmd_name,
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
    def prettyPrint(self, etNode=None):
        node = etNode if etNode else self.root
        return node.toprettyxml(indent="  ")

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

    df.dump()


if __name__ == "__main__":
    main()

#  LocalWords:  usr
