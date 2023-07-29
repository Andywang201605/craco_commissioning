#!/bin/bash
sbid=$1

./extract_bpscan.py -sbid $sbid
./bpscan_cal.py -sbid $sbid