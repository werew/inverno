"""
Config
"""

from typing import List, Dict, Optional, Generator, Any
from collections import defaultdict
import csv
from datetime import datetime
import yaml
import pandas as pd
import numpy as np
import dateutil.parser
from .price import Price, Currency
from .transaction import Transaction, TransactionAction
from .holding import Holding


class Config:
    """ Utility class representing a yaml project config """

    def __init__(self, path: str):
        with open(path) as fd:
            self._cfg = yaml.load(fd, Loader=yaml.SafeLoader)
        self._transactions = None
        self._prices = None
        self._holding_to_currency = {}

    def _get_opt(self, name: str) -> Any:
        opt = {}
        if "options" in self._cfg:
            opt = self._cfg["options"]
        return opt.get(name)

    @property
    def days(self) -> int:
        """ Number of days to analyse """
        return self._get_opt("days") or 90

    @property
    def currency(self) -> Currency:
        """ Base currency to use """
        curr = self._get_opt("currency")
        if curr is None:
            return Currency.USD
        return Currency[curr]

    @property
    def transactions(self) -> List[Transaction]:
        """ All transactions ever done (random order) """
        if self._transactions is None:
            self._transactions = self._load_transactions()
        return self._transactions

    def transactions_by_holding(
        self, holding: Holding
    ) -> Generator[Transaction, None, None]:
        """ All transactions ever done for the given holding """
        for trs in self.transactions:
            if holding.match_transaction(transaction=trs):
                yield trs

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

    def _find_matching_entry(self, config_section: List[Dict], holding: Holding):
        for entry in config_section:
            if not isinstance(entry, dict) or "match" not in entry:
                raise ValueError("Expected a matching list")
            if not isinstance(entry["match"], dict):
                raise ValueError("A match section must contain key,value pairs")

            if self._match_holding(match_section=entry["match"], holding=holding):
                return entry

    def _get_prices_file(self, holding: Holding) -> Optional[str]:
        # If prices are provided use those (missing values are interpolated)
        if "prices" not in self._cfg:
            return

        if not isinstance(self._cfg["prices"], list):
            raise ValueError("Prices section must contain a matching list")

        match = self._find_matching_entry(
            config_section=self._cfg["prices"], holding=holding
        )

        if match is None:
            return

        if "file" not in match:
            raise ValueError("Prices entries must contain a file field")

        return match["file"]

    def _find_matching_holding(
        self, match_section: Dict, holdings: List[Holding]
    ) -> Holding:
        if not isinstance(match_section, dict):
            raise ValueError("Expected a matching list")

        for holding in holdings:
            if self._match_holding(match_section=match_section, holding=holding):
                return holding

    def get_meta_attributes(self, holdings: List[Holding]) -> defaultdict:
        """
        Gets all meta attributes for the given list of holdings
        The returned attrs dict is structured as follows:
          attrs[<attribute name>][<entry>][<holding key>] = x
        where 0 < x <= 1.

        For instance, a meta attr "type: equity" will result in:
          attrs["type"]["equity"][<holding key>] = 1
        """
        attrs = defaultdict(lambda: defaultdict(dict))

        meta = self._cfg.get("meta")
        if meta is None:
            return attrs

        for entry in meta:
            if not isinstance(entry, dict) or "match" not in entry:
                raise ValueError("Expected a matching list")

            holding = self._find_matching_holding(entry["match"], holdings=holdings)
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

    def get_currency(self, holding: Holding) -> Optional[Currency]:
        """ Currency for the given holding (if provided) """
        path = self._get_prices_file(holding=holding)
        if path is None:
            return

        with open(path) as csvfile:
            for row in csv.DictReader(csvfile):
                price = Price.from_str(price=row["price"])
                return price.currency

    def get_prices(
        self, holding: Holding, start: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """ Prices history for the given holding (if provided) """

        path = self._get_prices_file(holding=holding)
        if path is None:
            return

        index = pd.date_range(start=start, end=datetime.now(), freq="D")
        prices = pd.Series(index=index, dtype=np.float64)
        prices.name = holding.get_key()

        with open(path) as csvfile:
            for row in csv.DictReader(csvfile):
                date = dateutil.parser.parse(row["date"], dayfirst=True)
                price = Price.from_str(price=row["price"])

                if start is None or date >= start:
                    prices[date] = price.amount

        return prices

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

    def _load_transactions_standard(self, filename: str) -> List[Transaction]:
        trs = []
        with open(filename) as csvfile:
            for row in list(csv.DictReader(csvfile)):
                date = dateutil.parser.parse(row["date"], dayfirst=True)
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

    def _load_transactions(self) -> List[Transaction]:
        transactions = []

        if "transactions" not in self._cfg:
            return transactions

        for entry in self._cfg["transactions"]:
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

        return list(sorted(transactions, key=lambda trs: trs.date))
