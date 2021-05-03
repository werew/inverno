from typing import Dict, List
import pytest
import pandas as pd
from datetime import datetime
from inverno.price import Currency, Price
from inverno.analysis import Analysis
from inverno.balance import Balance
from inverno.holding import Holding
from inverno.transaction import Transaction, TransactionAction


def _get_transactions(
    prices: pd.DataFrame, holding_currencies: Dict[str, Currency]
) -> Dict[str, List[Transaction]]:
    trans = {}

    trans["base"] = [
        Transaction(
            date=prices.index[0].date(),
            action=TransactionAction.CASH,
            amount=Price(currency=Currency.USD, amount=10.0),
        ),
        Transaction(
            date=prices.index[0].date(),
            action=TransactionAction.BUY,
            ticker="FB",
            quantity=1.0,
            price=Price(currency=holding_currencies["FB"], amount=prices.iloc[0]["FB"]),
        ),
        Transaction(
            date=prices.index[0].date(),
            action=TransactionAction.BUY,
            ticker="TSM",
            quantity=1.0,
            price=Price(
                currency=holding_currencies["TSM"], amount=prices.iloc[0]["TSM"]
            ),
        ),
    ]

    trans["base_add_cash"] = trans["base"] + [
        Transaction(
            date=prices.index[1].date(),
            action=TransactionAction.CASH,
            amount=Price(currency=Currency.USD, amount=10.0),
        ),
    ]

    trans["base_vest"] = trans["base"] + [
        Transaction(
            date=prices.index[1].date(),
            action=TransactionAction.VEST,
            ticker="FB",
            quantity=1.0,
        ),
    ]

    return trans


@pytest.fixture
def analysis_data():
    prices = pd.DataFrame(
        columns=["FB", "TSM"],
        index=pd.date_range(
            start=datetime.strptime("03/05/2021", "%d/%m/%Y"),
            end=datetime.strptime("04/05/2021", "%d/%m/%Y"),
            freq="D",
        ),
        data=[
            [4.0, 4.0],
            [8.0, 2.0],
        ],
    )

    conv_rates = {
        "USD": 1.0,
        "TWD": 2.0,
    }

    holding_currencies = {
        "FB": Currency.USD,
        "TSM": Currency.TWD,
    }

    trans = _get_transactions(prices=prices, holding_currencies=holding_currencies)

    yield {
        "prices": prices,
        "conv_rates": conv_rates,
        "holdings_currencies": holding_currencies,
        "transactions": trans,
    }


# pylint: disable=redefined-outer-name


def test_allocations(analysis_data):
    data = analysis_data
    analysis = Analysis(
        prices=data["prices"],
        conv_rates=data["conv_rates"],
        holdings_currencies=data["holdings_currencies"],
    )

    balances = Balance.get_balances(transactions=data["transactions"]["base"])
    allocations = analysis.get_allocations(balances=balances.values())
    df = pd.DataFrame(
        columns=list(data["prices"].columns) + ["cash"],
        index=data["prices"].index,
        data=[[4.0, 2.0, 4.0], [8.0, 1.0, 4.0]],
    )
    assert df.equals(allocations)

    balances = Balance.get_balances(transactions=data["transactions"]["base_add_cash"])
    allocations = analysis.get_allocations(balances=balances.values())
    df = pd.DataFrame(
        columns=list(data["prices"].columns) + ["cash"],
        index=data["prices"].index,
        data=[[4.0, 2.0, 4.0], [8.0, 1.0, 14.0]],
    )
    assert df.equals(allocations)

    balances = Balance.get_balances(transactions=data["transactions"]["base_vest"])
    allocations = analysis.get_allocations(balances=balances.values())
    df = pd.DataFrame(
        columns=list(data["prices"].columns) + ["cash"],
        index=data["prices"].index,
        data=[[4.0, 2.0, 4.0], [16.0, 1.0, 4.0]],
    )
    assert df.equals(allocations)


def test_earnings(analysis_data):
    data = analysis_data
    analysis = Analysis(
        prices=data["prices"],
        conv_rates=data["conv_rates"],
        holdings_currencies=data["holdings_currencies"],
    )

    transactions = data["transactions"]["base"]
    balances = Balance.get_balances(transactions=transactions)
    allocations = analysis.get_allocations(balances=balances.values())
    earnings = analysis.get_earnings(
        allocations=allocations,
        transactions=transactions,
    )
    expected = pd.Series(data=[0.0, 3.0], index=earnings.index)
    assert earnings.equals(expected)

    transactions = data["transactions"]["base_add_cash"]
    balances = Balance.get_balances(transactions=transactions)
    allocations = analysis.get_allocations(balances=balances.values())
    earnings = analysis.get_earnings(
        allocations=allocations,
        transactions=transactions,
    )
    expected = pd.Series(data=[0.0, 3.0], index=earnings.index)
    assert earnings.equals(expected)

    transactions = data["transactions"]["base_vest"]
    balances = Balance.get_balances(transactions=transactions)
    allocations = analysis.get_allocations(balances=balances.values())
    earnings = analysis.get_earnings(
        allocations=allocations,
        transactions=transactions,
    )
    expected = pd.Series(data=[0.0, 3.0], index=earnings.index)
    assert earnings.equals(expected)
