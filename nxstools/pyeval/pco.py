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

"""  pyeval helper functions for pco """

import json


def postrun(commonblock,
            filestartnum,
            filedir,
            nbframes,
            filepostfix,
            fileprefix,
            filestartnum_str, fromzero=False):
    """ code for postrun  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param filestartnum:  file start number
    :type filestartnum: :obj:`int`
    :param filedir: file directorentry name
    :type filedir: :obj:`str`
    :param nbframes: number of frams
    :type nbframes: :obj:`int`
    :param filepostfix: file postfix
    :type filepostfix: :obj:`str`
    :param fileprefix: file prefix
    :type fileprefix: :obj:`str`
    :param filestartnum_str: filestartnum string
    :type filestartnum_str: :obj:`str`
    :returns: postrun string
    :rtype: :obj:`str`
    """
    unixdir = filedir.replace("\\", "/")
    if len(unixdir) > 1 and unixdir[1] == ":":
        unixdir = "/data" + unixdir[2:]
    if unixdir and unixdir[-1] == "/":
        unixdir = unixdir[:-1]
    if fromzero:
        filestartnumer = commonblock[filestartnum_str]
    else:
        filestartnumer = commonblock[filestartnum_str] - 1
    if fileprefix.endswith("_"):
        fileprefix = fileprefix[:-1]
    result = "" + unixdir + "/" + fileprefix + "_%05d."
    if filepostfix.startswith("."):
        filepostfix = filepostfix[1:]
    result += filepostfix + ":"
    if fromzero:
        filelastnumber = filestartnum
    else:
        filelastnumber = filestartnum - 1
    if "__root__" in commonblock.keys():
        root = commonblock["__root__"]
        if hasattr(root, "currentfileid") and hasattr(root, "stepsperfile"):
            spf = root.stepsperfile
            cfid = root.currentfileid
            if spf > 0 and cfid > 0:
                filelastnumber = min(
                    filestartnumer + cfid * nbframes * spf - 1, filelastnumber)
                filestartnum = filestartnumer + \
                    (cfid - 1) * nbframes * spf
    result += str(filestartnumer) + ":" + str(filelastnumber)
    return result


def triggermode_cb(commonblock,  name, triggermode, filename,
                   filestartnum, filedir, nbframes,
                   filepostfix, fileprefix, filestartnum_str,
                   entryname, insname, shape=None,
                   dtype="uint16", acq_modes=""):
    """ code for postrun  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param name: component name
    :type name: :obj:`str`
    :param triggermode:  trigger mode
    :type triggermode: :obj:`int` or :obj:`str`
    :param filename: file name
    :type filename: :obj:`str`
    :param filestartnum:  file start number
    :type filestartnum: :obj:`int`
    :param filedir: file directorentry name
    :type filedir: :obj:`str`
    :param nbframes: number of frams
    :type nbframes: :obj:`int`
    :param filepostfix: file postfix
    :type filepostfix: :obj:`str`
    :param fileprefix: file prefix
    :type fileprefix: :obj:`str`
    :param filestartnum_str: filestartnum string
    :type filestartnum_str: :obj:`str`
    :param entryname: entry name
    :type entryname: :obj:`str`
    :param insname: instrument name
    :type insname: :obj:`str`
    :param shape:  shape
    :type shape: [:obj:`int`, :obj:`int` ]
    :param dtype: NeXus image data type
    :type dtype: :obj:`str`
    :param acq_modes: acquisition modes
    :type acq_modes: :obj:`str`
    :returns: postrun string
    :rtype: :obj:`str`
    """
    result = triggermode.lower()
    amodes = acq_modes.split(",")

    if filename:
        sfname = (filename).split("/")
        path = sfname[-1].split(".")[0] + "/"

    path += '%s/' % (name)

    # unixdir = filedir.replace("\\", "/")
    # if len(unixdir) > 1 and unixdir[1] == ":":
    #     unixdir = "/data" + unixdir[2:]
    # if unixdir and unixdir[-1] == "/":
    #     unixdir = unixdir[:-1]

    filestartnumer = commonblock[filestartnum_str]
    if filepostfix.startswith("."):
        filepostfix = filepostfix[1:]
    if fileprefix.endswith("_"):
        fileprefix = fileprefix[:-1]
    flpattern = "" + path + fileprefix + "_%05d." + filepostfix
    filelastnumber = filestartnum

    filepattern = flpattern
    grouppattern = fileprefix + "_%05d"

    # flpattern += ":" + str(filestartnumer) + ":" + str(filelastnumber)

    nbfiles = filelastnumber - filestartnum + 1
    if "__root__" in commonblock.keys():
        root = commonblock["__root__"]
        if hasattr(root, "currentfileid") and hasattr(root, "stepsperfile"):
            spf = root.stepsperfile
            cfid = root.currentfileid
        if root.h5object.__class__.__name__ == "File":
            import nxstools.h5pywriter as nxw
        else:
            import nxstools.h5cppwriter as nxw
    else:
        raise Exception("Writer cannot be found")
    en = root.open(entryname)
    dt = en.open("data")
    ins = en.open(insname)
    det = ins.open(name)
    col = det.open("collection")
    npath = "/entry/instrument/detector/data"
    for nbf in range(filestartnumer, filestartnumer + nbfiles):
        fnbf = filepattern % nbf
        gnbf = grouppattern % nbf
        if spf > 0 and cfid > 0:
            if cfid == nbf:
                nxw.link("%s:/%s" % (fnbf, npath), det, "data")
                nxw.link("/%s/%s/%s/data" % (entryname, insname, name),
                         dt, name)
            nxw.link("%s:/%s" % (fnbf, npath), col, "%s" % (gnbf))
        else:
            nxw.link("%s:/%s" % (fnbf, npath), col, "%s" % (gnbf))
            nxw.link("/%s/%s/%s/collection/%s" %
                     (entryname, insname, name, gnbf), dt,
                     "%s_%s" % (name, nbf))

    # create VDS field
    if shape and not isinstance(shape, list):
        try:
            shape = json.loads(shape)
        except Exception:
            shape = []
    if not shape or len(shape) < 2:
        return result

    if "VDS" in amodes and "data" not in det.names():

        totalframenumbers = nbfiles * nbframes

        vfl = nxw.virtual_field_layout(
            [totalframenumbers, shape[0], shape[1]], dtype)
        for nbf in range(filestartnumer, filestartnumer + nbfiles):
            fnm = filepattern % nbf
            gnbf = grouppattern % nbf
            ef = nxw.target_field_view(
                fnm, npath, [nbframes, shape[0], shape[1]], dtype)
            off = nbf * nbframes
            vfl.add(
                (slice(off, off + nbframes),
                 slice(0, shape[0]), slice(0, shape[1])),
                ef,
                (slice(None), slice(None), slice(None)))

        if "data" not in det.names():
            det.create_virtual_field("data", vfl)
        if name not in dt.names():
            nxw.link("/%s/%s/%s/data" % (entryname, insname, name),
                     dt, name)

    return result
