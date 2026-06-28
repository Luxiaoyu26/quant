from __future__ import annotations

import pytest

from brokers.base_broker import BaseBroker
from brokers.paper_broker import PaperBroker
from brokers.qmt_broker_stub import QMTBrokerStub


def test_base_broker_is_abstract():
    with pytest.raises(TypeError):
        BaseBroker()


def test_paper_broker_buy_and_sell_update_account_and_records():
    broker = PaperBroker(initial_cash=10_000)

    assert broker.connect() is True
    buy_order = broker.buy("600519", price=10, volume=100)
    sell_order = broker.sell("600519", price=12, volume=40)

    account = broker.get_account()
    positions = broker.get_positions()
    assert buy_order["status"] == "filled"
    assert sell_order["status"] == "filled"
    assert account["cash"] == pytest.approx(9_480)
    assert positions["600519"]["volume"] == 60
    assert positions["600519"]["avg_price"] == pytest.approx(10)
    assert len(broker.get_orders()) == 2
    assert len(broker.get_trades()) == 2


def test_paper_broker_rejects_invalid_or_unaffordable_orders():
    broker = PaperBroker(initial_cash=100)

    with pytest.raises(ValueError, match="positive"):
        broker.buy("600519", price=0, volume=10)
    with pytest.raises(ValueError, match="cash"):
        broker.buy("600519", price=20, volume=10)
    with pytest.raises(ValueError, match="position"):
        broker.sell("600519", price=10, volume=1)


@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        ("connect", ()),
        ("get_account", ()),
        ("get_positions", ()),
        ("get_orders", ()),
        ("get_trades", ()),
        ("buy", ("600519", 10, 100)),
        ("sell", ("600519", 10, 100)),
        ("cancel_order", ("order-1",)),
    ],
)
def test_qmt_stub_never_performs_real_operations(method_name, args):
    broker = QMTBrokerStub()

    with pytest.raises(NotImplementedError):
        getattr(broker, method_name)(*args)
