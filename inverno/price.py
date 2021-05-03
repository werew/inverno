from enum import Enum
from typing import Optional, Union, Dict
import re
from functools import total_ordering


class Currency(Enum):
    USD = "$"
    GBP = "£"
    EUR = "€"


@total_ordering
class Price:
    def __init__(self, currency: Currency, amount: float):
        self.currency = currency
        self.amount = amount

    @staticmethod
    def from_str(price: str, currency: Optional[Currency] = None) -> "Price":
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

        return Price(currency=currency, amount=amount)

    def normalize_currency(self, conversion_rates: Dict[str,float]) -> float:
        """ Convert price to dest currency """
        rate = conversion_rates.get(self.currency.name)
        if rate is None:
            raise ValueError(f"Unsupported currency {self.currency.name}")
        return self.amount / rate

    def __repr__(self):
        return f"{self.amount} {self.currency.name}"

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
