### Derive system temperature from a known calibrator observation

from scipy.optimize import leastsq
from casacore import tables
import numpy as np

import logging
import sys

### set logger...
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(formatter)
logger.addHandler(console)

def CasaGetNumAntenna(tab):
    # get from vis table directly instead of reading from Antenna table...
    ant = tab.getcol("ANTENNA1")
    return np.unique(ant).shape[0]
    

def CasaGetNumPol(tabpath):
    logger.info(f"loading pol tab from {tabpath}...")
    poltab = tables.table(f"{tabpath}::POLARIZATION")
    pol_count = poltab.getcol("NUM_CORR")[0]
    logger.info(f"{pol_count} polarisations found in {tabpath}")
    poltab.close()
    return pol_count

def CasaGetSpt(tabpath):
    logger.info(f"loading spectrum tab from {tabpath}...")
    return tables.table(f"{tabpath}::SPECTRAL_WINDOW")

def getnbl(nant, auto=True):
    return int(nant * (nant - 1) / 2 + nant) if auto else int(nant * (nant - 1) / 2)


def get_crosspair_index(nant):
    idx = 0
    crossidx = []
    for ant1 in range(nant):
        for ant2 in range(ant1, nant):
            if ant1 != ant2: crossidx.append(idx)
            idx += 1
    return crossidx


### tweak the data a little bit
def _tweak_time_slice(sample_ave, nsamp):
    if nsamp % sample_ave == 0: return slice(None, None)
    samp_remain = nsamp % sample_ave
    start = samp_remain // 2
    end = samp_remain - start
    return slice(start, -end)


def SEFD_pairs_function(SEFD_ants, SEFD_pairs):
    """
    function passed to `leastsq` function to do final fitting...
    """
    SEFD_pairs = SEFD_pairs.reshape(-1)
    
    nant = len(SEFD_ants)
    nbl = int(nant * (nant - 1) / 2)
    
    assert nbl == len(SEFD_pairs), "non-matched baseline numbers..."
    
    prod_list = []; index = 0
    for i in range(nant):
        for j in range(i+1, nant):
            if np.isnan(SEFD_pairs[index]):
                # set to zero for error value, otherwise it will give initial value...
                prod_list.append(0)
            else:
                prod_list.append(SEFD_ants[i]*SEFD_ants[j] - SEFD_pairs[index])
                
            index += 1
            
    return np.array(prod_list)


def SEFD_ant_fit(SEFD_pairs, nant, defaultSEFD):
    """
    SEFD fitting for a single antenna...
    """
    x0 = np.ones(nant) * defaultSEFD
    SEFD_ant, cov = leastsq(SEFD_pairs_function, x0, args=SEFD_pairs)
    return SEFD_ant


def main(calmspath, sample_ave=30, srcflux=15, defaultSEFD=1000, pathdir="."):
    if calmspath.endswith("/"): calmspath = calmspath[:-1]
    logger.info("loading calibrated visibility...")
    caltab = tables.table(calmspath)

    nant = CasaGetNumAntenna(caltab)
    npol = CasaGetNumPol(calmspath)
    spttab = CasaGetSpt(calmspath)
    nbl = getnbl(nant)

    nchan = spttab.getcol("CHAN_WIDTH").shape[-1]
    fres = spttab.getcol("CHAN_WIDTH").mean()
    tres = caltab.getcol("EXPOSURE").mean()

    logger.info(f"number of channel: {nchan}...")
    logger.info(f"frequency resolution: {fres/1e6:.3f}MHz, time resolution: {tres:3f}s...")

    logger.info("getting `DATA` column...")
    visdata = caltab.getcol("DATA")
    logger.info("getting `FLAG` column...")
    visflag = caltab.getcol("FLAG")

    logger.info("replacing flagged data as nan...")
    visdata[visflag] = np.nan

    logger.info("reshaping the vis data...")
    visdata = visdata.reshape(-1, nbl, nchan, npol)
    logger.info(f"reshaped data shape: {visdata.shape}")

    crossidx = get_crosspair_index(nant)
    logger.info("getting cross-correlation...")
    crossdata = visdata[:, crossidx, :, :]

    nsamp_raw = crossdata.shape[0]
    tsel = _tweak_time_slice(sample_ave, nsamp_raw)
    logger.info(f"selecting data to do further formatting... data selected - {tsel}")
    crossdata = crossdata[tsel, ...]

    logger.info(f"averaging data over {sample_ave} samples...")
    tave_crossdata = crossdata.reshape(-1, sample_ave, nbl-nant, nchan, npol)
    tave_crossdata = np.nanmean(tave_crossdata, axis=1)

    logger.info("extracting real part of the visibility data...")
    tave_crossreal = tave_crossdata.real

    logger.info("calculating snr of the observation...")
    tavem_ = np.nanmean(tave_crossreal, axis=0)
    taves_ = np.nanstd(tave_crossreal, axis=0)

    SEFD_pairs = (srcflux / (tavem_ / taves_))**2 * fres * sample_ave * tres / 2

    logger.info("fitting antenna temperatures...")
    SEFD_ants = []
    for ichan in range(nchan):
        if ichan % 32 == 0: logger.info(f"{ichan} finished...")
        SEFD_ant = SEFD_ant_fit(SEFD_pairs[:, ichan, 0], nant, defaultSEFD)
        SEFD_ants.append(SEFD_ant.reshape(1, -1))

    SEFD_ants = np.vstack(SEFD_ants)

    SEFD_ants[SEFD_ants == defaultSEFD] = np.nan # it cannot be the initial value after fitting...

    calmsname = calmspath.split("/")[-1]
    logger.info(f"saving final antenna temperature to {pathdir}/{calmsname}.SEFDant.npy...")
    np.save(f"{pathdir}/{calmsname}.SEFDant.npy", SEFD_ants)
    

if __name__ == "__main__":
    
    args = sys.argv
    calmspath = args[1]
    pathdir = args[2]

    main(calmspath=calmspath, pathdir=pathdir)
    
