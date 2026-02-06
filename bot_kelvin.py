import config
import re
from trading_engine import start_bot

# --- SPECIFIC PARSER FOR KELVIN CHANNEL ---
def parse_kelvin_signal(text):
    try:
        upper = text.upper()
        symbol = None
        
        # Kelvin often uses "Pair: BTC/USDT"
        if "PAIR:" in upper:
            match = re.search(r'PAIR:.*?([A-Z0-9]+)', upper)
            if match: symbol = match.group(1) + "USDT"
        
        if not symbol:
            # Fallback to looking for /USDT
            match = re.search(r'([A-Z0-9]+)/USDT', upper)
            if match: symbol = match.group(1) + "USDT"

        if not symbol: return None

        side = None
        if "LONG" in upper or "BUY" in upper: side = "Buy"
        elif "SHORT" in upper or "SELL" in upper: side = "Sell"
        
        entry, tp, sl = None, None, None
        number_pattern = r'(?<!\d)(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)(?!\d)'
        
        for line in text.split('\n'):
            u_line = line.upper()
            matches = re.findall(number_pattern, line)
            nums = [float(m.replace(',', '')) for m in matches if float(m.replace(',', '')) > 0]
            if not nums: continue
            
            if "ENTRY" in u_line and not entry: entry = nums[0]
            elif "TARGET" in u_line and not tp: tp = nums[-1] # Aim high
            elif "STOP" in u_line and not sl: sl = nums[0]

        if not side and entry and tp: side = "Buy" if tp > entry else "Sell"

        if symbol and side and entry and tp and sl:
            return {"sym": symbol, "side": side, "entry": entry, "tp": tp, "sl": sl}
        return None
    except: return None

cfg = {
    'TELEGRAM_API_ID': config.TELEGRAM_API_ID,
    'TELEGRAM_API_HASH': config.TELEGRAM_API_HASH,
    'CHANNEL_ID': config.KELVIN_CHANNEL_ID,
    'API_KEY': config.KELVIN_API_KEY,
    'API_SECRET': config.KELVIN_API_SECRET,
    'TESTNET': config.KELVIN_TESTNET,
    'RISK_MODE': config.KELVIN_RISK_MODE,
    'RISK_FACTOR': config.KELVIN_RISK_FACTOR,
    'RISK_AMOUNT': config.KELVIN_RISK_AMOUNT,
    'MAX_POS': config.KELVIN_MAX_POS,
    'LADDER': config.KELVIN_ENTRY_LADDER,
    'PARTIAL_TP': 0.5,
    'TP_TARGET': 0.8
}

if __name__ == "__main__":
    start_bot("KELVIN", cfg, parser=parse_kelvin_signal)
