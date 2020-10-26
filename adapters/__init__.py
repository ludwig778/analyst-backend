from analyst.settings import INVESTING_CONFIG, REDIS_CONFIG

from .datareaders import alpha_vantage, yahoo
from .datareaders.manager import DataReaderManager
from .investing import InvestingAdapter
from .redis import RedisAdapter

investing = InvestingAdapter(**INVESTING_CONFIG)
redis = RedisAdapter(**REDIS_CONFIG)

datareaders = DataReaderManager(
    yahoo,
    alpha_vantage
)
