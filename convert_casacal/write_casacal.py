from casacore import tables
import numpy as np
import pickle

def load_pickle_data(fname):
    with open(fname, "rb") as fp:
        data = pickle.load(fp)
    return data

def make_tabdesc(coldesc):
    """
    make table description based on the json file
    """
    coldesc = [tables.makecoldesc(col, coldesc[col]) for col in coldesc]
    return tables.maketabdesc(coldesc)

def _work_refant(bp):
    bp = bp[0]
    nant, nchan, npol = bp.shape
    for iant in range(nant):
        antdata = bp[iant, :, (0, 3)]
        antdata_degree = np.angle(antdata, deg=True)
        if (abs(antdata_degree) > 0.1).sum() == 0:
            return iant
    raise ValueError("no reference antenna found...")
#     for iant in range(nant):
#         antdata = bp[iant, :, (0, 3)]
#         if np.isnan(antdata).sum() == 0:
#             return iant
#     raise ValueError("no reference antenna found...")

def make_caltab(calpath, bp, refant=None, datapath="./data"):
    _, nant, nchan, npol = bp.shape
    
    coldesc = load_pickle_data(f"{datapath}/CAL_coldesc.pkl")
    tb = make_tabdesc(coldesc)
    tabpath = "{}".format(calpath)
    tab = tables.table(tabpath, tb, nrow=nant) # 36 antennas
    
    ###
    if refant is None:
        refant = _work_refant(bp) # bp should be a 4d array
    
    # columns
    tab.putcol("TIME", np.zeros(nant, dtype=int))
    tab.putcol("FIELD_ID", np.zeros(nant, dtype=int)) # only one source
    tab.putcol("SPECTRAL_WINDOW_ID", np.zeros(nant, dtype=int)) # again, only one spectral window
    tab.putcol("ANTENNA1", np.arange(nant, dtype=int))
    tab.putcol("ANTENNA2", np.ones(nant, dtype=int) * refant)
    tab.putcol("INTERVAL", np.zeros(nant))
    tab.putcol("OBSERVATION_ID", np.zeros(nant, dtype=int))
    tab.putcol("FLAG", np.zeros((nant, nchan, 2), dtype=bool)) # assume to flag here...
    tab.putcol("SNR", np.ones((nant, nchan, 2), ) * 10.)
    tab.putcol("PARAMERR", np.ones((nant, nchan, 2)))
    
    ### work out the parameter
    tab.putcol("CPARAM", bp[..., [0, 3]][0])
    tab.close()

def make_spwtab(calpath, freqs, datapath="./data"):
    ### work out frequencies...
    nchan = freqs.shape[0]
    chan_width = np.mean(freqs[1:] - freqs[:-1])
    total_bandwidth = chan_width * nchan
    
    coldesc = load_pickle_data(f"{datapath}/SPW_coldesc.pkl")
    coldata = load_pickle_data(f"{datapath}/SPW_coldata.pkl")
    ### make table
    tb = make_tabdesc(coldesc)
    
    tabpath = "{}/SPECTRAL_WINDOW".format(calpath)
    tab = tables.table(tabpath, tb, nrow=1) # for 36 antenna...
    for col in coldata:
        tab.putcol(col, coldata[col])
    
    ### put rows deleted...
    tab.putcol("CHAN_FREQ", np.array([freqs]))
    tab.putcol("REF_FREQUENCY", np.array([freqs[0]]))
    tab.putcol("CHAN_WIDTH", np.ones((1, nchan)) * chan_width)
    tab.putcol("EFFECTIVE_BW", np.ones((1, nchan)) * chan_width)
    tab.putcol("RESOLUTION", np.array([freqs]))
    tab.putcol("NUM_CHAN", np.array([nchan]))
    tab.putcol("TOTAL_BANDWIDTH", np.array([total_bandwidth]))
    
    tab.close()

def make_fietab(calpath, datapath="./data"):
    ### load data
    coldesc = load_pickle_data(f"{datapath}/FIELD_coldesc.pkl")
    coldata = load_pickle_data(f"{datapath}/FIELD_coldata.pkl")
    ### make table
    tb = make_tabdesc(coldesc)
    
    tabpath = "{}/FIELD".format(calpath)
    tab = tables.table(tabpath, tb, nrow=1) # for 36 antenna...
    for col in coldata:
        tab.putcol(col, coldata[col])
    tab.close()

def make_histab(calpath, datapath="./data"):
    ### load data
    coldesc = load_pickle_data(f"{datapath}/HISTORY_coldesc.pkl")
#     coldata = load_pickle_data("./data/HISTORY_coldata.pkl")
    ### make table
    tb = make_tabdesc(coldesc)
    
    tabpath = "{}/HISTORY".format(calpath)
    tab = tables.table(tabpath, tb, nrow=0) # for 36 antenna...
    tab.close()

def make_obstab(calpath, datapath="./data"):
    ### load data
    coldesc = load_pickle_data(f"{datapath}/OBS_coldesc.pkl")
    coldata = load_pickle_data(f"{datapath}/OBS_coldata.pkl")
    ### make table
    tb = make_tabdesc(coldesc)
    
    tabpath = "{}/OBSERVATION".format(calpath)
    tab = tables.table(tabpath, tb, nrow=1) # for 36 antenna...
    
    ### put data in it...
    for col in coldata:
        tab.putcol(col, coldata[col])
    tab.close()

def make_anttab(calpath, datapath="./data"):
    ### load data
    coldesc = load_pickle_data(f"{datapath}/ANTENNA_coldesc.pkl")
    coldata = load_pickle_data(f"{datapath}/ANTENNA_coldata.pkl")
    ### make table
    tb = make_tabdesc(coldesc)
    
    tabpath = "{}/ANTENNA".format(calpath)
    tab = tables.table(tabpath, tb, nrow=36) # for 36 antenna...
    
    ### put data in it...
    for col in coldata:
        tab.putcol(col, coldata[col])
    tab.close()

def make_full_casabp(calpath, bp, freqs, datapath="./data", refant=None):
    make_caltab(calpath, bp, refant=refant, datapath=datapath)
    make_spwtab(calpath, freqs, datapath=datapath)
    make_fietab(calpath, datapath=datapath)
    make_histab(calpath, datapath=datapath)
    make_obstab(calpath, datapath=datapath)
    make_anttab(calpath, datapath=datapath)

    ### add keywords
    t = tables.table(calpath, readonly=False)
    t.putkeyword("ParType", "Complex")
    # t.putkeyword("MSName", "cal.B0")
    t.putkeyword("VisCal", "B Jones")
    t.putkeyword("PolBasis", "unknown")
    t.putkeyword("OBSERVATION", f"Table: {calpath}/OBSERVATION")
    t.putkeyword("ANTENNA", f"Table: {calpath}/ANTENNA")
    t.putkeyword("FIELD", f"Table: {calpath}/FIELD")
    t.putkeyword("SPECTRAL_WINDOW", f"Table: {calpath}/SPECTRAL_WINDOW")
    t.putkeyword("HISTORY", f"Table: {calpath}/HISTORY")
    t.flush()

    ### add info...
    t.putinfo({
        "type": "Calibration",
        "subType": "B Jones",
        "readme": "",
    })

    t.close()
