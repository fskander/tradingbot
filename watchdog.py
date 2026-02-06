import time
import os
import subprocess
import datetime

# CONFIG
BOTS = {
    "bot.py": "output.log",
    "bot_cash.py": "output_cash.log",
    "bot_kelvin.py": "output_kelvin.log"
}

def log(msg):
    # Standardize format so it matches your other logs
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}", flush=True)

def is_running(script_name):
    try:
        # Check for the specific python process
        output = subprocess.check_output("ps aux", shell=True).decode()
        for line in output.split('\n'):
            if f"python3 -u {script_name}" in line and "grep" not in line and "nohup" not in line:
                parts = line.split()
                return parts[1] # Returns PID
    except: return None
    return None

def start_bot(script_name, log_file):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log(f"⚠️  RESTARTING {script_name}...")
    
    # 1. Inject visual separator into the log file so you see when it crashed
    os.system(f"echo '\n----- RESTARTED BY WATCHDOG AT {now} -----\n' >> {log_file}")
    
    # 2. Launch in background
    # We use nohup so it stays alive, but Systemd will own the process tree
    os.system(f"nohup python3 -u {script_name} >> {log_file} 2>&1 < /dev/null &")
    time.sleep(2)
    
    pid = is_running(script_name)
    if pid:
        log(f"✅ SUCCESS: {script_name} started with PID {pid}")
    else:
        log(f"❌ ERROR: {script_name} failed to start!")

def main():
    log("🛡️  UNIVERSAL WATCHDOG v4.0 ACTIVE (Systemd Optimized)")
    
    while True:
        for script, log_file in BOTS.items():
            pid = is_running(script)
            if pid:
                # Bot is alive, do nothing.
                # REMOVED: set_god_mode(pid) -> This stops the log spam.
                pass 
            else:
                log(f"💀 {script} is DEAD. Reviving...")
                start_bot(script, log_file)
        
        # Check every 10 seconds
        time.sleep(10)

if __name__ == "__main__":
    main()
