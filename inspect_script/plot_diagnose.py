import glob
import numpy as np
from compare_craco_askaphw import *

def plot_uvw_difference(craco_hw_uvw_diff, manual_bl_sel=None, title=None):
    if manual_bl_sel is not None:
        craco_hw_uvw_diff_blsel = craco_hw_uvw_diff[:, manual_bl_sel, :]
    else:
        craco_hw_uvw_diff_blsel = craco_hw_uvw_diff[:, :, :]
        
    uvw_name = ["UU", "VV", "WW"]
        
    fig = plt.figure(figsize=(18, 6))
    
    for idx, name in enumerate(uvw_name):
        ax = fig.add_subplot(1, 3, idx+1)
        ax.plot(craco_hw_uvw_diff_blsel[:, :, idx])
        ax.set_ylim(-100, 100)
        ax.set_xlabel("ASKAP Integration")
        ax.set_ylabel(f"{uvw_name[idx]} Difference (m)")
        
        if idx == 1 and title is not None:
            ax.set_title(title)
        
    return fig

def load_summarized_data(SBID, beam):
    ms_data = np.load(f"../workdir/HW_compare/{SBID}/{beam:0>2}/loaded_data.npz")
    
    cracodata = ms_data["cracodata"]
    hwdata = ms_data["hwdata"]
    craco_bl = ms_data["craco_bl"]
    hw_bl = ms_data["hw_bl"]
    cracouvw = ms_data["cracouvw"]
    hwuvw = ms_data["hwuvw"]
    hwuvw = hwuvw[:, find_hwbl_overlap(craco_bl, hw_bl), :]
    
    return cracodata, hwdata, craco_bl, hw_bl, cracouvw, hwuvw

def plot_main(SBID, beam, nant=30, plotwaterfall=True, plotuvw=True):
    ms_data = np.load(f"./{SBID}/{beam:0>2}/loaded_data.npz")
    
    cracodata = ms_data["cracodata"]
    hwdata = ms_data["hwdata"]
    craco_bl = ms_data["craco_bl"]
    hw_bl = ms_data["hw_bl"]
    cracouvw = ms_data["cracouvw"]
    hwuvw = ms_data["hwuvw"]
    
#     manual_bl_sel = None
############### CHANGE HERE IF YOU WANNA CHANGE FLAGGING ################
    manual_bl_sel = (~find_ant_bl(craco_bl, 29)) & (find_crosscor(craco_bl))
    #                    # flag antenna 29            # only include cross-correlation
############### CHANGE HERE IF YOU WANNA CHANGE FLAGGING ################

    if plotwaterfall:
    
        fig, ax = plt.subplots(nant, nant, figsize=(nant, nant), sharex=True, sharey=True, dpi=100)
        plt.subplots_adjust(wspace=0, hspace=0)

        for ant1 in range(1, nant+1):
            for ant2 in range(1, nant+1):

                if ant1 == 1:
                    ax[ant2-1, ant1-1].set_ylabel(f"ak{ant2}")
                if ant2 == nant:
                    ax[ant2-1, ant1-1].set_xlabel(f"ak{ant1}")

                if ant1 >= ant2: continue

                waterfall = waterfall_compare(cracodata, hwdata, craco_bl, hw_bl, ant1, ant2, metrics="phase")

                plot_waterfall_compare(waterfall, ax[ant2-1, ant1-1], metrics="phase")


                ax[ant2-1, ant1-1].set_xticks([])
                ax[ant2-1, ant1-1].set_yticks([])

        fig.savefig(f"./{SBID}/{beam:0>2}/hw_craco_phase_beam{beam:0>2}.pdf", bbox_inches="tight")
        plt.close()


        fig, ax = plt.subplots(nant, nant, figsize=(nant, nant), sharex=True, sharey=True, dpi=100)
        plt.subplots_adjust(wspace=0, hspace=0)

        for ant1 in range(1, nant+1):
            for ant2 in range(1, nant+1):

                if ant1 == 1:
                    ax[ant2-1, ant1-1].set_ylabel(f"ak{ant2}")
                if ant2 == nant:
                    ax[ant2-1, ant1-1].set_xlabel(f"ak{ant1}")

                if ant1 >= ant2: continue

                waterfall = waterfall_compare(cracodata, hwdata, craco_bl, hw_bl, ant1, ant2, metrics="amp")

                plot_waterfall_compare(waterfall, ax[ant2-1, ant1-1], metrics="amp")


                ax[ant2-1, ant1-1].set_xticks([])
                ax[ant2-1, ant1-1].set_yticks([])

        fig.savefig(f"./{SBID}/{beam:0>2}/hw_craco_phase_amp{beam:0>2}.pdf", bbox_inches="tight")
        plt.close()
        
    if plotuvw:

        logger.info(f"plotting uvw differences for beam{beam}...")

        hwuvw = hwuvw[:, find_hwbl_overlap(craco_bl, hw_bl), :]
        craco_hw_uvw_diff = cracouvw - hwuvw
        fig = plot_uvw_difference(craco_hw_uvw_diff, manual_bl_sel, f"BEAM{beam:0>2}")

        fig.savefig(f"./{SBID}/{beam:0>2}/hw_craco_uvw_diff{beam:0>2}.pdf", bbox_inches="tight")
        plt.close()
    
    
if __name__ == "__main__":
    SBID = "SB047619"
    
    
    filehandler = logging.FileHandler("run_diagnose.log", "w")
    filehandler.setLevel(logging.WARNING)
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)
    
    for beam in range(36):
        try:
            plot_main(SBID, beam)
        except:
            logger.critical(f"Cannot plot for beam{beam}... Please check later...")

