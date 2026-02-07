import asyncio
import sys
import bot
import bot_cash
import bot_kelvin
from trading_engine import TradingBot

async def main():
    print("\n🚨 MANUAL TRADE TRIGGER (PRODUCTION MODE) 🚨")
    print("==========================================")
    print("WARNING: This will use REAL position sizes from config.py")
    print("==========================================")
    print("1. 🤖 Main Bot (Scalp/Ladder)")
    print("2. 💵 Cash Bot (Limit/Multi-TP)")
    print("3. ❄️ Kelvin Bot (Fast/Native-TP)")
    
    choice = input("\nSelect Bot (1-3): ").strip()
    
    if choice == '1':
        name = "MAIN"
        cfg = bot.cfg
        parser = bot.parse_main_signal
    elif choice == '2':
        name = "CASH"
        cfg = bot_cash.cfg
        parser = bot_cash.parse_cash_signal
    elif choice == '3':
        name = "KELVIN"
        cfg = bot_kelvin.cfg
        parser = bot_kelvin.parse_kelvin_signal
    else:
        print("❌ Invalid choice.")
        return

    print(f"\n📝 Paste {name} Signal below.")
    print("   (Type 'END' on a new line and press Enter to finish)")
    print("------------------------------------------")
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == 'END':
                break
            lines.append(line)
        except EOFError:
            break
            
    signal_text = "\n".join(lines)

    print(f"\n🚀 Initializing {name} Engine...")
    
    # Initialize Engine
    engine = TradingBot(name, cfg, custom_parser=parser)
    await engine.async_exec.init_session()
    
    # 1. Pre-load Instruments
    engine.load_instruments()

    # 2. FIX: Fetch Wallet Balance Manually
    print("   💰 Fetching Wallet Balance...")
    try:
        r = engine.sess.get_wallet_balance(accountType="UNIFIED", coin="USDT")
        if r['retCode'] == 0:
            equity = float(r['result']['list'][0]['totalEquity'])
            engine.wallet_balance = equity
            print(f"   ✅ Balance: ${engine.wallet_balance:.2f}")
            
            # Show Risk Calculation Preview
            if engine.risk_mode == "PERCENTAGE":
                calc_risk = engine.wallet_balance * engine.risk_factor
                print(f"   📊 Dynamic Risk ({engine.risk_factor*100}%): ${calc_risk:.2f}")
            else:
                print(f"   📊 Fixed Risk: ${engine.risk_fixed:.2f}")
        else:
            print(f"   ⚠️ Balance fetch failed: {r['retMsg']}")
    except Exception as e:
        print(f"   ⚠️ Balance fetch error: {e}")

    print(f"\n🔍 Parsing Signal...")
    sig = parser(signal_text)
    
    if not sig:
        print("❌ PARSER FAILED. The bot would ignore this message.")
        await engine.async_exec.session.close()
        return

    print(f"✅ SUCCESS! Parsed Data:")
    print(f"   Symbol: {sig['sym']}")
    print(f"   Side:   {sig['side']}")
    print(f"   Entry:  {sig['entry']} ({-1 if sig['entry'] == -1 else ''})")
    print(f"   TPs:    {sig.get('tps', sig.get('tp'))}")
    print(f"   SL:     {sig['sl']}")

    confirm = input(f"\n⚠️  EXECUTE on BYBIT with REAL MONEY? (y/n): ").lower()
    
    if confirm == 'y':
        print("\n🚀 SENDING ORDERS...")
        await engine.execute_trade(sig)
        print("\n✅ Execution Logic Complete.")
    else:
        print("\n🚫 Cancelled.")

    await engine.async_exec.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
