# __main__.py is part of SpiralSort
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
"""Main script that calls all necessary processes."""

import click
import pandas as pd

from spiralsort.core import spiralsorted
from spiralsort import io
from spiralsort.utils import time_this


@click.command()
@click.argument("file_path", type=click.Path())
@click.argument("start_node_id")
@click.option('-f', "--output-format", type=click.STRING,
              default=None, show_default=True,
              help="defaults to the format of the input file")
@click.option('-a', "--save-animation", is_flag=True,
              help="saves an animation of the stepwise spiralsorting process")
@click.version_option(version=__import__('spiralsort').__version__,
                      prog_name=__import__('spiralsort').__name__,
                      message='%(version)s')
@time_this
def main(file_path,
         start_node_id,
         output_format,
         save_animation):
    nodes = io.read_data_file(file_path)

    # When chained_assignment occurs, raise an error, in order to have
    # full control of the process.
    with pd.option_context("mode.chained_assignment", "raise"):
        sorted_nodes = spiralsorted(nodes, start_node_id)

    output_file = io.output_file_path(file_path, output_format)
    io.write_output(sorted_nodes, output_file)

    if save_animation:
        try:
            from spiralsort import spiralsort_post
            click.echo("Creating the animation. This will take a while...")
            spiralsort_post.animate(sorted_nodes, file_path)
        except ModuleNotFoundError:
            raise Exception("Check if matplotlib and ffmpeg are installed.")

if __name__ == "__main__":
    main()
