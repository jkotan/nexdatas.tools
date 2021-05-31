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

"""  pyeval helper functions for limaccd """


def postrun(commonblock,
            saving_next_number,
            saving_directory,
            saving_suffix,
            acq_nb_frames,
            saving_format,
            saving_prefix,
            saving_next_number_str):
    """ code for postrun datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param saving_next_number: saving next number
    :type saving_next_number: :obj:`int`
    :param saving_directory: saving directory
    :type saving_directory: :obj:`str`
    :param saving_suffix: saving suffix
    :type saving_suffix: :obj:`str`
    :param acq_nb_frames: number of frames acquired
    :type acq_mb_frames: :obj:`str`
    :param saving_format: saving format
    :type saving_format: :obj:`str`
    :param saving_prefix: saving prefix
    :type saving_prefix: :obj:`str`
    :param saving_next_number_str: datasource string name
    :type saving_next_number_str: :obj:`str`
    :returns: name of saved file
    :rtype: :obj:`str`
    """
    unixdir = (saving_directory).replace("\\", "/")
    if len(unixdir) > 1 and unixdir[1] == ":":
        unixdir = "/data" + unixdir[2:]
    if unixdir and unixdir[-1] == "/":
        unixdir = unixdir[:-1]
    filestartnum = commonblock[saving_next_number_str] - 1
    result = "" + unixdir + "/" + saving_prefix + saving_format
    result += saving_suffix + ":"
    filelastnumber = saving_next_number - 1
    if "__root__" in commonblock.keys():
        root = commonblock["__root__"]
        if hasattr(root, "currentfileid") and hasattr(root, "stepsperfile"):
            spf = root.stepsperfile
            cfid = root.currentfileid
            if spf > 0 and cfid > 0:
                filelastnumber = min(
                    filestartnum + cfid * acq_nb_frames * spf - 1,
                    filelastnumber)
                filestartnum = filestartnum + (cfid - 1) * acq_nb_frames * spf
    result += str(filestartnum) + ":" + str(filelastnumber)
    return result
