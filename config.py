# ============================================================
# CRYPTO RESEARCH AGENT - CENTRAL CONFIGURATION
# ============================================================

# ------------------------------------------------------------
# GENERAL
# ------------------------------------------------------------

APP_NAME = "Crypto Research Agent"
VERSION = "2.0"

EXCHANGE = "binance"

# Ana piyasa
QUOTE_ASSET = "USDT"

# ------------------------------------------------------------
# ANA KOINLER
# ------------------------------------------------------------
# Bunlar her zaman ayrıca analiz edilir.

CORE_SYMBOLS = [
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

# ------------------------------------------------------------
# TIMEFRAMES
# ------------------------------------------------------------

TIMEFRAME_4H = "4h"
TIMEFRAME_1H = "1h"
TIMEFRAME_15M = "15m"
TIMEFRAME_5M = "5m"
TIMEFRAME_1M = "1m"

ALL_TIMEFRAMES = [
    TIMEFRAME_4H,
    TIMEFRAME_1H,
    TIMEFRAME_15M,
    TIMEFRAME_5M,
    TIMEFRAME_1M,
]

# ------------------------------------------------------------
# FUTURES ANALYSIS
# ------------------------------------------------------------

FUTURES_ENABLED = True

FUTURES_TIMEFRAMES = [
    "4h",
    "1h",
    "15m",
    "5m",
]

# Futures için ana yön filtresi
FUTURES_PRIMARY_TF = "4h"
FUTURES_CONFIRMATION_TF = "1h"

# İşleme yaklaşmadan önce kullanılacak alt zaman dilimleri
FUTURES_ENTRY_TFS = [
    "15m",
    "5m",
]

# ------------------------------------------------------------
# SCALPING
# ------------------------------------------------------------

SCALPING_ENABLED = True

# Scalping yönü yukarıdan aşağıya kontrol edilir:
#
# 15m -> ana yapı
# 5m  -> setup / teyit
# 1m  -> giriş
#
SCALPING_TIMEFRAMES = [
    "15m",
    "5m",
    "1m",
]

SCALPING_PRIMARY_TF = "15m"
SCALPING_CONFIRMATION_TF = "5m"
SCALPING_ENTRY_TF = "1m"

# ------------------------------------------------------------
# SPOT
# ------------------------------------------------------------

SPOT_ENABLED = True

SPOT_TIMEFRAMES = [
    "4h",
    "1h",
    "15m",
]

SPOT_PRIMARY_TF = "4h"
SPOT_CONFIRMATION_TF = "1h"
SPOT_ENTRY_TF = "15m"

# Spot tarafında short yok
SPOT_ALLOWED_SIDES = [
    "LONG",
]

# ------------------------------------------------------------
# DYNAMIC COIN DISCOVERY
# ------------------------------------------------------------
# Ana koinlerin yanında piyasadan yeni fırsatlar aranacak.

DISCOVERY_ENABLED = True

# Binance USDT paritelerinden taranacak maksimum coin
DISCOVERY_MAX_SYMBOLS = 150

# Sonuçlarda gösterilecek maksimum fırsat
MAX_OPPORTUNITIES = 15

# Çok düşük likiditeli coinleri ele
MIN_24H_QUOTE_VOLUME_USDT = 10_000_000

# Aşırı küçük fiyatlı / problemli pariteleri elemek için
MIN_PRICE_USDT = 0.0001

# Stablecoin ve bazı istenmeyen varlıkları hariç tut
EXCLUDED_SYMBOLS = [
    "USDCUSDT",
    "FDUSDUSDT",
    "USDTUSDT",
    "TUSDUSDT",
    "USDEUSDT",
    "DAIUSDT",
]

# ------------------------------------------------------------
# MARKET STRUCTURE
# ------------------------------------------------------------

STRUCTURE_ENABLED = True

# Swing tespit hassasiyeti
SWING_LOOKBACK = 3

# Daha güçlü yapı için minimum swing mesafesi
MIN_SWING_DISTANCE = 2

# Market Structure
USE_BOS = True
USE_CHOCH = True
USE_MSB = True

# ------------------------------------------------------------
# LIQUIDITY
# ------------------------------------------------------------

LIQUIDITY_ENABLED = True

USE_LIQUIDITY_SWEEP = True
USE_EQUAL_HIGH_LOW = True

# Likidite süpürme toleransı
LIQUIDITY_TOLERANCE = 0.0015

# ------------------------------------------------------------
# FVG
# ------------------------------------------------------------

FVG_ENABLED = True

FVG_MIN_SIZE_PERCENT = 0.10

# ------------------------------------------------------------
# ORDER BLOCK
# ------------------------------------------------------------

ORDER_BLOCK_ENABLED = True

# OB'nin geçerli sayılması için minimum mum büyüklüğü
ORDER_BLOCK_MIN_BODY_PERCENT = 0.20

# ------------------------------------------------------------
# MITIGATION
# ------------------------------------------------------------

MITIGATION_ENABLED = True

# Mitigation / retest toleransı
MITIGATION_TOLERANCE = 0.002

# ------------------------------------------------------------
# MSB / MITIGATION BREAK
# ------------------------------------------------------------

MSB_ENABLED = True

# MSB tespitinde kullanılacak zaman dilimleri
MSB_TIMEFRAMES = [
    "15m",
    "5m",
    "1m",
]

# 15m ana yapı
MSB_PRIMARY_TF = "15m"

# 5m pozisyon teyidi
MSB_CONFIRMATION_TF = "5m"

# 1m hassas giriş
MSB_ENTRY_TF = "1m"

# ------------------------------------------------------------
# TECHNICAL INDICATORS
# ------------------------------------------------------------

EMA_FAST = 20
EMA_SLOW = 50
EMA_TREND = 200

RSI_PERIOD = 14

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

ATR_PERIOD = 14

# RSI bölgeleri
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# Daha güvenli trend filtreleri
RSI_LONG_MIN = 50
RSI_SHORT_MAX = 50

# ------------------------------------------------------------
# VOLUME
# ------------------------------------------------------------

VOLUME_ENABLED = True

# Ortalama hacim periyodu
VOLUME_LOOKBACK = 20

# Güçlü hacim
STRONG_VOLUME_MULTIPLIER = 1.50

# Normal hacim
NORMAL_VOLUME_MULTIPLIER = 1.00

# Çok düşük hacim
WEAK_VOLUME_MULTIPLIER = 0.50

# ------------------------------------------------------------
# SIGNAL SCORING
# ------------------------------------------------------------

SIGNAL_SCORING_ENABLED = True

# Maksimum puan
MAX_SIGNAL_SCORE = 10

# Minimum işlem sinyali
MIN_SIGNAL_SCORE = 7

# Güçlü sinyal
STRONG_SIGNAL_SCORE = 8

# Çok güçlü sinyal
VERY_STRONG_SIGNAL_SCORE = 9

# ------------------------------------------------------------
# SIGNAL COMPONENT WEIGHTS
# ------------------------------------------------------------

WEIGHT_TREND = 2
WEIGHT_MARKET_STRUCTURE = 2
WEIGHT_MSB = 2
WEIGHT_LIQUIDITY = 1
WEIGHT_FVG = 1
WEIGHT_ORDER_BLOCK = 1
WEIGHT_VOLUME = 1

# ------------------------------------------------------------
# POSITION CONFIRMATION
# ------------------------------------------------------------

CONFIRMATION_ENABLED = True

# Long için minimum teyit
LONG_CONFIRMATION_SCORE = 7

# Short için minimum teyit
SHORT_CONFIRMATION_SCORE = 7

# Alt zaman diliminde yapı teyidi zorunlu
REQUIRE_ENTRY
