import aiohttp
import asyncio
import logging
import websockets
from aiofile import async_open
from websockets import WebSocketServerProtocol, WebSocketProtocolError
import names
from main import get_currency_data
import datetime
from aiopath import AsyncPath

logging.basicConfig(level=logging.INFO)


async def get_currency_history(days):
    currency_history = ""
    today = datetime.date.today()
    if days > 5:
        days = 5
    for i in range(days):
        date = today - datetime.timedelta(days=i)
        data = await get_currency_data(date.strftime("%d.%m.%Y"))

        eur_rate = None
        usd_rate = None

        for rate_data in data["exchangeRate"]:
            if rate_data["currency"] == "EUR":
                eur_rate = f"sale: {rate_data.get('saleRate')}, purchase: {rate_data.get('purchaseRate')}"

            elif rate_data["currency"] == "USD":
                usd_rate = f"sale: {rate_data.get('saleRate')}, purchase: {rate_data.get('purchaseRate')}"

        if eur_rate and usd_rate:
            exchange_rate = (
                f"({date.strftime('%d.%m.%Y')}): 'EUR': {eur_rate}; 'USD': {usd_rate};"
            )
            currency_history += exchange_rate

    return currency_history


def output(data):
    exchange_rate = ""
    date = datetime.date.today()

    eur_rate = None
    usd_rate = None

    for rate_data in data["exchangeRate"]:
        if rate_data["currency"] == "EUR":
            eur_rate = f"sale: {rate_data.get('saleRate')}, purchase: {rate_data.get('purchaseRate')}"

        elif rate_data["currency"] == "USD":
            usd_rate = f"sale: {rate_data.get('saleRate')}, purchase: {rate_data.get('purchaseRate')}"

    if eur_rate and usd_rate:
        exchange_rate += (
            f"{date.strftime('%d.%m.%Y')}: 'EUR': {eur_rate}; 'USD': {usd_rate};"
        )

    return exchange_rate


async def log(message, data):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"{current_time} - {message}: ({data})\n"
    async with async_open(AsyncPath("server_log"), "a", encoding="utf-8") as fr:
        await fr.write(formatted_message)


def parser(message):
    splited = message.split()
    msg = splited[0]
    args = splited[1] if len(splited) > 1 else None
    if args:
        args = int(args)
    return msg, args


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f"{ws.remote_address} connects")

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} disconnects")

    async def send_to_clients(self, message: str):
        import json

        message = json.dumps(message)
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distribute(ws)
        except WebSocketProtocolError as err:
            logging.error(err)
        finally:
            await self.unregister(ws)

    async def distribute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            msg, args = parser(message)
            if msg == "exchange":

                if args is None:
                    today = datetime.date.today()
                    m = await get_currency_data(today.strftime("%d.%m.%Y"))
                    m = output(m)
                else:
                    m = await get_currency_history(args)
                await log(message, m)
                await self.send_to_clients(m)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, "localhost", 8080):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
