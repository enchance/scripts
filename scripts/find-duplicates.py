#!/usr/bin/env python3

import click
import os
from pathlib import Path
from collections import defaultdict
import datetime
import humanize
from tabulate import tabulate
from typing import Dict, List, Tuple, Union

def truncate_path(path: str, max_length: int = 60) -> str:
    """Truncate the path to the specified maximum length."""
    if len(path) <= max_length:
        return path
    return '...' + path[-(max_length - 3):]

@click.command()
@click.argument('folder', type=click.Path(exists=True))
@click.option('--with-size', is_flag=True, help='Identify duplicates by name and size')
@click.option('-s', '--sensitive', is_flag=True, help='Case-sensitive search')
@click.option('--non-recursive', is_flag=True, help='Search only in the main folder')
@click.option('--show-all', is_flag=True, help='Show all duplicate sets at once')
@click.option('--no-truncate', is_flag=True, help='Show full file paths without truncation')
@click.option('--with-time', is_flag=True, help='Show complete date and time for creation date')
@click.option('--with-modified', is_flag=True, help='Show modified date column')
def find_duplicates(folder: str, with_size: bool, sensitive: bool, non_recursive: bool, show_all: bool, 
                    no_truncate: bool, with_time: bool, with_modified: bool) -> None:
    """
    Scan a folder for duplicate files based on their filename.

    This script searches for duplicate files in the specified folder and its subdirectories.
    It provides options to customize the search criteria and display format.
    """
    folder_path = Path(folder)
    if not folder_path.is_dir():
        click.echo("Error: Specified path is not a directory.")
        return

    files: Dict[Union[str, Tuple[str, int]], List[Path]] = defaultdict(list)
    for root, _, filenames in os.walk(folder_path):
        if non_recursive and root != str(folder_path):
            continue
        for filename in filenames:
            file_path = Path(root) / filename
            key = (file_path.name, file_path.stat().st_size) if with_size else file_path.name
            if not sensitive:
                key = str(key).lower()
            files[key].append(file_path)

    duplicates = {k: v for k, v in files.items() if len(v) > 1}
    if not duplicates:
        click.echo("No duplicate files found.")
        return

    if show_all:
        show_all_duplicates(duplicates, folder_path, no_truncate, with_time, with_modified)
    else:
        show_duplicates_individually(duplicates, folder_path, no_truncate, with_time, with_modified)

def show_all_duplicates(duplicates: Dict[Union[str, Tuple[str, int]], List[Path]], folder_path: Path, 
                        no_truncate: bool, with_time: bool, with_modified: bool) -> None:
    """Display all duplicate sets in a single table."""
    all_duplicates = []
    index = 1
    for _, paths in duplicates.items():
        for path in paths:
            row = create_file_row(path, folder_path, index, no_truncate, with_time, with_modified)
            all_duplicates.append(row)
            index += 1
        all_duplicates.append(["-" * 5, "-" * 20, "-" * 10, "-" * 10] + ["-" * 10] * with_modified)

    headers = ["#", "Location", "Size", "Created"]
    if with_modified:
        headers.append("Modified")
    click.echo(tabulate(all_duplicates, headers=headers, tablefmt="pipe"))
    handle_deletion(duplicates, folder_path)

def show_duplicates_individually(duplicates: Dict[Union[str, Tuple[str, int]], List[Path]], folder_path: Path, 
                                 no_truncate: bool, with_time: bool, with_modified: bool) -> None:
    """Display duplicate sets one at a time."""
    for _, paths in duplicates.items():
        table_data = []
        for i, path in enumerate(paths, 1):
            row = create_file_row(path, folder_path, i, no_truncate, with_time, with_modified)
            table_data.append(row)

        headers = ["#", "Location", "Size", "Created"]
        if with_modified:
            headers.append("Modified")
        click.echo(tabulate(table_data, headers=headers, tablefmt="pipe"))
        
        action = handle_deletion([paths], folder_path)
        if action == "exit":
            return
        elif action == "next":
            continue

def create_file_row(path: Path, folder_path: Path, index: int, no_truncate: bool, with_time: bool, with_modified: bool) -> List[Union[int, str]]:
    """Create a row of file information for the table."""
    size = humanize.naturalsize(path.stat().st_size)
    ctime = path.stat().st_ctime
    mtime = path.stat().st_mtime
    rel_path = path.relative_to(folder_path)
    
    if not no_truncate:
        rel_path = truncate_path(str(rel_path))
    
    date_format = '%Y-%m-%d %H:%M:%S' if with_time else '%Y-%m-%d'
    created = datetime.datetime.fromtimestamp(ctime).strftime(date_format)
    
    row = [index, str(rel_path), size, created]
    
    if with_modified:
        modified = datetime.datetime.fromtimestamp(mtime).strftime(date_format)
        row.append(modified)
    
    return row

def handle_deletion(duplicate_sets: List[List[Path]], folder_path: Path) -> str:
    """Handle the deletion of files based on user input."""
    to_delete = click.prompt("Enter indices to delete (comma-separated), press Enter to skip, or type 'exit' to quit", type=str, default="")
    if to_delete.lower() == 'exit':
        return "exit"
    if not to_delete:
        return "next"

    indices = [int(i.strip()) for i in to_delete.replace(' ', '').split(',') if i.strip().isdigit()]
    for idx in indices:
        if 1 <= idx <= sum(len(paths) for paths in duplicate_sets):
            file_to_delete = [path for paths in duplicate_sets for path in paths][idx - 1]
            try:
                file_to_delete.unlink()
                click.echo(f"Deleted: {file_to_delete.relative_to(folder_path)}")
            except PermissionError:
                click.echo(f"Unable to delete: {file_to_delete.relative_to(folder_path)}")
    return "continue"

if __name__ == '__main__':
    find_duplicates()