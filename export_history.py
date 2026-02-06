import gspread
import time
import os
from pybit.unified_trading import HTTP
from datetime import datetime, timedelta
import config 

# ================= CONFIGURATION =================
SHEET_NAME = "Bybit Trading History" 

# Define the accounts to process
ACCOUNTS = [
    {
        "name": "KELVIN/CASH",
        "api_key": config.KELVIN_API_KEY,
        "api_secret": config.KELVIN_API_SECRET,
        "tab_name": "Bots"
    },
    {
        "name": "MAIN",
        "api_key": config.MASTER_API_KEY,
        "api_secret": config.MASTER_API_SECRET,
        "tab_name": "Master"
    }
]

# ================= GLOBAL HELPERS =================

# 1. Load Local Logs (Done once for all accounts)
trade_sources = []
if os.path.exists("trades_log.csv"):
    print("📂 Loading local trade logs...")
    try:
        with open("trades_log.csv", "r") as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    trade_sources.append({
                        'ts': float(parts[0]),
                        'sym': parts[1],
                        'bot': parts[2]
                    })
    except: pass

def find_source(symbol, close_ts_ms):
    close_ts_sec = close_ts_ms / 1000
    # Look for logs within reasonable timeframe before close
    relevant_logs = [x for x in trade_sources if x['sym'] == symbol and x['ts'] < close_ts_sec]
    if not relevant_logs: return "-"
    relevant_logs.sort(key=lambda x: x['ts'], reverse=True)
    return relevant_logs[0]['bot']

def consolidate_rows(rows):
    """
    STRICT CONSOLIDATION:
    Only merge if fills happen within 60 seconds (System Split Fills).
    Everything else is treated as a separate position.
    """
    if not rows: return []
    # Sort by Ticker -> Date
    rows.sort(key=lambda x: (x[0], x[1])) 
    
    merged = []
    curr = rows[0]
    curr_exit_val = float(curr[7]) * float(curr[4]) 
    
    for i in range(1, len(rows)):
        next_row = rows[i]
        
        t1 = datetime.strptime(curr[1], '%Y-%m-%d %H:%M:%S')
        t2 = datetime.strptime(next_row[1], '%Y-%m-%d %H:%M:%S')
        time_diff = abs((t2 - t1).total_seconds())

        is_split_fill = False
        
        # Check Ticker and Direction match
        if curr[0] == next_row[0] and curr[3] == next_row[3]:
            # ONLY merge if it happened within 60 seconds (Split Fill)
            if time_diff < 60:
                is_split_fill = True

        if is_split_fill:
            # Merge Logic
            new_qty = float(curr[4]) + float(next_row[4])
            new_entry_val = float(curr[5]) + float(next_row[5])
            new_pnl = float(curr[8]) + float(next_row[8])
            
            next_exit_val = float(next_row[7]) * float(next_row[4])
            total_exit_val = curr_exit_val + next_exit_val
            
            curr[4] = new_qty
            curr[5] = new_entry_val
            curr[8] = new_pnl
            curr_exit_val = total_exit_val
            
            if new_qty > 0:
                curr[6] = new_entry_val / new_qty
                curr[7] = total_exit_val / new_qty
                
            if t2 > t1: curr[1] = next_row[1]
        else:
            merged.append(curr)
            curr = next_row
            curr_exit_val = float(curr[7]) * float(curr[4])
            
    merged.append(curr)
    return merged

# ================= WORKER FUNCTION =================
def run_export_task(account_name, api_key, api_secret, tab_name):
    print(f"\n🔵 STARTING EXPORT: {account_name} -> Tab: '{tab_name}'")
    
    # 1. Connect Google Sheets
    try:
        client = gspread.service_account(filename='service_account.json')
        spreadsheet = client.open(SHEET_NAME)
        try:
            sheet = spreadsheet.worksheet(tab_name)
        except:
            print(f"   📄 Tab not found, creating '{tab_name}'...")
            sheet = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=10)
    except Exception as e:
        print(f"   ❌ GSheet Error: {e}")
        return

    # 2. Backup Notes (Tab-Specific)
    print("   💾 Backing up notes...")
    existing_notes = {}
    try:
        raw_data = sheet.get_all_values()
        if raw_data:
            headers = raw_data[0]
            if "Notes" in headers:
                note_idx = headers.index("Notes")
                tick_idx = headers.index("Ticker")
                date_idx = headers.index("Closed Date")
                for row in raw_data[1:]:
                    if len(row) > note_idx:
                        # Backup Key: Ticker_Date
                        key = f"{row[tick_idx]}_{row[date_idx]}"
                        if row[note_idx].strip(): existing_notes[key] = row[note_idx]
        print(f"   ✅ Preserved {len(existing_notes)} notes.")
    except Exception as e:
        print(f"   ⚠️ Backup skipped: {e}")

    # 3. Connect Bybit
    print(f"   🔑 Connecting to Bybit...")
    session = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)

    # 4. Fetch History
    print(f"   ⬇️ Fetching trades since July 1st, 2025...")
    final_end_time = int(time.time() * 1000)
    start_dt = datetime(2025, 7, 1)
    current_start = int(start_dt.timestamp() * 1000)
    all_rows = []
    
    while current_start < final_end_time:
        current_end = current_start + (7 * 24 * 60 * 60 * 1000) - 1000
        if current_end > final_end_time: current_end = final_end_time
        
        cursor = None
        while True:
            try:
                params = {"category": "linear", "limit": 100, "startTime": current_start, "endTime": current_end}
                if cursor: params["cursor"] = cursor
                
                resp = session.get_closed_pnl(**params)
                if 'result' not in resp or 'list' not in resp['result']: break
                new_items = resp['result']['list']
                if not new_items: break
                
                for item in new_items:
                    sym = item['symbol']
                    ts = int(item['createdTime'])
                    date_str = datetime.fromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M:%S')
                    
                    row = [
                        sym, date_str, find_source(sym, ts),
                        "Short" if item['side'] == "Buy" else "Long",
                        float(item['closedSize']), float(item['cumEntryValue']),
                        float(item['avgEntryPrice']), float(item['avgExitPrice']),
                        float(item['closedPnl'])
                    ]
                    all_rows.append(row)
                
                cursor = resp['result'].get('nextPageCursor')
                if not cursor: break
                time.sleep(0.1)
            except Exception as e:
                print(f"   ⚠️ API Warning: {e}"); break
        
        current_start = current_end + 1000
        time.sleep(0.1)

    # 5. Consolidate & Restore Notes
    print(f"   ✅ Fetched {len(all_rows)} raw rows. Consolidating (Strict)...")
    final_rows = consolidate_rows(all_rows)
    print(f"   ✅ Consolidated to {len(final_rows)} positions.")
    
    for row in final_rows:
        key = f"{row[0]}_{row[1]}"
        row.append(existing_notes.get(key, ""))

    # 6. Upload
    if final_rows:
        print("   🚀 Uploading...")
        headers = ["Ticker", "Closed Date", "Source Bot", "Direction", "Qty (Size)", "Entry Value ($)", "Open Price", "Close Price", "PNL", "Notes"]
        sheet.clear()
        sheet.append_row(headers)
        final_rows.sort(key=lambda x: x[1], reverse=True)
        
        chunk_size = 500
        for i in range(0, len(final_rows), chunk_size):
            sheet.append_rows(final_rows[i:i + chunk_size])
        print("   ✅ Tab Updated.")
    else:
        print("   ⚠️ No history found.")

# ================= MAIN EXECUTION =================
if __name__ == "__main__":
    for acc in ACCOUNTS:
        run_export_task(acc['name'], acc['api_key'], acc['api_secret'], acc['tab_name'])
    print("\n✨ ALL EXPORTS COMPLETED.")
