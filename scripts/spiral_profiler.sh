#!/bin/bash
# script: spiral_profiler.sh
# --------------------------
# This script uses the line-profiler to produce a txt file with profilings
# of the algorithm. You need to decorate with @profile each function that you
# want to profile.

export PYTHONPATH="${PYTHONPATH}:.."
kernprof -lv ../spiralsort/__main__.py \
    ../examples/data_examples/point_cloud_example.csv N_4004 \
    > profiling.txt
