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
    from . import pniwriter
    WRITERS["pni"] = pniwriter
except Exception:
    pass

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
        """
        self.__nexusfilename = nexusfilename
        self.__compression = compression
        self.__skipmissing = skipmissing
        self.__testmode = testmode
        self.__storeold = storeold
        self.__tempfilename = None
        self.__filepattern = re.compile("[^:]+:\\d+:\\d+")
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

            fl = open(filename, "rb")
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

    def _loadh5data(self, filename):
        """ loads image from hdf5 file

        :param filename: hdf5 image file name
        :type filename: :obj:`str`
        :returns: (image data, image data type, image shape)
        :rtype: (:class:`numpy.ndarray`, :obj:`str`, :obj:`list` <:obj:`int`>)
        """
        try:
            dtype = None
            shape = None
            nxsfile = filewriter.open_file(
                filename, readonly=True, writer=self.__wrmodule)
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
        :type node: :class:`pni.io.nx.h5.nxgroup` or \
                    :class:`pni.io.nx.h5.nxlink`
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
        :rtype: :class:`pni.io.nx.h5.nxfield`
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
                field = node.create_field(
                    fieldname,
                    dtype,
                    shape=[0, shape[0], shape[1]],
                    chunk=[1, shape[0], shape[1]],
                    dfilter=cfilter)
                self._addattr(field, fieldattrs)
            return field

    def _collectimages(self, files, node, fieldname=None, fieldattrs=None,
                       fieldcompression=None, datatype=None, shape=None):
        """ collects images

        :param files: a list of file strings
        :type files: :obj:`list` <:obj:`str`>
        :param node: hdf5 parent node
        :type node: :class:`pni.io.nx.h5.nxgroup` or \
                    :class:`pni.io.nx.h5.nxlink`
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
                fname = self._findfile(fname, node.name)
                if not fname:
                    continue
                if datatype:
                    data, dtype, shape = self._loadrawimage(
                        fname, datatype, shape)
                elif not fname.endswith(".h5"):
                    data, dtype, shape = self._loadimage(fname)
                else:
                    data, dtype, shape = self._loadh5data(fname)
                if data is not None:
                    if field is None:
                        field = self._getfield(
                            node, fieldname, dtype, shape,
                            fieldattrs, fieldcompression)

                    if field and ind == field.shape[0]:
                        if not self.__testmode:
                            field.grow(0, 1)
                            field[-1, ...] = data
                        print(" * append %s " % (fname))
                    ind += 1
                    if not self.__testmode:
                        self.__nxsfile.flush()

    def _inspect(self, parent, collection=False):
        """ collects recursively the all image files defined
        by hdf5 postrun fields bellow hdf5 parent node

        :param parent: hdf5 parent node
        :type parent: :class:`pni.io.nx.h5.nxgroup` or \
                      :class:`pni.io.nx.h5.nxlink`
        :param collection: if parent is of NXcollection type
        :type collection: :obj:`bool`
        """
        if hasattr(parent, "names"):
            if collection:
                if "postrun" in parent.names():
                    inputfiles = parent.open("postrun")
                    files = inputfiles[...]
                    if isinstance(files, (str, unicode)):
                        files = [files]
                    fieldname = "data"
                    fielddtype = None
                    fieldshape = None
                    fieldattrs = {}
                    fieldcompression = None
                    for at in inputfiles.attributes:
                        if at.name == "fieldname":
                            fieldname = at[...]
                        elif at.name == "fieldcompression":
                            fieldcompression = at[...]
                        elif at.name == "fielddtype":
                            fielddtype = at[...]
                        elif at.name == "fieldshape":
                            fieldshape = json.loads(at[...])
                        elif at.name.startswith("fieldattr_"):
                            atname = at.name[10:]
                            if atname:
                                fieldattrs[atname] = (
                                    at[...], at.dtype, at.shape
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
                            gtype = at[...]
                            if gtype == 'NXcollection':
                                coll = True
                    self._inspect(child, coll)

    def collect(self):
        """ creates a temporary file,
        collects the all image files defined by hdf5
        postrun fields of NXcollection groups and renames the temporary file
        to the origin one if the action was successful
        """
        self._createtmpfile()
        try:
            self.__nxsfile = filewriter.open_file(
                self.__tempfilename, readonly=self.__testmode,
                writer=self.__wrmodule)
            root = self.__nxsfile.root()
            try:
                self.__fullfilename = root.attributes['file_name'][...]
                # print self.__fullfilename
            except Exception:
                pass
            self._inspect(root)
            self.__nxsfile.close()
            if self.__storeold:
                self._storeoldfile()
            shutil.move(self.__tempfilename, self.__nexusfilename)
        except Exception as e:
            print(str(e))
            os.remove(self.__tempfilename)


class Execute(Runner):

    """ Execute runner
    """

    #: (:obj:`str`) command description
    description = "execute the collection process"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxscollect execute -c1 /tmp/gpfs/raw/scan_234.nxs \n\n" \
        + "       nxscollect execute -c32008:0,2 /ramdisk/scan_123.nxs \n\n" \
        + "\n"

    def create(self):
        """ creates parser
        """
        parser = self._parser
        parser.add_argument(
            "-c", "--compression", dest="compression",
            action="store", type=str, default=2,
            help="deflate compression rate from 0 to 9 (default: 2)"
            " or <filterid>:opt1,opt2,..."
            " e.g.  -c 32008:0,2  for bitshuffle with lz4")
        parser.add_argument(
            "-s", "--skip_missing", action="store_true",
            default=False, dest="skipmissing",
            help="skip missing files")
        parser.add_argument(
            "-r", "--replace_nexus_file", action="store_true",
            default=False, dest="replaceold",
            help="if it is set the old file is not copied into "
            "a file with .__nxscollect__old__* extension")
        parser.add_argument(
            "--pni", action="store_true",
            default=False, dest="pni",
            help="use pni module as a nexus reader/writer")
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
        elif options.pni:
            writer = "pni"
        elif "h5cpp" in WRITERS.keys():
            writer = "h5cpp"
        elif "h5py" in WRITERS.keys():
            writer = "h5py"
        else:
            writer = "pni"
        if (options.pni and options.h5py and options.h5cpp) or \
           writer not in WRITERS.keys():
            sys.stderr.write("nxscollect: Writer '%s' cannot be opened\n"
                             % writer)
            sys.stderr.flush()
            parser.print_help()
            sys.exit(255)

        # configuration server
        for nxsfile in nexusfiles:
            collector = Collector(
                nxsfile, options.compression, options.skipmissing,
                not options.replaceold, False, writer=writer)
            collector.collect()


class Test(Execute):

    """ Test runner"""

    #: (:obj:`str`) command description
    description = "execute the process in the test mode " \
                  + "without changing any files"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxscollect test /tmp/gpfs/raw/scan_234.nxs \n\n" \
        + "\n"

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
        elif options.pni:
            writer = "pni"
        elif "h5cpp" in WRITERS.keys():
            writer = "h5cpp"
        elif "h5py" in WRITERS.keys():
            writer = "h5py"
        else:
            writer = "pni"
        if (options.pni and options.h5py and options.h5cpp) or \
           writer not in WRITERS.keys():
            sys.stderr.write("nxscollect: Writer '%s' cannot be opened\n"
                             % writer)
            parser.print_help()
            sys.exit(255)

        # configuration server
        for nxsfile in nexusfiles:
            collector = Collector(
                nxsfile, options.compression, options.skipmissing,
                not options.replaceold, True, writer=writer)
            collector.collect()


def _supportoldcommands():
    """ replace the old command names to the new ones
    """

    oldnew = {
        '-x': 'execute',
        '--execute': 'execute',
        '-t': 'test',
        '--test': 'test',
    }

    if sys.argv and len(sys.argv) > 1:
        if sys.argv[1] in oldnew.keys():
            sys.argv[1] = oldnew[sys.argv[1]]


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
        ('execute', Execute),
        ('test', Test)
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
        sys.stderr.write("nxsfileinfo: Neither h5cpp/pni nor h5py installed\n")
        sys.stderr.flush()
        parser.print_help()
        sys.exit(255)

    runners[options.subparser].run(options)


if __name__ == "__main__":
    main()
