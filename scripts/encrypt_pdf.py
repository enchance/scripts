#!/usr/bin/env python3

import click
import getpass
from PyPDF2 import PdfReader, PdfWriter


@click.command()
@click.argument('pdf_path', type=click.Path(exists=True, dir_okay=False, readable=True, writable=True))
def main(pdf_path):
    """Encrypt a PDF with a password."""
    password = getpass.getpass("Enter password: ")
    if not password.strip():
        click.echo("Password cannot be empty.", err=True)
        return

    # Check if valid PDF and apply encryption
    try:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        with open(pdf_path, "wb") as output_pdf:
            writer.write(output_pdf)
        click.echo("PDF encrypted successfully.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


if __name__ == "__main__":
    main()
