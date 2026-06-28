from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseBroker(ABC):
    """Common interface for simulated and live broker implementations."""

    @abstractmethod
    def connect(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_account(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_positions(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_orders(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_trades(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def buy(self, symbol: str, price: float, volume: int) -> Any:
        raise NotImplementedError

    @abstractmethod
    def sell(self, symbol: str, price: float, volume: int) -> Any:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, order_id: str) -> Any:
        raise NotImplementedError
