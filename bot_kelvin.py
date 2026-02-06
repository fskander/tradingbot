import config
import re
from trading_engine import start_bot

def parse_kelvin_signal(text):
    try:
        upper = text.upper()
        symbol = None
        
        # 1. Try PAIR: X/Y
        if "PAIR:" in upper:
            match = re.search(r'PAIR:.*?([A-Z0-9]+)', upper)
            if match: symbol = match.group(1) + "USDT"
            
        # 2. Try X/USDT
        if not symbol:
            match = re.search(r'([A-Z0-9]+)/USDT', upper)
            if match: symbol = match.group(1) + "USDT"
            
        # 3. Try X USDT (Space separated)
        if not symbol:
            match = re.search(r'([A-Z0-9]+)\s+USDT', upper)
            if match: symbol = match.group(1) + "USDT"

        if not symbol: return None

        side = None
        if "LONG" in upper or "BUY" in upper: side = "Buy"
        elif "SHORT" in upper or "SELL" in upper: side = "Sell"
        
        entry, sl = None, None
        possible_tps = []
        
        number_pattern = r'(?<!\d)(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)(?!\d)'
        
        for line in text.split('\n'):
            u_line = line.upper()
            matches = re.findall(number_pattern, line)
            nums = [float(m.replace(',', '')) for m in matches if float(m.replace(',', '')) > 0]
            if not nums: continue
            
            if "ENTRY" in u_line and not entry: entry = nums[0]
            elif "STOP" in u_line and not sl: sl = nums[0]
            elif "TARGET" in u_line or "TP" in u_line: 
                possible_tps.extend(nums)

        if not side and entry and sl: side = "Buy" if entry > sl else "Sell"

        final_tp = 0
        if possible_tps:
            # Smart TP: If Short, take the Lowest. If Long, take Highest.
            if side == "Buy": final_tp = max(possible_tps)
            elif side == "Sell": final_tp = min(possible_tps)

        if symbol and side and entry and sl:
            return {"sym": symbol, "side": side, "entry": entry, "tp": final_tp, "sl": sl}
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
    'PARTIAL_TP': 0.0,
    'TP_TARGET': 0.0,   
    'USE_TRAILING': False
}

if __name__ == "__main__":
    start_bot("KELVIN", cfg, parser=parse_kelvin_signal)
