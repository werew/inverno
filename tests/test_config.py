from datetime import datetime
import pytest
from inverno.price import Currency, Price
from inverno.config import Config
from inverno.holding import Holding
from inverno.transaction import Transaction, TransactionAction

# pylint: disable=missing-function-docstring

config = """
options:
    title: test_report
    days: 10
    end_date: 23/05/21
    currency: USD
transactions:
    - format: standard
      file: transactions.csv
prices:
    - match:
        name: TEST
      file: prices.csv
""".strip()

transactions_csv = """
date,action,name,ticker,isin,quantity,price,fees,amount
10/02/21,cash_in,,,,,,,"$4,000.00"
12/02/21,buy,,FB,,4,$1234.56,,
""".strip()

prices_csv = """
date,price
21 May 2021,$1234.56
22 May 2021,$42
""".strip()


@pytest.fixture
def get_config():
    global config

    cfg = Config(cfg=config)
    cfg.provide_file("transactions.csv", transactions_csv)
    cfg.provide_file("prices.csv", prices_csv)
    yield cfg


# pylint: disable=redefined-outer-name


def test_title(get_config):
    cfg = get_config
    assert cfg.title == "test_report"


def test_days(get_config):
    cfg = get_config
    assert cfg.days == 10


def test_end_date(get_config):
    cfg = get_config
    assert cfg.end_date == datetime(2021, 5, 23)


def test_currency(get_config):
    cfg = get_config
    assert cfg.currency == Currency.USD


def test_transactions(get_config):
    cfg = get_config
    assert cfg.transactions[0] == Transaction(
        action=TransactionAction.CASH_IN,
        date=datetime(2021, 2, 10),
        amount=Price(Currency.USD, 4000),
    )

    assert cfg.transactions[1] == Transaction(
        action=TransactionAction.BUY,
        date=datetime(2021, 2, 12),
        ticker="FB",
        quantity=4,
        price=Price(Currency.USD, 1234.56),
    )


def test_prices(get_config):
    cfg = get_config
    h = Holding(quantity=0, name="TEST")
    start = datetime(2021, 5, 21)
    prices = cfg.get_prices(h, start=start)
    assert prices[0] == 1234.56
    assert prices.index[0] == start
    assert prices[1] == 42
    assert prices.isna()[2]
    assert prices.index[-1] == cfg.end_date
    assert len(prices) == (cfg.end_date - start).days + 1

    prices = cfg.get_prices(h, start=start, end=start)
    assert prices[0] == 1234.56
    assert prices.index[0] == start
    assert len(prices) == 1

    start = datetime(2021, 5, 22)
    prices = cfg.get_prices(h, start=start)
    assert prices[0] == 42
    assert prices.index[0] == start
    assert prices.isna()[1]
    assert len(prices) == (cfg.end_date - start).days + 1


config_meta_base = """
meta:
    - match:
        name: H1
      apply:
        test_attr: val_a
    - match:
        name: H2
      apply:
        test_attr: 
            val_a: 30%
            val_b: 50%
""".strip()


def test_meta():
    cfg = Config(cfg=config_meta_base)
    holdings = [Holding(name="H1"), Holding(name="H2")]
    meta = cfg.get_meta_attributes(holdings)
    assert meta["test_attr"]["val_a"]["H1"] == 1.
    assert meta["test_attr"]["val_a"]["H2"] == 0.3
    assert meta["test_attr"]["val_b"]["H2"] == 0.5
    assert "H1" not in meta["test_attr"]["val_b"]

config_meta_composition = """
meta:
    - match:
        name: H1
      apply:
        attr_1: val_a
      composition:
        name:
            H2: 50%
            H3: 50%
    - match:
        name: H2
      apply:
        attr_1: val_b
        attr_2:
            val_a: 50%
            val_b: 50%
    - match:
        name: H3
      apply:
        attr_1: val_b
        attr_2: val_a
""".strip()

def test_meta_composition():
    cfg = Config(cfg=config_meta_composition)
    holdings = [Holding(name="H1")]
    meta = cfg.get_meta_attributes(holdings)

    assert meta["attr_1"]["val_a"]["H1"] == 1.
    assert "H1" not in meta["attr_1"]["val_b"]
    assert meta["attr_2"]["val_a"]["H1"] == 0.75
    assert meta["attr_2"]["val_b"]["H1"] == 0.25
