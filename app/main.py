import asyncio
import logging

from fastapi import FastAPI, Depends

from .exchange_clients import (
    BinanceClient,
    KrakenClient,
    run_clients_concurrently
)
from .filters import exchange_filter, pair_filter


app = FastAPI()
logging.basicConfig(level=logging.INFO)
task = None
clients = {
    "binance": BinanceClient(),
    "kraken": KrakenClient(),
}


@app.on_event("startup")
async def startup():
    """
    Start WS connections for data receiving via Exchange clients
    """
    global task
    task = asyncio.create_task(run_clients_concurrently(clients=clients.values()))


@app.on_event("shutdown")
async def shutdown():
    """
    Disable asyncio task, stop running clients
    """
    global task
    if task is not None:
        task.cancel()



@app.get("/api/prices", responses={
    200: {
        "content": {
            "application/json": {
                "example": {
                    "binance": {
                        "ETH/BTC": 0.055075,
                        "BNB/BTC": 0.006651499999999999,
                    },
                    "kraken": {
                        "GAS/BTC": 0.0001162,
                        "ETH/USDT": 3426.0550000000003
                    }
                }
            }
        }
    },
    400: {
        "description": "Invalid exchange provided",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Unsupported exchange"
                }
            }
        }
    }
})
async def get_prices(
    pair: str | None = Depends(pair_filter),
    exchange: str | None = Depends(exchange_filter)
):
    """
    Main endpoint to fetch data for any currency pair from the exchanges.

    If neither the pair nor the exchange is specified, display all prices from both exchanges.

    If only the exchange is specified, show all prices from that particular exchange.

    If both the exchange and pair are specified, display prices for the specified pair.
    """

    if exchange is not None:
        if pair is not None:
            # Display prices for the specified pair on specified exchanged
            return {exchange: {pair: clients[exchange].pairs_data.get(pair, None)}}

        # Show all prices from particular exchange
        return {exchange: clients[exchange].pairs_data}

    # Display all prices from both exchanges
    return {client: clients[client].pairs_data for client in clients}
