import logging

from datetime import date, datetime, timedelta
from time import sleep

import pandas as pd
import requests

from .exceptions import NoDataAvailable, SymbolNotFound, TooMuchApiCall

logger = logging.getLogger(__name__)


class AlphaVantageAdapter(object):
    name = "alpha_vantage"

    def __init__(self, url=None, key=None):
        self.url = url
        self.key = key
        self.session = requests.Session()
        self.last_call = None
        self.available_at = None

    def _is_available(self):
        if self.available_at is not None:
            if datetime.now() < self.available_at:
                return False

            self.available_at = None

        return True

    def _wait_before_call(self):
        """
        To avoid reaching the api call limit
        for there are only 5 requests allowed by minutes
        """
        if not self.last_call:
            self.last_call = datetime.now()

            return

        now = datetime.now()
        delta = (now - self.last_call).seconds

        if delta < 12:
            sleep(12 - delta)

        self.last_call = datetime.now()

    def _build_dataframe(self, data):
        """
        Build a generic dataframe with a daily datetime index
        with float values
        """
        df = pd.DataFrame(data).T
        df.index = pd.to_datetime(df.index)

        df = (
            df
            .rename(columns={
                "1. open": "open",
                "2. high": "high",
                "3. low": "low",
                "4. close": "close",
                "5. adjusted close": "adj_close",
                "6. volume": "volume"
            })
            .drop(
                ["7. dividend amount", "8. split coefficient"],
                axis=1
            )
            .sort_index()
            .applymap(lambda v: float(v))
        )

        return df

    def _build_url_query(self, symbol, asset_type, freq="DAILY", full=True, interval="60min"):
        """
        Build url query to hit the specified symbol resource
        """
        output_size = 'full' if full else 'compact'

        if asset_type == "F":
            from_symbol, to_symbol = symbol.split("/")
            url_query = (
                f"{self.url}/query?function=FX_{freq}&from_symbol={from_symbol}&"
                f"to_symbol={to_symbol}&outputsize={output_size}&apikey={self.key}"
            )
        elif asset_type in ("S", "I"):
            url_query = (
                f"{self.url}/query?function=TIME_SERIES_{freq}_ADJUSTED&symbol={symbol}&"
                f"outputsize={output_size}&apikey={self.key}"
            )

        if freq == "INTRADAY":
            url_query += f"&interval={interval}"

        return url_query

    def get(self, symbol, asset_type=None, **kwargs):
        """
        Get the latest data for the specified symbol
        """
        if not self._is_available():
            return

        if not asset_type:
            logger.error("No asset_type argument set")
            raise Exception("asset_type must be set")

        url_query = self._build_url_query(symbol, asset_type, **kwargs)

        self._wait_before_call()

        ret = self.session.get(url_query)

        if not ret.ok:
            logger.error(f"No data available for {symbol} ({ret.reason})")
            raise NoDataAvailable(symbol)

        ret_json = ret.json()

        if ret_json.get("Error Message"):
            logger.error(f"Symbol {symbol} not found")
            raise SymbolNotFound(symbol)

        elif ret_json.get("Note"):
            # Set the next time the api will be available
            self.available_at = datetime.combine(
                date.today() + timedelta(days=1),
                datetime.min.time()
            )

            logger.error("Too much api calls")
            raise TooMuchApiCall(symbol)

        if asset_type == "F":
            data = ret_json.get("Time Series FX (Daily)")
        elif asset_type in ("S", "I"):
            data = ret_json.get("Time Series (Daily)")

        if data:
            df = self._build_dataframe(data)

            df = (
                df[["adj_close"]]
                .rename({"adj_close": "close"}, axis=1)
            )

            return df
        else:
            logger.error(f"No data available for {symbol}")
            raise NoDataAvailable(symbol)
