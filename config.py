import os
import sys
from dotenv import load_dotenv

# Load secrets
load_dotenv()

def get_env_or_fail(key):
    value = os.getenv(key)
    if value is None:
        print(f"❌ CRITICAL ERROR: Environment variable {key} is missing.")
        sys.exit(1)
    return value

# ============================================================================
# 🤖 MAIN BOT CONFIG (Scalping / Ladder)
# ============================================================================
# SECURED: No hardcoded fallbacks for secrets
TELEGRAM_API_ID = int(get_env_or_fail('TELEGRAM_API_ID'))
TELEGRAM_API_HASH = get_env_or_fail('TELEGRAM_API_HASH')
MAIN_CHANNEL_ID = int(get_env_or_fail('MAIN_CHANNEL_ID'))

MAIN_API_KEY = get_env_or_fail('MAIN_API_KEY')
MAIN_API_SECRET = get_env_or_fail('MAIN_API_SECRET')
MAIN_TESTNET = False

# Risk Management
MAIN_RISK_MODE = "PERCENTAGE"       # "FIXED" or "PERCENTAGE"
MAIN_RISK_FACTOR = 0.10             # 10% Risk
MAIN_RISK_PER_TRADE = 450.0         # Fixed Risk in USDT (Fallback)
MAIN_MAX_POS = 75000.0              # Max position size in USDT

# Strategy: Interpolated Ladder (Legacy Logic)
# pos 0.0 = Market Price (CMP)
# pos 1.0 = Signal Entry Price
MAIN_ENTRY_LADDER = [
    {'pos': 0.0, 'weight': 2.0},  # 50% Size (Aggressive Market Entry)
    {'pos': 0.9, 'weight': 1.0},  # 25% Size (0.9 entry interpolation)
    {'pos': 1.0, 'weight': 1.0}   # 25% Size (At Signal Entry)
]

# Exits
MAIN_PARTIAL_TP = 0.50          # Take 50% profit at TP1
MAIN_TP_TARGET = 0.8            # TP1 is placed at 0.8R (0.8 * Risk Distance)

# ============================================================================
# 💵 CASH BOT CONFIG (Swing / Multi-TP)
# ============================================================================
CASH_CHANNEL_ID = int(get_env_or_fail('CASH_CHANNEL_ID'))
CASH_API_KEY = get_env_or_fail('CASH_API_KEY')
CASH_API_SECRET = get_env_or_fail('CASH_API_SECRET')
CASH_TESTNET = False

CASH_RISK_MODE = "PERCENTAGE"
CASH_RISK_FACTOR = 0.05        # 5% Risk
CASH_RISK_AMOUNT = 450.0       # Fallback
CASH_MAX_POS = 75000.0

CASH_ENTRY_LADDER = [{'pos': 1.0, 'weight': 1.0}] # Single Limit Entry
CASH_PARTIAL_PCT = 0.30        # 30% per TP target

# ============================================================================
# ❄️ KELVIN BOT CONFIG (Simple / Directional)
# ============================================================================
KELVIN_CHANNEL_ID = int(get_env_or_fail('KELVIN_CHANNEL_ID'))
KELVIN_API_KEY = get_env_or_fail('KELVIN_API_KEY')
KELVIN_API_SECRET = get_env_or_fail('KELVIN_API_SECRET')
KELVIN_TESTNET = False

KELVIN_RISK_MODE = "PERCENTAGE"
KELVIN_RISK_FACTOR = 0.05      # 5% Risk
KELVIN_RISK_AMOUNT = 450.0
KELVIN_MAX_POS = 75000.0

KELVIN_ENTRY_LADDER = [{'pos': 0.0, 'weight': 1.0}] # Single Market Entry
