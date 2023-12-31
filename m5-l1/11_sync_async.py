import asyncio

from typing import Iterable, Awaitable, List

from faker import Faker

from libs import async_timed

fake = Faker()


async def get_user_async(uid: int) -> dict:
    await asyncio.sleep(0.5)
    return {'id': uid, 'name': fake.name(), 'company': fake.company(), 'email': fake.email()}


def get_users(uids: List[int]) -> Iterable[Awaitable]:
    return [get_user_async(i) for i in uids]


@async_timed()
async def main(users: Iterable[Awaitable]):
    return await asyncio.gather(*users)


if __name__ == '__main__':
    uids = [1, 2, 3]
    r = asyncio.run(main(get_users(uids)))
    print(r)