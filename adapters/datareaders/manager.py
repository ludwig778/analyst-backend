import pandas as pd

from .exceptions import NoDataAvailable, SymbolNotFound, TooMuchApiCall


class DataReaderManager(object):
    def __init__(self, *adapters):
        self.adapters = adapters

    def get(self, symbol, asset_type=None):
        for adapter in self.adapters:
            if (
                (asset_type == "C" and adapter.name == "alpha_vantage") or
                (asset_type != "C" and adapter.name == "binance")
            ):
                continue

            try:
                df = adapter.get(symbol, asset_type=asset_type)
            except (NoDataAvailable, SymbolNotFound, TooMuchApiCall):
                continue

            if isinstance(df, pd.DataFrame) and not df.empty:
                df = df.loc["1970-01-01":]

                return adapter.name, df

        return None, None
