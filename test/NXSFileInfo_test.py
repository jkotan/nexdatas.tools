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
import json
import binascii
import docutils.parsers.rst
import docutils.utils
import getpass
import pwd
from dateutil import parser as duparser
import time
import grp
import shutil
import base64
import PIL
import PIL.Image
import numpy as np
from io import BytesIO

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

        self.helpinfo = """usage: nxsfileinfo [-h] """ \
            """{field,general,metadata,origdatablock,sample,""" \
            """instrument,attachment} ...

Command-line tool for showing meta data from Nexus Files

positional arguments:
  {field,general,metadata,origdatablock,sample,instrument,attachment}
                        sub-command help
    field               show field information for the nexus file
    general             show general information for the nexus file
    metadata            show metadata information for the nexus file
    origdatablock       generate description of all scan files
    sample              generate description of sample
    instrument          generate description of instrument
    attachment          generate description of attachment

optional arguments:
  -h, --help            show this help message and exit

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
        self.maxDiff = None

    # test starter
    # \brief Common set up
    def setUp(self):
        print("\nsetting up...")
        print("SEED = %s" % self.seed)

    # test closer
    # \brief Common tear down
    def tearDown(self):
        print("tearing down ...")

    def myAssertDict(self, dct, dct2, skip=None, parent=None):
        parent = parent or ""
        self.assertTrue(isinstance(dct, dict))
        self.assertTrue(isinstance(dct2, dict))
        if len(list(dct.keys())) != len(list(dct2.keys())):
            print(list(dct.keys()))
            print(list(dct2.keys()))
        self.assertEqual(
            len(list(dct.keys())), len(list(dct2.keys())))
        for k, v in dct.items():
            if parent:
                node = "%s.%s" % (parent, k)
            else:
                node = k
            if k not in dct2.keys():
                print("%s not in %s" % (k, dct2))
            self.assertTrue(k in dct2.keys())
            if not skip or node not in skip:
                if isinstance(v, dict):
                    self.myAssertDict(v, dct2[k], skip, node)
                else:
                    self.assertEqual(v, dct2[k])

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
        self.assertEqual(
            "".join(self.helpinfo.split()).replace(
                "optionalarguments:", "options:"),
            "".join(vl.split()).replace("optionalarguments:", "options:"))
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
            self.assertEqual(
                "".join(self.helpinfo.split()).replace(
                    "optionalarguments:", "options:"),
                "".join(vl.split()).replace("optionalarguments:", "options:"))
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

    def test_metadata_emptyfile(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = 'testfileinfo.nxs'

        commands = [
            ('nxsfileinfo metadata %s %s' % (filename, self.flags)).split(),
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
                self.assertEqual('', vl)
        finally:
            os.remove(filename)

    def test_metadata_nodata(self):
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
                ('nxsfileinfo metadata -m %s %s'
                 % (filename, self.flags)).split(),
                ('nxsfileinfo metadata --raw-metadata %s %s'
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
                    # print(vl)
                    dct = json.loads(vl)
                    res = {'entry12345':
                           {'NX_class': 'NXentry',
                            'data': {'NX_class': 'NXdata'},
                            'end_time': {'value': '%s' % arg[6]},
                            'experiment_identifier': {'value': '%s' % arg[2]},
                            'instrument': {
                                'NX_class': 'NXinstrument',
                                'detector': {
                                    'NX_class': 'NXdetector',
                                    'intimage': {'shape': [0, 30]}},
                                'name': {
                                    'short_name': '%s' % arg[4],
                                    'value': '%s' % arg[3]}},
                            'sample': {
                                'NX_class': 'NXsample',
                                'chemical_formula': {'value': '%s' % arg[8]},
                                'name': {'value': '%s' % arg[7]}},
                            'start_time': {
                                'value': '%s' % arg[5]},
                            'title': {'value': '%s' % arg[1]}}}
                    self.myAssertDict(dct, res)
            finally:
                os.remove(filename)

    def test_metadata_postfix(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = "ttestfileinfo.nxs"
        smpl = "water"

        commands = [
            ('nxsfileinfo metadata %s %s -m -g Group -v intimage ' % (
                filename, self.flags)).split(),
            ('nxsfileinfo metadata %s %s -m --group-postfix Group '
             '-v intimage' % (
                 filename, self.flags)).split(),
            ('nxsfileinfo metadata %s %s --raw-metadata -g Group '
             '-v intimage' % (
                 filename, self.flags)).split(),
            ('nxsfileinfo metadata %s %s  --raw-metadata '
             '--group-postfix Group -v intimage' % (
                 filename, self.flags)).split(),
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

            det.create_field("intimage", "uint32", [10], [10]).write(
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
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
                # print(vl)
                dct = json.loads(vl)
                res = {
                    "entry12345Group": {
                        "NX_class": "NXentry",
                        "dataGroup": {
                            "NX_class": "NXdata",
                            "lkintimage": {
                                "shape": [
                                    10
                                ]
                            }
                        },
                        "instrumentGroup": {
                            "NX_class": "NXinstrument",
                            "detectorGroup": {
                                "NX_class": "NXdetector",
                                "intimage": {
                                    'value': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                                    "shape": [10]
                                }
                            }
                        },
                        "sampleGroup": {
                            "NX_class": "NXsample",
                            "depends_on": {
                                "value": "transformations/phi"
                            },
                            "name": {
                                "value": "water"
                            },
                            "transformationsGroup": {
                                "NX_class": "NXtransformations",
                                "phi": {
                                    "depends_on": "z",
                                    "type": "NX_FLOAT64",
                                    "source":
                                    "haso0000:10000/p/motor/m16/Position",
                                    "source_name": "sphi",
                                    "source_type": "TANGO",
                                    "strategy": "FINAL",
                                    "transformation_type": "rotation",
                                    "vector": [1, 0, 0],
                                    "unit": "deg",
                                    "value": 0.5
                                },
                                "z": {
                                    "type": "NX_FLOAT32",
                                    "source":
                                    "haso0000:10000/p/motor/m15/Position",
                                    "source_name": "sz",
                                    "source_type": "TANGO",
                                    "strategy": "INIT",
                                    "transformation_type": "translation",
                                    "vector": [0, 0, 1],
                                    "unit": "mm",
                                    "value": 0.5
                                }
                            }
                        }
                    }
                }
                self.myAssertDict(dct, res)
        finally:
            os.remove(filename)

    def test_metadata_postfix_oned(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        filename = "ttestfileinfo.nxs"
        smpl = "water"

        commands = [
            ('nxsfileinfo metadata %s %s -m -g Group -v intimage --oned' % (
                filename, self.flags)).split(),
            ('nxsfileinfo metadata %s %s -m --group-postfix Group --oned '
             % (
                 filename, self.flags)).split(),
            ('nxsfileinfo metadata %s %s --raw-metadata -g Group  --oned '
             % (
                 filename, self.flags)).split(),
            ('nxsfileinfo metadata %s %s  --raw-metadata --oned '
             '--group-postfix Group' % (
                 filename, self.flags)).split(),
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

            det.create_field("intimage", "uint32", [10], [10]).write(
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
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
                # print(vl)
                dct = json.loads(vl)
                res = {
                    "entry12345Group": {
                        "NX_class": "NXentry",
                        "dataGroup": {
                            "NX_class": "NXdata",
                            "lkintimage": {
                                'value': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                                "shape": [10]
                            }
                        },
                        "instrumentGroup": {
                            "NX_class": "NXinstrument",
                            "detectorGroup": {
                                "NX_class": "NXdetector",
                                "intimage": {
                                    'value': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                                    "shape": [10]
                                }
                            }
                        },
                        "sampleGroup": {
                            "NX_class": "NXsample",
                            "depends_on": {
                                "value": "transformations/phi"
                            },
                            "name": {
                                "value": "water"
                            },
                            "transformationsGroup": {
                                "NX_class": "NXtransformations",
                                "phi": {
                                    "depends_on": "z",
                                    "type": "NX_FLOAT64",
                                    "source":
                                    "haso0000:10000/p/motor/m16/Position",
                                    "source_name": "sphi",
                                    "source_type": "TANGO",
                                    "strategy": "FINAL",
                                    "transformation_type": "rotation",
                                    "vector": [1, 0, 0],
                                    "unit": "deg",
                                    "value": 0.5
                                },
                                "z": {
                                    "type": "NX_FLOAT32",
                                    "source":
                                    "haso0000:10000/p/motor/m15/Position",
                                    "source_name": "sz",
                                    "source_type": "TANGO",
                                    "strategy": "INIT",
                                    "transformation_type": "translation",
                                    "vector": [0, 0, 1],
                                    "unit": "mm",
                                    "value": 0.5
                                }
                            }
                        }
                    }
                }
                self.myAssertDict(dct, res)
        finally:
            os.remove(filename)

    def test_metadata_attributes(self):
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
                "saxs",
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
                "waxs,saxs,PaNET01098"
            ],
        ]
        ltechs = [
            [
                {
                    'name': 'small angle x-ray scattering',
                    'pid':
                    'http://purl.org/pan-science/PaNET/PaNET01188'
                }
            ],
            [
                {
                    'name': 'wide angle x-ray scattering',
                    'pid':
                    'http://purl.org/pan-science/PaNET/PaNET01191'
                },
                {
                    'name': 'small angle x-ray scattering',
                    'pid':
                    'http://purl.org/pan-science/PaNET/PaNET01188'
                },
                {
                    'name': 'grazing incidence diffraction',
                    'pid':
                    'http://purl.org/pan-science/PaNET/PaNET01098'
                },
            ],
        ]
        sids = ["H20/1233123", "sample/12343"]
        iids = ["/fsec/e01", "/fsec/e02"]

        for k, arg in enumerate(args):
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            techniques = arg[9]
            ltech = ltechs[k]
            sid = sids[k]
            iid = iids[k]

            commands = [
                ('nxsfileinfo metadata %s %s -a units,NX_class '
                 ' -i 12344321 --pid-without-filename -q %s -j %s '
                 '  --instrument-id %s '
                 % (filename, self.flags, techniques, sid, iid)).split(),
                ('nxsfileinfo metadata %s %s  '
                 ' --beamtimeid 12344321 '
                 '--attributes units,NX_class --techniques %s --sample-id %s '
                 ' -y %s '
                 % (filename, self.flags, techniques, sid, iid)).split(),
                ('nxsfileinfo metadata %s %s -a units,NX_class'
                 ' --beamtimeid 12344321 -d --techniques %s -j %s -y %s '
                 % (filename, self.flags, techniques, sid, iid)).split(),
                ('nxsfileinfo metadata %s %s --attributes units,NX_class -q %s'
                 ' -i 12344321 --sample-id %s  --instrument-id %s '
                 % (filename, self.flags, techniques, sid, iid)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
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

                for kk, cmd in enumerate(commands):
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
                    # print(vl)

                    dct = json.loads(vl)
                    # print(dct)
                    res = {'pid': '12344321/12345',
                           'techniques': ltech,
                           'sampleId': sid,
                           'instrumentId': iid,
                           'scientificMetadata':
                           {'name': 'entry12345',
                            'data': {'NX_class': 'NXdata'},
                            'end_time': {'value': '%s' % arg[6]},
                            'experiment_identifier': {'value': '%s' % arg[2]},
                            'instrument': {
                                'NX_class': 'NXinstrument',
                                'detector': {
                                    'NX_class': 'NXdetector',
                                    'intimage': {
                                        'shape': [0, 30]}},
                                'name': {
                                    'value': '%s' % arg[3]}},
                            'sample': {
                                'NX_class': 'NXsample',
                                'chemical_formula': {'value': '%s' % arg[8]},
                                'name': {'value': '%s' % arg[7]}},
                            'start_time': {
                                'value': '%s' % arg[5]},
                            'title': {'value': '%s' % arg[1]}
                            },
                           'creationTime': '%s' % arg[6],
                           'endTime': '%s' % arg[6],
                           'description': '%s' % arg[1],
                           }
                    if kk % 2:
                        res['datasetName'] = "%s_12345" % fname
                    else:
                        res['datasetName'] = "12345"
                    self.myAssertDict(dct, res, skip=['pid'])
                    if kk % 2:
                        self.assertEqual(
                            dct["pid"], "12344321/%s_12345" % fname)
                    else:
                        self.assertEqual(
                            dct["pid"], "12344321/12345")
            finally:
                os.remove(filename)

    def test_metadata_attributes_description(self):
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
                'technique: "saxs"',
                'sample_id: "water/1234"'
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
                'techniques:\n'
                '  - "my new technique"\n'
                '  - "saxs"\n'
                '  - "PaNET01098"\n'
                'techniques_pids:\n'
                '  - "MNT1234353453ipo4pi"\n',
                'water/2134'
            ],
        ]
        sids = ["water/1234", "water/2134"]

        ltechs = [
            [
                {
                    'name': 'small angle x-ray scattering',
                    'pid':
                    'http://purl.org/pan-science/PaNET/PaNET01188'
                }
            ],
            [
                {
                    'name': 'my new technique',
                    'pid':
                    'MNT1234353453ipo4pi'
                },
                {
                    'name': 'small angle x-ray scattering',
                    'pid':
                    'http://purl.org/pan-science/PaNET/PaNET01188'
                },
                {
                    'name': 'grazing incidence diffraction',
                    'pid':
                    'http://purl.org/pan-science/PaNET/PaNET01098'
                },
            ],

        ]

        for k, arg in enumerate(args):
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            desc = arg[9]
            sdesc = arg[10]
            sid = sids[k]
            ltech = ltechs[k]

            commands = [
                ('nxsfileinfo metadata %s %s -a units,NX_class '
                 ' -i 12344321 --pid-without-filename'
                 % (filename, self.flags)).split(),
                ('nxsfileinfo metadata %s %s  '
                 ' --beamtimeid 12344321 '
                 '--attributes units,NX_class'
                 % (filename, self.flags)).split(),
                ('nxsfileinfo metadata %s %s -a units,NX_class'
                 ' --beamtimeid 12344321 -d'
                 % (filename, self.flags)).split(),
                ('nxsfileinfo metadata %s %s --attributes units,NX_class'
                 ' -i 12344321 '
                 % (filename, self.flags)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
                entry.create_field(
                    "experiment_description", "string").write(desc)
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
                sample.create_field(
                    "description", "string").write(sdesc)
                sfml = sample.create_field("chemical_formula", "string")
                sfml.write(formula)

                nxsfile.close()

                for kk, cmd in enumerate(commands):
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
                    # print(vl)

                    dct = json.loads(vl)
                    # print(dct)
                    res = {'pid': '12344321/12345',
                           'techniques': ltech,
                           'sampleId': sid,
                           'scientificMetadata':
                           {'name': 'entry12345',
                            'experiment_description': {
                                'value': desc
                            },
                            'data': {'NX_class': 'NXdata'},
                            'end_time': {'value': '%s' % arg[6]},
                            'experiment_identifier': {'value': '%s' % arg[2]},
                            'instrument': {
                                'NX_class': 'NXinstrument',
                                'detector': {
                                    'NX_class': 'NXdetector',
                                    'intimage': {
                                        'shape': [0, 30]}},
                                'name': {
                                    'value': '%s' % arg[3]}},
                            'sample': {
                                'NX_class': 'NXsample',
                                'chemical_formula': {'value': '%s' % arg[8]},
                                'description': {'value': '%s' % sdesc},
                                'name': {'value': '%s' % arg[7]}},
                            'start_time': {
                                'value': '%s' % arg[5]},
                            'title': {'value': '%s' % arg[1]}
                            },
                           'creationTime': '%s' % arg[6],
                           'endTime': '%s' % arg[6],
                           'description': '%s' % arg[1],
                           }
                    if kk % 2:
                        res['datasetName'] = "%s_12345" % fname
                    else:
                        res['datasetName'] = "12345"
                    self.myAssertDict(res, dct, skip=['pid'])
                    if kk % 2:
                        self.assertEqual(
                            dct["pid"], "12344321/%s_12345" % fname)
                    else:
                        self.assertEqual(
                            dct["pid"], "12344321/12345")
            finally:
                os.remove(filename)

    def test_metadata_hidden_attributes(self):
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
                ('nxsfileinfo metadata %s %s '
                 '-n nexdatas_strategy,nexdatas_source,NX_class'
                 % (filename, self.flags)).split(),
                ('nxsfileinfo metadata %s %s '
                 '--hidden-attributes'
                 ' nexdatas_strategy,nexdatas_source,NX_class'
                 % (filename, self.flags)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
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
                    # print(vl)
                    dct = json.loads(vl)
                    # print(dct)
                    res = {'scientificMetadata':
                           {
                            'name': 'entry12345',
                            'data': {},
                            'end_time': {'value': '%s' % arg[6]},
                            'experiment_identifier': {'value': '%s' % arg[2]},
                            'instrument': {
                                'detector': {
                                    'intimage': {
                                        'shape': [0, 30]}},
                                'name': {
                                    'short_name': '%s' % arg[4],
                                    'value': '%s' % arg[3]}},
                            'sample': {
                                'chemical_formula': {'value': '%s' % arg[8]},
                                'name': {'value': '%s' % arg[7]}},
                            'start_time': {
                                'value': '%s' % arg[5]},
                            'title': {'value': '%s' % arg[1]}},
                           'creationTime': '%s' % arg[6],
                           'endTime': '%s' % arg[6],
                           'description': '%s' % arg[1],
                           'techniques': [],
                           }
                    self.myAssertDict(dct, res)
            finally:
                os.remove(filename)

    def test_metadata_entry(self):
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
                ('nxsfileinfo metadata %s %s --pid 12341234 -t NXcollection'
                 % (filename, self.flags)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' -p 12341234 --entry-classes NXcollection'
                 % (filename, self.flags)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
                col.create_field("definition", "string").write("NXsaxs")
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

                    # print(vl)
                    self.assertEqual('', er)
                    dct = json.loads(vl)
                    res = {
                        'pid': '12341234',
                        'datasetName': '12341234',
                        'techniques': [{
                            'name': 'small angle x-ray scattering',
                            'pid':
                            'http://purl.org/pan-science/PaNET/PaNET01188'
                        }],
                        'scientificMetadata':
                        {"NX_class": "NXcollection",
                         "log1": {
                             "value": title
                         },
                         "definition": {
                             "value": "NXsaxs"
                         },
                         "name": "logs"
                         }
                    }

                    self.myAssertDict(dct, res)
            finally:
                os.remove(filename)

    def test_metadata_entrynames(self):
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
                ("nxsfileinfo metadata %s %s --pid 12341234 "
                 "-e logs --entry-classes \'\'"
                 % (filename, self.flags)).split(),
                ('nxsfileinfo metadata %s %s '
                 " -p 12341234 --entry-names logs -t \'\'"
                 % (filename, self.flags)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
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
                    dct = json.loads(vl)
                    res = {
                        'pid': '12341234',
                        'datasetName': '12341234',
                        'techniques': [],
                        'scientificMetadata':
                        {"NX_class": "NXcollection",
                         "log1": {
                             "value": title
                         },
                         "name": "logs"
                         }
                    }
                    self.myAssertDict(dct, res)
            finally:
                os.remove(filename)

    def test_metadata_duplications(self):
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

            commands = [
                ('nxsfileinfo metadata %s %s '
                 % (filename, self.flags)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                entry.create_group("instrument", "NXinstrument")
                sattr = entry.attributes.create(
                    "instrument", "string")
                sattr.write("duplicated")

                entry.create_field("title", "string").write(title)
                sattr = entry.attributes.create("title", "string")
                sattr.write("duplicated")
                filewriter.link("/entry12345/instrument/detector/intimage",
                                entry, "missingfield")

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
                    dct = json.loads(vl)
                    res = {'scientificMetadata':
                           {'name': 'entry12345',
                            'instrument_': 'duplicated',
                            'instrument': {
                                'NX_class': 'NXinstrument'},
                            'missingfield': {},
                            'title_': 'duplicated',
                            'title': {'value': '%s' % arg[1]},
                            },
                           'description': '%s' % arg[1],
                           'techniques': [],
                           }
                    self.myAssertDict(dct, res)
            finally:
                os.remove(filename)

    def test_metadata_beamtime(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "p01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

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
                "0o666",
                "0666",
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
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            chmod = arg[9]
            chmod2 = arg[10]

            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s'
                 ' --sample-id-from-name '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 ' --sample-id-from-name '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --sample-id-from-name '
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --sample-id-from-name '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
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

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    res = {
                        'techniques': [],
                        'sampleId': arg[7],
                        "contactEmail": "robust.robust@robust.com",
                        "createdAt": "2020-01-20T00:10:00Z",
                        "pid": "13243546",
                        "ownerGroup": "16171271-dmgt",
                        "accessGroups": [
                            '16171271-dmgt', '16171271-clbt', '16171271-part',
                            'p01dmgt', 'p01staff'],
                        "datasetName": "%s_12345" % fname,
                        "creationLocation": "/DESY/PETRA III/p01",
                        'instrumentId': '/petra3/p01',
                        # "description":
                        # "beautiful-cornflower-wallaby-of-agreement",
                        # "endTime": "2020-01-21T12:37:00Z",
                        "owner": "glossy",
                        "ownerEmail": "feathered.feathered@feathered.com",
                        "principalInvestigator": "robust.robust@robust.com",
                        "proposalId": "16171271",
                        "scientificMetadata": {
                            "beamtimeId": "16171271",
                            "DOOR_proposalId": "65300407",
                            "user_comments": "Awesome comment",
                            "data": {
                                "NX_class": "NXdata"
                            },
                            "end_time": {
                                "value": "2014-02-16T15:17:21+00:00"
                            },
                            "experiment_identifier": {
                                "value": '%s' % arg[2]
                            },
                            "instrument": {
                                "NX_class": "NXinstrument",
                                "detector": {
                                    "NX_class": "NXdetector",
                                    "intimage": {
                                        "shape": [
                                            0,
                                            30
                                        ]
                                    }
                                },
                                "name": {
                                    "short_name": '%s' % arg[4],
                                    "value": '%s' % arg[3]
                                }
                            },
                            "name": "entry12345",
                            "sample": {
                                "NX_class": "NXsample",
                                "chemical_formula": {
                                    "value": '%s' % arg[8]
                                },
                                "name": {
                                    "value": '%s' % arg[7]
                                }
                            },
                            "start_time": {
                                "value": '%s' % arg[5]
                            },
                            "title": {
                                "value": '%s' % arg[1]
                            }
                        },
                        "sourceFolder":
                        "/asap3/petra3/gpfs/p01/2020/data/12345678",
                        "type": "raw",
                        "isPublished": False,
                        "updatedAt": "2020-01-20T00:10:00Z",
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'description': '%s' % arg[1],
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s_12345" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s_12345" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_metadata_beamtime_fio(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "p01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

        args = [
            [
                "mymeta2_00011.fio",
                "0o666",
                "0666",
            ],
            [
                "mymeta2_00011.fio",
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            chmod = arg[1]
            chmod2 = arg[2]

            shutil.copy("test/files/%s" % filename, filename)
            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    # print(dct)
                    res = {
                        'accessGroups': [
                            '16171271-dmgt',
                            '16171271-clbt',
                            '16171271-part',
                            'p01dmgt',
                            'p01staff'],
                        'contactEmail': 'robust.robust@robust.com',
                        'createdAt': '2020-01-20T00:10:00Z',
                        'creationLocation': '/DESY/PETRA III/p01',
                        'instrumentId': '/petra3/p01',
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'datasetName': 'mymeta2_00011',
                        'description':
                        'beautiful-cornflower-wallaby-of-agreement',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'isPublished': False,
                        'owner': 'glossy',
                        'ownerEmail': 'feathered.feathered@feathered.com',
                        'ownerGroup': '16171271-dmgt',
                        'pid': '16171271/mymeta2_00011/'
                        '57f418a9-095b-442a-b512-1f9b2c65973c',
                        'principalInvestigator': 'robust.robust@robust.com',
                        'proposalId': '16171271',
                        'scientificMetadata': {
                            'DOOR_proposalId': '65300407',
                            'ScanCommand': 'ascan exp_mot04 0.0 4.0 4 0.5',
                            'beamtimeId': '16171271',
                            'comments': {
                                'line_1': 'ascan exp_mot04 0.0 4.0 4 0.5',
                                'line_2':
                                'user jkotan Acquisition started at '
                                'Thu Dec  8 17:00:43 2022'
                            },
                            'end_time': {'value': '2014-02-16T15:17:21+00:00'},
                            'parameters': {
                                'abs': 1423,
                                'anav': 5.14532,
                                'atten': 99777400.0,
                                'bpm1': 7,
                                'hkl': [
                                    0.0031110747648095565,
                                    0.0024437328201669176,
                                    0.1910783136442638],
                                'rois_p100k': [228, 115, 238, 123, 227, 97,
                                               252, 130, 238, 115, 248, 123],
                                'sdd': None,
                                'signalcounter':
                                'p100k_roi1',
                                'ubmatrix':
                                '[[ 0.82633922 -0.80961862 -0.01117831]; '
                                '[ 0.02460193  0.0091408   1.15661358]; '
                                '[-0.80932194 -0.82636427  0.02374563]]'
                            },
                            'start_time': 'Thu Dec  8 17:00:43 2022',
                            'user_comments': 'Awesome comment'},
                        'sourceFolder':
                        '/asap3/petra3/gpfs/p01/2020/data/12345678',
                        'techniques': [],
                        'type': 'raw',
                        'updatedAt': '2020-01-20T00:10:00Z'
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_metadata_beamtime_fio_oned(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "p01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''

        cpfname = '%s/copymap-12345678.json' % (os.getcwd())

        copymapfile = '''{
        "scientificMetadata.data": null,
        "scientificMetadata.parameters": null,
            "scientificMetadata.hkl":
        "scientificMetadata.parameters.hkl",
        "scientificMetadata.timestamp":
        "scientificMetadata.data.timestamp"
        }
        '''

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

        args = [
            [
                "mymeta2_00011.fio",
                "0o666",
                "0666",
            ],
            [
                "mymeta2_00011.fio",
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            chmod = arg[1]
            chmod2 = arg[2]

            shutil.copy("test/files/%s" % filename, filename)
            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s'
                 ' --copy-map-file %s '
                 ' --oned '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, cpfname)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 ' --copy-map-file %s '
                 ' --oned '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, cpfname)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --oned '
                 ' --copy-map-file %s '
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, cpfname)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --oned '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 ' --copy-map-file %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, cpfname)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(cpfname, "w") as fl:
                    fl.write(copymapfile)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    # print(dct)
                    res = {
                        'accessGroups': [
                            '16171271-dmgt',
                            '16171271-clbt',
                            '16171271-part',
                            'p01dmgt',
                            'p01staff'],
                        'contactEmail': 'robust.robust@robust.com',
                        'createdAt': '2020-01-20T00:10:00Z',
                        'creationLocation': '/DESY/PETRA III/p01',
                        'instrumentId': '/petra3/p01',
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'datasetName': 'mymeta2_00011',
                        'description':
                        'beautiful-cornflower-wallaby-of-agreement',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'isPublished': False,
                        'owner': 'glossy',
                        'ownerEmail': 'feathered.feathered@feathered.com',
                        'ownerGroup': '16171271-dmgt',
                        'pid': '16171271/mymeta2_00011/'
                        '57f418a9-095b-442a-b512-1f9b2c65973c',
                        'principalInvestigator': 'robust.robust@robust.com',
                        'proposalId': '16171271',
                        'scientificMetadata': {
                            'DOOR_proposalId': '65300407',
                            'ScanCommand': 'ascan exp_mot04 0.0 4.0 4 0.5',
                            'beamtimeId': '16171271',
                            'comments': {
                                'line_1': 'ascan exp_mot04 0.0 4.0 4 0.5',
                                'line_2':
                                'user jkotan Acquisition started at '
                                'Thu Dec  8 17:00:43 2022'
                            },
                            'hkl': [
                                0.0031110747648095565,
                                0.0024437328201669176,
                                0.1910783136442638],
                            'timestamp': [2.284174680709839,
                                          3.3944602012634277,
                                          4.407033920288086,
                                          5.524206161499023,
                                          6.656368255615234],
                            'end_time': {'value': '2014-02-16T15:17:21+00:00'},
                            'start_time': 'Thu Dec  8 17:00:43 2022',
                            'user_comments': 'Awesome comment'},
                        'sourceFolder':
                        '/asap3/petra3/gpfs/p01/2020/data/12345678',
                        'techniques': [],
                        'type': 'raw',
                        'updatedAt': '2020-01-20T00:10:00Z'
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s" % fname))
            finally:
                if os.path.isfile(cpfname):
                    os.remove(cpfname)
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_metadata_beamtime_copymapfile(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "p01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())
        cpfname = '%s/copymap-12345678.json' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''
        copymapfile = '''{
        "scientificMetadata.instrument": null,
        "scientificMetadata.sample": null,
        "scientificMetadata.instrument_name":
            "scientificMetadata.instrument.name.value",
        "scientificMetadata.chemical_formula.value":
            "scientificMetadata.sample.chemical_formula",
        "scientificMetadata.sample_name":
            "scientificMetadata.sample.name.value"
        }
        '''

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

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
                "0o666",
                "0666",
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
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            chmod = arg[9]
            chmod2 = arg[10]

            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s '
                 ' --copy-map-file %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, cpfname)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --copy-map-file %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    cpfname, ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --copy-map-file %s '
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, cpfname)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --copy-map-file %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    cpfname, ofname, chmod)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)
                with open(cpfname, "w") as fl:
                    fl.write(copymapfile)

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
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

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    # print(dct)
                    res = {
                        'techniques': [],
                        "contactEmail": "robust.robust@robust.com",
                        "createdAt": "2020-01-20T00:10:00Z",
                        "pid": "13243546",
                        "ownerGroup": "16171271-dmgt",
                        "accessGroups": [
                            '16171271-dmgt', '16171271-clbt', '16171271-part',
                            'p01dmgt', 'p01staff'],
                        "datasetName": "%s_12345" % fname,
                        "creationLocation": "/DESY/PETRA III/p01",
                        'instrumentId': '/petra3/p01',
                        # "description":
                        # "beautiful-cornflower-wallaby-of-agreement",
                        # "endTime": "2020-01-21T12:37:00Z",
                        "owner": "glossy",
                        "ownerEmail": "feathered.feathered@feathered.com",
                        "principalInvestigator": "robust.robust@robust.com",
                        "proposalId": "16171271",
                        "scientificMetadata": {
                            "beamtimeId": "16171271",
                            "DOOR_proposalId": "65300407",
                            "user_comments": "Awesome comment",
                            "data": {
                                "NX_class": "NXdata"
                            },
                            "end_time": {
                                "value": "2014-02-16T15:17:21+00:00"
                            },
                            "experiment_identifier": {
                                "value": '%s' % arg[2]
                            },
                            "instrument_name": arg[3],
                            "sample_name": arg[7],
                            "name": "entry12345",
                            "start_time": {
                                "value": '%s' % arg[5]
                            },
                            "title": {
                                "value": '%s' % arg[1]
                            }
                        },
                        "sourceFolder":
                        "/asap3/petra3/gpfs/p01/2020/data/12345678",
                        "type": "raw",
                        "isPublished": False,
                        "updatedAt": "2020-01-20T00:10:00Z",
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'description': '%s' % arg[1],
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s_12345" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s_12345" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)
                if os.path.isfile(cpfname):
                    os.remove(cpfname)

    def test_metadata_beamtime_copymapfile_yaml(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "p01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())
        cpfname = '%s/copymap-12345678.yaml' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''
        copymapfile = '"scientificMetadata.instrument": null\n' + \
            '"scientificMetadata.sample": null\n' + \
            '"scientificMetadata.instrument_name":' + \
            ' "scientificMetadata.instrument.name.value"\n' + \
            '"scientificMetadata.sample_name":' + \
            ' "scientificMetadata.sample.name.value"\n'

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

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
                "0o666",
                "0666",
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
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            chmod = arg[9]
            chmod2 = arg[10]

            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s '
                 ' --copy-map-file %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, cpfname)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --copy-map-file %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    cpfname, ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --copy-map-file %s '
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, cpfname)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --copy-map-file %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    cpfname, ofname, chmod)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)
                with open(cpfname, "w") as fl:
                    fl.write(copymapfile)

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
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

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    # print(dct)
                    res = {
                        'techniques': [],
                        "contactEmail": "robust.robust@robust.com",
                        "createdAt": "2020-01-20T00:10:00Z",
                        "pid": "13243546",
                        "ownerGroup": "16171271-dmgt",
                        "accessGroups": [
                            '16171271-dmgt', '16171271-clbt', '16171271-part',
                            'p01dmgt', 'p01staff'],
                        "datasetName": "%s_12345" % fname,
                        "creationLocation": "/DESY/PETRA III/p01",
                        'instrumentId': '/petra3/p01',
                        # "description":
                        # "beautiful-cornflower-wallaby-of-agreement",
                        # "endTime": "2020-01-21T12:37:00Z",
                        "owner": "glossy",
                        "ownerEmail": "feathered.feathered@feathered.com",
                        "principalInvestigator": "robust.robust@robust.com",
                        "proposalId": "16171271",
                        "scientificMetadata": {
                            "beamtimeId": "16171271",
                            "DOOR_proposalId": "65300407",
                            "user_comments": "Awesome comment",
                            "data": {
                                "NX_class": "NXdata"
                            },
                            "end_time": {
                                "value": "2014-02-16T15:17:21+00:00"
                            },
                            "experiment_identifier": {
                                "value": '%s' % arg[2]
                            },
                            "instrument_name": arg[3],
                            "sample_name": arg[7],
                            "name": "entry12345",
                            "start_time": {
                                "value": '%s' % arg[5]
                            },
                            "title": {
                                "value": '%s' % arg[1]
                            }
                        },
                        "sourceFolder":
                        "/asap3/petra3/gpfs/p01/2020/data/12345678",
                        "type": "raw",
                        "isPublished": False,
                        "updatedAt": "2020-01-20T00:10:00Z",
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'description': '%s' % arg[1],
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s_12345" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s_12345" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)
                if os.path.isfile(cpfname):
                    os.remove(cpfname)

    def test_metadata_beamtime_copymap(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "p01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''
        copymap = '{"scientificMetadata.instrument":null,' + \
            '"scientificMetadata.sample":null,' + \
            '"scientificMetadata.instrument_name":' + \
            '"scientificMetadata.instrument.name.value",' + \
            '"scientificMetadata.sample_name":' + \
            '"scientificMetadata.sample.name.value"}'

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

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
                "0o666",
                "0666",
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
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            chmod = arg[9]
            chmod2 = arg[10]

            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s '
                 ' --copy-map %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, copymap)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --copy-map %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    copymap, ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --copy-map %s '
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, copymap)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --copy-map %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    copymap, ofname, chmod)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
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

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    # print(dct)
                    res = {
                        'techniques': [],
                        "contactEmail": "robust.robust@robust.com",
                        "createdAt": "2020-01-20T00:10:00Z",
                        "pid": "13243546",
                        "ownerGroup": "16171271-dmgt",
                        "accessGroups": [
                            '16171271-dmgt', '16171271-clbt', '16171271-part',
                            'p01dmgt', 'p01staff'],
                        "datasetName": "%s_12345" % fname,
                        "creationLocation": "/DESY/PETRA III/p01",
                        'instrumentId': '/petra3/p01',
                        # "description":
                        # "beautiful-cornflower-wallaby-of-agreement",
                        # "endTime": "2020-01-21T12:37:00Z",
                        "owner": "glossy",
                        "ownerEmail": "feathered.feathered@feathered.com",
                        "principalInvestigator": "robust.robust@robust.com",
                        "proposalId": "16171271",
                        "scientificMetadata": {
                            "beamtimeId": "16171271",
                            "DOOR_proposalId": "65300407",
                            "user_comments": "Awesome comment",
                            "data": {
                                "NX_class": "NXdata"
                            },
                            "end_time": {
                                "value": "2014-02-16T15:17:21+00:00"
                            },
                            "experiment_identifier": {
                                "value": '%s' % arg[2]
                            },
                            "instrument_name": arg[3],
                            "sample_name": arg[7],
                            "name": "entry12345",
                            "start_time": {
                                "value": '%s' % arg[5]
                            },
                            "title": {
                                "value": '%s' % arg[1]
                            }
                        },
                        "sourceFolder":
                        "/asap3/petra3/gpfs/p01/2020/data/12345678",
                        "type": "raw",
                        "isPublished": False,
                        "updatedAt": "2020-01-20T00:10:00Z",
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'description': '%s' % arg[1],
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s_12345" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s_12345" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_metadata_beamtime_copymapfield(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "p01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''
        copymap = '{"scientificMetadata.instrument":null,' + \
            '"scientificMetadata.sample":null,' + \
            '"scientificMetadata.nxsfileinfo_parameters":null,' + \
            '"scientificMetadata.instrument_name":' + \
            '"scientificMetadata.instrument.name.value",' + \
            '"scientificMetadata.sample_name":' + \
            '"scientificMetadata.sample.name.value"}'

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

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
                "0o666",
                "0666",
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
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            chmod = arg[9]
            chmod2 = arg[10]

            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("detector", "NXdetector")
                entry.create_group("data", "NXdata")
                par = entry.create_group(
                    "nxsfileinfo_parameters", "NXparameters")
                par.create_field("copymap", "string").write(copymap)

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

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    # print(dct)
                    res = {
                        'techniques': [],
                        "contactEmail": "robust.robust@robust.com",
                        "createdAt": "2020-01-20T00:10:00Z",
                        "pid": "13243546",
                        "ownerGroup": "16171271-dmgt",
                        "accessGroups": [
                            '16171271-dmgt', '16171271-clbt', '16171271-part',
                            'p01dmgt', 'p01staff'],
                        "datasetName": "%s_12345" % fname,
                        "creationLocation": "/DESY/PETRA III/p01",
                        'instrumentId': '/petra3/p01',
                        # "description":
                        # "beautiful-cornflower-wallaby-of-agreement",
                        # "endTime": "2020-01-21T12:37:00Z",
                        "owner": "glossy",
                        "ownerEmail": "feathered.feathered@feathered.com",
                        "principalInvestigator": "robust.robust@robust.com",
                        "proposalId": "16171271",
                        "scientificMetadata": {
                            "beamtimeId": "16171271",
                            "DOOR_proposalId": "65300407",
                            "user_comments": "Awesome comment",
                            "data": {
                                "NX_class": "NXdata"
                            },
                            "end_time": {
                                "value": "2014-02-16T15:17:21+00:00"
                            },
                            "experiment_identifier": {
                                "value": '%s' % arg[2]
                            },
                            "instrument_name": arg[3],
                            "sample_name": arg[7],
                            "name": "entry12345",
                            "start_time": {
                                "value": '%s' % arg[5]
                            },
                            "title": {
                                "value": '%s' % arg[1]
                            }
                        },
                        "sourceFolder":
                        "/asap3/petra3/gpfs/p01/2020/data/12345678",
                        "type": "raw",
                        "isPublished": False,
                        "updatedAt": "2020-01-20T00:10:00Z",
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'description': '%s' % arg[1],
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s_12345" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s_12345" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_metadata_beamtime_copymapfield_yaml(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "p01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''
        copymap = '"scientificMetadata.instrument": null\n' + \
            '"scientificMetadata.nxsfileinfo_parameters": null\n' + \
            '"scientificMetadata.sample": null\n' + \
            '"scientificMetadata.instrument_name":' + \
            ' "scientificMetadata.instrument.name.value"\n' + \
            '"scientificMetadata.sample_name":' + \
            ' "scientificMetadata.sample.name.value"'

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

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
                "0o666",
                "0666",
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
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            chmod = arg[9]
            chmod2 = arg[10]

            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("detector", "NXdetector")
                entry.create_group("data", "NXdata")
                par = entry.create_group(
                    "nxsfileinfo_parameters", "NXparameters")
                par.create_field("copymap", "string").write(copymap)

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

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    # print(dct)
                    res = {
                        'techniques': [],
                        "contactEmail": "robust.robust@robust.com",
                        "createdAt": "2020-01-20T00:10:00Z",
                        "pid": "13243546",
                        "ownerGroup": "16171271-dmgt",
                        "accessGroups": [
                            '16171271-dmgt', '16171271-clbt', '16171271-part',
                            'p01dmgt', 'p01staff'],
                        "datasetName": "%s_12345" % fname,
                        "creationLocation": "/DESY/PETRA III/p01",
                        'instrumentId': '/petra3/p01',
                        # "description":
                        # "beautiful-cornflower-wallaby-of-agreement",
                        # "endTime": "2020-01-21T12:37:00Z",
                        "owner": "glossy",
                        "ownerEmail": "feathered.feathered@feathered.com",
                        "principalInvestigator": "robust.robust@robust.com",
                        "proposalId": "16171271",
                        "scientificMetadata": {
                            "beamtimeId": "16171271",
                            "DOOR_proposalId": "65300407",
                            "user_comments": "Awesome comment",
                            "data": {
                                "NX_class": "NXdata"
                            },
                            "end_time": {
                                "value": "2014-02-16T15:17:21+00:00"
                            },
                            "experiment_identifier": {
                                "value": '%s' % arg[2]
                            },
                            "instrument_name": arg[3],
                            "sample_name": arg[7],
                            "name": "entry12345",
                            "start_time": {
                                "value": '%s' % arg[5]
                            },
                            "title": {
                                "value": '%s' % arg[1]
                            }
                        },
                        "sourceFolder":
                        "/asap3/petra3/gpfs/p01/2020/data/12345678",
                        "type": "raw",
                        "isPublished": False,
                        "updatedAt": "2020-01-20T00:10:00Z",
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'description': '%s' % arg[1],
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s_12345" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s_12345" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_metadata_beamtime_copylistfile(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "p01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())
        cpfname = '%s/copymap-12345678.lst' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''
        copymapfile = 'scientificMetadata.instrument\n' + \
            'scientificMetadata.sample\n' + \
            'scientificMetadata.instrument_name ' + \
            'scientificMetadata.instrument.name.value\n' + \
            'scientificMetadata.sample_name ' + \
            'scientificMetadata.sample.name.value\n' + \
            '# scientificMetadata.chemical_formula ' + \
            'scientificMetadata.sample.chemical_formula.value'

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

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
                "0o666",
                "0666",
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
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            chmod = arg[9]
            chmod2 = arg[10]

            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s '
                 ' --copy-map-file %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, cpfname)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --copy-map-file %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    cpfname, ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --copy-map-file %s '
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, cpfname)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --copy-map-file %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    cpfname, ofname, chmod)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)
                with open(cpfname, "w") as fl:
                    fl.write(copymapfile)

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
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

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    # print(dct)
                    res = {
                        'techniques': [],
                        "contactEmail": "robust.robust@robust.com",
                        "createdAt": "2020-01-20T00:10:00Z",
                        "pid": "13243546",
                        "ownerGroup": "16171271-dmgt",
                        "accessGroups": [
                            '16171271-dmgt', '16171271-clbt', '16171271-part',
                            'p01dmgt', 'p01staff'],
                        "datasetName": "%s_12345" % fname,
                        "creationLocation": "/DESY/PETRA III/p01",
                        'instrumentId': '/petra3/p01',
                        # "description":
                        # "beautiful-cornflower-wallaby-of-agreement",
                        # "endTime": "2020-01-21T12:37:00Z",
                        "owner": "glossy",
                        "ownerEmail": "feathered.feathered@feathered.com",
                        "principalInvestigator": "robust.robust@robust.com",
                        "proposalId": "16171271",
                        "scientificMetadata": {
                            "beamtimeId": "16171271",
                            "DOOR_proposalId": "65300407",
                            "user_comments": "Awesome comment",
                            "data": {
                                "NX_class": "NXdata"
                            },
                            "end_time": {
                                "value": "2014-02-16T15:17:21+00:00"
                            },
                            "experiment_identifier": {
                                "value": '%s' % arg[2]
                            },
                            "instrument_name": arg[3],
                            "sample_name": arg[7],
                            "name": "entry12345",
                            "start_time": {
                                "value": '%s' % arg[5]
                            },
                            "title": {
                                "value": '%s' % arg[1]
                            }
                        },
                        "sourceFolder":
                        "/asap3/petra3/gpfs/p01/2020/data/12345678",
                        "type": "raw",
                        "isPublished": False,
                        "updatedAt": "2020-01-20T00:10:00Z",
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'description': '%s' % arg[1],
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s_12345" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s_12345" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)
                if os.path.isfile(cpfname):
                    os.remove(cpfname)

    def test_metadata_beamtime_copylistfile_json(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "p01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())
        cpfname = '%s/copymap-12345678.json' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''
        copymapfile = '''[
          ["scientificMetadata.instrument", null],
          ["scientificMetadata.sample"],
          ["scientificMetadata.instrument_name",
            "scientificMetadata.instrument.name.value"],
          ["scientificMetadata.sample_name",
            "scientificMetadata.sample.name.value"],
          ["scientificMetadata.chemical_formula.value",
            "scientificMetadata.sample.chemical_formula"]
           ]
        '''

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

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
                "0o666",
                "0666",
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
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            chmod = arg[9]
            chmod2 = arg[10]

            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s '
                 ' --copy-map-file %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, cpfname)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --copy-map-file %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    cpfname, ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --copy-map-file %s '
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, cpfname)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --copy-map-file %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    cpfname, ofname, chmod)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)
                with open(cpfname, "w") as fl:
                    fl.write(copymapfile)

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
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

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    # print(dct)
                    res = {
                        'techniques': [],
                        "contactEmail": "robust.robust@robust.com",
                        "createdAt": "2020-01-20T00:10:00Z",
                        "pid": "13243546",
                        "ownerGroup": "16171271-dmgt",
                        "accessGroups": [
                            '16171271-dmgt', '16171271-clbt', '16171271-part',
                            'p01dmgt', 'p01staff'],
                        "datasetName": "%s_12345" % fname,
                        "creationLocation": "/DESY/PETRA III/p01",
                        'instrumentId': '/petra3/p01',
                        # "description":
                        # "beautiful-cornflower-wallaby-of-agreement",
                        # "endTime": "2020-01-21T12:37:00Z",
                        "owner": "glossy",
                        "ownerEmail": "feathered.feathered@feathered.com",
                        "principalInvestigator": "robust.robust@robust.com",
                        "proposalId": "16171271",
                        "scientificMetadata": {
                            "beamtimeId": "16171271",
                            "DOOR_proposalId": "65300407",
                            "user_comments": "Awesome comment",
                            "data": {
                                "NX_class": "NXdata"
                            },
                            "end_time": {
                                "value": "2014-02-16T15:17:21+00:00"
                            },
                            "experiment_identifier": {
                                "value": '%s' % arg[2]
                            },
                            "instrument_name": arg[3],
                            "sample_name": arg[7],
                            "name": "entry12345",
                            "start_time": {
                                "value": '%s' % arg[5]
                            },
                            "title": {
                                "value": '%s' % arg[1]
                            }
                        },
                        "sourceFolder":
                        "/asap3/petra3/gpfs/p01/2020/data/12345678",
                        "type": "raw",
                        "isPublished": False,
                        "updatedAt": "2020-01-20T00:10:00Z",
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'description': '%s' % arg[1],
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s_12345" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s_12345" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)
                if os.path.isfile(cpfname):
                    os.remove(cpfname)

    def test_metadata_beamtime_copylistfile_yaml(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "p01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())
        cpfname = '%s/copymap-12345678.yaml' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''
        copymapfile = '- [ "scientificMetadata.instrument",  null]\n' + \
            '- [ "scientificMetadata.sample"]\n' + \
            '- ["scientificMetadata.instrument_name", ' + \
            ' "scientificMetadata.instrument.name.value"]\n' + \
            '- ["scientificMetadata.sample_name",' + \
            ' "scientificMetadata.sample.name.value"]\n'

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

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
                "0o666",
                "0666",
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
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            chmod = arg[9]
            chmod2 = arg[10]

            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s '
                 ' --copy-map-file %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, cpfname)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --copy-map-file %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    cpfname, ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --copy-map-file %s '
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, cpfname)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --copy-map-file %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    cpfname, ofname, chmod)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)
                with open(cpfname, "w") as fl:
                    fl.write(copymapfile)

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
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

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    # print(dct)
                    res = {
                        'techniques': [],
                        "contactEmail": "robust.robust@robust.com",
                        "createdAt": "2020-01-20T00:10:00Z",
                        "pid": "13243546",
                        "ownerGroup": "16171271-dmgt",
                        "accessGroups": [
                            '16171271-dmgt', '16171271-clbt', '16171271-part',
                            'p01dmgt', 'p01staff'],
                        "datasetName": "%s_12345" % fname,
                        "creationLocation": "/DESY/PETRA III/p01",
                        'instrumentId': '/petra3/p01',
                        # "description":
                        # "beautiful-cornflower-wallaby-of-agreement",
                        # "endTime": "2020-01-21T12:37:00Z",
                        "owner": "glossy",
                        "ownerEmail": "feathered.feathered@feathered.com",
                        "principalInvestigator": "robust.robust@robust.com",
                        "proposalId": "16171271",
                        "scientificMetadata": {
                            "beamtimeId": "16171271",
                            "DOOR_proposalId": "65300407",
                            "user_comments": "Awesome comment",
                            "data": {
                                "NX_class": "NXdata"
                            },
                            "end_time": {
                                "value": "2014-02-16T15:17:21+00:00"
                            },
                            "experiment_identifier": {
                                "value": '%s' % arg[2]
                            },
                            "instrument_name": arg[3],
                            "sample_name": arg[7],
                            "name": "entry12345",
                            "start_time": {
                                "value": '%s' % arg[5]
                            },
                            "title": {
                                "value": '%s' % arg[1]
                            }
                        },
                        "sourceFolder":
                        "/asap3/petra3/gpfs/p01/2020/data/12345678",
                        "type": "raw",
                        "isPublished": False,
                        "updatedAt": "2020-01-20T00:10:00Z",
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'description': '%s' % arg[1],
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s_12345" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s_12345" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)
                if os.path.isfile(cpfname):
                    os.remove(cpfname)

    def test_metadata_beamtime_copylist_json(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "p01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''
        copymap = '[["scientificMetadata.instrument",null],' + \
            '["scientificMetadata.sample"],' + \
            '["scientificMetadata.instrument_name",' + \
            '"scientificMetadata.instrument.name.value"],' + \
            '["scientificMetadata.sample_name",' + \
            '"scientificMetadata.sample.name.value"]]'

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

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
                "0o666",
                "0666",
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
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            chmod = arg[9]
            chmod2 = arg[10]

            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s '
                 ' --copy-map %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, copymap)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --copy-map %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    copymap, ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --copy-map %s '
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod, copymap)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --copy-map %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    copymap, ofname, chmod)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
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

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    # print(dct)
                    res = {
                        'techniques': [],
                        "contactEmail": "robust.robust@robust.com",
                        "createdAt": "2020-01-20T00:10:00Z",
                        "pid": "13243546",
                        "ownerGroup": "16171271-dmgt",
                        "accessGroups": [
                            '16171271-dmgt', '16171271-clbt', '16171271-part',
                            'p01dmgt', 'p01staff'],
                        "datasetName": "%s_12345" % fname,
                        "creationLocation": "/DESY/PETRA III/p01",
                        'instrumentId': '/petra3/p01',
                        # "description":
                        # "beautiful-cornflower-wallaby-of-agreement",
                        # "endTime": "2020-01-21T12:37:00Z",
                        "owner": "glossy",
                        "ownerEmail": "feathered.feathered@feathered.com",
                        "principalInvestigator": "robust.robust@robust.com",
                        "proposalId": "16171271",
                        "scientificMetadata": {
                            "beamtimeId": "16171271",
                            "DOOR_proposalId": "65300407",
                            "user_comments": "Awesome comment",
                            "data": {
                                "NX_class": "NXdata"
                            },
                            "end_time": {
                                "value": "2014-02-16T15:17:21+00:00"
                            },
                            "experiment_identifier": {
                                "value": '%s' % arg[2]
                            },
                            "instrument_name": arg[3],
                            "sample_name": arg[7],
                            "name": "entry12345",
                            "start_time": {
                                "value": '%s' % arg[5]
                            },
                            "title": {
                                "value": '%s' % arg[1]
                            }
                        },
                        "sourceFolder":
                        "/asap3/petra3/gpfs/p01/2020/data/12345678",
                        "type": "raw",
                        "isPublished": False,
                        "updatedAt": "2020-01-20T00:10:00Z",
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'description': '%s' % arg[1],
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s_12345" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s_12345" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_metadata_beamtime_copylistfield(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "p01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''
        copymap = 'scientificMetadata.instrument\n' + \
            'scientificMetadata.sample\n' + \
            'scientificMetadata.nxsfileinfo_parameters\n' + \
            'scientificMetadata.instrument_name ' + \
            'scientificMetadata.instrument.name.value\n' + \
            'scientificMetadata.sample_name ' + \
            'scientificMetadata.sample.name.value'

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

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
                "0o666",
                "0666",
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
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            chmod = arg[9]
            chmod2 = arg[10]

            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("detector", "NXdetector")
                entry.create_group("data", "NXdata")
                par = entry.create_group(
                    "nxsfileinfo_parameters", "NXparameters")
                par.create_field("copymap", "string").write(copymap)

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

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    # print(dct)
                    res = {
                        'techniques': [],
                        "contactEmail": "robust.robust@robust.com",
                        "createdAt": "2020-01-20T00:10:00Z",
                        "pid": "13243546",
                        "ownerGroup": "16171271-dmgt",
                        "accessGroups": [
                            '16171271-dmgt', '16171271-clbt', '16171271-part',
                            'p01dmgt', 'p01staff'],
                        "datasetName": "%s_12345" % fname,
                        "creationLocation": "/DESY/PETRA III/p01",
                        'instrumentId': '/petra3/p01',
                        # "description":
                        # "beautiful-cornflower-wallaby-of-agreement",
                        # "endTime": "2020-01-21T12:37:00Z",
                        "owner": "glossy",
                        "ownerEmail": "feathered.feathered@feathered.com",
                        "principalInvestigator": "robust.robust@robust.com",
                        "proposalId": "16171271",
                        "scientificMetadata": {
                            "beamtimeId": "16171271",
                            "DOOR_proposalId": "65300407",
                            "user_comments": "Awesome comment",
                            "data": {
                                "NX_class": "NXdata"
                            },
                            "end_time": {
                                "value": "2014-02-16T15:17:21+00:00"
                            },
                            "experiment_identifier": {
                                "value": '%s' % arg[2]
                            },
                            "instrument_name": arg[3],
                            "sample_name": arg[7],
                            "name": "entry12345",
                            "start_time": {
                                "value": '%s' % arg[5]
                            },
                            "title": {
                                "value": '%s' % arg[1]
                            }
                        },
                        "sourceFolder":
                        "/asap3/petra3/gpfs/p01/2020/data/12345678",
                        "type": "raw",
                        "isPublished": False,
                        "updatedAt": "2020-01-20T00:10:00Z",
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'description': '%s' % arg[1],
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s_12345" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s_12345" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_metadata_beamtime_copylistfield_json(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "p01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''
        copymap = '[["scientificMetadata.instrument", null],' + \
            '["scientificMetadata.nxsfileinfo_parameters"],' + \
            '["scientificMetadata.sample"],' + \
            '["scientificMetadata.instrument_name",' + \
            ' "scientificMetadata.instrument.name.value"],' + \
            '["scientificMetadata.sample_name",' + \
            ' "scientificMetadata.sample.name.value"]]'

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

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
                "0o666",
                "0666",
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
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            chmod = arg[9]
            chmod2 = arg[10]

            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("detector", "NXdetector")
                entry.create_group("data", "NXdata")
                par = entry.create_group(
                    "nxsfileinfo_parameters", "NXparameters")
                par.create_field("copymap", "string").write(copymap)

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

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    # print(dct)
                    res = {
                        'techniques': [],
                        "contactEmail": "robust.robust@robust.com",
                        "createdAt": "2020-01-20T00:10:00Z",
                        "pid": "13243546",
                        "ownerGroup": "16171271-dmgt",
                        "accessGroups": [
                            '16171271-dmgt', '16171271-clbt', '16171271-part',
                            'p01dmgt', 'p01staff'],
                        "datasetName": "%s_12345" % fname,
                        "creationLocation": "/DESY/PETRA III/p01",
                        'instrumentId': '/petra3/p01',
                        # "description":
                        # "beautiful-cornflower-wallaby-of-agreement",
                        # "endTime": "2020-01-21T12:37:00Z",
                        "owner": "glossy",
                        "ownerEmail": "feathered.feathered@feathered.com",
                        "principalInvestigator": "robust.robust@robust.com",
                        "proposalId": "16171271",
                        "scientificMetadata": {
                            "beamtimeId": "16171271",
                            "DOOR_proposalId": "65300407",
                            "user_comments": "Awesome comment",
                            "data": {
                                "NX_class": "NXdata"
                            },
                            "end_time": {
                                "value": "2014-02-16T15:17:21+00:00"
                            },
                            "experiment_identifier": {
                                "value": '%s' % arg[2]
                            },
                            "instrument_name": arg[3],
                            "sample_name": arg[7],
                            "name": "entry12345",
                            "start_time": {
                                "value": '%s' % arg[5]
                            },
                            "title": {
                                "value": '%s' % arg[1]
                            }
                        },
                        "sourceFolder":
                        "/asap3/petra3/gpfs/p01/2020/data/12345678",
                        "type": "raw",
                        "isPublished": False,
                        "updatedAt": "2020-01-20T00:10:00Z",
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'description': '%s' % arg[1],
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s_12345" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s_12345" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_metadata_beamtime_copylistfield_yaml(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "scdd01",
          "beamlineAlias": "scdd01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/fs-sc/gpfs/scdd01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "FS-SC",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''
        copymap = '- ["scientificMetadata.instrument"]\n' + \
            '- ["scientificMetadata.nxsfileinfo_parameters"]\n' + \
            '- ["scientificMetadata.sample", null]\n' + \
            '- ["scientificMetadata.instrument_name", ' + \
            ' "scientificMetadata.instrument.name.value"]\n' + \
            '- ["scientificMetadata.sample_name", ' + \
            ' "scientificMetadata.sample.name.value"]'

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

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
                "0o666",
                "0666",
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
                "0o662",
                "0662",
            ],
        ]

        for arg in args:
            filename = arg[0]
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]
            chmod = arg[9]
            chmod2 = arg[10]

            commands = [
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -u -x %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s -b %s  -s %s -o %s -x %s'
                 ' --pid-with-uuid'
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --beamtime-meta %s '
                 ' --scientific-meta %s '
                 ' --output %s '
                 ' --chmod %s '
                 % (filename, self.flags, btfname, smfname,
                    ofname, chmod)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)
                if os.path.isfile(smfname):
                    raise Exception("Test file %s exists" % smfname)
                with open(smfname, "w") as fl:
                    fl.write(smfile)

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("detector", "NXdetector")
                entry.create_group("data", "NXdata")
                par = entry.create_group(
                    "nxsfileinfo_parameters", "NXparameters")
                par.create_field("copymap", "string").write(copymap)

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

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    # print(dct)
                    res = {
                        'techniques': [],
                        "contactEmail": "robust.robust@robust.com",
                        "createdAt": "2020-01-20T00:10:00Z",
                        "pid": "13243546",
                        "ownerGroup": "16171271-dmgt",
                        "accessGroups": [
                            '16171271-dmgt', '16171271-clbt', '16171271-part',
                            'scdd01dmgt', 'scdd01staff'],
                        "datasetName": "%s_12345" % fname,
                        "creationLocation": "/DESY/FS-SC/scdd01",
                        'instrumentId': '/fs-sc/scdd01',
                        # "description":
                        # "beautiful-cornflower-wallaby-of-agreement",
                        # "endTime": "2020-01-21T12:37:00Z",
                        "owner": "glossy",
                        "ownerEmail": "feathered.feathered@feathered.com",
                        "principalInvestigator": "robust.robust@robust.com",
                        "proposalId": "16171271",
                        "scientificMetadata": {
                            "beamtimeId": "16171271",
                            "DOOR_proposalId": "65300407",
                            "user_comments": "Awesome comment",
                            "data": {
                                "NX_class": "NXdata"
                            },
                            "end_time": {
                                "value": "2014-02-16T15:17:21+00:00"
                            },
                            "experiment_identifier": {
                                "value": '%s' % arg[2]
                            },
                            "instrument_name": arg[3],
                            "sample_name": arg[7],
                            "name": "entry12345",
                            "start_time": {
                                "value": '%s' % arg[5]
                            },
                            "title": {
                                "value": '%s' % arg[1]
                            }
                        },
                        "sourceFolder":
                        "/asap3/fs-sc/gpfs/scdd01/2020/data/12345678",
                        "type": "raw",
                        "isPublished": False,
                        "updatedAt": "2020-01-20T00:10:00Z",
                        'creationTime': '2014-02-16T15:17:21+00:00',
                        'endTime': '2014-02-16T15:17:21+00:00',
                        'description': '%s' % arg[1],
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(dct["pid"],
                                         "16171271/%s_12345" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s_12345" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(smfname):
                    os.remove(smfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_beamtime_only(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p01",
          "beamlineAlias": "P01",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p01/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA III",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())

        smfile = '''{
          "user_comments": "Awesome comment",
          "end_time": {"value":"2014-02-16T15:17:21+00:00"}
        }
        '''

        smfname = '%s/scientific-metadata-12345678.json' % (os.getcwd())

        commands = [
            ('nxsfileinfo metadata %s -b %s  -s %s -o %s -u'
             % (self.flags, btfname, smfname, ofname)).split(),
            ('nxsfileinfo metadata %s '
             ' --beamtime-meta %s '
             ' --scientific-meta %s '
             ' --output %s '
             % (self.flags, btfname, smfname, ofname)).split(),
            ('nxsfileinfo metadata %s -b %s  -s %s -o %s'
             ' --pid-with-uuid'
             % (self.flags, btfname, smfname, ofname)).split(),
            ('nxsfileinfo metadata %s '
             ' --beamtime-meta %s '
             ' --scientific-meta %s '
             ' --output %s '
             % (self.flags, btfname, smfname, ofname)).split(),
        ]

        try:
            if os.path.isfile(btfname):
                raise Exception("Test file %s exists" % btfname)
            with open(btfname, "w") as fl:
                fl.write(beamtimefile)
            if os.path.isfile(smfname):
                raise Exception("Test file %s exists" % smfname)
            with open(smfname, "w") as fl:
                fl.write(smfile)

            for kk, cmd in enumerate(commands):
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
                self.assertEqual('', vl.strip())

                with open(ofname) as of:
                    dct = json.load(of)
                # print(dct)
                res = {
                    'techniques': [],
                    "contactEmail": "robust.robust@robust.com",
                    "createdAt": "2020-01-20T00:10:00Z",
                    "creationLocation": "/DESY/PETRA III/P01",
                    'instrumentId': '/petra3/p01',
                    "description":
                    "beautiful-cornflower-wallaby-of-agreement",
                    # "endTime": "2020-01-21T12:37:00Z",
                    "owner": "glossy",
                    "ownerGroup": "16171271-dmgt",
                    "accessGroups": [
                        '16171271-dmgt', '16171271-clbt', '16171271-part',
                        'p01dmgt', 'p01staff'],
                    "ownerEmail": "feathered.feathered@feathered.com",
                    "principalInvestigator": "robust.robust@robust.com",
                    "proposalId": "16171271",
                    "scientificMetadata": {
                        "beamtimeId": "16171271",
                        "DOOR_proposalId": "65300407",
                        "user_comments": "Awesome comment",
                        "end_time": {
                            "value": "2014-02-16T15:17:21+00:00"
                        },
                    },
                    "sourceFolder":
                    "/asap3/petra3/gpfs/p01/2020/data/12345678",
                    "type": "raw",
                    "isPublished": False,
                    "updatedAt": "2020-01-20T00:10:00Z",
                    'creationTime': '2014-02-16T15:17:21+00:00',
                    'endTime': '2014-02-16T15:17:21+00:00',
                }
                self.myAssertDict(dct, res, skip=["pid"])
        finally:
            if os.path.isfile(btfname):
                os.remove(btfname)
            if os.path.isfile(smfname):
                os.remove(smfname)
            if os.path.isfile(ofname):
                os.remove(ofname)

    def test_metadata_beamtime_filename(self):
        """ test nxsconfig execute empty file
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        beamtimefile = '''{
        "applicant": {
          "email": "cute.cute@cute.com",
          "institute": "Deutsches Elektronen-Synchrotron",
          "lastname": "famous",
          "userId": "987654321",
          "username": "piquant"
        },
          "beamline": "p02",
          "beamlineAlias": "p02",
          "beamtimeId": "16171271",
          "contact": "hilarious.hilarious@hilarious.com",
          "corePath": "/asap3/petra3/gpfs/p02/2020/data/12345678",
          "eventEnd": "2020-01-21T12:37:00Z",
          "eventStart": "2020-01-20T01:05:00Z",
          "facility": "PETRA IV",
          "generated": "2020-01-20T00:10:00Z",
          "leader": {
          "email": "feathered.feathered@feathered.com",
          "institute": "debonair",
          "lastname": "glossy",
          "userId": "2879",
          "username": "hairy"
        },
        "onlineAnalysis": {
          "asapoBeamtimeTokenPath": "/shared/asapo_token",
          "reservedNodes": [
              "node1",
              "node2",
              "node2"
          ],
          "slurmReservation": "ponline",
          "slurmPartition": "45473177",
          "sshPrivateKeyPath": "shared/rsa-key.pem",
          "sshPublicKeyPath": "shared/rsa-key.pub",
          "userAccount": "bttest03"
        },
        "pi": {
          "email": "robust.robust@robust.com",
          "institute": "nondescript",
          "lastname": "keen",
          "userId": "3553",
          "username": "military"
        },
        "proposalId": "65300407",
        "proposalType": "C",
        "title": "beautiful-cornflower-wallaby-of-agreement",
        "unixId": "8362",
        "users": {
          "doorDb": [
          "user1",
          "user2",
          "user3"
          ],
          "special": []
        }
        }
        '''
        btfname = '%s/beamtime-metadata-12345678.json' % (os.getcwd())
        ofname = '%s/metadata-12345678.json' % (os.getcwd())

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
            scanname, fext = os.path.splitext(filename)
            fdir, fname = os.path.split(filename)
            fname, fext = os.path.splitext(fname)
            title = arg[1]
            beamtime = arg[2]
            insname = arg[3]
            inssname = arg[4]
            stime = arg[5]
            etime = arg[6]
            smpl = arg[7]
            formula = arg[8]

            commands = [
                ('nxsfileinfo metadata %s %s  -o %s -u --add-empty-units'
                 % (filename, self.flags, ofname)).split(),
                ('nxsfileinfo metadata %s %s  --add-empty-units '
                 ' --output %s '
                 % (filename, self.flags, ofname)).split(),
                ('nxsfileinfo metadata %s %s -o %s  --add-empty-units'
                 ' --pid-with-uuid'
                 % (filename, self.flags, ofname)).split(),
                ('nxsfileinfo metadata %s %s '
                 ' --output %s  --add-empty-units '
                 % (filename, self.flags, ofname)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:
                if os.path.isfile(btfname):
                    raise Exception("Test file %s exists" % btfname)
                with open(btfname, "w") as fl:
                    fl.write(beamtimefile)

                nxsfile = filewriter.create_file(filename, overwrite=True)
                rt = nxsfile.root()
                entry = rt.create_group("entry12345", "NXentry")
                col = rt.create_group("logs", "NXcollection")
                col.create_field("log1", "string").write(title)
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("detector", "NXdetector")
                entry.create_group("data", "NXdata")
                sample = entry.create_group("sample", "NXsample")
                det.create_field("intimage", "uint32", [0, 30], [1, 30])

                entry.create_field("title", "string").write(title)
                pm = entry.create_field("program_name", "string")
                pm.write("NeXDaTaS")
                sn = pm.attributes.create("scan_command", "string")
                sn.write("ascan mot01 0 10 10 0.1")
                ei = entry.create_field(
                    "experiment_identifier", "string")
                ei.write(beamtime)
                eiattr = ei.attributes.create("beamtime_filename", "string")
                eiattr.write(btfname)
                eiattr = ei.attributes.create("beamtime_valid", "bool")
                eiattr.write(True)

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

                for kk, cmd in enumerate(commands):
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
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                    # print(dct)
                    res = {
                        'techniques': [],
                        "contactEmail": "robust.robust@robust.com",
                        "createdAt": "2020-01-20T00:10:00Z",
                        "pid": "13243546",
                        'datasetName': "%s_12345" % scanname,
                        "creationLocation": "/DESY/PETRA IV/p02",
                        'instrumentId': '/petra4/p02',
                        # "description":
                        # "beautiful-cornflower-wallaby-of-agreement",
                        # "endTime": "2020-01-21T12:37:00Z",
                        "owner": "glossy",
                        "ownerGroup": "16171271-dmgt",
                        "accessGroups": [
                            '16171271-dmgt', '16171271-clbt', '16171271-part',
                            'p02dmgt', 'p02staff'],
                        "ownerEmail": "feathered.feathered@feathered.com",
                        "principalInvestigator": "robust.robust@robust.com",
                        "proposalId": "16171271",
                        "scientificMetadata": {
                            "beamtimeId": "16171271",
                            "DOOR_proposalId": "65300407",
                            "ScanCommand": "ascan mot01 0 10 10 0.1",
                            "program_name": {
                                "value": "NeXDaTaS",
                                "unit": "",
                                "scan_command": "ascan mot01 0 10 10 0.1",
                            },
                            "data": {
                                "NX_class": "NXdata"
                            },
                            "end_time": {
                                "value": '%s' % etime,
                                "unit": ""
                            },
                            "experiment_identifier": {
                                "beamtime_filename": '%s' % btfname,
                                "unit": "",
                                "beamtime_valid": True,
                                "value": '%s' % arg[2]
                            },
                            "instrument": {
                                "NX_class": "NXinstrument",
                                "detector": {
                                    "NX_class": "NXdetector",
                                    "intimage": {
                                        "shape": [
                                            0,
                                            30
                                        ]
                                    }
                                },
                                "name": {
                                    "short_name": '%s' % arg[4],
                                    "unit": "",
                                    "value": '%s' % arg[3]
                                }
                            },
                            "name": "entry12345",
                            "sample": {
                                "NX_class": "NXsample",
                                "chemical_formula": {
                                    "unit": "",
                                    "value": '%s' % arg[8]
                                },
                                "name": {
                                    "unit": "",
                                    "value": '%s' % arg[7]
                                }
                            },
                            "start_time": {
                                "unit": "",
                                "value": '%s' % arg[5]
                            },
                            "title": {
                                "unit": "",
                                "value": '%s' % arg[1]
                            }
                        },
                        "sourceFolder":
                        "/asap3/petra3/gpfs/p02/2020/data/12345678",
                        "type": "raw",
                        "isPublished": False,
                        "updatedAt": "2020-01-20T00:10:00Z",
                        'creationTime': '%s' % etime,
                        'endTime': '%s' % etime,
                        'description': '%s' % arg[1],
                    }
                    self.myAssertDict(dct, res, skip=["pid"])
                    if kk % 2:
                        self.assertEqual(
                            dct["pid"], "16171271/%s_12345" % fname)
                    else:
                        self.assertTrue(
                            dct["pid"].startswith(
                                "16171271/%s_12345" % fname))
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(btfname):
                    os.remove(btfname)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_origdatablock_nofiles(self):
        """ test nxsfileinfo origdatablock
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        scanname = 'mytestfileinfo'

        commands = [
            ('nxsfileinfo origdatablock %s' % (scanname)).split(),
        ]

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
            dct = json.loads(vl)
            res = {
                "size": 0,
                "dataFileList": []
            }
            self.myAssertDict(dct, res)

    def test_origdatablock_emptyfile(self):
        """ test nxsfileinfo origdatablock
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        scanname = 'testfile_123456'
        filename = "%s.nxs" % scanname
        ofname = '%s/origdatablock-12345678.json' % (os.getcwd())
        chmod = "0o666"
        chmod2 = "0666"

        commands = [
            ('nxsfileinfo origdatablock %s -o %s -x %s '
             % (scanname, ofname, chmod)).split(),
            ('nxsfileinfo origdatablock %s --output %s --chmod %s '
             % (scanname, ofname, chmod)).split(),
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
                self.assertEqual('', vl.strip())
                with open(ofname) as of:
                    dct = json.load(of)
                status = os.stat(ofname)
                try:
                    self.assertEqual(chmod, str(oct(status.st_mode & 0o777)))
                except Exception:
                    self.assertEqual(
                        chmod2, str(oct(status.st_mode & 0o777)))
                # dct = json.loads(vl)
                self.assertTrue(dct["size"] > 4000)
                dfl = dct["dataFileList"]
                self.assertEqual(len(dfl), 1)
                df = dfl[0]

                self.assertEqual(df["size"], dct["size"])
                self.assertEqual(df["path"], filename)
                self.assertEqual(df["uid"], getpass.getuser())
                self.assertTrue(df["perm"] in ['-rw-r--r--', '-rw-rw-r--'])

                gid = pwd.getpwnam(getpass.getuser()).pw_gid
                self.assertEqual(df["gid"], grp.getgrgid(gid).gr_name)

                tm = df["time"]
                if sys.version_info > (3,):
                    tst = duparser.parse(tm).timestamp()
                    ct = time.time()
                    self.assertTrue(tst <= ct)
                    self.assertTrue(ct - tst < 1)

        finally:
            if os.path.isfile(filename):
                os.remove(filename)
            if os.path.isfile(ofname):
                os.remove(ofname)

    def test_origdatablock_nxsextras(self):
        """ test nxsfileinfo origdatablock
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        locpath, _ = os.path.split(__file__)
        scanname = os.path.join(os.path.relpath(locpath), 'nxsextras')

        commands = [
            ('nxsfileinfo origdatablock %s'
             " -s *.pyc,*~,*.py" % (scanname)).split(),
            ('nxsfileinfo origdatablock %s'
             " --skip *.pyc,*~,*.py" % (scanname)).split(),
        ]

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
            dct = json.loads(vl)
            self.assertEqual(dct["size"], 966)
            dfl = dct["dataFileList"]
            self.assertEqual(len(dfl), 3)
            df = None
            for df in dfl:
                if df["path"] == 'nxsextrasp00/common4_common.ds.xml':
                    break

            self.assertEqual(
                df["path"], 'nxsextrasp00/common4_common.ds.xml')
            self.assertEqual(df["size"], 258)

            self.assertTrue(isinstance(df["uid"], unicode))
            self.assertTrue(isinstance(df["gid"], unicode))
            self.assertTrue(isinstance(df["time"], unicode))
            self.assertTrue(isinstance(df["perm"], unicode))

            for df in dfl:
                if df["path"] == 'nxsextrasp00/collect4.xml':
                    break

            #    df = dfl[1]
            self.assertEqual(
                df["path"], 'nxsextrasp00/collect4.xml')
            self.assertEqual(df["size"], 143)

            self.assertTrue(isinstance(df["uid"], unicode))
            self.assertTrue(isinstance(df["gid"], unicode))
            self.assertTrue(isinstance(df["time"], unicode))
            self.assertTrue(isinstance(df["perm"], unicode))

            for df in dfl:
                if df["path"] == 'nxsextrasp00/mymca.xml':
                    break

            # df = dfl[2]
            self.assertEqual(
                df["path"], 'nxsextrasp00/mymca.xml')
            self.assertEqual(df["size"], 565)

            self.assertTrue(isinstance(df["uid"], unicode))
            self.assertTrue(isinstance(df["gid"], unicode))
            self.assertTrue(isinstance(df["time"], unicode))
            self.assertTrue(isinstance(df["perm"], unicode))

    def test_origdatablock_nxsextras_add(self):
        """ test nxsfileinfo origdatablock
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        locpath, _ = os.path.split(__file__)
        filename = 'testfile_123456.nxs'
        scanname = os.path.join(os.path.relpath(locpath), 'nxsextras')

        commands = [
            ('nxsfileinfo origdatablock %s -a %s'
             " -s *.pyc,*~,*.py" % (scanname, filename)).split(),
            ('nxsfileinfo origdatablock %s --add %s'
             " --skip *.pyc,*~,*.py" % (scanname, filename)).split(),
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
                dct = json.loads(vl)
                self.assertTrue(dct["size"] > 4966)
                dfl = dct["dataFileList"]
                self.assertEqual(len(dfl), 4)

                df = dfl[0]

                self.assertTrue(df["size"] < dct["size"])
                self.assertEqual(df["path"],
                                 os.path.relpath(filename, locpath))
                self.assertEqual(df["uid"], getpass.getuser())
                self.assertTrue(df["perm"] in ['-rw-r--r--', '-rw-rw-r--'])

                gid = pwd.getpwnam(getpass.getuser()).pw_gid
                self.assertEqual(df["gid"], grp.getgrgid(gid).gr_name)

                tm = df["time"]
                if sys.version_info > (3,):
                    tst = duparser.parse(tm).timestamp()
                    ct = time.time()
                    self.assertTrue(tst <= ct)
                    self.assertTrue(ct - tst < 1)

                for df in dfl:
                    if df["path"] == 'nxsextrasp00/common4_common.ds.xml':
                        break
                #    df = dfl[1]
                self.assertEqual(
                    df["path"], 'nxsextrasp00/common4_common.ds.xml')
                self.assertEqual(df["size"], 258)

                self.assertTrue(isinstance(df["uid"], unicode))
                self.assertTrue(isinstance(df["gid"], unicode))
                self.assertTrue(isinstance(df["time"], unicode))
                self.assertTrue(isinstance(df["perm"], unicode))

                for df in dfl:
                    if df["path"] == 'nxsextrasp00/collect4.xml':
                        break
                # df = dfl[2]
                self.assertEqual(
                    df["path"], 'nxsextrasp00/collect4.xml')
                self.assertEqual(df["size"], 143)

                self.assertTrue(isinstance(df["uid"], unicode))
                self.assertTrue(isinstance(df["gid"], unicode))
                self.assertTrue(isinstance(df["time"], unicode))
                self.assertTrue(isinstance(df["perm"], unicode))

                for df in dfl:
                    if df["path"] == 'nxsextrasp00/mymca.xml':
                        break

                # df = dfl[3]
                self.assertEqual(
                    df["path"], 'nxsextrasp00/mymca.xml')
                self.assertEqual(df["size"], 565)

                self.assertTrue(isinstance(df["uid"], unicode))
                self.assertTrue(isinstance(df["gid"], unicode))
                self.assertTrue(isinstance(df["time"], unicode))
                self.assertTrue(isinstance(df["perm"], unicode))

        finally:
            if os.path.isfile(filename):
                os.remove(filename)

    def test_origdatablock_nxsextras_add_more(self):
        """ test nxsfileinfo origdatablock
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        locpath, _ = os.path.split(__file__)
        filename = 'testfile_123456.nxs'
        scanname = os.path.join(os.path.relpath(locpath), 'testfile_123456')
        scanname = 'testfile_123456'
        scanname2 = os.path.join(os.path.relpath(locpath), 'nxsextras')
        relpath = os.path.relpath(locpath, ".")

        commands = [
            ('nxsfileinfo origdatablock %s %s'
             " -s *.pyc,*~,*.py" % (scanname, scanname2)).split(),
            ('nxsfileinfo origdatablock %s %s'
             " --skip *.pyc,*~,*.py" % (scanname, scanname2)).split(),
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
                dct = json.loads(vl)
                self.assertTrue(dct["size"] > 4966)
                dfl = dct["dataFileList"]
                self.assertEqual(len(dfl), 4)

                df = dfl[0]

                self.assertTrue(df["size"] < dct["size"])
                self.assertEqual(df["path"], filename)
                self.assertEqual(df["uid"], getpass.getuser())
                self.assertTrue(df["perm"] in ['-rw-r--r--', '-rw-rw-r--'])

                gid = pwd.getpwnam(getpass.getuser()).pw_gid
                self.assertEqual(df["gid"], grp.getgrgid(gid).gr_name)

                tm = df["time"]
                if sys.version_info > (3,):
                    tst = duparser.parse(tm).timestamp()
                    ct = time.time()
                    self.assertTrue(tst <= ct)
                    self.assertTrue(ct - tst < 1)

                for df in dfl:
                    if df["path"] == os.path.join(
                            relpath, 'nxsextrasp00/common4_common.ds.xml'):
                        break
                #    df = dfl[1]
                self.assertEqual(
                    df["path"], os.path.join(
                            relpath, 'nxsextrasp00/common4_common.ds.xml'))
                self.assertEqual(df["size"], 258)

                self.assertTrue(isinstance(df["uid"], unicode))
                self.assertTrue(isinstance(df["gid"], unicode))
                self.assertTrue(isinstance(df["time"], unicode))
                self.assertTrue(isinstance(df["perm"], unicode))

                for df in dfl:
                    if df["path"] == os.path.join(
                            relpath, 'nxsextrasp00/collect4.xml'):
                        break
                # df = dfl[2]
                self.assertEqual(
                    df["path"], os.path.join(
                            relpath, 'nxsextrasp00/collect4.xml'))
                self.assertEqual(df["size"], 143)

                self.assertTrue(isinstance(df["uid"], unicode))
                self.assertTrue(isinstance(df["gid"], unicode))
                self.assertTrue(isinstance(df["time"], unicode))
                self.assertTrue(isinstance(df["perm"], unicode))

                for df in dfl:
                    if df["path"] == os.path.join(
                            relpath, 'nxsextrasp00/mymca.xml'):
                        break

                # df = dfl[3]
                self.assertEqual(
                    df["path"], os.path.join(
                            relpath, 'nxsextrasp00/mymca.xml'))
                self.assertEqual(df["size"], 565)

                self.assertTrue(isinstance(df["uid"], unicode))
                self.assertTrue(isinstance(df["gid"], unicode))
                self.assertTrue(isinstance(df["time"], unicode))
                self.assertTrue(isinstance(df["perm"], unicode))

        finally:
            if os.path.isfile(filename):
                os.remove(filename)

    def test_origdatablock_nxsextras_add_det(self):
        """ test nxsfileinfo origdatablock
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        locpath, _ = os.path.split(__file__)
        fdir = fun
        print(locpath)
        relpath = os.path.relpath(locpath, fdir)
        purefname = 'testfile_123456.nxs'
        filename = os.path.join(fdir, purefname)
        scanname = os.path.join(fdir, 'testfile_123456')
        scanname2 = os.path.join(locpath, 'nxsextras')

        commands = [
            ('nxsfileinfo origdatablock %s %s'
             " -s *.pyc,*~,*.py" % (scanname, scanname2)).split(),
            ('nxsfileinfo origdatablock %s %s'
             " --skip *.pyc,*~,*.py" % (scanname, scanname2)).split(),
        ]

        wrmodule = WRITERS[self.writer]
        filewriter.writer = wrmodule

        try:
            os.mkdir(fdir)
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
                dct = json.loads(vl)
                self.assertTrue(dct["size"] > 4966)
                dfl = dct["dataFileList"]
                self.assertEqual(len(dfl), 4)

                df = dfl[0]

                self.assertTrue(df["size"] < dct["size"])
                self.assertEqual(df["path"], purefname)
                self.assertEqual(df["uid"], getpass.getuser())
                self.assertTrue(df["perm"] in ['-rw-r--r--', '-rw-rw-r--'])

                gid = pwd.getpwnam(getpass.getuser()).pw_gid
                self.assertEqual(df["gid"], grp.getgrgid(gid).gr_name)

                tm = df["time"]
                if sys.version_info > (3,):
                    tst = duparser.parse(tm).timestamp()
                    ct = time.time()
                    self.assertTrue(tst <= ct)
                    self.assertTrue(ct - tst < 1)

                for df in dfl:
                    if df["path"] == os.path.join(
                            relpath, 'nxsextrasp00/common4_common.ds.xml'):
                        break
                #    df = dfl[1]
                self.assertEqual(
                    df["path"], os.path.join(
                        relpath, 'nxsextrasp00/common4_common.ds.xml'))
                self.assertEqual(df["size"], 258)

                self.assertTrue(isinstance(df["uid"], unicode))
                self.assertTrue(isinstance(df["gid"], unicode))
                self.assertTrue(isinstance(df["time"], unicode))
                self.assertTrue(isinstance(df["perm"], unicode))

                for df in dfl:
                    if df["path"] == os.path.join(
                            relpath, 'nxsextrasp00/collect4.xml'):
                        break
                # df = dfl[2]
                self.assertEqual(
                    df["path"], os.path.join(
                            relpath, 'nxsextrasp00/collect4.xml'))
                self.assertEqual(df["size"], 143)

                self.assertTrue(isinstance(df["uid"], unicode))
                self.assertTrue(isinstance(df["gid"], unicode))
                self.assertTrue(isinstance(df["time"], unicode))
                self.assertTrue(isinstance(df["perm"], unicode))

                for df in dfl:
                    if df["path"] == os.path.join(
                            relpath, 'nxsextrasp00/mymca.xml'):
                        break

                # df = dfl[3]
                self.assertEqual(
                    df["path"], os.path.join(
                            relpath, 'nxsextrasp00/mymca.xml'))
                self.assertEqual(df["size"], 565)

                self.assertTrue(isinstance(df["uid"], unicode))
                self.assertTrue(isinstance(df["gid"], unicode))
                self.assertTrue(isinstance(df["time"], unicode))
                self.assertTrue(isinstance(df["perm"], unicode))

        finally:
            if os.path.isfile(filename):
                os.remove(filename)
            if os.path.isdir(fdir):
                shutil.rmtree(fdir)

    def test_instrument_empty(self):
        """ test nxsfileinfo instrument
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        commands = [
            ('nxsfileinfo instrument').split(),
        ]

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
            dct = json.loads(vl)
            res = {
                "customMetadata": {}
            }
            self.myAssertDict(dct, res)

    def test_instrument_parameters(self):
        """ test nxsfileinfo instrument
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        imfname = '%s/custom-instrument-metadata-p00.json' % (os.getcwd())
        ofname = '%s/instrument-metadata-p00.json' % (os.getcwd())

        params = {
            "pid": "/petra3/p00",
            "name": "P00",
            "bid": "1312312",
            "bl": "p02",
            "ogrp": "1312312-part",
            "agrps": "1312312-part,1312312-clbt,1312312-dmgt",
            "chmod": "0o662",
            "meta": imfname,
            "output": ofname,
        }

        commands = [
            ('nxsfileinfo instrument '
             ' -p {pid} -n {name} '
             ' -i {bid} -b {bl} '
             ' -w {ogrp} -c {agrps} '
             ' -x {chmod} '
             ' -m {meta} '
             ' -o {output} '
             ''.format(**params)).split(),
            ('nxsfileinfo instrument '
             ' --pid {pid} --name {name} '
             ' --beamtimeid {bid} --beamline {bl} '
             ' --owner-group {ogrp} --access-groups {agrps} '
             ' --chmod {chmod} '
             ' --custom-metadata {meta} '
             ' --output {output} '
             ''.format(**params)).split(),
        ]

        try:

            imfile = '''{
                "comments": "Awesome comment",
                "description": {"techniques":["saxs","waxs"]}
            }
            '''

            chmod = "0o662"
            chmod2 = "0662"

            if os.path.isfile(imfname):
                raise Exception("Test file %s exists" % imfname)
            with open(imfname, "w") as fl:
                fl.write(imfile)

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
                self.assertEqual('', vl.strip())

                with open(ofname) as of:
                    dct = json.load(of)
                status = os.stat(ofname)
                try:
                    self.assertEqual(
                        chmod, str(oct(status.st_mode & 0o777)))
                except Exception:
                    self.assertEqual(
                        chmod2, str(oct(status.st_mode & 0o777)))
                res = {
                    'accessGroups': [
                        '1312312-part',
                        '1312312-clbt',
                        '1312312-dmgt'],
                    'customMetadata': {
                        'comments': 'Awesome comment',
                        'description': {
                            'techniques': ['saxs', 'waxs']
                        }
                    },
                    'name': 'P00',
                    'ownerGroup': '1312312-part',
                    'pid': '/petra3/p00'
                }

                self.myAssertDict(dct, res)
        finally:
            if os.path.isfile(imfname):
                os.remove(imfname)
            if os.path.isfile(ofname):
                os.remove(ofname)

    def test_sample_empty(self):
        """ test nxsfileinfo sample
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        commands = [
            ('nxsfileinfo sample').split(),
        ]

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
            dct = json.loads(vl)
            res = {
                "isPublished": False,
                "sampleCharacteristics": {}
            }
            self.myAssertDict(dct, res)

    def test_sample_parameters(self):
        """ test nxsfileinfo sample
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        imfname = '%s/custom-sample-metadata-p00.json' % (os.getcwd())
        ofname = '%s/sample-metadata-p00.json' % (os.getcwd())

        params = {
            "sid": "/petra3/sample/234234",
            "bid": "1312312",
            "bl": "p02",
            "des": "HH_Water_1",
            "ogrp": "1312312-part",
            "agrps": "1312312-part,1312312-clbt,1312312-dmgt",
            "chmod": "0o662",
            "meta": imfname,
            "output": ofname,
        }

        commands = [
            ('nxsfileinfo sample '
             ' --sample-id {sid} --description {des} --published '
             ' --beamtimeid {bid} --beamline {bl} '
             ' --owner-group {ogrp} --access-groups {agrps} '
             ' --chmod {chmod} '
             ' --sample-characteristics {meta} '
             ' --output {output} '
             ''.format(**params)).split(),
            ('nxsfileinfo sample '
             ' -s {sid} -d {des} -p '
             ' -i {bid} -b {bl} '
             ' -w {ogrp} -c {agrps} '
             ' -x {chmod} '
             ' -m {meta} '
             ' -o {output} '
             ''.format(**params)).split(),
        ]

        try:

            imfile = '''{
                "comments": "Awesome comment",
                "formula": "H2O"
            }
            '''

            chmod = "0o662"
            chmod2 = "0662"

            if os.path.isfile(imfname):
                raise Exception("Test file %s exists" % imfname)
            with open(imfname, "w") as fl:
                fl.write(imfile)

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
                self.assertEqual('', vl.strip())

                with open(ofname) as of:
                    dct = json.load(of)
                status = os.stat(ofname)
                try:
                    self.assertEqual(
                        chmod, str(oct(status.st_mode & 0o777)))
                except Exception:
                    self.assertEqual(
                        chmod2, str(oct(status.st_mode & 0o777)))
                res = {
                    'accessGroups': [
                        '1312312-part',
                        '1312312-clbt',
                        '1312312-dmgt'],
                    'description': 'HH_Water_1',
                    'isPublished': True,
                    'ownerGroup': '1312312-part',
                    'sampleCharacteristics': {
                        'comments': 'Awesome comment',
                        'formula': 'H2O'},
                    'sampleId': '/petra3/sample/234234'}

                self.myAssertDict(dct, res)
        finally:
            if os.path.isfile(imfname):
                os.remove(imfname)
            if os.path.isfile(ofname):
                os.remove(ofname)

    def test_attachment_empty(self):
        """ test nxsfileinfo attachment
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        commands = [
            ('nxsfileinfo attachment').split(),
        ]

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
            dct = json.loads(vl)
            res = {}
            self.myAssertDict(dct, res)

    def test_attachment_png(self):
        """ test nxsfileinfo attachment
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                "tn.png",
                "123/423/543",
                "My_tests",
                "12312312",
                "p00",
            ],
            [
                "tn.png",
                "petra3/1223/543",
                "Water_tests",
                "54352312",
                "p99",
            ],
        ]

        for arg in args:
            filename = arg[0]
            atid = arg[1]
            caption = arg[2]
            bid = arg[3]
            bl = arg[4]

            shutil.copy("test/files/%s" % filename, filename)
            commands = [
                ('nxsfileinfo attachment %s '
                 ' -a %s '
                 ' -t %s '
                 ' -i %s '
                 ' -b %s '
                 % (filename, atid, caption, bid, bl)).split(),
                ('nxsfileinfo attachment %s '
                 ' --id %s '
                 ' --caption %s '
                 ' --beamtimeid %s '
                 ' --beamline %s '
                 % (filename, atid, caption, bid, bl)).split(),
            ]
            for cmd in commands:
                # print(cmd)
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
                dct = json.loads(vl)
                res = {
                    'id': atid,
                    'caption': caption,
                    'thumbnail':
                    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCA"
                    "IAAAACUFjqAAAACXBIWXMAAC4jAAAuIwF4pT92AAAAB3RJTUUH5wEbCA"
                    "AYYJKxWgAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDh"
                    "cAAAEQSURBVBjTBcFNTgIxFADg9vVNO1MGCPiDxugK4wIXmpi40GN4Pg"
                    "/gQbyAKxcaIxojKCoFZtq+vvp98uZ4cjDQ1+ejnX5n+uzvH+cXl/XV2f"
                    "j27iHIBLvdemjt/tbAlqA0Y1qP93qHA4PtT78gjKuV1KYSWYpY1WitBi"
                    "EpppiETAAhZ86CvNdKaY2F7bsATS4Je9NFA2SqNeWmjUZXwYfYbLRk9u"
                    "3aLREQCJJL8LdJbrm0XVtv17oDqCnB5vTkCBAYjUlZSQDPHImYBQvgon"
                    "x5n4EWXIA0pTFlhyKj0qiMc7EJ+DSdw6iuikyc+eNzPpv9fi/c69uXW+"
                    "U2Qm84BKtAZW6D90SqqDyDz+CTQFSllv+/oo3kf3+TDAAAAABJRU5Erk"
                    "Jggg==",
                    "ownerGroup": "%s-dmgt" % bid,
                    "accessGroups": [
                        '%s-clbt' % bid,
                        '%s-part' % bid,
                        '%s-dmgt' % bid,
                        '%sdmgt' % bl, '%sstaff' % bl],
                }
                self.myAssertDict(dct, res)

    def test_attachment_fio(self):
        """ test nxsfileinfo attachment
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        ofname = '%s/attachment-metadata-12345678.json' % (os.getcwd())

        args = [
            [
                "mymeta2_00011.fio",
                "123/423/543",
                "My_tests",
                "12312312",
                "p00",
                "0o666",
                "0666",
                "exp_c03",
                "exp_mot04",
                "exp_c03.(counts)",
                "lat.(mm)",
            ],
            [
                "mymeta2_00011.fio",
                "petra3/1223/543",
                "Water_tests",
                "54352312",
                "p99",
                "0o662",
                "0662",
                "exp_c99,exp_c02",
                "timestamp",
                "exp_p02.(counts)",
                "time.(s)",
            ],
        ]

        for arg in args:
            filename = arg[0]
            atid = arg[1]
            caption = arg[2]
            bid = arg[3]
            bl = arg[4]
            chmod = arg[5]
            chmod2 = arg[6]
            signals = arg[7]
            axes = arg[8]
            slabel = arg[9]
            xlabel = arg[10]

            shutil.copy("test/files/%s" % filename, filename)
            commands = [
                ('nxsfileinfo attachment %s '
                 ' -a %s '
                 ' -t %s '
                 ' -i %s '
                 ' -b %s '
                 ' -o %s '
                 ' -x %s '
                 ' -s %s '
                 ' -e %s '
                 % (filename, atid, caption, bid, bl,
                    ofname, chmod, signals, axes)).split(),
                ('nxsfileinfo attachment %s '
                 ' --id %s '
                 ' --caption %s '
                 ' --beamtimeid %s '
                 ' --beamline %s '
                 ' --output %s '
                 ' --chmod %s '
                 ' --signals %s '
                 ' --axes %s '
                 ' --signal-label %s '
                 ' --xlabel %s '
                 % (filename, atid, caption, bid, bl,
                    ofname, chmod, signals, axes, slabel, xlabel)).split(),
            ]
            try:
                for cmd in commands:
                    # print(cmd)
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
                    self.assertEqual('', er)
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                        status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    res = {
                        'id': atid,
                        'caption': caption,
                        'thumbnail': "",
                        "ownerGroup": "%s-dmgt" % bid,
                        "accessGroups": [
                            '%s-clbt' % bid,
                            '%s-part' % bid,
                            '%s-dmgt' % bid,
                            '%sdmgt' % bl, '%sstaff' % bl],
                    }
                    self.myAssertDict(dct, res, ["thumbnail"])

                    tn = dct["thumbnail"]
                    self.assertTrue(tn.startswith("data:image/png;base64,"))
                    ctn = tn[len("data:image/png;base64,"):]

                    ipng = base64.b64decode(ctn.encode("utf-8"))

                    img = PIL.Image.open(BytesIO(ipng))
                    shape = np.array(img).shape
                    self.assertEqual(len(shape), 3)
                    self.assertTrue(shape[0] > 100)
                    self.assertTrue(shape[1] > 100)

            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_attachment_nxs_empty(self):
        """ test nxsfileinfo attachment
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        ofname = '%s/attachment-metadata-12345678.json' % (os.getcwd())

        args = [
            [
                'testfileinfo.nxs',
                "123/423/543",
                "My_tests",
                "12312312",
                "p00",
                "0o666",
                "0666",
                "exp_c03",
                "exp_mot04",
                "exp_c03.(counts)",
                "lat.(mm)",
            ],
            [
                'testfileinfo.nxs',
                "petra3/1223/543",
                "Water_tests",
                "54352312",
                "p99",
                "0o662",
                "0662",
                "exp_c99,exp_c02",
                "timestamp",
                "exp_p02.(counts)",
                "time.(s)",
            ],
        ]

        for arg in args:
            filename = arg[0]
            atid = arg[1]
            caption = arg[2]
            bid = arg[3]
            bl = arg[4]
            chmod = arg[5]
            chmod2 = arg[6]
            signals = arg[7]
            axes = arg[8]
            slabel = arg[9]
            xlabel = arg[10]

            commands = [
                ('nxsfileinfo attachment %s '
                 ' -a %s '
                 ' -t %s '
                 ' -i %s '
                 ' -b %s '
                 ' -o %s '
                 ' -x %s '
                 ' -s %s '
                 ' -e %s '
                 % (filename, atid, caption, bid, bl,
                    ofname, chmod, signals, axes)).split(),
                ('nxsfileinfo attachment %s '
                 ' --id %s '
                 ' --caption %s '
                 ' --beamtimeid %s '
                 ' --beamline %s '
                 ' --output %s '
                 ' --chmod %s '
                 ' --signals %s '
                 ' --axes %s '
                 ' --signal-label %s '
                 ' --xlabel %s '
                 % (filename, atid, caption, bid, bl,
                    ofname, chmod, signals, axes, slabel, xlabel)).split(),
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule

            try:

                nxsfile = filewriter.create_file(filename, overwrite=True)
                nxsfile.close()

                for cmd in commands:
                    # print(cmd)
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
                    self.assertEqual('', er)
                    self.assertEqual('', vl.strip())

                    with open(ofname) as of:
                        dct = json.load(of)
                        status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    res = {
                        'id': atid,
                        'caption': caption,
                        "ownerGroup": "%s-dmgt" % bid,
                        "accessGroups": [
                            '%s-clbt' % bid,
                            '%s-part' % bid,
                            '%s-dmgt' % bid,
                            '%sdmgt' % bl, '%sstaff' % bl],
                    }
                    self.myAssertDict(dct, res)

            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_attachment_nxs_counter(self):
        """ test nxsfileinfo attachment
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        ofname = '%s/attachment-metadata-12345678.json' % (os.getcwd())

        args = [
            [
                'testfileinfo.nxs',
                "123/423/543",
                "My_tests",
                "12312312",
                "p00",
                "0o666",
                "0666",
                "exp_c03",
                "exp_mot04",
                "exp_c03.(counts)",
                "lat.(mm)",
            ],
            [
                'testfileinfo.nxs',
                "petra3/1223/543",
                "Water_tests",
                "54352312",
                "p99",
                # "0o666",
                # "0666",
                "0o662",
                "0662",
                "exp_c99,exp_c02",
                "timestamp",
                "exp_p02.(counts)",
                "time.(s)",
            ],
        ]

        for arg in args:
            filename = arg[0]
            atid = arg[1]
            caption = arg[2]
            bid = arg[3]
            bl = arg[4]
            chmod = arg[5]
            chmod2 = arg[6]
            signals = arg[7]
            axes = arg[8]
            slabel = arg[9]
            xlabel = arg[10]

            commands = [
                ('nxsfileinfo attachment %s '
                 ' -a %s '
                 ' -t %s '
                 ' -i %s '
                 ' -b %s '
                 ' -o %s '
                 ' -x %s '
                 ' -s %s '
                 ' -e %s '
                 # ' --overwrite '
                 % (filename, atid, caption, bid, bl,
                    ofname, chmod, signals, axes)).split(),
                ('nxsfileinfo attachment %s '
                 ' --id %s '
                 ' --caption %s '
                 ' --beamtimeid %s '
                 ' --beamline %s '
                 ' --output %s '
                 ' --chmod %s '
                 ' --signals %s '
                 ' --axes %s '
                 ' --signal-label %s '
                 ' --xlabel %s '
                 # ' --overwrite '
                 % (filename, atid, caption, bid, bl,
                    ofname, chmod, signals, axes, slabel, xlabel)).split(),
            ]

            c2d = [1, 432, 3456, 654, 6546, 56, 56, 77, 24, 2]
            c3d = [2, 32, 356, 654, 646, 156, 56, 7, 4, 2]
            m4d = [2., 2.2, 2.3, 2.5, 2.6, 2.8, 3.0, 3.4, 4.1, 5.2]
            tsd = [0., 0.2, 0.3, 0.5, 0.6, 0.8, 1.0, 1.4, 2.1, 3.2]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule
            nxsfile = filewriter.create_file(filename, overwrite=True)
            rt = nxsfile.root()
            entry = rt.create_group("entry1234", "NXentry")
            entry.create_group("instrument", "NXinstrument")
            da = entry.create_group("data", "NXdata")
            c2 = da.create_field("exp_c02", "uint32", [10], [10])
            c2.write(c2d)
            c3 = da.create_field("exp_c03", "uint32", [10], [10])
            c3.write(c3d)
            m4 = da.create_field("exp_mot04", "float32", [10], [10])
            m4.write(m4d)
            ts = da.create_field("timestamp", "float64", [10], [10])
            ts.write(tsd)
            nxsfile.close()

            try:
                for cmd in commands:
                    # print(cmd)
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
                    self.assertEqual('', er)
                    self.assertEqual('', vl.strip())
                    # print(vl)

                    with open(ofname) as of:
                        dct = json.load(of)
                        status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    res = {
                        'id': atid,
                        'caption': caption,
                        'thumbnail': "",
                        "ownerGroup": "%s-dmgt" % bid,
                        "accessGroups": [
                            '%s-clbt' % bid,
                            '%s-part' % bid,
                            '%s-dmgt' % bid,
                            '%sdmgt' % bl, '%sstaff' % bl],
                    }
                    self.myAssertDict(dct, res, ["thumbnail"])

                    tn = dct["thumbnail"]
                    self.assertTrue(tn.startswith("data:image/png;base64,"))
                    ctn = tn[len("data:image/png;base64,"):]

                    ipng = base64.b64decode(ctn.encode("utf-8"))

                    img = PIL.Image.open(BytesIO(ipng))
                    shape = np.array(img).shape
                    self.assertEqual(len(shape), 3)
                    self.assertTrue(shape[0] > 100)
                    self.assertTrue(shape[1] > 100)
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_attachment_nxs_mca(self):
        """ test nxsfileinfo attachment
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        ofname = '%s/attachment-metadata-12345678.json' % (os.getcwd())

        args = [
            [
                'testfileinfo.nxs',
                "123/423/543",
                "My_tests",
                "12312312",
                "p00",
                "0o666",
                "0666",
                "exp_mca01",
                "exp_mot04",
                "MCA01",
                "lat.(mm)",
            ],
            [
                'testfileinfo.nxs',
                "petra3/1223/543",
                "Water_tests",
                "54352312",
                "p99",
                "0o666",
                "0666",
                # "0o662",
                # "0662",
                "exp_c99,exp_mca01",
                "timestamp",
                "MCA01",
                "time.(s)",
            ],
        ]

        for arg in args:
            filename = arg[0]
            atid = arg[1]
            caption = arg[2]
            bid = arg[3]
            bl = arg[4]
            chmod = arg[5]
            chmod2 = arg[6]
            signals = arg[7]
            axes = arg[8]
            slabel = arg[9]
            xlabel = arg[10]

            commands = [
                ('nxsfileinfo attachment %s '
                 ' -a %s '
                 ' -t %s '
                 ' -i %s '
                 ' -b %s '
                 ' -o %s '
                 ' -x %s '
                 ' -s %s '
                 ' -e %s '
                 # ' --overwrite '
                 % (filename, atid, caption, bid, bl,
                    ofname, chmod, signals, axes)).split(),
                ('nxsfileinfo attachment %s '
                 ' --id %s '
                 ' --caption %s '
                 ' --beamtimeid %s '
                 ' --beamline %s '
                 ' --output %s '
                 ' --chmod %s '
                 ' --signals %s '
                 ' --axes %s '
                 ' --signal-label %s '
                 ' --xlabel %s '
                 # ' --overwrite '
                 % (filename, atid, caption, bid, bl,
                    ofname, chmod, signals, axes, slabel, xlabel)).split(),
            ]

            c3d = [2, 32, 356, 654, 646, 156, 56, 7, 4, 2]
            m4d = [2., 2.2, 2.3, 2.5, 2.6, 2.8, 3.0, 3.4, 4.1, 5.2]
            tsd = [0., 0.2, 0.3, 0.5, 0.6, 0.8, 1.0, 1.4, 2.1, 3.2]

            c2d = [
                np.random.normal(0, 0.1, 1024),
                np.random.normal(0.01, 0.11, 1024),
                np.random.normal(0.02, 0.12, 1024),
                np.random.normal(0.03, 0.13, 1024),
                np.random.normal(0.04, 0.14, 1024),
                np.random.normal(0.05, 0.15, 1024)
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule
            nxsfile = filewriter.create_file(filename, overwrite=True)
            rt = nxsfile.root()
            entry = rt.create_group("entry1234", "NXentry")
            entry.create_group("instrument", "NXinstrument")
            da = entry.create_group("data", "NXdata")
            c2 = da.create_field("exp_mca01", "float64", [6, 1024], [1, 1024])
            for di, d2 in enumerate(c2d):
                c2[di, :] = d2
            c3 = da.create_field("exp_c03", "uint32", [10], [10])
            c3.write(c3d)
            m4 = da.create_field("exp_mot04", "float32", [10], [10])
            m4.write(m4d)
            ts = da.create_field("timestamp", "float64", [10], [10])
            ts.write(tsd)
            nxsfile.close()

            try:
                for cmd in commands:
                    # print(cmd)
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
                    self.assertEqual('', er)
                    self.assertEqual('', vl.strip())
                    # print(vl)

                    with open(ofname) as of:
                        dct = json.load(of)
                        status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    res = {
                        'id': atid,
                        'caption': caption,
                        'thumbnail': "",
                        "ownerGroup": "%s-dmgt" % bid,
                        "accessGroups": [
                            '%s-clbt' % bid,
                            '%s-part' % bid,
                            '%s-dmgt' % bid,
                            '%sdmgt' % bl, '%sstaff' % bl],
                    }
                    self.myAssertDict(dct, res, ["thumbnail"])

                    tn = dct["thumbnail"]
                    self.assertTrue(tn.startswith("data:image/png;base64,"))
                    ctn = tn[len("data:image/png;base64,"):]

                    ipng = base64.b64decode(ctn.encode("utf-8"))

                    img = PIL.Image.open(BytesIO(ipng))
                    shape = np.array(img).shape
                    self.assertEqual(len(shape), 3)
                    self.assertTrue(shape[0] > 100)
                    self.assertTrue(shape[1] > 100)
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(ofname):
                    os.remove(ofname)

    def test_attachment_nxs_images(self):
        """ test nxsfileinfo attachment
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        ofname = '%s/attachment-metadata-12345678.json' % (os.getcwd())

        args = [
            [
                'testfileinfo.nxs',
                "123/423/543",
                "My_tests",
                "12312312",
                "p00",
                "0o666",
                "0666",
                "exp_mca01",
                "lambda",
                "MCA01",
                3,
            ],
            [
                'testfileinfo.nxs',
                "petra3/1223/543",
                "Water_tests",
                "54352312",
                "p99",
                "0o666",
                "0666",
                # "0o662",
                # "0662",
                "exp_c99,lambda",
                "timestamp",
                "MCA01",
                2,
            ],
        ]

        for arg in args:
            filename = arg[0]
            atid = arg[1]
            caption = arg[2]
            bid = arg[3]
            bl = arg[4]
            chmod = arg[5]
            chmod2 = arg[6]
            signals = arg[7]
            axes = arg[8]
            slabel = arg[9]
            frame = arg[10]

            commands = [
                ('nxsfileinfo attachment %s '
                 ' -a %s '
                 ' -t %s '
                 ' -i %s '
                 ' -b %s '
                 ' -o %s '
                 ' -x %s '
                 ' -s %s '
                 ' -e %s '
                 ' -m %s '
                 # ' --overwrite '
                 % (filename, atid, caption, bid, bl,
                    ofname, chmod, signals, axes, frame)).split(),
                ('nxsfileinfo attachment %s '
                 ' --id %s '
                 ' --caption %s '
                 ' --beamtimeid %s '
                 ' --beamline %s '
                 ' --output %s '
                 ' --chmod %s '
                 ' --signals %s '
                 ' --axes %s '
                 ' --frame %s '
                 ' --signal-label %s '

                 # ' --overwrite '
                 % (filename, atid, caption, bid, bl,
                    ofname, chmod, signals, axes, frame, slabel)).split(),
            ]

            c3d = [2, 32, 356, 654, 646, 156, 56, 7, 4, 2]
            m4d = [2., 2.2, 2.3, 2.5, 2.6, 2.8, 3.0, 3.4, 4.1, 5.2]
            tsd = [0., 0.2, 0.3, 0.5, 0.6, 0.8, 1.0, 1.4, 2.1, 3.2]

            c2d = [
                np.random.normal(0, 0.1, 1024).reshape(16, 64),
                np.random.normal(0.01, 0.11, 1024).reshape(16, 64),
                np.random.normal(0.02, 0.12, 1024).reshape(16, 64),
                np.random.normal(0.03, 0.13, 1024).reshape(16, 64),
                np.random.normal(0.04, 0.14, 1024).reshape(16, 64),
                np.random.normal(0.05, 0.15, 1024).reshape(16, 64)
            ]

            wrmodule = WRITERS[self.writer]
            filewriter.writer = wrmodule
            nxsfile = filewriter.create_file(filename, overwrite=True)
            rt = nxsfile.root()
            entry = rt.create_group("entry1234", "NXentry")
            entry.create_group("instrument", "NXinstrument")
            da = entry.create_group("data", "NXdata")
            c2 = da.create_field("lambda", "float64", [6, 16, 64], [1, 16, 64])
            for di, d2 in enumerate(c2d):
                c2[di, :, :] = d2
            c3 = da.create_field("exp_c03", "uint32", [10], [10])
            c3.write(c3d)
            m4 = da.create_field("exp_mot04", "float32", [10], [10])
            m4.write(m4d)
            ts = da.create_field("timestamp", "float64", [10], [10])
            ts.write(tsd)
            nxsfile.close()

            try:
                for cmd in commands:
                    # print(cmd)
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
                    self.assertEqual('', er)
                    self.assertEqual('', vl.strip())
                    # print(vl)

                    with open(ofname) as of:
                        dct = json.load(of)
                        status = os.stat(ofname)
                    try:
                        self.assertEqual(
                            chmod, str(oct(status.st_mode & 0o777)))
                    except Exception:
                        self.assertEqual(
                            chmod2, str(oct(status.st_mode & 0o777)))
                    res = {
                        'id': atid,
                        'caption': caption,
                        'thumbnail': "",
                        "ownerGroup": "%s-dmgt" % bid,
                        "accessGroups": [
                            '%s-clbt' % bid,
                            '%s-part' % bid,
                            '%s-dmgt' % bid,
                            '%sdmgt' % bl, '%sstaff' % bl],
                    }
                    self.myAssertDict(dct, res, ["thumbnail"])

                    tn = dct["thumbnail"]
                    self.assertTrue(tn.startswith("data:image/png;base64,"))
                    ctn = tn[len("data:image/png;base64,"):]

                    ipng = base64.b64decode(ctn.encode("utf-8"))

                    img = PIL.Image.open(BytesIO(ipng))
                    shape = np.array(img).shape
                    self.assertEqual(len(shape), 3)
                    self.assertTrue(shape[0] > 100)
                    self.assertTrue(shape[1] > 100)
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                if os.path.isfile(ofname):
                    os.remove(ofname)


if __name__ == '__main__':
    unittest.main()
