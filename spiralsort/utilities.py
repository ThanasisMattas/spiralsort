"""
info:
    file        :  utilities.py
    author      :  Thanasis Mattas
    license     :  GNU General Public License v3
    description :  Houses everything that has no obvious homeland

SpiralSort is free software; you may redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version. You should have received a copy of the GNU
General Public License along with this program. If not, see
<https://www.gnu.org/licenses/>.
"""


import os

import numpy as np
import pandas as pd

from spiralsort import config


def point_cloud_mock():
    """creates a mock point-cloud"""
    np.random.seed(2)
    num_nodes = config.NUM_NODES

    x = np.random.rand(num_nodes) - 0.5
    y = np.random.rand(num_nodes) - 0.5
    z = np.random.rand(num_nodes) - 0.5

    id_range = np.arange(num_nodes)
    max_length = len(str(num_nodes))
    node_id = ["N_" + (max_length - len(str(x))) * '0' + str(x)
               for x in id_range]

    cloud = pd.DataFrame(
        {
            "node_id": node_id,
            'x': x,
            'y': y,
            'z': z
        }
    )

    cloud["d_squared"] = cloud.x ** 2 + cloud.y ** 2 + cloud.z ** 2

    # exclude an inner sphere and pick the topmost node as the master
    # node, to assist visualization
    cloud = cloud[cloud.d_squared > 0.21]
    master_node_id = cloud.loc[cloud.z.idxmax(), "node_id"]

    # have a sneak peek
    # from spiralsort import spiralsort_post as ssp
    # ssp.quick_scatter(cloud.x, cloud.y, cloud.z)

    return cloud.loc[:, ["node_id", 'x', 'y', 'z']], master_node_id


def create_slices(nodes):
    """segments nodes into slices, not to work on the whole df

    [
        [0, 2000], [2000, 6000], [6000, 14000], [14000, 30000],
        [30000, 62000], [62000, 94000], [94000, 126000], ...
    ]
    """
    BASE = config.BASE
    CONST_WINDOW = config.CONST_WINDOW
    slice_bins = pd.DataFrame({"bins": [2000, 6000, 14000, 30000, np.inf],
                               "max_exponent": [1, 2, 3, 4, 5]})
    num_nodes = len(nodes.index)
    max_exponent = slice_bins.loc[slice_bins.bins.searchsorted(num_nodes),
                                  "max_exponent"]
    slices =                                                                  \
        [slice(BASE * (2 ** n - 1), BASE * (2 ** (n + 1) - 1))
         for n in range(max_exponent)]                                        \
        + [slice(start, start + CONST_WINDOW)
           for start in range(BASE * (2 ** (max_exponent) - 1) + CONST_WINDOW,
                              len(nodes.index),
                              CONST_WINDOW)]
    return slices


def calc_half_slice(slicing_obj):
    """calculates the half of the range of a slice"""
    half_slice = (slicing_obj.indices(int(1e100))[1]
                  - slicing_obj.indices(int(1e100))[0]) // 2
    return half_slice


def delete_images(directory):
    """deletes all images in a given directory (for debugging)"""
    files_list = [f for f in os.listdir(directory)]
    for f in files_list:
        if f.endswith(".png") or f.endswith(".jpg"):
            os.remove(os.path.join(directory, f))
