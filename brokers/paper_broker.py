from __future__ import annotations

from copy import deepcopy
from typing import Any

from .base_broker import BaseBroker


class PaperBroker(BaseBroker):
    """Minimal in-memory broker with immediate fills and no transaction fees."""

    def __init__(self, initial_cash: float = 1_000_000):
        if initial_cash < 0:
            raise ValueError("initial_cash cannot be negative")
        self.cash = float(initial_cash)
        self.positions: dict[str, dict[str, float | int]] = {}
        self.orders: list[dict[str, Any]] = []
        self.trades: list[dict[str, Any]] = []
        self.connected = False
        self._next_id = 1

    def connect(self) -> bool:
        self.connected = True
        return True

    def get_account(self) -> dict[str, float | bool]:
        positions_value = sum(
            float(position["avg_price"]) * int(position["volume"])
            for position in self.positions.values()
        )
        return {
            "connected": self.connected,
            "cash": self.cash,
            "positions_value": positions_value,
            "total_asset": self.cash + positions_value,
        }

    def get_positions(self) -> dict[str, dict[str, float | int]]:
        return deepcopy(self.positions)

    def get_orders(self) -> list[dict[str, Any]]:
        return deepcopy(self.orders)

    def get_trades(self) -> list[dict[str, Any]]:
        return deepcopy(self.trades)

    def buy(self, symbol: str, price: float, volume: int) -> dict[str, Any]:
        symbol, price, volume = self._validate_order(symbol, price, volume)
        amount = price * volume
        if amount > self.cash:
            raise ValueError("Insufficient cash for buy order")

        current = self.positions.get(symbol, {"volume": 0, "avg_price": 0.0})
        old_volume = int(current["volume"])
        new_volume = old_volume + volume
        average_price = (
            float(current["avg_price"]) * old_volume + amount
        ) / new_volume
        self.cash -= amount
        self.positions[symbol] = {
            "volume": new_volume,
            "avg_price": average_price,
        }
        return self._record_fill("buy", symbol, price, volume)

    def sell(self, symbol: str, price: float, volume: int) -> dict[str, Any]:
        symbol, price, volume = self._validate_order(symbol, price, volume)
        current = self.positions.get(symbol)
        if current is None or int(current["volume"]) < volume:
            raise ValueError("Insufficient position for sell order")

        remaining = int(current["volume"]) - volume
        self.cash += price * volume
        if remaining == 0:
            del self.positions[symbol]
        else:
            current["volume"] = remaining
        return self._record_fill("sell", symbol, price, volume)

    def cancel_order(self, order_id: str) -> bool:
        for order in self.orders:
            if order["order_id"] == order_id:
                return False
        raise ValueError(f"Order not found: {order_id}")

    @staticmethod
    def _validate_order(symbol: str, price: float, volume: int) -> tuple[str, float, int]:
        normalized_symbol = str(symbol).strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol cannot be empty")
        numeric_price = float(price)
        numeric_volume = int(volume)
        if numeric_price <= 0 or numeric_volume <= 0:
            raise ValueError("price and volume must be positive")
        return normalized_symbol, numeric_price, numeric_volume

    def _record_fill(
        self,
        side: str,
        symbol: str,
        price: float,
        volume: int,
    ) -> dict[str, Any]:
        identifier = f"PAPER-{self._next_id:06d}"
        self._next_id += 1
        order = {
            "order_id": identifier,
            "symbol": symbol,
            "side": side,
            "price": price,
            "volume": volume,
            "status": "filled",
        }
        trade = {
            "trade_id": identifier,
            "order_id": identifier,
            "symbol": symbol,
            "side": side,
            "price": price,
            "volume": volume,
            "amount": price * volume,
        }
        self.orders.append(order)
        self.trades.append(trade)
        return deepcopy(order)
