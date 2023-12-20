#!/usr/bin/env python3

import click


@click.group(invoke_without_command=True)
@click.option('--score', '-s', type=float, help='Your score')
@click.pass_context
def baz(ctx, score):
    if not ctx.invoked_subcommand:
        click.echo('abc')

# @click.option('--age', '-a', help='Your age', prompt='Age', default='4', type=click.Int)
# @click.version_option("0.1.0", prog_name="hello")
# @click.command(help='Foobar')

@baz.command()
@click.argument('age', type=int)
def aaa(age: int):
    click.echo(type(age))
    # click.echo(f'Hello there, {name}')



if __name__ == '__main__':
    # @baz.add_command(aaa)
    # baz()
    baz()