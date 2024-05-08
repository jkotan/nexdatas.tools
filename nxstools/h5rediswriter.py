#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2017 DESY, Jan Kotanski <jkotan@mail.desy.de>
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

""" Provides redis h5cpp file writer """

# import math
import os
import sys
import time
# import numpy as np
# from pninexus import h5cpp
import threading

from . import filewriter
from .redisutils import REDIS, getDataStore
from .nxsfileparser import getdsname

H5CPP = False
try:
    from . import h5cppwriter as h5writer
    H5File = h5writer.H5CppFile
    H5Group = h5writer.H5CppGroup
    H5Field = h5writer.H5CppField
    H5Link = h5writer.H5CppLink
    H5VirtualFieldLayout = h5writer.H5CppVirtualFieldLayout
    H5TargetFieldView = h5writer.H5CppTargetFieldView
    H5DataFilter = h5writer.H5CppDataFilter
    H5Deflate = h5writer.H5CppDeflate
    H5AttributeManager = h5writer.H5CppAttributeManager
    H5Attribute = h5writer.H5CppAttribute
    H5CPP = True
except Exception:
    from . import h5pywriter as h5writer
    H5File = h5writer.H5PYFile
    H5Group = h5writer.H5PYGroup
    H5Field = h5writer.H5PYField
    H5Link = h5writer.H5PYLink
    H5VirtualFieldLayout = h5writer.H5PYVirtualFieldLayout
    H5TargetFieldView = h5writer.H5PYTargetFieldView
    H5DataFilter = h5writer.H5PYDataFilter
    H5Deflate = h5writer.H5PYDeflate
    H5AttributeManager = h5writer.H5PYAttributeManager
    H5Attribute = h5writer.H5PYAttribute

try:
    from blissdata.redis_engine.encoding.numeric import NumericStreamEncoder
except Exception:
    NumericStreamEncoder = None
try:
    from blissdata.redis_engine.encoding.json import JsonStreamEncoder
except Exception:
    JsonStreamEncoder = None


def nptype(dtype):
    """ converts to numpy types

    :param dtype: h5 writer type type
    :type dtype: :obj:`str`
    :returns: nupy type
    :rtype: :obj:`str`
    """
    return h5writer.nptype(dtype)


if sys.version_info > (3,):
    unicode = str
    long = int
else:
    bytes = str


def _tostr(text):
    """ converts text  to str type

    :param text: text
    :type text: :obj:`bytes` or :obj:`unicode`
    :returns: text in str type
    :rtype: :obj:`str`
    """
    if isinstance(text, str):
        return text
    elif sys.version_info > (3,):
        return str(text, "utf8")
    else:
        return str(text)


def unlimited_selection(sel, shape):
    """ checks if hyperslab is unlimited

    :param sel: hyperslab selection
    :type sel: :class:`filewriter.FTHyperslab`
    :param shape: give shape
    :type shape: :obj:`list`
    :returns: if hyperslab is unlimited list
    :rtype: :obj:`list` <:obj:`bool`>
    """
    return h5writer.unlimited_selection(sel, shape)


def _slice2selection(t, shape):
    """ converts slice(s) to selection

    :param t: slice tuple
    :type t: :obj:`tuple`
    :return shape: field shape
    :type shape: :obj:`list` < :obj:`int` >
    :returns: hyperslab selection
    :rtype: :class:`h5cpp.dataspace.Hyperslab`
    """
    return h5writer._slice2selection(t, shape)


def unlimited(parent=None):
    """ return dataspace UNLIMITED variable for the current writer module

    :param parent: parent object
    :type parent: :class:`FTObject`
    :returns:  dataspace UNLIMITED variable
    :rtype: :class:`h5cpp.dataspace.UNLIMITED`
    """
    return h5writer.unlimited(parent)


def open_file(filename, readonly=False, redisurl=None, **pars):
    """ open the new file

    :param filename: file name
    :type filename: :obj:`str`
    :param readonly: readonly flag
    :type readonly: :obj:`bool`
    :param redisurl: redis URL
    :type redisurl: :obj:`str`
    :param libver: library version: 'lastest' or 'earliest'
    :type libver: :obj:`str`
    :returns: file object
    :rtype: :class:`H5RedisFile`
    """
    return H5RedisFile(h5imp=h5writer.open_file(filename, readonly, **pars),
                       redisurl=redisurl)


def is_image_file_supported():
    """ provides if loading of image files are supported

    :retruns: if loading of image files are supported
    :rtype: :obj:`bool`
    """
    return h5writer.is_image_file_supported()


def is_vds_supported():
    """ provides if vds are supported

    :retruns: if vds are supported
    :rtype: :obj:`bool`
    """
    return h5writer.is_vds_supported()


def is_unlimited_vds_supported():
    """ provides if unlimited vds are supported

    :retruns: if unlimited vds are supported
    :rtype: :obj:`bool`
    """
    return h5writer.is_unlimited_vds_supported()


def load_file(membuffer, filename=None, readonly=False, **pars):
    """ load a file from memory byte buffer

    :param membuffer: memory buffer
    :type membuffer: :obj:`bytes` or :obj:`io.BytesIO`
    :param filename: file name
    :type filename: :obj:`str`
    :param readonly: readonly flag
    :type readonly: :obj:`bool`
    :param pars: parameters
    :type pars: :obj:`dict` < :obj:`str`, :obj:`str`>
    :returns: file object
    :rtype: :class:`H5RedisFile`
    """
    return H5RedisFile(
        h5imp=h5writer.load_file(membuffer, filename, readonly, **pars))


def create_file(filename, overwrite=False, redisurl=None, **pars):
    """ create a new file

    :param filename: file name
    :type filename: :obj:`str`
    :param overwrite: overwrite flag
    :type overwrite: :obj:`bool`
    :param libver: library version: 'lastest' or 'earliest'
    :type libver: :obj:`str`
    :param redisurl: redis URL
    :type redisurl: :obj:`str`
    :returns: file object
    :rtype: :class:`H5RedisFile`
    """
    return H5RedisFile(
        h5imp=h5writer.create_file(filename, overwrite, **pars),
        redisurl=redisurl)


def link(target, parent, name):
    """ create link

    :param target: nexus path name
    :type target: :obj:`str`
    :param parent: parent object
    :type parent: :class:`FTObject`
    :param name: link name
    :type name: :obj:`str`
    :returns: link object
    :rtype: :class:`H5RedisLink`
    """
    return H5RedisLink(h5imp=h5writer.link(target, parent, name))


def get_links(parent):
    """ get links

    :param parent: parent object
    :type parent: :class:`FTObject`
    :returns: list of link objects
    :returns: link object
    :rtype: :obj: `list` <:class:`H5RedisLink`>
    """
    links = h5writer.get_links(parent)
    return [H5RedisLink(h5imp=lk) for lk in links]


def data_filter(filterid=None, name=None, options=None, availability=None,
                shuffle=None, rate=None):
    """ create data filter

    :param filterid: hdf5 filter id
    :type filterid: :obj:`int`
    :param name: filter name
    :type name: :obj:`str`
    :param options: filter cd values
    :type options: :obj:`tuple` <:obj:`int`>
    :param availability: filter availability i.e. 'optional' or 'mandatory'
    :type availability: :obj:`str`
    :param shuffle: filter shuffle
    :type shuffle: :obj:`bool`
    :param rate: filter shuffle
    :type rate: :obj:`bool`
    :returns: data filter object
    :rtype: :class:`H5RedisDataFilter`
    """
    return H5RedisDataFilter(h5imp=h5writer.data_filter(
        filterid, name, options, availability, shuffle, rate))


def deflate_filter(rate=None, shuffle=None, availability=None):
    """ create data filter

    :param rate: filter shuffle
    :type rate: :obj:`bool`
    :param shuffle: filter shuffle
    :type shuffle: :obj:`bool`
    :returns: deflate filter object
    :rtype: :class:`H5RedisDataFilter`
    """
    return H5RedisDataFilter(
        h5imp=h5writer.deflate_filter(rate, shuffle, availability))


def target_field_view(filename, fieldpath, shape,
                      dtype=None, maxshape=None):
    """ create target field view for VDS

    :param filename: file name
    :type filename: :obj:`str`
    :param fieldpath: nexus field path
    :type fieldpath: :obj:`str`
    :param shape: shape
    :type shape: :obj:`list` < :obj:`int` >
    :param dtype: attribute type
    :type dtype: :obj:`str`
    :param maxshape: shape
    :type maxshape: :obj:`list` < :obj:`int` >
    :returns: target field view object
    :rtype: :class:`H5RedisTargetFieldView`
    """
    return H5RedisTargetFieldView(
        h5imp=h5writer.target_field_view(
            filename, fieldpath, shape, dtype, maxshape))


def virtual_field_layout(shape, dtype, maxshape=None):
    """ creates a virtual field layout for a VDS file

    :param shape: shape
    :type shape: :obj:`list` < :obj:`int` >
    :param dtype: attribute type
    :type dtype: :obj:`str`
    :param maxshape: shape
    :type maxshape: :obj:`list` < :obj:`int` >
    :returns: virtual layout
    :rtype: :class:`H5RedisVirtualFieldLayout`
    """
    return H5RedisVirtualFieldLayout(
        h5imp=h5writer.virtual_field_layout(
            shape, dtype, maxshape))


class H5RedisFile(H5File):

    """ file tree file
    """

    def __init__(self, h5object=None, filename=None, h5imp=None,
                 redisurl=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param filename:  file name
        :type filename: :obj:`str`
        :param h5imp: h5 implementation file
        :type h5imp: :class:`filewriter.FTFile`
        :param redisurl: redis url string
        :type redisurl: :obj:`str`
        """
        if h5imp is not None:
            H5File.__init__(self, h5imp.h5object, h5imp.name)
        else:
            if h5object is None or filename is None:
                raise Exception("Undefined constructor parameters")
            H5File.__init__(self, h5object, filename)
        #: (:obj:`str`) redis url
        self.__redisurl = redisurl or "redis://localhost:6380"
        self.__datastore = None
        self.__scan = None
        self.__scan_info = {}
        self.__scan_lock = threading.Lock()
        if REDIS and self.__redisurl:
            # print("FILENAME", self.name)
            self.__datastore = getDataStore(self.__redisurl)

    def root(self):
        """ root object

        :returns: parent object
        :rtype: :class:`H5RedisGroup`
        """
        return H5RedisGroup(h5imp=H5File.root(self), redis=self.__datastore,
                            nxclass="NXroot")

    def set_scan(self, scan):
        """ scan object

        :param scan: scan object
        :param type: :class:`Scan`
        """
        with self.__scan_lock:
            self.__scan = scan

    def set_scaninfo(self, value, keys=None):
        """ set scan info parameters

        :param value: scan parameter value
        :type value: :obj:`any`
        :param keys: scan parameter value
        :type key: :obj:`list` <:obj:`str`>
        """
        with self.__scan_lock:
            if keys is None:
                self.__scaninfo = dict(value)
                return
            sinfo = self.__scaninfo

            rkeys = reversed(keys)
            while rkeys:
                ky = rkeys.pop()
                if len(rkeys) > 0:
                    sinfo = sinfo[ky]
                else:
                    sinfo[ky] = value

    def get_scaninfo(self, keys=None):
        """ get scan info parameters

        :param keys: scan parameter value
        :type key: :obj:`list` <:obj:`str`>
        :returns value: scan parameter value
        :rtype value: :obj:`any`
        """
        with self.__scan_lock:
            if keys is None:
                return dict(self.__scaninfo)
            sinfo = self.__scaninfo

            rkeys = reversed(keys)
            while rkeys:
                ky = rkeys.pop()
                sinfo = sinfo[ky]
            return sinfo

    def scan_command(self, command, *args, **kwargs):
        """ set scan attribute

        :param command: scan command
        :type command: :obj:`str`
        :param args: function list arguments
        :type args: :obj:`list` <`any`>
        :param kwargs: function dict arguments
        :type kwargs: :obj:`dict` <:obj:`str` , `any`>
        :returns: scan command value
        :rtype:  :obj:`any`
        """
        vl = None
        with self.__scan_lock:
            if hasattr(self.__scan, command):
                cmd = getattr(self.__scan, command)
                if callable(cmd):
                    vl = cmd(*args, **kwargs)
        return vl

    def scan_getattr(self, attr):
        """ get scan attribute

        :param attr: scan attr
        :type attr: :obj:`str`
        :returns: scan attr value
        :rtype:  :obj:`any`
        """
        attr = None
        with self.__scan_lock:
            if hasattr(self.__scan, attr):
                attr = getattr(self.__scan, attr)
        return attr

    def scan_setattr(self, attr, value):
        """ set attribute

        :param attr: scan attr
        :type attr: :obj:`str`
        :param value: scan attr value
        :type value: :obj:`any`
        """
        with self.__scan_lock:
            if hasattr(self.__scan, attr):
                attr = setattr(self.__scan, attr, value)

    def start(self):
        """ start scan

        """

        self.scan_command("prepare")
        self.scan_command("start")


class H5RedisGroup(H5Group):

    """ file tree group
    """

    def __init__(self, h5object=None, tparent=None, h5imp=None,
                 redis=None, nxclass=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: tree parent
        :type tparent: :obj:`FTObject`
        :param h5imp: h5 implementation group
        :type h5imp: :class:`filewriter.FTGroup`
        :param redis: redis object
        :type redis: :obj:`any`
        :param nxclass: nxclass
        :type nxclass: :obj:`str`
        """
        if h5imp is not None:
            H5Group.__init__(self, h5imp.h5object, h5imp._tparent)
        else:
            if h5object is None:
                raise Exception("Undefined constructor parameters")
            H5Group.__init__(self, h5object, tparent)
        self.__redis = redis
        self.__nxclass = nxclass

    def open(self, name):
        """ open a file tree element

        :param name: element name
        :type name: :obj:`str`
        :returns: file tree object
        :rtype: :class:`H5RedisLink`
        """
        h5obj = H5Group.open(self, name)
        if isinstance(h5obj, H5Group):
            # if self.__redis is not None:
            nxclass = None
            if u"NX_class" in [at.name for at in h5obj.attributes]:
                nxclass = filewriter.first(
                    h5obj.attributes["NX_class"]).read()

            return H5RedisGroup(h5imp=h5obj, nxclass=nxclass)
        elif isinstance(h5obj, H5Field):
            return H5RedisField(h5imp=h5obj)
        elif isinstance(h5obj, H5Attribute):
            return H5RedisAttribute(h5imp=h5obj)
        return H5RedisLink(h5imp=h5obj)

    def open_link(self, name):
        """ open a file tree element as link

        :param name: element name
        :type name: :obj:`str`
        :returns: file tree object
        :rtype: :class:`H5RedisLink`
        """
        return H5RedisLink(h5imp=H5Group.open_link(self, name))

    def set_scan(self, scan):
        """ scan object

        :param scan: scan object
        :param type: :class:`Scan`
        """
        if hasattr(self._tparent, "set_scan"):
            return self._tparent.set_scan(scan)

    def set_scaninfo(self, value, keys=None):
        """ set scan info parameters

        :param value: scan parameter value
        :type value: :obj:`any`
        :param keys: scan parameter value
        :type key: :obj:`list` <:obj:`str`>
        """
        if hasattr(self._tparent, "set_scaninfo"):
            return self._tparent.set_scaninfo(value, keys)

    def get_scaninfo(self, value, keys=None):
        """ get scan info parameters

        :param keys: scan parameter value
        :type key: :obj:`list` <:obj:`str`>
        :returns value: scan parameter value
        :rtype value: :obj:`any`
        """
        if hasattr(self._tparent, "get_scaninfo"):
            return self._tparent.get_scaninfo(keys)

    def scan_command(self, command, *args, **kwargs):
        """ set scan attribute

        :param command: scan command
        :type command: :obj:`str`
        :param args: function list arguments
        :type args: :obj:`list` <`any`>
        :param kwargs: function dict arguments
        :type kwargs: :obj:`dict` <:obj:`str` , `any`>
        :returns: scan command value
        :rtype:  :obj:`any`
        """
        if hasattr(self._tparent, "scan_command"):
            return self._tparent.scan_command(command, *args, **kwargs)

    def scan_getattr(self, attr):
        """ get scan attribute

        :param attr: scan attr
        :type attr: :obj:`str`
        :returns: scan attr value
        :rtype:  :obj:`any`
        """
        if hasattr(self._tparent, "scan_getattr"):
            return self._tparent.scan_getattr(attr)

    def scan_setattr(self, attr, value):
        """ set attribute

        :param attr: scan attr
        :type attr: :obj:`str`
        :param value: scan attr value
        :type value: :obj:`any`
        """
        if hasattr(self._tparent, "scan_setattr"):
            return self._tparent.scan_getattr(attr, value)

    def create_group(self, n, nxclass=None):
        """ open a file tree element

        :param n: group name
        :type n: :obj:`str`
        :param nxclass: group type
        :type nxclass: :obj:`str`
        :returns: file tree group
        :rtype: :class:`H5RedisGroup`
        """
        # scan = data_store.create_scan(   ## create_group nxclass='NXentry'
        #     {"name": "myscan",           # filename    "{name}_{number}.nxs"
        #      "number": 1234,             # or NXentry name  "{name}_{number}"
        #      "data_policy": "no_policy"})
        # scan.prepare()
        # scan.start()
        if REDIS:
            redis = self.__redis
            if nxclass in ["NXentry", u'NXentry'] \
               and self.__redis is not None \
               and str(type(self.__redis).__name__) == "DataStore":
                localfname = H5RedisLink.getfilename(self)
                # print("FILE", localfname, n, nxclass)
                if localfname:
                    dr, fn = os.path.split(localfname)
                    fbase, ext = os.path.splitext(fn)
                    sfbase = fbase.rsplit("_", 1)
                    sn = n.rsplit("_", 1)
                    number = 0
                    measurement = "scan"
                    try:
                        number = int(sn[1])
                        if sn[0]:
                            measurement = sn[0]
                    except Exception:
                        try:
                            number = int(sfbase[1])
                            if sfbase[0]:
                                measurement = sfbase[0]
                        except Exception:
                            number = int(time.time() * 10)
                            measurement = fbase
                    # print("SCAN", measurement, number)
                    # proposal = ''
                    # print("NAMES", self.names())
                    # if "experiment_identifier" in self.names():
                    #     proposal = filewriter.first(
                    #         self.open("experiment_identifier").read())
                    # beamline = ''
                    # if "instrument" in self.names():
                    #     ins = self.open("instrument")
                    #     print("INSNAMES", ins.names())
                    #     if "name" in ins.names():
                    #         insname = self.open("name")
                    #         print("INSNAMES", insname.attributes.names())
                    #         if insname.attributes.exists("short_name"):
                    #             beamline = filewriter.first(
                    #                 insname.attributes["short_name"].read())
                    scandct = {"name": fbase,
                               "number": number,
                               "dataset": fbase,
                               "path": dr,
                               "session": "test_session",
                               "collection": measurement,
                               "data_policy": "no_policy"}
                    # if beamline:
                    #     scandct["beamline"] = beamline
                    # if proposal:
                    #     scandct["proposal"] = proposal
                    scan = redis.create_scan(scandct, info={"name": fbase})
                    self.set_scan(scan)
                    # scan.prepare()
                    # scan.start()
                    redis = scan
        # print("CREATe", n, nxclass)
        return H5RedisGroup(
            h5imp=H5Group.create_group(self, n, nxclass), redis=redis,
            nxclass=nxclass)

    def create_virtual_field(self, name, layout, fillvalue=0):
        """ creates a virtual filed tres element

        :param name: field name
        :type name: :obj:`str`
        :param layout: virual field layout
        :type layout: :class:`H5CppFieldLayout`
        :param fillvalue:  fill value
        :type fillvalue: :obj:`int` or :class:`np.ndarray`
        :returns: file tree field
        :rtype: :class:`H5RedisField`
        """
        return H5RedisField(
            h5imp=H5Group.create_virtual_field(
                self, name, layout, fillvalue))

    def create_field(self, name, type_code,
                     shape=None, chunk=None, dfilter=None):
        """ open a file tree element

        :param n: group name
        :type n: :obj:`str`
        :param type_code: nexus field type
        :type type_code: :obj:`str`
        :param shape: shape
        :type shape: :obj:`list` < :obj:`int` >
        :param chunk: chunk
        :type chunk: :obj:`list` < :obj:`int` >
        :param dfilter: filter deflater
        :type dfilter: :class:`H5CppDataFilter`
        :returns: file tree field
        :rtype: :class:`H5RedisField`
        """
        # encoder = NumericStreamEncoder(
        #     dtype="int",
        #     shape=[]
        # )
        # scalar_stream = scan.create_stream(
        #     "exp_c01",                 # @nexdatas_name <= @nexdatas_source
        #     encoder,                   # @type,  data.shape
        #     info={"unit": "counts"}    # @units
        # )

        # stream_list = {}
        # stream_list["exp_c01"] = scalar_stream
        #
        # # record
        # scalar_stream.send(12)
        # scalar_stream.send(22)
        #
        #
        # # end
        # stream.seal()
        #
        # scan.stop()
        # scan.close()
        #
        # print("NAMES", self.names())
        # if type_code not in ["string", "str"]:
        #     print("CREATE FIELD", name, shape, chunk, type_code)
        redis = self.__redis
        return H5RedisField(
            h5imp=H5Group.create_field(
                self, name, type_code, shape, chunk,
                (dfilter if dfilter is None else dfilter)), redis=redis)

    @property
    def attributes(self):
        """ return the attribute manager

        :returns: attribute manager
        :rtype: :class:`H5CppAttributeManager`
        """
        return H5RedisAttributeManager(
            h5imp=super(H5RedisGroup, self).attributes)

    def __del__(self):
        """ close the group
        """
        # print("CLOSE GROUP", self.__nxclass, self.name)
        if REDIS:
            if self.__nxclass in ['NXentry', u'NXentry'] and \
                    str(type(self.__redis).__name__) == "Scan":
                if hasattr(self.__redis, "stop"):
                    self.scan_command("stop")
                    print("stop SCAN", self.__redis)
                if hasattr(self.__redis, "close"):
                    self.scan_command("close")
                    print("close SCAN", self.__redis)
        H5File.close(self)
        H5File.__del__(self)

    def close(self):
        """ close the group
        """
        H5File.close(self)

    class H5RedisGroupIter(object):

        def __init__(self, group=None):
            """ constructor

            :param group: group object
            :type group: :obj:`H5RedisGroup`
            """
            self.__group = group
            self.__names = group.names()

        def __next__(self):
            """ the next attribute

            :returns: attribute object
            :rtype: :class:`FTAtribute`
            """
            if self.__names:
                return self.__group.open(self.__names.pop(0))
            else:
                raise StopIteration()

        next = __next__

        def __iter__(self):
            """ attribute iterator

            :returns: attribute iterator
            :rtype: :class:`H5RedisAttrIter`
            """
            return self

    def __iter__(self):
        """ attribute iterator

        :returns: attribute iterator
        :rtype: :class:`H5RedisAttrIter`
        """
        return self.H5RedisGroupIter(self)


class H5RedisField(H5Field):

    """ file tree file
    """

    def __init__(self, h5object=None, tparent=None, h5imp=None, redis=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: treee parent
        :type tparent: :obj:`FTObject`
        :param h5imp: h5 implementation field
        :type h5imp: :class:`filewriter.FTField`
        :param redis: redis object
        :type redis: :obj:`any`
        """
        if h5imp is not None:
            H5Field.__init__(self, h5imp.h5object, h5imp._tparent)
        else:
            if h5object is None:
                raise Exception("Undefined constructor parameters")
            H5Field.__init__(self, h5object, tparent)
        self.__dsname = None
        self.__stream = None
        self.__jstream = None
        self.__scan = redis

    def set_scan(self, scan):
        """ scan object

        :param scan: scan object
        :param type: :class:`Scan`
        """
        if hasattr(self._tparent, "set_scan"):
            return self._tparent.set_scan(scan)

    def get_scaninfo(self, value, keys=None):
        """ get scan info parameters

        :param keys: scan parameter value
        :type key: :obj:`list` <:obj:`str`>
        :returns value: scan parameter value
        :rtype value: :obj:`any`
        """
        if hasattr(self._tparent, "get_scaninfo"):
            return self._tparent.get_scaninfo(keys)

    def set_scaninfo(self, value, keys=None):
        """ set scan info parameters

        :param value: scan parameter value
        :type value: :obj:`any`
        :param keys: scan parameter value
        :type key: :obj:`list` <:obj:`str`>
        """
        if hasattr(self._tparent, "set_scaninfo"):
            return self._tparent.set_scaninfo(value, keys)

    def scan_command(self, command, *args, **kwargs):
        """ set scan attribute

        :param command: scan command
        :type command: :obj:`str`
        :param args: function list arguments
        :type args: :obj:`list` <`any`>
        :param kwargs: function dict arguments
        :type kwargs: :obj:`dict` <:obj:`str` , `any`>
        :returns: scan command value
        :rtype:  :obj:`any`
        """
        if hasattr(self._tparent, "scan_command"):
            return self._tparent.scan_command(command, *args, **kwargs)

    def scan_getattr(self, attr):
        """ get scan attribute

        :param attr: scan attr
        :type attr: :obj:`str`
        :returns: scan attr value
        :rtype:  :obj:`any`
        """
        if hasattr(self._tparent, "scan_getattr"):
            return self._tparent.scan_getattr(attr)

    def scan_setattr(self, attr, value):
        """ set attribute

        :param attr: scan attr
        :type attr: :obj:`str`
        :param value: scan attr value
        :type value: :obj:`any`
        """
        if hasattr(self._tparent, "scan_setattr"):
            return self._tparent.scan_getattr(attr, value)

    @property
    def attributes(self):
        """ return the attribute manager

        :returns: attribute manager
        :rtype: :class:`H5CppAttributeManager`
        """
        return H5RedisAttributeManager(
            h5imp=super(H5RedisField, self).attributes)

    def __setitem__(self, t, o):
        """ set value

        :param t: slice tuple
        :type t: :obj:`tuple`
        :param o: h5 object
        :type o: :obj:`any`
        """
        if REDIS:
            if self.__dsname is None and \
               "nexdatas_strategy" in self.attributes.names():
                attrs = self.attributes
                strategy = filewriter.first(attrs["nexdatas_strategy"].read())
                dsname = self.name
                if "nexdatas_source" in attrs.names():
                    dsname = getdsname(
                        filewriter.first(attrs["nexdatas_source"].read()))
                units = ""
                if "units" in attrs.names():
                    units = filewriter.first(attrs["units"].read())
                self.__dsname = dsname
                shape = []
                if hasattr(o, "shape"):
                    shape = o.shape
                print("SETITEM", self, self.name, self.shape,
                      self.attributes.names(),
                      self.__dsname, strategy, self.dtype,
                      type(o), str(t), units)
                if strategy in ["STEP"]:
                    if self.dtype not in ['string', b'string']:
                        # if self.shape == (1,) or self.shape == [1,]:
                        encoder = NumericStreamEncoder(
                            dtype=self.dtype,
                            shape=shape)
                        self.__stream = self.scan_command(
                            "create_stream",
                            dsname,
                            encoder,
                            info={"unit": units})
                    else:
                        self.__jstream = self.scan_command(
                            "create_stream",
                            dsname, JsonStreamEncoder())
        if self.__dsname is not None:
            if hasattr(self.__stream, "send"):
                self.__stream.send(o)
            jo = o
            if hasattr(self.__jstream, "send"):
                if not isinstance(o, dict):
                    jo = {"value": o}
                self.__jstream.send(jo)
        H5Field.__setitem__(self, t, o)

    def __del__(self):
        """ close the field
        """
        if REDIS:
            if hasattr(self.__stream, "seal"):
                # print("STREAM SEAL", self.__dsname)
                self.__stream.seal()
            if hasattr(self.__jstream, "seal"):
                # print("STREAM SEAL", self.__dsname)
                self.__jstream.seal()
        H5Field.__del__(self)


class H5RedisLink(H5Link):

    """ file tree link
    """

    def __init__(self, h5object=None, tparent=None, h5imp=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: treee parent
        :type tparent: :obj:`FTObject`
        """
        if h5imp is not None:
            H5Link.__init__(self, h5imp.h5object, h5imp._tparent)
        else:
            if h5object is None:
                raise Exception("Undefined constructor parameters")
            H5Link.__init__(self, h5object, tparent)


class H5RedisDataFilter(H5DataFilter):

    """ file tree deflate
    """
    def __init__(self, h5object=None, tparent=None, h5imp=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: treee parent
        :type tparent: :obj:`FTObject`
        :param h5imp: h5 implementation data filter
        :type h5imp: :class:`filewriter.FTDataFilter`
        """
        if h5imp is not None:
            H5DataFilter.__init__(
                self, h5imp.h5object, h5imp._tparent)
            self.shuffle = h5imp.shuffle
            self.rate = h5imp.rate
            self.filterid = h5imp.filterid
            self.options = h5imp.options
            self.name = h5imp.name
            self.availability = h5imp.availability
        else:
            if h5object is None:
                raise Exception("Undefined constructor parameters")
            H5DataFilter.__init__(self, h5object, tparent)


class H5RedisVirtualFieldLayout(H5VirtualFieldLayout):

    """ virtual field layout """

    def __init__(self, h5object=None, shape=None, dtype=None, maxshape=None,
                 h5imp=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param shape: shape
        :type shape: :obj:`list` < :obj:`int` >
        :param dtype: attribute type
        :type dtype: :obj:`str`
        :param maxshape: shape
        :type maxshape: :obj:`list` < :obj:`int` >
        :param h5imp: h5 implementation  virtual field layout
        :type h5imp: :class:`filewriter.FTVirtualFieldLayout`
        """
        if h5imp is not None:
            H5VirtualFieldLayout.__init__(
                self, h5imp.h5object, h5imp.shape, h5imp.dtype,
                h5imp.maxshape)
        else:
            if h5object is None or shape is None:
                raise Exception("Undefined constructor parameters")
            H5VirtualFieldLayout.__init__(
                self, h5object, shape, dtype, maxshape)


class H5RedisTargetFieldView(H5TargetFieldView):

    """ target field for VDS """

    def __init__(self, filename=None, fieldpath=None, shape=None, dtype=None,
                 maxshape=None, h5imp=None):
        """ constructor

        :param filename: file name
        :type filename: :obj:`str`
        :param fieldpath: nexus field path
        :type fieldpath: :obj:`str`
        :param shape: shape
        :type shape: :obj:`list` < :obj:`int` >
        :param dtype: attribute type
        :type dtype: :obj:`str`
        :param maxshape: shape
        :type maxshape: :obj:`list` < :obj:`int` >
        :param h5imp: h5 implementation targetfieldview
        :type h5imp: :class:`filewriter.FTTargetFieldView`
        """
        if h5imp is not None:
            if H5CPP:
                H5TargetFieldView.__init__(
                    self, h5imp.filename, h5imp.fieldpath, h5imp.shape,
                    h5imp.dtype, h5imp.maxshape)
            else:
                H5TargetFieldView.__init__(
                    self, h5imp.filename, h5imp.fieldpath, h5imp.shape,
                    h5imp.dtype, h5imp.maxshape)
        else:
            if fieldpath is None or shape is None or filename is None:
                raise Exception("Undefined constructor parameters")
            if H5CPP:
                H5TargetFieldView.__init__(
                    self, filename, fieldpath, shape, dtype, maxshape)


class H5RedisDeflate(H5RedisDataFilter):

    """ deflate filter """


class H5RedisAttributeManager(H5AttributeManager):

    """ file tree attribute
    """

    def __init__(self, h5object=None, tparent=None, h5imp=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: treee parent
        :type tparent: :obj:`FTObject`
        :param h5imp: h5 implementation attributemanager
        :type h5imp: :class:`filewriter.FTAttributeManager`
        """
        if h5imp is not None:
            H5AttributeManager.__init__(self, h5imp.h5object, h5imp._tparent)
        else:
            if h5object is None:
                raise Exception("Undefined constructor parameters")
            H5AttributeManager.__init__(self, h5object, tparent)

    def create(self, name, dtype, shape=None, overwrite=False):
        """ create a new attribute

        :param name: attribute name
        :type name: :obj:`str`
        :param dtype: attribute type
        :type dtype: :obj:`str`
        :param shape: attribute shape
        :type shape: :obj:`list` < :obj:`int` >
        :param overwrite: overwrite flag
        :type overwrite: :obj:`bool`
        :returns: attribute object
        :rtype: :class:`H5RedisAttribute`
        """
        return H5RedisAttribute(
            h5imp=H5AttributeManager.create(
                self, name, dtype, shape, overwrite))

    def __getitem__(self, name):
        """ get value

        :param name: attribute name
        :type name: :obj:`str`
        :returns: attribute object
        :rtype: :class:`FTAtribute`
        """
        return H5RedisAttribute(
            h5imp=H5AttributeManager.__getitem__(self, name))


class H5RedisAttribute(H5Attribute):

    """ file tree attribute
    """

    def __init__(self, h5object=None, tparent=None, h5imp=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: treee parent
        :type tparent: :obj:`FTObject`
        :param h5imp: h5 implementation attribute
        :type h5imp: :class:`filewriter.FTAttribute`
        """
        if h5imp is not None:
            H5Attribute.__init__(self, h5imp.h5object, h5imp._tparent)
        else:
            if h5object is None:
                raise Exception("Undefined constructor parameters")
            H5Attribute.__init__(self, h5object, tparent)
