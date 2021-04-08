from typing import Optional, Dict
import copy
from datetime import datetime
from .transaction import Transaction, TransactionAction
from .price import Price, Currency
from .holding import Holding, holdings_currencies


class Balance:
    def __init__(
        self,
        date: datetime,
        holdings: Optional[Dict] = None,
        cash: Optional[Dict] = None,
    ):
        self.date = date
        self.holdings = holdings or {}
        self.cash = cash or {}

    def process_transaction(self, transaction: Transaction) -> "Balance":
        new_balance = copy.deepcopy(self)
        new_balance.date = max(transaction.date, new_balance.date)

        if transaction.action == TransactionAction.BUY:
            self._process_buy_transaction(
                new_balance=new_balance, transaction=transaction
            )
        elif transaction.action == TransactionAction.SELL:
            self._process_sell_transaction(
                new_balance=new_balance, transaction=transaction
            )
        elif transaction.action == TransactionAction.CASH:
            self._process_cash_transaction(
                new_balance=new_balance, transaction=transaction
            )
        elif transaction.action == TransactionAction.DIV:
            self._process_div_transaction(
                new_balance=new_balance, transaction=transaction
            )
        elif transaction.action == TransactionAction.TAX:
            self._process_tax_transaction(
                new_balance=new_balance, transaction=transaction
            )
        elif transaction.action == TransactionAction.VEST:
            self._process_vest_transaction(
                new_balance=new_balance, transaction=transaction
            )
        else:
            raise ValueError(
                f"Couldn't process transaction action {transaction.action.name}:"
                " this action is currently not fully supported"
            )

        return new_balance

    def _make_holding(self, transaction: Transaction) -> Holding:
        return Holding(
            quantity=transaction.quantity,
            name=transaction.name,
            ticker=transaction.ticker,
            isin=transaction.isin,
        )

    def get_cash_balance(self, currency: Currency) -> Price:
        cash = self.cash.get(currency)
        if cash is None:
            cash = Price(currency=currency, amount=0.0)
        return cash

    def _process_sell_transaction(
        self, new_balance: "Balance", transaction: Transaction
    ):
        # Reduce available holdings
        new_holding = self._make_holding(transaction=transaction)
        if new_holding.get_key() in new_balance.holdings:
            new_balance.holdings[new_holding.get_key()] -= new_holding
        else:
            new_balance.holdings[new_holding.get_key()] = -new_holding

        # Update cash after transaction
        cash = new_balance.get_cash_balance(transaction.price.currency)
        new_cash = cash + (transaction.price * transaction.quantity)
        if transaction.fees:
            new_cash -= transaction.fees
        new_balance.cash[new_cash.currency] = new_cash

        # Register holding currency
        holdings_currencies[new_holding.get_key()] = transaction.price.currency

    def _process_buy_transaction(
        self, new_balance: "Balance", transaction: Transaction
    ):
        # Reduce cash for the given currency
        cash = new_balance.get_cash_balance(transaction.price.currency)
        new_cash = cash - (transaction.price * transaction.quantity)
        if transaction.fees:
            new_cash -= transaction.fees
        new_balance.cash[new_cash.currency] = new_cash

        # Add holdings
        new_holding = self._make_holding(transaction=transaction)
        if new_holding.get_key() in new_balance.holdings:
            new_balance.holdings[new_holding.get_key()] += new_holding
        else:
            new_balance.holdings[new_holding.get_key()] = new_holding

        # Register holding currency
        holdings_currencies[new_holding.get_key()] = transaction.price.currency

    def _process_cash_transaction(
        self, new_balance: "Balance", transaction: Transaction
    ):
        # Reduce cash for the given currency
        cash = new_balance.get_cash_balance(transaction.amount.currency)
        new_cash = cash + transaction.amount
        if transaction.fees:
            new_cash -= transaction.fees
        new_balance.cash[new_cash.currency] = new_cash

    def _process_div_transaction(
        self, new_balance: "Balance", transaction: Transaction
    ):
        self._process_cash_transaction(new_balance=new_balance, transaction=transaction)

    def _process_tax_transaction(
        self, new_balance: "Balance", transaction: Transaction
    ):
        self._process_cash_transaction(new_balance=new_balance, transaction=transaction)

    def _process_vest_transaction(
        self, new_balance: "Balance", transaction: Transaction
    ):
        # Apply fees (if any) (??)
        if transaction.fees:
            cash = new_balance.get_cash_balance(transaction.fees.currency)
            new_cash = cash - transaction.fees
            new_balance.cash[new_cash.currency] = new_cash

        # Add holdings
        new_holding = self._make_holding(transaction=transaction)
        if new_holding.get_key() in new_balance.holdings:
            new_balance.holdings[new_holding.get_key()] += new_holding
        else:
            new_balance.holdings[new_holding.get_key()] = new_holding

    def __str__(self):
        return f"CASH: {list(self.cash.values())}, HOLDINGS: {list(self.holdings.values())}"