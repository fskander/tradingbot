import config
import re
from trading_engine import start_bot

def parse_cash_signal(text):
    try:
        upper = text.upper()
        symbol = None
        
        # 1. Symbol
        hash_match = re.search(r'#([A-Z0-9]+)', upper)
        if hash_match: 
            s = hash_match.group(1)
            if s == "TRADERCASH": return None # Ignore footer tag
            symbol = s + "USDT"
        
        # Fallback if #BTC not found but text mentions BTC
        if not symbol and "BTC" in upper: symbol = "BTCUSDT"
        
        if not symbol: return None

        # 2. Side
        side = None
        if "BUY" in upper or "LONG" in upper: side = "Buy"
        elif "SELL" in upper or "SHORT" in upper: side = "Sell"
        
        entry, sl = None, None
        tps = []
        
        number_pattern = r'(?<!\d)(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)(?!\d)'
        
        for line in text.split('\n'):
            u_line = line.upper()
            if "PERCENTAGE" in u_line: continue
            
            matches = re.findall(number_pattern, line)
            nums = [float(m.replace(',', '')) for m in matches if float(m.replace(',', '')) > 0]
            if not nums: continue
            
            # Entry / SL
            if any(k in u_line for k in ["ENTRY", "ENT", "EP "]) and not entry: entry = nums[0]
            elif any(k in u_line for k in ["STOPLOSS", "STOP LOSS", "SL", "STOP"]) and not sl: sl = nums[0]
            
            # Multi-Target Capture
            if "TARGET" in u_line:
                tps.append(nums[0])

        if not side and entry and sl: 
            side = "Buy" if entry > sl else "Sell"

        if symbol and side and entry and sl and len(tps) > 0:
            return {
                "sym": symbol, "side": side, "entry": entry, 
                "sl": sl, "tp": tps[-1], "tps": tps 
            }
        return None
    except: return None

cfg = {
    'TELEGRAM_API_ID': config.TELEGRAM_API_ID,
    'TELEGRAM_API_HASH': config.TELEGRAM_API_HASH,
    'CHANNEL_ID': config.CASH_CHANNEL_ID,
    'API_KEY': config.CASH_API_KEY,
    'API_SECRET': config.CASH_API_SECRET,
    'TESTNET': config.CASH_TESTNET,
    'RISK_MODE': config.CASH_RISK_MODE,
    'RISK_FACTOR': config.CASH_RISK_FACTOR,
    'RISK_AMOUNT': config.CASH_RISK_AMOUNT,
    'MAX_POS': config.CASH_MAX_POS,
    'LADDER': config.CASH_ENTRY_LADDER,
    'PARTIAL_TP': config.CASH_PARTIAL_PCT, # e.g. 0.30
    'TP_TARGET': 0.0,     # Not used in Multi-TP mode
    'USE_TRAILING': False
}

if __name__ == "__main__":
    start_bot("CASH", cfg, parser=parse_cash_signal)
