import config
import re
from trading_engine import start_bot

def parse_cash_signal(text):
    try:
        upper = text.upper()
        symbol = None
        hash_match = re.search(r'\$([A-Z0-9]+)', upper)
        if hash_match: symbol = hash_match.group(1) + "USDT"
        if not symbol: return None

        side = None
        if "LONG" in upper: side = "Buy"
        elif "SHORT" in upper: side = "Sell"
        
        entry, tp, sl = None, None, None
        number_pattern = r'(?<!\d)(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)(?!\d)'
        
        for line in text.split('\n'):
            u_line = line.upper()
            if "PERCENTAGE" in u_line: continue
            matches = re.findall(number_pattern, line)
            nums = [float(m.replace(',', '')) for m in matches if float(m.replace(',', '')) > 0]
            if not nums: continue
            
            if any(k in u_line for k in ["ENTRY", "ENT", "EP "]) and not entry: entry = nums[0]
            elif any(k in u_line for k in ["TARGET", "TP", "TAKE PROFIT"]) and not tp: tp = nums[-1]
            elif any(k in u_line for k in ["STOPLOSS", "STOP LOSS", "SL", "STOP"]) and not sl: sl = nums[0]

        if not side and entry and tp: side = "Buy" if tp > entry else "Sell"
        if symbol and side and entry and tp and sl:
            return {"sym": symbol, "side": side, "entry": entry, "tp": tp, "sl": sl}
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
    'PARTIAL_TP': 0.0,    # Disable Split TP
    'TP_TARGET': 0.0,     # Irrelevant
    'USE_TRAILING': False # Disable Trailing Stop
}

if __name__ == "__main__":
    start_bot("CASH", cfg, parser=parse_cash_signal)
