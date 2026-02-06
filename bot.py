import config
from trading_engine import start_bot

cfg = {
    'TELEGRAM_API_ID': config.TELEGRAM_API_ID,
    'TELEGRAM_API_HASH': config.TELEGRAM_API_HASH,
    'CHANNEL_ID': config.MAIN_CHANNEL_ID,
    'API_KEY': config.MAIN_API_KEY,
    'API_SECRET': config.MAIN_API_SECRET,
    'TESTNET': config.MAIN_TESTNET,
    'RISK_MODE': config.MAIN_RISK_MODE,
    'RISK_FACTOR': config.MAIN_RISK_FACTOR,
    'RISK_AMOUNT': config.MAIN_RISK_PER_TRADE,
    'MAX_POS': config.MAIN_MAX_POS,
    'LADDER': config.MAIN_ENTRY_LADDER,
    'PARTIAL_TP': 0.5,    # Enable Split TP
    'TP_TARGET': 0.8,     # 0.8R Target for first TP
    'USE_TRAILING': True  # Enable Trailing Stop
}

if __name__ == "__main__":
    start_bot("MAIN", cfg)
