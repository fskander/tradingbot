import bot
import asyncio

# --- TEST SIGNAL SETTINGS ---
TEST_SIGNAL = {
    "sym": "DOGEUSDT",   
    "side": "Buy",       
    "entry": 0.12,       # Make sure this is close to market price
    "tp": 0.20,          
    "sl": 0.05           
}

async def main():
    print(f"🔫 MANUALLY FIRING TRADE FOR {TEST_SIGNAL['sym']} (ASYNC MODE)...")
    print("----------------------------------------------------")
    
    # We must await the function now
    await bot.execute_trade(TEST_SIGNAL)
    
    # Clean up the session if it was opened
    if bot.async_exec.session:
        await bot.async_exec.session.close()

if __name__ == "__main__":
    asyncio.run(main())
