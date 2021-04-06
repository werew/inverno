from typing import Dict, List, Set
from datetime import datetime
import csv
import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from .transaction import Transaction, TransactionAction
from .balance import Balance
from .price import Price
from .holding import Holding


class Project:
    def __init__(self, config: str):
        with open(config) as fd:
            cfg = yaml.load(fd, Loader=yaml.SafeLoader)
            self.transactions = self._load_transactions(config=cfg)
            self.balances = self._process_transactions()
            self.meta = cfg["meta"]
            self._prices = self._get_prices()

    def get_meta_attributes(self) -> Set[str]:
        attrs = set()
        for entry in self.meta:
            for attribute in entry["apply"]:
                attrs.add(attribute)
        return attrs

    def _get_prices(self):
        # Collect holdngs and earliest date
        holdings = {}
        for balance in self.balances:
            for holding in balance.holdings.values():
                if holding.get_key() not in holdings:
                    holdings[holding.get_key()] = {
                        "date": balance.date,
                        "holding": holding,
                    }
        prices = []
        for _, entry in holdings.items():
            price_history = self._get_holding_price(
                start=entry["date"], holding=entry["holding"]
            )
            if price_history is not None:
                prices.append(price_history)

        # Put all together in a single dataframe
        prices = pd.concat(prices, axis=1, join="outer")

        # Use linear interpolation to cover NaNs
        prices = prices.interpolate(method="linear", axis=0)

        return prices

    def _get_holding_price(self, start: datetime, holding: Holding):
        # If prices are provided use those (missing values are interpolated)
        # TODO

        # Try to fetch prices from Yahoo Finance
        if holding.ticker is not None:
            ticker = yf.Ticker(holding.ticker)
            prices = ticker.history(start=start, interval="1d")["Close"]
            prices.name = holding.get_key()
            if prices.size > 0:
                return prices

        # Try to infer from transaction data
        index = pd.date_range(start=start, end=datetime.now(), freq="D")
        prices = pd.Series([np.nan] * index.size, index=index)
        prices.name = holding.get_key()

        cnt = 0
        for trs in self.transactions:
            if not holding.match_transaction(transaction=trs) or trs.price is None:
                continue
            prices[trs.date] = trs.price.amount
            cnt += 1

        if cnt > 2:
            return prices

    def _process_transactions(self) -> List[Transaction]:
        if not self.transactions:
            return []

        balances = []

        start_date = self.transactions[0].date
        last_balance = Balance(date=start_date)

        for trs in self.transactions:
            last_balance = last_balance.process_transaction(trs)
            balances.append(last_balance)

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
