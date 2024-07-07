#!/usr/bin/env python3

import click
import hashlib
import os

@click.command()
@click.option('--type', '-t', type=click.Choice(['sha1', 'sha256', 'md5']), required=True, help='Hash type to verify')
@click.option('--hash', '-h', required=True, help='Expected hash value')
@click.argument('file', type=click.Path(exists=True))
def verify_hash(type, hash, file):
    """Verify the hash of a file."""
    try:
        file_path = os.path.abspath(file)
        
        if type == 'sha1':
            file_hash = hashlib.sha1()
        elif type == 'sha256':
            file_hash = hashlib.sha256()
        elif type == 'md5':
            file_hash = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                file_hash.update(chunk)
        
        calculated_hash = file_hash.hexdigest()
        
        if calculated_hash.lower() == hash.lower():
            click.echo('Success: Hash match')
        else:
            click.echo('Failed: Wrong hash')
    
    except IOError as e:
        click.echo(f"Error reading file: {e}", err=True)
    except Exception as e:
        click.echo(f"An error occurred: {e}", err=True)

if __name__ == '__main__':
    verify_hash()