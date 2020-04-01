"""
info:
    file        :  __main__.py
    author      :  Thanasis Mattas
    license     :  GNU General Public License v3
    description :  Main script that calls all necessary processes

SpiralSort is free software; you may redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version. You should have received a copy of the GNU
General Public License along with this program. If not, see
<https://www.gnu.org/licenses/>.
"""


from datetime import timedelta
from timeit import default_timer as timer

import click
import pandas as pd

from spiralsort import io
from spiralsort.core import spiralsort


@click.command()
@click.argument("file_path")
@click.argument("master_node_id")
@click.option("--output-format", "output_format", help="defaults to the"
              " format of the input file")
@click.option("--save-animation/--no-save-animation", "save_animation",
              default=False, show_default=True, help="save an animation"
              " of the stepwise spiralsorting process")
def main(file_path,
         master_node_id,
         save_animation=False,
         output_format=None):

    start = timer()
    nodes = io.read_data_file(file_path)

    # when chained_assignment occurs, raise an error, in order to have
    # full control of the process
    with pd.option_context("mode.chained_assignment", "raise"):
        sorted_nodes = spiralsort(nodes, master_node_id)

    output_file = io.output_file_path(file_path, output_format)
    io.write_output(sorted_nodes, output_file)

    ss_duration = str(timedelta(seconds=timer() - start))
    click.echo("SpiralSorting completed. Duration: " + ss_duration)

    if save_animation:
        try:
            from spiralsort import spiralsort_post
            click.echo("Creating the animation. This will take a while...")
            spiralsort_post.save_animation(sorted_nodes, file_path)
        except ModuleNotFoundError:
            raise Exception("Check if matplotlib and ffmpeg are installed."
                            " Exiting...")

if __name__ == "__main__":
    main()
