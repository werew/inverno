from enum import Enum
from typing import Optional, Union, Dict
import re
from functools import total_ordering


class Currency(Enum):
    USD = "$"
    GBP = "£"
    EUR = "€"
    TWD = "NT$"


@total_ordering
class Price:
    """
    A monetary price, including a currency and a positive amount.
    Providing a negative amount will result in an error (note that we only allow
    positive amounts for safety reasons, if you are really in need of representing
    negative amounts depending on your use case you should associate some meta info to
    the price, for example for cash transactions this is done with CASH_OUT vs CASH_IN)
    """
    def __init__(self, currency: Currency, amount: float):
        self.currency = currency
        self.amount = amount

    @property
    def amount(self) -> float:
        return self._amount

    @amount.setter
    def amount(self, amount: float):
        if amount < 0:
            raise ValueError(("Price can only be positive"))
        self._amount = abs(amount)
    
    @staticmethod
    def from_str(price: str, currency: Optional[Currency] = None, expect_negative=False) -> "Price":
        match = re.search(r"[\d\.,]+", price)
        if match is None:
            raise ValueError(f'Cannot find valid price in string "{price}"')
        amount = float(match.group().replace(",", ""))
        if price.strip().startswith("-"):
            amount = -amount

        if currency is None:
            for known_currency in Currency:
                for symbol in [known_currency.name, known_currency.value]:
                    if symbol in price:
                        currency = known_currency
                        break

                if currency is not None:
                    break

            if currency is None:
                raise ValueError(f"Couldn't get currency for price {str}")

        if expect_negative:
            if amount > 0:
                raise ValueError(f"Expected a negative value")
            amount = - amount
        return Price(currency=currency, amount=amount)

    def normalize_currency(self, conversion_rates: Dict[str,float]) -> float:
        """ Convert price to dest currency """
        rate = conversion_rates.get(self.currency.name)
        if rate is None:
            raise ValueError(f"Unsupported currency {self.currency.name}")
        return self.amount / rate

    def to_string(self):
        return f"{self.currency.value}{self.amount :,.2f}"

    def __repr__(self):
        return self.to_string()

    def __add__(self, other: Union["Price", float]):
        if isinstance(other, float):
            return Price(currency=self.currency, amount=self.amount + other)
        elif isinstance(other, Price):
            if self.currency != other.currency:
                raise ValueError("Prices have different currencies")
            return Price(currency=self.currency, amount=self.amount + other.amount)
        raise ValueError(f"Incompatible type {type(other)}")

    def __sub__(self, other: Union["Price", float]):
        if isinstance(other, float):
            return Price(currency=self.currency, amount=self.amount - other)
        elif isinstance(other, Price):
            if self.currency != other.currency:
                raise ValueError("Prices have different currencies")
            return Price(currency=self.currency, amount=self.amount - other.amount)
        raise ValueError(f"Incompatible type {type(other)}")

    def __mul__(self, other: Union["Price", float]):
        if isinstance(other, float):
            return Price(currency=self.currency, amount=self.amount * other)
        elif isinstance(other, Price):
            if self.currency != other.currency:
                raise ValueError("Prices have different currencies")
            return Price(currency=self.currency, amount=self.amount * other.amount)
        raise ValueError(f"Incompatible type {type(other)}")

    def __eq__(self, other: Union["Price", float]):
        if isinstance(other, float):
            return self.amount == other
        elif isinstance(other, Price):
            if self.currency != other.currency:
                raise ValueError("Prices have different currencies")
            return self.amount == other.amount
        raise ValueError(f"Incompatible type {type(other)}")

    def __lt__(self, other: Union["Price", float]):
        if isinstance(other, float):
            return self.amount < other
        elif isinstance(other, Price):
            if self.currency != other.currency:
                raise ValueError("Prices have different currencies")
            return self.amount < other.amount
        raise ValueError(f"Incompatible type {type(other)}")
