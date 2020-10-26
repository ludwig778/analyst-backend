from analyst.settings import PRICE_DIFF_ALLOWED


def check_prices_diff(last_close, last_close_stored, diff_allowed=PRICE_DIFF_ALLOWED):
    """
    Return True if the 2 prices are in the allowed range
    """
    return (
        last_close * diff_allowed < last_close_stored and
        last_close / diff_allowed > last_close_stored
    )
