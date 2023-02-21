"""
create python script for casa to export measurement sets files...
"""

import glob

sbid = "SB047619"
datapath = "/import/ada1/zwan4817/craco/commissioning"
workpath = "/import/ada1/zwan4817/craco/workdir/HW_compare"

export_scripts = []

for beam in range(36):
    # for beam in range(1, 3):
    uvfiles = glob.glob(f"{datapath}/{sbid}/{beam:0>2}/*/cal/*.uvfits")
    if len(uvfiles) != 1: 
        print("No/Multiple uvfits files found!")
        continue
    uvfile = uvfiles[0]
    msfile = uvfile + ".ms"

    export_scripts.append(f'''importuvfits(fitsfile="{uvfile}", vis="{msfile}")\n\n''')


with open(f"{workpath}/export_{sbid}_fits2ms.py", "w") as fp:
    fp.writelines(export_scripts)
