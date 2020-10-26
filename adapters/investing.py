import logging
import re

from datetime import datetime
from time import sleep

from bs4 import BeautifulSoup
from cached_property import cached_property
from requests import Session

logger = logging.getLogger(__name__)


unit_dict = {"K": 3, "M": 6, "B": 9, "T": 12}


def float_parsing(string):
    return float(string.replace(",", "").replace(" ", ""))


def parse_unit(string):
    number, prefix = string[0:-1], string[-1]
    number = number.replace(",", "")
    return int(float(number)) * (10 ** unit_dict[prefix])


def integer_parsing(string):
    if any(map(lambda x: x in string, unit_dict.keys())):
        return parse_unit(string)

    return int(string.replace(",", "").replace(" ", ""))


def first_element(elements):
    return float(elements.split()[0])


def capital_parsing(cap):
    return parse_unit(cap)


PARSING_DICT = {
    "Dividend (Yield)": {
        "replace": "dividend",
        "func": first_element,
        "default": 0.0
    },
    "Beta": {
        "replace": "beta",
        "func": float_parsing,
        "default": 0.0
    },
    "EPS": {
        "replace": "eps",
        "func": float_parsing,
        "default": 0.0
    },
    "Shares Outstanding": {
        "replace": "shares",
        "func": integer_parsing,
        "default": 0
    },
    "Market Cap": {
        "replace": "cap",
        "func": capital_parsing,
        "default": 0
    },
    "Prev. Close": {
        "replace": "close",
        "func": float_parsing,
        "default": 0.0
    }
}


class CouldNotFindTicker(Exception):
    pass


class NoTickerDataFound(Exception):
    pass


class InvestingAdapter(object):

    def __init__(self, url=None, config=None, session=None):
        self.url = url
        self.config = config

        if session:
            self.session = session
        else:
            self.session = Session()
            self.session.headers["User-Agent"] = "Mozilla/5.1"

        self.last_call = None

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

        if delta < 10:
            sleep(10 - delta)

        self.last_call = datetime.now()

    def get_full_url(self, url):
        return self.url + url

    def get_soup(self, endpoint):
        data = self.session.get(self.url + endpoint)

        self._wait_before_call()

        return BeautifulSoup(data.content, "html.parser")

    def is_allowed(self, data, filter_key=None, bypass_filter=False, **kwargs):
        if self.config and filter_key and not bypass_filter:
            filter_dict = self.config.get(filter_key, {})

            include = filter_dict.get("include", {})
            exclude = filter_dict.get("exclude", {})

            if exclude != {} and any(self.check_filter(data, exclude)):
                return False
            elif include != {} and any(self.check_filter(data, include)):
                return True
            elif include == {} and exclude == {}:
                return True

            return False

        return True

    @staticmethod
    def check_filter(data, condition):
        return [
            data.get(arg) in values
            for arg, values in condition.items()
            if values
        ]

    def parse_span(self, tr_item):
        tds = tr_item.findAll("td")
        country = tds[0].span.attrs["title"]
        link = tds[1].a.attrs["href"]
        name = tds[1].a.text.replace(";", "")

        return {
            "name": name,
            "link": link,
            "country": country
        }

    @cached_property
    def indices(self):
        return self.get_indices()

    def get_indices(self, **kwargs):
        indices = {}

        soup = self.get_soup("/indices/major-indices")
        indices_data = (
            soup.find(id="cross_rates_container")
            .find("tbody")
            .findAll("tr")
        )

        for indice_data in indices_data:
            indice = self.parse_span(indice_data)

            if self.is_allowed(indice, filter_key="indice", **kwargs):
                indices[indice["name"]] = indice

        return indices

    def get_assets(self, indice_url):
        return self._get_assets(indice_url)

    def _get_assets(self, indice_url, page_num=None):
        assets = {}

        full_indice_url = f"{indice_url}-components"
        if page_num:
            full_indice_url += f"/{page_num}"

        soup = self.get_soup(full_indice_url)
        assets_data = (
            soup.find(id="marketInnerContent")
            .find("tbody")
            .findAll("tr")
        )

        for asset_data in assets_data:
            asset = self.parse_span(asset_data)

            if self.is_allowed(asset, filter_key="asset"):
                assets[asset["name"]] = asset

        if not page_num and (pagination := soup.find(id="paginationWrap")):
            page_nums = pagination.findAll("a", attrs={"class": "pagination"})
            for page_num in range(2, len(page_nums) + 1):
                assets.update(self._get_assets(
                    indice_url,
                    page_num=page_num
                ))

        return assets

    @staticmethod
    def parse_extra_list(soup):
        extra_dict = {}
        extra_list = soup.find("div", attrs={"class": "overviewDataTable"})

        if not extra_list:
            return {}

        for div in extra_list.findAll("div"):
            spans = div.findAll("span")
            key = spans[0].text
            value = spans[1].text

            if parsing_conf := PARSING_DICT.get(key):
                if "n/a" in value.lower():
                    extra_dict[parsing_conf["replace"]] = parsing_conf["default"]
                else:
                    extra_dict[parsing_conf["replace"]] = parsing_conf["func"](value)

        return extra_dict

    @staticmethod
    def get_ticker_datas(soup):
        ticker = None

        ticker_list = soup.find(id="DropdownSiblingsTable")
        if ticker_list:
            for tr_item in ticker_list.findAll("tr")[1:]:
                tds = tr_item.findAll("td")
                ticker = tds[1].a.text
                currency = tds[3].text

                if ticker.isdigit():
                    continue

                return {
                    "pending_ticker": ticker,
                    "currency": currency
                }
        else:
            instrument = soup.findAll(
                "div",
                attrs={"class": "instrumentHead"}
            )
            if instrument:
                indice_text = instrument[0].h1.text
                splitted = re.split(r"\(|\)", indice_text)
                if len(splitted) > 1:
                    ticker = splitted[-2]
                else:
                    ticker = indice_text.split()[0]

        return {"pending_ticker": ticker}

    def get_asset(self, asset_url):
        sleep(10)
        soup = self.get_soup(asset_url)
        ticker_data = self.get_ticker_datas(soup)

        if "indices" in asset_url:
            kind = "I"
            if "pending_ticker" in ticker_data:
                ticker_data["pending_ticker"] = "^" + ticker_data["pending_ticker"]
        elif "currencies" in asset_url:
            kind = "F"
        elif "equities" in asset_url:
            kind = "S"
        else:
            raise NotImplementedError("For url: %s" % asset_url)

        extra_data = self.parse_extra_list(soup)

        return {
            **ticker_data,
            **extra_data,
            "link": asset_url,
            "kind": kind
        }
