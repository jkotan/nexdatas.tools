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

""" Command-line tool for showing meta data from Nexus Files"""

import sys
import argparse
import json
import uuid
import os
import re

from .nxsparser import TableTools
from .nxsfileparser import (NXSFileParser, numpyEncoder)
from .nxsargparser import (Runner, NXSArgParser, ErrorException)
from . import filewriter


WRITERS = {}
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


class General(Runner):

    """ General runner"""

    #: (:obj:`str`) command description
    description = "show general information for the nexus file"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxsfileinfo general /user/data/myfile.nxs\n" \
        + "\n"

    def create(self):
        """ creates parser

        """
        self._parser.add_argument(
            "--h5py", action="store_true",
            default=False, dest="h5py",
            help="use h5py module as a nexus reader")
        self._parser.add_argument(
            "--h5cpp", action="store_true",
            default=False, dest="h5cpp",
            help="use h5cpp module as a nexus reader")

    def postauto(self):
        """ parser creator after autocomplete run """
        self._parser.add_argument(
            'args', metavar='nexus_file', type=str, nargs=1,
            help='new nexus file name')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :returns: output information
        :rtype: :obj:`str`
        """
        if options.h5cpp:
            writer = "h5cpp"
        elif options.h5py:
            writer = "h5py"
        elif "h5cpp" in WRITERS.keys():
            writer = "h5cpp"
        else:
            writer = "h5py"
        if (options.h5py and options.h5cpp) or \
           writer not in WRITERS.keys():
            sys.stderr.write("nxsfileinfo: Writer '%s' cannot be opened\n"
                             % writer)
            sys.stderr.flush()
            self._parser.print_help()
            sys.exit(255)
        wrmodule = WRITERS[writer.lower()]
        try:
            fl = filewriter.open_file(
                options.args[0], readonly=True,
                writer=wrmodule)
        except Exception:
            sys.stderr.write("nxsfileinfo: File '%s' cannot be opened\n"
                             % options.args[0])
            sys.stderr.flush()
            self._parser.print_help()
            sys.exit(255)

        root = fl.root()
        self.show(root)
        fl.close()

    @classmethod
    def parseentry(cls, entry, description):
        """ parse entry of nexus file

        :param entry: nexus entry node
        :type entry: :class:`filewriter.FTGroup`
        :param description: dict description list
        :type description: :obj:`list` <:obj:`dict` <:obj:`str`, `any` > >
        :return: (key, value) name pair of table headers
        :rtype: [:obj:`str`, :obj:`str`]

        """
        key = "A"
        value = "B"
        at = None
        try:
            at = entry.attributes["NX_class"]
        except Exception:
            pass
        if at and filewriter.first(at.read()) == 'NXentry':
            # description.append(None)
            # value = filewriter.first(value)
            key = "Scan entry:"
            value = entry.name
            # description.append({key: "Scan entry:", value: entry.name})
            # description.append(None)
            try:
                vl = filewriter.first(entry.open("title").read())
                description.append(
                    {key: "Title:", value: vl})
            except Exception:
                sys.stderr.write("nxsfileinfo: title cannot be found\n")
                sys.stderr.flush()
            try:
                vl = filewriter.first(
                    entry.open("experiment_identifier").read())
                description.append(
                    {key: "Experiment identifier:",
                     value: vl})
            except Exception:
                sys.stderr.write(
                    "nxsfileinfo: experiment identifier cannot be found\n")
                sys.stderr.flush()
            for ins in entry:
                if isinstance(ins, filewriter.FTGroup):
                    iat = ins.attributes["NX_class"]
                    if iat and filewriter.first(iat.read()) == 'NXinstrument':
                        try:
                            vl = filewriter.first(ins.open("name").read())
                            description.append({
                                key: "Instrument name:",
                                value: vl})
                        except Exception:
                            sys.stderr.write(
                                "nxsfileinfo: instrument name cannot "
                                "be found\n")
                            sys.stderr.flush()
                        try:
                            vl = filewriter.first(
                                ins.open("name").attributes[
                                    "short_name"].read())
                            description.append({
                                key: "Instrument short name:",
                                value: vl
                            })
                        except Exception:
                            sys.stderr.write(
                                "nxsfileinfo: instrument short name cannot"
                                " be found\n")
                            sys.stderr.flush()

                        for sr in ins:
                            if isinstance(sr, filewriter.FTGroup):
                                sat = sr.attributes["NX_class"]
                                if sat and filewriter.first(sat.read()) \
                                   == 'NXsource':
                                    try:
                                        vl = filewriter.first(
                                            sr.open("name").read())
                                        description.append({
                                            key: "Source name:",
                                            value: vl})
                                    except Exception:
                                        sys.stderr.write(
                                            "nxsfileinfo: source name"
                                            " cannot be found\n")
                                        sys.stderr.flush()
                                    try:
                                        vl = filewriter.first(
                                            sr.open("name").attributes[
                                                "short_name"].read())
                                        description.append({
                                            key: "Source short name:",
                                            value: vl})
                                    except Exception:
                                        sys.stderr.write(
                                            "nxsfileinfo: source short name"
                                            " cannot be found\n")
                                        sys.stderr.flush()
                    elif iat and filewriter.first(iat.read()) == 'NXsample':
                        try:
                            vl = filewriter.first(ins.open("name").read())
                            description.append({
                                key: "Sample name:",
                                value: vl})
                        except Exception:
                            sys.stderr.write(
                                "nxsfileinfo: sample name cannot be found\n")
                            sys.stderr.flush()
                        try:
                            vl = filewriter.first(
                                ins.open("chemical_formula").read())
                            description.append({
                                key: "Sample formula:",
                                value: vl})
                        except Exception:
                            sys.stderr.write(
                                "nxsfileinfo: sample formula cannot"
                                " be found\n")
                            sys.stderr.flush()
            try:
                vl = filewriter.first(entry.open("start_time").read())
                description.append({key: "Start time:", value: vl})
            except Exception:
                sys.stderr.write("nxsfileinfo: start time cannot be found\n")
                sys.stderr.flush()
            try:
                vl = filewriter.first(entry.open("end_time").read())
                description.append({key: "End time:",
                                    value: vl})
            except Exception:
                sys.stderr.write("nxsfileinfo: end time cannot be found\n")
                sys.stderr.flush()
            if "program_name" in entry.names():
                pn = entry.open("program_name")
                pname = filewriter.first(pn.read())
                attr = pn.attributes
                names = [att.name for att in attr]
                if "scan_command" in names:
                    scommand = filewriter.first(attr["scan_command"].read())
                    pname = "%s (%s)" % (pname, scommand)
                description.append({key: "Program:", value: pname})
        return [key, value]

    def show(self, root):
        """ show general informations

        :param root: nexus file root
        :type root: class:`filewriter.FTGroup`
        """

        description = []

        attr = root.attributes

        names = [at.name for at in attr]
        fname = filewriter.first(
            (attr["file_name"].read()
             if "file_name" in names else " ") or " ")
        title = "File name: '%s'" % fname

        print("")
        for en in root:
            description = []
            headers = self.parseentry(en, description)
            ttools = TableTools(description)
            ttools.title = title
            ttools.headers = headers
            rstdescription = ttools.generateList()
            title = ""
            print("\n".join(rstdescription).strip())
            print("")


class BeamtimeLoader(object):

    btmdmap = {
        "principalInvestigator": "pi.email",
        # "pid": "beamtimeId",   # ?? is not unique for dataset
        "owner": "applicant.lastname",
        "contactEmail": "contact",
        "sourceFolder": "corePath",

        "endTime": "eventEnd",    # ?? should be endTime for dataset
        "ownerEmail": "applicant.email",
        "description": "title",   # ?? should be from dataset
        "createdAt": "generated",  # ?? should be automatic
        "updatedAt": "generated",  # ?? should be automatic
        "proposalId": "proposalId",
    }

    strcre = {
        "creationLocation": "/DESY/{facility}/{beamline}",
        "type": "raw",
        "isPublished": False,
    }

    cre = {
        "creationTime": [],  # ?? startTime for dataset !!!
        "ownerGroup": [],  # ??? !!!

        "sampleId": [],  # ???
        "publisheddataId": [],
        "accessGroups": [],  # ???
        "createdBy": [],  # ???
        "updatedBy": [],  # ???
        "createdAt": [],  # ???
        "updatedAt": [],  # ???
        "isPublished": ["false"],
        "dataFormat": [],
        "scientificMetadata": {},
        "orcidOfOwner": "ORCID of owner https://orcid.org "
        "if available",
        "sourceFolderHost": [],
        "size": [],
        "packedSize": [],
        "numberOfFiles": [],
        "numberOfFilesArchived": [],
        "validationStatus": [],
        "keywords": [],
        "datasetName": [],
        "classification": [],
        "license": [],
        "version": [],
        "techniques": [],
        "instrumentId": [],
        "history": [],
        "datasetlifecycle": [],

    }

    dr = {
        "eventStart": [],
        "beamlineAlias": [],
        "leader": [],
        "onlineAnalysis": [],
        "pi.*": [],
        "applicant.*": [],
        "proposalType": [],
        "users": [],
    }

    copymap = {
        "endTime": "scientificMetadata.end_time.value",
        "creationTime": "scientificMetadata.end_time.value",
        "description": "scientificMetadata.title.value",
    }

    def __init__(self, options):
        """ loader constructor

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        """
        self.__pid = options.pid
        dct = {}
        if options.beamtimemeta:
            with open(options.beamtimemeta, "r") as fl:
                # jstr = fl.read()
                # # print(jstr)
                dct = json.load(fl)
        self.__btmeta = dct
        dct = {}
        if options.scientificmeta:
            with open(options.scientificmeta, "r") as fl:
                jstr = fl.read()
                # print(jstr)
                try:
                    dct = json.loads(jstr)
                except Exception:
                    if jstr:
                        nan = float('nan')    # noqa: F841
                        dct = eval(jstr)
                        # mdflatten(dstr, [], dct)
        if 'scientificMetadata' in dct.keys():
            self.__scmeta = dct['scientificMetadata']
        else:
            self.__scmeta = dct
        self.__metadata = {}

    def run(self):
        """ runner for DESY beamtime file parser

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :returns: metadata dictionary
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """

        if self.__btmeta:
            for sc, ds in self.btmdmap.items():
                sds = ds.split(".")
                md = self.__btmeta
                for sd in sds:
                    if sd in md:
                        md = md[sd]
                    else:
                        print("%s cannot be found" % ds)
                        break
                else:
                    self.__metadata[sc] = md
            for sc, vl in self.strcre.items():
                if hasattr(vl, "format"):
                    self.__metadata[sc] = vl.format(**self.__btmeta)
                else:
                    self.__metadata[sc] = vl
        if self.__scmeta or self.__btmeta:
            self.__metadata["scientificMetadata"] = {}
        if self.__scmeta:
            self.__metadata["scientificMetadata"].update(self.__scmeta)
        if self.__btmeta and \
           "beamtimeId" not in self.__metadata["scientificMetadata"]:
            self.__metadata["scientificMetadata"]["beamtimeId"] = \
                self.__btmeta["beamtimeId"]
        if self.__pid:
            self.__metadata["pid"] = self.__pid
        # print(self.__metadata)
        return self.__metadata

    def merge(self, metadata):
        """ update metadata with dictionary

        :param metadata: metadata dictionary to merge in
        :type metadata: :obj:`dict` <:obj:`str`, `any`>
        :returns: metadata dictionary
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        if not self.__metadata:
            return metadata
        elif not metadata:
            return metadata
        return dict(self._mergedict(metadata, self.__metadata))

    def overwrite(self, metadata, cmap=None):
        """ overwrite metadata with dictionary

        :param metadata: metadata dictionary to merge in
        :type metadata: :obj:`dict` <:obj:`str`, `any`>
        :param cmap: overwrite dictionary
        :type cmap: :obj:`dict` <:obj:`str`, :obj:`str`>
        :returns: metadata dictionary
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        if cmap is None:
            cmap = self.copymap
        if metadata:
            for ts, vs in self.copymap.items():
                vls = vs.split(".")
                md = metadata
                for vl in vls:
                    if vl in md:
                        md = md[vl]
                    else:
                        break
                else:
                    tgs = ts.split(".")
                    td = metadata
                    parent = None
                    for tg in tgs:
                        parent = td
                        if tg in td:
                            td = td[tg]
                        else:
                            td = td[tg] = {}
                    parent[tg] = md
        return metadata

    @classmethod
    def _mergedict(self, dct1, dct2):
        for key in set(dct1) | set(dct2):
            if key in dct1 and key in dct2:
                if isinstance(dct1[key], dict) and isinstance(dct2[key], dict):
                    yield (key, dict(self._mergedict(dct1[key], dct2[key])))
                else:
                    yield (key, dct2[key])
            elif key in dct1:
                yield (key, dct1[key])
            else:
                yield (key, dct2[key])

    def updatepid(self, metadata, filename=None, puuid=False, pfname=False,
                  beamtimeid=None):
        """ update pid metadata with dictionary

        :param metadata: metadata dictionary to merge in
        :type metadata: :obj:`dict` <:obj:`str`, `any`>
        :param filename: nexus filename
        :type filename: :obj:`str`
        :param puuid: pid with uuid
        :type puuid: :obj:`bool`
        :param pfname: pid with file name
        :type pfname: :obj:`bool`
        :returns: metadata dictionary
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        if "pid" not in metadata:
            beamtimeid = beamtimeid or ""
            if not beamtimeid and "scientificMetadata" in metadata \
               and "beamtimeId" in metadata["scientificMetadata"]:
                beamtimeid = metadata["scientificMetadata"]["beamtimeId"]
            scanid = ""
            fsscanid = ""
            fiscanid = None
            fname = ""
            if filename:
                fdir, fname = os.path.split(filename)
                fname, fext = os.path.splitext(fname)
                lfl = fname.split("_")
                fsscanid = lfl[-1]
                res = re.search(r'\d+$', fsscanid)
                fiscanid = int(res.group()) if res else None
            esscanid = ""
            eiscanid = None
            lfl = None
            if "scientificMetadata" in metadata and \
               "name" in metadata["scientificMetadata"] and \
               metadata["scientificMetadata"]["name"]:
                lfl = metadata["scientificMetadata"]["name"].split("_")
                esscanid = lfl[-1]
                res = re.search(r'\d+$', esscanid)
                eiscanid = int(res.group()) if res else None
                # if eiscanid:
                #     print("WWWW:", eiscanid)
            if pfname and fname and fiscanid is not None:
                scanid = pfname
            elif pfname and fname and eiscanid is not None:
                scanid = "%s_%s" % (fname, eiscanid)
            elif pfname and fname:
                scanid = pfname
            elif fiscanid is not None:
                scanid = str(fiscanid)
            elif eiscanid is not None:
                scanid = str(eiscanid)
            elif fsscanid and esscanid and esscanid == fsscanid:
                scanid = esscanid
            elif fsscanid and esscanid and esscanid != fsscanid:
                scanid = "%s_%s" % (fsscanid, esscanid)
            elif fsscanid:
                scanid = fsscanid
            else:
                scanid = esscanid
            if beamtimeid and scanid:
                if puuid:
                    metadata["pid"] = "%s/%s/%s" % \
                        (beamtimeid, scanid, str(uuid.uuid4()))
                else:
                    metadata["pid"] = "%s/%s" % \
                        (beamtimeid, scanid)

        return metadata


class Metadata(Runner):

    """ Metadata runner"""

    #: (:obj:`str`) command description
    description = "show metadata information for the nexus file"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxsfileinfo metadata /user/data/myfile.nxs\n" \
        + "       nxsfileinfo metadata /user/data/myfile.nxs -p 'Group'\n" \
        + "       nxsfileinfo metadata /user/data/myfile.nxs -s\n" \
        + "       nxsfileinfo metadata /user/data/myfile.nxs " \
        + "-a units,NX_class\n" \
        + "\n"

    def create(self):
        """ creates parser

        """
        self._parser.add_argument(
            "-a", "--attributes",
            help="names of field or group attributes to be show "
            " (separated by commas without spaces). "
            "The  default takes all attributes",
            dest="attrs", default=None)
        self._parser.add_argument(
            "-n", "--hidden-attributes",
            help="names of field or group attributes to be hidden "
            " (separated by commas without spaces). "
            "The  default: 'nexdatas_source,nexdatas_strategy'",
            dest="nattrs", default="nexdatas_source,nexdatas_strategy")
        self._parser.add_argument(
            "-v", "--values",
            help="field names of more dimensional datasets"
            " which value should be shown"
            " (separated by commas without spaces)",
            dest="values", default="")
        self._parser.add_argument(
            "-g", "--group-postfix",
            help="postfix to be added to NeXus group name. "
            "The  default: 'Parameters'",
            dest="group_postfix", default="Parameters")
        self._parser.add_argument(
            "-t", "--entry-classes",
            help="names of entry NX_class to be shown"
            " (separated by commas without spaces)."
            " If name is '' all groups are shown. "
            "The  default: 'NXentry'",
            dest="entryclasses", default="NXentry")
        self._parser.add_argument(
            "-e", "--entry-names",
            help="names of entry groups to be shown"
            " (separated by commas without spaces)."
            " If name is '' all groups are shown. "
            "The  default: ''",
            dest="entrynames", default="")
        self._parser.add_argument(
            "-r", "--raw-metadata", action="store_true",
            default=False, dest="rawscientific",
            help="do not store NXentry as scientificMetadata")
        self._parser.add_argument(
            "-p", "--pid", dest="pid",
            help=("dataset pid"))
        self._parser.add_argument(
            "-i", "--beamtimeid", dest="beamtimeid",
            help=("beamtime id"))
        self._parser.add_argument(
            "-u", "--pid-with-uuid", action="store_true",
            default=False, dest="puuid",
            help=("generate pid with uuid"))
        self._parser.add_argument(
            "-f", "--pid-with-filename", action="store_true",
            default=False, dest="pfname",
            help=("generate pid with file name"))
        self._parser.add_argument(
            "--h5py", action="store_true",
            default=False, dest="h5py",
            help="use h5py module as a nexus reader")
        self._parser.add_argument(
            "--h5cpp", action="store_true",
            default=False, dest="h5cpp",
            help="use h5cpp module as a nexus reader")

    def postauto(self):
        """ parser creator after autocomplete run """
        self._parser.add_argument(
            "-b", "--beamtime-meta", dest="beamtimemeta",
            help=("beamtime metadata file"))
        self._parser.add_argument(
            "-s", "--scientific-meta", dest="scientificmeta",
            help=("scientific metadata file"))
        self._parser.add_argument(
            "-o", "--output", dest="output",
            help=("output scicat metadata file"))
        self._parser.add_argument(
            'args', metavar='nexus_file', type=str, nargs=1,
            help='new nexus file name')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :returns: output information
        :rtype: :obj:`str`
        """
        if options.h5cpp:
            writer = "h5cpp"
        elif options.h5py:
            writer = "h5py"
        elif "h5cpp" in WRITERS.keys():
            writer = "h5cpp"
        else:
            writer = "h5py"
        if (options.h5cpp and options.h5py) or writer not in WRITERS.keys():
            sys.stderr.write("nxsfileinfo: Writer '%s' cannot be opened\n"
                             % writer)
            sys.stderr.flush()
            self._parser.print_help()
            sys.exit(255)
        wrmodule = WRITERS[writer.lower()]
        try:
            fl = filewriter.open_file(
                options.args[0], readonly=True,
                writer=wrmodule)
        except Exception:
            sys.stderr.write("nxsfileinfo: File '%s' cannot be opened\n"
                             % options.args[0])
            sys.stderr.flush()
            self._parser.print_help()
            sys.exit(255)

        root = fl.root()
        self.show(root, options)
        fl.close()

    @classmethod
    def metadata(cls, root, options):
        """ get metadata from nexus and beamtime file

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :param root: nexus file root
        :type root: :class:`filewriter.FTGroup`
        :returns: nexus file root
        :rtype: :obj:`str`
        """
        values = []
        attrs = None
        entryclasses = []
        entrynames = []

        if options.values:
            values = options.values.split(',')

        if options.attrs:
            attrs = options.attrs.split(',')
        elif options.attrs is not None:
            attrs = []

        if options.nattrs not in [None, '', "''", '""']:
            nattrs = options.nattrs.split(',')
        else:
            nattrs = []

        if options.entryclasses not in [None, '', "''", '""']:
            entryclasses = options.entryclasses.split(',')

        if options.entrynames not in [None, '', "''", '""']:
            entrynames = options.entrynames.split(',')

        nxsparser = NXSFileParser(root)
        nxsparser.valuestostore = values
        nxsparser.group_postfix = options.group_postfix
        nxsparser.entryclasses = entryclasses
        nxsparser.entrynames = entrynames
        nxsparser.scientific = not options.rawscientific
        nxsparser.attrs = attrs
        nxsparser.hiddenattrs = nattrs
        nxsparser.parseMeta()

        if nxsparser.description:
            if len(nxsparser.description) == 1:
                desc = nxsparser.description[0]
                if not options.beamtimemeta:
                    try:
                        if "scientificMetadata" in desc \
                           and "experiment_identifier" in \
                           desc["scientificMetadata"] \
                           and "beamtime_filename" in \
                           desc["scientificMetadata"][
                               "experiment_identifier"]:
                            options.beamtimemeta = \
                                desc["scientificMetadata"][
                                    "experiment_identifier"][
                                        "beamtime_filename"]
                    except Exception:
                        pass
                bl = BeamtimeLoader(options)
                bl.run()
                result = bl.merge(desc)
                result = bl.overwrite(result)
                result = bl.updatepid(
                    result, options.args[0], options.puuid,
                    options.pfname, options.beamtimeid)

            else:
                result = []
                for desc in nxsparser.description:
                    if not options.beamtimemeta:
                        try:
                            if "scientificMetadata" in desc \
                               and "experimental_identifier" in \
                               desc["scientificMetadata"] \
                               and "beamtime_filename" in \
                               desc["scientificMetadata"][
                                   "experimental_identifier"]:
                                options.beamtimemeta = \
                                    desc["scientificMetadata"][
                                        "experimental_identifier"][
                                            "beamtime_filename"]
                        except Exception:
                            pass
                    bl = BeamtimeLoader(options)
                    bl.run()
                    rst = bl.merge(desc)
                    rst = bl.overwrite(rst)
                    rst = bl.updatepid(
                        rst, options.args[0], options.puuid,
                        options.pfname, options.beamtimeid)
                    result.append(rst)
            return json.dumps(
                result, sort_keys=True, indent=4,
                cls=numpyEncoder)

    def show(self, root, options):
        """ the main function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :param root: nexus file root
        :type root: :class:`filewriter.FTGroup`
        """
        try:
            metadata = self.metadata(root, options)
            if metadata:
                if options.output:
                    with open(options.output, "w") as fl:
                        fl.write(metadata)
                else:
                    print(metadata)
        except Exception as e:
            sys.stderr.write("nxsfileinfo: '%s'\n"
                             % str(e))
            sys.stderr.flush()
            self._parser.print_help()
            sys.exit(255)


class Field(Runner):

    """ Field runner"""

    #: (:obj:`str`) command description
    description = "show field information for the nexus file"
    #: (:obj:`str`) command epilog
    epilog = "" \
        + " examples:\n" \
        + "       nxsfileinfo field /user/data/myfile.nxs\n" \
        + "       nxsfileinfo field /user/data/myfile.nxs -g\n" \
        + "       nxsfileinfo field /user/data/myfile.nxs -s\n" \
        + "\n"

    def create(self):
        """ creates parser

        """
        self._parser.add_argument(
            "-c", "--columns",
            help="names of column to be shown (separated by commas "
            "without spaces). The possible names are: "
            "depends_on, dtype, full_path, nexus_path, nexus_type, shape,"
            " source, source_name, source_type, strategy, trans_type, "
            "trans_offset, trans_vector, units, value",
            dest="headers", default="")
        self._parser.add_argument(
            "-f", "--filters",
            help="full_path filters (separated by commas "
            "without spaces). Default: '*'. E.g. '*:NXsample/*'",
            dest="filters", default="")
        self._parser.add_argument(
            "-v", "--values",
            help="field names which value should be stored"
            " (separated by commas "
            "without spaces). Default: depends_on",
            dest="values", default="")
        self._parser.add_argument(
            "-g", "--geometry", action="store_true",
            default=False, dest="geometry",
            help="perform geometry full_path filters, i.e."
            "*:NXtransformations/*,*/depends_on. "
            "It works only when  -f is not defined")
        self._parser.add_argument(
            "-s", "--source", action="store_true",
            default=False, dest="source",
            help="show datasource parameters")
        self._parser.add_argument(
            "--h5py", action="store_true",
            default=False, dest="h5py",
            help="use h5py module as a nexus reader")
        self._parser.add_argument(
            "--h5cpp", action="store_true",
            default=False, dest="h5cpp",
            help="use h5cpp module as a nexus reader")

    def postauto(self):
        """ parser creator after autocomplete run """
        self._parser.add_argument(
            'args', metavar='nexus_file', type=str, nargs=1,
            help='new nexus file name')

    def run(self, options):
        """ the main program function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :returns: output information
        :rtype: :obj:`str`
        """
        if options.h5cpp:
            writer = "h5cpp"
        elif options.h5py:
            writer = "h5py"
        elif "h5cpp" in WRITERS.keys():
            writer = "h5cpp"
        else:
            writer = "h5py"
        if (options.h5cpp and options.h5py) or writer not in WRITERS.keys():
            sys.stderr.write("nxsfileinfo: Writer '%s' cannot be opened\n"
                             % writer)
            sys.stderr.flush()
            self._parser.print_help()
            sys.exit(255)
        wrmodule = WRITERS[writer.lower()]
        try:
            fl = filewriter.open_file(
                options.args[0], readonly=True,
                writer=wrmodule)
        except Exception:
            sys.stderr.write("nxsfileinfo: File '%s' cannot be opened\n"
                             % options.args[0])
            sys.stderr.flush()
            self._parser.print_help()
            sys.exit(255)

        root = fl.root()
        self.show(root, options)
        fl.close()

    def show(self, root, options):
        """ the main function

        :param options: parser options
        :type options: :class:`argparse.Namespace`
        :param root: nexus file root
        :type root: class:`filewriter.FTGroup`
        """
        #: (:obj:`list`< :obj:`str`>)   \
        #     parameters which have to exists to be shown
        toshow = None

        #: (:obj:`list`< :obj:`str`>)  full_path filters
        filters = []

        #: (:obj:`list`< :obj:`str`>)  column headers
        headers = ["nexus_path", "source_name", "units",
                   "dtype", "shape", "value"]
        if options.geometry:
            filters = ["*:NXtransformations/*", "*/depends_on"]
            headers = ["nexus_path", "source_name", "units",
                       "trans_type", "trans_vector", "trans_offset",
                       "depends_on"]
        if options.source:
            headers = ["source_name", "nexus_type", "shape", "strategy",
                       "source"]
            toshow = ["source_name"]
        #: (:obj:`list`< :obj:`str`>)  field names which value should be stored
        values = ["depends_on"]

        if options.headers:
            headers = options.headers.split(',')
        if options.filters:
            filters = options.filters.split(',')
        if options.values:
            values = options.values.split(',')

        nxsparser = NXSFileParser(root)
        nxsparser.filters = filters
        nxsparser.valuestostore = values
        nxsparser.parse()

        description = []
        ttools = TableTools(nxsparser.description, toshow)
        ttools.title = "File name: '%s'" % options.args[0]
        ttools.headers = headers
        description.extend(ttools.generateList())
        print("\n".join(description))


def main():
    """ the main program function
    """

    description = "Command-line tool for showing meta data" \
                  + " from Nexus Files"

    epilog = 'For more help:\n  nxsfileinfo <sub-command> -h'
    parser = NXSArgParser(
        description=description, epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.cmdrunners = [('field', Field),
                         ('general', General),
                         ('metadata', Metadata),
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

    result = runners[options.subparser].run(options)
    if result and str(result).strip():
        print(result)


if __name__ == "__main__":
    main()
