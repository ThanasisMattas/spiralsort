# spiralsort_post.py is part of SpiralSort
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
"""Handles the post-processing"""

import os
import shutil

import matplotlib.pyplot as plt

from spiralsort import config, core, io, utils
from spiralsort.utils import time_this


def quick_scatter(x, y, z):
    fig = plt.figure()
    sub = fig.add_subplot(111, projection="3d")
    sub.scatter(x, y, z)
    plt.show()


def _spiral_sort_frame(current_node_idx,
                       current_node_id,
                       next_node,
                       stride_nodes,
                       counterclock_filtered,
                       spiral_slice,
                       nodes_rest,
                       nodes_next_slices,
                       stride,
                       spiral_window,
                       effective_slice,
                       half_slice,
                       num_nodes_next_slices,
                       output_dir,
                       show=False):
    """plot a frame, as a 3D scatter, of the spiral-sort algorithm"""
    fig = plt.figure()
    sub = fig.add_subplot(111, projection="3d")
    # rotate the frame, to aid visualization of the poin-cloud
    sub.view_init(40, 30 + current_node_idx / 4)
    sub.use_sticky_edges = False
    # sub.margins(x=0, y=-0.45)
    plt.tight_layout()
    # plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
    plt.subplots_adjust(top=0.85)
    plt.axis("off")
    # sub.set_xlabel('x')
    # sub.set_ylabel('y')
    # sub.set_zlabel('z')
    # fig.gca().set_xlim([-1, 1])
    # fig.gca().set_ylim([-1, 1])
    fig.gca().set_zlim([-0.6, 0.6])

    # color labels:
    # b: blue     g: green    r: red     m: magenta
    # w: white    k: black    c: cyan    y: yellow

    # next_node
    sub.scatter(next_node['x'],
                next_node['y'],
                next_node['z'],
                c='r', marker='x', s=150, label="next_node")
    # stride_nodes
    if stride_nodes is not None:
        sub.scatter(stride_nodes.x,
                    stride_nodes.y,
                    stride_nodes.z,
                    c='k', marker='*', s=15, alpha=1,
                    label="stride ({})".format(stride))
    # spiral_slice
    if spiral_slice is not None:
        sub.scatter(spiral_slice.x,
                    spiral_slice.y,
                    spiral_slice.z,
                    c='y', s=15,
                    label="spiral window ({})".format(spiral_window))
    # counterclock_filtered
    if counterclock_filtered is not None:
        sub.scatter(counterclock_filtered.x,
                    counterclock_filtered.y,
                    counterclock_filtered.z,
                    c='g', s=15, label="counterclockwise filter")
    # nodes_rest
    if nodes_rest is not None:
        sub.scatter(nodes_rest.x,
                    nodes_rest.y,
                    nodes_rest.z,
                    s=10, label="nodes slice ({0} + {1})".format(
                        effective_slice, half_slice
                    ))
    # nodes_next_slices
    if nodes_next_slices is not None:
        sub.scatter(nodes_next_slices.x,
                    nodes_next_slices.y,
                    nodes_next_slices.z,
                    c='lightgray', marker='D', s=4,
                    label="not in current slice ({})".format(
                        num_nodes_next_slices
                    ))

    # legend location:
    # best, upper right, upper left, lower left, lower right, right,
    #    0,           1,          2,          3,           4,     5,
    # center left, center right, lower center, upper center, center
    #           6,            7,            8,            9,     10
    sub.legend(fontsize=8, loc=2)
    plt.title("node #{0} (ID: {1})".format(current_node_idx, current_node_id))
    # sub.title.set_position([0.5, 1.5])

    if show:
        plt.show()
    else:
        zeros_left = (5 - len(str(current_node_idx))) * '0'
        image_name = zeros_left + str(current_node_idx)
        os.makedirs(output_dir, exist_ok=True)
        plt.savefig(output_dir + image_name + ".jpg", dpi=200)
        plt.close()


def _plot_spiralsort(nodes_sorted, start_node_id, output_dir):
    """saves an image for each step of the spiralsorting algorithm"""
    nodes_sorted.reset_index(drop=True, inplace=True)
    start_node = \
        nodes_sorted.loc[nodes_sorted["node_id"] == start_node_id].squeeze()
    nodes_sorted["|node - start|"] = \
        core._distances_from_node(nodes_sorted, start_node)

    SPIRAL_WINDOW = config.SPIRAL_WINDOW
    STRIDE = config.STRIDE

    # [
    #     [0, 2000], [2000, 6000], [6000, 14000], [14000, 30000],
    #     [30000, 62000], [62000, 94000], [94000, 126000], ...
    # ]
    slices = utils.create_slices(nodes_sorted)

    # nodes are distance-sorted from the start_node, but the indexes
    # are not sorted
    nodes_raw = core._cost_sort(nodes_sorted.copy(),
                                nodes_sorted.iloc[0],
                                ignore_index=False)

    # - nodes_sorted will  be used for iterating through the next
    #   nodes and saving the prev_node (perfect division with STRIDE)
    #
    # - nodes_raw will be used for marking the SPIRAL_WINDOW nodes, as
    #   the algorithm sees it

    # node iterator
    i = 0
    # stride front, when a perfect division with STRIDE occurs
    prev_perfect_division = 0
    # the last popped node, from which the next stide
    # will be defined
    stride_node_idx = 0
    # the remainder of the stride is sliced from the stride using
    # <% STRIDE>, but when a new slice is merged, it has to be
    # calibrated, subtracting the nodes_popped length
    new_slice_calibrator = 0
    # the remainder of nodes, which the sorting algorithm is working on
    nodes_remainder = 0

    for slice_index, slicing_obj in enumerate(slices):

        new_slice_just_been_merged = True
        spiral_window = SPIRAL_WINDOW + slice_index * 100
        half_slice = utils.calc_half_slice(slicing_obj)
        slice_last_node_idx = slicing_obj.indices(int(1e100))[1]

        # nodes_next_slices
        nodes_next_slices = nodes_sorted.loc[slice_last_node_idx:]
        num_nodes_next_slices = len(nodes_next_slices.index)

        if (slicing_obj is not slices[-1]) and (len(slices) != 1):
            # the last popped node, before the remainder of the nodes
            # will be merged with the next slice
            effective_last_node_idx = slice_last_node_idx - half_slice
            effective_slice = nodes_remainder + half_slice
            nodes_remainder = half_slice
        else:
            effective_last_node_idx = nodes_sorted.iloc[-1].name
            effective_slice = nodes_remainder + 2 * half_slice
            half_slice = 0
            node_remainder = None

        while i < effective_last_node_idx:

            # - remaining_nodes: the slice of all the nodes that the
            #                    algorithm is working on.
            # - spiral_slice   : the slice of the remaining_nodes that
            #                    nodes are iteretively popping out (the
            #                    algorithm isolates this window after
            #                    making an initial sorting to the slice,
            #                    when it makes a certain stride, not to
            #                    work on the whole slice)
            # - nodes_rest     : the rest of the remaining nodes
            # remaining_nodes = spiral_slice + nodes_rest

            # nodes_popped
            nodes_popped = nodes_sorted[: i + 1]
            current_node_id = nodes_sorted.loc[i, "node_id"]

            # remaining_nodes
            remaining_nodes = nodes_raw.iloc[: slice_last_node_idx]
            remaining_nodes = remaining_nodes.loc[
                ~remaining_nodes.node_id.isin(nodes_popped.node_id)
            ]

            # stride front, when a perfect division with STRIDE occurs
            perfect_division = (i - new_slice_calibrator) // STRIDE

            # only for the 1st slice (don't counterclockwise filter)
            if slice_index == 0:
                # when a perfect_division occurs, the algorithm moves to
                # the next SPIRAL_WINDOW to make the next STRIDE
                if prev_perfect_division < perfect_division:
                    # the nodes of each stride lie at the same window,
                    # which starts at the last popped node
                    # (spiral_w_ref_node)
                    stride_node_idx += STRIDE
                    prev_perfect_division = perfect_division

                # full_spiral_slice
                full_spiral_slice = remaining_nodes.iloc[: spiral_window]

            # rest of the slices
            else:
                # calibrate stride_node_idx to last popped node (i) and
                # prev_perfect_division to (current) perfect_division
                if new_slice_just_been_merged:
                    stride_node_idx = i
                    new_slice_calibrator = len(nodes_popped.index) - 1
                    perfect_division = (i - new_slice_calibrator) // STRIDE
                    prev_perfect_division = perfect_division
                    new_slice_just_been_merged = False
                if prev_perfect_division < perfect_division:
                    stride_node_idx += STRIDE
                    prev_perfect_division = perfect_division

                # full_spiral_slice
                counterclock_filtered = remaining_nodes.loc[
                    core._counterclockwise_filter(
                        remaining_nodes,
                        nodes_sorted.loc[stride_node_idx]
                    )
                ]
                cost_sorted = core._cost_sort(
                    counterclock_filtered,
                    nodes_sorted.loc[stride_node_idx]
                )
                full_spiral_slice = cost_sorted.iloc[: spiral_window]

            # full_stride_nodes
            full_stride = nodes_sorted[
                stride_node_idx + 1: stride_node_idx + 1 + STRIDE
            ]

            # stride_nodes
            stride_nodes = full_stride[(i - new_slice_calibrator) % 15:]
            # stride_nodes = remaining_nodes.loc[
            #     remaining_nodes.node_id.isin(full_stride.loc[i:].node_id)
            # ]

            # full_spiral_slice (remove full_stride_nodes)
            full_spiral_slice = full_spiral_slice.loc[
                ~full_spiral_slice.node_id.isin(full_stride.node_id)
            ]

            # counterclock_filtered
            counterclock_filtered = full_spiral_slice.loc[
                core._counterclockwise_filter(
                    full_spiral_slice,
                    nodes_sorted.loc[i]
                )
            ]

            # spiral_slice
            spiral_slice = full_spiral_slice.loc[
                ~full_spiral_slice.node_id.isin(counterclock_filtered.node_id)
            ]

            # nodes_rest
            nodes_rest = remaining_nodes.loc[
                ~remaining_nodes.node_id.isin(full_spiral_slice.node_id)
            ]
            nodes_rest = nodes_rest.loc[
                ~nodes_rest.node_id.isin(full_stride.node_id)
            ]

            # 0. next_node
            # 1. stride (from nodes_sorted)
            # 2. counterclock_filtered
            # 3. spiral_slice
            # 4. nodes_rest (rest to remaining_nodes)
            _spiral_sort_frame(current_node_idx=i,
                               current_node_id=current_node_id,
                               next_node=nodes_sorted.iloc[i],
                               stride_nodes=stride_nodes,
                               counterclock_filtered=counterclock_filtered,
                               spiral_slice=spiral_slice,
                               nodes_rest=nodes_rest,
                               nodes_next_slices=nodes_next_slices,
                               stride=STRIDE,
                               spiral_window=spiral_window,
                               effective_slice=effective_slice,
                               half_slice=half_slice,
                               num_nodes_next_slices=num_nodes_next_slices,
                               output_dir=output_dir,
                               show=False)
            i += 1


def _ffmpeg_write_animation(input_file_path, output_dir, animation_speed):
    """uses ffmpeg to write a timelapse from the images"""
    if (animation_speed < 0.1) | (animation_speed > 4.0):
        print("animation_speed out of limits. Setting it to 0.6 ...")
        animation_speed = 0.6

    animation_speed = str(animation_speed)
    ani_name = io.animation_name(input_file_path)
    command = ('ffmpeg -pattern_type glob -i ' '"' + output_dir + '*.jpg"'
               ' -filter:v "setpts=' + animation_speed + '*PTS" ' + ani_name)

    os.system(command)


@time_this
def animate(nodes_sorted,
            input_file_path,
            animation_speed=0.6):
    """Saves an animation, where each frame is a step of the spiralsort
    algorithm, with detais about the slices that it is working on.

    Args:
        nodes_sorted (df)       :  the spiralsorted point-cloud
        start_node_id (str)     :  the node_id of the node where
                                   spiralsorting started
        input_file_path (str)   :  path/to/input/file
        animation_speed (float) :  the decimal ratio of the default
                                   Presentation Time Stamp of the video
                                   (between 0.1 and 4.0)
    """
    output_dir = os.path.join(os.getcwd(), "spiral_sort_visualization/")

    # start_node is the 1st node
    start_node_id = nodes_sorted.iloc[0, 0]

    # save the frames at output_dir
    _plot_spiralsort(nodes_sorted, start_node_id, output_dir)

    # save the video at the input_file_path dir
    _ffmpeg_write_animation(input_file_path, output_dir, animation_speed)

    # cleanup the images
    shutil.rmtree(output_dir)
