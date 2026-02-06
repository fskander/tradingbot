import config
import re
from trading_engine import start_bot

def parse_cash_signal(text):
    try:
        upper = text.upper()
        symbol = None
        
        # 1. Symbol Extraction
        hash_match = re.search(r'#([A-Z0-9]+)', upper)
        if hash_match: 
            s = hash_match.group(1)
            if s != "TRADERCASH": symbol = s + "USDT"
        
        if not symbol and "BTC" in upper: symbol = "BTCUSDT"
        if not symbol: return None

        # 2. Side Extraction
        side = None
        if "BUY" in upper or "LONG" in upper: side = "Buy"
        elif "SELL" in upper or "SHORT" in upper: side = "Sell"
        
        entry, sl = None, None
        entries_list = []
        tps = []
        
        number_pattern = r'(?<!\d)(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)(?!\d)'
        
        for line in text.split('\n'):
            u_line = line.upper()
            if "PERCENTAGE" in u_line: continue
            
            matches = re.findall(number_pattern, line)
            # Clean commas (e.g. 65,000 -> 65000)
            nums = [float(m.replace(',', '')) for m in matches if float(m.replace(',', '')) > 0]
            if not nums: continue
            
            # Entry Logic (Range vs Single)
            if any(k in u_line for k in ["ENTRY", "ENT", "EP "]) and not entry:
                if len(nums) >= 2:
                    entries_list = nums[:2] 
                    entry = sum(entries_list) / 2
                else:
                    entry = nums[0]

            # SL Logic
            elif any(k in u_line for k in ["STOPLOSS", "STOP LOSS", "SL", "STOP"]) and not sl: 
                sl = nums[0]
            
            # TP Logic (Fix: Take the LAST number in the line to avoid "Target 1")
            if "TARGET" in u_line:
                tps.append(nums[-1])

        # Auto-detect side if missing
        if not side and entry and sl: 
            side = "Buy" if entry > sl else "Sell"

        if symbol and side and entry and sl:
            return {
                "sym": symbol, "side": side, "entry": entry, 
                "entries": entries_list, 
                "sl": sl, "tp": tps[-1] if tps else 0, "tps": tps 
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
    'PARTIAL_TP': config.CASH_PARTIAL_PCT,
    'TP_TARGET': 0.0,    
    'USE_TRAILING': False
}

if __name__ == "__main__":
    start_bot("CASH", cfg, parser=parse_cash_signal)
