import bot_kelvin
import time

print("🚀 MANUALLY TRIGGERING BTC SWING SETUP...")

# Define the signal manually
# Note: We manually add "USDT" here to be safe, though your new parser would do it too.
sig = {
    "sym": "BTCUSDT",
    "side": "Buy",
    "entry": 68020.0,
    "tp": 109717.0,
    "sl": 63584.0
}

# Execute the trade using Kelvin's logic
bot_kelvin.execute_trade(sig)

print("✅ Execution script finished.")
