# config.py

MAIN_COINS = [
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

# Ana coinler dışındaki fırsatları scanner arayacak
SCAN_MARKET = True

# Tarama ayarları
SCAN_QUOTE = "USDT"
SCAN_LIMIT = 80
MIN_24H_VOLUME_USDT = 5_000_000

# Timeframes
TREND_TIMEFRAME = "4h"
ENTRY_TIMEFRAME = "1h"

SCALPING_TIMEFRAMES = [
    "15m",
    "5m",
    "1m",
]

# Futures / Spot
ENABLE_FUTURES = True
ENABLE_SPOT = True
ENABLE_SCALPING = True

# Signal thresholds
MIN_FUTURES_SCORE = 7
MIN_SPOT_SCORE = 7
MIN_SCALP_SCORE = 7

# Risk
MAX_RISK_PER_TRADE = 0.01
MIN_RR = 2.0

# Paper account
PAPER_BALANCE = 1000.0

# Binance
BINANCE_SPOT_URL = "https://data-api.binance.vision"
BINANCE_API_URL = "https://api.binance.com"

# İleride değiştirilebilir
DATA_PROVIDER = "binance"

# Paper trading açık
PAPER_TRADING = True

# Gerçek emir KESİNLİKLE kapalı
LIVE_TRADING = False
