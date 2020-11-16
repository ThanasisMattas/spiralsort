# io.py is part of SpiralSort
#
# SpiralSort is free software; you may redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. You should have received a copy of the GNU
# General Public License along with this program. If not, see
# <https://www.gnu.org/licenses/>.
#
# (C) 2020 Athanasios Mattas
# ======================================================================
"""Basic io functionality."""

import os

import numpy as np
import pandas as pd


def read_data_file(input_file):
    """reads the input file and stores it to a DataFrame
    (suported formats: csv, json)
    """
    read_file = {
        ".json": pd.read_json,
        ".csv": pd.read_csv,
    }

    _, input_format = os.path.splitext(input_file)

    with open(input_file, 'r') as f:
        nodes = read_file[input_format](f)      \
            .loc[:, ["node_id", 'x', 'y', 'z']] \
            .astype({"node_id": str,
                     'x': np.float32,
                     'y': np.float32,
                     'z': np.float32})
    return nodes


def output_file_path(input_file_path, output_format=None):
    """appends '_spiralsorted' to the input file name

    Args:
        input_file_path (string)
        output_format (stirng)   :  defaults to the format of the input

    Returns:
        output_file (string)
    """
    head, tail = os.path.splitext(input_file_path)

    if output_format is None:
        pass
    else:
        tail = "." + output_format

    output_file = head + "_spiralsorted" + tail
    return output_file


def animation_name(input_file_path):
    """creates the animation name at the input_file_path"""
    head, _ = os.path.splitext(input_file_path)
    ani_name = head + ".mp4"
    return ani_name


def write_output(sorted_nodes, output_file):
    """writes the sorted point-cloud into a file
    (suported formats: csv, json, xlsx)"""
    _, format = os.path.splitext(output_file)

    write_file = {
        ".json": sorted_nodes.to_json,
        ".csv": sorted_nodes.to_csv,
        ".xlsx": sorted_nodes.to_excel
    }

    write_file[format](output_file)
