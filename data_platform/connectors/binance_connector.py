import pandas as pd
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BinanceConnector:
    """
    Standardized adapter for fetching OHLCV data from Binance.
    """
    BASE_URL = "https://api.binance.com/api/v3/klines"

    def fetch_historical_data(self, symbol: str, interval: str, limit: int = 1000) -> pd.DataFrame:
        """Fetches historical klines and formats them into a standard DataFrame."""
        logger.info(f"Fetching {limit} bars of {interval} data for {symbol}...")

        params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()

        # Standardize columns for the QTS architecture
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])

        # Clean and type-cast
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)

        return df[["timestamp", "open", "high", "low", "close", "volume"]].set_index("timestamp")