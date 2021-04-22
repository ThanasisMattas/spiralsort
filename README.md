# SpiralSort

![PyPI] ![Build_Status] ![codecov]

<br />
A point-cloud spiral-sorting algorithm
<br />

<img src="https://raw.githubusercontent.com/ThanasisMattas/spiralsort/master/bin/spiralsort_2D.gif" width="400" height="248" /> <img src="https://raw.githubusercontent.com/ThanasisMattas/spiralsort/master/bin/spiralsort_3D.gif" width="400" height="248" />

<br />

| requirements        | optional              | os        |
| ------------------- | --------------------- | --------- |
| python3             | pillow>=7.0.0         | GNU/Linux |
| click>=7.0          | matplotlib>=3.1.3     | Windows   |
| numba>=0.48.0       | ffmpeg>=4.1.4         |           |
| numpy>=1.18.0       | pytest>=5.4.2         |           |
| pandas>=1.0.1       |                       |           |

## Install

```bash
$ pip install spiralsort
```

```bash
$ conda install -c mattasa spiralsort
```

## Usage

1. command line

```bash
$ spiralsort <file_name> <start_node_id>
```

2. inside a python script

```python
from spiralsort.core import spiralsorted

point_cloud_spiralsorted = spiralsorted(point_cloud, start_node_id)
```

3. docker container &nbsp; ![Docker Cloud Build Status]

Insert input_file and take the output, using a shared volume between the
host and the container.


```
$ docker pull thanasismatt/spiralsort:latest
$ docker run -it --rm -v ${PWD}:<container_dir> thanasismatt/spiralsort bin/bash
root@<container_id>:/# spiralsort <container_dir>/<file_name> <start_node_id>
```

## Options

**-f/--output-format=<format** **>** <br />
(suported: csv, json, xlsx; defaults to the format of the input file) <br />
**-a/--save-animation** <br />
save an animation of the spiralsorting process (.mp4)


## Input/Output format

| node_id |   x   |   y   |   z   |
| ------- | ----- | ----- | ----- |
| N000    |  1.12 |  2.32 | 12.24 |
| N001    |  1.28 |  2.64 | 13.04 |
| ...

- File (csv, json) or DataFrame
- node_ids have to be unique
- In case of 2D data, just use a constant value for the 3rd dimension.

## Test

```bash
$ pytest spiralsort
```

## Under the hood

Starting from the *start_node* the algorithm evaluates a cost for each node and
moves to the <br /> node with the minimum cost (cost for node<sup>i+1</sup> is
the distance from node<sup>i</sup> plus the distance from <br /> the
start_node). At each step, a counterclockwise filter is applied, in order to
force a constant <br /> rotational direction.

Optimizing the process, a methodology of slicing is applied on the point-cloud,
described by the <br /> following steps:

1. Sort the point cloud with respect to the distance from the start node
2. Segment it into slices and take the first slice
3. Take a SPIRAL_WINDOW (slice further) <br />
   Spiral windows for the 1st slice consist of 400 nodes, starting from the last
   sorted node <br /> (the start_node for the 1st window)
1. Iteretively pop 15 nodes (a STRIDE), by the minimum cost. Namely, a
   SPIRAL_WINDOW is <br /> sliced to spiralsort a STRIDE of nodes, before moving
   to the next SPIRAL_WINDOW. <br />
   (cost = |node - start_node| + |node - prev_node|) <br />
   At each iterative step, a filter is applied, keeping only nodes from the
   counterclockwise side <br /> of the vector that starts from the start node
   and ends at the previous node, in order to <br /> force the algorithm to move
   on a constant rotating direction.
2. Take the next SPIRAL_WINDOW and pop the next STRIDE. <br />
3. Continue until the remainder of the nodes reaches the size of the
   half slice (1000 nodes for <br /> the 1st slice).
4. Merge the remaining nodes with the next slice <br />
   This overlap of the slices ensures that there is a continuity while
   selecting the next nodes, <br /> when the algorithm reaches the last nodes of
   the slice.
5. For the next slices, while moving away from the *start_node*, the
   SPIRAL_WINDOW is <br /> selected differently. Specifically, before each
   STRIDE, the counterclockwise filter is applied, <br /> then the remaining
   nodes are cost-sorted (with respect to their cost) from the last <br />
   spiralsorted node and, finally, a SPIRAL_WINDOW is sliced, to start the
   iterative spiralsorting <br /> of the nodes in the next STRIDE.
6. Keep moving by SPIRAL_WINDOWs, counterclockwise
   filtering at each stride, popping <br /> STRIDEs of nodes until the half
   slice thresshold.
7.  Upon reaching the last slice, remove the *half_slice* threshold, to
   pop all the remaining nodes.

## Animate the process

1. command line

```bash
$ spiralsort <file_name> <start_node_id> --save-animation
```

2. inside a python script

```python
from spiralsort.spiralsort_post import animate

animate(point_cloud_sorted, path_to_input_file)
```

## License
[GNU General Public License v3.0]

<br />

> (C) 2020, Athanasios Mattas <br />
> thanasismatt@gmail.com

[//]: # "links"

[Docker Cloud Build Status]: <https://img.shields.io/docker/cloud/build/thanasismatt/spiralsort?style=plastic>
[PyPI]: <https://img.shields.io/pypi/v/spiralsort?color=success>
[Build_Status]: <https://travis-ci.com/ThanasisMattas/spiralsort.svg?branch=master>
[codecov]: <https://codecov.io/gh/ThanasisMattas/spiralsort/branch/master/graph/badge.svg>
[GNU General Public License v3.0]: <https://github.com/ThanasisMattas/spiralsort/blob/master/COPYING>