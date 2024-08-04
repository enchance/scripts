#!/usr/bin/env python3

import os, sys, shutil, click  # noqa
from pathlib import Path
from rich import print

from utils.utils import command_config, path_config, clean_filename

__version__ = "0.3.0"
errors = {}


def chunk_it(data: list, n: int):
    """Yield successive n-sized chunks from data."""
    for i in range(0, len(data), n):
        yield data[i:i + n]


@click.command(**command_config)
@click.version_option(__version__, prog_name='chunkfiles')
@click.argument('input_path', type=path_config)
@click.option('--count', '-c', help='Number of files per chunked folder', type=click.IntRange(min=2, max=300),
              default=110, show_default=True)
@click.option('--start', '-s', type=click.IntRange(min=0, max=30000), help='Starting folder number', default=1,
              show_default=True)
@click.option('--prefix', help='Prefix of each folder chunked folder', default='chunk-', show_default=True)
@click.option('--suffix', help='Suffix of each folder chunked folder', default='x', show_default=True)
@click.option('--output', '-o', type=path_config, help='Output path to create subfolders in')
def main(input_path: Path, count: int, prefix: str, suffix: str, output: Path, start: int):
    """
    Group all first-level files into subfolders. All subfolders will be serialized and can be customized with any
    prefix and suffix of your choice. \n
    Works with the mergefiles script.
    """
    folder_path = input_path
    output = output or folder_path

    # Rename
    files = [i for i in os.listdir(folder_path) if os.path.isfile(i)]
    if not files:
        raise click.ClickException('You did not provide an input path: Example: chunkfiles .')
    for name in files:
        try:
            clean_filename(folder_path, name)
        except Exception as e:
            click.echo('Unable to rename file. Skipping.')

    files = sorted([i for i in os.listdir(folder_path) if os.path.isfile(i)])
    chunks = list(chunk_it(files, count))
    pad = len(str(len(chunks)))
    pad = 2 if pad == 1 else pad
    counter = 0

    for idx, namelist in enumerate(chunks):
        num = start + idx
        chunk_name = f'{prefix}{num:0{pad}}{suffix}'
        folder = os.path.join(output, chunk_name)

        os.makedirs(folder, exist_ok=True)
        for name in namelist:
            from_path = os.path.join(folder_path, name)
            to_path = os.path.join(output, chunk_name, name)

            try:
                shutil.move(from_path, to_path)
                counter += 1
            except Exception:  # noqa
                errors.setdefault('unmoved', [])
                errors['unmoved'].append(name)

    if len(errors):
        print(errors)

    total = f'{counter} files moved'
    print(total)


if __name__ == '__main__':
    main()
