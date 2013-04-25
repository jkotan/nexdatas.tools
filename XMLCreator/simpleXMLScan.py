#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2013 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \package ndtstools tools for ndts
## \file simpleXMLScan.py
# test of XML file creator

from simpleXML import *

## the main function
def main():
    df = XMLFile("scan.xml")
    
    en = NGroup(df, "entry1", "NXentry")

    ## instrument
    ins = NGroup(en, "instrument", "NXinstrument")
#    NXsource    
    dt = NGroup(ins, "detector", "NXdetector")
    f = NField(dt, "counter1", "NX_FLOAT")
    f.setUnits("m")
#    f.setText("0.2")
    f.setStrategy("STEP")
    sr = NDSource(f)

    sr.initClient("exp_c01","exp_c01");


    f = NField(dt, "counter2", "NX_FLOAT")
    f.setUnits("s")
#    f.setText("0.2")
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initClient("exp_c02","exp_c02");
    

    f = NField(dt, "mca", "NX_FLOAT")
    f.setUnits("")
    d = NDimensions(f, "1")
    d.dim("1", "2048")
    f.setStrategy("STEP")
    sr = NDSource(f)
    sr.initTango("p09/mca/exp.02","p09/mca/exp.02", "attribute", "Data")
#    sr.initClient("p09/mca/exp.02","p09/mca/exp.02")

        ##    NXdata
    da = NGroup(en, "data", "NXdata")
    ## link
    l = NLink(da, "data", "/NXentry/NXinstrument/NXdetector/mca")
    l.addDoc("Link to mca in /NXentry/NXinstrument/NXdetector")
    l = NLink(da, "counter1", "/NXentry/NXinstrument/NXdetector/counter1")
    l.addDoc("Link to counter1 in /NXentry/NXinstrument/NXdetector")
    l = NLink(da, "counter2", "/NXentry/NXinstrument/NXdetector/counter2")
    l.addDoc("Link to counter2 in /NXentry/NXinstrument/NXdetector")



    df.dump()



if __name__ == "__main__":
    main()
