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

"""  pyeval helper functions for lambdavds """

try:
    import tango
except Exception:
    import PyTango as tango


def triggermode_cb(commonblock, name, triggermode,
                   nbimages, hostname, device,
                   filename, stepindex_str, entryname, insname,
                   eigerdectris_str="EigerDectris",
                   eigerfilewriter_str="EigerFileWriter"):
    """ code for triggermode_cb  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param name: component name
    :type name: :obj:`str`
    :param triggermode:  trigger mode
    :type triggermode: :obj:`int` or :obj:`str`
    :param nbimages: a number of images
    :type nbimages: :obj:`int`
    :param hostname: tango host name
    :type hostname: :obj:`str`
    :param device: tango device name
    :type device: :obj:`str`
    :param filename: file name
    :type filename: :obj:`str`
    :param stepindex_str: name of stepindex datasource
    :type stepindex_str: :obj:`str`
    :param entryname: entry name
    :type entryname: :obj:`str`
    :param insname: instrument name
    :type insname: :obj:`str`
    :param eigerdectris_str: eigerdectris string
    :type eigerdectris_str: :obj:`str`
    :param eigerfilewriter_str: eigerwriter string
    :type eigerfilewriter_str: :obj:`str`
    :returns: triggermode
    :rtype: :obj:`str` or :obj:`int`
    """

    host, port = hostname.split(":")
    port = int(port or 10000)
    edb = tango.Database(host, port)

    sl = edb.get_server_list("%s/*" % (eigerdectris_str))
    writer = None
    for ms in sl:
        devserv = edb.get_device_class_list(ms).value_string
        if device in devserv:
            dev = devserv[0::2]
            serv = devserv[1::2]
            for idx, ser in enumerate(serv):
                if ser == eigerfilewriter_str:
                    writer = dev[idx]
                    break
    wp = tango.DeviceProxy('%s/%s' % (hostname, writer))
    filepattern = wp.FilenamePattern.split("/")[-1]
    imagesperfile = wp.ImagesPerFile
    if filename:
        path = (filename).split("/")[-1].split(".")[0] + "/"
    else:
        path = ""
    path += '%s/%s_' % (name, filepattern)
    totnbimages = sum(commonblock[stepindex_str])
    nbfiles = (totnbimages + imagesperfile - 1) // imagesperfile
    result = triggermode.lower()
    spf = 0
    cfid = 0
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
        raise("Writer cannot be found")
    en = root.open(entryname)
    dt = en.open("data")
    ins = en.open(insname)
    det = ins.open(name)
    col = det.open("collection")
    for nbf in range(1, nbfiles+1):
        if spf > 0 and cfid > 0:
            if cfid == nbf:
                nxw.link("%sdata_%06i.h5://entry/data/data" % (path, nbf),
                         det, "data")
                nxw.link("/%s/%s/%s/data" % (entryname, insname, name),
                         dt, name)
            nxw.link("%sdata_%06i.h5://entry/data/data" % (path, nbf),
                     col, "data_%06i" % nbf)
        else:
            nxw.link("%sdata_%06i.h5://entry/data/data" % (path, nbf),
                     col, "data_%06i" % nbf)
            nxw.link("/%s/%s/%s/collection/data_%06i" %
                     (entryname, insname, name, nbf), dt,
                     "%s_%06i" % (name, nbf))
    return result
