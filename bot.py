import config
import re
import builtins
from datetime import datetime
from trading_engine import start_bot

# ==============================================================================
# 1. RESTORE VERBOSE LOGGING (Global Print Override)
# ==============================================================================
def log(*args, **kwargs):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    builtins.original_print(f"{timestamp} [MAIN]", *args, **kwargs)

if not hasattr(builtins, 'original_print'):
    builtins.original_print = print
    builtins.print = log

print("✅ Verbose Logging Restored")

# ==============================================================================
# 2. RESTORE ORIGINAL REGEX PARSER
# ==============================================================================
# This pattern matches "$COIN Buying Setup" or "SHORT COIN", etc.
REGEX_PATTERN = re.compile(r'(?:\$)?([A-Z0-9]+)(.{0,100}?(?:Buying|Buy|Short|Sell|Long))', re.IGNORECASE | re.DOTALL)

def parse_main_signal(t):
    try:
        # 1. Pattern Match for Symbol & Side
        m = REGEX_PATTERN.search(t)
        if not m: return None
        
        sym = m.group(1).upper() + "USDT"
        phrase = m.group(2).upper()
        
        if "BUY" in phrase or "LONG" in phrase: side = "Buy"
        elif "SELL" in phrase or "SHORT" in phrase: side = "Sell"
        else: return None

        # 2. Extract Numbers (Entry, TP, SL)
        # Scan for "CMP", "Entry", "Limit", etc.
        is_cmp = "CMP" in t.upper() or "MARKET" in t.upper()
        
        # Regex to find entry price numbers
        p1 = re.search(r'(?:til{1,2}|and|&|limit|entry|at|-)\s*[^\d\n]*([\d\.]+)', t, re.IGNORECASE)
        val_price = float(p1.group(1)) if p1 else None
        
        entry = None
        entries_list = []
        
        if is_cmp:
            # -1 signals the Engine to use Current Market Price
            entry = -1 
            if val_price: # If they said "CMP till 0.50", treat 0.50 as top of range
                entries_list = [-1, val_price] 
        elif val_price:
            entry = val_price

        # Extract TP
        tp_m = re.search(r'(?:TP|Target|Tgt|Goal)\s*[^\d\n]*([\d\.]+)', t, re.IGNORECASE)
        tp_val = float(tp_m.group(1)) if tp_m else None
        
        # Extract SL
        sl_m = re.search(r'(?:SL|Stop|Loss)\s*[^\d\n]*([\d\.]+)', t, re.IGNORECASE)
        sl_val = float(sl_m.group(1)) if sl_m else None
        
        # 3. Construct Signal Object
        if sym and side and sl_val:
            return {
                "sym": sym,
                "side": side,
                "entry": entry if entry is not None else 0,
                "entries": entries_list,
                "tp": tp_val if tp_val else 0,
                "sl": sl_val
            }
        return None
    except Exception as e:
        print(f"⚠️ Parser Exception: {e}")
        return None

# ==============================================================================
# 3. CONFIGURATION & START
# ==============================================================================
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
    'PARTIAL_TP': config.MAIN_PARTIAL_TP,
    'TP_TARGET': config.MAIN_TP_TARGET,
    'USE_TRAILING': True
}

if __name__ == "__main__":
    # Pass the specialized parser to the v8 Engine
    start_bot("MAIN", cfg, parser=parse_main_signal)
