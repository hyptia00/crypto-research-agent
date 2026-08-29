# ============================================================
# CRYPTO RESEARCH AGENT
# CONFIGURATION
# ============================================================

# -----------------------------
# CORE COINS
# -----------------------------

CORE_COINS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOTUSDT",
    "NEARUSDT",
    "JUPUSDT",
    "MOVRUSDT",
    "TNSRUSDT",
]


# -----------------------------
# DISCOVERY
# -----------------------------

# Ana coinler dışında piyasayı taramak için
DISCOVERY_ENABLED = True

# USDT pariteleri
DISCOVERY_QUOTE = "USDT"

# Çok düşük likiditeli coinleri elemek için
MIN_24H_VOLUME_USDT = 5_000_000


# -----------------------------
# TIMEFRAMES
# -----------------------------

FUTURES_TIMEFRAME = "1h"

SPOT_TIMEFRAME = "4h"

SCALPING_TIMEFRAMES = [
    "15m",
    "5m",
    "1m",
]


# -----------------------------
# INDICATORS
# -----------------------------

EMA_FAST = 20
EMA_SLOW = 50

RSI_PERIOD = 14

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

ATR_PERIOD = 14

OBV_ENABLED = True


# -----------------------------
# MARKET STRUCTURE
# -----------------------------

STRUCTURE_LOOKBACK = 50

BOS_ENABLED = True

MSB_ENABLED = True

LIQUIDITY_ENABLED = True


# -----------------------------
# SIGNAL THRESHOLDS
# -----------------------------

# Futures
FUTURES_MIN_SCORE = 6

# Spot
SPOT_MIN_SCORE = 6

# Scalping
SCALPING_MIN_SCORE = 7

# Discovery
DISCOVERY_MIN_SCORE = 7


# -----------------------------
# RISK / REWARD
# -----------------------------

MIN_RR = 2.0

DEFAULT_RR = 2.5

MAX_RISK_PERCENT = 1.0


# -----------------------------
# BTC REGIME FILTER
# -----------------------------

BTC_REGIME_ENABLED = True

BTC_REGIME_TIMEFRAME = "4h"


# -----------------------------
# SCALPING CONFIRMATION
# -----------------------------

# Scalping sıralaması:
#
# 15m = yön / yapı
# 5m  = setup teyidi
# 1m  = giriş tetikleyicisi

SCALP_REQUIRE_15M = True
SCALP_REQUIRE_5M = True
SCALP_REQUIRE_1M = True


# -----------------------------
# PAPER TRADING
# -----------------------------

PAPER_TRADING = True

# Şimdilik gerçek emir gönderme
LIVE_TRADING = False


# -----------------------------
# API
# -----------------------------

# GitHub Secrets üzerinden alınacak
BINANCE_API_KEY = ""
BINANCE_API_SECRET = ""


# -----------------------------
# OUTPUT
# -----------------------------

MAX_SIGNALS = 10

SHOW_CORE_SIGNALS = True

SHOW_DISCOVERY_SIGNALS = True

SHOW_SPOT_SIGNALS = True

SHOW_FUTURES_SIGNALS = True

SHOW_SCALPING_SIGNALS = True
