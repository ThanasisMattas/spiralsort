# config.py is part of SpiralSort
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
"""Houses some global variables."""

# used at slicing the point-cloud
BASE = 2000
CONST_WINDOW = 32000

# used by the spiralsort algorithm
SPIRAL_WINDOW = 400
STRIDE = 15

# used at creating a mock point-cloud
NUM_NODES = 7000
