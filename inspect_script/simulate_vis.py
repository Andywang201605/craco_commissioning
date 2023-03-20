import os
import numpy as np

import logging

### set logger...
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(formatter)
logger.addHandler(console)

def sim_ant_data(nant, nt, srcflux=0.01, ave=True):
    logger.info(f"creating noise vector for antennas - shape: ({nant}, {nt})")
    n = 1/np.sqrt(2) * np.random.randn(nant, nt) + 1j * 1/np.sqrt(2) * np.random.randn(nant, nt)
    logger.info(f"creating noise vector for antennas - shape: ({nant}, {nt})")
    s = np.repeat(np.sqrt(srcflux) * np.random.randn(1, nt), nant, axis=0)

    a = n + s

    if not ave: raise NotImplementedError("Do not support non-average at this point...")
    
    logger.info("performing correlation...")
    c_ave = np.array([(a[i] * a[j].conj()).mean() for i in range(nant) for j in range(i, nant)])
        
    return c_ave.reshape(-1, 1)

def sim_series_data(nant=36, nt=20, nave=1000000, srcflux=0.01):
    logger.info(f"creating simulated sigal from {nant} antennas, with {nave/1e6}M samples averaging, and {nt} integrations...")
    logger.info(f"source signal flux is {srcflux} unit...")
    
    c_data = []
    for i in range(nt):
        if i % 5 == 0:
            logger.info("*" * 80); logger.info(f"{i} integration..."); logger.info("*" * 80)
        
        c_data.append(sim_ant_data(nant, nave, srcflux))

    return c_data

def dump_data(c_data, fname):
    ### combine data together...
    c_ = np.concatenate(c_data, axis = 1)
    logger.info(f"saving simulated data to {fname}... final data shape is {c_.shape}")
    np.save(fname, c_)
    
    
def main(folder="./sim", nant=36, nt=100, nave=1000000, srcflux=0.01, prefix="sim"):
    if srcflux < 0.01: return None
    if not os.path.exists(folder): os.makedirs(folder)
        
    c_data =sim_series_data(nant, nt, nave, srcflux)
    fname = f"{prefix}_nant{nant}_nt{nt}_nave{nave/1e6:.0f}M_srcflux{srcflux:.2f}.npy"
    
    dump_data(c_data, f"{folder}/{fname}")
    
    
    
if __name__ == "__main__":
    nt = 200
    for srcflux in np.linspace(0.001, 0.009, 9):
        main(nt=nt, srcflux=srcflux)
        
    for srcflux in np.linspace(0.01, 0.1, 10):
        main(nt=nt, srcflux=srcflux)