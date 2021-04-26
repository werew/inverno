from typing import Dict, List
from datetime import datetime
from collections import defaultdict
import shutil
import tempfile
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as ani
import yfinance as yf
from forex_python.converter import CurrencyRates
from jinja2 import Environment, PackageLoader, select_autoescape
from .transaction import TransactionAction
from .balance import Balance
from .price import Price, Currency
from .common import log_info, log_warning
from .holding import Holding, holdings_currencies
from .config import Config


class Project:
    def __init__(self, config: str):

        self.cfg = Config(path=config)

        self._dst_currency_rates = CurrencyRates().get_rates(self.cfg.currency.name)

        # Maps holdings to their currency
        self._holding_to_currency = {}

        self.balances = self._get_balances()
        self._first_holdings = self._get_first_holdings()
        self._prices = self._get_prices()
        self._allocations = self._get_allocations()
        self._money_balances = self._allocations.sum(axis=1)
        self._earnings = self._get_earnings()
        self._meta = self.cfg.get_meta_attributes(self._first_holdings)
        self.gen_report(dst="./qwe")

    def _normalize_currency(self, price: Price):
        rate = self._dst_currency_rates.get(price.currency.name)
        if rate is None:
            raise ValueError(f"Unsupported currency {price.currency.name}")
        return price.amount / rate

    def _get_earnings(self):
        earnings = self._money_balances.copy()

        for trs in self.cfg.transactions:
            if trs.action == TransactionAction.CASH:
                rows = earnings.loc[trs.date :]
                delta = self._normalize_currency(trs.amount)
                earnings.loc[trs.date :] = rows.add(-delta)
            elif trs.action == TransactionAction.VEST:
                rows = earnings.loc[trs.date :]
                price = self._prices.loc[trs.date :][trs.get_holding_key()].iloc[0]
                delta = trs.quantity * price  # TODO convert currency
                earnings.loc[trs.date :] = rows.add(-delta)

        return earnings

    def gen_report(self, dst: str):
        # First we copy the html dir into a tmp folder
        src = os.path.join(os.path.dirname(__file__), "html")
        tmp_dst = tempfile.TemporaryDirectory(suffix="." + __package__)
        shutil.copytree(src=src, dst=tmp_dst.name, dirs_exist_ok=True)

        tmp_balances_view = self._money_balances.iloc[-self.cfg.days :]
        balances = {
            "data": tmp_balances_view.values.tolist(),
            "labels": [d.strftime("%d %b %Y") for d in tmp_balances_view.index],
        }

        tmp_earnings_view = self._earnings.iloc[-self.cfg.days :]
        earnings_start = tmp_earnings_view.iloc[0]
        tmp_earnings_view = tmp_earnings_view.add(-earnings_start)
        earnings = {
            "data": tmp_earnings_view.values.tolist(),
            "labels": [d.strftime("%d %b %Y") for d in tmp_earnings_view.index],
        }

        meta_reports = self._gen_all_meta_reports(report_dir=tmp_dst.name)

        jinja_env = Environment(
            loader=PackageLoader("inverno", "html"),
            autoescape=select_autoescape(["html", "xml"]),
        )

        index_path = os.path.join(tmp_dst.name, "index.html")
        index_template = jinja_env.get_template(name="index.html")
        index_template.stream(
            meta_reports=meta_reports, balances=balances, earnings=earnings
        ).dump(index_path)

        # The report is ready, move it to dst
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(dst))
        shutil.move(src=tmp_dst.name, dst=dst)

    def _gen_all_meta_reports(self, report_dir: str) -> Dict[str, Dict]:
        reports = {}
        for attr in self._meta:
            log_info(f"Generating report for attribute {attr}")
            reports[attr] = []

            df = self._gen_meta_attr_df(attribute=attr)

            # Allocation
            allocation = df.tail(1).values.tolist()[0]
            reports[attr].append(
                {
                    "type": "piechart",
                    "name": "Allocation",
                    "data": allocation,
                    "labels": list(df.columns),
                }
            )

            # Allocation history
            src = os.path.join("media", f"{attr}_plot_anim.mp4")
            plot_anim_path = os.path.join(report_dir, src)
            self._gen_animated_plot(df=df, dst=plot_anim_path)
            reports[attr].append(
                {"type": "video", "name": "Allocation history", "src": src}
            )

        return reports

    def _gen_meta_attr_df(self, attribute: str):

        columns = list(self._meta[attribute]) + ["unknown"]
        df = pd.DataFrame(
            0, columns=columns, index=self._allocations.index, dtype=np.float64
        )

        # Keep record of how much we allocate for each holding
        tot_holdings = defaultdict(lambda: 0)

        # Compute holdings allocations
        for entry, values in self._meta[attribute].items():
            for holding_key, portion in values.items():
                df[entry] += portion * self._allocations[holding_key]
                tot_holdings[holding_key] += portion

        # Cumpute unknown allocations
        for holding_key in self._first_holdings:
            allocation = tot_holdings[holding_key]

            if allocation > 1:
                raise ValueError(
                    f"Holding {holding_key} has more than 100% allocation for attribute {attribute}"
                )

            elif allocation == 1:
                continue

            df["unknown"] += self._allocations[holding_key] * (1 - allocation)
        return df

    def _gen_animated_plot(self, df: pd.DataFrame, dst: str):
        fig = plt.figure()
        plt.xticks(rotation=45, ha="right", rotation_mode="anchor")
        plt.subplots_adjust(bottom=0.2, top=0.9)
        colors = ["red", "green", "blue", "orange"]

        frames = min(self.cfg.days, df.index.size)
        frames = 10  # TODO rm
        start = df.index.size - frames

        def update_frame(i):
            plt.legend(df.columns)
            p = plt.plot(df[start : start + i].index, df[start : start + i].values)
            for i in range(len(df.columns)):
                p[i].set_color(colors[i % len(colors)])

        animator = ani.FuncAnimation(fig, update_frame, frames=frames, interval=300)
        animator.save(dst, fps=10)

    def _get_first_holdings(self):
        # Collect holdngs and earliest date
        holdings = {}
        for balance in self.balances.values():
            for holding in balance.holdings.values():
                if holding.get_key() not in holdings:
                    holdings[holding.get_key()] = {
                        "date": balance.date,
                        "holding": holding,
                    }
        return holdings

    def _get_allocations(self):

        # New dataframe with the same layout of prices
        allocations = pd.DataFrame().reindex_like(self._prices)
        cash = pd.DataFrame(columns=["cash"], index=allocations.index, dtype=np.float64)

        for balance in self.balances.values():
            # Populate holdings columns
            for holding in balance.holdings.values():
                allocations.loc[balance.date, holding.get_key()] = holding.quantity

            # Populate cash dataframe
            total_cash = 0.0
            for c in balance.cash.values():
                total_cash += self._normalize_currency(c)
            cash.loc[balance.date, "cash"] = total_cash

        # Fill empty slot using previous known values
        allocations = allocations.interpolate(method="pad", axis=0)
        cash = cash.interpolate(method="pad", axis=0)

        # Apply prices
        allocations *= self._prices

        # For each column, apply conversion rate to USD
        # TODO select currency
        for key in self._first_holdings:
            currency = holdings_currencies.get(key)
            if currency is None:
                raise ValueError(f"Couldn't determine currency for holding {key}")

            rate = self._dst_currency_rates.get(currency.name)
            if rate is None:
                raise ValueError(f"Unsupported currency {currency.name}")

            allocations[key] /= rate

        # Return holdings allocations including cash
        return pd.concat([allocations, cash], axis=1).fillna(0)

    def _get_prices(self):
        prices = []
        for _, entry in self._first_holdings.items():
            price_history = self._get_holding_prices(
                start=entry["date"], holding=entry["holding"]
            )
            if price_history is not None:
                prices.append(price_history)

        # Put all together in a single dataframe
        prices = pd.concat(prices, axis=1, join="outer")

        # Use linear interpolation to cover NaNs
        # TODO make interpolation optional
        prices = prices.interpolate(method="time", axis=0, limit_direction="both")

        return prices

    def _get_currencies(self):
        currencies = {}
        for holding in self._first_holdings:
            # Try from prices
            c = self.cfg.get_currency(holding=holding)
            if c is not None:
                currencies[holding.get_key()] = c
                continue

            # Try from Yahoo Finance
            ticker = yf.Ticker(holding.ticker)
            try:
                c = Currency[ticker.info['currency']]
                currencies[holding.get_key()] = c
            except KeyError:
                pass

            # Try from transactions
            for trs in self.cfg.transactions_by_holding(holding=holding):
                if trs.price is not None:
                    currencies[holding.get_key()] = trs.price.currency

        return currencies


    def _get_holding_prices(self, start: datetime, holding: Holding):

        prices = self.cfg.get_prices(holding=holding, start=start)
        if prices is not None:
            log_info(f"Using user-provided prices for {holding.get_key()}")
            return prices

        # Try to fetch prices from Yahoo Finance
        if holding.ticker is not None:
            ticker = yf.Ticker(holding.ticker)
            prices = ticker.history(start=start, interval="1d")["Close"]
            prices.name = holding.get_key()
            if prices.size > 0:
                log_info(f"Using Yahoo Finance prices for {holding.get_key()}")
                return prices

        # Try to infer from transaction data
        log_warning(
            f"Inferring prices from transactions for {holding.get_key()}"
            ", prices could be inaccurate"
        )
        index = pd.date_range(start=start, end=datetime.now(), freq="D")
        prices = pd.Series(index=index, dtype=np.float64)
        prices.name = holding.get_key()

        for trs in self.cfg.transactions_by_holding(holding=holding):
            if trs.price is None:
                continue
            prices[trs.date] = trs.price.amount

        return prices

    def _get_balances(self) -> Dict[datetime, Balance]:
        if not self.cfg.transactions:
            return {}

        balances = {}

        start_date = self.cfg.transactions[0].date
        last_balance = Balance(date=start_date)

        for trs in self.cfg.transactions:
            last_balance = last_balance.process_transaction(trs)
            balances[last_balance.date] = last_balance

        return balances
