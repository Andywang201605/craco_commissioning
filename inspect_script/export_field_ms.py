import glob
import sys

from casacore import tables

args = sys.argv

input_folder = sys.argv[1]
output_folder = sys.argv[2]
suffix = sys.argv[3]

def get_msfiles(stem, oflag):
    mslist = {}

    # Account for override
    if oflag:
        msfiles = [stem + '.ms']
    else:
        msfiles = glob.glob('%s*.ms' % (stem))

    # Construct the list based on the header information
    for ms in msfiles:
        t = tables.table("%s" % ms, ack=False)
        beam = t.getcol("FEED1")[0]
        t.close()

        t = tables.table("%s::SPECTRAL_WINDOW" % ms, ack=False)
        freq = int('%.0f' % (t.getcol("REF_FREQUENCY")[0]/1e6))
        t.close()

        # Append to the mslist dictionary for later processing
        if freq not in mslist.keys():
            mslist[freq] = {beam : ms}
        else:
            mslist[freq][beam] = ms

    return mslist

def create_casa_script(mslist, output_folder, suffix=""):

    casa_scripts = []

    for freq in mslist:
        freqlist = mslist[freq]

        for beam in freqlist:
            input_ms = freqlist[beam]
            input_ms_fname = input_ms.split("/")[-1]
            output_ms_fname = input_ms_fname.replace(".ms", f".{freq}MHz.BEAM{beam}.{suffix}.ms")
            output_ms = f"{output_folder}/{output_ms_fname}"

            ms_split_script = f"""split(vis="{input_ms}", outputvis="{output_ms}", field="{beam}", datacolumn="all")\n"""
            casa_scripts.append(ms_split_script)

    with open(f"{output_folder}/split_askaphw_beam.py", "w") as fp:
        fp.writelines(casa_scripts)

if __name__ == "__main__":
    mslist = get_msfiles(input_folder, False)
    create_casa_script(mslist, output_folder, suffix)
