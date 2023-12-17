#!/usr/bin/env python3

import os, sys, shutil, typer       # noqa
from pathlib import Path
from typing_extensions import Annotated
from typing import Optional
from pathvalidate import sanitize_filename
from rich import print


__version__ = "0.1.0"
errors = {}


def chunk_it(data: list, n: int):
    """Yield successive n-sized chunks from data."""
    for i in range(0, len(data), n):
        yield data[i:i + n]


def rename_file(path: Path, file: str) -> str | None:
    try:
        new_file = sanitize_filename(file)
        new_path = os.path.join(path, new_file)
        fullpath = os.path.join(path, file)
        if new_file != file:
            os.rename(fullpath, new_path)
        return new_file
    except Exception:       # noqa
        errors.setdefault('filenames', [])
        errors['filenames'].append(file)
        return None


def version_callback(show: bool):
    if show:
        print(f'Chunk CLI version:', __version__)
        raise typer.Exit()


def clean_path(path: str):
    path = os.path.abspath(path)
    if _ := os.path.isdir(path):
        return path

    print("Directory doesn't exist")
    raise typer.Abort()


def main(
        path: Annotated[Path, typer.Argument(help='Folder path', callback=os.path.abspath,
                                             exists=True, file_okay=False)],
        count: Annotated[int, typer.Option('--count', '-c', help='Number of files per chunked folder',
                                           min=2, max=300)] = 110,
        prefix: Annotated[str, typer.Option('--prefix', '-p', help='Prefix of each folder chunked folder')] = 'chunk-',
        version: Annotated[bool, typer.Option('--version', callback=version_callback, is_eager=True,
                                              help='Show program version')] = False,
):
    """
    Group all first-level files into subfolders.
    """
    folder_path = path

    # Rename
    files = [i for i in os.listdir(folder_path) if os.path.isfile(i)]
    if not files:
        raise typer.Exit()
    for name in files:
        rename_file(folder_path, name)

    files = sorted([i for i in os.listdir(folder_path) if os.path.isfile(i)])
    chunks = list(chunk_it(files, count))
    pad = len(str(len(chunks)))
    counter = 0

    for idx, namelist in enumerate(chunks):
        num = idx + 1
        chunk_name = f'{prefix}{num:0{pad}}'
        folder = os.path.join(folder_path, chunk_name)

        os.makedirs(folder, exist_ok=True)
        for name in namelist:
            from_path = os.path.join(folder_path, name)
            to_path = os.path.join(folder_path, chunk_name, name)

            try:
                shutil.move(from_path, to_path)
                counter += 1
            except Exception:   # noqa
                errors.setdefault('unmoved', [])
                errors['unmoved'].append(name)

    if len(errors):
        print(errors)

    total = f'{counter} files moved'
    print(total)


if __name__ == '__main__':
    typer.run(main)

