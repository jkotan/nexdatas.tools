#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2018 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
#

""" Command-line tool for ascess to the nexdatas configuration server """

import xml
from xml.dom.minidom import parseString


class ParserTools(object):

    """ configuration server adapter
    """

    @classmethod
    def _getPureText(cls, node):
        """ provides  xml content of the node
        :param node: DOM node
        :type node: :class:`xml.dom.minidom.Node`
        :returns: xml content string
        :rtype: :obj:`str`
        """
        rc = []
        for child in node.childNodes:
            if child.nodeType == node.TEXT_NODE:
                rc.append(str(child.data).strip())
        return ''.join(rc).strip()

    @classmethod
    def _getText(cls, node):
        """ provides  xml content of the node

        :param node: DOM node
        :type node: :class:`xml.dom.minidom.Node`
        :returns: xml content string
        :rtype: :obj:`str`
        """
        if not node:
            return
        xmlc = node.toxml()
        start = xmlc.find('>')
        end = xmlc.rfind('<')
        if start == -1 or end < start:
            return ""
        return xmlc[start + 1:end].replace("&lt;", "<").replace("&gt;", ">"). \
            replace("&quot;", "\"").replace("&amp;", "&")

    @classmethod
    def getRecord(cls, node):
        """ fetches record name or query from datasource node

        :param node: datasource node
        :type node: :class:`xml.dom.minidom.Node`
        :returns: record name or query
        :rtype: :obj:`str`
        """
        withRec = ["CLIENT", "TANGO"]
        withQuery = ["DB"]
        if node.nodeName == 'datasource':
            dsource = node
        else:
            dsource = node.getElementsByTagName("datasource")[0] \
                if len(node.getElementsByTagName("datasource")) else None
        dstype = dsource.attributes["type"] \
            if dsource and dsource.hasAttribute("type") else None
        if dstype and dstype.value in withRec:
            res = ''
            host = None
            port = None
            dname = None
            rname = None
            device = dsource.getElementsByTagName("device")
            if device and len(device) > 0:
                if device[0].hasAttribute("hostname"):
                    host = device[0].attributes["hostname"].value
                if device[0].hasAttribute("port"):
                    port = device[0].attributes["port"].value
                if device[0].hasAttribute("name"):
                    dname = device[0].attributes["name"].value

            record = dsource.getElementsByTagName("record")
            if record and len(record) > 0:
                if record[0].hasAttribute("name"):
                    rname = record[0].attributes["name"].value
                    if dname:
                        if host:
                            if not port:
                                port = '10000'
                            res = '%s:%s/%s/%s' % (host, port, dname, rname)
                        else:
                            res = '%s/%s' % (dname, rname)
                    else:
                        res = rname
            return res
        elif dstype and dstype.value in withQuery:
            query = cls._getText(dsource.getElementsByTagName("query")[0]) \
                if len(dsource.getElementsByTagName("query")) else None
            if query and query.strip():
                return query.strip() or ""

    @classmethod
    def mergeDefinitions(cls, xmls):
        """ merges the xmls list of definitions xml strings
            to one output xml string

        :param xmls: a list of xml string with definitions
        :type xmls: :obj:`list` <:obj:`str`>
        :returns: one output xml string
        :rtype: :obj:`str`
        """
        rxml = ""
        if xmls:
            indom1 = parseString(xmls[0])
            for xmlc in xmls[1:]:
                indom2 = parseString(xmlc)
                definitions = indom2.getElementsByTagName("definition")
                for defin in definitions:
                    for tag in defin.childNodes:
                        imp = indom1.importNode(tag, True)
                        indom1.childNodes[0].appendChild(imp)
            rxml = indom1.toxml()
        return rxml

    @classmethod
    def parseDataSources(cls, xmlc):
        """ provides datasources and its records from xml string

        :param xmlc: xml string
        :type xmlc: :obj:`str`
        :returns: list of datasource descriptions
        :rtype: :obj:`list` <:obj:`dict` <:obj:`str`, :obj:`str`>>
        """
        indom = parseString(xmlc)
        return cls.__getDataSources(indom)

    @classmethod
    def __getDataSources(cls, node, direct=False):
        """ provides datasources and its records from xml string

        :param xmlc: xml string
        :type xmlc: :obj:`str`
        :returns: list of datasource descriptions
        :rtype: :obj:`list` <:obj:`dict` <:obj:`str`, :obj:`str`>>
        """
        if direct:
            dss = cls.__getChildrenByTagName(node, "datasource")
        else:
            dss = node.getElementsByTagName("datasource")
        dslist = []
        for ds in dss:
            if ds.nodeName == 'datasource':
                if ds.hasAttribute("type"):
                    dstype = ds.attributes["type"].value
                else:
                    dstype = None
                if ds.hasAttribute("name"):
                    dsname = ds.attributes["name"].value
                else:
                    dsname = None
                record = cls.getRecord(ds)
                dslist.append({
                    "source_type": dstype,
                    "source_name": dsname,
                    "source": record,
                })

        return dslist

    @classmethod
    def __getPath(cls, node):
        """ provides node path

        :param node: minidom node
        :type node: :class:`xml.dom.minidom.Node`
        :returns: node path
        :rtype: :obj:`str`
        """
        name = cls.__getAttr(node, "name")
        start = True
        while node.parentNode:
            node = node.parentNode
            if node.nodeName != "group":
                return name
            elif node.nodeName != "attribute":
                gname = cls.__getAttr(node, "name")
                if not gname:
                    gname = cls.__getAttr(node, "type")
                    if len(gname) > 2:
                        gname = gname[2:]
                if start:
                    name = gname + "@" + name
                else:
                    name = gname + "/" + name
            else:
                gname = cls.__getAttr(node, "name")
                if not gname:
                    gname = cls.__getAttr(node, "type")
                    if len(gname) > 2:
                        gname = gname[2:]
                name = gname + "/" + name
            start = False
        return name

    @classmethod
    def __getAttr(cls, node, name, tag=False):
        """ provides value of attirbute

        :param node: minidom node
        :type node: :class:`xml.dom.minidom.Node`
        :returns: attribute value
        :rtype: :obj:`str`
        """
        if node.hasAttribute(name):
            return node.attributes[name].value
        elif tag:
            atnodes = node.getElementsByTagName("attribute")
            text = None
            for at in atnodes:
                if cls.__getAttr(at, "name") == name:
                    text = str(cls._getPureText(at)).strip()
                    if not text:
                        dss = cls.__getDataSources(at)
                        text = " ".join(["$datasources.%s" % ds for ds in dss])
            return text
        else:
            return None

    @classmethod
    def __getShape(cls, node):
        """ provides node shape

        :param node: minidom node
        :type node: :class:`xml.dom.minidom.Node`
        :returns: shape list
        :rtype: :obj:`list` <:obj:`int`>
        """
        rank = int(node.attributes["rank"].value)
        #        shape = ['*'] * rank
        shape = [None] * rank
        dims = node.getElementsByTagName("dim")
        for dim in dims:
            index = int(dim.attributes["index"].value)
            if dim.hasAttribute("value"):
                try:
                    value = int(dim.attributes["value"].value)
                except ValueError:
                    value = str(dim.attributes["value"].value)
                shape[index - 1] = value
            else:
                dss = node.getElementsByTagName("datasource")
                if dss:
                    if dss[0].hasAttribute("name"):
                        value = dss[0].attributes["name"].value
                    else:
                        value = '__unnamed__'
                    shape[index - 1] = "$datasources.%s" % value
                else:
                    value = " ".join(t.nodeValue for t in dim.childNodes
                                     if t.nodeType == t.TEXT_NODE)
                    try:
                        value = int(value)
                    except:
                        value = value.strip()
                        if not value:
                            value = None
                    shape[index - 1] = value

        return shape

    @classmethod
    def __getChildrenByTagName(cls, parent, name):
        """ provides direct children by tag name

        :param parent: parent node
        :type parent: :class:`xml.dom.minidom.Node`
        :param name: tag name
        :type name: :obj:`str`
        :returns: list of children
        :rtype: :obj:`list` <:class:`xml.dom.minidom.Node`>
        """
        children = []
        for child in parent.childNodes:
            if child.nodeType == xml.dom.Node.ELEMENT_NODE:
                if child.tagName == name:
                    children.append(child)

        return children

    @classmethod
    def parseFields(cls, xmlc):
        """ provides datasources and its records from xml string

        :param xmlc: xml string
        :type xmlc: :obj:`str`
        :returns: list of datasource descriptions
        :rtype: :obj:`list` < :obj:`dict` <:obj:`str`, `any`> >
        """
        tagname = "field"
        indom = parseString(xmlc)
        nodes = indom.getElementsByTagName(tagname)
        taglist = []
        for nd in nodes:
            if nd.nodeName == tagname:

                nxtype = cls.__getAttr(nd, "type")
                units = cls.__getAttr(nd, "units")
                value = cls._getPureText(nd) or None
                trtype = cls.__getAttr(nd, "transformation_type", True)
                trvector = cls.__getAttr(nd, "vector", True)
                troffset = cls.__getAttr(nd, "offset", True)
                trdependson = cls.__getAttr(nd, "depends_on", True)
                nxpath = cls.__getPath(nd)
                dnodes = cls.__getChildrenByTagName(nd, "dimensions")
                shape = cls.__getShape(dnodes[0]) if dnodes else None
                stnodes = cls.__getChildrenByTagName(nd, "strategy")
                strategy = cls.__getAttr(stnodes[0], "mode") \
                    if stnodes else None

                sfdinfo = {
                    "strategy": strategy,
                    "nexus_path": nxpath,
                }
                fdinfo = {
                    "nexus_type": nxtype,
                    "units": units,
                    "shape": shape,
                    "trans_type": trtype,
                    "trans_vector": trvector,
                    "trans_offset": troffset,
                    "depends_on": trdependson,
                    "value": value
                }
                fdinfo.update(sfdinfo)
                dss = cls.__getDataSources(nd, direct=True)
                if dss:
                    for ds in dss:
                        ds.update(fdinfo)
                        taglist.append(ds)
                        nddss = cls.__getChildrenByTagName(nd, "datasource")
                        for ndds in nddss:
                            sdss = cls.__getDataSources(ndds, direct=True)
                            if sdss:
                                for sds in sdss:
                                    sds.update(sfdinfo)
                                    sds["source_name"] \
                                        = "\\" + sds["source_name"]
                                    taglist.append(sds)
                else:
                    taglist.append(fdinfo)

        return taglist

    @classmethod
    def parseAttributes(cls, xmlc):
        """ provides datasources and its records from xml string

        :param xmlc: xml string
        :type xmlc: :obj:`str`
        :returns: list of datasource descriptions
        :rtype: :obj:`list` < :obj:`dict` <:obj:`str`, `any`> >
        """
        tagname = "attribute"
        indom = parseString(xmlc)
        nodes = indom.getElementsByTagName(tagname)
        taglist = []
        for nd in nodes:
            if nd.nodeName == tagname:

                nxtype = cls.__getAttr(nd, "type")
                units = cls.__getAttr(nd, "units")
                value = cls._getPureText(nd) or None
                trtype = cls.__getAttr(nd, "transformation_type", True)
                trvector = cls.__getAttr(nd, "vector", True)
                troffset = cls.__getAttr(nd, "offset", True)
                trdependson = cls.__getAttr(nd, "depends_on", True)
                nxpath = cls.__getPath(nd)
                dnodes = cls.__getChildrenByTagName(nd, "dimensions")
                shape = cls.__getShape(dnodes[0]) if dnodes else None
                stnodes = cls.__getChildrenByTagName(nd, "strategy")
                strategy = cls.__getAttr(stnodes[0], "mode") \
                    if stnodes else None

                sfdinfo = {
                    "strategy": strategy,
                    "nexus_path": nxpath,
                }
                fdinfo = {
                    "nexus_type": nxtype,
                    "units": units,
                    "shape": shape,
                    "trans_type": trtype,
                    "trans_vector": trvector,
                    "trans_offset": troffset,
                    "depends_on": trdependson,
                    "value": value
                }
                fdinfo.update(sfdinfo)
                dss = cls.__getDataSources(nd, direct=True)
                if dss:
                    for ds in dss:
                        ds.update(fdinfo)
                        taglist.append(ds)
                        nddss = cls.__getChildrenByTagName(nd, "datasource")
                        for ndds in nddss:
                            sdss = cls.__getDataSources(ndds, direct=True)
                            if sdss:
                                for sds in sdss:
                                    sds.update(sfdinfo)
                                    sds["source_name"] \
                                        = "\\" + sds["source_name"]
                                    taglist.append(sds)
                else:
                    taglist.append(fdinfo)

        return taglist

    @classmethod
    def parseLinks(cls, xmlc):
        """ provides datasources and its records from xml string

        :param xmlc: xml string
        :type xmlc: :obj:`str`
        :returns: list of datasource descriptions
        :rtype: :obj:`list` < :obj:`dict` <:obj:`str`, `any`> >
        """
        tagname = "link"
        indom = parseString(xmlc)
        nodes = indom.getElementsByTagName(tagname)
        taglist = []
        for nd in nodes:
            if nd.nodeName == tagname:

                target = cls.__getAttr(nd, "target")
                value = cls._getPureText(nd) or None
                nxpath = cls.__getPath(nd)
                stnodes = cls.__getChildrenByTagName(nd, "strategy")
                strategy = cls.__getAttr(stnodes[0], "mode") \
                    if stnodes else None

                sfdinfo = {
                    "strategy": strategy,
                    "nexus_path": "[%s]" % nxpath,
                }
                fdinfo = {
                    "value": value
                }
                fdinfo.update(sfdinfo)
                dss = cls.__getDataSources(nd, direct=True)
                if dss:
                    for ds in dss:
                        ds.update(fdinfo)
                        taglist.append(ds)
                        nddss = cls.__getChildrenByTagName(nd, "datasource")
                        for ndds in nddss:
                            sdss = cls.__getDataSources(ndds, direct=True)
                            if sdss:
                                for sds in sdss:
                                    sds.update(sfdinfo)
                                    sds["source_name"] \
                                        = "\\" + sds["source_name"]
                                    taglist.append(sds)
                else:
                    taglist.append(fdinfo)
                    if target.strip():
                        fdinfo2 = dict(fdinfo)
                        fdinfo2["nexus_path"] = "\\-> %s" % target
                        taglist.append(fdinfo2)

        return taglist

    @classmethod
    def parseRecord(cls, xmlc):
        """ provides source record from xml string

        :param xmlc: xml string
        :type xmlc: :obj:`str`
        :returns: source record
        :rtype: :obj:`str`
        """
        indom = parseString(xmlc)
        return cls.getRecord(indom)


class TableTools(object):

    """ configuration server adapter
    """

    def __init__(self, description, nonone=None):
        """ constructor

        :param description: description list
        :type description:  :obj:`list` <:obj:`str`>
        :param nonone: list of parameters which have to exist to be shown
        :type nonone:  :obj:`list` <:obj:`str`>
        """
        #: (:obj:`list` <:obj:`str`>)
        #:    list of parameters which have to exist to be shown
        self.__nonone = nonone or []
        #: (:obj:`list` <:obj:`str`>)
        #:    description list
        self.__description = []
        #: (:obj:`dict` <:obj:`str` , :obj:`int`>) header sizes
        self.__hdsizes = {}
        #: (:obj:`list` <:obj:`str`>) table headers
        self.headers = [
            'nexus_path',
            'nexus_type',
            'strategy',
            'shape',
            'units',
            'depends_on',
            'trans_type',
            'trans_vector',
            'trans_offset',
            'source_name',
            'source_type',
            'source',
            'value',
        ]
        #: (:obj:`str`) table title
        self.title = None
        self.__loadDescription(description)

    def __loadDescription(self, description):
        """ loads description

        :param description:  description list
        :type description:  :obj:`list` <:obj:`str`>
        """
        for desc in description:
            if desc is None:
                self.__description.append(desc)
                continue
            skip = False
            field = desc.get("nexus_path", "").split('/')[-1]
            value = desc.get("value", "")
            if field == 'depends_on' and value:
                desc["depends_on"] = "[%s]" % value
            for hd in self.__nonone:
                vl = desc.get(hd, "")
                if isinstance(vl, (list, tuple)):
                    vl = self.__toString(vl)
                if not vl:
                    skip = True
                    break
            if not skip:
                self.__description.append(desc)

        for desc in self.__description:
            if desc is None:
                continue
            for hd, vl in desc.items():
                if hd not in self.__nonone or vl:
                    if hd not in self.__hdsizes.keys():
                        self.__hdsizes[hd] = max(len(hd) + 1, 5)
                    if isinstance(vl, (list, tuple)):
                        vl = self.__toString(vl)
                    if not isinstance(vl, str):
                        vl = str(vl)
                    if self.__hdsizes[hd] <= len(vl):
                        self.__hdsizes[hd] = len(vl) + 1

    @classmethod
    def __toString(cls, lst):
        """ converts list to string

        :param lst: given list
        :type lst: :obj:`list` <:obj:`str`>
        :returns: list in string representation
        :rtype: :obj:`str`
        """
        res = []
        for it in lst:
            res.append(it or "*")
        return str(res)

    def generateList(self):
        """ generate row lists of table

        :returns:  table rows
        :rtype: :obj:`list` <:obj:`str`>
        """
        lst = [""]
        if self.title is not None:
            lst.append(self.title)
            lst.append("")
        line = ""
        headers = [hd for hd in self.headers if hd in self.__hdsizes.keys()]
        for hd in headers:
            line += hd + " " * (self.__hdsizes[hd] - len(hd))
        lst.append(line)
        line = ""
        for hd in headers:
            line += "-" * (self.__hdsizes[hd] - 1) + " "
        lst.append(line)
        for desc in self.__description:
            line = ""
            if desc is None:
                for hd in headers:
                    line += "-" * (self.__hdsizes[hd] - 1) + " "
                lst.append(line.rstrip())
                continue
            line = ""
            for hd in headers:
                vl = desc[hd] if hd in desc else None
                if isinstance(vl, (list, tuple)):
                    vl = self.__toString(vl)
                elif vl is None:
                    vl = ""
                elif not isinstance(vl, str):
                    vl = str(vl)
                line += vl + " " * (self.__hdsizes[hd] - len(vl))

            lst.append(line.rstrip())
        lst.append("")
        return lst
