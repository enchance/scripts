#!/usr/bin/env python3

import os, sys, shutil, click  # noqa
from pathlib import Path
from rich import print

from utils.utils import command_config, path_config


__version__ = '0.3.0'
errors = {}


def is_valid_folder(prefix: str, name: str) -> bool:
    return name.startswith(prefix)


def cleanup_folders(path: str):
    os.rmdir(path)


@click.command(**command_config)
@click.version_option(__version__, prog_name='mergefiles')
@click.argument('input_path', type=path_config)
@click.option('--prefix', '-p', help='Prefix of each folder chunked folder', default='chunk-', show_default=True)
@click.option('--output', '-o', type=path_config, help='Output path to create subfolders in')
def main(input_path: Path, prefix: str, output: Path):
    """
    Collate all files in subfolders that have a specific prefix. Only searches for first-level subfolders.\n
    Works with the chunkfiles script.
    """
    folder_path = input_path
    output_path = output or folder_path
    counter = 0

    chunk_folders = [i for i in os.listdir(folder_path) if is_valid_folder(prefix, i)]

    for folder in chunk_folders:
        subfolder_path = os.path.join(folder_path, folder)
        counter += len(os.listdir(subfolder_path))
        for file in os.listdir(subfolder_path):
            from_path = os.path.join(folder_path, folder, file)
            to_path = os.path.join(output_path, file)

            try:
                shutil.move(from_path, to_path)
            except Exception:   # noqa
                errors.setdefault('unmoved', [])
                errors['unmoved'].append(from_path)

        try:
            cleanup_folders(subfolder_path)
        except Exception:   # noqa
            errors.setdefault('undeleted', [])
            errors['undeleted'].append(subfolder_path)

    if len(errors):
        print(errors)

    total = f'{counter} files moved'
    print(total)


if __name__ == '__main__':
    main()
