import bot_kelvin
import time

print("🧪 STARTING MANUAL TEST...")

# --- STEP 1: SAFETY OVERRIDE ---
# We force the risk to be $10 only for this test run.
print("📉 Overriding Risk Amount to $10 for safety...")
bot_kelvin.RISK_AMOUNT = 10.0 

# --- STEP 2: DEFINE SIGNALS ---
# These mimic exactly what the parser would output from your text
sig_popcat = {
    "sym": "POPCATUSDT",   # INTENTIONAL: We use the wrong name to test the auto-fix
    "side": "Buy",
    "entry": 0.0742,
    "tp": 0.1040,
    "sl": 0.0712
}

sig_render = {
    "sym": "RENDERUSDT",
    "side": "Buy",
    "entry": 1.916,
    "tp": 2.146,
    "sl": 1.839
}

# --- STEP 3: EXECUTE ---
print("\n-------------------------------------------------")
print("1️⃣  TESTING POPCAT (Goal: Auto-map to 1000POPCAT)")
print("-------------------------------------------------")
bot_kelvin.execute_trade(sig_popcat)

print("\n-------------------------------------------------")
print("2️⃣  TESTING RENDER (Goal: Pass Logic Check)")
print("-------------------------------------------------")
bot_kelvin.execute_trade(sig_render)

print("\n✅ TEST COMPLETE.")
