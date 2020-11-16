# core.py is part of SpiralSort
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
"""Usually does some spiralsorting stuff."""

import numpy as np
from numba import njit
import pandas as pd

from spiralsort import utils
from spiralsort.utils import time_this


def _start_offset(nodes, start_node_id):
    """offsets all nodes, so that start_node becomes the origin"""
    nodes = nodes.copy()
    start_index = nodes.loc[nodes.node_id == start_node_id].index[0]
    nodes.x = nodes.x - nodes.loc[start_index, "x"]
    nodes.y = nodes.y - nodes.loc[start_index, "y"]
    nodes.z = nodes.z - nodes.loc[start_index, "z"]
    return nodes


@njit(cache=True, nogil=True)
def _distances_from_node_numpy(nodes_x, nodes_y, nodes_z,
                               node_x, node_y, node_z):
    """numpy version of _distances_from_node for numba optinization"""
    distances = np.sqrt(
        (nodes_x - node_x) ** 2
        + (nodes_y - node_y) ** 2
        + (nodes_z - node_z) ** 2
    )
    return distances


def _distances_from_node(nodes, node):
    """evaluates the distances (norm L2) of nodes from node

    Args:
        nodes (df) :  the point-cloud
        node (df)  :  the reference node

    Returns:
        distances (array)
    """
    distances = _distances_from_node_numpy(
        nodes.x.values, nodes.y.values, nodes.z.values,
        node.x, node.y, node.z)
    return distances


def _prev_node_xy_gradient(prev_node):  # pragma: no cover
    """returns the angle of the prev_node vector from the 0x axis

    **Deprecated**

    this is the angle that the point-cloud will be rotated, in order to
    filter the counterclockwise side of the prev_node vector

    Args:
        prev_node (df) :  the last sorted node

    Returns:
        theta (float)  :  the gradient of the prev_node in radians
    """
    if ((prev_node.x < 0.001) and (prev_node.x > -0.001)
            and (prev_node.y >= 0)):
        theta = np.pi / 2
    elif ((prev_node.x < 0.001) and (prev_node.x > -0.001)
            and (prev_node.y < 0)):
        theta = - np.pi / 2
    elif prev_node.x >= 0.001:
        theta = np.arctan(prev_node.y / prev_node.x)
    # elif prev_node.iloc[0].x <= -0.001:
    else:
        theta = np.arctan(prev_node.y / prev_node.x) + np.pi
    return theta


@njit(cache=True, nogil=True)
def _prev_node_xy_gradient_numpy(prev_node_x, prev_node_y):
    """returns the angle of the prev_node vector from the 0x axis"""
    theta = np.angle(prev_node_x + prev_node_y * 1j)
    return theta


@njit(cache=True, nogil=True)
def _z_rotation_numpy(theta, nodes_x, nodes_y):
    """numpy implementation of _z_rotation for numba optimization"""
    rotated_x = np.cos(theta) * nodes_x + np.sin(theta) * nodes_y
    rotated_y = - np.sin(theta) * nodes_x + np.cos(theta) * nodes_y
    return rotated_x, rotated_y


def _z_rotation(nodes, prev_node):
    """2D rotation on z axis (linear transformation), such as prev_node
    will fall on the 0x axis

    transformation matrix:

        | cos(theta)  sin(theta)|
        |-sin(theta)  cos(theta)|

    theta > 0 : clockwise
    theta < 0 : counterclockwise

    Args:
        nodes (df)     :  the point-cloud
        prev_node (df) :  the node that will fall on the 0x axis

    Returns:
        rotated (df)   :  the point-cloud after the rotation
    """
    # theta = _prev_node_xy_gradient(prev_node)
    theta = _prev_node_xy_gradient_numpy(prev_node.x, prev_node.y)
    rotated = nodes.copy()
    rotated.x, rotated.y = _z_rotation_numpy(
        theta, nodes.x.values, nodes.y.values
    )
    return rotated


def _counterclockwise_filter(nodes, prev_node):
    """keeps only nodes from the counterclockwise side of the vector
    that starts at the start_node and ends at prev_node

    The goal is to force the algorithm to spiral counter-clockwise. This
    is achieved by rotating the cloud, so that the vector of prev_node
    falls on the (positive side of) x axis, and keeping only the nodes
    with positive y.

    Args:
        nodes (df)     :  the point-cloud
        prev_node (df) :  the last popped node

    Returns:
        (index)        :  the indexes of the filtered nodes
    """
    nodes_rotated = _z_rotation(nodes, prev_node)
    nodes_filtered_index = nodes_rotated[nodes_rotated.y >= 0].index

    # don't counterclockwise filter if prev_node is the start_node
    # or no nodes are left after the filter
    if len(nodes_filtered_index):
        return nodes_filtered_index
    else:
        return nodes.index


def _cost(nodes, prev_node):
    """cost = |node - start| + |node - prev_node|

    Args:
        nodes (df)         : the point-cloud
        prev_node (df)     : the node from which to calculate the cost

    Returns:
        cost_ (series)     : the cost column, to be inserted to the df
    """
    cost = nodes["|node - start|"].add(
        _distances_from_node(nodes, prev_node)
    )
    return cost


def _cost_sort(nodes, prev_node, ignore_index=True):
    """sorts the nodes by cost from prev_node

    cost = |node - start| + |node - prev_node|

    Args:
        nodes (df)          : the point-cloud
        prev_node (df)      : the node from which to calculate the cost
        ignore_index (bool) : whether to keep or reset the old index
                              (default True)

    Returns:
        nodes (df)          : the point-cloud, cost-sorted
    """
    with pd.option_context("mode.chained_assignment", None):
        nodes.loc[:, "cost"] = _cost(nodes, prev_node)
        nodes.sort_values("cost", inplace=True, kind="mergesort",
                          na_position="first", ignore_index=ignore_index)
    return nodes


def _pop_next_node(nodes, prev_node):
    """nodewise step of the algorithm

    1. evaluate cost
    2. pop the node with the min cost

    Args:
        nodes (df)          : the point-cloud
        prev_node (df)      : the last popped node

    Returns:
        nodes (df)          : the point-cloud, without the currently
                              popped node
        next_node_id (str)  : to be appended to the node_ids list
        next_node (series)  : the currently popped node
    """
    nodes_filtered = nodes.loc[_counterclockwise_filter(nodes, prev_node)]

    # 1. evaluate cost
    nodes_filtered.loc[:, "cost"] = _cost(nodes_filtered, prev_node)

    # 2. pop the next_node
    next_node_idx = nodes_filtered["cost"].idxmin()
    next_node = nodes_filtered.loc[next_node_idx]
    next_node_id = next_node.node_id
    nodes = nodes[~nodes.index.isin([next_node.name])]
    return nodes, next_node_id, next_node


def _spiral_stride(nodes,
                   node_ids,
                   prev_node,
                   spiral_window,
                   stride):
    """moves one stride inside the spiral_window, iteretively popping
    nodes with respect to the min cost

    Args:
        nodes (df)          :  the nodes batch that the algorithm is
                               woring on
        node_ids (list)     :  the so far spiral-sorted list of node_ids
        prev_node (df)      :  the last sorted (popped) node
        spiral_window (int) :  the window of nodes that the algorithm
                               will iteretively search for the next node
        stride (int)        :  the number of nodes to be sorted, before
                               moving to the next spiral_window

    Returns:
        nodes (df)          :  the initially nodes batch, without the
                               nodes popped at this stride
        node_ids (list)     :  the so far spiral-sorted list of node_ids
                               updated with the nodes popped at this
                               stride
        prev_node (df)      :  the last popped node at this stride
    """
    # keep a temp node_ids list, not to search through the whole list
    node_ids_inner = []

    # for the first 1000 nodes dont filter the counterclockwise side
    # nodes, to prevent from oscilating on a lobe (half spherical disk)
    if len(node_ids) <= 1000:
        nodes_filtered = nodes[slice(0, spiral_window)]
    else:
        nodes_filtered = nodes.loc[_counterclockwise_filter(nodes, prev_node)]
        nodes_filtered = _cost_sort(nodes, prev_node)
        nodes_filtered = nodes_filtered[slice(0, spiral_window)]

    iters = min(stride, len(nodes_filtered.index))

    for _ in range(iters):
        nodes_filtered, prev_node_id, prev_node = _pop_next_node(
            nodes_filtered,
            prev_node
        )
        node_ids_inner.append(prev_node_id)

    # drop node_ids_inner from nodes remainder
    nodes = nodes[~nodes.node_id.isin(node_ids_inner)]

    # update node_ids
    node_ids += node_ids_inner

    return nodes, node_ids, prev_node


@time_this
def spiralsorted(nodes_input, start_node_id):
    """SpiralSorts the point-cloud, starting from the start_node.

    The SpiralSort algorithm:
    1. Sort the point cloud with respect to the distance from the start
       node
    2. Segment it into slices and take the first slice
    3. Take a SPIRAL_WINDOW (slice further)
       Spiral windows for the 1st slice consist of 400 nodes, starting
       from the last sorted node (the start_node for the 1st window)
    4. Iteretively pop 15 nodes (a STRIDE), by the minimum cost. Namely,
       a SPIRAL_WINDOW is sliced to spiralsort a STRIDE of nodes, before
       moving to the next SPIRAL_WINDOW.
       (cost = |node - start_node| + |node - prev_node|)
       At each iterative step, a filter is applied, keeping only nodes
       from the counterclockwise side of the vector that starts from the
       start node and ends at the previous node, in order to force the
       algorithm to move on a constant rotating direction.
    5. Take the next SPIRAL_WINDOW and pop the next STRIDE.
    6. Continue until the remainder of the nodes reaches the size of the
       half slice (1000 nodes for the 1st slice).
    7. Merge the remaining nodes with the next slice
       This overlap of the slices ensures that there is a continuity
       while selecting the next nodes, when the algorithm reaches the
       last nodes of the slice.
    8. For the next slices, while moving away from the start_node, the
       SPIRAL_WINDOW is selected differently. Specifically, before each
       STRIDE, the counterclockwise filter is applied, then the
       remaining nodes are cost-sorted (with respect to their cost) from
       the last spiralsorted node and, finally, a SPIRAL_WINDOW is
       sliced, to start the iterative spiralsorting of the nodes in the
       next STRIDE.
    9. Keep moving by SPIRAL_WINDOWs, counterclockwise
       filtering at each stride, popping STRIDEs of nodes until the half
       slice thresshold.
    10. Upon reaching the last slice, remove the *half_slice* threshold,
       to pop all the remaining nodes.

    Args:
        nodes (df)           :  the point-cloud
        start_node_id (str)  :  the node where spiralsorting starts

    Returns:
        nodes_sorted (df)    :  the spiralsorted point-cloud
    """
    # first, check if the node_ids are unique
    utils.check_duplicated_ids(nodes_input)

    # final sequence of ids, used to sort the final dataframe,
    # initialized with the start node
    node_ids = [start_node_id]

    # make start_node the origin of the axes
    nodes = _start_offset(nodes_input, start_node_id)

    # initialize previous node with the start node (series)
    start_node = nodes.loc[nodes["node_id"] == start_node_id]
    prev_node = start_node.iloc[0]

    # drop start node
    nodes.drop(start_node.index, inplace=True)

    # distance of all nodes from the start node
    nodes["|node - start|"] = _distances_from_node(nodes, prev_node)

    # distance-sort from start_node
    nodes.sort_values("|node - start|", inplace=True, kind="mergesort",
                      ignore_index=True)

    # segment nodes into slices, not to work on the whole df
    # [
    #     [0, 2000], [2000, 6000], [6000, 14000], [14000, 30000],
    #     [30000, 62000], [62000, 94000], [94000, 126000], ...
    # ]
    slices = utils.create_slices(nodes)

    # number of nodes anti-clockwise filtered and cost_sorted from prev
    # node, in order to iteretively pop the next nodes in the STRIDE
    SPIRAL_WINDOW = 400
    STRIDE = 15

    # this is the container that the sorting algorithm will work with
    remaining_nodes = pd.DataFrame(columns=nodes.columns)

    for idx, slicing_obj in enumerate(slices):

        # moving to more distant slices, spiral_window gets bigger, as
        # the nodes are more spread out away from the start node
        spiral_window = int(SPIRAL_WINDOW + 100 * idx)

        # Concat with the remainder of the nodes (which is the half of
        # the previous slice), in order to have continuity.
        # (For example, previous to last node will only have the last
        # remaining node to find the next cost-sorted node, which is
        # not correct, because there are other candidates, not included
        # in the current slice.)
        remaining_nodes = pd.concat([remaining_nodes, nodes[slicing_obj]])

        half_slice = utils.calc_half_slice(slicing_obj)

        # leave half_slice remaining nodes to merge with the next slice
        # except from the last slice
        if (slicing_obj in slices[: -1]) and (len(slices) > 1):
            strides = (len(remaining_nodes.index) - half_slice) // STRIDE
        else:
            strides = - (-len(remaining_nodes.index) // STRIDE)

        for _ in range(strides):
            remaining_nodes, node_ids, prev_node = _spiral_stride(
                remaining_nodes,
                node_ids,
                prev_node,
                spiral_window,
                STRIDE
            )

    # return start node to nodes
    nodes = pd.concat([start_node, nodes])
    # reorder nodes with respect to the spiral-sorted node_ids
    node_ids = pd.DataFrame({"node_id": node_ids})
    nodes_sorted = node_ids.merge(nodes_input, on="node_id")      \
                           .loc[:, ["node_id", 'x', 'y', 'z']]    \
                           .reset_index(drop=True, inplace=False)

    return nodes_sorted
