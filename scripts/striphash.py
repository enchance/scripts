#!/usr/bin/env python3

import os, re, click, sys  # noqa

__version__ = '0.1.0'
__progname__ = 'Stripslashes'


def strip_hash(filename: str, formats: list[str], prefix: str):
    base, ext = os.path.splitext(filename)
    if ext[1:].lower() not in formats:
        return None

    match = re.match(fr'^(.+?)\s*{prefix}[a-zA-Z0-9]{{9,16}}$', base)
    if match:
        new_name = f"{match.group(1)}{ext}"
        return new_name
    return None


def process_directory(directory: str, formats: list[str], recursive: bool, prefix: str, verbose: bool):
    renamed_count = 0
    processed_dirs = 0
    retained_files = []

    for root, dirs, files in os.walk(directory):
        processed_dirs += 1
        for filename in files:
            full_path = os.path.join(root, filename)
            new_name = strip_hash(filename, formats, prefix)
            if new_name:
                new_full_path = os.path.join(root, new_name)
                if not os.path.exists(new_full_path):
                    os.rename(full_path, new_full_path)
                    renamed_count += 1
                    if verbose:
                        click.echo(f'{new_name}: {os.path.join(root, new_name[:10])}...')
                else:
                    retained_files.append(full_path)

        if not recursive:
            break

    return renamed_count, processed_dirs, retained_files


@click.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('-r', '--recursive', is_flag=True, help='Process directories recursively')
@click.option('-f', '--format', default='mp4', help='File formats to process (comma-separated)')
@click.option('-p', '--prefix', default='-', help='Prefix before the hash')
@click.option('-v', '--verbose', is_flag=True, help='Show verbose info')
def main(directory: str, recursive: bool, format: str, prefix: str, verbose: bool):  # noqa
    """
    Rename files by removing any hash patterns at the end of the filename. Follows the format "-<HASH HERE>".
    Defaults to mp4 files.
    """
    skip_dirs = ['.thumbnails']
    if not os.path.isdir(directory) or directory in skip_dirs:
        click.echo(f"Error: The directory '{directory}' does not exist.")
        sys.exit(1)

    formats = [fmt.lower() for fmt in format.split(',')]
    renamed, dirs, retained = process_directory(directory, formats, recursive, prefix, verbose)

    if retained:
        click.echo('Some files were retained:')
        for i in retained:
            click.echo(f'  {i}')
    click.echo(f"\nRenamed {renamed} file(s) in {dirs} folder(s).")


if __name__ == "__main__":
    main()
