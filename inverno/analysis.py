from typing import Dict, List, Iterable, Optional
from collections import defaultdict
import pandas as pd
import numpy as np
from .transaction import TransactionAction, Transaction
from .balance import Balance
from .price import Price, Currency


class Analysis:
    def __init__(
        self,
        prices: pd.DataFrame,
        conv_rates: Dict[str, float],
        holdings_currencies: Dict[str, Currency],
    ):
        self.prices = prices
        self.conv_rates = conv_rates
        self.holdings_currencies = holdings_currencies
        self.holdings_keys = list(self.prices.columns)

    def get_allocations(
        self, balances: Iterable[Balance], ndays: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Given a list of known balances, creates a pandas dataframe of allocations
        where each column represent an holding and each row represent holdings'
        values (i.e.  as cash) for a day.
        An extra cash column is added to represent the amount of cash held.

        For example, considering a single day X, two holdings which corresponding
        value in cash in 100$ each and 50$ cash deposited in the account, then the
        resulting allocations dataframe will look like this:

                    | HOLDING_1 | HOLDING_2 | cash
                ----+-----------+-----------+--------
                X   |   100     |   100     | 50

        If in day X+1 we have bought 50$ worth of HOLDING_1 and HOLDING_2's price
        has increased +5%, then the allocation table will look like this:

                    | HOLDING_1 | HOLDING_2 | cash
                ----+-----------+-----------+--------
                X   |   100     |   100     | 50
                X+1 |   150     |   105     |  0
        """

        # New dataframe with the same layout of prices
        allocations = pd.DataFrame().reindex_like(self.prices)
        cash = pd.DataFrame(columns=["cash"], index=allocations.index, dtype=np.float64)

        for balance in balances:
            # Populate holdings columns
            for holding in balance.holdings.values():
                allocations.loc[
                    pd.Timestamp(balance.date), holding.get_key()
                ] = holding.quantity

            # Populate cash dataframe
            total_cash = 0.0
            for curr, amount in balance.cash.items():
                total_cash += Price(currency=curr, amount=amount).normalize_currency(
                    self.conv_rates
                )
            cash.loc[pd.Timestamp(balance.date), "cash"] = total_cash

        # Fill empty slot using previous known values
        allocations = allocations.interpolate(method="pad", axis=0)
        cash = cash.interpolate(method="pad", axis=0)

        # Apply prices
        allocations *= self.prices

        # For each column, apply conversion rate
        for key in self.prices.columns:
            currency = self.holdings_currencies.get(key)
            if currency is None:
                raise ValueError(f"Couldn't determine currency for holding {key}")

            rate = self.conv_rates.get(currency.name)
            if rate is None:
                raise ValueError(f"Unsupported currency {currency.name}")

            allocations[key] /= rate

        # Return holdings allocations including cash
        res = pd.concat([allocations, cash], axis=1).fillna(0)

        # Take only the last n days
        if ndays is not None:
            # pylint: disable=invalid-unary-operand-type
            res = res.iloc[-ndays:]

        return res

    def get_earnings(
        self,
        allocations: pd.DataFrame,
        transactions: List[Transaction],
        ndays: Optional[int] = None,
    ) -> pd.Series:
        """
        Computes net earnings by discounting incoming cash flows that are not
        directly coming from an investment (e.g.  cash transfer, vesting).
        """
        earnings = allocations.sum(axis=1)

        for trs in transactions:
            # Discount cash put into the account
            if trs.action == TransactionAction.CASH:
                rows = earnings.loc[trs.date :]
                delta = trs.amount.normalize_currency(self.conv_rates)
                earnings.loc[trs.date :] = rows.add(-delta)

            # Discount vested stock (as it is not earning from investiment)
            elif trs.action == TransactionAction.VEST:
                rows = earnings.loc[trs.date :]
                price = self.prices.loc[trs.date :][trs.get_holding_key()].iloc[0]
                holding_cur = self.holdings_currencies[trs.get_holding_key()]
                delta = Price(
                    currency=holding_cur, amount=trs.quantity * price
                ).normalize_currency(self.conv_rates)
                earnings.loc[trs.date :] = rows.add(-delta)

        # Take only the last n days
        if ndays is not None:
            # pylint: disable=invalid-unary-operand-type
            earnings = earnings.iloc[-ndays:]

        # Subtract initial value so that we always start from zero
        earnings = earnings.add(-earnings.iloc[0])

        return earnings

    def get_attr_allocations(
        self, allocations: pd.DataFrame, attr_weights: Dict[str, Dict[str, float]]
    ) -> pd.DataFrame:
        """
        Creates an allocations dataframe for a given meta attribute, where each
        column represents an attribute's value and each row contains the total amount
        allocated to that value.
        An extra column "unknown" is created to fit all holdings (or portions of
        holdings) that do not specify any allocation for this attribute.

        The arg attr_weights is used to specify holdings allocations with respect
        of this attribute's values, e.g.:
            {
                "VALUE_1": {"HOLDING_1": 0.5, "HOLDING_2": 0.9},
                "VALUE_2": {"HOLDING_1": 0.5}
            }

        For a single day X, assuming an equal price for HOLDING_1 and HOLDING_2 and
        an equal allocation of 100$ each, the resulting dataframe will look like
        this:

                  |VALUE_1 | VALUE_2 | unknown
                --+--------+---------+--------
                X |  140   |   50    |   10
        """

        columns = list(attr_weights) + ["unknown"]
        df = pd.DataFrame(0, columns=columns, index=allocations.index, dtype=np.float64)

        # Keep record of how much we allocate for each holding
        tot_holdings = defaultdict(lambda: 0)

        # Compute holdings allocations
        for entry, values in attr_weights.items():
            for holding_key, portion in values.items():
                df[entry] += portion * allocations[holding_key]
                tot_holdings[holding_key] += portion

        # Cumpute unknown allocations
        for holding_key in self.holdings_keys:
            allocation = tot_holdings[holding_key]

            if allocation > 1:
                raise ValueError(
                    f"Holding {holding_key} cannot have more than 100% allocation"
                )

            elif allocation == 1:
                continue

            df["unknown"] += allocations[holding_key] * (1 - allocation)
        return df
