#!/usr/bin/env python3

import click, os, sys, asyncio, arrow
from enum import StrEnum, auto
from icecream import IceCreamDebugger
from sqlmodel import select
from datetime import datetime


ic = IceCreamDebugger(prefix='')

try:
    SCRIPTS_URL = os.environ.get('SCRIPTS_URL')
    sys.path.append(SCRIPTS_URL)
    
    from video.vidgrab.models import Video, async_session, Status
except KeyError as e:
    ic(e)


async def main():
    async with async_session() as session:
        # now = arrow.utcnow()
        # vid = Video(url='https://foo.bar', session=now.date(), status=Status.done, source='foo.bar')
        # session.add(vid)
        # await session.commit()
        # await session.refresh(vid)
        # ic(vid)

        stmt = select(Video)
        execdata = await session.exec(stmt)
        ic(execdata.all())
        # for i in execdata.all():
        #     ic(i.model_dump())


if __name__ == '__main__':
    asyncio.run(main())