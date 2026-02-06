import asyncio
import time
import config
from trading_engine import TradingBot

# --- 1. DEFINE A SAFE "MICRO" CONFIG ---
# We verify the main bot config, but we OVERRIDE risk for safety.
test_cfg = {
    'TELEGRAM_API_ID': config.TELEGRAM_API_ID,
    'TELEGRAM_API_HASH': config.TELEGRAM_API_HASH,
    'CHANNEL_ID': config.MAIN_CHANNEL_ID,
    'API_KEY': config.MAIN_API_KEY,
    'API_SECRET': config.MAIN_API_SECRET,
    'TESTNET': config.MAIN_TESTNET,
    
    # 🛡️ SAFETY OVERRIDES 🛡️
    'RISK_MODE': 'FIXED', 
    'RISK_AMOUNT': 6.0,          # Only risk $6.00 (approx min order size)
    'RISK_FACTOR': 0.0,          # Ignore percentage
    'MAX_POS': 20.0,             # Hard cap at $20 position
    
    # Strategy Settings (Same as Main Bot)
    'LADDER': config.MAIN_ENTRY_LADDER,
    'PARTIAL_TP': 0.5,
    'TP_TARGET': 0.8,
    'USE_TRAILING': True
}

# --- 2. DEFINE A TEST SIGNAL ---
# We use DOGE because it has low min order size.
# We set Entry = Current Market Price (approx) so it fills immediately (Market Order)
# or places Limits very close.
TEST_SIGNAL = {
    "sym": "DOGEUSDT",
    "side": "Buy",
    "entry": 0.10,   # <--- CHANGE THIS to be close to current price for limit testing
    "sl": 0.09,
    "tp": 0.15
}

async def run_benchmark():
    print(f"\n⏱️  STARTING LATENCY TEST (Risk: ${test_cfg['RISK_AMOUNT']})")
    print("---------------------------------------------------")
    
    # 1. Initialize Bot
    bot = TradingBot("BENCHMARK", test_cfg)
    await bot.async_exec.init_session()
    
    # 2. Get Current Price (to make signal realistic)
    print("🔎 Fetching current price...")
    r = await bot.async_exec.session.get(f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={TEST_SIGNAL['sym']}")
    data = await r.json()
    cur_price = float(data['result']['list'][0]['lastPrice'])
    print(f"   Current DOGE Price: {cur_price}")
    
    # 3. Update Signal to be actionable
    TEST_SIGNAL['entry'] = cur_price
    TEST_SIGNAL['sl'] = cur_price * 0.95  # 5% SL
    TEST_SIGNAL['tp'] = cur_price * 1.10  # 10% TP
    
    print(f"🎯 Signal Adjusted: Entry {TEST_SIGNAL['entry']} | SL {TEST_SIGNAL['sl']:.4f}")
    
    # 4. EXECUTE & MEASURE
    print("\n🚀 FIRING TRADE NOW...")
    start_time = time.perf_counter()
    
    # --- THE CRITICAL CALL ---
    await bot.execute_trade(TEST_SIGNAL)
    # -------------------------
    
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    print("---------------------------------------------------")
    print(f"✅ EXECUTION COMPLETE")
    print(f"⏱️  Total Time: {duration:.4f} seconds")
    print("---------------------------------------------------")

    # Cleanup
    await bot.async_exec.session.close()

if __name__ == "__main__":
    asyncio.run(run_benchmark())
