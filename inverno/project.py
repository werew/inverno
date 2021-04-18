from typing import Dict, List
from datetime import datetime
from collections import defaultdict
import shutil
import tempfile
import os
import csv
import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import dateutil.parser
import matplotlib.animation as ani
from forex_python.converter import CurrencyRates
from jinja2 import Environment, PackageLoader, select_autoescape
from .transaction import Transaction, TransactionAction
from .balance import Balance
from .price import Price
from .holding import Holding, holdings_currencies


class Project:
    def __init__(self, config: str):
        with open(config) as fd:
            cfg = yaml.load(fd, Loader=yaml.SafeLoader)

            self.transactions = self._load_transactions(config=cfg)
            self.balances = self._get_balances()
            self._first_holdings = self._get_first_holdings()
            self._prices = self._get_prices(config=cfg)
            self._allocations = self._get_allocations()
            self._meta = self._parse_meta_attributes(config=cfg)
            self.gen_report(dst="./qwe")

    def gen_report(self, dst: str):
        # First we copy the html dir into a tmp folder
        src = os.path.join(os.path.dirname(__file__), "html")
        tmp_dst = tempfile.TemporaryDirectory(suffix="." + __package__)
        shutil.copytree(src=src, dst=tmp_dst.name, dirs_exist_ok=True)

        meta_reports = self._gen_all_meta_reports(report_dir=tmp_dst.name)

        jinja_env = Environment(
            loader=PackageLoader("inverno", "html"),
            autoescape=select_autoescape(["html", "xml"]),
        )

        index_path = os.path.join(tmp_dst.name, "index.html")
        index_template = jinja_env.get_template(name="index.html")
        index_template.stream(meta_reports=meta_reports).dump(index_path)
        #index = index_template.render(meta_reports=meta_reports)

        # The report is ready, move it to dst
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(dst))
        shutil.move(src=tmp_dst.name, dst=dst)

    def _parse_meta_attributes(self, config: Dict) -> defaultdict:
        # This dict is structured as following:
        #  attrs[<attribute name>][<entry>][<holding key>] = x
        # where 0 < x <= 1
        attrs = defaultdict(lambda: defaultdict(dict))

        meta = config.get("meta")
        if meta is None:
            return attrs

        for entry in meta:
            if not isinstance(entry, dict) or "match" not in entry:
                raise ValueError("Expected a matching list")

            holding = self._find_matching_holding(entry["match"])
            if holding is None:
                raise ValueError(f"Couldn't find holding {entry['match']}")

            for attr, val in entry["apply"].items():
                if isinstance(val, str):
                    attrs[attr][val][holding.get_key()] = 1

                elif isinstance(val, dict):
                    for k, v in val.items():
                        v = float(v.strip("%")) / 100.0
                        attrs[attr][k][holding.get_key()] = v
        return attrs

    def _gen_all_meta_reports(self, report_dir: str) -> Dict[str,Dict]:
        reports = {}
        for attr in self._meta:
            reports[attr] = []

            # Allocation history
            df = self._gen_meta_attr_df(attribute=attr)
            src = os.path.join("media", f"{attr}_plot_anim.mp4")
            plot_anim_path = os.path.join(report_dir, src)
            self._gen_animated_plot(df=df, dst=plot_anim_path)
            reports[attr].append({'type': 'video', 'name': 'Allocation history', 'src': src})

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

    def _gen_animated_plot(self, df: pd.DataFrame, dst: str, days: int = 10):
        print("generating ", dst)
        fig = plt.figure()
        plt.xticks(rotation=45, ha="right", rotation_mode="anchor")
        plt.subplots_adjust(bottom=0.2, top=0.9)
        colors = ["red", "green", "blue", "orange"]

        frames = min(days, df.index.size)
        start = df.index.size - frames

        def update_frame(i):
            plt.legend(df.columns)
            p = plt.plot(df[start:start+i].index, df[start:start+i].values)
            for i in range(len(df.columns)):
                p[i].set_color(colors[i % len(colors)])

        animator = ani.FuncAnimation(
            fig, update_frame, frames=frames, interval=300
        )
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
        usd_rates = CurrencyRates().get_rates("USD")

        for balance in self.balances.values():
            # Populate holdings columns
            for holding in balance.holdings.values():
                allocations.loc[balance.date, holding.get_key()] = holding.quantity

            # Populate cash dataframe
            total_cash = 0.0
            for c in balance.cash.values():
                rate = usd_rates.get(c.currency.name)
                if rate is None:
                    raise ValueError(f"Unsupported currency {cash.currency.name}")
                total_cash += c.amount / rate
            cash.loc[balance.date, "cash"] = total_cash

        # Fill empty slot using previous known values
        allocations = allocations.interpolate(method="pad", axis=0)
        cash = cash.interpolate(method="pad", axis=0)

        # Apply prices
        allocations *= self._prices

        # For each column, apply conversion rate to USD
        for key in self._first_holdings:
            currency = holdings_currencies.get(key)
            if currency is None:
                raise ValueError(f"Couldn't determine currency for holding {key}")

            rate = usd_rates.get(currency.name)
            if rate is None:
                raise ValueError(f"Unsupported currency {currency.name}")

            allocations[key] /= rate

        # Return holdings allocations including cash
        return pd.concat([allocations, cash], axis=1).fillna(0)

    def _get_prices(self, config: Dict):
        prices = []
        for _, entry in self._first_holdings.items():
            price_history = self._get_holding_prices(
                config=config, start=entry["date"], holding=entry["holding"]
            )
            if price_history is not None:
                prices.append(price_history)

        # Put all together in a single dataframe
        prices = pd.concat(prices, axis=1, join="outer")

        # Use linear interpolation to cover NaNs
        prices = prices.interpolate(method="time", axis=0)

        return prices

    def _match_holding(self, match_section: Dict, holding: Holding) -> bool:
        if not isinstance(match_section, dict):
            raise ValueError("Expected a matching list")

        h = holding
        m = match_section
        t = "ticker"
        i = "isin"
        n = "name"

        return (
            (m.get(t) is not None and m[t].strip() == getattr(h, t))
            or (m.get(i) is not None and m[i].strip() == getattr(h, i))
            or (m.get(n) is not None and m[n].strip() == getattr(h, n))
        )

    def _find_matching_holding(self, match_section: Dict) -> Holding:
        if not isinstance(match_section, dict):
            raise ValueError("Expected a matching list")

        for entry in self._first_holdings.values():
            if self._match_holding(
                match_section=match_section, holding=entry["holding"]
            ):
                return entry["holding"]

    def _find_matching_entry(self, config_section: List[Dict], holding: Holding):
        for entry in config_section:
            if not isinstance(entry, dict) or "match" not in entry:
                raise ValueError("Expected a matching list")
            if not isinstance(entry["match"], dict):
                raise ValueError("A match section must contain key,value pairs")

            if self._match_holding(match_section=entry["match"], holding=holding):
                return entry

    def _try_get_holding_prices_from_cfg(
        self, config: Dict, start: datetime, holding: Holding
    ):
        # If prices are provided use those (missing values are interpolated)
        if "prices" not in config:
            return

        if not isinstance(config["prices"], list):
            raise ValueError("Prices section must contain a matching list")

        match = self._find_matching_entry(
            config_section=config["prices"], holding=holding
        )

        if match is None:
            return

        if "file" not in match:
            raise ValueError("Prices entries must contain a file field")

        index = pd.date_range(start=start, end=datetime.now(), freq="D")
        prices = pd.Series(index=index, dtype=np.float64)
        prices.name = holding.get_key()

        with open(match["file"]) as csvfile:
            for row in list(csv.DictReader(csvfile)):
                date = dateutil.parser.parse(row["date"], dayfirst=True)
                price = Price.from_str(price=row["price"])
                if date >= start:
                    prices[date] = price.amount

        return prices

    def _get_holding_prices(self, config: Dict, start: datetime, holding: Holding):

        prices = self._try_get_holding_prices_from_cfg(
            config=config, start=start, holding=holding
        )
        if prices is not None:
            return prices

        # Try to fetch prices from Yahoo Finance
        # if holding.ticker is not None:
        #    ticker = yf.Ticker(holding.ticker)
        #    prices = ticker.history(start=start, interval="1d")["Close"]
        #    prices.name = holding.get_key()
        #    if prices.size > 0:
        #        return prices

        # Try to infer from transaction data
        index = pd.date_range(start=start, end=datetime.now(), freq="D")
        prices = pd.Series(index=index, dtype=np.float64)
        prices.name = holding.get_key()

        for trs in self.transactions:
            if not holding.match_transaction(transaction=trs) or trs.price is None:
                continue
            prices[trs.date] = trs.price.amount

        return prices

    def _get_balances(self) -> Dict[datetime, Balance]:
        if not self.transactions:
            return {}

        balances = {}

        start_date = self.transactions[0].date
        last_balance = Balance(date=start_date)

        for trs in self.transactions:
            last_balance = last_balance.process_transaction(trs)
            balances[last_balance.date] = last_balance

        return balances

    def _load_transactions(self, config: Dict) -> List[Transaction]:
        transactions = []

        if "transactions" not in config:
            return transactions

        for entry in config["transactions"]:
            loader = entry["format"]
            if loader == "standard":
                transactions.extend(
                    self._load_transactions_standard(filename=entry["file"])
                )
            elif loader == "schwab":
                transactions.extend(
                    self._load_transactions_schwab(filename=entry["file"])
                )
            else:
                raise ValueError(f"Unsupported transactions' format {loader}")

        return sorted(transactions, key=lambda t: t.date)

    def _load_transactions_standard(self, filename: str) -> List[Transaction]:
        trs = []
        with open(filename) as csvfile:
            for row in list(csv.DictReader(csvfile)):
                date = datetime.strptime(row["date"], "%d/%m/%Y")
                action = TransactionAction(row["action"])
                price_str = row["price"]
                price = Price.from_str(price_str) if price_str else None

                fees_str = row["fees"]
                fees = Price.from_str(fees_str) if fees_str else None

                quantity_str = row["quantity"]
                quantity = float(quantity_str) if quantity_str else None

                amount_str = row["amount"]
                amount = Price.from_str(amount_str) if amount_str else None

                trs.append(
                    Transaction(
                        action=action,
                        date=date,
                        ticker=row["ticker"] or None,
                        name=row["name"],
                        price=price,
                        quantity=quantity,
                        fees=fees,
                        amount=amount,
                    )
                )
        return trs

    def _load_transactions_schwab(self, filename: str) -> List[Transaction]:
        trs = []
        with open(filename) as csvfile:
            # skip first line, which contains the document title
            next(csvfile, None)

            # skip last line, which contains the total
            for row in list(csv.DictReader(csvfile))[:-1]:
                # dates are sometime expressed as "mm/dd/yyyy as of mm/dd/yyy"
                # in which case we pick the first date
                date_str = row["Date"].split(" ")[0]
                date = datetime.strptime(date_str, "%m/%d/%Y")

                action = TransactionAction.from_schwab_action(row["Action"])

                price_str = row["Price"]
                price = Price.from_str(price_str) if price_str else None

                fees_str = row["Fees & Comm"]
                fees = Price.from_str(fees_str) if fees_str else None

                quantity_str = row["Quantity"]
                quantity = float(quantity_str) if quantity_str else None

                amount_str = row["Amount"]
                amount = Price.from_str(amount_str) if amount_str else None

                trs.append(
                    Transaction(
                        action=action,
                        date=date,
                        ticker=row["Symbol"] or None,
                        name=row["Description"],
                        price=price,
                        quantity=quantity,
                        fees=fees,
                        amount=amount,
                    )
                )
        return trs
