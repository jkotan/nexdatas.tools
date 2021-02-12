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

""" Command-line tool to merge images of external file-formats
into the master NeXus file
"""

import sys
import os
import re
import shutil
import fabio
import signal
import argparse
import numpy
import json

from .filenamegenerator import FilenameGenerator
from .nxsargparser import (Runner, NXSArgParser, ErrorException)
from . import filewriter


if sys.version_info > (3,):
    unicode = str
    long = int
else:
    bytes = str


WRITERS = {}
try:
    from . import h5pywriter
    WRITERS["h5py"] = h5pywriter
except Exception:
    pass

try:
    from . import h5cppwriter
    WRITERS["h5cpp"] = h5cppwriter
except Exception:
    pass


def getcompression(compression):
    """ converts compression string to a deflate level parameter
        or list with [filterid, opt1, opt2, ...]

    :param compression: compression string
    :type compression: :obj:`str`
    :returns: deflate level parameter
              or list with [filterid, opt1, opt2, ...]
    :rtype: :obj:`int` or :obj:`list` < :obj:`int` > or `None`

    """
    if compression:
        if isinstance(compression, int) or ":" not in compression:
            level = None
            try:
                level = int(compression)
            except Exception:
                raise Exception(
                    "Error: argument -c/--compression: "
                    "invalid int value: '%s'\n" % compression)
            return level
        else:
            opts = None
            try:
                sfid, sopts = compression.split(":")
                opts = [int(sfid)]
                opts.extend([int(opt) for opt in sopts.split(",")])
            except Exception:
                raise Exception(
                    "Error: argument -c/--compression: "
                    "invalid format: '%s'\n" % compression)
            return opts
        return


class Linker(object):

    """ Create external and internal links of NeXus files
    """

    def __init__(self, nexusfilepath, target, name=None,
                 storeold=False, testmode=False, writer=None):
        """ The constructor creates the collector object

        :param nexusfilepath: the nexus file name and nexus path
        :type nexusfilepath: :obj:`str`
        :param target: the nexus file name and nexus path
        :type target: :obj:`str`
        :param storeold: if backup the input file
        :type storeold: :obj:`bool`
        :param testmode: if run in a test mode
        :type testmode: :obj:`bool`
        :param writer: the writer module
        :type writer: :obj:`str`
        """
        self.__target = target
        self.__name = name
        if not name:
            self.__name = target.split("/")[-1]
        self.__testmode = testmode
        self.__storeold = storeold
        self.__wrmodule = None
        self.__nexuspath = None
        self.__nexusfilename, self.__nexuspath = \
            nexusfilepath.split(":/")

        if writer and writer.lower() in WRITERS.keys():
            self.__wrmodule = WRITERS[writer.lower()]
        self.__siginfo = dict(
            (signal.__dict__[sname], sname)
            for sname in ('SIGINT', 'SIGHUP', 'SIGALRM', 'SIGTERM'))

        for sig in self.__siginfo.keys():
            signal.signal(sig, self._signalhandler)

    def _signalhandler(self, sig, _):
        """ signal handler

        :param sig: signal name, i.e. 'SIGINT', 'SIGHUP', 'SIGALRM', 'SIGTERM'
        :type sig: :obj:`str`
        """
        if sig in self.__siginfo.keys():
            self.__break = True
            print("terminated by %s" % self.__siginfo[sig])

    def _createtmpfile(self):
        """ creates temporary file
        """
        self.__tempfilename = self.__nexusfilename + ".__nxscollect_temp__"
        while os.path.exists(self.__tempfilename):
            self.__tempfilename += "_"
        shutil.copy2(self.__nexusfilename, self.__tempfilename)

    def _storeoldfile(self):
        """ makes back up of the input file
        """
        temp = self.__nexusfilename + ".__nxscollect_old__"
        while os.path.exists(temp):
            temp += "_"
        shutil.move(self.__nexusfilename, temp)

    def link(self):
        """ creates NeXus link
        """
        self._createtmpfile()
        path = self.__nexuspath
        try:
            self.__nxsfile = filewriter.open_file(
                self.__tempfilename, readonly=False,
                writer=self.__wrmodule)
            root = self.__nxsfile.root()
            groups = path.split("/")
            parent = root
            tgr = ""
            for gr in groups:
                if gr:
                    if ":" in gr:
                        gr, tgr = gr.split(":", 1)
                    if parent is not None and gr in parent.names():
                        parent = parent.open(gr)
                    else:
                        if not tgr:
                            tgr = "NX" + gr
                        if not self.__testmode:
                            parent = parent.create_group(gr, tgr)
                        else:
                            parent = None

            if parent:
                print("link: target %s at %s://%s as %s" %
                      (self.__target, self.__nexusfilename,
                       parent.path, self.__name))
            else:
                print("link: target %s at %s as %s" %
                      (self.__target, path, self.__name))
            if not self.__testmode:
                filewriter.link(self.__target, parent, self.__name)

            if self.__storeold:
                self._storeoldfile()
            shutil.move(self.__tempfilename, self.__nexusfilename)
        except Exception as e:
            print(str(e))
            os.remove(self.__tempfilename)


class Collector(object):

    """ Collector merge images of external file-formats
    into the master NeXus file
    """

    def __init__(self, nexusfilename, compression=2,
                 skipmissing=False, storeold=False, testmode=False,
                 writer=None):
        """ The constructor creates the collector object

        :param nexusfilename: the nexus file name
        :type nexusfilename: :obj:`str`
        :param compression: compression rate
        :type compression: :obj:`int`
        :param skipmissing: if skip missing images
        :type skipmissing: :obj:`bool`
        :param storeold: if backup the input file
        :type storeold: :obj:`bool`
        :param testmode: if run in a test mode
        :type testmode: :obj:`bool`
        :param writer: the writer module
        :type writer: :obj:`str`
        """
        self.__nexusfilename = nexusfilename
        self.__compression = compression
        self.__skipmissing = skipmissing
        self.__testmode = testmode
        self.__storeold = storeold
        self.__tempfilename = None
        self.__filepattern = re.compile(".+:\\d+:\\d+")
        self.__nxsfile = None
        self.__break = False
        self.__fullfilename = None
        self.__wrmodule = None
        if writer and writer.lower() in WRITERS.keys():
            self.__wrmodule = WRITERS[writer.lower()]
        self.__siginfo = dict(
            (signal.__dict__[sname], sname)
            for sname in ('SIGINT', 'SIGHUP', 'SIGALRM', 'SIGTERM'))

        for sig in self.__siginfo.keys():
            signal.signal(sig, self._signalhandler)

    def _signalhandler(self, sig, _):
        """ signal handler

        :param sig: signal name, i.e. 'SIGINT', 'SIGHUP', 'SIGALRM', 'SIGTERM'
        :type sig: :obj:`str`
        """
        if sig in self.__siginfo.keys():
            self.__break = True
            print("terminated by %s" % self.__siginfo[sig])

    def _createtmpfile(self):
        """ creates temporary file
        """
        self.__tempfilename = self.__nexusfilename + ".__nxscollect_temp__"
        while os.path.exists(self.__tempfilename):
            self.__tempfilename += "_"
        shutil.copy2(self.__nexusfilename, self.__tempfilename)

    def _storeoldfile(self):
        """ makes back up of the input file
        """
        temp = self.__nexusfilename + ".__nxscollect_old__"
        while os.path.exists(temp):
            temp += "_"
        shutil.move(self.__nexusfilename, temp)

    def _filegenerator(self, filestr):
        """ provides file name generator from file string

        :param filestr: file string
        :type: filestr: :obj:`str`
        :returns: file name generator or a list of file names
        :rtype: :class:`methodinstance`
        """
        if self.__filepattern.match(filestr):
            return FilenameGenerator.from_slice(filestr)
        else:
            def _files():
                return [filestr]
            return _files

    @classmethod
    def _absolutefilename(cls, filename, masterfile):
        """ provides absolute image file name

        :param filename: image file name
        :type: filename: :obj:`str`
        :param masterfile: nexus file name
        :type: masterfile: :obj:`str`
        :returns: absolute image file name
        :rtype: :obj:`str`
        """
        if not os.path.isabs(filename):
            nexusfilepath = os.path.join('/', *os.path.abspath(
                masterfile).split('/')[:-1])
            filename = os.path.abspath(os.path.join(nexusfilepath, filename))
        return filename

    def _findfile(self, filename, nname=None):
        """ searches for absolute image file name

        :param filename: image file name
        :type: filename: :obj:`str`
        :param nname: hdf5 node name
        :typ nname: :obj:`str`

        :returns: absolute image file name
        :rtype: :obj:`str`
        """
        filelist = []

        if nname is not None:
            tmpfname = '%s/%s/%s' % (
                os.path.splitext(self.__nexusfilename)[0],
                nname,
                filename.split("/")[-1])
            if os.path.exists(tmpfname):
                return tmpfname
            else:
                filelist.append(tmpfname)
            tmpfname = '%s/%s/%s' % (
                os.path.splitext(self.__fullfilename)[0],
                nname,
                filename.split("/")[-1])
            if os.path.exists(tmpfname):
                return tmpfname
            else:
                filelist.append(tmpfname)
        tmpfname = self._absolutefilename(filename, self.__nexusfilename)
        if os.path.exists(tmpfname):
            return tmpfname
        else:
            filelist.append(tmpfname)
        tmpfname = self._absolutefilename(filename, self.__fullfilename)
        if os.path.exists(tmpfname):
            return tmpfname
        else:
            filelist.append(tmpfname)
        if os.path.exists(filename):
            return filename
        else:
            filelist.append(filename)
        if not self.__skipmissing:
            raise Exception(
                "Cannot open any of %s files" % sorted(set(filelist)))
        else:
            print("Cannot open any of %s files" % sorted(set(filelist)))
        return None

    def _loadrawimage(self, filename, dtype, shape=None):
        """ loads image from file

        :param filename: image file name
        :type filename: :obj:`str`
        :param dtype: field data type
        :type dtype: :obj:`str`
        :param shape: field shape
        :type shape: :obj:`list` <:obj:`int` >
        :returns: (image data, image data type, image shape)
        :rtype: (:class:`numpy.ndarray`, :obj:`str`, :obj:`list` <:obj:`int`>)
        """
        try:
            idata = None

            with open(filename, "rb") as fl:
                idata = numpy.fromfile(fl, dtype=dtype)
            if shape:
                idata = idata.reshape(shape)
            dtype = idata.dtype.__str__()
            shape = idata.shape
            if idata is not None:
                return idata, dtype, shape
            else:
                raise Exception("Cannot open a file %s" % filename)
        except Exception as e:
            print(str(e))
            if not self.__skipmissing:
                raise Exception("Cannot open a file %s" % filename)
            else:
                print("Cannot open a file %s" % filename)

            return None, None, None

    def _loadimage(self, filename):
        """ loads image from file

        :param filename: image file name
        :type filename: :obj:`str`
        :returns: (image data, image data type, image shape)
        :rtype: (:class:`numpy.ndarray`, :obj:`str`, :obj:`list` <:obj:`int`>)
        """
        try:
            dtype = None
            shape = None
            idata = None
            image = fabio.open(filename)
            if image:
                idata = image.data[...]
                dtype = image.data.dtype.__str__()
                shape = image.data.shape
                return idata, dtype, shape
            else:
                raise Exception("Cannot open a file %s" % filename)
        except Exception:
            if not self.__skipmissing:
                raise Exception("Cannot open a file %s" % filename)
            else:
                print("Cannot open a file %s" % filename)

            return None, None, None

    def _loadh5data(self, filename, path=None):
        """ loads image from hdf5 file

        :param filename: hdf5 image file name
        :type filename: :obj:`str`
        :param path: hdf5 field path
        :type path: :obj:`str`
        :returns: (image data, image data type, image shape)
        :rtype: (:class:`numpy.ndarray`, :obj:`str`, :obj:`list` <:obj:`int`>)
        """
        try:
            dtype = None
            shape = None
            nxsfile = filewriter.open_file(
                filename, readonly=True, writer=self.__wrmodule)
            if path:
                root = nxsfile.root()
                parent = root
                nodes = path.split("/")
                for nd in nodes:
                    if nd in parent.names():
                        parent = parent.open(nd)
                    else:
                        raise Exception(
                            "Error: path %s in % cannot be open" % (path, nd))
                image = parent
            else:
                image = nxsfile.default_field()
            if image is None:
                root = nxsfile.root()
                image = root.open("data")
            idata = image.read()
            if image is not None:
                idata = image[...]
                dtype = image.dtype
                shape = image.shape
            nxsfile.close()
            return idata, dtype, shape
        except Exception as e:
            print(str(e))
            if not self.__skipmissing:
                raise Exception("Cannot open a file %s" % filename)
            else:
                print("Cannot open a file %s" % filename)
            return None, None, None

    def _addattr(self, node, attrs):
        """ adds attributes to the parent node in nexus file

        :param node: parent hdf5 node
        :type node: parent hdf5 node
        :param attrs: dictionary with attributes
        """
        attrs = attrs or {}
        for name, (value, dtype, shape) in attrs.items():
            if not self.__testmode:
                node.attributes.create(
                    name, dtype, shape, overwrite=True)[...] = value
            print(" + add attribute: %s = %s" % (name, value))

    def _getfield(self, node, fieldname, dtype, shape, fieldattrs,
                  fieldcompression):
        """ creates a field in nexus file

        :param node: parent hdf5 node
        :type node: :class:`filewriter.FTGroup` or \
                    :class:`filewriter.FTLink`
        :param fieldname: field name
        :type fieldname: :obj:`str`
        :param dtype: field data type
        :type dtype: :obj:`str`
        :param shape: filed data shape
        :type shape: :obj:`list` <:obj:`int`>
        :param fieldattrs: dictionary with field attributes
        :type fieldattrs: :obj:`dict` <:obj:`str`, :obj:`str`>
        :param fieldcompression: field compression rate
        :type fieldcompression: :obj:`int`
        :returns: hdf5 field node
        :rtype: :class:`filewriter.FTField`
        """
        field = None
        if fieldname in node.names():
            return node.open(fieldname)
        else:
            if not self.__testmode:
                cfilter = None
                if fieldcompression:
                    opts = getcompression(fieldcompression)
                    if isinstance(opts, int):
                        cfilter = filewriter.data_filter(node)
                        cfilter.rate = opts
                    elif isinstance(opts, list) and opts:
                        cfilter = filewriter.data_filter(node)
                        cfilter.filterid = opts[0]
                        cfilter.options = tuple(opts[1:])
                if len(shape) == 2:
                    nshape = [0, shape[0], shape[1]]
                    nchunk = [1, shape[0], shape[1]]
                elif len(shape) == 3:
                    nshape = [0, shape[0], shape[1], shape[2]]
                    nchunk = [1, shape[0], shape[1], shape[2]]
                else:
                    nshape = [0, shape[0]]
                    nchunk = [1, shape[0]]
                field = node.create_field(
                    fieldname,
                    dtype,
                    shape=nshape,
                    chunk=nchunk,
                    dfilter=cfilter)
                self._addattr(field, fieldattrs)
            return field

    def _collectimages(self, files, node, fieldname=None, fieldattrs=None,
                       fieldcompression=None, datatype=None, shape=None):
        """ collects images

        :param files: a list of file strings
        :type files: :obj:`list` <:obj:`str`>
        :param node: hdf5 parent node
        :type node: :class:`filewriter.FTGroup` or \
                    :class:`filewriter.FTLink`
        :param fieldname: field name
        :type fieldname: :obj:`str`
        :param fieldattrs: dictionary with field attributes
        :type fieldattrs: :obj:`dict` <:obj:`str`, :obj:`str`>
        :param fieldcompression: field compression rate
        :type fieldcompression: :obj:`int`
        :param datatype: field data type
        :type datatype: :obj:`str`
        :param shape: field shape
        :type shape: :obj:`list` <:obj:`int` >
        """
        fieldname = fieldname or "data"
        field = None
        ind = 0
        for filestr in files:
            if self.__break:
                break
            inputfiles = self._filegenerator(filestr)
            for fname in inputfiles():
                if self.__break:
                    break
                npath = None
                if not datatype and \
                   ".h5://" in fname or ".nxs://" in fname:
                    fname, npath = fname.split("://", 1)
                if not self.__testmode or node is not None:
                    fname = self._findfile(fname, node.name)
                if not fname:
                    continue
                if datatype:
                    data, dtype, shape = self._loadrawimage(
                        fname, datatype, shape)
                elif fname.endswith(".h5") or fname.endswith(".nxs"):
                    try:
                        data, dtype, shape = self._loadh5data(fname, npath)
                    except Exception as e:
                        print(str(e))
                        data, dtype, shape = self._loadimage(fname)
                else:
                    data, dtype, shape = self._loadimage(fname)
                if data is not None:
                    ishape = shape
                    nrim = 1
                    if len(shape) == 3:
                        ishape = [shape[1], shape[2]]
                        nrim = shape[0]
                    if field is None:
                        if not self.__testmode or node is not None:
                            field = self._getfield(
                                node, fieldname, dtype, ishape,
                                fieldattrs, fieldcompression)
                    if field and ind == field.shape[0]:
                        if not self.__testmode:
                            if nrim == 1:
                                field.grow(0, 1)
                                field[-1, ...] = data
                            else:
                                field.grow(0, nrim)
                                field[field.shape[0]-nrim:, ...] = data
                        print(" * append %s " % (fname))
                    ind += nrim
                    if not self.__testmode:
                        self.__nxsfile.flush()

    def _inspect(self, parent, collection=False):
        """ collects recursively the all image files defined
        by hdf5 postrun fields bellow hdf5 parent node

        :param parent: hdf5 parent node
        :type parent: :class:`filewriter.FTGroup` or \
                      :class:`filewriter.FTLink`
        :param collection: if parent is of NXcollection type
        :type collection: :obj:`bool`
        """
        if hasattr(parent, "names"):
            if collection:
                if "postrun" in parent.names():
                    inputfiles = parent.open("postrun")
                    files = inputfiles.read()
                    if hasattr(files, "tolist"):
                        files = files.tolist()
                    if isinstance(files, (str, unicode)):
                        files = [files]
                    fieldname = "data"
                    fielddtype = None
                    fieldshape = None
                    fieldattrs = {}
                    fieldcompression = None
                    for at in inputfiles.attributes:
                        if at.name == "fieldname":
                            fieldname = filewriter.first(at.read())
                        elif at.name == "fieldcompression":
                            fieldcompression = filewriter.first(at.read())
                        elif at.name == "fielddtype":
                            fielddtype = filewriter.first(at.read())
                        elif at.name == "fieldshape":
                            fieldshape = json.loads(
                                filewriter.first(at.read()))
                        elif at.name.startswith("fieldattr_"):
                            atname = at.name[10:]
                            if atname:
                                fieldattrs[atname] = (
                                    at.read(), at.dtype, at.shape
                                )
                    print("populate: %s/%s with %s" % (
                        parent.parent.path, fieldname, files))
                    if fieldcompression is None:
                        fieldcompression = self.__compression
                    self._collectimages(
                        files, parent.parent, fieldname, fieldattrs,
                        fieldcompression, fielddtype, fieldshape)
            try:
                names = parent.names()
            except Exception:
                names = []
            for name in names:
                coll = False
                child = parent.open(name)
                if hasattr(child, "attributes"):
                    for at in child.attributes:
                        if at.name == "NX_class":
                            gtype = filewriter.first(at.read())
                            if gtype == 'NXcollection':
                                coll = True
                    self._inspect(child, coll)

    def _add(self, root, path, inputfiles, fieldtype=None, fieldshape=None):
        """appends specific data if path and inputfiles are given

        :param path: nexus path of the data field
        :type path: :obj:`str`
        :param inputfiles: a list of file strings
        :type inputfiles: :obj:`list` <:obj:`str`>
        :param datatype: field data type
        :type datatype: :obj:`str`
        :param shape: field shape
        :type shape: :obj:`list` <:obj:`int` >
        """
        groups = path.split("/")
        parent = root
        tgr = ""
        for gr in groups[:-1]:
            if gr:
                if ":" in gr:
                    gr, tgr = gr.split(":", 1)
                if parent is not None and gr in parent.names():
                    parent = parent.open(gr)
                else:
                    if not tgr:
                        tgr = "NX" + gr
                    if not self.__testmode:
                        parent = parent.create_group(gr, tgr)
                    else:
                        parent = None
                    # raise Exception(
                    #     "Error: path %s in % cannot be open" % (path, gr))

        fieldname = groups[-1]
        if parent:
            print("populate: %s/%s with %s" %
                  (parent.path, fieldname, inputfiles))
        else:
            print("populate: %s/%s with %s" %
                  (path, fieldname, inputfiles))
        fieldcompression = self.__compression
        fieldattrs = {}
        self._collectimages(
            inputfiles, parent, fieldname, fieldattrs,
            fieldcompression, fieldtype, fieldshape)

    def collect(self, path=None, inputfiles=None, datatype=None, shape=None):
        """ creates a temporary file,
        collects the all image files defined by hdf5
        postrun fields of NXcollection groups and renames the temporary file
        to the origin one if the action was successful
        or appends specific data if path and inputfiles are given

        :param path: nexus path of the data field
        :type path: :obj:`str`
        :param inputfiles: a list of file strings
        :type inputfiles: :obj:`list` <:obj:`str`>
        :param datatype: field data type
        :type datatype: :obj:`str`
        :param shape: field shape
        :type shape: :obj:`list` <:obj:`int` >
        """
        self._createtmpfile()
        try:
            self.__nxsfile = filewriter.open_file(
                self.__tempfilename, readonly=self.__testmode,
                writer=self.__wrmodule)
            root = self.__nxsfile.root()
            try:
                self.__fullfilename = filewriter.first(
                    root.attributes['file_name'].read())
                # print self.__fullfilename
            except Exception:
                pass
            if path and inputfiles:
                self._add(root, path, inputfiles, datatype, shape)
            else:
                self._inspect(root)
            self.__nxsfile.close()
            if self.__storeold:
                self._storeoldfile()
            shutil.move(self.__tempfilename, self.__nexusfilename)
        except Exception as e:
            print(str(e))
            os.remove(self.__tempfilename)


class VDS(Runner):

    """ Execute runner
    """

    #: (:obj:`str`) command description
    description = "create a virual dataset in the master file"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxscollect vds " \
        + "scan_234.nxs://entry/instrument/lambda/data " \
        + "--external-fields lambda.nxs://entry/data/data \n\n" \
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            "-n", "--name", dest="name",
            action="store", type=str, default=None,
            help="link name")
        parser.add_argument(
            "-t", "--target", dest="target",
            action="store", type=str, default=None,
            help="link target with the file name if external")
        parser.add_argument(
            "-r", "--replace-nexus-file", action="store_true",
            default=False, dest="replaceold",
            help="if it is set the old file is not copied into "
            "a file with .__nxscollect__old__* extension")
        parser.add_argument(
            "--test", action="store_true",
            default=False, dest="testmode",
            help="execute in the test mode")
        parser.add_argument(
            "--h5py", action="store_true",
            default=False, dest="h5py",
            help="use h5py module as a nexus reader/writer")
        self._parser.add_argument(
            "--h5cpp", action="store_true",
            default=False, dest="h5cpp",
            help="use h5cpp module as a nexus reader")

    def postauto(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            'args', metavar='nexus_file_path_field',
            type=str, nargs='?',
            help='nexus files with the nexus directory and a field name '
            'to create VDS')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        parser = self._parser
        nexusfilepath = options.args

        if not nexusfilepath or not nexusfilepath[0]:
            parser.print_help()
            print("")
            sys.exit(0)

        if options.h5cpp:
            writer = "h5cpp"
        elif options.h5py:
            writer = "h5py"
        elif "h5cpp" in WRITERS.keys():
            writer = "h5cpp"
        else:
            writer = "h5py"

        if (options.h5py and options.h5cpp) or \
           writer not in WRITERS.keys():
            sys.stderr.write("nxscollect: Writer '%s' cannot be opened\n"
                             % writer)
            sys.stderr.flush()
            parser.print_help()
            sys.exit(255)

        # configuration server
        linker = Linker(
            nexusfilepath, options.target, options.name,
            not options.replaceold, options.testmode, writer=writer)
        linker.link()


class Link(Runner):

    """ Execute runner
    """

    #: (:obj:`str`) command description
    description = "create an external or internal link in the master file"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxscollect link " \
        + "scan_234.nxs://entry/instrument/lambda " \
        + "--name data --target scan_234/lambda.nxs://entry/data/data \n\n" \
        + "scan_234.nxs://entry/instrument/eiger:NXdetector " \
        + "  --target scan_234/eiger.nxs://entry/data/data \n\n" \
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            "-n", "--name", dest="name",
            action="store", type=str, default=None,
            help="link name")
        parser.add_argument(
            "-t", "--target", dest="target",
            action="store", type=str, default=None,
            help="link target with the file name if external")
        parser.add_argument(
            "-r", "--replace-nexus-file", action="store_true",
            default=False, dest="replaceold",
            help="if it is set the old file is not copied into "
            "a file with .__nxscollect__old__* extension")
        parser.add_argument(
            "--test", action="store_true",
            default=False, dest="testmode",
            help="execute in the test mode")
        parser.add_argument(
            "--h5py", action="store_true",
            default=False, dest="h5py",
            help="use h5py module as a nexus reader/writer")
        self._parser.add_argument(
            "--h5cpp", action="store_true",
            default=False, dest="h5cpp",
            help="use h5cpp module as a nexus reader")

    def postauto(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            'args', metavar='nexus_file_path',
            type=str, nargs='?',
            help='nexus files with the nexus directory to place the link')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        parser = self._parser
        nexusfilepath = options.args

        if not nexusfilepath or not nexusfilepath[0]:
            parser.print_help()
            print("")
            sys.exit(0)

        if options.h5cpp:
            writer = "h5cpp"
        elif options.h5py:
            writer = "h5py"
        elif "h5cpp" in WRITERS.keys():
            writer = "h5cpp"
        else:
            writer = "h5py"

        if (options.h5py and options.h5cpp) or \
           writer not in WRITERS.keys():
            sys.stderr.write("nxscollect: Writer '%s' cannot be opened\n"
                             % writer)
            sys.stderr.flush()
            parser.print_help()
            sys.exit(255)

        # configuration server
        linker = Linker(
            nexusfilepath, options.target, options.name,
            not options.replaceold, options.testmode, writer=writer)
        linker.link()


class Execute(Runner):

    """ Execute runner
    """

    #: (:obj:`str`) command description
    description = "append images to the master file"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxscollect append -c1 /tmp/gpfs/raw/scan_234.nxs \n\n" \
        + "       nxscollect append -c32008:0,2 /ramdisk/scan_123.nxs \n\n" \
        + "       nxscollect append --test /tmp/gpfs/raw/scan_234.nxs \n\n" \
        + "       nxscollect append scan_234.nxs " \
        + "--path /scan/instrument/pilatus/data  " \
        + "--input-files 'scan_%05d.tif:0:100' "\
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            "-c", "--compression", dest="compression",
            action="store", type=str, default="2",
            help="deflate compression rate from 0 to 9 (default: 2)"
            " or <filterid>:opt1,opt2,..."
            " e.g.  -c 32008:0,2  for bitshuffle with lz4")
        parser.add_argument(
            "-p", "--path", dest="path",
            action="store", type=str, default=None,
            help="nexus path for the output field, e.g."
            " /scan/instrument/pilatus/data")
        parser.add_argument(
            "-i", "--input-files", dest="inputfiles",
            action="store", type=str, default=None,
            help="input data files defined with a pattern "
            "or separated by ',' e.g."
            "'scan_%%05d.tif:0:100'")
        parser.add_argument(
            "--separator", dest="separator",
            action="store", type=str, default=",",
            help="input data files separator (default: ',')")
        parser.add_argument(
            "--dtype", dest="datatype",
            action="store", type=str, default=None,
            help="datatype of input data - only for raw data,"
            " e.g. 'uint8'")
        parser.add_argument(
            "--shape", dest="shape",
            action="store", type=str, default=None,
            help="shape of input data - only for raw data,"
            " e.g. '[4096,2048]'")
        parser.add_argument(
            "-s", "--skip-missing", action="store_true",
            default=False, dest="skipmissing",
            help="skip missing files")
        parser.add_argument(
            "-r", "--replace-nexus-file", action="store_true",
            default=False, dest="replaceold",
            help="if it is set the old file is not copied into "
            "a file with .__nxscollect__old__* extension")
        parser.add_argument(
            "--test", action="store_true",
            default=False, dest="testmode",
            help="execute in the test mode")
        parser.add_argument(
            "--h5py", action="store_true",
            default=False, dest="h5py",
            help="use h5py module as a nexus reader/writer")
        self._parser.add_argument(
            "--h5cpp", action="store_true",
            default=False, dest="h5cpp",
            help="use h5cpp module as a nexus reader")

    def postauto(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument('args', metavar='nexus_file',
                            type=str, nargs='*',
                            help='nexus files to be collected')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        parser = self._parser
        nexusfiles = options.args

        try:
            getcompression(options.compression)
        except Exception as e:
            print(str(e))
            parser.print_help()
            print("")
            sys.exit(0)

        if not nexusfiles or not nexusfiles[0]:
            parser.print_help()
            print("")
            sys.exit(0)

        if options.h5cpp:
            writer = "h5cpp"
        elif options.h5py:
            writer = "h5py"
        elif "h5cpp" in WRITERS.keys():
            writer = "h5cpp"
        else:
            writer = "h5py"
        if (options.h5py and options.h5cpp) or \
           writer not in WRITERS.keys():
            sys.stderr.write("nxscollect: Writer '%s' cannot be opened\n"
                             % writer)
            sys.stderr.flush()
            parser.print_help()
            sys.exit(255)
        if (options.path and not options.inputfiles):
            sys.stderr.write(
                "nxscollect: --input-files argument is missing")
            parser.print_help()
            sys.exit(255)
        if (not options.path and options.inputfiles):
            sys.stderr.write(
                "nxscollect: --path argument is missing")
            parser.print_help()
            sys.exit(255)
        inputfiles = None
        if options.inputfiles:
            if options.separator:
                inputfiles = options.inputfiles.split(options.separator)
            else:
                inputfiles = [options.inputfiles]

        shape = None
        if options.shape:
            try:
                shape = json.loads(options.shape)
            except Exception:
                sys.stderr.write(
                    "nxscollect: shape is not readable")
                parser.print_help()
                sys.exit(255)

        # configuration server
        for nxsfile in nexusfiles:
            collector = Collector(
                nxsfile, options.compression, options.skipmissing,
                not options.replaceold, options.testmode, writer=writer)
            collector.collect(options.path, inputfiles,
                              options.datatype, shape)


def _supportoldcommands():
    """ replace the old command names to the new ones
    """

    oldnew = {
        '-x': 'append',
        '--execute': 'append',
        '--replace_nexus_file': '--replace-nexus-file',
        '--input_files': '--input-files',
        '--skip_missing': '--skip-missing',
        'execute': 'append',
    }

    if sys.argv and len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if i > 0 and arg in oldnew.keys():
                sys.stderr.write(
                    "Warning: `%s` is deprecated, "
                    "please use `%s` instead\n\n"
                    % (arg, oldnew[arg]))
                sys.argv[i] = oldnew[arg]


def main():
    """ the main program function
    """
    description = "  Command-line tool to merge images of external " \
                  + "file-formats into the master NeXus file"

    epilog = 'For more help:\n  nxscollect <sub-command> -h'
    _supportoldcommands()

    parser = NXSArgParser(
        description=description, epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.cmdrunners = [
        ('append', Execute),
        ('link', Link)
        # ('vds', VDS)
    ]
    runners = parser.createSubParsers()

    try:
        options = parser.parse_args()
    except ErrorException as e:
        sys.stderr.write("Error: %s\n" % str(e))
        sys.stderr.flush()
        parser.print_help()
        print("")
        sys.exit(255)

    if options.subparser is None:
        sys.stderr.write(
            "Error: %s\n" % str("too few arguments"))
        sys.stderr.flush()
        parser.print_help()
        print("")
        sys.exit(255)

    if not WRITERS:
        sys.stderr.write(
            "nxsfileinfo: Neither pnineuxs.h5cpp nor h5py installed\n")
        sys.stderr.flush()
        parser.print_help()
        sys.exit(255)

    runners[options.subparser].run(options)


if __name__ == "__main__":
    main()
