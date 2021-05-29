from enum import Enum
from typing import Optional
from datetime import datetime
from .price import Price


class TransactionAction(Enum):
    BUY = "buy"
    SELL = "sell"
    VEST = "vest"
    TAX = "tax"
    DIV = "dividends"
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"
    SPLIT = "split"

    @staticmethod
    def from_schwab_action(action: str) -> "TransactionAction":
        action = action.lower()
        if action == "buy" or action == "reinvest shares":
            return TransactionAction.BUY
        elif action == "sell":
            return TransactionAction.SELL
        elif action == "stock plan activity":
            return TransactionAction.VEST
        elif action == "nra tax adj":
            return TransactionAction.TAX
        elif action == "foreign tax paid":
            return TransactionAction.TAX
        elif action == "qual div reinvest":
            return TransactionAction.DIV
        elif action == "qualified dividend":
            return TransactionAction.DIV
        raise ValueError(f'Cannot translate action "{action}"')


class Transaction:
    def __init__(
        self,
        action: TransactionAction,
        date: datetime,
        quantity: Optional[float] = None,
        price: Optional[Price] = None,
        ticker: Optional[str] = None,
        isin: Optional[str] = None,
        name: Optional[str] = None,
        fees: Optional[Price] = None,
        amount: Optional[Price] = None,
    ):
        self.action = action
        self.date = date
        self.quantity = None if quantity is None else abs(quantity)
        self.price = price
        self.fees = fees
        self.name = name
        self.ticker = ticker
        self.isin = isin
        self.amount = amount

        self._check_constraints()
        self._infer_missing_fields()

    def __str__(self):
        return f"Transaction: {self.date} {self.action.value} {self.name} {self.amount}"

    def get_holding_key(self):
        if (
            self.action != TransactionAction.BUY
            and self.action != TransactionAction.SELL
            and self.action != TransactionAction.VEST
            and self.action != TransactionAction.SPLIT
        ):
            raise ValueError(
                f"Cannot get holding key from transaction with action {self.action}"
            )

        # prioritize stronger identifiers
        if self.isin is not None:
            return self.isin
        elif self.ticker is not None:
            return self.ticker
        elif self.name is not None:
            return self.name
        raise ValueError("Cannot construct holding name")

    def _infer_missing_fields(self):
        if self.amount is None and self.quantity is not None and self.price is not None:
            fees = 0. if self.fees is None else self.fees
            self.amount = Price(
                currency=self.price.currency, amount=(self.quantity * self.price.amount) - fees
            )

    def _check_constraints(self):
        if self.quantity is not None and self.quantity <= 0:
            raise ValueError("Quantity must be > 0")

        if self.price is not None and self.price.amount <= 0:
            raise ValueError("Price must be > 0")

        if self.fees is not None and self.fees.amount <= 0:
            raise ValueError("Fees must be > 0")

        currency = None
        for price_arg in [self.price, self.fees, self.amount]:
            if price_arg is not None:
                if currency is None:
                    currency = price_arg.currency
                elif currency != price_arg.currency:
                    raise ValueError(
                        "Currency of price, fees and amount must be the same"
                    )

        if self.action == TransactionAction.BUY:
            self._check_constraints_buy()
        elif self.action == TransactionAction.SELL:
            self._check_constraints_sell()
        elif self.action == TransactionAction.VEST:
            self._check_constraints_vest()
        elif self.action == TransactionAction.TAX:
            self._check_constraints_tax()
        elif self.action == TransactionAction.CASH_IN:
            self._check_constraints_cash()
        elif self.action == TransactionAction.CASH_OUT:
            self._check_constraints_cash()
        elif self.action == TransactionAction.DIV:
            self._check_constraints_div()

    def _check_has_identifier(self):
        if not any([self.name, self.ticker, self.isin]):
            raise ValueError("Didn't find any valid identifier for transaction")

    def _check_constraints_buy(self):
        # Quantity must be set, default to one
        if self.quantity is None:
            self.quantity = 1

        # Buy transactions must have an identifier
        self._check_has_identifier()

        # Price must be set, or we should be able to fetch it
        if self.price is None and self.amount is None:
            raise ValueError("Price or amount must be set for buy/sell transactions")

        # Infer price from amount
        if self.price is None:
            self.price = Price(
                currency=self.amount.currency,
                amount=abs(self.amount.amount / self.quantity),
            )

        # Currency must be consistent
        if self.amount is not None and self.price is not None:
            if self.amount.currency != self.price.currency:
                raise ValueError("Price and amount must use the same currency")


    def _check_constraints_sell(self):
        # Same constrains as buy transactions
        self._check_constraints_buy()

    def _check_constraints_vest(self):
        if self.quantity is None:
            raise ValueError("Quantity must be set for vest transactions")

    def _check_constraints_tax(self):
        if self.amount is None:
            raise ValueError("Amount must be set for tax transactions")

    def _check_constraints_cash(self):
        if self.amount is None:
            raise ValueError("Amount must be set for cash transactions")

    def _check_constraints_div(self):
        if self.amount is None:
            raise ValueError("Amount must be set for dividends transactions")

    def __eq__(self, o):
        return (
            self.action == o.action and
            self.date == o.date and
            self.ticker == o.ticker and
            self.isin == o.isin and
            self.name == o.name and
            self.fees == o.fees and
            self.price == o.price and
            self.quantity == o.quantity and
            self.amount == o.amount
        )
