#!/usr/bin/env python3

import os, sys, click, tarfile, time           # noqa
from pathlib import Path
from contextlib import chdir
from icecream import IceCreamDebugger

from utils.utils import path_config, command_config, clean_filename


__version__ = '0.1.0'
__progname__ = 'Bulk Merge Compressor'

ic = IceCreamDebugger(prefix='')

def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@click.command(**command_config)
@click.version_option(__version__, prog_name=__progname__)
@click.argument('extension', type=click.STRING)
@click.argument('input_path', type=path_config)
@click.argument('added_path', nargs=-1, type=path_config)
@click.option('--name', '-n', help='File name of the generated compressed file',
              default='<extension> compressed source',
              show_default=True)
@click.option('--recursive', '-R', help='Scan recursively saving one compressed file per folder',
              type=click.BOOL, is_flag=True)
@click.option('--delete', '-d', help='Delete file once compressed', type=click.BOOL, is_flag=True)
@click.option('--hidden', '-h/ ', help='Allow scanning of hidden folders', type=click.BOOL, is_flag=True)
def compress_files(extension: str, input_path: Path, added_path: Path, name: str,
                   recursive: bool, delete: bool, hidden: bool):
    """
    Look for files in a folder and compress them to the tar.gz format.
    One compressed file will be generated per folder.
    """
    # ic(delete)
    # sys.exit(1)

    def _is_valid(file_: str) -> bool:
        return file_.lower().endswith(f'.{extension.lower()}')

    def _is_hidden(filepath) -> bool:
        return os.path.basename(folder_path).startswith(".")

    def _scan_and_compress(folder_path_: Path, datalist: list[str], output_file_: str) -> int:
        # ic(type(current_folder_), current_folder_)
        # ic(type(datalist), datalist)

        total = 0
        if datalist:
            rel_path = os.path.relpath(folder_path_)
            with chdir(rel_path):
                folder = os.path.basename(Path(rel_path))
                fill_char = click.style("#", fg="green")
                empty_char = click.style("-", fg="white", dim=True)
                d = dict(label=f'Compressing {folder}:', fill_char=fill_char, empty_char=empty_char)

                with click.progressbar(datalist, **d) as bar:
                    with tarfile.open(output_file_, 'w:gz') as tar:
                        for f in datalist:
                            for j in bar:
                                tar.add(j)
                    total += 1

            # Delete
            if delete:
                with chdir(rel_path):
                    for f in datalist:
                        os.remove(f)
        else:
            ic(f'No {extension.upper()} files found.')
        return total

    if delete := delete and click.confirm(f'Confirm deletion of source files?'):
        pass

    name = name.replace('<extension>', extension.upper())
    output_file = f'{name}.tar.gz'

    count = 0
    for path in [input_path, *list(added_path)]:        # noqa
        if recursive:
            for current_folder, dirnames, files in os.walk(path):
                folder_path = Path(current_folder)
                if not hidden and _is_hidden(folder_path):
                    continue
                valid_files = [i for i in files if _is_valid(i)]
                count += _scan_and_compress(folder_path, valid_files, output_file)
        else:
            if valid_files := [i for i in os.listdir(path) if _is_valid(i)]:
                count += _scan_and_compress(path, valid_files, output_file)
            else:
                click.echo(f'No {extension.upper()} files found.')

    plural = 'files' if count > 1 else 'file'
    click.echo(f'CREATED: {count} compressed {plural}')

    if not delete:
        click.echo('Source files not deleted')


if __name__ == '__main__':
    compress_files()