from datetime import datetime, timedelta
import pandas as pd

from adapters import datareaders, investing

from .models import Asset, Index
from .utils.scrapper import check_prices_diff


def scrap_investing(show_indices=False, **kwargs):  # noqa: C901
    if show_indices:
        indices = investing.get_indices(bypass_filter=True)

        for indice_name, indice_data in sorted(indices.items(), key=lambda x: x[1]["country"]):
            print(f"{indice_data.get('country'):25s} \"{indice_name}\"")

        return

    indices = investing.get_indices(**kwargs)

    for indice_name, indice_data in indices.items():
        indice_url = indice_data.get("link")
        indice_country = indice_data.get("country")

        indice_asset = Asset.objects.filter(name=indice_name).first()
        if indice_asset and indice_asset.up_to_date():
            print(f"Index Asset {indice_name} already up to date")
        else:
            indice_asset_data = investing.get_asset(indice_data.get("link"))

            indice_asset_attrs = {
                "name": indice_name,
                "kind": "I",
                "country": indice_country,
                "init_source": "investing.com",
                "extra_data": indice_asset_data
            }

            if indice_asset:
                if indice_asset.update_values(**indice_asset_attrs):
                    print(f"Update Index Asset {indice_name}")
                else:
                    print(f"Index Asset {indice_name} already up to date")
            else:
                print(f"Create Index Asset {indice_name}")
                indice_asset = Asset.objects.create(**indice_asset_attrs)

        indice_attrs = {
            "name": indice_name,
            "asset": indice_asset,
            "country": indice_country,
            "init_source": "investing.com"
        }

        if indice := Index.objects.filter(name=indice_name).first():
            if indice.update_values(**indice_attrs):
                print(f"Update Index {indice_name}")
            else:
                print(f"Index {indice_name} already up to date")
        else:
            print(f"Create Index {indice_name}")
            indice = Index.objects.create(**indice_attrs)

        indice_components = []

        assets = investing.get_assets(indice_url)

        for asset_name, asset_data in assets.items():

            asset = Asset.objects.filter(name=asset_name).first()
            if asset and asset.up_to_date():
                print(f"Asset {asset_name} already up to date")
            else:
                asset_extra_data = investing.get_asset(asset_data.get("link"))
                asset_data.update(asset_extra_data)

                asset_attrs = {
                    "name": asset_name,
                    "kind": asset_data.get("kind"),
                    "country": asset_data.get("country"),
                    "init_source": "investing.com",
                    "extra_data": asset_data
                }

                if asset:
                    if asset.update_values(**asset_attrs):
                        print(f"Update Asset {asset_name}")
                    else:
                        print(f"Asset {asset_name} already up to date")
                else:
                    print(f"Create Asset {asset_name}")
                    asset = Asset.objects.create(**asset_attrs)

            indice_components.append(asset)

        old_indice_components = list(indice.components.all())

        for old_component in old_indice_components:
            if old_component not in indice_components:
                print(f"{indice}: Removing {old_component}")

        for component in indice_components:
            if component not in old_indice_components:
                print(f"{indice}: Adding {component}")

        if set(indice_components) != set(old_indice_components):
            print(f"Saving indice new components on {indice}")
            indice.components.set(indice_components)
            indice.save()


def scrap_values():  # noqa: C901
    for asset in Asset.objects.all():
        dataframe = asset.dataframe

        if (
            isinstance(dataframe, pd.DataFrame) and
            dataframe.last("d").index.to_pydatetime()[0] > datetime.now() - timedelta(days=3)
        ):
            print(f"Dataframe up to date : {asset.name}")
            continue

        ticker = asset.ticker
        pending_ticker = None

        if not ticker:
            pending_ticker = asset.extra_data.get("pending_ticker")

            invalid_tickers = asset.extra_data.get("invalid_tickers") or ()
            if (
                not pending_ticker or
                pending_ticker in invalid_tickers
            ):
                print(f"No tickers           : {asset.name}")
                continue

        ticker = ticker or pending_ticker

        source, df = datareaders.get(ticker, asset.kind)

        if not source:
            if pending_ticker:
                asset.extra_data.setdefault("invalid_tickers", [])

                if pending_ticker not in asset.extra_data["invalid_tickers"]:
                    asset.extra_data["invalid_tickers"].append(pending_ticker)
                    asset.save()

            continue

        if pending_ticker:
            # Check between investing.com prices and the one retrieved
            last_close_stored = asset.extra_data.get("close")
            last_close = df.iloc[-1].close

            if not check_prices_diff(last_close, last_close_stored):
                print(f"Prices don't match   : {asset.name} ({last_close};{last_close_stored})")

                asset.extra_data.setdefault("invalid_tickers", [])

                if pending_ticker not in asset.extra_data["invalid_tickers"]:
                    asset.extra_data["invalid_tickers"].append(pending_ticker)
                    asset.save()

                continue

            asset.update_values(ticker=ticker)

        asset.update_values(data_source=source)
        asset.store_dataframe(df)

        print(f"Dataframe stored     : {asset.name}")
