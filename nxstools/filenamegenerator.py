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
## \package nexdatas nexdatas.tools
## \file nxscollect.py
# Command-line tool to merging NeXus files with other file-format images
#
""" Filename generator """


class FilenameGenerator(object):
    """Generate image file names

    (c) Copyright 2015 Eugen Wintersberger <eugen.wintersberger@gmail.com>
    (c) Copyright 2015 DESY
    This file is part of nx2img.

    nx2img is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    nx2img is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with nx2img.  If not, see <http://www.gnu.org/licenses/>.

    Generator class creating image file names.
    """
    def __init__(self, fname_template, start_index=0, stop_index=None):
        self.file_index = start_index
        self.file_template = fname_template
        self.stop_index = stop_index

    def __call__(self):
        # if self.stop_index is -1 we loop forever, otherwise we stop
        # when the current index exceeds self.stop_index
        while self.stop_index is None or self.file_index <= self.stop_index:
            filename = self.file_template % (self.file_index)
            self.file_index += 1
            yield filename

    @staticmethod
    def from_slice(file_template):
        """
        Static factory method to create a filename_generator instance
        from a sliced user input
        """

        (file_format, start_index_str, stop_index_str) = \
            file_template.split(":")
        stop_index = None
        if stop_index_str is not None:
            stop_index = long(stop_index_str)

        start_index = int(start_index_str)

        return FilenameGenerator(file_format, start_index, stop_index)
