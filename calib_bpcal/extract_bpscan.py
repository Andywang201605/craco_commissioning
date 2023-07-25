#!/usr/bin/env python

"""
function to extract the scan with the bandpass calibrator at the phase centre
perform the direction fix
"""

from casatasks import importuvfits, split, initweights
from casacore import tables
import bpcal_cfg as cfg # configuration file

import os
import glob
import argparse
import numpy as np

import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def split_bpcal_allscam(sbid):
    """
    the structure should be: SB050677/scans/00/20230622110317/00
    """
    if isinstance(sbid, int): sbid = str(sbid)
    if not sbid.startswith("SB"): sbid = "SB{:0>6}".format(sbid)

    sbidcalpath = "{}/{}/scans/00/19000101000000".format(cfg.CALIBRATION_PATH, sbid)

    for beam in range(36):
        try: _split_bpcal_beamscan(sbid, beam, sbidcalpath)
        except: continue

def _polsum_ms(msfname):
    """
    perform polarization sum between XX and YY
    """
    tab = tables.table(msfname, readonly=False)
    log.info("summing polarisation for hardware data...")

    flagcol = tab.getcol("FLAG")
    datacol = tab.getcol("DATA")

    meandata_ = np.mean(datacol, axis=-1, keepdims=True)
    flagdata_ = np.all(flagcol, axis=-1, keepdims=True)

    meandata = np.concatenate([meandata_, meandata_], axis=-1)
    flagdata = np.concatenate([flagdata_, flagdata_], axis=-1)

    tab.putcol("DATA", meandata)
    tab.putcol("FLAG", flagdata)

    tab.close()

def _split_bpcal_beamscan(sbid, beam, calpath):
    """
    split the bandpass observation scan for a given SBID and a given scan
    """
    beamcalpath = "{}/{:0>2}".format(calpath, beam)
    if not os.path.exists(beamcalpath):
        os.makedirs(beamcalpath)
    else:
        log.info("beam directory found... deleting original content within the folder...")
        rmbeam_cmd = "rm -r {}/*".format(beamcalpath)
        os.system(rmbeam_cmd)
    bpscanms_path = "{}/b{:0>2}.ms".format(beamcalpath, beam)

    ### find calibration
    if sbid.startswith("SB"): sbid_int = int(sbid[2:])
    beamms_paths = glob.glob("{}/{}/*_{}.ms".format(cfg.RAWSCAN_PATH, sbid_int, beam))
    log.info("finding {} measurement set(s) from {} - BEAM{:0>2}".format(len(beamms_paths), sbid, beam))
    if len(beamms_paths) == 0: return None
    beamms_path = beamms_paths[0]

    ### start perform splitting...
    log.info("splitting measurement sets for BEAM{:0>2}".format(beam))
    split(
        vis=beamms_path,
        outputvis=bpscanms_path,
        scan=str(beam),
        datacolumn="data",
        correlation="XX,YY",
    )

    ### perform polsum
    _polsum_ms(bpscanms_path)

    ### initweights
    log.info("initialise spectral weights...")
    initweights(
        vis=bpscanms_path,
        wtmode="weight",
        dowtsp=True,
    )

    ### TODO: run fix_dir.py
    log.info("executing fix_dir.py on the splitted measurement sets...")
    fixdir_cmd = "{} {}".format(cfg.FIX_DIR_PATH, bpscanms_path)
    os.system(fixdir_cmd)

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument(
        "-sbid", type=str, help="Schedule block used for calibration",
    )
    args = a.parse_args()

    split_bpcal_allscam(args.sbid)
    os.system("rm casa*.log")






