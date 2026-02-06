import os
from dotenv import load_dotenv

# Load secrets from the .env file
load_dotenv()

# ============================================================================
# 🔐 SHARED SECRETS (TELEGRAM)
# ============================================================================
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")

# ============================================================================
# MASTER BYBIT KEYS 
# ============================================================================
MASTER_API_KEY = os.getenv("MASTER_API_KEY")
MASTER_API_SECRET = os.getenv("MASTER_API_SECRET")

# ============================================================================
# 🤖 MAIN BOT SETTINGS
# ============================================================================
MAIN_API_KEY = os.getenv("MAIN_API_KEY")
MAIN_API_SECRET = os.getenv("MAIN_API_SECRET")
MAIN_CHANNEL_ID = int(os.getenv("MAIN_CHANNEL_ID", 0))

# --- RISK SETTINGS ---
MAIN_RISK_MODE = "PERCENTAGE" 
MAIN_RISK_FACTOR = 0.01      
MAIN_RISK_PER_TRADE = 450.0  
MAIN_MAX_POS = 75000.0       
MAIN_PARTIAL_TP = 0.50       
MAIN_TP_TARGET = 0.8         
MAIN_TESTNET = False

# ============================================================================
# 💰 CASH BOT SETTINGS
# ============================================================================
CASH_API_KEY = os.getenv("CASH_API_KEY")
CASH_API_SECRET = os.getenv("CASH_API_SECRET")
CASH_CHANNEL_ID = int(os.getenv("CASH_CHANNEL_ID", 0))

# --- RISK SETTINGS ---
CASH_RISK_MODE = "PERCENTAGE"
CASH_RISK_FACTOR = 0.015     
CASH_RISK_AMOUNT = 450.0     
CASH_MAX_POS = 75000.0
CASH_TESTNET = False
CASH_PARTIAL_PCT = 0.30      

# ============================================================================
# 🌡️ KELVIN BOT SETTINGS
# ============================================================================
KELVIN_API_KEY = os.getenv("KELVIN_API_KEY")
KELVIN_API_SECRET = os.getenv("KELVIN_API_SECRET")
KELVIN_CHANNEL_ID = int(os.getenv("KELVIN_CHANNEL_ID", 0))

# --- RISK SETTINGS ---
KELVIN_RISK_MODE = "PERCENTAGE"
KELVIN_RISK_FACTOR = 0.02    
KELVIN_RISK_AMOUNT = 450.0   
KELVIN_MAX_POS = 75000.0
KELVIN_TESTNET = False

# ============================================================================
# 🪜 LADDER ENTRY STRATEGY
# ============================================================================
MAIN_ENTRY_LADDER = [
    {'pos': 0.0, 'weight': 2.0},
    {'pos': 0.9, 'weight': 1.0},
    {'pos': 1.0, 'weight': 1.0}
]

# ============================================================================
# 🪜 LADDER STRATEGIES (SHARED)
# ============================================================================
# Aggressive Ladder (Used by Main)
MAIN_ENTRY_LADDER = [
    {'pos': 0.0, 'weight': 2.0},  # Market Order (40%)
    {'pos': 0.9, 'weight': 1.0},  # Limit (20%)
    {'pos': 1.0, 'weight': 1.0}   # Limit (20%)
]

# Conservative Ladder (Default for Cash/Kelvin - Single Entry)
# If you want them to ladder, copy the MAIN_ENTRY_LADDER structure here.
CASH_ENTRY_LADDER = [{'pos': 0.0, 'weight': 1.0}]
KELVIN_ENTRY_LADDER = [{'pos': 0.0, 'weight': 1.0}]
