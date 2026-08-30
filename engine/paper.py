# ============================================================
# PAPER TRADING ENGINE
# ============================================================

from dataclasses import dataclass, asdict
from typing import Optional


# ============================================================
# POSITION
# ============================================================

@dataclass
class PaperPosition:

    symbol: str
    side: str

    entry: float
    stop: float

    tp1: float
    tp2: float

    quantity: float = 0.0

    risk_amount: float = 0.0

    tp1_reached: bool = False

    status: str = "OPEN"

    def to_dict(self):

        return asdict(self)


# ============================================================
# PAPER TRADER
# ============================================================

class PaperTrader:

    def __init__(
        self,
        starting_balance: float = 1000.0,
        risk_per_trade: float = 0.01,
        max_portfolio_risk: float = 0.03,
        max_open_positions: int = 3,
    ):

        self.starting_balance = float(
            starting_balance
        )

        self.balance = float(
            starting_balance
        )

        self.risk_per_trade = float(
            risk_per_trade
        )

        self.max_portfolio_risk = float(
            max_portfolio_risk
        )

        self.max_open_positions = int(
            max_open_positions
        )

        self.positions = {}

        self.closed_trades = []

    # ========================================================
    # CURRENT OPEN RISK
    # ========================================================

    def current_open_risk(self):

        return sum(
            position.risk_amount
            for position
            in self.positions.values()
        )

    # ========================================================
    # AVAILABLE RISK
    # ========================================================

    def available_risk(self):

        max_risk = (
            self.balance
            *
            self.max_portfolio_risk
        )

        used_risk = (
            self.current_open_risk()
        )

        return max(
            0.0,
            max_risk - used_risk
        )

    # ========================================================
    # OPEN POSITION
    # ========================================================

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

        symbol = str(
            symbol
        ).upper()

        side = str(
            side
        ).upper()

        # ----------------------------------------------------
        # BASIC VALIDATION
        # ----------------------------------------------------

        if not symbol:

            return {
                "success": False,
                "reason": "INVALID_SYMBOL",
            }

        if side not in (
            "LONG",
            "SHORT",
        ):

            return {
                "success": False,
                "reason": "INVALID_SIDE",
            }

        # ----------------------------------------------------
        # DUPLICATE POSITION
        # ----------------------------------------------------

        if symbol in self.positions:

            return {
                "success": False,
                "reason": "POSITION_ALREADY_EXISTS",
            }

        # ----------------------------------------------------
        # POSITION LIMIT
        # ----------------------------------------------------

        if (
            len(self.positions)
            >= self.max_open_positions
        ):

            return {
                "success": False,
                "reason": "MAX_OPEN_POSITIONS_REACHED",
                "max_open_positions":
                    self.max_open_positions,
            }

        # ----------------------------------------------------
        # PRICE CONVERSION
        # ----------------------------------------------------

        try:

            entry = float(entry)
            stop = float(stop)
            tp1 = float(tp1)
            tp2 = float(tp2)

        except (
            TypeError,
            ValueError,
        ):

            return {
                "success": False,
                "reason": "INVALID_PRICE",
            }

        if (
            entry <= 0
            or stop <= 0
            or tp1 <= 0
            or tp2 <= 0
        ):

            return {
                "success": False,
                "reason": "INVALID_PRICE",
            }

        # ====================================================
        # LONG VALIDATION
        # ====================================================

        if side == "LONG":

            if stop >= entry:

                return {
                    "success": False,
                    "reason": "LONG_STOP_INVALID",
                }

            if tp1 <= entry:

                return {
                    "success": False,
                    "reason": "LONG_TP1_INVALID",
                }

            if tp2 <= tp1:

                return {
                    "success": False,
                    "reason": "LONG_TP2_INVALID",
                }

        # ====================================================
        # SHORT VALIDATION
        # ====================================================

        if side == "SHORT":

            if stop <= entry:

                return {
                    "success": False,
                    "reason": "SHORT_STOP_INVALID",
                }

            if tp1 >= entry:

                return {
                    "success": False,
                    "reason": "SHORT_TP1_INVALID",
                }

            if tp2 >= tp1:

                return {
                    "success": False,
                    "reason": "SHORT_TP2_INVALID",
                }

        # ====================================================
        # RISK
        # ====================================================

        if risk_amount is None:

            risk_amount = (
                self.balance
                *
                self.risk_per_trade
            )

        try:

            risk_amount = float(
                risk_amount
            )

        except (
            TypeError,
            ValueError,
        ):

            return {
                "success": False,
                "reason": "INVALID_RISK_AMOUNT",
            }

        if risk_amount <= 0:

            return {
                "success": False,
                "reason": "INVALID_RISK_AMOUNT",
            }

        # ----------------------------------------------------
        # MAX SINGLE TRADE RISK
        # ----------------------------------------------------

        max_trade_risk = (
            self.balance
            *
            self.risk_per_trade
        )

        if risk_amount > max_trade_risk:

            return {
                "success": False,
                "reason": "TRADE_RISK_TOO_HIGH",
                "requested_risk":
                    risk_amount,
                "max_trade_risk":
                    max_trade_risk,
            }

        # ----------------------------------------------------
        # PORTFOLIO RISK
        # ----------------------------------------------------

        available_risk = (
            self.available_risk()
        )

        if risk_amount > available_risk:

            return {
                "success": False,
                "reason": "PORTFOLIO_RISK_LIMIT_REACHED",
                "requested_risk":
                    risk_amount,
                "available_risk":
                    available_risk,
            }

        # ====================================================
        # POSITION SIZE
        # ====================================================

        stop_distance = abs(
            entry - stop
        )

        if stop_distance <= 0:

            return {
                "success": False,
                "reason": "INVALID_STOP_DISTANCE",
            }

        quantity = (
            risk_amount
            /
            stop_distance
        )

        if quantity <= 0:

            return {
                "success": False,
                "reason": "INVALID_QUANTITY",
            }

        # ====================================================
        # CREATE POSITION
        # ====================================================

        position = PaperPosition(

            symbol=symbol,

            side=side,

            entry=entry,

            stop=stop,

            tp1=tp1,

            tp2=tp2,

            quantity=quantity,

            risk_amount=risk_amount,

        )

        self.positions[
            symbol
        ] = position

        # ====================================================
        # RESULT
        # ====================================================

        return {

            "success": True,

            "action": "OPEN",

            "position":
                position.to_dict(),

            "risk_amount":
                risk_amount,

            "portfolio_open_risk":
                self.current_open_risk(),

            "portfolio_risk_percent":
                (
                    self.current_open_risk()
                    /
                    self.balance
                    *
                    100
                ),

        }

    # ========================================================
    # UPDATE POSITION
    # ========================================================

    def update_position(
        self,
        symbol: str,
        price: float,
    ):

        symbol = str(
            symbol
        ).upper()

        try:

            price = float(
                price
            )

        except (
            TypeError,
            ValueError,
        ):

            return {
                "success": False,
                "reason": "INVALID_PRICE",
            }

        if price <= 0:

            return {
                "success": False,
                "reason": "INVALID_PRICE",
            }

        position = self.positions.get(
            symbol
        )

        if position is None:

            return {
                "success": False,
                "reason": "POSITION_NOT_FOUND",
            }

        # ====================================================
        # LONG
        # ====================================================

        if position.side == "LONG":

            # Stop önce kontrol edilir.
            if price <= position.stop:

                return self._close_position(
                    symbol,
                    price,
                    "STOP",
                )

            if price >= position.tp2:

                return self._close_position(
                    symbol,
                    price,
                    "TP2",
                )

            if (
                price >= position.tp1
                and not position.tp1_reached
            ):

                position.tp1_reached = True

                return {
                    "symbol":
                        symbol,

                    "status":
                        "TP1_REACHED",

                    "price":
                        price,
                }

        # ====================================================
        # SHORT
        # ====================================================

        elif position.side == "SHORT":

            if price >= position.stop:

                return self._close_position(
                    symbol,
                    price,
                    "STOP",
                )

            if price <= position.tp2:

                return self._close_position(
                    symbol,
                    price,
                    "TP2",
                )

            if (
                price <= position.tp1
                and not position.tp1_reached
            ):

                position.tp1_reached = True

                return {
                    "symbol":
                        symbol,

                    "status":
                        "TP1_REACHED",

                    "price":
                        price,
                }

        return {

            "symbol":
                symbol,

            "status":
                "OPEN",

            "price":
                price,

            "tp1_reached":
                position.tp1_reached,

        }

    # ========================================================
    # CLOSE POSITION
    # ========================================================

    def _close_position(
        self,
        symbol: str,
        exit_price: float,
        reason: str,
    ):

        position = self.positions.pop(
            symbol,
            None,
        )

        if position is None:

            return {
                "success": False,
                "reason": "POSITION_NOT_FOUND",
            }

        # ----------------------------------------------------
        # PNL
        # ----------------------------------------------------

        if position.side == "LONG":

            pnl = (
                exit_price
                -
                position.entry
            ) * position.quantity

        else:

            pnl = (
                position.entry
                -
                exit_price
            ) * position.quantity

        self.balance += pnl

        # ----------------------------------------------------
        # TRADE RECORD
        # ----------------------------------------------------

        trade = {

            "symbol":
                symbol,

            "side":
                position.side,

            "entry":
                position.entry,

            "exit":
                exit_price,

            "quantity":
                position.quantity,

            "risk_amount":
                position.risk_amount,

            "pnl":
                pnl,

            "reason":
                reason,

            "balance":
                self.balance,

        }

        self.closed_trades.append(
            trade
        )

        return {

            "symbol":
                symbol,

            "status":
                "CLOSED",

            "reason":
                reason,

            "pnl":
                pnl,

            "balance":
                self.balance,

        }

    # ========================================================
    # CLOSE ALL
    # ========================================================

    def close_all(
        self,
        prices,
        reason="MANUAL",
    ):

        results = []

        if not prices:
            return results

        for symbol in list(
            self.positions.keys()
        ):

            if symbol not in prices:
                continue

            result = self._close_position(
                symbol,
                float(
                    prices[symbol]
                ),
                reason,
            )

            results.append(
                result
            )

        return results

    # ========================================================
    # GET STATUS
    # ========================================================

    def status(self):

        max_portfolio_risk = (
            self.balance
            *
            self.max_portfolio_risk
        )

        open_risk = (
            self.current_open_risk()
        )

        return {

            "starting_balance":
                self.starting_balance,

            "balance":
                self.balance,

            "open_positions":
                {
                    symbol:
                        position.to_dict()

                    for symbol, position
                    in self.positions.items()
                },

            "open_position_count":
                len(self.positions),

            "closed_trades":
                len(
                    self.closed_trades
                ),

            "open_risk":
                open_risk,

            "open_risk_percent":
                (
                    open_risk
                    /
                    self.balance
                    *
                    100
                    if self.balance > 0
                    else 0
                ),

            "max_portfolio_risk":
                max_portfolio_risk,

            "available_risk":
                self.available_risk(),

        }


# ============================================================
# FACTORY
# ============================================================

def create_paper_trader(
    starting_balance: float = 1000.0,
):

    return PaperTrader(
        starting_balance=
            starting_balance,

        risk_per_trade=0.01,

        max_portfolio_risk=0.03,

        max_open_positions=3,
            )
