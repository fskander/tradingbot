import asyncio
import config
import re
from trading_engine import TradingBot

# ==============================================================================
# 1. DEFINE THE SIGNALS (Past/Test Data)
# ==============================================================================

SIGNAL_MAIN = """
$XRP Scalp Long Setup:

➡️ Entry: CMP
➡️ TP> 1.5917
➡️ SL> 1.3708
➡️ SL % > 3%

Trying a scalp here with less risk and pure risk management

#TraderGauls 🎭
"""

SIGNAL_CASH = """
#BTC Limit Buy Order

well i see now a Rejection from the VAL of the whole Range which could bring BTC again lower.

i hold the SL tight as this could also bounce back again lower, but i expect a bit more rally until we see again a new low.

📈 Entry: 63936.1
🛑 SL: 62646.7

🎯 Target 1: 65528.0
🎯 Target 2: 69519.0
🎯 Target 3: 72393.3

#TraderCash
"""

SIGNAL_KELVIN = """
SOL USDT 
(SHORT )
ENTRY :  102.824 
TARGET : 67.364
STOPLOSS : 110.00
"""

# ==============================================================================
# 2. DEFINE CUSTOM PARSERS (Copied from your bots)
# ==============================================================================

def parse_cash_signal(text):
    try:
        upper = text.upper()
        symbol = None
        hash_match = re.search(r'#([A-Z0-9]+)', upper)
        if hash_match: 
            s = hash_match.group(1)
            if s != "TRADERCASH": symbol = s + "USDT"
        if not symbol and "BTC" in upper: symbol = "BTCUSDT"
        if not symbol: return None

        side = "Buy" if "BUY" in upper or "LONG" in upper else "Sell" if "SELL" in upper or "SHORT" in upper else None
        entry, sl, tps = None, None, []
        entries_list = []
        number_pattern = r'(?<!\d)(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)(?!\d)'
        
        for line in text.split('\n'):
            u_line = line.upper()
            if "PERCENTAGE" in u_line: continue
            matches = re.findall(number_pattern, line)
            nums = [float(m.replace(',', '')) for m in matches if float(m.replace(',', '')) > 0]
            if not nums: continue
            
            if any(k in u_line for k in ["ENTRY", "ENT", "EP "]) and not entry:
                if len(nums) >= 2: entries_list = nums[:2]; entry = sum(entries_list)/2
                else: entry = nums[0]
            elif any(k in u_line for k in ["STOPLOSS", "STOP LOSS", "SL", "STOP"]) and not sl: sl = nums[0]
            if "TARGET" in u_line: tps.append(nums[0])

        if not side and entry and sl: side = "Buy" if entry > sl else "Sell"

        if symbol and side and entry and sl:
            return {
                "sym": symbol, "side": side, "entry": entry, 
                "entries": entries_list, "sl": sl, "tp": tps[-1] if tps else 0, "tps": tps 
            }
        return None
    except: return None

def parse_kelvin_signal(text):
    try:
        upper = text.upper()
        symbol = None
        if "PAIR:" in upper:
            match = re.search(r'PAIR:.*?([A-Z0-9]+)', upper)
            if match: symbol = match.group(1) + "USDT"
        if not symbol:
            match = re.search(r'([A-Z0-9]+)/USDT', upper)
            if match: symbol = match.group(1) + "USDT"
        if not symbol: return None

        side = None
        if "LONG" in upper or "BUY" in upper: side = "Buy"
        elif "SHORT" in upper or "SELL" in upper: side = "Sell"
        
        entry, sl, possible_tps = None, None, []
        number_pattern = r'(?<!\d)(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)(?!\d)'
        
        for line in text.split('\n'):
            u_line = line.upper()
            matches = re.findall(number_pattern, line)
            nums = [float(m.replace(',', '')) for m in matches if float(m.replace(',', '')) > 0]
            if not nums: continue
            
            if "ENTRY" in u_line and not entry: entry = nums[0]
            elif "STOP" in u_line and not sl: sl = nums[0]
            elif "TARGET" in u_line or "TP" in u_line: possible_tps.extend(nums)

        if not side and entry and sl: side = "Buy" if entry > sl else "Sell"
        final_tp = 0
        if possible_tps and side == "Buy": final_tp = max(possible_tps)
        elif possible_tps and side == "Sell": final_tp = min(possible_tps)

        if symbol and side and entry and sl:
            return {"sym": symbol, "side": side, "entry": entry, "tp": final_tp, "sl": sl}
        return None
    except: return None

# ==============================================================================
# 3. GENERATE SAFE CONFIGS (Risk $6.00 Only)
# ==============================================================================
base_overrides = {
    'RISK_MODE': 'FIXED', 
    'RISK_AMOUNT': 6.0,   # Minimum risk
    'RISK_FACTOR': 0.0,
    'MAX_POS': 20.0
}

cfg_main = {
    'TELEGRAM_API_ID': config.TELEGRAM_API_ID, 'TELEGRAM_API_HASH': config.TELEGRAM_API_HASH,
    'CHANNEL_ID': config.MAIN_CHANNEL_ID, 'API_KEY': config.MAIN_API_KEY, 'API_SECRET': config.MAIN_API_SECRET,
    'TESTNET': config.MAIN_TESTNET, 'LADDER': config.MAIN_ENTRY_LADDER,
    'PARTIAL_TP': config.MAIN_PARTIAL_TP, 'TP_TARGET': config.MAIN_TP_TARGET, 'USE_TRAILING': True,
    **base_overrides
}

cfg_cash = {
    'TELEGRAM_API_ID': config.TELEGRAM_API_ID, 'TELEGRAM_API_HASH': config.TELEGRAM_API_HASH,
    'CHANNEL_ID': config.CASH_CHANNEL_ID, 'API_KEY': config.CASH_API_KEY, 'API_SECRET': config.CASH_API_SECRET,
    'TESTNET': config.CASH_TESTNET, 'LADDER': config.CASH_ENTRY_LADDER,
    'PARTIAL_TP': config.CASH_PARTIAL_PCT, 'TP_TARGET': 0.0, 'USE_TRAILING': False,
    **base_overrides
}

cfg_kelvin = {
    'TELEGRAM_API_ID': config.TELEGRAM_API_ID, 'TELEGRAM_API_HASH': config.TELEGRAM_API_HASH,
    'CHANNEL_ID': config.KELVIN_CHANNEL_ID, 'API_KEY': config.KELVIN_API_KEY, 'API_SECRET': config.KELVIN_API_SECRET,
    'TESTNET': config.KELVIN_TESTNET, 'LADDER': config.KELVIN_ENTRY_LADDER,
    'PARTIAL_TP': 0.0, 'TP_TARGET': 0.0, 'USE_TRAILING': False,
    **base_overrides
}

# ==============================================================================
# 4. EXECUTION LOOP
# ==============================================================================
async def main():
    print("\n🧪 STARTING BOT LOGIC TEST (Risk: $6.00)")
    print("========================================")

    # --- TEST 1: MAIN BOT ---
    print("\n🤖 1. Testing MAIN BOT (Scalp Logic)...")
    bot1 = TradingBot("MAIN", cfg_main) # Uses default parser
    await bot1.async_exec.init_session()
    
    # Manually parsing via default logic inside engine? 
    # Actually Main uses engine default. We can call bot1.default_parser(text)
    sig1 = bot1.default_parser(SIGNAL_MAIN)
    if sig1:
        print(f"   ✅ Parsed: {sig1}")
        # Note: XRP price might be different, let's force current price check
        await bot1.execute_trade(sig1)
    else:
        print("   ❌ Parse Failed")
    await bot1.async_exec.session.close()


    # --- TEST 2: CASH BOT ---
    print("\n💵 2. Testing CASH BOT (Multi-TP Logic)...")
    bot2 = TradingBot("CASH", cfg_cash, custom_parser=parse_cash_signal)
    await bot2.async_exec.init_session()
    
    sig2 = parse_cash_signal(SIGNAL_CASH)
    if sig2:
        print(f"   ✅ Parsed: {sig2['sym']} {sig2['side']} | Targets: {sig2['tps']}")
        # Note: BTC price 63k is far from current market. 
        # If current > 63k, Limit orders will be placed.
        await bot2.execute_trade(sig2)
    else:
        print("   ❌ Parse Failed")
    await bot2.async_exec.session.close()


    # --- TEST 3: KELVIN BOT ---
    print("\n❄️ 3. Testing KELVIN BOT (Single TP Logic)...")
    bot3 = TradingBot("KELVIN", cfg_kelvin, custom_parser=parse_kelvin_signal)
    await bot3.async_exec.init_session()

    sig3 = parse_kelvin_signal(SIGNAL_KELVIN)
    if sig3:
        print(f"   ✅ Parsed: {sig3['sym']} {sig3['side']} | Entry: {sig3['entry']} | TP: {sig3['tp']}")
        # Note: SOL Short at 102. If current is 200, this is a deep Limit Sell.
        await bot3.execute_trade(sig3)
    else:
        print("   ❌ Parse Failed")
    await bot3.async_exec.session.close()

    print("\n========================================")
    print("✅ TEST COMPLETE. Check Bybit Orders.")

if __name__ == "__main__":
    asyncio.run(main())
