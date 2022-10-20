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

"""  pyeval helper functions for datasignal """

from nxstools import filewriter


def signalname(commonblock, detector, firstchannel,
               timers, mgchannels, entryname, defaultattrs=True):
    """ code for signalname  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param detector: detector name
    :type detector: :obj:`str`
    :param firstchannel: first mg channel
    :type firstchannel: :obj:`str`
    :param timers: a list of timers separated by space
    :type timers: :obj:`str`
    :param mgchannels: a list of mgchannels separated by space
    :type mgchannels: :obj:`str`
    :param entryname:  entry group name
    :type entryname: :obj:`str`
    :param defaultattrs:  set default attributes in NXentry and NXdata
    :type defaultattrs: :obj:`bool`
    :returns: signal name
    :rtype: :obj:`str`
    """

    result = ""
    try:
        timers = [ch for ch in str(timers).split(" ") if ch]
        mgchannels = [ch for ch in str(mgchannels).split(" ") if ch]
        root = commonblock["__root__"]
        if defaultattrs:
            attrs = root.attributes
            at = attrs.create("default", "string", overwrite=True)
            at.write(entryname)
            at.close()
        nxentry = root.open(entryname)
        if defaultattrs:
            attrs = nxentry.attributes
            at = attrs.create("default", "string", overwrite=True)
            at.write("data")
            at.close()
        nxdata = nxentry.open("data")
        writer = root.parent.writer
        links = writer.get_links(nxdata)
        names = list(sorted([ch.name for ch in links]))
        if detector in names:
            result = str(detector)
        elif firstchannel in names:
            result = str(firstchannel)
        elif mgchannels:
            for ch in mgchannels:
                if ch in names and ch not in timers:
                    result = str(ch)
                    break
        if not result:
            for name in names:
                fld = nxdata.open(name)
                if isinstance(fld, filewriter.FTField) and \
                   len(fld.shape) == 1 and fld.shape[0] > 1:
                    result = str(fld.name)
                    break
        if not result and names:
            result = str(names[0])
    except Exception as e:
        result = str(e)
    return result

def axesnames(commonblock, detector, firstchannel,
              timers, mgchannels, entryname, nexus_step_datasources):
    """ code for signalname  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param detector: detector name
    :type detector: :obj:`str`
    :param firstchannel: first mg channel
    :type firstchannel: :obj:`str`
    :param timers: a list of timers separated by space
    :type timers: :obj:`str`
    :param mgchannels: a list of mgchannels separated by space
    :type mgchannels: :obj:`str`
    :param entryname:  entry group name
    :type entryname: :obj:`str`
    :param mgchannels: a list of nexus_step_datasources
    :type mgchannels: :obj:`str`
    :returns: signal name
    :rtype: :obj:`str`
    """
    signal = signalname(
        commonblock, detector, firstchannel, timers, mgchannels, entryname,
        False)

    result = []
    try:
        timers = [ch for ch in str(timers).split(" ") if ch]
        stepdss = [
            ch for ch in str(nexus_step_datasources).split(" ") if ch]
        root = commonblock["__root__"]
        nxentry = root.open(entryname)
        nxdata = nxentry.open("data")
        writer = root.parent.writer
        links = writer.get_links(nxdata)
        names = list(sorted([ch.name for ch in links]))
        if signal != detector:
            dt = nxdata.open(signal)
            dtshape = dt.shape
            if len(dtshape) > 0 and dtshape[0] > 0:
                if stepdss and stepdss[0] in names:
                    ax = nxdata.open(stepdss[0])
                    if len(ax.shape) == 1 and ax.shape[0] == dtshape[0]:
                        result = [stepdss[0]]
            if result and len(dtshape) > 1 and dtshape[1] > 0:
                if len(stepdss) > 1  and stepdss[1] in names:
                    ax = nxdata.open(stepdss[1])
                    if len(ax.shape) == 1 and ax.shape[0] == dtshape[1]:
                        result.append(stepdss[1])
            if result:
                while len(dtshape) > len(result):
                    result.append(".")


    except Exception as e:
        result = str(e)
    return result
