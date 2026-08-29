# ============================================================
# PAPER TRADING ENGINE
# ============================================================

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class PaperPosition:
    symbol: str
    side: str
    entry: float
    stop: float
    tp1: float
    tp2: float
    quantity: float = 0.0
    status: str = "OPEN"

    def to_dict(self):
        return asdict(self)


class PaperTrader:

    def __init__(self, starting_balance: float = 1000.0):

        self.starting_balance = float(starting_balance)
        self.balance = float(starting_balance)

        self.positions = {}
        self.closed_trades = []

    # --------------------------------------------------------
    # OPEN POSITION
    # --------------------------------------------------------

    def open_position(
        self,
        symbol: str,
        side: str,
        entry: float,
        stop: float,
        tp1: float,
        tp2: float,
        risk_amount: Optional[float] = None,
    ):

        symbol = symbol.upper()
        side = side.upper()

        if symbol in self.positions:
            return {
                "success": False,
                "reason": "POSITION_ALREADY_EXISTS",
            }

        entry = float(entry)
        stop = float(stop)
        tp1 = float(tp1)
        tp2 = float(tp2)

        if entry <= 0 or stop <= 0:
            return {
                "success": False,
                "reason": "INVALID_PRICE",
            }

        if side not in ("LONG", "SHORT"):
            return {
                "success": False,
                "reason": "INVALID_SIDE",
            }

        # ----------------------------------------------------
        # RISK
        # ----------------------------------------------------

        if risk_amount is None:
            risk_amount = self.balance * 0.01

        risk_amount = float(risk_amount)

        distance = abs(entry - stop)

        if distance <= 0:
            return {
                "success": False,
                "reason": "INVALID_STOP_DISTANCE",
            }

        quantity = risk_amount / distance

        position = PaperPosition(
            symbol=symbol,
            side=side,
            entry=entry,
            stop=stop,
            tp1=tp1,
            tp2=tp2,
            quantity=quantity,
        )

        self.positions[symbol] = position

        return {
            "success": True,
            "action": "OPEN",
            "position": position.to_dict(),
            "risk_amount": risk_amount,
        }

    # --------------------------------------------------------
    # UPDATE POSITION
    # --------------------------------------------------------

    def update_position(
        self,
        symbol: str,
        price: float,
    ):

        symbol = symbol.upper()
        price = float(price)

        position = self.positions.get(symbol)

        if position is None:
            return None

        side = position.side

        # ----------------------------------------------------
        # LONG
        # ----------------------------------------------------

        if side == "LONG":

            if price <= position.stop:

                return self._close_position(
                    symbol,
                    price,
                    "STOP"
                )

            if price >= position.tp2:

                return self._close_position(
                    symbol,
                    price,
                    "TP2"
                )

            if price >= position.tp1:

                return {
                    "symbol": symbol,
                    "status": "TP1_REACHED",
                    "price": price,
                }

        # ----------------------------------------------------
        # SHORT
        # ----------------------------------------------------

        elif side == "SHORT":

            if price >= position.stop:

                return self._close_position(
                    symbol,
                    price,
                    "STOP"
                )

            if price <= position.tp2:

                return self._close_position(
                    symbol,
                    price,
                    "TP2"
                )

            if price <= position.tp1:

                return {
                    "symbol": symbol,
                    "status": "TP1_REACHED",
                    "price": price,
                }

        return {
            "symbol": symbol,
            "status": "OPEN",
            "price": price,
        }

    # --------------------------------------------------------
    # CLOSE
    # --------------------------------------------------------

    def _close_position(
        self,
        symbol: str,
        exit_price: float,
        reason: str,
    ):

        position = self.positions.pop(symbol)

        if position.side == "LONG":

            pnl = (
                exit_price - position.entry
            ) * position.quantity

        else:

            pnl = (
                position.entry - exit_price
            ) * position.quantity

        self.balance += pnl

        trade = {
            "symbol": symbol,
            "side": position.side,
            "entry": position.entry,
            "exit": exit_price,
            "quantity": position.quantity,
            "pnl": pnl,
            "reason": reason,
            "balance": self.balance,
        }

        self.closed_trades.append(trade)

        return {
            "symbol": symbol,
            "status": "CLOSED",
            "reason": reason,
            "pnl": pnl,
            "balance": self.balance,
        }

    # --------------------------------------------------------
    # GET STATUS
    # --------------------------------------------------------

    def status(self):

        return {
            "starting_balance": self.starting_balance,
            "balance": self.balance,
            "open_positions": {
                symbol: position.to_dict()
                for symbol, position
                in self.positions.items()
            },
            "closed_trades": len(
                self.closed_trades
            ),
        }


# ------------------------------------------------------------
# SIMPLE FACTORY
# ------------------------------------------------------------

def create_paper_trader(
    starting_balance: float = 1000.0
):

    return PaperTrader(
        starting_balance=starting_balance
    )
