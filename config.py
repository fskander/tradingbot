import os
from dotenv import load_dotenv

# Load secrets
load_dotenv()

# ============================================================================
# 🤖 MAIN BOT CONFIG (Scalping / Ladder)
# ============================================================================
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID', '21596700'))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', 'a95632eb991ebcc0368c93540b61501c')
MAIN_CHANNEL_ID = int(os.getenv('MAIN_CHANNEL_ID', '-1002260702759'))

MAIN_API_KEY = os.getenv('MAIN_API_KEY')
MAIN_API_SECRET = os.getenv('MAIN_API_SECRET')
MAIN_TESTNET = False

# Risk Management
MAIN_RISK_MODE = "FIXED"       # "FIXED" or "PERCENTAGE"
MAIN_RISK_FACTOR = 0.01        # 1% risk if PERCENTAGE mode
MAIN_RISK_PER_TRADE = 450.0    # Fixed Risk in USDT (Fallback)
MAIN_MAX_POS = 75000.0         # Max position size in USDT

# Strategy: Interpolated Ladder (Legacy Logic)
# pos 0.0 = Market Price (CMP)
# pos 1.0 = Signal Entry Price
# weight = How much of the total size to put at this step
MAIN_ENTRY_LADDER = [
    {'pos': 0.0, 'weight': 2.0},  # 50% Size (Aggressive Market Entry)
    {'pos': 0.5, 'weight': 1.0},  # 25% Size (Halfway to Entry)
    {'pos': 1.0, 'weight': 1.0}   # 25% Size (At Signal Entry)
]

# Exits
MAIN_PARTIAL_TP = 0.50         # Take 50% profit at TP1
MAIN_TP_TARGET = 0.8           # TP1 is placed at 0.8R (0.8 * Risk Distance)

# ============================================================================
# 💵 CASH BOT CONFIG (Swing / Multi-TP)
# ============================================================================
CASH_CHANNEL_ID = int(os.getenv('CASH_CHANNEL_ID', '-1002447666487'))
CASH_API_KEY = os.getenv('CASH_API_KEY')
CASH_API_SECRET = os.getenv('CASH_API_SECRET')
CASH_TESTNET = False

CASH_RISK_MODE = "PERCENTAGE"
CASH_RISK_FACTOR = 0.015       # 1.5% Risk
CASH_RISK_AMOUNT = 450.0       # Fallback
CASH_MAX_POS = 75000.0

CASH_ENTRY_LADDER = [{'pos': 0.0, 'weight': 1.0}] # Single Entry
CASH_PARTIAL_PCT = 0.30        # 30% per TP target

# ============================================================================
# ❄️ KELVIN BOT CONFIG (Simple / Directional)
# ============================================================================
KELVIN_CHANNEL_ID = int(os.getenv('KELVIN_CHANNEL_ID', '-1002237608034'))
KELVIN_API_KEY = os.getenv('KELVIN_API_KEY')
KELVIN_API_SECRET = os.getenv('KELVIN_API_SECRET')
KELVIN_TESTNET = False

KELVIN_RISK_MODE = "PERCENTAGE"
KELVIN_RISK_FACTOR = 0.015     # 1.5% Risk
KELVIN_RISK_AMOUNT = 450.0
KELVIN_MAX_POS = 75000.0

KELVIN_ENTRY_LADDER = [{'pos': 0.0, 'weight': 1.0}] # Single Entry
