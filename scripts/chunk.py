#!/usr/bin/env python3

import os, sys, shutil, argparse  # noqa
from icecream import IceCreamDebugger
from pathvalidate import sanitize_filename


ic = IceCreamDebugger(prefix='')

CHUNK_NAME = 'chunk'
ITEM_COUNT = 110
errors = {}


def chunk_it(data: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(data), n):
        yield data[i:i + n]


def can_continue() -> bool:
    args = sys.argv
    if len(args) != 2:
        ic('Missing folder path')
        return False

    path = os.path.abspath(args[1])

    if not os.path.isdir(path):
        ic('Not a folder')
        return False

    return True


def rename_file(path: str, file: str) -> str | None:
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


def has_errors() -> int:
    return len(errors)


if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-c', '--chunk', default=ITEM_COUNT, type=int, help='Number of files per chunked folder')
    # args = parser.parse_args()
    # ic(args.chunk)

    if not can_continue():
        sys.exit(1)

    folder_path = os.path.abspath(sys.argv[1])

    # CLean names
    files = [i for i in os.listdir(folder_path) if os.path.isfile(i)]
    for name in files:
        rename_file(folder_path, name)



    files = sorted([i for i in os.listdir(folder_path) if os.path.isfile(i)])
    chunks = list(chunk_it(files, ITEM_COUNT))
    pad = len(str(len(chunks)))
    count = 0

    for idx, namelist in enumerate(chunks):
        num = idx + 1
        chunk_name = f'{CHUNK_NAME}-{num:0{pad}}'
        folder = os.path.join(folder_path, chunk_name)

        os.makedirs(folder, exist_ok=True)
        for name in namelist:
            from_path = os.path.join(folder_path, name)
            to_path = os.path.join(folder_path, chunk_name, name)

            try:
                shutil.move(from_path, to_path)
                count += 1
            except Exception:   # noqa
                errors.setdefault('unmoved', [])
                errors['unmoved'].append(name)

    if has_errors():
        ic(errors)

    total = f'{count} files moved'
    ic(total)
