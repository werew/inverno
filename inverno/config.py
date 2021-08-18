"""
Config
"""

from typing import List, Dict, Optional, Generator, Any
from collections import defaultdict
from enum import Enum
import os
import csv
import datetime
import yaml
import pandas as pd
import numpy as np
import dateutil.parser
from .price import Price, Currency
from .transaction import Transaction, TransactionAction
from .holding import Holding

class ConfKeys(Enum):
    OPTIONS = "options"
    PRICES = "prices"
    META = "meta"
    TRANSACTIONS = "transactions"
    INCLUDE = "include"



class Config:
    """ Utility class representing a yaml project config """

    def __init__(self, cfg: str, path=None):
        self._cfg = yaml.load(cfg, Loader=yaml.SafeLoader)
        self._transactions = None
        self._prices = None
        self._holding_to_currency = {}
        self._files_provided = {}
        self._path = path

        self._load_includes()

    def _load_includes(self):
        for path in (self._cfg.get(ConfKeys.INCLUDE.value) or []):
            cfg_str = self._read_file(path=path)
            cfg = Config(cfg=cfg_str, path=path)
            self.merge(cfg=cfg)

    @staticmethod
    def from_file(path: str):
        """ Create Config object from file """
        with open(path) as fd:
            return Config(cfg=fd.read(), path=path)

    def merge(self, cfg: "Config"):
        self._cfg[ConfKeys.OPTIONS.value] = {
            **(cfg._cfg.get(ConfKeys.OPTIONS.value) or {}),
            **(self._cfg.get(ConfKeys.OPTIONS.value) or {}),
        }

        self._cfg[ConfKeys.META.value] = [
            *(cfg._cfg.get(ConfKeys.META.value) or []),
            *(self._cfg.get(ConfKeys.META.value) or []),
        ]

        self._cfg[ConfKeys.TRANSACTIONS.value] = [
            *(cfg._cfg.get(ConfKeys.TRANSACTIONS.value) or []),
            *(self._cfg.get(ConfKeys.TRANSACTIONS.value) or []),
        ]

        self._cfg[ConfKeys.PRICES.value] = [
            *(cfg._cfg.get(ConfKeys.PRICES.value) or []),
            *(self._cfg.get(ConfKeys.PRICES.value) or []),
        ]



    def provide_file(self, path: str, content: str):
        """
        Use this method if instead of reading from a path
        contained in the config you would like to provide
        directly the content of the file.
        This is similar to mocking.
        """
        self._files_provided[path] = content

    def _read_file(self, path: str) -> str:
        if not os.path.isabs(path) and self._path is not None:
            path = os.path.join(os.path.dirname(self._path), path)

        if path in self._files_provided:
            return self._files_provided[path]
        with open(path) as fd:
            return fd.read()

    def _get_opt(self, name: str) -> Any:
        opt = {}
        if ConfKeys.OPTIONS.value in self._cfg:
            opt = self._cfg[ConfKeys.OPTIONS.value]
        return opt.get(name)

    @property
    def title(self) -> int:
        """ Title of the project """
        return self._get_opt("title") or "Unnamed Project"

    @property
    def days(self) -> int:
        """ Number of days to analyse """
        return self._get_opt("days") or 90

    @property
    def end_date(self) -> datetime.datetime:
        """ When to stop the analysis """
        date_opt = self._get_opt("end_date")
        if date_opt is None:
            return datetime.datetime.now()

        return dateutil.parser.parse(date_opt, dayfirst=True)

    @property
    def start_date(self) -> datetime.datetime:
        """ When to start the analysis """
        return self.end_date - datetime.timedelta(days=self.days)

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
            (m.get(t) is None or m[t].strip() == getattr(h, t))
            and (m.get(i) is None or m[i].strip() == getattr(h, i))
            and (m.get(n) is None or m[n].strip() == getattr(h, n))
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

    def _get_meta_attributes_apply(
        self, attrs: Dict, holding: Holding, apply: Dict
    ) -> defaultdict:
        holding_key = holding.get_key()

        for attr, val in apply.items():

            # Apply has the precendence over everything else.
            # If this attribute was already set, remove it.
            for holdings_alloc in attrs[attr].values():
                if holding_key in holdings_alloc:
                    del holdings_alloc[holding_key]

            if isinstance(val, str):
                attrs[attr][val][holding_key] = 1

            elif isinstance(val, dict):
                for k, v in val.items():
                    v = float(v.strip("%")) / 100.0
                    attrs[attr][k][holding_key] = v

    def _get_meta_attributes_composition(
        self, attrs: Dict, holding: Holding, holdings: List[Holding], composition: Dict
    ) -> defaultdict:
        # Collect all sub holdings
        sub_holdings = {}

        def _collect_by(field: str):
            if field not in composition:
                return

            if not isinstance(composition[field], dict):
                raise ValueError("Components must be key value pairs")

            for val, percentage in composition[field].items():

                # Try to find holding among known holdings
                sub_holding = self._find_matching_holding(
                    {field: val},
                    holdings,
                )

                if sub_holding is None:
                    sub_holding = self._find_matching_holding(
                        {field: val},
                        self._collect_holdings_from_meta(),
                    )

                if sub_holding is None:
                    continue

                sub_holdings[sub_holding.get_key()] = {
                    "holding": sub_holding,
                    "percentage": float(percentage.strip("%")) / 100.0,
                }

        _collect_by("name")
        _collect_by("ticker")
        _collect_by("isin")

        sub_holding_attrs = self.get_meta_attributes(
            [s["holding"] for s in sub_holdings.values()]
        )
        for attr, entries in sub_holding_attrs.items():
            for entry, holdings_alloc in entries.items():
                for holding_key, sub_alloc_percentage in holdings_alloc.items():
                    old_val = attrs[attr][entry].get(holding.get_key()) or 0.0
                    attrs[attr][entry][holding.get_key()] = old_val + (
                        sub_holdings[holding_key]["percentage"] * sub_alloc_percentage
                    )

    def _collect_holdings_from_meta(self) -> List[Holding]:
        holdings = []
        meta = self._cfg.get("meta") or []

        for entry in meta:
            m = entry["match"]
            name, ticker, isin = None, None, None

            if "name" in m:
                name = m["name"]

            if "ticker" in m:
                ticker = m["ticker"]

            if "isin" in m:
                isin = m["isin"]

            holdings.append(Holding(name=name, ticker=ticker, isin=isin))
        return holdings

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
                continue

            if "composition" in entry:
                self._get_meta_attributes_composition(
                    attrs=attrs,
                    holding=holding,
                    holdings=holdings,
                    composition=entry["composition"],
                )

            if "apply" in entry:
                self._get_meta_attributes_apply(
                    attrs=attrs, holding=holding, apply=entry["apply"]
                )

        return attrs

    def get_currency(self, holding: Holding) -> Optional[Currency]:
        """ Currency for the given holding (if provided) """
        path = self._get_prices_file(holding=holding)
        if path is None:
            return

        for row in csv.DictReader(self._read_file(path)):
            price = Price.from_str(price=row["price"])
            return price.currency

    def get_prices(
        self,
        holding: Holding,
        start: datetime.datetime,
        end: Optional[datetime.datetime] = None,
    ) -> Optional[pd.DataFrame]:
        """ Prices history for the given holding (if provided) """

        path = self._get_prices_file(holding=holding)
        if path is None:
            return

        if end is None:
            end = self.end_date

        index = pd.date_range(start=start, end=end, freq="D")
        prices = pd.Series(index=index, dtype=np.float64)
        prices.name = holding.get_key()

        for row in csv.DictReader(self._read_file(path).split("\n")):
            date = dateutil.parser.parse(row["date"], dayfirst=True)
            price = Price.from_str(price=row["price"])

            if date >= start and date <= end:
                prices[date] = price.amount

        return prices

    def _load_transactions_schwab(self, filename: str) -> List[Transaction]:
        trs = []

        csvfile = self._read_file(filename).split("\n")

        # skip first line, which contains the document title
        csvfile = csvfile[1:]

        # skip last line, which contains the total
        for row in list(csv.DictReader(csvfile))[:-1]:
            # dates are sometime expressed as "mm/dd/yyyy as of mm/dd/yyy"
            # in which case we pick the first date
            date_str = row["Date"].split(" ")[0]
            date = datetime.datetime.strptime(date_str, "%m/%d/%Y")

            action = TransactionAction.from_schwab_action(row["Action"])

            price_str = row["Price"]
            price = Price.from_str(price_str) if price_str else None

            fees_str = row["Fees & Comm"]
            fees = Price.from_str(fees_str) if fees_str else None

            quantity_str = row["Quantity"]
            quantity = float(quantity_str) if quantity_str else None

            amount_str = row["Amount"]
            if amount_str:
                if action == TransactionAction.TAX or action == TransactionAction.BUY:
                    amount = Price.from_str(amount_str, expect_negative=True)
                else:
                    amount = Price.from_str(amount_str)
            else:
                amount = None

            trs.append(
                Transaction(
                    action=action,
                    date=date,
                    ticker=row["Symbol"] or None,
                    name=row["Description"] or None,
                    price=price,
                    quantity=quantity,
                    fees=fees,
                    amount=amount,
                )
            )
        return trs

    def _load_transactions_standard(self, filename: str) -> List[Transaction]:
        trs = []
        for row in list(csv.DictReader(self._read_file(filename).split("\n"))):
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
                    name=row["name"] or None,
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

        transactions = filter(lambda trs: trs.date <= self.end_date, transactions)
        return list(sorted(transactions, key=lambda trs: trs.date))
