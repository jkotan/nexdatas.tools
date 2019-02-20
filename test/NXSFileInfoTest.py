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
# \package test nexdatas
# \file XMLConfiguratorTest.py
# unittests for field Tags running Tango Server
#
import unittest
import os
import sys
import random
import struct
import binascii
import shutil
import fabio
import numpy as np
# import time
# import threading
# import PyTango
import json
from nxstools import nxsfileinfo
from nxstools import filewriter

# import datetime
import docutils.parsers.rst
import docutils.utils
# import dateutil.parser


try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


if sys.version_info > (3,):
    unicode = str
    long = int

WRITERS = {}
try:
    from nxstools import pniwriter
    WRITERS["pni"] = pniwriter
except Exception:
    pass

try:
    from nxstools import h5pywriter
    WRITERS["h5py"] = h5pywriter
except Exception:
    pass

try:
    from nxstools import h5cppwriter
    WRITERS["h5cpp"] = h5cppwriter
except Exception:
    pass


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

# from nxsconfigserver.XMLConfigurator  import XMLConfigurator
# from nxsconfigserver.Merger import Merger
# from nxsconfigserver.Errors import (
# NonregisteredDBRecordError, UndefinedTagError,
#                                    IncompatibleNodeError)
# import nxsconfigserver


def myinput(w, text):
    myio = os.fdopen(w, 'w')
    myio.write(text)

    # myio.close()


# test fixture
class NXSFileInfoTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self.helperror = "Error: too few arguments\n"

        self.helpinfo = """usage: nxsfileinfo [-h] {field,general} ...

Command-line tool for showing meta data from Nexus Files

positional arguments:
  {field,general}  sub-command help
    field          show field information for the nexus file
    general        show general information for the nexus file

optional arguments:
  -h, --help       show this help message and exit

For more help:
  nxsfileinfo <sub-command> -h

"""

        try:
            # random seed
            self.seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            import time
            # random seed
            self.seed = long(time.time() * 256)  # use fractional seconds

        self.__rnd = random.Random(self.seed)

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        if "h5cpp" in WRITERS.keys():
            self.writer = "h5cpp"
        elif "h5py" in WRITERS.keys():
            self.writer = "h5py"
        else:
            self.writer = "pni"

        self.flags = ""

    # test starter
    # \brief Common set up
    def setUp(self):
        print("\nsetting up...")
        print("SEED = %s" % self.seed)

    # test closer
    # \brief Common tear down
    def tearDown(self):
        print("tearing down ...")

    # Exception tester
    # \param exception expected exception
    # \param method called method
    # \param args list with method arguments
    # \param kwargs dictionary with method arguments
    def myAssertRaise(self, exception, method, *args, **kwargs):
        try:
            error = False
            method(*args, **kwargs)
        except exception:
            error = True
        self.assertEqual(error, True)

    def checkGroupRow(self, row, gname):
        self.assertEqual(len(row), 3)
        self.assertEqual(row.tagname, "row")
        self.assertEqual(len(row[0]), 1)
        self.assertEqual(row[0].tagname, "entry")
        self.assertEqual(len(row[0][0]), 1)
        self.assertEqual(row[0][0].tagname, "paragraph")
        self.assertEqual(str(row[0][0][0]), gname)
        self.assertEqual(len(row[1]), 0)
        self.assertEqual(str(row[1]), '<entry/>')
        self.assertEqual(len(row[2]), 0)
        self.assertEqual(str(row[2]), '<entry/>')

    def checkFieldRow(self, row, fname, ftype, fshape):
        self.assertEqual(len(row), 3)
        self.assertEqual(row.tagname, "row")
        self.assertEqual(len(row[0]), 1)
        self.assertEqual(row[0].tagname, "entry")
        self.assertEqual(len(row[0][0]), 1)
        self.assertEqual(row[0][0].tagname, "paragraph")
        self.assertEqual(str(row[0][0][0]), fname)
        self.assertEqual(len(row[1]), 1)
        self.assertEqual(row[1].tagname, 'entry')
        self.assertEqual(row[1][0].tagname, 'paragraph')
        self.assertEqual(len(row[1][0]), 1)
        self.assertEqual(str(row[1][0][0]), ftype)
        self.assertEqual(row[2][0].tagname, 'paragraph')
        self.assertEqual(len(row[2][0]), 1)
        self.assertEqual(str(row[2][0][0]), fshape)

    def test_default(self):
        """ test nxsconfig default
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = mystdout = StringIO()
        sys.stderr = mystderr = StringIO()
        old_argv = sys.argv
        sys.argv = ['nxsfileinfo']
        with self.assertRaises(SystemExit):
            nxsfileinfo.main()

        sys.argv = old_argv
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        vl = mystdout.getvalue()
        er = mystderr.getvalue()
        self.assertEqual(self.helpinfo, vl)
        self.assertEqual(self.helperror, er)

    def test_help(self):
        """ test nxsconfig help
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        helps = ['-h', '--help']
        for hl in helps:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = ['nxsfileinfo', hl]
            with self.assertRaises(SystemExit):
                nxsfileinfo.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue()
            er = mystderr.getvalue()
            self.assertEqual(self.helpinfo[0:-1], vl)
            self.assertEqual('', er)

    def test_general_emptyfile(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'

        commands = [
            ('nxsfileinfo general %s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:
            nxsfile = filewriter.create_file(filename, overwrite=True)
            nxsfile.close()

            for cmd in commands:
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertEqual('\n', vl)

        finally:
            os.remove(filename)

    def test_field_emptyfile(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'

        commands = [
            ('nxsfileinfo field %s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:
            nxsfile = filewriter.create_file(filename, overwrite=True)
            nxsfile.close()

            for cmd in commands:
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertEqual(
                    "\nFile name: 'testfileinfo.nxs'\n"
                    "-----------------------------\n\n"
                    "========== \n"
                    "nexus_path \n"
                    "========== \n/\n"
                    "========== \n\n",
                    vl)

                parser = docutils.parsers.rst.Parser()
                components = (docutils.parsers.rst.Parser,)
                settings = docutils.frontend.OptionParser(
                    components=components).get_default_values()
                document = docutils.utils.new_document(
                    '<rst-doc>', settings=settings)
                parser.parse(vl, document)
                self.assertEqual(len(document), 1)
                section = document[0]
                self.assertEqual(len(section), 2)
                self.assertEqual(len(section[0]), 1)
                self.assertEqual(
                    str(section[0]),
                    "<title>File name: 'testfileinfo.nxs'</title>")
                self.assertEqual(len(section[1]), 3)
                self.assertEqual(len(section[1][0]), 1)
                self.assertEqual(
                    str(section[1][0]), '<title>nexus_path</title>')
                self.assertEqual(len(section[1][1]), 1)
                self.assertEqual(
                    str(section[1][1]),
                    '<system_message level="1" line="8" source="<rst-doc>" '
                    'type="INFO">'
                    '<paragraph>Possible incomplete section title.\n'
                    'Treating the overline as ordinary text '
                    'because it\'s so short.</paragraph></system_message>')
                self.assertEqual(len(section[1][2]), 1)
                self.assertEqual(
                    str(section[1][2]),
                    '<section ids="id1" names="/"><title>/</title></section>')
        finally:
            os.remove(filename)

    def test_field_emptyfile_geometry_source(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'

        commands = [
            ('nxsfileinfo field -g %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo field --geometry %s %s'
             % (filename, self.flags)).split(),
            ('nxsfileinfo field -s %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo field --source %s %s'
             % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:
            nxsfile = filewriter.create_file(filename, overwrite=True)
            nxsfile.close()

            for cmd in commands:
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)

                parser = docutils.parsers.rst.Parser()
                components = (docutils.parsers.rst.Parser,)
                settings = docutils.frontend.OptionParser(
                    components=components).get_default_values()
                document = docutils.utils.new_document(
                    '<rst-doc>', settings=settings)
                parser.parse(vl, document)
                self.assertEqual(len(document), 1)
                section = document[0]
                self.assertEqual(len(section), 1)
                self.assertEqual(len(section[0]), 1)
                self.assertEqual(
                    str(section[0]),
                    "<title>File name: 'testfileinfo.nxs'</title>")
        finally:
            os.remove(filename)

    def test_general_simplefile_nodata(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'

        commands = [
            ('nxsfileinfo general %s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:
            nxsfile = filewriter.create_file(filename, overwrite=True)
            rt = nxsfile.root()
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            entry.create_group("data", "NXdata")
            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            nxsfile.close()

            for cmd in commands:
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual(
                    'nxsfileinfo: title cannot be found\n'
                    'nxsfileinfo: experiment identifier cannot be found\n'
                    'nxsfileinfo: instrument name cannot be found\n'
                    'nxsfileinfo: instrument short name cannot be found\n'
                    'nxsfileinfo: start time cannot be found\n'
                    'nxsfileinfo: end time cannot be found\n', er)
                parser = docutils.parsers.rst.Parser()
                components = (docutils.parsers.rst.Parser,)
                settings = docutils.frontend.OptionParser(
                    components=components).get_default_values()
                document = docutils.utils.new_document(
                    '<rst-doc>', settings=settings)
                parser.parse(vl, document)
                self.assertEqual(len(document), 1)
                section = document[0]
                self.assertEqual(len(section), 1)
                self.assertTrue(
                    "File name: 'testfileinfo.nxs'" in str(section[0]))

        finally:
            os.remove(filename)

    def test_general_simplefile_metadata(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                "ttestfileinfo.nxs",
                "Test experiment",
                "BL1234554",
                "PETRA III",
                "P3",
                "2014-02-12T15:19:21+00:00",
                "2014-02-15T15:17:21+00:00",
                "water",
                "H20",
            ],
            [
                "mmyfileinfo.nxs",
                "My experiment",
                "BT123_ADSAD",
                "Petra III",
                "PIII",
                "2019-02-14T15:19:21+00:00",
                "2019-02-15T15:27:21+00:00",
                "test sample",
                "LaB6",
            ],
            [
                "mmytestfileinfo.nxs",
                "Super experiment",
                "BT12sdf3_ADSAD",
                "HASYLAB",
                "HL",
                "2019-01-14T15:19:21+00:00",
                "2019-01-15T15:27:21+00:00",
                "my sample",
                "LaB6",
            ],
        ]

        for arg in args:
            filename = arg[0]
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]

            commands = [
                ('nxsfileinfo general %s %s' % (filename, self.flags)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("detector", "NXdetector")
                entry.create_group("data", "NXdata")
                sample = entry.create_group("sample", "NXsample")
                det.create_field("intimage", "uint32", [0, 30], [1, 30])

                entry.create_field("title", "string").write(title)
                entry.create_field(
                    "experiment_identifier", "string").write(beamtime)
                entry.create_field("start_time", "string").write(stime)
                entry.create_field("end_time", "string").write(etime)
                sname = ins.create_field("name", "string")
                sname.write(insname)
                sattr = sname.attributes.create("short_name", "string")
                sattr.write(inssname)
                sname = sample.create_field("name", "string")
                sname.write(smpl)
                sfml = sample.create_field("chemical_formula", "string")
                sfml.write(formula)

                nxsfile.close()

                for cmd in commands:
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    sys.stdout = mystdout = StringIO()
                    sys.stderr = mystderr = StringIO()
                    old_argv = sys.argv
                    sys.argv = cmd
                    nxsfileinfo.main()

                    sys.argv = old_argv
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    vl = mystdout.getvalue()
                    er = mystderr.getvalue()

                    self.assertEqual('', er)
                    parser = docutils.parsers.rst.Parser()
                    components = (docutils.parsers.rst.Parser,)
                    settings = docutils.frontend.OptionParser(
                        components=components).get_default_values()
                    document = docutils.utils.new_document(
                        '<rst-doc>', settings=settings)
                    parser.parse(vl, document)
                    self.assertEqual(len(document), 1)
                    section = document[0]
                    self.assertEqual(len(section), 2)
                    self.assertEqual(len(section[0]), 1)
                    self.assertEqual(
                        str(section[0]),
                        "<title>File name: '%s'</title>" % filename)
                    self.assertEqual(len(section[1]), 1)
                    table = section[1]
                    self.assertEqual(table.tagname, 'table')
                    self.assertEqual(len(table), 1)
                    self.assertEqual(table[0].tagname, 'tgroup')
                    self.assertEqual(len(table[0]), 4)
                    for i in range(2):
                        self.assertEqual(table[0][i].tagname, 'colspec')
                    self.assertEqual(table[0][2].tagname, 'thead')
                    self.assertEqual(
                        str(table[0][2]),
                        '<thead><row>'
                        '<entry><paragraph>Scan entry:</paragraph></entry>'
                        '<entry><paragraph>entry12345</paragraph></entry>'
                        '</row></thead>'
                    )
                    tbody = table[0][3]
                    self.assertEqual(tbody.tagname, 'tbody')
                    self.assertEqual(len(tbody), 8)
                    self.assertEqual(len(tbody[0]), 2)
                    self.assertEqual(len(tbody[0][0]), 1)
                    self.assertEqual(len(tbody[0][0][0]), 1)
                    self.assertEqual(str(tbody[0][0][0][0]), "Title:")
                    self.assertEqual(len(tbody[0][1]), 1)
                    self.assertEqual(len(tbody[0][1][0]), 1)
                    self.assertEqual(str(tbody[0][1][0][0]), title)

                    self.assertEqual(len(tbody[1]), 2)
                    self.assertEqual(len(tbody[1][0]), 1)
                    self.assertEqual(len(tbody[1][0][0]), 1)
                    self.assertEqual(str(tbody[1][0][0][0]),
                                     "Experiment identifier:")
                    self.assertEqual(len(tbody[1][1]), 1)
                    self.assertEqual(len(tbody[1][1][0]), 1)
                    self.assertEqual(str(tbody[1][1][0][0]), beamtime)

                    self.assertEqual(len(tbody[2]), 2)
                    self.assertEqual(len(tbody[2][0]), 1)
                    self.assertEqual(len(tbody[2][0][0]), 1)
                    self.assertEqual(str(tbody[2][0][0][0]),
                                     "Instrument name:")
                    self.assertEqual(len(tbody[2][1]), 1)
                    self.assertEqual(len(tbody[2][1][0]), 1)
                    self.assertEqual(str(tbody[2][1][0][0]), insname)

                    self.assertEqual(len(tbody[3]), 2)
                    self.assertEqual(len(tbody[3][0]), 1)
                    self.assertEqual(len(tbody[3][0][0]), 1)
                    self.assertEqual(str(tbody[3][0][0][0]),
                                     "Instrument short name:")
                    self.assertEqual(len(tbody[3][1]), 1)
                    self.assertEqual(len(tbody[3][1][0]), 1)
                    self.assertEqual(str(tbody[3][1][0][0]), inssname)

                    self.assertEqual(len(tbody[4]), 2)
                    self.assertEqual(len(tbody[4][0]), 1)
                    self.assertEqual(len(tbody[4][0][0]), 1)
                    self.assertEqual(str(tbody[4][0][0][0]),
                                     "Sample name:")
                    self.assertEqual(len(tbody[4][1]), 1)
                    self.assertEqual(len(tbody[4][1][0]), 1)
                    self.assertEqual(str(tbody[4][1][0][0]), smpl)

                    self.assertEqual(len(tbody[5]), 2)
                    self.assertEqual(len(tbody[5][0]), 1)
                    self.assertEqual(len(tbody[5][0][0]), 1)
                    self.assertEqual(str(tbody[5][0][0][0]),
                                     "Sample formula:")
                    self.assertEqual(len(tbody[5][1]), 1)
                    self.assertEqual(len(tbody[5][1][0]), 1)
                    self.assertEqual(str(tbody[5][1][0][0]), formula)

                    self.assertEqual(len(tbody[6]), 2)
                    self.assertEqual(len(tbody[6][0]), 1)
                    self.assertEqual(len(tbody[6][0][0]), 1)
                    self.assertEqual(str(tbody[6][0][0][0]),
                                     "Start time:")
                    self.assertEqual(len(tbody[6][1]), 1)
                    self.assertEqual(len(tbody[6][1][0]), 1)
                    self.assertEqual(str(tbody[6][1][0][0]), stime)

                    self.assertEqual(len(tbody[7]), 2)
                    self.assertEqual(len(tbody[7][0]), 1)
                    self.assertEqual(len(tbody[7][0][0]), 1)
                    self.assertEqual(str(tbody[7][0][0][0]),
                                     "End time:")
                    self.assertEqual(len(tbody[7][1]), 1)
                    self.assertEqual(len(tbody[7][1][0]), 1)
                    self.assertEqual(str(tbody[7][1][0][0]), etime)

            finally:
                os.remove(filename)

    def test_field_nodata(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                "ttestfileinfo.nxs",
                "Test experiment",
                "BL1234554",
                "PETRA III",
                "P3",
                "2014-02-12T15:19:21+00:00",
                "2014-02-15T15:17:21+00:00",
                "water",
                "H20",
                "int",
                ""
            ],
            [
                "mmyfileinfo.nxs",
                "My experiment",
                "BT123_ADSAD",
                "Petra III",
                "PIII",
                "2019-02-14T15:19:21+00:00",
                "2019-02-15T15:27:21+00:00",
                "test sample",
                "LaB6",

            ],
        ]

        for arg in args:
            filename = arg[0]
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]

            commands = [
                ('nxsfileinfo field %s %s' % (filename, self.flags)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("detector", "NXdetector")
                entry.create_group("data", "NXdata")
                sample = entry.create_group("sample", "NXsample")
                det.create_field("intimage", "uint32", [0, 30], [1, 30])

                entry.create_field("title", "string").write(title)
                entry.create_field(
                    "experiment_identifier", "string").write(beamtime)
                entry.create_field("start_time", "string").write(stime)
                entry.create_field("end_time", "string").write(etime)
                sname = ins.create_field("name", "string")
                sname.write(insname)
                sattr = sname.attributes.create("short_name", "string")
                sattr.write(inssname)
                sname = sample.create_field("name", "string")
                sname.write(smpl)
                sfml = sample.create_field("chemical_formula", "string")
                sfml.write(formula)

                nxsfile.close()

                for cmd in commands:
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    sys.stdout = mystdout = StringIO()
                    sys.stderr = mystderr = StringIO()
                    old_argv = sys.argv
                    sys.argv = cmd
                    nxsfileinfo.main()

                    sys.argv = old_argv
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    vl = mystdout.getvalue()
                    er = mystderr.getvalue()

                    self.assertEqual('', er)
                    parser = docutils.parsers.rst.Parser()
                    components = (docutils.parsers.rst.Parser,)
                    settings = docutils.frontend.OptionParser(
                        components=components).get_default_values()
                    document = docutils.utils.new_document(
                        '<rst-doc>', settings=settings)
                    parser.parse(vl, document)
                    self.assertEqual(len(document), 1)
                    section = document[0]
                    self.assertEqual(len(section), 2)
                    self.assertEqual(len(section[0]), 1)
                    self.assertEqual(
                        str(section[0]),
                        "<title>File name: '%s'</title>" % filename)
                    self.assertEqual(len(section[1]), 1)
                    table = section[1]
                    self.assertEqual(table.tagname, 'table')
                    self.assertEqual(len(table), 1)
                    self.assertEqual(table[0].tagname, 'tgroup')
                    self.assertEqual(len(table[0]), 5)
                    for i in range(3):
                        self.assertEqual(table[0][i].tagname, 'colspec')
                    self.assertEqual(table[0][3].tagname, 'thead')
                    self.assertEqual(
                        str(table[0][3]),
                        '<thead><row>'
                        '<entry><paragraph>nexus_path</paragraph></entry>'
                        '<entry><paragraph>dtype</paragraph></entry>'
                        '<entry><paragraph>shape</paragraph></entry>'
                        '</row></thead>'
                    )
                    tbody = table[0][4]
                    self.assertEqual(tbody.tagname, 'tbody')
                    self.assertEqual(len(tbody), 14)
                    row = tbody[0]
                    self.assertEqual(len(row), 3)
                    self.assertEqual(row.tagname, "row")
                    self.assertEqual(len(row[0]), 2)
                    self.assertEqual(row[0].tagname, "entry")
                    self.assertEqual(len(row[0][0]), 1)
                    self.assertEqual(row[0][0].tagname, "system_message")
                    self.assertEqual(
                        str(row[0][0][0]),
                        "<paragraph>"
                        "Unexpected possible title overline or transition.\n"
                        "Treating it as ordinary text because it's so short."
                        "</paragraph>"
                    )
                    self.assertEqual(len(row[1]), 0)
                    self.assertEqual(str(row[1]), '<entry/>')
                    self.assertEqual(len(row[2]), 0)
                    self.assertEqual(str(row[2]), '<entry/>')

                    drows = {}
                    for irw in range(len(tbody)-1):
                        rw = tbody[irw + 1]
                        drows[str(rw[0][0][0])] = rw

                    rows = [drows[nm] for nm in sorted(drows.keys())]

                    self.checkGroupRow(
                        rows[1], "/entry12345/data")
                    self.checkFieldRow(
                        rows[2], "/entry12345/end_time", "string", "[1]")
                    self.checkFieldRow(
                        rows[3], "/entry12345/experiment_identifier",
                        "string", "[1]")
                    self.checkGroupRow(
                        rows[4], "/entry12345/instrument")
                    self.checkGroupRow(
                        rows[5], "/entry12345/instrument/detector")

                    self.checkFieldRow(
                        rows[6],
                        "/entry12345/instrument/detector/intimage",
                        "uint32", "['*', 30]"
                    )
                    self.checkFieldRow(
                        rows[7],
                        "/entry12345/instrument/name",
                        "string", "[1]"
                    )
                    self.checkGroupRow(rows[8], "/entry12345/sample")
                    self.checkFieldRow(
                        rows[9], "/entry12345/sample/chemical_formula",
                        "string", "[1]"
                    )
                    self.checkFieldRow(
                        rows[10], "/entry12345/sample/name",
                        "string", "[1]"
                    )
                    self.checkFieldRow(
                        rows[11], "/entry12345/start_time", "string", "[1]")
                    self.checkFieldRow(
                        rows[12], "/entry12345/title", "string", "[1]")

            finally:
                os.remove(filename)

    def ttest_execute_test_nofile(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo execute %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute -s %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute -s %s -r %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test %s -s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -s -r %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        nxsfile = filewriter.create_file(
            filename, overwrite=True)
        nxsfile.close()
        os.remove(filename)

        for cmd in commands:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            self.myAssertRaise(IOError, nxsfileinfo.main)

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue()
            er = mystderr.getvalue()

            self.assertEqual('', er)
            self.assertEqual('', vl)

    def ttest_execute_test_file_withdata(self):
        """ test nxsconfig execute file with data field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo execute %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute %s -s  %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test %s -s  %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute %s -s -r %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test %s -s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -s -r %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:
            nxsfile = filewriter.create_file(
                filename, overwrite=True)
            rt = nxsfile.root()
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            entry.create_group("data", "NXdata")
            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            nxsfile.close()

            for cmd in commands:
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertEqual('', vl)
                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)

        finally:
            os.remove(filename)

    def ttest_execute_test_file_withpostrun_nofile(self):
        """ test nxsconfig execute file with data field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo execute  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute -r %s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x -r %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test -r %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t -r %s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:
            nxsfile = filewriter.create_file(
                filename, overwrite=True)
            rt = nxsfile.root()
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            entry.create_group("data", "NXdata")
            col = det.create_group("fileinfoion", "NXfileinfoion")
            postrun = col.create_field("postrun", "string")
            postrun.write("test1_%05d.cbf:0:5")
            nxsfile.close()

            for cmd in commands:
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                # if '-r' not in cmd:
                #     os.remove("%s.__nxsfileinfo_old__" % filename)

        finally:
            os.remove(filename)

    def ttest_execute_file_withpostrun_tif(self):
        """ test nxsconfig execute file with a tif postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo execute  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:
            shutil.copy2('test/files/test_file0.tif', './test1_00000.tif')
            shutil.copy2('test/files/test_file1.tif', './test1_00001.tif')
            shutil.copy2('test/files/test_file2.tif', './test1_00002.tif')
            shutil.copy2('test/files/test_file3.tif', './test1_00003.tif')
            shutil.copy2('test/files/test_file4.tif', './test1_00004.tif')
            shutil.copy2('test/files/test_file5.tif', './test1_00005.tif')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.tif:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                # er =
                mystderr.getvalue()

                # self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 8)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.tif:0:5']")
                for i in range(1, 6):

                    self.assertTrue(svl[i].startswith(' * append '))
                    self.assertTrue(
                        svl[i].endswith('test1_%05d.tif ' % (i - 1)))

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                dt = det.open("data")
                buffer = dt.read()
                self.assertEqual(buffer.shape, (6, 195, 487))
                for i in range(6):
                    fbuffer = fabio.open('./test1_%05d.tif' % i)
                    fimage = fbuffer.data[...]
                    image = buffer[i, :, :]
                    self.assertTrue((image == fimage).all())
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./test1_00000.tif')
            os.remove('./test1_00001.tif')
            os.remove('./test1_00002.tif')
            os.remove('./test1_00003.tif')
            os.remove('./test1_00004.tif')
            os.remove('./test1_00005.tif')

    def ttest_execute_file_withpostrun_tif_pilatus300k_comp(self):
        """ test nxsconfig execute file with a tif postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo execute  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -s -c1 %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -c2 %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -c3 %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r -c4 %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -c5 %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -s -c6 %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -s -c7 %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r -s -c8 %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -s %s -c9' %
             (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            shutil.copy2('test/files/test_file0.tif',
                         './testfileinfo/pilatus300k/test1_00000.tif')
            shutil.copy2('test/files/test_file1.tif',
                         './testfileinfo/pilatus300k/test1_00001.tif')
            shutil.copy2('test/files/test_file2.tif',
                         './testfileinfo/pilatus300k/test1_00002.tif')
            shutil.copy2('test/files/test_file3.tif',
                         './testfileinfo/pilatus300k/test1_00003.tif')
            shutil.copy2('test/files/test_file4.tif',
                         './testfileinfo/pilatus300k/test1_00004.tif')
            shutil.copy2('test/files/test_file5.tif',
                         './testfileinfo/pilatus300k/test1_00005.tif')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.tif:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 8)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.tif:0:5']")
                for i in range(1, 6):
                    self.assertTrue(
                        svl[i],
                        ' * append /home/jkotan/ndts/nexdatas.tools/'
                        'test1_%05d.tif ' % (i - 1)
                    )

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                dt = det.open("data")
                buffer = dt.read()
                self.assertEqual(buffer.shape, (6, 195, 487))
                for i in range(6):
                    fbuffer = fabio.open(
                        './testfileinfo/pilatus300k/test1_%05d.tif' % i)
                    fimage = fbuffer.data[...]
                    image = buffer[i, :, :]
                    self.assertTrue((image == fimage).all())
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./testfileinfo/pilatus300k/test1_00000.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00001.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00002.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00003.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00004.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00005.tif')
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_execute_file_withpostrun_tif_pilatus300k_skip(self):
        """ test nxsconfig execute file with a tif postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo execute  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            shutil.copy2('test/files/test_file0.tif',
                         './testfileinfo/pilatus300k/test1_00000.tif')
            shutil.copy2('test/files/test_file1.tif',
                         './testfileinfo/pilatus300k/test1_00001.tif')
            # shutil.copy2('test/files/test_file2.tif',
            #              './testfileinfo/pilatus300k/test1_00002.tif')
            shutil.copy2('test/files/test_file3.tif',
                         './testfileinfo/pilatus300k/test1_00003.tif')
            # shutil.copy2('test/files/test_file4.tif',
            #              './testfileinfo/pilatus300k/test1_00004.tif')
            shutil.copy2('test/files/test_file5.tif',
                         './testfileinfo/pilatus300k/test1_00005.tif')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.tif:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 8)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.tif:0:5']")
                for i in range(1, 6):
                    if i not in [3, 5]:
                        self.assertEqual(
                            svl[i],
                            ' * append testfileinfo/pilatus300k/'
                            'test1_%05d.tif ' % (i - 1)
                        )
                    else:
                        self.assertTrue(
                            svl[i].startswith("Cannot open any of "))

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                dt = det.open("data")
                buffer = dt.read()
                self.assertEqual(buffer.shape, (4, 195, 487))
                ii = 0
                for i in range(6):
                    if i not in [2, 4]:
                        fbuffer = fabio.open(
                            './testfileinfo/pilatus300k/test1_%05d.tif' % i)
                        fimage = fbuffer.data[...]
                        image = buffer[ii, :, :]
                        self.assertTrue((image == fimage).all())
                        ii += 1
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./testfileinfo/pilatus300k/test1_00000.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00001.tif')
            # os.remove('./testfileinfo/pilatus300k/test1_00002.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00003.tif')
            # os.remove('./testfileinfo/pilatus300k/test1_00004.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00005.tif')
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_execute_file_withpostrun_tif_pilatus300k_wait(self):
        """ test nxsconfig execute file with a tif postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo execute  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.tif:0:5")
                nxsfile.close()

                shutil.copy2('test/files/test_file0.tif',
                             './testfileinfo/pilatus300k/test1_00000.tif')
                shutil.copy2('test/files/test_file1.tif',
                             './testfileinfo/pilatus300k/test1_00001.tif')
                shutil.copy2('test/files/test_file2.tif',
                             './testfileinfo/pilatus300k/test1_00002.tif')

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 8)

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                dt = det.open("data")
                buffer = dt.read()
                self.assertEqual(buffer.shape, (3, 195, 487))
                ii = 0
                for i in range(3):
                    fbuffer = fabio.open(
                        './testfileinfo/pilatus300k/test1_%05d.tif' % i)
                    fimage = fbuffer.data[...]
                    image = buffer[ii, :, :]
                    self.assertTrue((image == fimage).all())
                    ii += 1
                nxsfile.close()

                shutil.copy2('test/files/test_file3.tif',
                             './testfileinfo/pilatus300k/test1_00003.tif')
                shutil.copy2('test/files/test_file4.tif',
                             './testfileinfo/pilatus300k/test1_00004.tif')

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                dt = det.open("data")
                buffer = dt.read()
                self.assertEqual(buffer.shape, (5, 195, 487))
                ii = 0
                for i in range(5):
                    fbuffer = fabio.open(
                        './testfileinfo/pilatus300k/test1_%05d.tif' % i)
                    fimage = fbuffer.data[...]
                    image = buffer[ii, :, :]
                    self.assertTrue((image == fimage).all())
                    ii += 1
                nxsfile.close()

                os.remove('./testfileinfo/pilatus300k/test1_00000.tif')
                os.remove('./testfileinfo/pilatus300k/test1_00001.tif')
                os.remove('./testfileinfo/pilatus300k/test1_00002.tif')
                os.remove('./testfileinfo/pilatus300k/test1_00003.tif')
                os.remove('./testfileinfo/pilatus300k/test1_00004.tif')
                os.remove(filename)

        finally:
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_execute_file_withpostrun_tif_pilatus300k_missing(self):
        """ test nxsconfig execute file with a tif postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo execute  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            shutil.copy2('test/files/test_file0.tif',
                         './testfileinfo/pilatus300k/test1_00000.tif')
            shutil.copy2('test/files/test_file1.tif',
                         './testfileinfo/pilatus300k/test1_00001.tif')
            shutil.copy2('test/files/test_file2.tif',
                         './testfileinfo/pilatus300k/test1_00002.tif')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.tif:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 6)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.tif:0:5']")
                for i in range(1, 5):
                    if i not in [4]:
                        self.assertEqual(
                            svl[i],
                            ' * append testfileinfo/pilatus300k/'
                            'test1_%05d.tif ' % (i - 1)
                        )
                    else:
                        self.assertTrue(
                            svl[i].startswith("Cannot open any of "))

                # if '-r' not in cmd:
                #      os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                self.assertTrue('data' not in det.names())
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./testfileinfo/pilatus300k/test1_00000.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00001.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00002.tif')
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_execute_file_withpostrun_cbf(self):
        """ test nxsconfig execute file with a cbf postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo execute  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:
            shutil.copy2('test/files/test_file.cbf', './test1_00000.cbf')
            shutil.copy2('test/files/test_file.cbf', './test1_00001.cbf')
            shutil.copy2('test/files/test_file.cbf', './test1_00002.cbf')
            shutil.copy2('test/files/test_file.cbf', './test1_00003.cbf')
            shutil.copy2('test/files/test_file.cbf', './test1_00004.cbf')
            shutil.copy2('test/files/test_file.cbf', './test1_00005.cbf')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.cbf:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 8)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.cbf:0:5']")
                for i in range(1, 6):

                    self.assertTrue(svl[i].startswith(' * append '))
                    self.assertTrue(
                        svl[i].endswith('test1_%05d.cbf ' % (i - 1)))

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                dt = det.open("data")
                buffer = dt.read()
                self.assertEqual(buffer.shape, (6, 195, 487))
                for i in range(6):
                    fbuffer = fabio.open('./test1_%05d.cbf' % i)
                    fimage = fbuffer.data[...]
                    image = buffer[i, :, :]
                    self.assertTrue((image == fimage).all())
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./test1_00000.cbf')
            os.remove('./test1_00001.cbf')
            os.remove('./test1_00002.cbf')
            os.remove('./test1_00003.cbf')
            os.remove('./test1_00004.cbf')
            os.remove('./test1_00005.cbf')

    def ttest_execute_file_withpostrun_cbf_pilatus300k_comp(self):
        """ test nxsconfig execute file with a cbf postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo execute  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -s -c1 %s'
             % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -c2 %s'
             % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -c3 %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r -c4 %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -c5 %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -s -c6 %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -s -c7 %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r -s -c8 %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -s %s -c9' %
             (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00000.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00001.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00002.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00003.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00004.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00005.cbf')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.cbf:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 8)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.cbf:0:5']")
                for i in range(1, 6):
                    self.assertTrue(
                        svl[i],
                        ' * append /home/jkotan/ndts/nexdatas.tools/'
                        'test1_%05d.cbf ' % (i - 1)
                    )

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                dt = det.open("data")
                buffer = dt.read()
                self.assertEqual(buffer.shape, (6, 195, 487))
                for i in range(6):
                    fbuffer = fabio.open(
                        './testfileinfo/pilatus300k/test1_%05d.cbf' % i)
                    fimage = fbuffer.data[...]
                    image = buffer[i, :, :]
                    self.assertTrue((image == fimage).all())
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./testfileinfo/pilatus300k/test1_00000.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00001.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00002.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00003.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00004.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00005.cbf')
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_execute_file_withpostrun_cbf_pilatus300k_skip(self):
        """ test nxsconfig execute file with a cbf postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo execute  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00000.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00001.cbf')
            # shutil.copy2('test/files/test_file.cbf',
            #              './testfileinfo/pilatus300k/test1_00002.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00003.cbf')
            # shutil.copy2('test/files/test_file.cbf',
            #              './testfileinfo/pilatus300k/test1_00004.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00005.cbf')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.cbf:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 8)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.cbf:0:5']")
                for i in range(1, 6):
                    if i not in [3, 5]:
                        self.assertEqual(
                            svl[i],
                            ' * append testfileinfo/pilatus300k/'
                            'test1_%05d.cbf ' % (i - 1)
                        )
                    else:
                        self.assertTrue(
                            svl[i].startswith("Cannot open any of "))

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                dt = det.open("data")
                buffer = dt.read()
                self.assertEqual(buffer.shape, (4, 195, 487))
                ii = 0
                for i in range(6):
                    if i not in [2, 4]:
                        fbuffer = fabio.open(
                            './testfileinfo/pilatus300k/test1_%05d.cbf' % i)
                        fimage = fbuffer.data[...]
                        image = buffer[ii, :, :]
                        self.assertTrue((image == fimage).all())
                        ii += 1
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./testfileinfo/pilatus300k/test1_00000.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00001.cbf')
            # os.remove('./testfileinfo/pilatus300k/test1_00002.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00003.cbf')
            # os.remove('./testfileinfo/pilatus300k/test1_00004.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00005.cbf')
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_execute_file_withpostrun_cbf_pilatus300k_wait(self):
        """ test nxsconfig execute file with a cbf postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo execute  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.cbf:0:5")
                nxsfile.close()

                shutil.copy2('test/files/test_file.cbf',
                             './testfileinfo/pilatus300k/test1_00000.cbf')
                shutil.copy2('test/files/test_file.cbf',
                             './testfileinfo/pilatus300k/test1_00001.cbf')
                shutil.copy2('test/files/test_file.cbf',
                             './testfileinfo/pilatus300k/test1_00002.cbf')

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 8)

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                dt = det.open("data")
                buffer = dt.read()
                self.assertEqual(buffer.shape, (3, 195, 487))
                ii = 0
                for i in range(3):
                    fbuffer = fabio.open(
                        './testfileinfo/pilatus300k/test1_%05d.cbf' % i)
                    fimage = fbuffer.data[...]
                    image = buffer[ii, :, :]
                    self.assertTrue((image == fimage).all())
                    ii += 1
                nxsfile.close()

                shutil.copy2('test/files/test_file.cbf',
                             './testfileinfo/pilatus300k/test1_00003.cbf')
                shutil.copy2('test/files/test_file.cbf',
                             './testfileinfo/pilatus300k/test1_00004.cbf')

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                dt = det.open("data")
                buffer = dt.read()
                self.assertEqual(buffer.shape, (5, 195, 487))
                ii = 0
                for i in range(5):
                    fbuffer = fabio.open(
                        './testfileinfo/pilatus300k/test1_%05d.cbf' % i)
                    fimage = fbuffer.data[...]
                    image = buffer[ii, :, :]
                    self.assertTrue((image == fimage).all())
                    ii += 1
                nxsfile.close()

                os.remove('./testfileinfo/pilatus300k/test1_00000.cbf')
                os.remove('./testfileinfo/pilatus300k/test1_00001.cbf')
                os.remove('./testfileinfo/pilatus300k/test1_00002.cbf')
                os.remove('./testfileinfo/pilatus300k/test1_00003.cbf')
                os.remove('./testfileinfo/pilatus300k/test1_00004.cbf')
                os.remove(filename)

        finally:
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_execute_file_withpostrun_cbf_pilatus300k_missing(self):
        """ test nxsconfig execute file with a cbf postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo execute  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00000.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00001.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00002.cbf')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.cbf:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 6)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.cbf:0:5']")
                for i in range(1, 5):
                    if i not in [4]:
                        self.assertEqual(
                            svl[i],
                            ' * append testfileinfo/pilatus300k/'
                            'test1_%05d.cbf ' % (i - 1)
                        )
                    else:
                        self.assertTrue(
                            svl[i].startswith("Cannot open any of "))

                # if '-r' not in cmd:
                #      os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                self.assertTrue('data' not in det.names())
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./testfileinfo/pilatus300k/test1_00000.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00001.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00002.cbf')
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_execute_file_withpostrun_raw(self):
        """ test nxsconfig execute file with a cbf postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        attrs = {
            "int": [-123, "NX_INT", "int64", (1,)],
            "int8": [12, "NX_INT8", "int8", (1,)],
            "int16": [-123, "NX_INT16", "int16", (1,)],
            "int32": [12345, "NX_INT32", "int32", (1,)],
            "int64": [-12345, "NX_INT64", "int64", (1,)],
            "uint": [123, "NX_UINT", "uint64", (1,)],
            "uint8": [12, "NX_UINT8", "uint8", (1,)],
            "uint16": [123, "NX_UINT16", "uint16", (1,)],
            "uint32": [12345, "NX_UINT32", "uint32", (1,)],
            "uint64": [12345, "NX_UINT64", "uint64", (1,)],
            "float": [-12.345, "NX_FLOAT", "float64", (1,), 1.e-14],
            "number": [-12.345e+2, "NX_NUMBER", "float64", (1,), 1.e-14],
            "float32": [-12.345e-1, "NX_FLOAT32", "float32", (1,), 1.e-5],
            "float64": [-12.345, "NX_FLOAT64", "float64", (1,), 1.e-14],
        }

        commands = [
            ('nxsfileinfo execute  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -s %s' % (filename, self.flags)).split(),
        ]
        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule
        for k in attrs.keys():
            mlen = [self.__rnd.randint(10, 200),
                    self.__rnd.randint(10, 200)]

            attrs[k][0] = np.array(
                [[[attrs[k][0] * self.__rnd.randint(0, 3)
                   for c in range(mlen[1])]
                  for i in range(mlen[0])]
                 for _ in range(6)],
                dtype=attrs[k][2]
                )
            try:
                for i in range(6):
                    with open("rawtest1_%05d.dat" % i, "w") as fl:
                        attrs[k][0][i].tofile(fl)
                for cmd in commands:
                    nxsfile = filewriter.create_file(
                        filename, overwrite=True)
                    rt = nxsfile.root()
                    entry = rt.create_group("entry12345", "NXentry")
                    ins = entry.create_group("instrument", "NXinstrument")
                    det = ins.create_group("pilatus300k", "NXdetector")
                    entry.create_group("data", "NXdata")
                    col = det.create_group("fileinfoion", "NXfileinfoion")
                    postrun = col.create_field("postrun", "string")
                    postrun.write("rawtest1_%05d.dat:0:5")
                    atts = postrun.attributes
                    atts.create("fielddtype", "string").write(attrs[k][2])
                    atts.create("fieldshape", "string").write(
                        json.dumps(attrs[k][0].shape[1:]))
                    nxsfile.close()

                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    sys.stdout = mystdout = StringIO()
                    sys.stderr = mystderr = StringIO()
                    old_argv = sys.argv
                    sys.argv = cmd
                    nxsfileinfo.main()

                    sys.argv = old_argv
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    vl = mystdout.getvalue()
                    er = mystderr.getvalue()

                    self.assertEqual('', er)
                    self.assertTrue(vl)
                    svl = vl.split("\n")
                    self.assertEqual(len(svl), 8)
                    self.assertTrue(
                        svl[0],
                        "populate: /entry12345:NXentry/"
                        "instrument:NXinstrument/pilatus300k:NXdetector"
                        "/data with ['test1_%05d.cbf:0:5']")
                    for i in range(1, 6):
                        self.assertTrue(svl[i].startswith(' * append '))
                        self.assertTrue(
                            svl[i].endswith('test1_%05d.dat ' % (i - 1)))

                    if '-r' not in cmd:
                        os.remove("%s.__nxsfileinfo_old__" % filename)
                    nxsfile = filewriter.open_file(filename, readonly=True)
                    rt = nxsfile.root()
                    entry = rt.open("entry12345")
                    ins = entry.open("instrument")
                    det = ins.open("pilatus300k")
                    dt = det.open("data")
                    buffer = dt.read()
                    self.assertEqual(buffer.shape, attrs[k][0].shape)
                    for i in range(6):
                        fimage = attrs[k][0][i]
                        image = buffer[i, :, :]
                        self.assertTrue((image == fimage).all())
                    nxsfile.close()
                    os.remove(filename)

            finally:
                for i in range(6):
                    os.remove("rawtest1_%05d.dat" % i)

    def ttest_execute_file_withpostrun_h5(self):
        """ test nxsconfig execute file with a cbf postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        attrs = {
            "int": [-123, "NX_INT", "int64", (1,)],
            "int8": [12, "NX_INT8", "int8", (1,)],
            "int16": [-123, "NX_INT16", "int16", (1,)],
            "int32": [12345, "NX_INT32", "int32", (1,)],
            "int64": [-12345, "NX_INT64", "int64", (1,)],
            "uint": [123, "NX_UINT", "uint64", (1,)],
            "uint8": [12, "NX_UINT8", "uint8", (1,)],
            "uint16": [123, "NX_UINT16", "uint16", (1,)],
            "uint32": [12345, "NX_UINT32", "uint32", (1,)],
            "uint64": [12345, "NX_UINT64", "uint64", (1,)],
            "float": [-12.345, "NX_FLOAT", "float64", (1,), 1.e-14],
            "number": [-12.345e+2, "NX_NUMBER", "float64", (1,), 1.e-14],
            "float32": [-12.345e-1, "NX_FLOAT32", "float32", (1,), 1.e-5],
            "float64": [-12.345, "NX_FLOAT64", "float64", (1,), 1.e-14],
        }

        commands = [
            ('nxsfileinfo execute  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo execute  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -x %s -r -s %s' % (filename, self.flags)).split(),
        ]
        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule
        for k in attrs.keys():
            mlen = [self.__rnd.randint(10, 200),
                    self.__rnd.randint(10, 200)]

            attrs[k][0] = np.array(
                [[[attrs[k][0] * self.__rnd.randint(0, 3)
                   for c in range(mlen[1])]
                  for i in range(mlen[0])]
                 for _ in range(6)],
                dtype=attrs[k][2]
                )
            try:
                for i in range(6):
                    fl = filewriter.create_file("h5test1_%05d.h5" % i, )
                    rt = fl.root()
                    shp = attrs[k][0][i].shape
                    data = rt.create_field("data", attrs[k][2], shp, shp)
                    data.write(attrs[k][0][i])
                    data.close()
                    fl.close()
                for cmd in commands:
                    nxsfile = filewriter.create_file(
                        filename, overwrite=True)
                    rt = nxsfile.root()
                    entry = rt.create_group("entry12345", "NXentry")
                    ins = entry.create_group("instrument", "NXinstrument")
                    det = ins.create_group("pilatus300k", "NXdetector")
                    entry.create_group("data", "NXdata")
                    col = det.create_group("fileinfoion", "NXfileinfoion")
                    postrun = col.create_field("postrun", "string")
                    postrun.write("h5test1_%05d.h5:0:5")
                    nxsfile.close()

                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    sys.stdout = mystdout = StringIO()
                    sys.stderr = mystderr = StringIO()
                    old_argv = sys.argv
                    sys.argv = cmd
                    nxsfileinfo.main()

                    sys.argv = old_argv
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    vl = mystdout.getvalue()
                    er = mystderr.getvalue()

                    self.assertEqual('', er)
                    self.assertTrue(vl)
                    svl = vl.split("\n")
                    self.assertEqual(len(svl), 8)
                    self.assertTrue(
                        svl[0],
                        "populate: /entry12345:NXentry/"
                        "instrument:NXinstrument/pilatus300k:NXdetector"
                        "/data with ['test1_%05d.cbf:0:5']")
                    for i in range(1, 6):
                        self.assertTrue(svl[i].startswith(' * append '))
                        self.assertTrue(
                            svl[i].endswith('test1_%05d.h5 ' % (i - 1)))

                    if '-r' not in cmd:
                        os.remove("%s.__nxsfileinfo_old__" % filename)
                    nxsfile = filewriter.open_file(filename, readonly=True)
                    rt = nxsfile.root()
                    entry = rt.open("entry12345")
                    ins = entry.open("instrument")
                    det = ins.open("pilatus300k")
                    dt = det.open("data")
                    buffer = dt.read()
                    self.assertEqual(buffer.shape, attrs[k][0].shape)
                    for i in range(6):
                        fimage = attrs[k][0][i]
                        image = buffer[i, :, :]
                        self.assertTrue((image == fimage).all())
                    nxsfile.close()
                    os.remove(filename)

            finally:
                pass
                for i in range(6):
                    os.remove("h5test1_%05d.h5" % i)

    def ttest_test_file_withpostrun_tif(self):
        """ test nxsconfig test file with a tif postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo test  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r -s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:
            shutil.copy2('test/files/test_file0.tif', './test1_00000.tif')
            shutil.copy2('test/files/test_file1.tif', './test1_00001.tif')
            shutil.copy2('test/files/test_file2.tif', './test1_00002.tif')
            shutil.copy2('test/files/test_file3.tif', './test1_00003.tif')
            shutil.copy2('test/files/test_file4.tif', './test1_00004.tif')
            shutil.copy2('test/files/test_file5.tif', './test1_00005.tif')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.tif:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                # er =
                mystderr.getvalue()

                # self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 2)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.tif:0:5']")

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                self.assertTrue('data' not in det.names())
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./test1_00000.tif')
            os.remove('./test1_00001.tif')
            os.remove('./test1_00002.tif')
            os.remove('./test1_00003.tif')
            os.remove('./test1_00004.tif')
            os.remove('./test1_00005.tif')

    def ttest_test_file_withpostrun_tif_pilatus300k(self):
        """ test nxsconfig test file with a tif postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo test  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r -s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            shutil.copy2('test/files/test_file0.tif',
                         './testfileinfo/pilatus300k/test1_00000.tif')
            shutil.copy2('test/files/test_file1.tif',
                         './testfileinfo/pilatus300k/test1_00001.tif')
            shutil.copy2('test/files/test_file2.tif',
                         './testfileinfo/pilatus300k/test1_00002.tif')
            shutil.copy2('test/files/test_file3.tif',
                         './testfileinfo/pilatus300k/test1_00003.tif')
            shutil.copy2('test/files/test_file4.tif',
                         './testfileinfo/pilatus300k/test1_00004.tif')
            shutil.copy2('test/files/test_file5.tif',
                         './testfileinfo/pilatus300k/test1_00005.tif')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.tif:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 2)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.tif:0:5']")
                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                self.assertTrue('data' not in det.names())
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./testfileinfo/pilatus300k/test1_00000.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00001.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00002.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00003.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00004.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00005.tif')
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_test_file_withpostrun_tif_pilatus300k_skip(self):
        """ test nxsconfig test file with a tif postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo test  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r -s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            shutil.copy2('test/files/test_file0.tif',
                         './testfileinfo/pilatus300k/test1_00000.tif')
            shutil.copy2('test/files/test_file1.tif',
                         './testfileinfo/pilatus300k/test1_00001.tif')
            # shutil.copy2('test/files/test_file2.tif',
            #              './testfileinfo/pilatus300k/test1_00002.tif')
            shutil.copy2('test/files/test_file3.tif',
                         './testfileinfo/pilatus300k/test1_00003.tif')
            # shutil.copy2('test/files/test_file4.tif',
            #              './testfileinfo/pilatus300k/test1_00004.tif')
            shutil.copy2('test/files/test_file5.tif',
                         './testfileinfo/pilatus300k/test1_00005.tif')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.tif:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 4)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.tif:0:5']")

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                self.assertTrue('data' not in det.names())
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./testfileinfo/pilatus300k/test1_00000.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00001.tif')
            # os.remove('./testfileinfo/pilatus300k/test1_00002.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00003.tif')
            # os.remove('./testfileinfo/pilatus300k/test1_00004.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00005.tif')
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_test_file_withpostrun_tif_pilatus300k_wait(self):
        """ test nxsconfig test file with a tif postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo test  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r -s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.tif:0:5")
                nxsfile.close()

                shutil.copy2('test/files/test_file0.tif',
                             './testfileinfo/pilatus300k/test1_00000.tif')
                shutil.copy2('test/files/test_file1.tif',
                             './testfileinfo/pilatus300k/test1_00001.tif')
                shutil.copy2('test/files/test_file2.tif',
                             './testfileinfo/pilatus300k/test1_00002.tif')

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                self.assertTrue('data' not in det.names())
                nxsfile.close()

                shutil.copy2('test/files/test_file3.tif',
                             './testfileinfo/pilatus300k/test1_00003.tif')
                shutil.copy2('test/files/test_file4.tif',
                             './testfileinfo/pilatus300k/test1_00004.tif')

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                self.assertTrue('data' not in det.names())
                nxsfile.close()

                os.remove('./testfileinfo/pilatus300k/test1_00000.tif')
                os.remove('./testfileinfo/pilatus300k/test1_00001.tif')
                os.remove('./testfileinfo/pilatus300k/test1_00002.tif')
                os.remove('./testfileinfo/pilatus300k/test1_00003.tif')
                os.remove('./testfileinfo/pilatus300k/test1_00004.tif')
                os.remove(filename)

        finally:
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_test_file_withpostrun_tif_pilatus300k_missing(self):
        """ test nxsconfig test file with a tif postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo test  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            shutil.copy2('test/files/test_file0.tif',
                         './testfileinfo/pilatus300k/test1_00000.tif')
            shutil.copy2('test/files/test_file1.tif',
                         './testfileinfo/pilatus300k/test1_00001.tif')
            shutil.copy2('test/files/test_file2.tif',
                         './testfileinfo/pilatus300k/test1_00002.tif')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.tif:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 3)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.tif:0:5']")

                # if '-r' not in cmd:
                #      os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                self.assertTrue('data' not in det.names())
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./testfileinfo/pilatus300k/test1_00000.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00001.tif')
            os.remove('./testfileinfo/pilatus300k/test1_00002.tif')
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_test_file_withpostrun_cbf(self):
        """ test nxsconfig test file with a cbf postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo test  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r -s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:
            shutil.copy2('test/files/test_file.cbf', './test1_00000.cbf')
            shutil.copy2('test/files/test_file.cbf', './test1_00001.cbf')
            shutil.copy2('test/files/test_file.cbf', './test1_00002.cbf')
            shutil.copy2('test/files/test_file.cbf', './test1_00003.cbf')
            shutil.copy2('test/files/test_file.cbf', './test1_00004.cbf')
            shutil.copy2('test/files/test_file.cbf', './test1_00005.cbf')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.cbf:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 2)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.cbf:0:5']")

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                self.assertTrue('data' not in det.names())
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./test1_00000.cbf')
            os.remove('./test1_00001.cbf')
            os.remove('./test1_00002.cbf')
            os.remove('./test1_00003.cbf')
            os.remove('./test1_00004.cbf')
            os.remove('./test1_00005.cbf')

    def ttest_test_file_withpostrun_cbf_pilatus300k(self):
        """ test nxsconfig test file with a cbf postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo test  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r -s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00000.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00001.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00002.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00003.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00004.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00005.cbf')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.cbf:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 2)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.cbf:0:5']")

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                self.assertTrue('data' not in det.names())
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./testfileinfo/pilatus300k/test1_00000.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00001.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00002.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00003.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00004.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00005.cbf')
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_test_file_withpostrun_cbf_pilatus300k_skip(self):
        """ test nxsconfig test file with a cbf postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo test  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r -s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00000.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00001.cbf')
            # shutil.copy2('test/files/test_file.cbf',
            #              './testfileinfo/pilatus300k/test1_00002.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00003.cbf')
            # shutil.copy2('test/files/test_file.cbf',
            #              './testfileinfo/pilatus300k/test1_00004.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00005.cbf')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.cbf:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 4)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.cbf:0:5']")
                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                self.assertTrue('data' not in det.names())
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./testfileinfo/pilatus300k/test1_00000.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00001.cbf')
            # os.remove('./testfileinfo/pilatus300k/test1_00002.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00003.cbf')
            # os.remove('./testfileinfo/pilatus300k/test1_00004.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00005.cbf')
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_test_file_withpostrun_cbf_pilatus300k_wait(self):
        """ test nxsconfig test file with a cbf postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo test  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r -s %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.cbf:0:5")
                nxsfile.close()

                shutil.copy2('test/files/test_file.cbf',
                             './testfileinfo/pilatus300k/test1_00000.cbf')
                shutil.copy2('test/files/test_file.cbf',
                             './testfileinfo/pilatus300k/test1_00001.cbf')
                shutil.copy2('test/files/test_file.cbf',
                             './testfileinfo/pilatus300k/test1_00002.cbf')

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 5)

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                self.assertTrue('data' not in det.names())
                nxsfile.close()

                shutil.copy2('test/files/test_file.cbf',
                             './testfileinfo/pilatus300k/test1_00003.cbf')
                shutil.copy2('test/files/test_file.cbf',
                             './testfileinfo/pilatus300k/test1_00004.cbf')

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")

                if '-r' not in cmd:
                    os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                self.assertTrue('data' not in det.names())
                nxsfile.close()

                os.remove('./testfileinfo/pilatus300k/test1_00000.cbf')
                os.remove('./testfileinfo/pilatus300k/test1_00001.cbf')
                os.remove('./testfileinfo/pilatus300k/test1_00002.cbf')
                os.remove('./testfileinfo/pilatus300k/test1_00003.cbf')
                os.remove('./testfileinfo/pilatus300k/test1_00004.cbf')
                os.remove(filename)

        finally:
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_test_file_withpostrun_cbf_pilatus300k_missing(self):
        """ test nxsconfig test file with a cbf postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        commands = [
            ('nxsfileinfo test  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r %s' % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        dircreated = False
        try:
            if not os.path.exists("./testfileinfo/pilatus300k"):
                os.makedirs("./testfileinfo/pilatus300k")
                dircreated = True

            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00000.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00001.cbf')
            shutil.copy2('test/files/test_file.cbf',
                         './testfileinfo/pilatus300k/test1_00002.cbf')
            for cmd in commands:
                nxsfile = filewriter.create_file(
                    filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("pilatus300k", "NXdetector")
                entry.create_group("data", "NXdata")
                col = det.create_group("fileinfoion", "NXfileinfoion")
                postrun = col.create_field("postrun", "string")
                postrun.write("test1_%05d.cbf:0:5")
                nxsfile.close()

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsfileinfo.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue()
                er = mystderr.getvalue()

                self.assertEqual('', er)
                self.assertTrue(vl)
                svl = vl.split("\n")
                self.assertEqual(len(svl), 3)
                self.assertTrue(
                    svl[0],
                    "populate: /entry12345:NXentry/instrument:NXinstrument/"
                    "pilatus300k:NXdetector/data with ['test1_%05d.cbf:0:5']")
                # if '-r' not in cmd:
                #      os.remove("%s.__nxsfileinfo_old__" % filename)
                nxsfile = filewriter.open_file(filename, readonly=True)
                rt = nxsfile.root()
                entry = rt.open("entry12345")
                ins = entry.open("instrument")
                det = ins.open("pilatus300k")
                self.assertTrue('data' not in det.names())
                nxsfile.close()
                os.remove(filename)

        finally:
            os.remove('./testfileinfo/pilatus300k/test1_00000.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00001.cbf')
            os.remove('./testfileinfo/pilatus300k/test1_00002.cbf')
            if dircreated:
                shutil.rmtree("./testfileinfo")

    def ttest_test_file_withpostrun_raw(self):
        """ test nxsconfig test file with a cbf postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        attrs = {
            "int": [-123, "NX_INT", "int64", (1,)],
            "int8": [12, "NX_INT8", "int8", (1,)],
            "int16": [-123, "NX_INT16", "int16", (1,)],
            "int32": [12345, "NX_INT32", "int32", (1,)],
            "int64": [-12345, "NX_INT64", "int64", (1,)],
            "uint": [123, "NX_UINT", "uint64", (1,)],
            "uint8": [12, "NX_UINT8", "uint8", (1,)],
            "uint16": [123, "NX_UINT16", "uint16", (1,)],
            "uint32": [12345, "NX_UINT32", "uint32", (1,)],
            "uint64": [12345, "NX_UINT64", "uint64", (1,)],
            "float": [-12.345, "NX_FLOAT", "float64", (1,), 1.e-14],
            "number": [-12.345e+2, "NX_NUMBER", "float64", (1,), 1.e-14],
            "float32": [-12.345e-1, "NX_FLOAT32", "float32", (1,), 1.e-5],
            "float64": [-12.345, "NX_FLOAT64", "float64", (1,), 1.e-14],
        }

        commands = [
            ('nxsfileinfo test  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r -s %s' % (filename, self.flags)).split(),
        ]
        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule
        for k in attrs.keys():
            mlen = [self.__rnd.randint(10, 200),
                    self.__rnd.randint(10, 200)]

            attrs[k][0] = np.array(
                [[[attrs[k][0] * self.__rnd.randint(0, 3)
                   for c in range(mlen[1])]
                  for i in range(mlen[0])]
                 for _ in range(6)],
                dtype=attrs[k][2]
                )
            try:
                for i in range(6):
                    with open("rawtest1_%05d.dat" % i, "w") as fl:
                        attrs[k][0][i].tofile(fl)
                for cmd in commands:
                    nxsfile = filewriter.create_file(
                        filename, overwrite=True)
                    rt = nxsfile.root()
                    entry = rt.create_group("entry12345", "NXentry")
                    ins = entry.create_group("instrument", "NXinstrument")
                    det = ins.create_group("pilatus300k", "NXdetector")
                    entry.create_group("data", "NXdata")
                    col = det.create_group("fileinfoion", "NXfileinfoion")
                    postrun = col.create_field("postrun", "string")
                    postrun.write("rawtest1_%05d.dat:0:5")
                    atts = postrun.attributes
                    atts.create("fielddtype", "string").write(attrs[k][2])
                    atts.create("fieldshape", "string").write(
                        json.dumps(attrs[k][0].shape[1:]))
                    nxsfile.close()

                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    sys.stdout = mystdout = StringIO()
                    sys.stderr = mystderr = StringIO()
                    old_argv = sys.argv
                    sys.argv = cmd
                    nxsfileinfo.main()

                    sys.argv = old_argv
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    vl = mystdout.getvalue()
                    er = mystderr.getvalue()

                    self.assertEqual('', er)
                    self.assertTrue(vl)
                    svl = vl.split("\n")
                    self.assertEqual(len(svl), 2)
                    self.assertTrue(
                        svl[0],
                        "populate: /entry12345:NXentry/"
                        "instrument:NXinstrument/pilatus300k:NXdetector"
                        "/data with ['test1_%05d.cbf:0:5']")

                    if '-r' not in cmd:
                        os.remove("%s.__nxsfileinfo_old__" % filename)
                    nxsfile = filewriter.open_file(filename, readonly=True)
                    rt = nxsfile.root()
                    entry = rt.open("entry12345")
                    ins = entry.open("instrument")
                    det = ins.open("pilatus300k")
                    self.assertTrue('data' not in det.names())
                    nxsfile.close()
                    os.remove(filename)

            finally:
                for i in range(6):
                    os.remove("rawtest1_%05d.dat" % i)

    def ttest_test_file_withpostrun_h5(self):
        """ test nxsconfig test file with a cbf postrun field
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'
        attrs = {
            "int": [-123, "NX_INT", "int64", (1,)],
            "int8": [12, "NX_INT8", "int8", (1,)],
            "int16": [-123, "NX_INT16", "int16", (1,)],
            "int32": [12345, "NX_INT32", "int32", (1,)],
            "int64": [-12345, "NX_INT64", "int64", (1,)],
            "uint": [123, "NX_UINT", "uint64", (1,)],
            "uint8": [12, "NX_UINT8", "uint8", (1,)],
            "uint16": [123, "NX_UINT16", "uint16", (1,)],
            "uint32": [12345, "NX_UINT32", "uint32", (1,)],
            "uint64": [12345, "NX_UINT64", "uint64", (1,)],
            "float": [-12.345, "NX_FLOAT", "float64", (1,), 1.e-14],
            "number": [-12.345e+2, "NX_NUMBER", "float64", (1,), 1.e-14],
            "float32": [-12.345e-1, "NX_FLOAT32", "float32", (1,), 1.e-5],
            "float64": [-12.345, "NX_FLOAT64", "float64", (1,), 1.e-14],
        }

        commands = [
            ('nxsfileinfo test  %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -s %s' % (filename, self.flags)).split(),
            ('nxsfileinfo test  %s -r -s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo -t %s -r -s %s' % (filename, self.flags)).split(),
        ]
        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule
        for k in attrs.keys():
            mlen = [self.__rnd.randint(10, 200),
                    self.__rnd.randint(10, 200)]

            attrs[k][0] = np.array(
                [[[attrs[k][0] * self.__rnd.randint(0, 3)
                   for c in range(mlen[1])]
                  for i in range(mlen[0])]
                 for _ in range(6)],
                dtype=attrs[k][2]
                )
            try:
                for i in range(6):
                    fl = filewriter.create_file("h5test1_%05d.h5" % i, )
                    rt = fl.root()
                    shp = attrs[k][0][i].shape
                    data = rt.create_field("data", attrs[k][2], shp, shp)
                    data.write(attrs[k][0][i])
                    data.close()
                    fl.close()
                for cmd in commands:
                    nxsfile = filewriter.create_file(
                        filename, overwrite=True)
                    rt = nxsfile.root()
                    entry = rt.create_group("entry12345", "NXentry")
                    ins = entry.create_group("instrument", "NXinstrument")
                    det = ins.create_group("pilatus300k", "NXdetector")
                    entry.create_group("data", "NXdata")
                    col = det.create_group("fileinfoion", "NXfileinfoion")
                    postrun = col.create_field("postrun", "string")
                    postrun.write("h5test1_%05d.h5:0:5")
                    nxsfile.close()

                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    sys.stdout = mystdout = StringIO()
                    sys.stderr = mystderr = StringIO()
                    old_argv = sys.argv
                    sys.argv = cmd
                    nxsfileinfo.main()

                    sys.argv = old_argv
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    vl = mystdout.getvalue()
                    er = mystderr.getvalue()

                    self.assertEqual('', er)
                    self.assertTrue(vl)
                    svl = vl.split("\n")
                    self.assertEqual(len(svl), 2)
                    self.assertTrue(
                        svl[0],
                        "populate: /entry12345:NXentry/"
                        "instrument:NXinstrument/pilatus300k:NXdetector"
                        "/data with ['test1_%05d.cbf:0:5']")

                    if '-r' not in cmd:
                        os.remove("%s.__nxsfileinfo_old__" % filename)
                    nxsfile = filewriter.open_file(filename, readonly=True)
                    rt = nxsfile.root()
                    entry = rt.open("entry12345")
                    ins = entry.open("instrument")
                    det = ins.open("pilatus300k")
                    self.assertTrue('data' not in det.names())
                    nxsfile.close()
                    os.remove(filename)

            finally:
                pass
                for i in range(6):
                    os.remove("h5test1_%05d.h5" % i)


if __name__ == '__main__':
    unittest.main()
