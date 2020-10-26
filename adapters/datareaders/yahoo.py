import logging

from pandas_datareader._utils import RemoteDataError
from pandas_datareader.data import DataReader

from .exceptions import SymbolNotFound

logger = logging.getLogger(__name__)


class YahooAdapter(object):
    name = "yahoo"

    def get(self, symbol, asset_type=None, **kwargs):
        """
        Get the latest data for the specified symbol
        """
        if not asset_type:
            logger.error("No asset_type argument set")
            raise Exception("asset_type must be set")

        if asset_type == "F":
            symbol = symbol.replace("/", "") + "=X"

        try:
            df = DataReader(symbol, "yahoo", start="1950-01-01", **kwargs)
        except (RemoteDataError, KeyError):
            logger.error(f"Symbol {symbol} not found")
            raise SymbolNotFound(symbol)

        df = (
            df
            .rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
                "Adj Close": "adj_close"
            })
            .sort_index()
        )

        df = (
            df[["adj_close"]]
            .rename({"adj_close": "close"}, axis=1)
        )

        return df
