import os

from spiralsort import io, spiralsort_post
from spiralsort.core import spiralsort


def main():
    # reed input
    input_file = os.path.join(os.getcwd(),
                              "data_examples",
                              "point_cloud_example.csv")
    nodes = io.read_data_file(input_file)

    # say spiralsorting starts form the node with id "N_4004"
    start_node_id = "N_4004"

    # spiralsort
    sorted_nodes = spiralsort(nodes, start_node_id)

    # write output
    output_file = io.output_file_path(input_file)
    io.write_output(sorted_nodes, output_file)

    # save an animation, visualizing how the SpiralSort works
    spiralsort_post.animate(sorted_nodes, input_file)

if __name__ == '__main__':
    main()
