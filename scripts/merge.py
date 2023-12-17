#!/usr/bin/env python3

import os, sys, shutil, typer  # noqa
from typing_extensions import Annotated
from pathlib import Path
from rich import print


__version__ = '0.2.0'
errors = {}


def is_valid_folder(prefix: str, name: str) -> bool:
    return name.startswith(prefix)


def version_callback(show: bool):
    if show:
        print(f'Merge CLI version:', __version__)
        raise typer.Exit()


def main(
        path: Annotated[Path, typer.Argument(help='Folder path', callback=os.path.abspath,
                                             exists=True, file_okay=False)],
        prefix: Annotated[str, typer.Option('--prefix', '-p', help='Prefix of each folder chunked folder')] = 'chunk',
        output: Annotated[Path, typer.Option('--output', '-o', help='Output path', callback=os.path.abspath,
                                             exists=True, file_okay=False)] = '.',
        version: Annotated[bool, typer.Option('--version', callback=version_callback, is_eager=True,
                                              help='Show program version')] = False,
):
    """
    Collate all the files of subfolders that begin with a prefix. \n
    Only searches for first-level subfolders.
    """
    folder_path = path
    output_path = output or path
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
            os.rmdir(os.path.join(subfolder_path))
        except Exception:   # noqa
            errors.setdefault('undeleted', [])
            errors['undeleted'].append(subfolder_path)

    if len(errors):
        print(errors)

    total = f'{counter} files moved'
    print(total)


if __name__ == '__main__':
    typer.run(main)
