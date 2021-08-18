from typing import Dict
from datetime import datetime
import shutil
import tempfile
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as ani
import yfinance as yf
from currency_converter import CurrencyConverter
from jinja2 import Environment, PackageLoader
from .balance import Balance
from .price import Currency, Price
from .common import log_info, log_warning
from .holding import Holding
from .analysis import Analysis
from .config import Config


class Project:
    """
    Root class for handling a project and the creation of a report
    """

    def __init__(self, config: str):

        self.cfg = Config.from_file(path=config)

        # Conversion rates to the dest currency
        self._dst_currency_rates = self._get_currency_rates(self.cfg.currency.name)

        # Balances after each transaction (max one balance per day)
        self.balances = Balance.get_balances(transactions=self.cfg.transactions)

        # For each holding identity (key) this list contains the
        # first one ever hold
        self._first_holdings = self._get_first_holdings()

        # Maps holdings to their currency
        self._holding_to_currency = self._get_currencies()

        # Daily prices for every holding
        self._prices = self._get_prices()

        # All meta attributes
        self._meta = self.cfg.get_meta_attributes(
            [h["holding"] for h in self._first_holdings.values()]
        )

        # Adding dummy attribute holdings
        self._meta["holdings"] = {
            h["holding"].get_key(): {h["holding"].get_key(): 1.0}
            for h in self._first_holdings.values()
        }

    def _get_currency_rates(self, currency: str) -> Dict[str, float]:
        cc = CurrencyConverter()
        rates = {currency: 1.0}
        for cu in cc.currencies:
            try:
                rates[cu] = cc.convert(1, currency, cu)
            except Exception:
                pass
        return rates

    def _get_attrs_report_data(self, analysis: Analysis, allocations: pd.DataFrame):
        reports = []
        for attr in self._meta:
            log_info(f"Generating report for attribute {attr}")
            reports.append({"name": attr.capitalize(), "reports": []})

            attr_alloc = analysis.get_attr_allocations(
                allocations=allocations, attr=attr, attr_weights=self._meta[attr],
            )

            # Get current allocation from last (more recent) row
            last_alloc = attr_alloc.tail(1).values.tolist()[0]
            reports[-1]["reports"].append(
                {
                    "type": "piechart",
                    "name": "Allocation",
                    "data": last_alloc,
                    "labels": list(attr_alloc.columns),
                    "help": "Shows how much is allocated for each type in the portfolio.",
                }
            )

            # Allocation history
            reports[-1]["reports"].append(
                {
                    "type": "areachart_stacked",
                    "name": "Allocation history",
                    "datasets": [
                        {"label": c, "data": attr_alloc[c].tolist()}
                        for c in attr_alloc.columns
                    ],
                    "labels": [d.strftime("%d %b %Y") for d in attr_alloc.index],
                    "show_legend": True,
                    "help": "Full history of allocations.",
                }
            )

            # Earnings
            earnings = analysis.get_attr_earnings(
                attr_allocations=attr_alloc,
                transactions=self.cfg.transactions,
                attr_weights=self._meta[attr],
            )
            earnings_perc = (earnings / attr_alloc) * 100
            earnings_perc.replace([np.inf, -np.inf], np.nan, inplace=True)
            earnings_perc = earnings_perc.fillna(0.0)

            reports[-1]["reports"].append(
                {
                    "type": "multi",
                    "name": "Earnings",
                    "help": "Earnings growth for each type adjusted for cash flow.",
                    "reports": [
                        {
                            "type": "areachart",
                            "name": "Value",
                            "datasets": [
                                {"label": c, "data": earnings[c].tolist()}
                                for c in earnings.columns
                            ],
                            "labels": [d.strftime("%d %b %Y") for d in earnings.index],
                            "show_legend": True,
                        },
                        {
                            "type": "areachart",
                            "name": "Percentage (%)",
                            "datasets": [
                                {"label": c, "data": earnings_perc[c].tolist()}
                                for c in earnings_perc.columns
                            ],
                            "labels": [
                                d.strftime("%d %b %Y") for d in earnings_perc.index
                            ],
                            "show_legend": True,
                            "format": "percent",
                        },
                    ],
                }
            )

        return sorted(reports, key=lambda r: r["name"].lower() != "holdings")

    def _get_report_data(self):
        analysis = Analysis(
            prices=self._prices,
            conv_rates=self._dst_currency_rates,
            holdings_currencies=self._holding_to_currency,
        )

        # Balances graph
        allocations = analysis.get_allocations(
            balances=self.balances.values(), ndays=self.cfg.days
        )
        balances = {
            "datasets": [
                {
                    "label": "Balance",
                    "data": allocations.sum(axis=1).values.tolist(),
                },
            ],
            "labels": [d.strftime("%d %b %Y") for d in allocations.index],
        }

        # Earning graph
        earnings_s = analysis.get_earnings(
            allocations=allocations,
            transactions=self.cfg.transactions,
            ndays=self.cfg.days,
        )

        benchmarks = self._get_benchmarks(
            start=self.cfg.start_date,
            end=self.cfg.end_date,
        )
        earnings = {
            "datasets": [
                {
                    "label": "Earnings",
                    "data": earnings_s.values.tolist(),

                },
                *[ { "label": k, "data": v.values.tolist()} for k,v in benchmarks.items() ]
            ],
            "labels": [d.strftime("%d %b %Y") for d in earnings_s.index],
        }

        # Generate report data for all known attributes
        attrs_report = self._get_attrs_report_data(
            analysis=analysis, allocations=allocations
        )

        # Rate of return
        ror = analysis.get_ror(allocations, earnings_s)

        # Current number of holdings
        nb_holdings = (allocations.iloc[-1] > 0).sum()

        return {
            "balances": balances,
            "earnings": earnings,
            "attrs": attrs_report,
            "ror": ror,
            "nb_holdings": nb_holdings,
        }

    def gen_report(self, dst: str):
        """ Create an html report at the given destination """

        # First we copy the html dir into a tmp folder
        src = os.path.join(os.path.dirname(__file__), "html")
        tmp_dst = tempfile.TemporaryDirectory(suffix="." + __package__)
        shutil.copytree(src=src, dst=tmp_dst.name, dirs_exist_ok=True)

        # This is the data that we will feed to the report
        report_data = self._get_report_data()

        # Generate report
        jinja_env = Environment(
            loader=PackageLoader("inverno", "html"),
            # autoescape=select_autoescape(["html", "xml"]),
            autoescape=True,
        )

        index_path = os.path.join(tmp_dst.name, "index.html")
        index_template = jinja_env.get_template(name="index.html")
        index_template.stream(
            cfg=self.cfg,
            attrs=report_data["attrs"],
            balance=Price(
                currency=self.cfg.currency,
                amount=report_data["balances"]["datasets"][0]["data"][-1],
            ).to_string(),
            earnings_amount=Price(
                currency=self.cfg.currency,
                amount=report_data["earnings"]["datasets"][0]["data"][-1],
            ).to_string(),
            ror=f"{report_data['ror']*100: .2f}",
            nb_holdings=report_data["nb_holdings"],
            balances=report_data["balances"],
            earnings=report_data["earnings"],
            transactions=sorted(
                self.cfg.transactions, key=lambda t: t.date, reverse=True
            ),
        ).dump(index_path)

        # Move report to dst
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(dst))
        shutil.move(src=tmp_dst.name, dst=dst)

    def _gen_animated_plot(self, df: pd.DataFrame, dst: str):
        fig = plt.figure()
        plt.xticks(rotation=45, ha="right", rotation_mode="anchor")
        plt.subplots_adjust(bottom=0.2, top=0.9)
        colors = [
            "red",
            "green",
            "blue",
            "orange",
            "black",
            "violet",
            "brown",
            "yellow",
            "purple",
        ]

        frames = min(self.cfg.days, df.index.size)
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

    def _get_prices(self):
        prices = []
        end_date = self.cfg.end_date
        for _, entry in self._first_holdings.items():
            price_history = self._get_holding_prices(
                start=entry["date"], end=end_date, holding=entry["holding"]
            )
            if price_history is not None:
                if all([np.isnan(p) for p in price_history.tail(7)]):
                    log_warning(
                        "Most recent price is older than one "
                        f"week for {entry['holding'].get_key()}"
                    )
                prices.append(price_history)

        # Put all together in a single dataframe
        prices = pd.concat(prices, axis=1, join="outer")

        # Use linear interpolation to cover NaNs
        prices = prices.interpolate(method="time", axis=0, limit_direction="both")

        return prices

    def _get_currencies(self):
        currencies = {}
        for entry in self._first_holdings.values():
            holding = entry["holding"]
            log_info(f"Getting currency for {holding.get_key()}")

            # Try from transactions
            for trs in self.cfg.transactions_by_holding(holding=holding):
                if trs.price is not None:
                    currencies[holding.get_key()] = trs.price.currency
                    break

            if holding.get_key() in currencies:
                continue

            # Try from prices
            c = self.cfg.get_currency(holding=holding)
            if c is not None:
                currencies[holding.get_key()] = c
                continue

            # Try from Yahoo Finance
            if holding.ticker is not None:
                ticker = yf.Ticker(holding.ticker)
                try:
                    c = Currency[ticker.info["currency"]]
                    currencies[holding.get_key()] = c
                    continue
                except KeyError:
                    pass

            raise ValueError(f"Couldn't determine currency for {holding.get_key()}")

        return currencies

    def _get_benchmarks(self, start: datetime, end: datetime):
        def _reindex(s: pd.Series):
            s = s.add(-s.iloc[0])
            return s.reindex(
                index=pd.date_range(s.index.min(), s.index.max()),
                method="pad",
            )

        benchmarks = {}

        # S&P 500
        ticker = yf.Ticker("^GSPC")
        prices = ticker.history(start=start, end=end, interval="1d")["Close"]
        if prices.size > 0:
            benchmarks["S&P 500"] = _reindex(prices)

        # DJIA
        ticker = yf.Ticker("^DJI")
        prices = ticker.history(start=start, end=end, interval="1d")["Close"]
        if prices.size > 0:
            benchmarks["DJIA"] = _reindex(prices)
            

        # NASDAQ
        ticker = yf.Ticker("^IXIC")
        prices = ticker.history(start=start, end=end, interval="1d")["Close"]
        if prices.size > 0:
            benchmarks["NASDAQ"] = _reindex(prices)

        # Russel 2000 
        ticker = yf.Ticker("^RUT")
        prices = ticker.history(start=start, end=end, interval="1d")["Close"]
        if prices.size > 0:
            benchmarks["Russell 2000"] = _reindex(prices)

        return benchmarks

    def _get_holding_prices(
        self, start: datetime, end: datetime, holding: Holding
    ) -> pd.Series:
        def _reindex(s: pd.Series):
            return s.reindex(
                index=pd.date_range(s.index.min(), s.index.max()),
                method="pad",
            )

        prices = self.cfg.get_prices(holding=holding, start=start, end=end)
        if prices is not None:
            log_info(f"Using user-provided prices for {holding.get_key()}")
            return _reindex(prices)

        # Try to fetch prices from Yahoo Finance
        if holding.ticker is not None:
            ticker = yf.Ticker(holding.ticker)
            prices = ticker.history(start=start, end=end, interval="1d")["Close"]
            prices.name = holding.get_key()
            if prices.size > 0:
                log_info(f"Using Yahoo Finance prices for {holding.get_key()}")
                return _reindex(prices)

        # Try to infer from transaction data
        log_warning(
            f"Inferring prices from transactions for {holding.get_key()}"
            ", prices could be inaccurate"
        )
        index = pd.date_range(start=start, end=end, freq="D")
        prices = pd.Series(index=index, dtype=np.float64)
        prices.name = holding.get_key()

        for trs in self.cfg.transactions_by_holding(holding=holding):
            if trs.price is None:
                continue
            prices[trs.date] = trs.price.amount

        return _reindex(prices)
