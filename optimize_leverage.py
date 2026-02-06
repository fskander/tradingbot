import os, time, sys, json
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

# 1. Load Secrets
load_dotenv()
API_KEY = os.getenv('MAIN_API_KEY')
API_SECRET = os.getenv('MAIN_API_SECRET')
TESTNET = str(os.getenv('MAIN_TESTNET', 'False')).lower() == 'true'
TARGET_SIZE = 30000.0 
CACHE_FILE = "leverage_cache.json"

# 2. Safety Check
if not API_KEY or not API_SECRET:
    print("❌ CRITICAL ERROR: API Keys not found in .env")
    sys.exit(1)

sess = HTTP(testnet=TESTNET, api_key=API_KEY, api_secret=API_SECRET)

# --- CACHE FUNCTIONS ---
def load_cache():
    if not os.path.exists(CACHE_FILE): return {}
    try:
        with open(CACHE_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_cache(data):
    try:
        with open(CACHE_FILE, 'w') as f: json.dump(data, f)
    except Exception as e: print(f"⚠️ Cache Save Failed: {e}")

# --- OPTIMIZER LOGIC ---
def get_optimized_leverage(symbol):
    try:
        r = sess.get_risk_limit(category="linear", symbol=symbol)
        tiers = r['result']['list']
        best_leverage = 1.0
        found_valid_tier = False

        for t in tiers:
            max_lev = float(t.get('maxLeverage', 1))
            limit_val = float(t.get('riskLimitValue', 0))
            if limit_val >= TARGET_SIZE:
                found_valid_tier = True
                if max_lev > best_leverage: best_leverage = max_lev
        
        if found_valid_tier: return str(int(best_leverage))
        return "10"
    except Exception as e: return "10"

def main():
    # --- CHECK FOR FORCE FLAG ---
    force_mode = "--force" in sys.argv
    mode_str = "💪 FORCE MODE (Ignoring Cache)" if force_mode else "⚡ SMART MODE (Using Cache)"
    
    print(f"🚀 LEVERAGE OPTIMIZER | {mode_str}")
    print("----------------------------------------------------------")
    
    cache = load_cache()
    if not force_mode:
        print(f"💾 Loaded Cache: {len(cache)} symbols.")

    try:
        r = sess.get_instruments_info(category="linear", limit=1000)
        symbols = [i['symbol'] for i in r['result']['list'] if i['quoteCoin'] == 'USDT']
    except Exception as e:
        print(f"❌ Failed to fetch symbols: {e}")
        return

    print(f"📉 Market has {len(symbols)} pairs. Scanning...")
    
    updates_count = 0

    for i, sym in enumerate(symbols):
        # --- SMART SKIP ---
        # Only skip if NOT in force mode AND symbol is in cache
        if not force_mode and sym in cache:
            continue

        target_lev = get_optimized_leverage(sym)
        status = ""
        success = False
        
        try:
            # Try to set leverage
            sess.set_leverage(category="linear", symbol=sym, buyLeverage=target_lev, sellLeverage=target_lev)
            status = f"✅ {sym} -> {target_lev}x"
            success = True
        except Exception as e:
            msg = str(e)
            if "not modified" in msg: 
                status = f"🆗 {sym} verified {target_lev}x"
                success = True
            elif "Too many visits" in msg:
                print(f"⚠️ RATE LIMIT. Pausing 5s...")
                time.sleep(5)
                try:
                    sess.set_leverage(category="linear", symbol=sym, buyLeverage=target_lev, sellLeverage=target_lev)
                    status = f"✅ {sym} -> {target_lev}x (Retry)"
                    success = True
                except: status = f"⏭️ Skipped {sym} (Rate Limit)"
            else: status = f"⚠️ {sym}: {msg}"

        if success:
            try:
                sess.switch_margin_mode(category="linear", symbol=sym, tradeMode=0, buyLeverage=target_lev, sellLeverage=target_lev)
            except: pass
            
            # Update cache locally
            cache[sym] = target_lev
            updates_count += 1

        print(f"[{i+1}/{len(symbols)}] {status}")
        
        if updates_count % 10 == 0 and updates_count > 0:
            save_cache(cache)

        # Sleep to be nice to API
        time.sleep(0.12) 

    save_cache(cache)
    print("---------------------------------------------")
    print(f"✅ DONE. Processed {updates_count} symbols.")

if __name__ == "__main__":
    main()
