#!/usr/bin/env python

import bpcal_cfg as cfg
import argparse
import os

import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def _calibration_beam(sbid, beam):
    sbidcalpath = "{}/{}/scans/00/19000101000000".format(cfg.CALIBRATION_PATH, sbid)
    beamcalpath = "{}/{:0>2}".format(sbidcalpath, beam)
    bpscanms_path = "{}/b{:0>2}.ms".format(beamcalpath, beam)

    if not os.path.exists(bpscanms_path):
        log.warning("no measurement sets file found for {} Beam {}".format(sbid, beam))

    cal_cmd = "{} -vis_ms {} -clean {} -build_dir {} -catalog {} -catfreq {}".format(
        cfg.CALROUTIN_PATH, bpscanms_path, cfg.CLEAN_MS, 
        cfg.CALBUILD_DIR, cfg.RACS_CATALOG, cfg.RACS_REFFREQ,
    )

    log.info("start to calibrate with {}".format(cal_cmd))

    os.system(cal_cmd)

def calibration_sbid(sbid):
    if isinstance(sbid, int): sbid = str(sbid)
    if not sbid.startswith("SB"): sbid = "SB{:0>6}".format(sbid)

    for beam in range(36):
        try: _calibration_beam(sbid, beam)
        except: 
            log.warning("failed to derive calibration from BEAM {}".format(beam))

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument(
        "-sbid", type=str, help="Schedule block used for calibration",
    )
    args = a.parse_args()

    calibration_sbid(args.sbid)
    os.system("rm casa*.log")