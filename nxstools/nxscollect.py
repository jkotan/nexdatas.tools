#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2016 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
from optparse import OptionParser
from pni.io.nx.h5 import open_file, deflate_filter
from .filenamegenerator import FilenameGenerator


class Collector(object):
    """ Collector merge images of external file-formats
    into the master NeXus file
    """
    def __init__(self, nexusfilename, compression=2,
                 skipmissing=False, storeold=False, testmode=False):
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
            print ("terminated by %s" % self.__siginfo[sig])

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
            nxsfile = open_file(filename, readonly=True)
            root = nxsfile.root()
            image = root.open("data")
            idata = image.read()
            nxsfile.close()
            if image:
                idata = image[...]
                dtype = image.dtype
                shape = image.shape
            nxsfile.close()
            return idata, dtype, shape
        except Exception:
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
            print " + add attribute: %s = %s" % (name, value)

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
            return node[fieldname]
        else:
            if not self.__testmode:
                cfilter = None
                if fieldcompression:
                    cfilter = deflate_filter()
                    cfilter.rate = fieldcompression
                    field = node.create_field(
                        fieldname,
                        dtype,
                        shape=[0, shape[0], shape[1]],
                        chunk=[1, shape[0], shape[1]],
                        filter=cfilter)
            self._addattr(field, fieldattrs)
            return field

    def _collectimages(self, files, node, fieldname=None, fieldattrs=None,
                       fieldcompression=None):
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
                if not fname.endswith(".h5"):
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
                        print " * append %s " % (fname)
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
                    fieldattrs = {}
                    fieldcompression = None
                    for at in inputfiles.attributes:
                        if at.name == "fieldname":
                            fieldname = at[...]
                        elif at.name == "fieldcompression":
                            fieldcompression = int(at[...])
                        elif at.name.startswith("fieldattr_"):
                            atname = at.name[10:]
                            if atname:
                                fieldattrs[atname] = (
                                    at[...], at.dtype, at.shape
                                )

                    print "populate: %s/%s with %s" % (
                        parent.parent.path, fieldname, files)
                    if fieldcompression is None:
                        fieldcompression = self.__compression
                    self._collectimages(
                        files, parent.parent, fieldname, fieldattrs,
                        fieldcompression)
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
            self.__nxsfile = open_file(
                self.__tempfilename, readonly=self.__testmode)
            root = self.__nxsfile.root()
            try:
                self.__fullfilename = root.attributes['file_name'][...]
                # print self.__fullfilename
            except:
                pass
            self._inspect(root)
            self.__nxsfile.close()
            if self.__storeold:
                self._storeoldfile()
            shutil.move(self.__tempfilename, self.__nexusfilename)
        except Exception as e:
            print str(e)
            os.remove(self.__tempfilename)


def _createParser():
    """ creates command-line parameters parser

    :returns: option parser
    :rtype: :class:`optparse.OptionParser`
    """
    #: (:obj:`str`) usage example
    usage = "usage: \n" \
            + " nxscollect [-x|-t] [<options>] <command> <main_nexus_file> \n" \
            + " e.g.: nxscollect -x -c1 /tmp/gpfs/raw/scan_234.nxs \n\n" \
            + " "

    #: (:class:`optparse.OptionParser`) option parser
    parser = OptionParser(usage=usage)
    parser.add_option("-x", "--execute", action="store_true",
                      default=False, dest="execute",
                      help="execute the collection process")
    parser.add_option("-t", "--test", action="store_true",
                      default=False, dest="test",
                      help="execute the process in the test mode "
                      + "without changing any files")
    parser.add_option("-c", "--compression", dest="compression",
                      action="store", type=int, default=2,
                      help="deflate compression rate from 0 to 9 (default: 2)")
    parser.add_option("-s", "--skip_missing", action="store_true",
                      default=False, dest="skipmissing",
                      help="skip missing files")
    parser.add_option("-r", "--replace_nexus_file", action="store_true",
                      default=False, dest="replaceold",
                      help="if it is set the old file is not copied into "
                      "a file with .__nxscollect__old__* extension")

    return parser


def main():
    """ the main program function
    """

    #: run options
    options = None
    parser = _createParser()
    (options, nexusfiles) = parser.parse_args()

    if not nexusfiles or not nexusfiles[0]:
        parser.print_help()
        print ""
        sys.exit(0)

    if not options.execute and not options.test:
        parser.print_help()
        print ""
        sys.exit(0)

    # configuration server
    for nxsfile in nexusfiles:
        collector = Collector(nxsfile,
                              options.compression,
                              options.skipmissing,
                              not options.replaceold,
                              options.test)
        collector.collect()

if __name__ == "__main__":
    main()
