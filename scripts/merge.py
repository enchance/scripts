#!/usr/bin/env python3

import os, sys, shutil  # noqa
from icecream import IceCreamDebugger


ic = IceCreamDebugger(prefix='')

CHUNK_NAME = 'chunk'
errors = {}


def can_continue() -> bool:
    if len(sys.argv) != 2:  # noqa
        ic('Missing folder path')
        return False

    path_ = os.path.abspath(sys.argv[1])

    if not os.path.isdir(path_):
        ic("Invalid folder path.")
        return False

    return True


def is_valid_folder(prefix: str, name: str) -> bool:
    return name.startswith(prefix) and os.path.isdir(name)


def has_errors() -> int:
    return len(errors)


if __name__ == '__main__':
    if not can_continue():
        sys.exit(1)

    folder_path = os.path.abspath(sys.argv[1])

    chunk_folders = sorted(i for i in os.listdir(folder_path) if is_valid_folder(CHUNK_NAME, i))
    count = 0
    for folder in chunk_folders:
        path = os.path.join(folder_path, folder)
        count += len(os.listdir(path))
        for file in os.listdir(path):
            from_path = os.path.join(folder_path, folder, file)
            to_path = os.path.join(folder_path, file)
            try:
                shutil.move(from_path, to_path)
            except Exception:   # noqa
                errors.setdefault('unmoved', [])
                errors['unmoved'].append(from_path)

        try:
            os.rmdir(os.path.join(path))
        except Exception:   # noqa
            errors.setdefault('undeleted', [])
            errors['undeleted'].append(path)

    if has_errors():
        ic(errors)

    total = f'{count} files moved'
    ic(total)