from __future__ import annotations

from typing import Any

from .base_broker import BaseBroker


class QMTBrokerStub(BaseBroker):
    """Future QMT/MiniQMT integration point; never sends real orders."""

    def connect(self) -> Any:
        raise NotImplementedError("QMT integration is not implemented")

    def get_account(self) -> Any:
        raise NotImplementedError("QMT integration is not implemented")

    def get_positions(self) -> Any:
        raise NotImplementedError("QMT integration is not implemented")

    def get_orders(self) -> Any:
        raise NotImplementedError("QMT integration is not implemented")

    def get_trades(self) -> Any:
        raise NotImplementedError("QMT integration is not implemented")

    def buy(self, symbol: str, price: float, volume: int) -> Any:
        raise NotImplementedError("QMT integration is not implemented")

    def sell(self, symbol: str, price: float, volume: int) -> Any:
        raise NotImplementedError("QMT integration is not implemented")

    def cancel_order(self, order_id: str) -> Any:
        raise NotImplementedError("QMT integration is not implemented")
