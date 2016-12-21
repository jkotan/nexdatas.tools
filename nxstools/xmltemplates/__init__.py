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

"""  xml templates """


#: (:obj:`dict` <:obj:`str` , :obj:`dict` <:obj:`str` , :obj:`str` > >)
#:     standatd component template variables
#:     and its [default value, doc string]
standardComponentVariables = {
    'pinhole': {
        'x': {
            'default': None,
            'doc': "horizontal position (datasource)"
        },
        'y': {
            'default': None,
            'doc': "vertical position (datasource)"
        },
        'z': {
            'default': None,
            'doc': "vertical position (datasource)"
        },
    },
    'beamstop': {

        'description': {
            'default': 'circular',
            'doc': " circular or  rectangular (string)"
        },
        'x': {
            'default': None,
            'doc': "horizontal position (datasource)"
        },
        'y': {
            'default': None,
            'doc': "vertical position (datasource)"
        },
        'z': {
            'default': None,
            'doc': "vertical position (datasource)"
        },
    },
    'samplehkl': {
        'sname': {
            'default': 'sample',
            'doc': "sample group name (string)"
        },
        'psi': {
            'default': None,
            'doc': "psi angle position of analyzer (datasource)"
        },
        'h': {
            'default': None,
            'doc': "h position in hkl space (datasource)"
        },
        'k': {
            'default': None,
            'doc': "k position in hkl space (datasource)"
        },
        'l': {
            'default': None,
            'doc': "l position in hkl space (datasource)"
        },
    },
    'absorber': {
        'attenfactor': {
            'default': None,
            'doc': "attenuation factor (datasource)"
        },
        'position': {
            'default': None,
            'doc': "which sliders are in [bitarray] (datasource)"
        },
        'foil': {
            'default': None,
            'doc': "foil type, i.e. standard <cpname>_foil (datasource)"
        },
        'thickness': {
            'default': None,
            'doc': "foil thickness, i.e. standard <cpname>_thickness (datasource)"
        },
        'foillist': {
            'default': '["Ag", "Ag", "Ag", "Ag", "", "Al", "Al", "Al", "Al"]',
            'doc': "foil_type position json dictionary (string)"
        },
        'thicknesslist': {
            'default': '[0.5, 0.05, 0.025, 0.0125, 0, 0.1, 0.3, 0.5, 1.0]',
            'doc': "foil_type position json dictionary (string)"
        },
        'distance': {
            'default': None,
            'doc': "distance for the sample in m, e.g. 0 (string)"
        },
        'distanceoffset': {
            'default': None,
            'doc': "3-vector distance offset in m, e.g. sample-source offset if the distance is taken from the source (string)"
        },
        'dependstop': {
            'default': None,
            'doc': "the first transformation, e.g. distance (string)"
        },
        'transformations': {
            'default': None,
            'doc': "transformations group name i.e. 'transformations'. If it is  not set it is not created (string)"
        },
    },
    'keithley': {
        'gain': {
            'default': None,
            'doc': "gain in V/A (datasource)"
        },
        'risetime': {
            'default': None,
            'doc': "rise time (datasource)"
        },
        'current': {
            'default': None,
            'doc': "current in A (datasource)"
        },
        'voltage': {
            'default': None,
            'doc': "voltage in V (datasource)"
        },
        'sourvoltlevel': {
            'default': None,
            'doc': "source voltage level in V (datasource)"
        },
    },
    'qbpm': {
        'foil': {
            'default': None,
            'doc': "foil type, i.e. standard <cpname>_foil (datasource)"
        },
        'foilpos': {
            'default': None,
            'doc': "foil position (datasource)"
        },
        'x': {
            'default': None,
            'doc': "horizontal position (datasource)"
        },
        'y': {
            'default': None,
            'doc': "vertical position (datasource)"
        },
        'foilposdict': {
            'default': '{"Ti": 43, "Ni": 23, "Out": 3}',
            'doc': "foil_type position json dictionary (string)"
        },
        'distance': {
            'default': None,
            'doc': "distance for the sample in m, e.g. 0 (string)"
        },
        'distanceoffset': {
            'default': None,
            'doc': "3-vector distance offset in m, e.g. sample-source offset if the distance is taken from the source (string)"
        },
        'dependstop': {
            'default': "x",
            'doc': "the first transformation, e.g. distance (string)"
        },
        'dependsony': {
            'default': "",
            'doc': "the  depends_on y field value,  e.g. distance (string)"
        },
    },
    'slit': {
        'xgap': {
            'default': None,
            'doc': "horizontal gap (datasource)"
        },
        'ygap': {
            'default': None,
            'doc': "vertical gap (datasource)"
        },
        'xoffset': {
            'default': None,
            'doc': "horizontal offset (datasource)"
        },
        'yoffset': {
            'default': None,
            'doc': "vertiacal offset (datasource)"
        },
        'left': {
            'default': None,
            'doc': "left blade position (datasource)"
        },
        'right': {
            'default': None,
            'doc': "right blade position (datasource)"
        },
        'bottom': {
            'default': None,
            'doc': "bottom blade position (datasource)"
        },
        'top': {
            'default': None,
            'doc': "top blade position (datasource)"
        },
        'distance': {
            'default': None,
            'doc': "distance for the sample in m, e.g. 0 (string)"
        },
        'distanceoffset': {
            'default': None,
            'doc': "3-vector distance offset in m, e.g. sample-source offset if the distance is taken from the source (string)"
        },
        'dependstop': {
            'default': None,
            'doc': "the first transformation, e.g. distance (string)"
        },
        'transformations': {
            'default': None,
            'doc': "transformations group name i.e. 'transformations'. If it is  not set it is not created (string)"
        },
    },
    'source': {
        'beamcurrent': {
            'default': None,
            'doc': "ring beam current (datasource)"
        },
        'sourceenergy': {
            'default': None,
            'doc': "ring beam energy (datasource)"
        },
        'numberofbunches': {
            'default': None,
            'doc': "number of source bunches (datasource)"
        },
        'bunchmode': {
            'default': 'Multi Bunch',
            'doc': "bunch mode (string)"
        },
    },
    'undulator': {
        'uname': {
            'default': 'insertion_device',
            'doc': "insertion_device group name (string)"
        },
        'energy': {
            'default': None,
            'doc': "undulator energy (datasource)"
        },
        'gap': {
            'default': None,
            'doc': "separation between opposing pairs of magnetic pole"
            " (datasource)"
        },
        'taper': {
            'default': None,
            'doc': "gap difference between upstream and downstream ends"
            " of the insertion device (datasource)"
        },
        'harmonic': {
            'default': None,
            'doc': "undulator harmonic (datasource)"
        },
        'type': {
            'default': "undulator",
            'doc': "undulator or wiggler (string)"
        },
        'length': {
            'default': "2",
            'doc': "length of insertion device in meters (string)"
        },
        'distance': {
            'default': None,
            'doc': "distance from the sample in m, e.g. 0 (string)"
        },
        'distanceoffset': {
            'default': None,
            'doc': "3-vector distance offset in m, e.g. sample-source offset if the distance is taken from the source (string)"
        },
        'dependstop': {
            'default': None,
            'doc': "the first transformation, e.g. distance (string)"
        },
        'transformations': {
            'default': None,
            'doc': "transformations group name i.e. 'transformations'. If it is  not set it is not created (string)"
        },
    },
    'beamtimeid': {
        'shortname': {
            'default': "P09",
            'doc': "beamline short name (string)"
        },
        'currentdir': {
            'default': "/gpfs/current",
            'doc': "beamtime file directory (string)"
        },
        'currentprefix': {
            'default': "beamtime-metadata-",
            'doc': "beamtime file prefix (string)"
        },
        'currentpostfix': {
            'default': ".txt",
            'doc': "beamtime file postfix (string)"
        },
        'commissiondir': {
            'default': "/gpfs/commissioning",
            'doc': "commission file directory (string)"
        },
        'commissionprefix': {
            'default': "commission-metadata-",
            'doc': "commission file prefix (string)"
        },
        'commissionpostfix': {
            'default': ".txt",
            'doc': "commission file postfix (string)"
        },
    },
    'default': {
        'shortname': {
            'default': "P09",
            'doc': "beamline short name (string)"
        },
        'longname': {
            'default': "P09 Resonant Scattering and Diffraction beamline",
            'doc': "beamline long name (string)"
        },
        'sourcename': {
            'default': "PETRA III",
            'doc': "source name (string)"
        },
        '__tangohost__': {
            'default': "localhost",
            'doc': "tango host (string)"
        },
        '__tangoport__': {
            'default': "10000",
            'doc': "tango port (string)"
        },
        '__configdevice__': {
            'default': "nxs/configserver/localhost",
            'doc': "configuration server device name (string)"
        },
    },
    'dcm': {
        'energy': {
            'default': None,
            'doc': "synchronized monochromator energy (datasource)"
        },
        'energyfmb': {
            'default': None,
            'doc': "monochromator energy (datasource)"
        },
        'lat': {
            'default': None,
            'doc': "horizontal lattice translation of the first cristal"
            " (datasource)"
        },
        'yaw': {
            'default': None,
            'doc': "phi rotation of the first cristal"
            " (datasource)"
        },
        'roll1': {
            'default': None,
            'doc': "chi rotation of the first cristal"
            " (datasource)"
        },
        'roll2': {
            'default': None,
            'doc': "chi rotation of the second cristal"
            " (datasource)"
        },
        'pitch2': {
            'default': None,
            'doc': "theta rotation of the second cristal"
            " (datasource)"
        },
        'perp2': {
            'default': None,
            'doc': "vertical translation of the second cristal"
            " (datasource)"
        },
        'par2': {
            'default': None,
            'doc': "beam parallel translation of the second cristal"
            " (datasource)"
        },
        'braggangle': {
            'default': None,
            'doc': "bragg angle"
            " (datasource)"
        },
        'jack1': {
            'default': None,
            'doc': "first vertical jack of table"
            " (datasource)"
        },
        'jack2': {
            'default': None,
            'doc': "second vertical jack of table"
            " (datasource)"
        },
        'jack3': {
            'default': None,
            'doc': "third vertical jack of table"
            " (datasource)"
        },
        'table': {
            'default': None,
            'doc': "vertical position of table"
            " (datasource)"
        },
        'oxfordhorizontal': {
            'default': None,
            'doc': " horizontal translation"
            " (datasource)"
        },
        'unitcalibration': {
            'default': None,
            'doc': "unit calibration from dcmmotor"
            " (datasource)"
        },
        'crystal': {
            'default': None,
            'doc': "type of crystal i.e. 0->Si111,1->Si311,2->Si111 ChannelCut"
            " (datasource)"
        },
        'exitoffset': {
            'default': None,
            'doc': " exit offset"
            " (datasource)"
        },
        'theta': {
            'default': None,
            'doc': "theta angle"
            " (datasource)"
        },
        'dcmdevice': {
            'default': None,
            'doc': "FMBOxfDCMEnergy tango device"
            " (string)"
        },
    },
    'collect2': {
        'first': {
            'default': None,
            'doc': "name of the first component to collect (datasource)"
        },
        'second': {
            'default': None,
            'doc': "name of the second component to collect (datasource)"
        }
    },
    'collect3': {
        'first': {
            'default': None,
            'doc': "name of the first component to collect (datasource)"
        },
        'second': {
            'default': None,
            'doc': "name of the second component to collect (datasource)"
        },
        'third': {
            'default': None,
            'doc': "name of the third component to collect (datasource)"
        }
    },
    'common2': {
        'dds': {
            'default': None,
            'doc': "default read datasource name (datasource)"
        },
        'ods': {
            'default': None,
            'doc': "optional detasource name (datasource)"
        }
    },
    'common3': {
        'dds': {
            'default': None,
            'doc': "default read datasource name (datasource)"
        },
        'ods1': {
            'default': None,
            'doc': "fist optional detasource name (datasource)"
        },
        'ods2': {
            'default': None,
            'doc': "second optional detasource name (datasource)"
        }
    },
}

#: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`str`> >)
#:     xml template files of modules
standardComponentTemplateFiles = {
    'qbpm': [
        'qbpm.xml',
        'qbpm_foil.ds.xml',
    ],
    'slit': ['slit.xml'],
    'source': ['source.xml'],
    'undulator': ['undulator.xml'],
    'beamtimeid': [
        'beamtimeid.xml',
        'beamtimeid.ds.xml',
        'beamtimeid_current.ds.xml',
        'beamtimeid_commission.ds.xml',
        'beamtimeid_local.ds.xml',
        'start_time.ds.xml',
    ],
    'default': [
        'default.xml',
        'sample_name.ds.xml',
        'chemical_formula.ds.xml',
        'beamtime_id.ds.xml',
        'start_time.ds.xml',
        'end_time.ds.xml',
        'nexdatas_version.ds.xml',
        'nexdatas_configuration.ds.xml',
        'title.ds.xml',
    ],
    'dcm': [
        'dcm.xml',
        'dcm_reflection.ds.xml',
        'dcm_unitcalibration.ds.xml',
        'dcm_crystal.ds.xml',
    ],
    'collect2': [
        'collect2.xml',
    ],
    'collect3': [
        'collect3.xml',
    ],
    'common2': [
        'common2_common.ds.xml',
    ],
    'common3': [
        'common3_common.ds.xml',
    ],
    'absorber': [
        'absorber.xml',
        'absorber_foil.ds.xml',
        'absorber_thickness.ds.xml',
    ],
    'keithley': [
        'keithley.xml',
    ],
    'pinhole': [
        'pinhole.xml',
    ],
    'beamstop': [
        'beamstop.xml',
    ],
}

#: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`str`> >)
#:     xml template files of modules
moduleTemplateFiles = {
    'mythen2': ['mythen2.xml'],
    'mythen': ['mythen.xml',
               'mythen_postrun.ds.xml',
               'mythen_filestartnumber.ds.xml'],
    'pilatus100k': ['pilatus.xml',
                    'pilatus_postrun.ds.xml',
                    'pilatus100k_description.ds.xml',
                    'pilatus_filestartnum_cb.ds.xml'],
    'pilatus300k': ['pilatus.xml',
                    'pilatus_postrun.ds.xml',
                    'pilatus300k_description.ds.xml',
                    'pilatus_filestartnum_cb.ds.xml'],
    'pilatus1m': ['pilatus.xml',
                  'pilatus_postrun.ds.xml',
                  'pilatus1m_description.ds.xml',
                  'pilatus_filestartnum_cb.ds.xml'],
    'pilatus2m': ['pilatus.xml',
                  'pilatus_postrun.ds.xml',
                  'pilatus2m_description.ds.xml',
                  'pilatus_filestartnum_cb.ds.xml'],
    'pilatus6m': ['pilatus.xml',
                  'pilatus_postrun.ds.xml',
                  'pilatus6m_description.ds.xml',
                  'pilatus_filestartnum_cb.ds.xml'],
    'pilatus': ['pilatus.xml',
                'pilatus_postrun.ds.xml',
                'pilatus_description.ds.xml',
                'pilatus_filestartnum_cb.ds.xml'],
    'pco': ['pco.xml',
            'pco_postrun.ds.xml',
            'pco_description.ds.xml',
            'pco_filestartnum_cb.ds.xml'],
    'pcoedge': ['pco.xml',
                'pco_postrun.ds.xml',
                'pco_description.ds.xml',
                'pco_filestartnum_cb.ds.xml'],
    'pco4000': ['pco.xml',
                'pco_postrun.ds.xml',
                'pco_description.ds.xml',
                'pco_filestartnum_cb.ds.xml'],
    'lambda': ['lambda.xml',
               'lambda_external_data.ds.xml'],
    'lambda2m': ['lambda2m.xml',
                 'lambda2m_m1_external_data.ds.xml',
                 'lambda2m_m2_external_data.ds.xml',
                 'lambda2m_m3_external_data.ds.xml'],
    'perkinelmerdetector': [
        'perkinelmerdetector.xml',
        'perkinelmerdetector_postrun.ds.xml',
        'perkinelmerdetector_description.ds.xml',
        'perkinelmerdetector_fileindex_cb.ds.xml'
    ],
    'perkinelmer': [
        'perkinelmerdetector.xml',
        'perkinelmerdetector_postrun.ds.xml',
        'perkinelmerdetector_description.ds.xml',
        'perkinelmerdetector_fileindex_cb.ds.xml'
    ],
    'pedetector': [
        'perkinelmerdetector.xml',
        'perkinelmerdetector_postrun.ds.xml',
        'perkinelmerdetector_description.ds.xml',
        'perkinelmerdetector_fileindex_cb.ds.xml'
    ],
    'marccd': ['marccd.xml',
               'marccd_postrun.ds.xml'],
    'mca_xia': [
        'mcaxia.xml'
    ],
    'eigerdectris': [
        'eigerdectris.xml',
        'eigerdectris_stepindex.ds.xml',
        'eigerdectris_description_cb.ds.xml',
        'eigerdectris_triggermode_cb.ds.xml'
    ],
}

#: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`str`> >)
#:     important attributes of modules
moduleMultiAttributes = {
    'mca_xia': [
    ],
    'mca_xia@pool': [
        'CountsRoI', 'RoIEnd', 'RoIStart', 'Value',
    ],
    'pco': [
        'DelayTime', 'ExposureTime', 'NbFrames', 'TriggerMode',
        'FileDir', 'FilePostfix', 'FilePrefix', 'FileStartNum',
        'Binning_x', 'Binning_y', 'ROI_x_min', 'ROI_x_max',
        'ROI_y_min', 'ROI_y_max', 'Pixelrate', 'ADCs',
        'CoolingTemp', 'CoolingTempSet', 'ImageTimeStamp',
        'RecorderMode',
    ],
    'pcoedge': [
        'DelayTime', 'ExposureTime', 'NbFrames', 'TriggerMode',
        'FileDir', 'FilePostfix', 'FilePrefix', 'FileStartNum',
        'Binning_x', 'Binning_y', 'ROI_x_min', 'ROI_x_max',
        'ROI_y_min', 'ROI_y_max', 'Pixelrate', 'ADCs',
        'CoolingTemp', 'CoolingTempSet', 'ImageTimeStamp',
        'RecorderMode',
    ],
    'pco4000': [
        'DelayTime', 'ExposureTime', 'NbFrames', 'TriggerMode',
        'FileDir', 'FilePostfix', 'FilePrefix', 'FileStartNum',
        'Binning_x', 'Binning_y', 'ROI_x_min', 'ROI_x_max',
        'ROI_y_min', 'ROI_y_max', 'Pixelrate', 'ADCs',
        'CoolingTemp', 'CoolingTempSet', 'ImageTimeStamp',
        'RecorderMode',
    ],
    'pilatus100k': [
        'DelayTime', 'ExposurePeriod', 'ExposureTime', 'FileDir',
        'FilePostfix', 'FilePrefix', 'FileStartNum', 'LastImageTaken',
        'NbExposures', 'NbFrames'],
    'pilatus300k': [
        'DelayTime', 'ExposurePeriod', 'ExposureTime', 'FileDir',
        'FilePostfix', 'FilePrefix', 'FileStartNum', 'LastImageTaken',
        'NbExposures', 'NbFrames'],
    'pilatus1m': [
        'DelayTime', 'ExposurePeriod', 'ExposureTime', 'FileDir',
        'FilePostfix', 'FilePrefix', 'FileStartNum', 'LastImageTaken',
        'NbExposures', 'NbFrames'],
    'pilatus2m': [
        'DelayTime', 'ExposurePeriod', 'ExposureTime', 'FileDir',
        'FilePostfix', 'FilePrefix', 'FileStartNum', 'LastImageTaken',
        'NbExposures', 'NbFrames'],
    'pilatus6m': [
        'DelayTime', 'ExposurePeriod', 'ExposureTime', 'FileDir',
        'FilePostfix', 'FilePrefix', 'FileStartNum', 'LastImageTaken',
        'NbExposures', 'NbFrames'],
    'perkinelmerdetector': [
        'BinningMode', 'FileIndex', 'ExposureTime', 'SkippedAtStart',
        'SummedSaveImages', 'SkippedBetweenSaved', 'FilesAfterTrigger',
        'FilesBeforeTrigger', 'SummedDarkImages', 'OutputDirectory',
        'FilePattern', 'FileName', 'LogFile', 'UserComment1', 'CameraGain',
        'UserComment2', 'UserComment3', 'UserComment4', 'SaveRawImages',
        'SaveDarkImages', 'PerformIntegration', 'SaveIntegratedData',
        'SaveSubtracted', 'PerformDarkSubtraction'
    ],
    'perkinelmer': [
        'BinningMode', 'FileIndex', 'ExposureTime', 'SkippedAtStart',
        'SummedSaveImages', 'SkippedBetweenSaved', 'FilesAfterTrigger',
        'FilesBeforeTrigger', 'SummedDarkImages', 'OutputDirectory',
        'FilePattern', 'FileName', 'LogFile', 'UserComment1', 'CameraGain',
        'UserComment2', 'UserComment3', 'UserComment4', 'SaveRawImages',
        'SaveDarkImages', 'PerformIntegration', 'SaveIntegratedData',
        'SaveSubtracted', 'PerformDarkSubtraction'
    ],
    'lambda': [
        'TriggerMode', 'ShutterTime', 'DelayTime', 'FrameNumbers', 'ThreadNo',
        'EnergyThreshold', 'OperatingMode', 'ConfigFilePath', 'SaveAllImages',
        'FilePrefix', 'FileStartNum', 'FilePreExt', 'FilePostfix',
        'SaveFilePath', 'SaveFileName', 'LatestImageNumber', 'LiveMode',
        'TotalLossFrames', 'CompressorShuffle', 'CompressionRate',
        'CompressionEnabled', 'Layout', 'ShutterTimeMax', 'ShutterTimeMin',
        'Width', 'Height', 'Depth', 'LiveFrameNo', 'DistortionCorrection',
        'LiveLastImageData'
    ],
    'lambda2m': [
        'TriggerMode', 'ShutterTime', 'DelayTime', 'FrameNumbers', 'ThreadNo',
        'EnergyThreshold', 'OperatingMode', 'ConfigFilePath', 'SaveAllImages',
        'FilePrefix', 'FileStartNum', 'FilePreExt', 'FilePostfix',
        'SaveFilePath', 'SaveFileName', 'LatestImageNumber', 'LiveMode',
        'TotalLossFrames', 'CompressorShuffle', 'CompressionRate',
        'CompressionEnabled', 'Layout', 'ShutterTimeMax', 'ShutterTimeMin',
        'Width', 'Height', 'Depth', 'LiveFrameNo', 'DistortionCorrection',
        'LiveLastImageData'
    ],
    'pedetector': [
        'BinningMode', 'FileIndex', 'ExposureTime', 'SkippedAtStart',
        'SummedSaveImages', 'SkippedBetweenSaved', 'FilesAfterTrigger',
        'FilesBeforeTrigger', 'SummedDarkImages', 'OutputDirectory',
        'FilePattern', 'FileName', 'LogFile', 'UserComment1', 'CameraGain',
        'UserComment2', 'UserComment3', 'UserComment4', 'SaveRawImages',
        'SaveDarkImages', 'PerformIntegration', 'SaveIntegratedData',
        'SaveSubtracted', 'PerformDarkSubtraction'
    ],
    'pilatus': [
        'DelayTime', 'ExposurePeriod', 'ExposureTime', 'FileDir',
        'FilePostfix', 'FilePrefix', 'FileStartNum', 'LastImageTaken',
        'NbExposures', 'NbFrames'],
    'mythen': [
        'Counts1', 'Counts2', 'CountsMax', 'CountsTotal', 'ExposureTime',
        'FileDir', 'FileIndex', 'FilePrefix', 'Data', 'RoI1', 'RoI2'
    ],
    'mythen2': [
        'Counts1', 'Counts2', 'CountsMax', 'CountsTotal', 'ExposureTime',
        'FileDir', 'FileIndex', 'FilePrefix', 'Data',
        'Energy', 'NbFrames', 'RoI1End', 'RoI2End', 'RoI1Start', 'RoI2Start',
        'Threshold'
    ],
    'marccd': [
        'FrameShift', 'SavingDirectory', 'SavingPostfix', 'SavingPrefix'],
    'eigerdectris': [
        'TriggerMode', 'NbTriggers', 'Description', 'NbImages', 'BitDepth',
        'ReadoutTime', 'CountTime', 'EnergyThreshold', 'FrameTime',
        'RateCorrectionEnabled', 'FlatFieldEnabled', 'Temperature',
        'AutoSummationEnabled', 'Humidity', 'PhotonEnergy', 'Wavelength',
    ],
    'samplehkl': [
        'samplehkl.xml'
    ],
}
