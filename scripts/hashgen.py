#!/usr/bin/env python3

import random
import click


DEFAULT_CHARS = "ABCDEFGHJKLMNPQRSTVWXYZabcdefghjkmnpqrstvwxyz23456789"
ALL_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


@click.command()
@click.option("-l", "--len", "length", default=4, show_default=True, type=int, help="Length of the hash.")
@click.option('-f', "--full", is_flag=True, show_default=True, type=bool, help="Include lowercase characters.")
@click.option("-a", "--all", "all_", is_flag=True, help="Include all alphanumeric characters.")
@click.option("-c", "--count", default=1, show_default=True, type=int, help="Number of hashes to generate.")
def generate_hash(length, full, all_, count):
    """
    Generate random alphanumeric hashes. Excludes similar looking characters such as 1, l, i, etc.
    Use -a to include all alphanumeric characters.
    """
    chars = ALL_CHARS if all_ else DEFAULT_CHARS
    for _ in range(count):
        hash_ = "".join(random.choices(chars, k=length))
        hash_ = full and hash_ or hash_.upper()
        print(hash_)


if __name__ == "__main__":
    generate_hash()
