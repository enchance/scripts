#!/usr/bin/env python3

import click, os, sys, asyncio, arrow
from enum import StrEnum, auto
from icecream import IceCreamDebugger
from sqlmodel import select
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv



try:
    path = Path(__file__).resolve().parent.parent.parent    # scripts/scripts
    load_dotenv(dotenv_path=os.path.join(path, '.env'))
    sys.path.append(os.environ.get('SCRIPTS_URL'))

    from utils.utils import command_config, group_config
except KeyError as e:
    sys.exit(1)

__version__ = '0.1.0'
__prog_name__ = 'Vidgrab'
ic = IceCreamDebugger(prefix='')

try:
    SCRIPTS_URL = os.environ.get('SCRIPTS_URL')
    sys.path.append(SCRIPTS_URL)

    from video.vidgrab.models import Video, async_session, Status
except KeyError as e:
    ic(e)


@click.group(**group_config, invoke_without_command=True)
@click.version_option(version=__version__, prog_name=__prog_name__)
def cli():
    pass


@cli.command(**group_config, help='Add urls')
def add():
    pass


@cli.command(**command_config, help='Show active sessions')
@click.option('--activate', '-a', help='Activate session based on its ID', type=click.BOOL, default=False)
def session(activate: bool):
    # List active sessions
    pass


@cli.command(**command_config, help='Show whitelisted domains')
@click.argument('urls', nargs=-1)
@click.option('-l', type=click.BOOL, help='List all whitelisted domains', default=False)
def whitelist(urls: tuple[str], l: bool):     # noqa
    ic(l)


# async def main():
#     async with async_session() as session:
#         # now = arrow.utcnow()
#         # vid = Video(url='https://foo.bar', session=now.date(), status=Status.done, source='foo.bar')
#         # session.add(vid)
#         # await session.commit()
#         # await session.refresh(vid)
#         # ic(vid)
#
#         stmt = select(Video)
#         execdata = await session.exec(stmt)
#         ic(execdata.all())
#         # for i in execdata.all():
#         #     ic(i.model_dump())


if __name__ == '__main__':
    cli()