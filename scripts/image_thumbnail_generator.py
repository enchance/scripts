#!/usr/bin/env python3

import os
import click
from PIL import Image
import re
from pathlib import Path

PRESET_HEIGHT = 400
NAME = 'resized'
FORMAT = 'jpeg'
PREFIX = 'thumb-'


def compute_scaling(original_width: int, original_height: int, width: int, height: int) -> tuple[int, int]:
    """
    Compute scaling factor to maintain aspect ratio.
    :param original_width:      Original width
    :param original_height:     Original height
    :param width:               New width
    :param height:              New height
    :return:                    Tuple for use when resizing image
    """
    if height != original_height and width != original_width:
        return int(width), int(height)
    elif height != original_height:
        scaling_factor = height / original_height
        width = original_width * scaling_factor
    elif width != original_width:
        scaling_factor = width / original_width
        height = original_height * scaling_factor
    return int(width), int(height)


def create_slug(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    slug = re.sub(r'[^\w\s-]', '', name).strip().lower()
    return re.sub(r'[-\s]+', '-', slug)


def resize_image(image_path: str, output_path: str, width: int, height: int, output_format: str,
                 compression: int) -> str | None:
    """
    Resize the image based on width and/or height. If only one is specified then image maintains aspect ratio; both
    then image is distorded; neither then no resizing is applied.
    :param image_path:
    :param output_path:
    :param width:
    :param height:
    :param output_format:
    :param compression:
    :return:
    """
    if not width and not height:
        height = PRESET_HEIGHT
    try:
        with Image.open(image_path) as img:
            original_width, original_height = img.size

            new_size = (original_width, original_height)
            if width and height:
                new_size = (int(width), int(height))
            elif width:
                new_size = compute_scaling(original_width, original_height, width, original_height)
            elif height:
                new_size = compute_scaling(original_width, original_height, original_width, height)
            img = img.resize(new_size, Image.LANCZOS)

            pillow_quality = int(compression * 0.95)  # Map 1-100 to 1-95
            pillow_quality = max(1, min(pillow_quality, 95))  # Ensure it's within 1-95
            img.save(output_path, format=output_format, quality=pillow_quality)
            return output_path
    except Exception as e:
        click.echo(f"Error processing {image_path}: {str(e)}")
        return None


def get_unique_filename(output_path: Path, increment: int) -> Path:
    if not increment:
        return output_path

    counter = 1
    original_path = output_path
    while os.path.exists(output_path):
        filename = os.path.basename(original_path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(os.path.dirname(original_path), f"{name}-{counter}{ext}")
        counter += 1
    return output_path


@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('-c', '--compression', default=80, help='Compression quality (1-100, default: 80)')
@click.option('-x', '--exclude', help='Exclude formats (comma-separated)')
@click.option('-h', '--height', type=int, help='Resize to height maintaining aspect ratio')
@click.option('-w', '--width', type=int, help='Resize to width maintaining aspect ratio')
@click.option('-n', '--name', default=NAME, help=f'Name of output folder (default: {NAME})')
@click.option('-o', '--output', default=FORMAT, help=f'Output format (default: {FORMAT})')
@click.option('--overwrite', is_flag=True, help='Overwrite original files')
@click.option('-p', '--prefix', default=PREFIX, help=f'Prefix for resized images (Default: {PREFIX})')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.option('-i', '--increment', is_flag=True, help='Append an integer to filename if it already exists')
@click.version_option(version='0.2')
def main(path, compression, exclude, height, width, name, output, overwrite, prefix, verbose, increment):
    """Resize and compress images in the specified directory."""
    path = Path(path).absolute()
    excluded_formats = [f.strip().lower() for f in exclude.split(',')] if exclude else []
    output_dir = path if overwrite else path / name
    if not overwrite:
        output_dir.mkdir(exist_ok=True)

    processed_files = 0
    failed_files = []

    def process_file(file_path):
        nonlocal processed_files, failed_files

        for child in file_path.iterdir():
            if child.is_file() and child.suffix.lower()[1:] not in excluded_formats:
                slug = create_slug(child.name)
                output_filename = f"{prefix}{slug}{Path(output).suffix}.{FORMAT}"
                output_path = get_unique_filename(output_dir / output_filename, increment)
                result = resize_image(str(child), str(output_path), width, height, output, compression)

                if result:
                    processed_files += 1
                    if verbose:
                        click.echo(f"Compressed: {child} -> {output_path.name}")
                else:
                    failed_files.append(str(child))

    # Execute
    process_file(path)

    click.echo(f"Processed {processed_files} files.")
    if failed_files:
        click.echo("Failed to process the following files:")
        for file in failed_files:
            click.echo(file)


if __name__ == '__main__':
    main()
