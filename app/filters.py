from fastapi import Query, HTTPException, status

from .exchange_clients import AVAILABLE_CLIENTS


async def pair_filter(
    pair: str | None = Query(
        default=None,
        title="Pair",
        description="Name of the pair to retrieve price for"
    )
) -> str:
    """Proccess pair"""
    return pair


async def exchange_filter(
    exchange: str | None = Query(
        default=None,
        title="Exchange",
        description="Name of the exchange to retrieve data from (Binance or Kraken)"
    )
) -> str:
    """
    Make sure provided exchange is valid string and is supported by API.
    """
    if exchange is not None:
        exchange = exchange.strip().lower()
        if exchange not in AVAILABLE_CLIENTS:
            raise HTTPException(detail="Unsupported exchange.", status_code=status.HTTP_400_BAD_REQUEST)
        return exchange
