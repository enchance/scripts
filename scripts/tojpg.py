#!/usr/bin/env python3

from pathlib import Path
from typing import List, Tuple, Optional
import click
from PIL import Image
import random
import string
from rich.console import Console


console = Console()
JPG_QUALITY = 95


def scan_for_files(folder_path: Path, formats: List[str], recursive: bool) -> List[Path]:
    """Get all image files of specified formats from the folder."""
    pattern = "**/*." if recursive else "*."
    files: List[Path] = []
    for fmt in formats:
        files.extend(folder_path.glob(f"{pattern}{fmt}"))
    return sorted(files)


def generate_unique_filename(original_path: Path) -> Path:
    """Generate a unique filename with a random hash if the file already exists."""
    if not original_path.exists():
        return original_path

    # Generate random 6-character alphanumeric hash
    hash_chars = string.ascii_letters + string.digits
    random_hash = ''.join(random.choices(hash_chars, k=6))

    # Insert hash before the extension
    new_name = f"{original_path.stem}-{random_hash}{original_path.suffix}"
    return original_path.parent / new_name


def convert_image(source: Path, target: Path, quality: int) -> Tuple[bool, Optional[str]]:
    """Convert a single image to JPG format."""
    try:
        with Image.open(source) as img:
            # Convert to RGB if necessary (for PNG transparency)
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            img.save(target, 'JPEG', quality=quality)
        return True, None
    except Exception as e:
        return False, str(e)


def process_images(files: List[Path], delete_original: bool, verbose: bool, dry_run: bool, recursive: bool,
                   quality: int) -> Tuple[int, List[str], List[str]]:
    """Process all images with progress bar and error tracking."""
    converted_count = 0
    conversion_errors: List[str] = []
    other_errors: List[str] = []

    with click.progressbar(files, label='Converting images') as progress_files:
        for source in progress_files:
            # Create target path with .jpg extension
            target = source.parent / f"{source.stem}.jpg"
            target = generate_unique_filename(target)

            if verbose:
                display_path = str(source.relative_to(source.parent)) if not recursive else str(source)
                click.echo(f"Processing: {display_path}")

            if dry_run:
                click.echo(f"Would convert: {source} -> {target}")
                if delete_original:
                    click.echo(f"Would delete: {source}")
                continue

            success, error_msg = convert_image(source, target, quality)

            if success:
                converted_count += 1
                if delete_original:
                    try:
                        source.unlink()
                    except Exception as e:
                        other_errors.append(f"Could not delete {source}: {str(e)}")
            else:
                conversion_errors.append(f"{source}: {error_msg}")

    return converted_count, conversion_errors, other_errors


def confirm_deletion() -> bool:
    """Ask user for confirmation before deleting files."""
    return click.confirm(
        click.style(
            "Warning: Are you sure you wan to delete the original files?",
            fg="yellow",
            bold=True
        ),
        abort=True  # This will exit if user says no
    )


@click.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option('-r', '--recursive', is_flag=True, help='Search recursively in subdirectories.')
@click.option('-f', '--format', 'formats', default='png',
              help='Image formats to convert (comma-separated). Default: png')
@click.option('-d', '--delete', is_flag=True, help='Delete original files after conversion.')
@click.option('-q', '--quality', default=JPG_QUALITY, help=f'JPEG quality. Default: {JPG_QUALITY}')
@click.option('-v', '--verbose', is_flag=True, help='Show verbose output.')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes.')
def main(path: Path, recursive: bool, formats: str, delete: bool, verbose: bool, dry_run: bool, quality: int):
    """Convert image files to JPG format."""
    if not path.exists() or not path.is_dir():
        click.echo("Error: Specified folder does not exist or is not accessible.", err=True)
        return

    if delete:
        confirm_deletion()

    format_list = [fmt.strip().lower() for fmt in formats.split(',')]
    files = scan_for_files(path, format_list, recursive)

    if not files:
        click.echo("No matching files found.")
        return

    if dry_run:
        click.echo("Dry run - no changes will be made")
        click.echo(f"Found {len(files)} files to process")

    converted_count, conversion_errors, other_errors = process_images(files, delete, verbose, dry_run,
                                                                      recursive, quality)

    # Display results with color
    if not dry_run:
        console.print(f"\n[green]Successfully converted {converted_count} images[/green]")

        if conversion_errors:
            console.print("\n[red]Conversion errors:[/red]")
            for error in conversion_errors:
                console.print(f"[red]- {error}[/red]")

        if other_errors:
            console.print("\n[yellow]Other errors:[/yellow]")
            for error in other_errors:
                console.print(f"[yellow]- {error}[/yellow]")


if __name__ == '__main__':
    main()
