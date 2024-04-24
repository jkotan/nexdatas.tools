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

""" Provides h5cpp file writer """

# import math
# import os
import sys
# import numpy as np
# from pninexus import h5cpp

from . import filewriter

H5CPP = False
try:
    from . import h5cppwriter as h5writer
    H5File = h5writer.H5CppFile
    H5Group = h5writer.H5CppGroup
    H5GroupIter = h5writer.H5CppGroupIter
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
    H5GroupIter = h5writer.H5PYGroupIter
    H5Field = h5writer.H5PYField
    H5Link = h5writer.H5PYLink
    H5VirtualFieldLayout = h5writer.H5PYVirtualFieldLayout
    H5TargetFieldView = h5writer.H5PYTargetFieldView
    H5DataFilter = h5writer.H5PYDataFilter
    H5Deflate = h5writer.H5PYDeflate
    H5AttributeManager = h5writer.H5PYAttributeManager
    H5Attribute = h5writer.H5PYAttribute


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


def open_file(filename, readonly=False, **pars):
    """ open the new file

    :param filename: file name
    :type filename: :obj:`str`
    :param readonly: readonly flag
    :type readonly: :obj:`bool`
    :param libver: library version: 'lastest' or 'earliest'
    :type libver: :obj:`str`
    :returns: file object
    :rtype: :class:`H5RedisFile`
    """
    return H5RedisFile(h5file=h5writer.open_file(filename, readonly, **pars))


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
        h5file=h5writer.load_file(membuffer, filename, readonly, **pars))


def create_file(filename, overwrite=False, **pars):
    """ create a new file

    :param filename: file name
    :type filename: :obj:`str`
    :param overwrite: overwrite flag
    :type overwrite: :obj:`bool`
    :param libver: library version: 'lastest' or 'earliest'
    :type libver: :obj:`str`
    :returns: file object
    :rtype: :class:`H5RedisFile`
    """
    return H5RedisFile(
        h5file=h5writer.create_file(filename, overwrite, **pars))


def link(target, parent, name):
    """ create link

    :param target: nexus path name
    :type target: :obj:`str`
    :param parent: parent object
    :type parent: :class:`FTObject`
    :param name: link name
    :type name: :obj:`str`
    :returns: link object
    :rtype: :class:`H5CppLink`
    """
    return h5writer.link(target, parent, name)


def get_links(parent):
    """ get links

    :param parent: parent object
    :type parent: :class:`FTObject`
    :returns: list of link objects
    :returns: link object
    :rtype: :obj: `list` <:class:`H5CppLink`>
    """
    return h5writer.link(parent)


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
    :rtype: :class:`H5CppDataFilter`
    """
    return h5writer.data_filter(filterid, name, options, availability,
                                shuffle, rate)


def deflate_filter(rate=None, shuffle=None, availability=None):
    """ create data filter

    :param rate: filter shuffle
    :type rate: :obj:`bool`
    :param shuffle: filter shuffle
    :type shuffle: :obj:`bool`
    :returns: deflate filter object
    :rtype: :class:`H5CppDataFilter`
    """
    return h5writer.deflate_filter(rate, shuffle, availability)


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
    :rtype: :class:`H5CppTargetFieldView`
    """
    return h5writer.target_field_view(filename, fieldpath, shape,
                                      dtype, maxshape)


def virtual_field_layout(shape, dtype, maxshape=None):
    """ creates a virtual field layout for a VDS file

    :param shape: shape
    :type shape: :obj:`list` < :obj:`int` >
    :param dtype: attribute type
    :type dtype: :obj:`str`
    :param maxshape: shape
    :type maxshape: :obj:`list` < :obj:`int` >
    :returns: virtual layout
    :rtype: :class:`H5CppVirtualFieldLayout`
    """
    return h5writer.virtual_field_layout(shape, dtype, maxshape)


class H5RedisFile(filewriter.FTFile):

    """ file tree file
    """

    def __init__(self, h5object=None, filename=None, h5file=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param filename:  file name
        :type filename: :obj:`str`
        """
        if h5file is not None:
            self.__h5file = h5file
        else:
            if h5object is None or filename is None:
                raise Exception("Undefined constructor parameters")
            self.__h5file = H5File(self, h5object, filename)

    def root(self):
        """ root object

        :returns: parent object
        :rtype: :class:`H5CppGroup`
        """
        return self.__h5file.root()

    def flush(self):
        """ flash the data
        """
        return self.__h5file.flush()

    def close(self):
        """ close file
        """
        return self.__h5file.close()

    @property
    def is_valid(self):
        """ check if file is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        return self.__h5file.is_valid

    @property
    def readonly(self):
        """ check if file is readonly

        :returns: readonly flag
        :rtype: :obj:`bool`
        """
        return self.__h5file.readonly

    def reopen(self, readonly=False, swmr=False, libver=None):
        """ reopen file

        :param readonly: readonly flag
        :type readonly: :obj:`bool`
        :param swmr: swmr flag
        :type swmr: :obj:`bool`
        :param libver:  library version, default: 'latest'
        :type libver: :obj:`str`
        """
        return self.__h5file.reopen(readonly, swmr, libver)


class H5RedisGroup(filewriter.FTGroup):

    """ file tree group
    """

    def __init__(self, h5object, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: tree parent
        :type tparent: :obj:`FTObject`
        """
        self.__h5group = H5Group(self, h5object, tparent)

    def open(self, name):
        """ open a file tree element

        :param name: element name
        :type name: :obj:`str`
        :returns: file tree object
        :rtype: :class:`FTObject`
        """
        return self.__h5group.open(name)

    def open_link(self, name):
        """ open a file tree element as link

        :param name: element name
        :type name: :obj:`str`
        :returns: file tree object
        :rtype: :class:`FTObject`
        """
        return self.__h5group.open_link(name)

    def create_group(self, n, nxclass=None):
        """ open a file tree element

        :param n: group name
        :type n: :obj:`str`
        :param nxclass: group type
        :type nxclass: :obj:`str`
        :returns: file tree group
        :rtype: :class:`H5CppGroup`
        """
        return self.__h5group.create_group(n)

    def create_virtual_field(self, name, layout, fillvalue=0):
        """ creates a virtual filed tres element

        :param name: field name
        :type name: :obj:`str`
        :param layout: virual field layout
        :type layout: :class:`H5CppFieldLayout`
        :param fillvalue:  fill value
        :type fillvalue: :obj:`int` or :class:`np.ndarray`
        """
        return self.__h5group.create_virtual_field(name, layout, fillvalue)

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
        :rtype: :class:`H5CppField`
        """
        return self.__h5group.create_field(
            name, type_code, shape, chunk, dfilter)

    @property
    def size(self):
        """ group size

        :returns: group size
        :rtype: :obj:`int`
        """
        return self.__h5group.size

    @property
    def attributes(self):
        """ return the attribute manager

        :returns: attribute manager
        :rtype: :class:`H5CppAttributeManager`
        """
        return self.__h5group.attributes

    def close(self):
        """ close group
        """
        return self.__h5group.close()

    def reopen(self):
        """ reopen group
        """
        return self.__h5group.reopen()

    def exists(self, name):
        """ if child exists

        :param name: child name
        :type name: :obj:`str`
        :returns: existing flag
        :rtype: :obj:`bool`
        """
        return self.__h5group.exists()

    def names(self):
        """ read the child names

        :returns: h5 object
        :rtype: :obj:`list` <`str`>
        """
        return self.__h5group.names()

    class H5RedisGroupIter(object):

        def __init__(self, group):
            """ constructor

            :param group: group object
            :type manager: :obj:`H5CppGroup`
            """
            self.__h5groupiter = H5GroupIter(self, group)

        def __next__(self):
            """ the next attribute

            :returns: attribute object
            :rtype: :class:`FTAtribute`
            """
            self.__h5groupiter.__next__()

        next = __next__

        def __iter__(self):
            """ attribute iterator

            :returns: attribute iterator
            :rtype: :class:`H5CppAttrIter`
            """
            return self.__h5groupiter.__iter__()

    def __iter__(self):
        """ attribute iterator

        :returns: attribute iterator
        :rtype: :class:`H5CppAttrIter`
        """
        return self.__h5group.__iter__()

    @property
    def is_valid(self):
        """ check if field is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        return self.__h5group.is_valid


class H5RedisField(filewriter.FTField):

    """ file tree file
    """

    def __init__(self, h5object, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: treee parent
        :type tparent: :obj:`FTObject`
        """

    @property
    def attributes(self):
        """ return the attribute manager

        :returns: attribute manager
        :rtype: :class:`H5CppAttributeManager`
        """
        return self.__h5field.attributes

    def close(self):
        """ close field
        """
        return self.__h5field.close()

    def reopen(self):
        """ reopen field
        """
        return self.__h5field.reopen()

    def refresh(self):
        """ refresh the field

        :returns: refreshed
        :rtype: :obj:`bool`
        """
        return self.__h5field.refresh()

    def grow(self, dim=0, ext=1):
        """ grow the field

        :param dim: growing dimension
        :type dim: :obj:`int`
        :param dim: size of the grow
        :type dim: :obj:`int`
        """
        return self.__h5field.grow(dim, ext)

    def read(self):
        """ read the field value

        :returns: h5 object
        :rtype: :obj:`any`
        """
        return self.__h5field.read()

    def write(self, o):
        """ write the field value

        :param o: h5 object
        :type o: :obj:`any`
        """
        return self.__h5field.read(o)

    def __setitem__(self, t, o):
        """ set value

        :param t: slice tuple
        :type t: :obj:`tuple`
        :param o: h5 object
        :type o: :obj:`any`
        """
        return self.__h5field.__setitem__(t, o)

    def __getitem__(self, t):
        """ get value

        :param t: slice tuple
        :type t: :obj:`tuple`
        :returns: h5 object
        :rtype: :obj:`any`
        """
        return self.__h5field.__getitem__(t)

    @property
    def is_valid(self):
        """ check if field is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        return self.__h5field.is_valid

    @property
    def dtype(self):
        """ field data type

        :returns: field data type
        :rtype: :obj:`str`
        """
        # if self.boolflag:
        #     return "bool"
        return self.__h5field.dtype

    @property
    def shape(self):
        """ field shape

        :returns: field shape
        :rtype: :obj:`list` < :obj:`int` >
        """
        return self.__h5field.shape

    @property
    def size(self):
        """ field size

        :returns: field size
        :rtype: :obj:`int`
        """
        return self.__h5field.size


class H5RedisLink(filewriter.FTLink):

    """ file tree link
    """

    def __init__(self, h5object=None, tparent=None, h5link=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: treee parent
        :type tparent: :obj:`FTObject`
        """
        if h5link is not None:
            self.__h5link = h5link
        else:
            if h5object is None:
                raise Exception("Undefined constructor parameters")
            self.__h5link = H5Link(self, h5object, tparent)

    @property
    def is_valid(self):
        """ check if link is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        return self.__h5link.is_valid

    def refresh(self):
        """ refresh the field

        :returns: refreshed
        :rtype: :obj:`bool`
        """
        return self.__h5link.refresh()

    @classmethod
    def getfilename(cls, obj):
        """ provides a filename from h5 node

        :param obj: h5 node
        :type obj: :class:`FTObject`
        :returns: file name
        :rtype: :obj:`str`
        """
        return cls.__h5link.getfilename()

    @property
    def target_path(self):
        """ target path

        :returns: target path
        :rtype: :obj:`str`
        """
        return self.__h5link.target_path

    def reopen(self):
        """ reopen field
        """
        return self.__h5link.reopen()

    def close(self):
        """ close group
        """
        return self.__h5link.close()


class H5RedisDataFilter(h5writer.H5CppDataFilter):

    """ file tree deflate
    """


class H5RedisVirtualFieldLayout(filewriter.FTVirtualFieldLayout):

    """ virtual field layout """

    def __init__(self, h5object, shape, dtype=None, maxshape=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param shape: shape
        :type shape: :obj:`list` < :obj:`int` >
        :param dtype: attribute type
        :type dtype: :obj:`str`
        :param maxshape: shape
        :type maxshape: :obj:`list` < :obj:`int` >
        """
        self.__h5virtualfieldlayout = H5VirtualFieldLayout(
            h5object, shape, dtype, maxshape)

    def __setitem__(self, key, source):
        """ add target field to layout

        :param key: slide
        :type key: :obj:`tuple`
        :param source: target field view
        :type source: :class:`H5PYTargetFieldView`
        """
        return self.__h5virtualfieldlayout.__item__(key, source)

    def add(self, key, source, sourcekey=None, shape=None):
        """ add target field to layout

        :param key: slide
        :type key: :obj:`tuple`
        :param source: target field view
        :type source: :class:`H5PYTargetFieldView`
        :param sourcekey: slide or selection
        :type sourcekey: :obj:`tuple`
        :param shape: target shape in the layout
        :type shape: :obj:`tuple`
        """
        return self.__h5virtualfieldlayout.add(key, source, sourcekey, shape)


class H5RedisTargetFieldView(filewriter.FTTargetFieldView):

    """ target field for VDS """

    def __init__(self, filename, fieldpath, shape, dtype=None, maxshape=None):
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
        """
        self.__h5targetfieldview = H5TargetFieldView(
            filename, fieldpath, shape, dtype, maxshape)


class H5RedisDeflate(H5DataFilter):

    """ deflate filter """


class H5RedisAttributeManager(filewriter.FTAttributeManager):

    """ file tree attribute
    """

    def __init__(self, h5object, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: treee parent
        :type tparent: :obj:`FTObject`
        """
        self.__h5attributemanager = H5AttributeManager(
            h5object, tparent)

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
        :rtype: :class:`H5CppAtribute`
        """
        return self.__h5attributemanager.create(name, dtype, shape, overwrite)

    def __len__(self):
        """ number of attributes

        :returns: number of attributes
        :rtype: :obj:`int`
        """
        return self.__h5attributemanager.__len__()

    def __getitem__(self, name):
        """ get value

        :param name: attribute name
        :type name: :obj:`str`
        :returns: attribute object
        :rtype: :class:`FTAtribute`
        """
        return self.__h5attributemanager.__getitem__(name)

    def names(self):
        """ key values

        :returns: attribute names
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self.__h5attributemanager.names()

    def close(self):
        """ close attribure manager
        """
        return self.__h5attributemanager.close()

    def reopen(self):
        """ reopen field
        """
        return self.__h5attributemanager.reopen()

    @property
    def is_valid(self):
        """ check if link is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        return self.__h5attributemanager.is_valid


class H5RedisAttribute(filewriter.FTAttribute):

    """ file tree attribute
    """

    def __init__(self, h5object, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: treee parent
        :type tparent: :obj:`FTObject`
        """
        self.__h5attribute = H5Attribute(h5object, tparent)

        #: (:obj:`bool`) bool flag
        # self.boolflag = False

    def close(self):
        """ close attribute
        """
        return self.__h5attribute.close()

    def read(self):
        """ read attribute value

        :returns: python object
        :rtype: :obj:`any`
        """
        return self.__h5attribute.read()

    def write(self, o):
        """ write attribute value

        :param o: python object
        :type o: :obj:`any`
        """
        return self.__h5attribute.write(o)

    def __setitem__(self, t, o):
        """ write attribute value

        :param t: slice tuple
        :type t: :obj:`tuple`
        :param o: python object
        :type o: :obj:`any`
        """
        return self.__h5attribute.__setitem__(t, o)

    def __getitem__(self, t):
        """ read attribute value

        :param t: slice tuple
        :type t: :obj:`tuple`
        :returns: python object
        :rtype: :obj:`any`
        """
        return self.__h5attribute.__getitem__(t)

    @property
    def is_valid(self):
        """ check if attribute is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        return self.__h5attribute.is_valid

    @property
    def dtype(self):
        """ field data type

        :returns: field data type
        :rtype: :obj:`str`
        """
        return self.__h5attribute.dtype

    @property
    def shape(self):
        """ attribute shape

        :returns: attribute shape
        :rtype: :obj:`list` < :obj:`int` >
        """
        return self.__h5attribute.shape

    def reopen(self):
        """ reopen attribute
        """
        return self.__h5attribute.reopen()
