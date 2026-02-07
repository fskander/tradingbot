import asyncio
import config
import bot          # Main Bot File
import bot_cash     # Cash Bot File
import bot_kelvin   # Kelvin Bot File
from trading_engine import TradingBot

# ==============================================================================
# 1. THE SIGNALS
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
# 2. CONFIGS (Safety Overrides)
# ==============================================================================
base_overrides = {
    'RISK_MODE': 'FIXED', 
    'RISK_AMOUNT': 200.0,   # Safe $6 test risk
    'RISK_FACTOR': 0.0,
    'MAX_POS': 20000.0
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
    'TESTNET': config.CASH_TESTNET, 'LADDER': [{'pos': 1.0, 'weight': 1.0}],
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
# 3. TEST RUNNER
# ==============================================================================
async def run_test(name, parser_func, signal_text, cfg):
    print(f"\n---------------------------------------------------")
    print(f"🤖 TESTING {name} BOT...")
    print(f"---------------------------------------------------")
    
    # 1. Init Engine
    engine = TradingBot(name, cfg, custom_parser=parser_func)
    await engine.async_exec.init_session()
    
    # 2. Pre-load Cache (Test v9.0 Feature)
    print("   📦 Pre-loading instruments...")
    engine.load_instruments()
    
    # 3. Parse (Using the REAL imported parser)
    print("   🔎 Parsing...")
    sig = parser_func(signal_text)
    
    if sig:
        print(f"   ✅ SUCCESS: {sig}")
        print("   🚀 Executing Trade...")
        await engine.execute_trade(sig)
    else:
        print("   ❌ PARSE FAILED")
        
    await engine.async_exec.session.close()

async def main():
    print("🧪 STARTING PRODUCTION LOGIC TEST (Risk: $6.00)")
    
    # Test 1: Main (Regex Parser)
    await run_test("MAIN", bot.parse_main_signal, SIGNAL_MAIN, cfg_main)

    # Test 2: Cash (Multi-TP Parser)
    await run_test("CASH", bot_cash.parse_cash_signal, SIGNAL_CASH, cfg_cash)

    # Test 3: Kelvin (Space-Separated Parser)
    await run_test("KELVIN", bot_kelvin.parse_kelvin_signal, SIGNAL_KELVIN, cfg_kelvin)

    print("\n✅ ALL TESTS COMPLETE.")

if __name__ == "__main__":
    asyncio.run(main())
