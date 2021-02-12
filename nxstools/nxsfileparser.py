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

""" NeXus main metadata viewer """

from . import filewriter
import fnmatch
import sys
import xml.etree.ElementTree as et
from lxml.etree import XMLParser

from nxstools.nxsparser import ParserTools


def getdsname(xmlstring):
    """ provides datasource name from datasource xml string

    :param xmlstring: datasource xml string
    :type xmlstring: :obj:`str`
    """

    if sys.version_info > (3,):
        node = et.fromstring(
            bytes(xmlstring, "UTF-8"),
            parser=XMLParser(collect_ids=False))
    else:
        node = et.fromstring(
            xmlstring,
            parser=XMLParser(collect_ids=False))
    if node.tag == 'datasource':
        nodes = [node]
    else:
        nodes = node.findall(".//datasource")
    dsname = ""
    if nodes:
        dsname = nodes[0].attrib["name"]
    return dsname or ""


def getdstype(xmlstring):
    """ provides datasource type from datasource xml string

    :param xmlstring: datasource xml string
    :type xmlstring: :obj:`str`
    """

    if sys.version_info > (3,):
        node = et.fromstring(
            bytes(xmlstring, "UTF-8"),
            parser=XMLParser(collect_ids=False))
    else:
        node = et.fromstring(
            xmlstring,
            parser=XMLParser(collect_ids=False))
    if node.tag == 'datasource':
        nodes = [node]
    else:
        nodes = node.findall(".//datasource")
    dstype = ""
    if nodes:
        dstype = nodes[0].attrib["type"]
    return dstype


def getdssource(xmlstring):
    """ provides source from datasource xml string

    :param xmlstring: datasource xml string
    :type xmlstring: :obj:`str`
    """

    if sys.version_info > (3,):
        node = et.fromstring(
            bytes(xmlstring, "UTF-8"),
            parser=XMLParser(collect_ids=False))
    else:
        node = et.fromstring(
            xmlstring,
            parser=XMLParser(collect_ids=False))
    if node.tag == 'datasource':
        nodes = [node]
    else:
        nodes = node.findall(".//datasource")
    dssource = ""
    if nodes:
        ds = nodes[0]
        dssource = ParserTools.getRecord(ds)
    return dssource


class NXSFileParser(object):

    """ Metadata parser for NeXus files
    """

    def __init__(self, root):
        """ constructor

        :param root: nexus root node
        :type root: :class:`filewriter.FTGroup`
        """

        #: (:obj:`list` <:obj:`dict` <:obj:`str`, `any`> >) \
        #  description list of found nodes
        self.description = []

        #: (<:obj:`dict` <:obj:`str`, \
        #   [ :obj:`str`, :obj:`types.MethodType` ] >) \
        #    nexus field attribute show names and their type convertes
        self.attrdesc = {
            "nexus_type": ["type", str],
            "units": ["units", str],
            "depends_on": ["depends_on", str],
            "trans_type": ["transformation_type", str],
            "trans_vector": ["vector", str],
            "trans_offset": ["offset", str],
            "source_name": ["nexdatas_source", getdsname],
            "source_type": ["nexdatas_source", getdstype],
            "source": ["nexdatas_source", getdssource],
            "strategy": ["nexdatas_strategy", str],
        }
        #: (:obj:`list`< :obj:`str`>)  field names which value should be stored
        self.valuestostore = ["depends_on"]
        self.__root = root
        #: (:obj:`list`< :obj:`str`>)  filters for `full_path` names
        self.filters = []

    @classmethod
    def getpath(cls, path):
        """ converts full_path with NX_classes into nexus_path

        :param path: nexus full_path
        :type path: :obj:`str`
        """
        spath = path.split("/")
        return "/".join(
            [(dr if ":" not in dr else dr.split(":")[0])
             for dr in spath])

    def __addnode(self, node, tgpath):
        """adds the node into the description list

        :param node: nexus node
        :type node: :class:`filewriter.FTField` or \
                    :class:`filewriter.FTLink` or \
                    :class:`filewriter.FTAttribute` or \
                    :class:`filewriter.FTGroup`
        :param path: path of the link target or `None`
        :type path: :obj:`str`
        """
        desc = {}
        path = filewriter.first(node.path)
        desc["full_path"] = str(path)
        desc["nexus_path"] = str(self.getpath(path))
        if hasattr(node, "dtype"):
            desc["dtype"] = str(node.dtype)
        if hasattr(node, "shape"):
            desc["shape"] = [int(n) for n in (node.shape or [])]
        if hasattr(node, "attributes"):
            attrs = node.attributes
            anames = [at.name for at in attrs]
            for key, vl in self.attrdesc.items():
                if vl[0] in anames:
                    desc[key] = vl[1](filewriter.first(attrs[vl[0]].read()))
        if node.name in self.valuestostore and node.is_valid:
            vl = node.read()
            cont = True
            while cont:
                try:
                    if not isinstance(vl, str) and \
                       (hasattr(vl, "__len__") and len(vl) == 1):
                        vl = vl[0]
                    else:
                        cont = False
                except Exception:
                    cont = False
            desc["value"] = vl

        self.description.append(desc)
        if tgpath:
            fname = self.__root.parent.name
            if "%s:/%s" % (fname, desc["nexus_path"]) != tgpath:
                ldesc = dict(desc)
                if tgpath.startswith(fname):
                    tgpath = tgpath[len(fname) + 2:]
                ldesc["nexus_path"] = "\\-> %s" % tgpath
                self.description.append(ldesc)

    def __parsenode(self, node, tgpath=None):
        """parses the node and add it into the description list

        :param node: nexus node
        :type node: :class:`filewriter.FTField` or \
                    :class:`filewriter.FTLink` or \
                    :class:`filewriter.FTAttribute` or \
                    :class:`filewriter.FTGroup`
        :param path: path of the link target or `None`
        :type path: :obj:`str`
        """
        self.__addnode(node, tgpath)
        names = []
        if isinstance(node, filewriter.FTGroup):
            names = [
                (ch.name,
                 str(ch.target_path) if hasattr(ch, "target_path") else None)
                for ch in filewriter.get_links(node)]
        for nm in names:
            try:
                ch = node.open(nm[0])
                self.__parsenode(ch, nm[1])
#            except Exception:
#                pass
            finally:
                pass

    def __filter(self):
        """filters description list

        """
        res = []
        if self.filters:
            for elem in self.description:
                fpath = elem['full_path']
                found = False
                for df in self.filters:
                    found = fnmatch.filter([fpath], df)
                    if found:
                        break
                if found:
                    res.append(elem)
            self.description[:] = res

    def parse(self):
        """parses the file and creates the filtered description list

        """
        self.__parsenode(self.__root)
        self.__filter()
