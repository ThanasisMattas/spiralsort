# SpiralSort is free software; you may redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. You should have received a copy of the GNU
# General Public License along with this program. If not, see
# <https://www.gnu.org/licenses/>.
"""
info:
    file        :  spiralsort_test.py
    author      :  Thanasis Mattas
    license     :  GNU General Public License v3
    description :  Houses all the tests (fail is not an option)

"""
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal, assert_index_equal
import pytest

from spiralsort import core, io, utils


# core.py tests
def test_counterclockwise_filter():
    prev_node_mock = pd.Series({'x': 2, 'y': 1})
    nodes_mock = pd.DataFrame(
        {
            'x': [-2, -2, -2, 1, 1, 2, 2, 4, 4, 5, 40, 40],
            'y': [1, -0.5, -1.5, -0.5, -1, 2, -1, 3, 1, 5, 21, 19]
        }
    )
    index_expected = pd.Index([0, 1, 5, 7, 9, 10])
    index_filtered = core._counterclockwise_filter(nodes_mock, prev_node_mock)
    assert_index_equal(index_expected, index_filtered)


def test_spiralsort():
    spiralsorted_expected = pd.DataFrame(
        {
            #     0, 1, 2, 3, 4, 5,  6,  7,  8,  9, 10, 11, 12, 13, 14,15,16,17,18,19  20, 21, 22,23,24,25
            'x': [0, 1, 2, 2, 1, 0, -1, -2, -2, -2, -1,  0,  1,  2,  3, 3, 3, 2, 1, 0, -2, -2,  3, 3, 2, 3],
            'y': [0, 0, 0, 1, 2, 2,  2,  1,  0, -1, -2, -2, -2, -2, -1, 0, 1, 2, 3, 3,  2, -2, -2, 2, 3, 3],
            'z': [0, 0, 0, 0, 0, 0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 0, 0, 0, 0, 0,  0,  0,  0, 0, 0, 0]
        }
    )
    max_digits = len(str(spiralsorted_expected.index.max()))
    node_id = ["N_" + (max_digits - len(str(idx))) * '0' + str(idx)
               for idx in spiralsorted_expected.index]
    spiralsorted_expected.insert(0, "node_id", node_id)
    spiralsorted_expected = spiralsorted_expected.astype(
        {'x': "float", 'y': "float", 'z': "float"}
    )

    # format
    # ---------------------------
    #    node_id    x    y    z
    # 0     N_00  0.0  0.0  0.0
    # 1     N_01  1.0  0.0  0.0
    # ...

    #             19  18  24   25
    #
    #      20  6   5   4  17   23
    #
    #       7              3   16
    #
    #       8      0   1   2   15
    #
    #       9                  14
    #
    #      21 10  11  12  13   22

    nodes_mock = spiralsorted_expected.copy()
    # shuffle the DataFrame
    nodes_mock = nodes_mock.sample(frac=1, random_state=9) \
                           .reset_index(drop=True)
    spiralsorted = core.spiralsort(nodes_mock,
                                   spiralsorted_expected.loc[0, "node_id"])
    assert_frame_equal(spiralsorted_expected,
                       spiralsorted.iloc[:, [0, 1, 2, 3]])


# =============================================================================
# io.py tests
def test_output_file_path():
    input_file_path_mock = "path/to/file.csv"
    output_file_path_expected = "path/to/file_spiralsorted.csv"
    output_file_path_expected_xlsx = "path/to/file_spiralsorted.xlsx"
    assert output_file_path_expected == \
        io.output_file_path(input_file_path_mock)
    assert output_file_path_expected_xlsx == \
        io.output_file_path(input_file_path_mock, output_format="xlsx")

def test_animation_name():
    input_file_path_mock = "path/to/file.csv"
    ani_name = "path/to/file.mp4"
    assert ani_name == io.animation_name(input_file_path_mock)


# =============================================================================
# utils.py tests
def test_duplicated_ids():
    nodes_mock_passing = pd.DataFrame({"node_id": ["N_00", "N_01", "N_02"]})
    nodes_mock_failling = pd.DataFrame({"node_id": ["N_00", "N_01", "N_00"]})
    with pytest.raises(Exception) as excifno:
        utils.check_duplicated_ids(nodes_mock_failling)
    assert utils.check_duplicated_ids(nodes_mock_passing) is True

def test_calc_half_slice():
    assert utils.calc_half_slice(slice(1, 6)) == 2
    assert utils.calc_half_slice(slice(1, 7)) == 3
