from analyst.settings import ALPHA_VANTAGE_CONFIG

from .alpha_vantage import AlphaVantageAdapter
from .yahoo import YahooAdapter

alpha_vantage = AlphaVantageAdapter(**ALPHA_VANTAGE_CONFIG)
yahoo = YahooAdapter()
