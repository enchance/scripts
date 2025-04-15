#!/usr/bin/env python3

import click
import os
from getpass import getpass
from PyPDF2 import PdfReader, PdfWriter

@click.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def remove_password(input_path, output):
    """Remove password protection from a PDF file."""
    # Get password securely
    password = getpass("Enter PDF password: ")
    
    # Generate default output name if not provided
    if not output:
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        output = f"{name}_unlocked{ext}"
    
    try:
        # Read the PDF with password
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            reader.decrypt(password)
        
        # Create new PDF without encryption
        writer = PdfWriter()
        
        # Add all pages to the writer
        for page in reader.pages:
            writer.add_page(page)
        
        # Write the output file
        with open(output, 'wb') as out_file:
            writer.write(out_file)
        
        click.echo(f"Unlocked PDF saved to: {output}")
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        return 1
    
    return 0

if __name__ == '__main__':
    remove_password()