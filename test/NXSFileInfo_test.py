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
import docutils.parsers.rst
import docutils.utils

from nxstools import nxsfileinfo
from nxstools import filewriter


try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


if sys.version_info > (3,):
    unicode = str
    long = int

WRITERS = {}
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
        else:
            self.writer = "h5py"

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

    def checkRow(self, row, args, strip=False):
        self.assertEqual(len(row), len(args))
        self.assertEqual(row.tagname, "row")

        for i, arg in enumerate(args):
            if arg is None:
                self.assertEqual(len(row[i]), 0)
                self.assertEqual(str(row[i]), "<entry/>")
            else:
                self.assertEqual(len(row[i]), 1)
                self.assertEqual(row[i].tagname, 'entry')
                self.assertEqual(row[i][0].tagname, 'paragraph')
                if strip:
                    self.assertEqual(
                        str(row[i][0][0]).replace(" ]", "]").
                        replace("[ ", "[").replace("  ", " "),
                        arg.replace(" ]", "]").
                        replace("[ ", "[").replace("  ", " "))
                elif str(row[i][0][0]).startswith("\x00"):
                    self.assertEqual(str(row[i][0][0])[1:], arg)
                else:
                    self.assertEqual(str(row[i][0][0]), arg)

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

                    self.checkRow(
                        rows[0],
                        ["/entry12345", None, None])
                    self.checkRow(
                        rows[1],
                        ["/entry12345/data", None, None])
                    self.checkRow(
                        rows[2],
                        ["/entry12345/end_time", "string", "[]"])
                    self.checkRow(
                        rows[3],
                        ["/entry12345/experiment_identifier",
                         "string", "[]"])
                    self.checkRow(
                        rows[4],
                        ["/entry12345/instrument", None, None])
                    self.checkRow(
                        rows[5],
                        ["/entry12345/instrument/detector", None, None])

                    self.checkRow(
                        rows[6],
                        ["/entry12345/instrument/detector/intimage",
                         "uint32", "['*', 30]"]
                    )
                    self.checkRow(
                        rows[7],
                        ["/entry12345/instrument/name",
                         "string", "[]"]
                    )
                    self.checkRow(rows[8],
                                  ["/entry12345/sample", None, None])
                    self.checkRow(
                        rows[9],
                        ["/entry12345/sample/chemical_formula",
                         "string", "[]"]
                    )
                    self.checkRow(
                        rows[10],
                        ["/entry12345/sample/name",
                         "string", "[]"]
                    )
                    self.checkRow(
                        rows[11],
                        ["/entry12345/start_time", "string", "[]"])
                    self.checkRow(
                        rows[12],
                        ["/entry12345/title", "string", "[]"])

            finally:
                os.remove(filename)

    def test_field_data(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = "ttestfileinfo.nxs"
        smpl = "water"

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
            dt = entry.create_group("data", "NXdata")
            sample = entry.create_group("sample", "NXsample")
            sample.create_field("name", "string").write(smpl)
            sample.create_field("depends_on", "string").write(
                "transformations/phi")
            trans = sample.create_group(
                "transformations", "NXtransformations")
            phi = trans.create_field("phi", "float64")
            phi.write(0.5)
            phi.attributes.create("units", "string").write("deg")
            phi.attributes.create("type", "string").write("NX_FLOAT64")
            phi.attributes.create("transformation_type", "string").write(
                "rotation")
            phi.attributes.create("depends_on", "string").write("z")
            phi.attributes.create("nexdatas_source", "string").write(
                '<datasource type="TANGO" name="sphi">'
                '<device member="attribute" hostname="haso0000" '
                'group="__CLIENT__" name="p/motor/m16" port="10000">'
                '</device>'
                '<record name="Position"></record>'
                '</datasource>')
            phi.attributes.create("vector", "int32", [3]).write(
                [1, 0, 0])
            phi.attributes.create("nexdatas_strategy", "string").write(
                "FINAL")

            sz = trans.create_field("z", "float32")
            sz.write(0.5)
            sz.attributes.create("units", "string").write("mm")
            sz.attributes.create("type", "string").write("NX_FLOAT32")
            sz.attributes.create("transformation_type", "string").write(
                "translation")
            sz.attributes.create("nexdatas_strategy", "string").write(
                "INIT")
            sz.attributes.create("nexdatas_source", "string").write(
                '<datasource type="TANGO" name="sz">'
                '<device member="attribute" hostname="haso0000" '
                'group="__CLIENT__" name="p/motor/m15" port="10000">'
                '</device>'
                '<record name="Position"></record>'
                '</datasource>')
            sz.attributes.create("vector", "int32", [3]).write(
                [0, 0, 1])

            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            filewriter.link(
                "/entry12345/instrument/detector/intimage",
                dt, "lkintimage")

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
                self.assertEqual(len(table[0]), 8)
                for i in range(6):
                    self.assertEqual(table[0][i].tagname, 'colspec')
                self.assertEqual(table[0][6].tagname, 'thead')
                self.assertEqual(
                    str(table[0][6]),
                    '<thead><row>'
                    '<entry><paragraph>nexus_path</paragraph></entry>'
                    '<entry><paragraph>source_name</paragraph></entry>'
                    '<entry><paragraph>units</paragraph></entry>'
                    '<entry><paragraph>dtype</paragraph></entry>'
                    '<entry><paragraph>shape</paragraph></entry>'
                    '<entry><paragraph>value</paragraph></entry>'
                    '</row></thead>'
                )
                tbody = table[0][7]
                self.assertEqual(tbody.tagname, 'tbody')
                self.assertEqual(len(tbody), 14)
                row = tbody[0]
                self.assertEqual(len(row), 6)
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
                self.checkRow(
                    rows[0],
                    ["-> /entry12345/instrument/detector/intimage",
                     None, None, "uint32", "['*', 30]", None]
                )
                self.checkRow(
                    rows[1],
                    ["/entry12345", None, None, None, None, None])
                self.checkRow(
                    rows[2],
                    ["/entry12345/data", None, None, None, None, None])
                rows = [drows[nm] for nm in sorted(drows.keys())]
                self.checkRow(
                    rows[3],
                    ["/entry12345/data/lkintimage", None, None,
                     "uint32", "['*', 30]", None]
                )
                self.checkRow(
                    rows[4],
                    ["/entry12345/instrument", None, None, None, None, None])
                self.checkRow(
                    rows[5],
                    ["/entry12345/instrument/detector",
                     None, None, None, None, None])
                self.checkRow(
                    rows[6],
                    ["/entry12345/instrument/detector/intimage", None, None,
                     "uint32", "['*', 30]", None]
                )
                self.checkRow(
                    rows[7],
                    ["/entry12345/sample", None, None, None, None, None])
                self.checkRow(
                    rows[8],
                    ["/entry12345/sample/depends_on", None, None,
                     "string", "[]",
                     "transformations/phi"]
                )
                self.checkRow(
                    rows[9],
                    ["/entry12345/sample/name", None, None,
                     "string", "[]", None]
                )
                self.checkRow(
                    rows[10],
                    ["/entry12345/sample/transformations",
                     None, None, None, None, None]
                )
                self.checkRow(
                    rows[11],
                    ["/entry12345/sample/transformations/phi",
                     "sphi", "deg", "float64", "[1]", None]
                )
                self.checkRow(
                    rows[12],
                    ["/entry12345/sample/transformations/z",
                     "sz", "mm", "float32", "[1]", None]
                )

        finally:
            os.remove(filename)

    def test_field_geometry(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = "gtestfileinfo.nxs"
        smpl = "water"

        commands = [
            ('nxsfileinfo field -g %s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo field --geometry %s %s' %
             (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:

            nxsfile = filewriter.create_file(filename, overwrite=True)
            rt = nxsfile.root()
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")
            sample = entry.create_group("sample", "NXsample")
            sample.create_field("name", "string").write(smpl)
            sample.create_field("depends_on", "string").write(
                "transformations/phi")
            trans = sample.create_group(
                "transformations", "NXtransformations")
            phi = trans.create_field("phi", "float64")
            phi.write(0.5)
            phi.attributes.create("units", "string").write("deg")
            phi.attributes.create("type", "string").write("NX_FLOAT64")
            phi.attributes.create("transformation_type", "string").write(
                "rotation")
            phi.attributes.create("depends_on", "string").write("z")
            phi.attributes.create("nexdatas_source", "string").write(
                '<datasource type="TANGO" name="sphi">'
                '<device member="attribute" hostname="haso0000" '
                'group="__CLIENT__" name="p/motor/m16" port="10000">'
                '</device>'
                '<record name="Position"></record>'
                '</datasource>')
            phi.attributes.create("vector", "int32", [3]).write(
                [1, 0, 0])
            phi.attributes.create("nexdatas_strategy", "string").write(
                "FINAL")

            sz = trans.create_field("z", "float32")
            sz.write(0.5)
            sz.attributes.create("units", "string").write("mm")
            sz.attributes.create("type", "string").write("NX_FLOAT32")
            sz.attributes.create("transformation_type", "string").write(
                "translation")
            sz.attributes.create("nexdatas_source", "string").write(
                '<datasource type="TANGO" name="sz">'
                '<device member="attribute" hostname="haso0000" '
                'group="__CLIENT__" name="p/motor/m15" port="10000">'
                '</device>'
                '<record name="Position"></record>'
                '</datasource>')
            sz.attributes.create("vector", "int32", [3]).write(
                [0, 0, 1])
            sz.attributes.create("offset", "float64", [3]).write(
                [2.3, 1.2, 0])
            sz.attributes.create("nexdatas_strategy", "string").write(
                "INIT")

            image = det.create_field("intimage", "uint32", [0, 30], [1, 30])
            image.attributes.create("nexdatas_source", "string").write(
                '<datasource type="TANGO" name="data">'
                '<device member="attribute" hostname="haso0000" '
                'group="__CLIENT__" name="p/mca/1" port="10000">'
                '</device>'
                '<record name="Position"></record>'
                '</datasource>')
            image.attributes.create("nexdatas_strategy", "string").write(
                "STEP")

            filewriter.link(
                "/entry12345/instrument/detector/intimage",
                dt, "lkintimage")

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
                self.assertEqual(len(table[0]), 9)
                for i in range(7):
                    self.assertEqual(table[0][i].tagname, 'colspec')
                self.assertEqual(table[0][7].tagname, 'thead')
                self.assertEqual(
                    str(table[0][7]),
                    '<thead><row>'
                    '<entry><paragraph>nexus_path</paragraph></entry>'
                    '<entry><paragraph>source_name</paragraph></entry>'
                    '<entry><paragraph>units</paragraph></entry>'
                    '<entry><paragraph>trans_type</paragraph></entry>'
                    '<entry><paragraph>trans_vector</paragraph></entry>'
                    '<entry><paragraph>trans_offset</paragraph></entry>'
                    '<entry><paragraph>depends_on</paragraph></entry>'
                    '</row></thead>'
                )
                tbody = table[0][8]
                self.assertEqual(tbody.tagname, 'tbody')
                self.assertEqual(len(tbody), 3)

                drows = {}
                for irw in range(len(tbody)):
                    rw = tbody[irw]
                    drows[str(rw[0][0][0])] = rw

                rows = [drows[nm] for nm in sorted(drows.keys())]
                self.checkRow(
                    rows[0],
                    ["/entry12345/sample/depends_on",
                     None, None, None, None, None,
                     "[transformations/phi]"]
                )
                self.checkRow(
                    rows[1],
                    ["/entry12345/sample/transformations/phi",
                     "sphi", "deg", "rotation", "[1 0 0]", None,
                     "z"]
                )
                self.checkRow(
                    rows[2],
                    ["/entry12345/sample/transformations/z",
                     "sz", "mm", "translation", "[0 0 1]",
                     "[ 2.3  1.2  0. ]", None],
                    strip=True
                )

        finally:
            os.remove(filename)

    def test_field_source(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = "sgtestfileinfo.nxs"
        smpl = "water"

        commands = [
            ('nxsfileinfo field -s %s %s' %
             (filename, self.flags)).split(),
            ('nxsfileinfo field --source %s %s' %
             (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:

            nxsfile = filewriter.create_file(filename, overwrite=True)
            rt = nxsfile.root()
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")
            sample = entry.create_group("sample", "NXsample")
            sample.create_field("name", "string").write(smpl)
            sample.create_field("depends_on", "string").write(
                "transformations/phi")
            trans = sample.create_group(
                "transformations", "NXtransformations")
            phi = trans.create_field("phi", "float64")
            phi.write(0.5)
            phi.attributes.create("units", "string").write("deg")
            phi.attributes.create("type", "string").write("NX_FLOAT64")
            phi.attributes.create("transformation_type", "string").write(
                "rotation")
            phi.attributes.create("depends_on", "string").write("z")
            phi.attributes.create("nexdatas_source", "string").write(
                '<datasource type="TANGO" name="sphi">'
                '<device member="attribute" hostname="haso0000" '
                'group="__CLIENT__" name="p/motor/m16" port="10000">'
                '</device>'
                '<record name="Position"></record>'
                '</datasource>')
            phi.attributes.create("vector", "int32", [3]).write(
                [1, 0, 0])
            phi.attributes.create("nexdatas_strategy", "string").write(
                "FINAL")

            sz = trans.create_field("z", "float32")
            sz.write(0.5)
            sz.attributes.create("units", "string").write("mm")
            sz.attributes.create("type", "string").write("NX_FLOAT32")
            sz.attributes.create("transformation_type", "string").write(
                "translation")
            sz.attributes.create("nexdatas_source", "string").write(
                '<datasource type="TANGO" name="sz">'
                '<device member="attribute" hostname="haso0000" '
                'group="__CLIENT__" name="p/motor/m15" port="10000">'
                '</device>'
                '<record name="Position"></record>'
                '</datasource>')
            sz.attributes.create("vector", "int32", [3]).write(
                [0, 0, 1])
            sz.attributes.create("offset", "float64", [3]).write(
                [2.3, 1.2, 0])
            sz.attributes.create("nexdatas_strategy", "string").write(
                "INIT")

            image = det.create_field("intimage", "uint32", [0, 30], [1, 30])
            image.attributes.create("nexdatas_source", "string").write(
                '<datasource type="TANGO" name="data">'
                '<device member="attribute" hostname="haso0000" '
                'group="__CLIENT__" name="p/mca/1" port="10000">'
                '</device>'
                '<record name="Data"></record>'
                '</datasource>')
            image.attributes.create("nexdatas_strategy", "string").write(
                "STEP")

            filewriter.link(
                "/entry12345/instrument/detector/intimage",
                dt, "lkintimage")

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
                self.assertEqual(len(table[0]), 7)
                for i in range(5):
                    self.assertEqual(table[0][i].tagname, 'colspec')
                self.assertEqual(table[0][5].tagname, 'thead')
                self.assertEqual(
                    str(table[0][5]),
                    '<thead><row>'
                    '<entry><paragraph>source_name</paragraph></entry>'
                    '<entry><paragraph>nexus_type</paragraph></entry>'
                    '<entry><paragraph>shape</paragraph></entry>'
                    '<entry><paragraph>strategy</paragraph></entry>'
                    '<entry><paragraph>source</paragraph></entry>'
                    '</row></thead>'
                )
                tbody = table[0][6]
                self.assertEqual(tbody.tagname, 'tbody')
                self.assertEqual(len(tbody), 5)

                drows = {}
                for irw in range(len(tbody)):
                    rw = tbody[irw]
                    drows[str(rw[0][0][0])] = rw

                rows = [drows[nm] for nm in sorted(drows.keys())]
                self.checkRow(
                    rows[0],
                    ["data", None, "['*', 30]", "STEP",
                     "haso0000:10000/p/mca/1/Data"]
                )
                self.checkRow(
                    rows[1],
                    ["sphi", "NX_FLOAT64", "[1]", "FINAL",
                     "haso0000:10000/p/motor/m16/Position"]
                )
                self.checkRow(
                    rows[2],
                    ["sz", "NX_FLOAT32", "[1]", "INIT",
                     "haso0000:10000/p/motor/m15/Position"]
                )

        finally:
            os.remove(filename)

    def test_field_data_filter(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = "fttestfileinfo.nxs"
        smpl = "water"

        commands = [
            ("nxsfileinfo field %s %s -f *:NXinstrument/*" %
             (filename, self.flags)).split(),
            ("nxsfileinfo field %s %s --filter *:NXinstrument/*" %
             (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:

            nxsfile = filewriter.create_file(filename, overwrite=True)
            rt = nxsfile.root()
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")
            sample = entry.create_group("sample", "NXsample")
            sample.create_field("name", "string").write(smpl)
            sample.create_field("depends_on", "string").write(
                "transformations/phi")
            trans = sample.create_group(
                "transformations", "NXtransformations")
            phi = trans.create_field("phi", "float64")
            phi.write(0.5)
            phi.attributes.create("units", "string").write("deg")
            phi.attributes.create("type", "string").write("NX_FLOAT64")
            phi.attributes.create("transformation_type", "string").write(
                "rotation")
            phi.attributes.create("depends_on", "string").write("z")
            phi.attributes.create("nexdatas_source", "string").write(
                '<datasource type="TANGO" name="sphi">'
                '<device member="attribute" hostname="haso0000" '
                'group="__CLIENT__" name="p/motor/m16" port="10000">'
                '</device>'
                '<record name="Position"></record>'
                '</datasource>')
            phi.attributes.create("vector", "int32", [3]).write(
                [1, 0, 0])
            phi.attributes.create("nexdatas_strategy", "string").write(
                "FINAL")

            sz = trans.create_field("z", "float32")
            sz.write(0.5)
            sz.attributes.create("units", "string").write("mm")
            sz.attributes.create("type", "string").write("NX_FLOAT32")
            sz.attributes.create("transformation_type", "string").write(
                "translation")
            sz.attributes.create("nexdatas_strategy", "string").write(
                "INIT")
            sz.attributes.create("nexdatas_source", "string").write(
                '<datasource type="TANGO" name="sz">'
                '<device member="attribute" hostname="haso0000" '
                'group="__CLIENT__" name="p/motor/m15" port="10000">'
                '</device>'
                '<record name="Position"></record>'
                '</datasource>')
            sz.attributes.create("vector", "int32", [3]).write(
                [0, 0, 1])

            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            filewriter.link(
                "/entry12345/instrument/detector/intimage",
                dt, "lkintimage")

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
                self.assertEqual(len(tbody), 2)

                drows = {}
                for irw in range(len(tbody)):
                    rw = tbody[irw]
                    drows[str(rw[0][0][0])] = rw

                rows = [drows[nm] for nm in sorted(drows.keys())]
                self.checkRow(
                    rows[0],
                    ["/entry12345/instrument/detector",
                     None, None])
                self.checkRow(
                    rows[1],
                    ["/entry12345/instrument/detector/intimage",
                     "uint32", "['*', 30]"]
                )

        finally:
            os.remove(filename)

    def test_field_data_columns(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = "cttestfileinfo.nxs"
        smpl = "water"

        commands = [
            ('nxsfileinfo field %s %s --columns '
             ' nexus_path,source_name,shape,dtype,strategy' %
             (filename, self.flags)).split(),
            ('nxsfileinfo field %s %s '
             ' -c  nexus_path,source_name,shape,dtype,strategy' %
             (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:

            nxsfile = filewriter.create_file(filename, overwrite=True)
            rt = nxsfile.root()
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")
            sample = entry.create_group("sample", "NXsample")
            sample.create_field("name", "string").write(smpl)
            sample.create_field("depends_on", "string").write(
                "transformations/phi")
            trans = sample.create_group(
                "transformations", "NXtransformations")
            phi = trans.create_field("phi", "float64")
            phi.write(0.5)
            phi.attributes.create("units", "string").write("deg")
            phi.attributes.create("type", "string").write("NX_FLOAT64")
            phi.attributes.create("transformation_type", "string").write(
                "rotation")
            phi.attributes.create("depends_on", "string").write("z")
            phi.attributes.create("nexdatas_source", "string").write(
                '<datasource type="TANGO" name="sphi">'
                '<device member="attribute" hostname="haso0000" '
                'group="__CLIENT__" name="p/motor/m16" port="10000">'
                '</device>'
                '<record name="Position"></record>'
                '</datasource>')
            phi.attributes.create("vector", "int32", [3]).write(
                [1, 0, 0])
            phi.attributes.create("nexdatas_strategy", "string").write(
                "FINAL")

            sz = trans.create_field("z", "float32")
            sz.write(0.5)
            sz.attributes.create("units", "string").write("mm")
            sz.attributes.create("type", "string").write("NX_FLOAT32")
            sz.attributes.create("transformation_type", "string").write(
                "translation")
            sz.attributes.create("nexdatas_strategy", "string").write(
                "INIT")
            sz.attributes.create("nexdatas_source", "string").write(
                '<datasource type="TANGO" name="sz">'
                '<device member="attribute" hostname="haso0000" '
                'group="__CLIENT__" name="p/motor/m15" port="10000">'
                '</device>'
                '<record name="Position"></record>'
                '</datasource>')
            sz.attributes.create("vector", "int32", [3]).write(
                [0, 0, 1])

            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            filewriter.link(
                "/entry12345/instrument/detector/intimage",
                dt, "lkintimage")

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
                self.assertEqual(len(table[0]), 7)
                for i in range(5):
                    self.assertEqual(table[0][i].tagname, 'colspec')
                self.assertEqual(table[0][5].tagname, 'thead')
                self.assertEqual(
                    str(table[0][5]),
                    '<thead><row>'
                    '<entry><paragraph>nexus_path</paragraph></entry>'
                    '<entry><paragraph>source_name</paragraph></entry>'
                    '<entry><paragraph>shape</paragraph></entry>'
                    '<entry><paragraph>dtype</paragraph></entry>'
                    '<entry><paragraph>strategy</paragraph></entry>'
                    '</row></thead>'
                )
                tbody = table[0][6]
                self.assertEqual(tbody.tagname, 'tbody')
                self.assertEqual(len(tbody), 14)
                row = tbody[0]
                self.assertEqual(len(row), 5)
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
                self.checkRow(
                    rows[0],
                    ["-> /entry12345/instrument/detector/intimage",
                     None, "['*', 30]", "uint32",  None]
                )
                self.checkRow(
                    rows[1],
                    ["/entry12345", None, None, None, None])
                self.checkRow(
                    rows[2],
                    ["/entry12345/data", None, None, None, None])
                rows = [drows[nm] for nm in sorted(drows.keys())]
                self.checkRow(
                    rows[3],
                    ["/entry12345/data/lkintimage", None,
                     "['*', 30]", "uint32", None]
                )
                self.checkRow(
                    rows[4],
                    ["/entry12345/instrument", None, None, None, None])
                self.checkRow(
                    rows[5],
                    ["/entry12345/instrument/detector",
                     None, None, None, None])
                self.checkRow(
                    rows[6],
                    ["/entry12345/instrument/detector/intimage", None,
                     "['*', 30]", "uint32", None]
                )
                self.checkRow(
                    rows[7],
                    ["/entry12345/sample", None, None, None, None])
                self.checkRow(
                    rows[8],
                    ["/entry12345/sample/depends_on", None,
                     "[]", "string", None]
                )
                self.checkRow(
                    rows[9],
                    ["/entry12345/sample/name", None,
                     "[]", "string", None]
                )
                self.checkRow(
                    rows[10],
                    ["/entry12345/sample/transformations",
                     None, None, None, None]
                )
                self.checkRow(
                    rows[11],
                    ["/entry12345/sample/transformations/phi",
                     "sphi", "[1]", "float64", "FINAL"]
                )
                self.checkRow(
                    rows[12],
                    ["/entry12345/sample/transformations/z",
                     "sz", "[1]", "float32", "INIT"]
                )

        finally:
            os.remove(filename)

    def test_field_data_values(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = "vttestfileinfo.nxs"
        smpl = "water"

        commands = [
            ('nxsfileinfo field %s %s'
             ' -v z,phi '
             % (filename, self.flags)).split(),
            ('nxsfileinfo field %s %s'
             ' --value z,phi '
             % (filename, self.flags)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:

            nxsfile = filewriter.create_file(filename, overwrite=True)
            rt = nxsfile.root()
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")
            sample = entry.create_group("sample", "NXsample")
            sample.create_field("name", "string").write(smpl)
            sample.create_field("depends_on", "string").write(
                "transformations/phi")
            trans = sample.create_group(
                "transformations", "NXtransformations")
            phi = trans.create_field("phi", "float64")
            phi.write(5.)
            phi.attributes.create("units", "string").write("deg")
            phi.attributes.create("type", "string").write("NX_FLOAT64")
            phi.attributes.create("transformation_type", "string").write(
                "rotation")
            phi.attributes.create("depends_on", "string").write("z")
            phi.attributes.create("nexdatas_source", "string").write(
                '<datasource type="TANGO" name="sphi">'
                '<device member="attribute" hostname="haso0000" '
                'group="__CLIENT__" name="p/motor/m16" port="10000">'
                '</device>'
                '<record name="Position"></record>'
                '</datasource>')
            phi.attributes.create("vector", "int32", [3]).write(
                [1, 0, 0])
            phi.attributes.create("nexdatas_strategy", "string").write(
                "FINAL")

            sz = trans.create_field("z", "float32")
            sz.write(23.)
            sz.attributes.create("units", "string").write("mm")
            sz.attributes.create("type", "string").write("NX_FLOAT32")
            sz.attributes.create("transformation_type", "string").write(
                "translation")
            sz.attributes.create("nexdatas_strategy", "string").write(
                "INIT")
            sz.attributes.create("nexdatas_source", "string").write(
                '<datasource type="TANGO" name="sz">'
                '<device member="attribute" hostname="haso0000" '
                'group="__CLIENT__" name="p/motor/m15" port="10000">'
                '</device>'
                '<record name="Position"></record>'
                '</datasource>')
            sz.attributes.create("vector", "int32", [3]).write(
                [0, 0, 1])

            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            filewriter.link(
                "/entry12345/instrument/detector/intimage",
                dt, "lkintimage")

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
                self.assertEqual(len(table[0]), 8)
                for i in range(6):
                    self.assertEqual(table[0][i].tagname, 'colspec')
                self.assertEqual(table[0][6].tagname, 'thead')
                self.assertEqual(
                    str(table[0][6]),
                    '<thead><row>'
                    '<entry><paragraph>nexus_path</paragraph></entry>'
                    '<entry><paragraph>source_name</paragraph></entry>'
                    '<entry><paragraph>units</paragraph></entry>'
                    '<entry><paragraph>dtype</paragraph></entry>'
                    '<entry><paragraph>shape</paragraph></entry>'
                    '<entry><paragraph>value</paragraph></entry>'
                    '</row></thead>'
                )
                tbody = table[0][7]
                self.assertEqual(tbody.tagname, 'tbody')
                self.assertEqual(len(tbody), 14)
                row = tbody[0]
                self.assertEqual(len(row), 6)
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
                self.checkRow(
                    rows[0],
                    ["-> /entry12345/instrument/detector/intimage",
                     None, None, "uint32", "['*', 30]", None]
                )
                self.checkRow(
                    rows[1],
                    ["/entry12345", None, None, None, None, None])
                self.checkRow(
                    rows[2],
                    ["/entry12345/data", None, None, None, None, None])
                rows = [drows[nm] for nm in sorted(drows.keys())]
                self.checkRow(
                    rows[3],
                    ["/entry12345/data/lkintimage", None, None,
                     "uint32", "['*', 30]", None]
                )
                self.checkRow(
                    rows[4],
                    ["/entry12345/instrument", None, None, None, None, None])
                self.checkRow(
                    rows[5],
                    ["/entry12345/instrument/detector",
                     None, None, None, None, None])
                self.checkRow(
                    rows[6],
                    ["/entry12345/instrument/detector/intimage", None, None,
                     "uint32", "['*', 30]", None]
                )
                self.checkRow(
                    rows[7],
                    ["/entry12345/sample", None, None, None, None, None])
                self.checkRow(
                    rows[8],
                    ["/entry12345/sample/depends_on", None, None,
                     "string", "[]",
                     None]
                )
                self.checkRow(
                    rows[9],
                    ["/entry12345/sample/name", None, None,
                     "string", "[]", None]
                )
                self.checkRow(
                    rows[10],
                    ["/entry12345/sample/transformations",
                     None, None, None, None, None]
                )
                self.checkRow(
                    rows[11],
                    ["/entry12345/sample/transformations/phi",
                     "sphi", "deg", "float64", "[1]", "5.0"]
                )
                self.checkRow(
                    rows[12],
                    ["/entry12345/sample/transformations/z",
                     "sz", "mm", "float32", "[1]", "23.0"]
                )

        finally:
            os.remove(filename)


if __name__ == '__main__':
    unittest.main()
