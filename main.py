import platform

import aiohttp
import datetime
import argparse
import asyncio


async def get_currency_data(date):
    async with aiohttp.ClientSession() as session:
        url = f"https://api.privatbank.ua/p24api/exchange_rates?json&date={date}"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    return data

                else:
                    print(f"Error status: {response.status} for {url}")
        except aiohttp.ClientConnectorError as err:
            print(f"Connection error: {url}", str(err))


async def get_currency_history(days):
    currency_history = []
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
                eur_rate = {
                    "sale": rate_data.get("saleRate"),
                    "purchase": rate_data.get("purchaseRate"),
                }
            elif rate_data["currency"] == "USD":
                usd_rate = {
                    "sale": rate_data.get("saleRate"),
                    "purchase": rate_data.get("purchaseRate"),
                }

        if eur_rate and usd_rate:
            exchange_rate = {
                date.strftime("%d.%m.%Y"): {"EUR": eur_rate, "USD": usd_rate}
            }
            currency_history.append(exchange_rate)

    return currency_history


async def get_specific_currency_history(days, currency_code):
    currency_history = []
    today = datetime.date.today()
    if days > 5:
        days = 5
    for i in range(days):
        date = today - datetime.timedelta(days=i)
        data = await get_currency_data(date.strftime("%d.%m.%Y"))

        for rate_data in data["exchangeRate"]:
            if rate_data["currency"] == currency_code:
                exchange_rate = {
                    date.strftime("%d.%m.%Y"): {
                        currency_code: {
                            "sale": rate_data.get("saleRate"),
                            "purchase": rate_data.get("purchaseRate"),
                        }
                    }
                }
                currency_history.append(exchange_rate)

    return currency_history


def main():
    parser = argparse.ArgumentParser(description="Get currency exchange rates history")
    parser.add_argument(
        "--days",
        "-d",
        type=int,
        required=True,
        help="Number of days to retrieve currency history",
    )
    parser.add_argument(
        "--currency",
        "-c",
        help="Currency to retrieve",
    )
    args = parser.parse_args()

    if args.currency:
        currency_history = asyncio.run(
            get_specific_currency_history(args.days, args.currency)
        )

    else:
        currency_history = asyncio.run(get_currency_history(args.days))

    for exchange_rate in currency_history:
        print(exchange_rate)


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
