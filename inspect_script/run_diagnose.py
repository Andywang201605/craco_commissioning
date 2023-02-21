import glob
import numpy as np
from compare_craco_askaphw import *


def find_craco_ms(sbid, beam):
    beam = f"{beam:0>2}"
    mspath = f"/import/ada1/zwan4817/craco/commissioning/{sbid}/{beam}/*/cal/*.uvfits.ms"
    msfile = glob.glob(mspath)[0]
    
    return msfile

def find_hw_ms(sbid, beam):
    mspath = f"/import/ada1/zwan4817/craco/commissioning/{sbid}/askap-hardware/1934/*.BEAM{beam}.*.ms"
    msfile = glob.glob(mspath)[0]
    
    return msfile

if __name__ == "__main__":
    
    SBID = "SB047619"
    
    filehandler = logging.FileHandler("run_diagnose.log", "w")
    filehandler.setLevel(logging.DEBUG)
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)
    
    
    for beam in range(36):
        craco_tab_path = find_craco_ms(SBID, beam)
        hw_tab_path = find_hw_ms(SBID, beam)
        
        try:
        
            cracodata, hwdata, cracouvw, hwuvw, central_freq, central_time, craco_bl, hw_bl = load_measurement_sets(
                craco_tab_path = craco_tab_path,
                hw_tab_path = hw_tab_path
            )
            
            logger.info("Saving data to `.npz` file...")
            logger.info(f"cracouvw shape: {cracouvw.shape}, hwuvw shape: {hwuvw.shape}...")
            
            np.savez(
                f"./{SBID}/{beam:0>2}/loaded_data.npz",
                cracodata = cracodata, hwdata = hwdata,
                cracouvw = cracouvw, hwuvw = hwuvw,
                central_freq = central_freq, central_time = central_time,
                craco_bl = craco_bl, hw_bl = hw_bl,
            )
            
        except:
            logger.critical(f"Error occurs for BEAM{beam} data... Please check later...")
            
        
        
        
