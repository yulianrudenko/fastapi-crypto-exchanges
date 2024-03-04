import json
import logging
import asyncio
import aiohttp
import websockets

from abc import ABC, abstractmethod
from crypto_pair import normalize_pair


AVAILABLE_CLIENTS = ["binance", "kraken"]


class BaseExchangeClient(ABC):
    """
    Base Exchange client for connecting to WS API and receiving data
    """
    ws_url: str = None
    api_exchange_pairs_url: str | None = None

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pairs_data: dict[str, float] = {}

    @property
    def cls_name(self) -> str:
        """
        Get the name of the client class (for logging)
        """
        return f"{self.__class__.__name__}"

    @staticmethod
    def normalize_pair_name(pair: str, exchange: str) -> str:
        """
        Normalize the pair name to a common format.

        Example: BTC/USDT ---> BTCUSDT 
        """
        return normalize_pair(symbol=pair, exchange=exchange)

    @abstractmethod
    async def start_connection(self):
        """Connect to single Exchange WebSocket URL to receive real-time data (symbol and sell/buy price to calculate average)"""
        pass


class BinanceClient(BaseExchangeClient):
    ws_url = "wss://stream.binance.com:9443/ws/!ticker@arr"
    api_exchange_pairs_url = None

    async def start_connection(self):
        async with websockets.connect(self.ws_url) as websocket:
            self.logger.info(f"{self.cls_name}: Successfully subscribed to price updates.")
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                for item in data:
                    if "s" in item.keys():
                        symbol = self.normalize_pair_name(pair=item["s"], exchange="binance")
                        buy_price = float(item["b"])
                        sell_price = float(item["a"])
                        avg_price = (buy_price + sell_price) / 2
                        self.pairs_data[symbol] = avg_price


class KrakenClient(BaseExchangeClient):
    ws_url = "wss://ws.kraken.com/ws"
    api_exchange_pairs_url = "https://api.kraken.com/0/public/AssetPairs"

    async def get_symbols(self) -> list[str]:
        """
        Fetch all available symbols on Kraken from the API.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_exchange_pairs_url) as response:
                    data = await response.json()
                pairs_data = list(data["result"].values())
                return [item["wsname"] for item in pairs_data]
        except Exception as e:
            self.logger.error(f"{self.cls_name}: Error while fetching symbols: {e}")
            return []

    async def start_connection(self):
        async with websockets.connect(self.ws_url) as websocket:
            try:
                available_symbols = await self.get_symbols()
                payload = {
                    "event": "subscribe",
                    "pair": available_symbols,
                    "subscription": {
                        "name": "ticker"
                    }
                }
                await websocket.send(json.dumps(payload))
                self.logger.info(f"{self.cls_name}: Successfully subscribed to price updates.")
            except Exception as err:
                self.logger.error(f"{self.cls_name}: Error during websocket subscription: {err}")
                return

            while True:
                response = await websocket.recv()
                data = json.loads(response)
                if type(data) is list:
                    symbol = self.normalize_pair_name(pair=data[-1], exchange="kraken")
                    sell_price = float(data[1]["a"][0])
                    buy_price = float(data[1]["b"][0])
                    avg_price = (sell_price + buy_price) / 2
                    self.pairs_data[symbol] = avg_price


async def run_clients_concurrently(clients: list[BaseExchangeClient]) -> None:
    """Run Exchange clients' connection tasks concurrently"""
    coroutines = [client.start_connection() for client in clients]
    await asyncio.gather(*coroutines)
