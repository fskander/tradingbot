import re, asyncio, time, threading, hmac, hashlib, json, sys, random, gc
import uvloop, aiohttp
from datetime import datetime
from telethon import TelegramClient, events, functions
from pybit.unified_trading import HTTP

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

class AsyncBybit:
    def __init__(self, api_key, api_secret, testnet=False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api-testnet.bybit.com" if testnet else "https://api.bybit.com"
        self.session = None

    async def init_session(self):
        if not self.session:
            connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
            self.session = aiohttp.ClientSession(connector=connector)

    def _sign(self, params):
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        param_str = json.dumps(params)
        raw_str = timestamp + self.api_key + recv_window + param_str
        signature = hmac.new(self.api_secret.encode('utf-8'), raw_str.encode('utf-8'), hashlib.sha256).hexdigest()
        return {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
            "Content-Type": "application/json"
        }

    async def _post(self, endpoint, payload):
        if not self.session: await self.init_session()
        url = f"{self.base_url}{endpoint}"
        headers = self._sign(payload)
        try:
            t0 = time.time()
            async with self.session.post(url, headers=headers, json=payload, timeout=5) as resp:
                data = await resp.json()
                # print(f"      ⏱️ API Latency: {(time.time()-t0)*1000:.2f}ms") 
                return data
        except Exception as e: return {"retCode": -1, "retMsg": str(e)}

    async def place_order(self, **kwargs):
        return await self._post("/v5/order/create", kwargs)

    # --- RESTORED: Batch Order Support ---
    async def place_batch_order(self, category, requests):
        return await self._post("/v5/order/create-batch", {"category": category, "request": requests})

    async def set_trading_stop(self, **kwargs):
        return await self._post("/v5/position/trading-stop", kwargs)

    async def get_position_idx(self, symbol, side):
        if not self.session: await self.init_session()
        timestamp = str(int(time.time() * 1000))
        try:
            params = f"category=linear&symbol={symbol}"
            raw = timestamp + self.api_key + "5000" + params
            sig = hmac.new(self.api_secret.encode('utf-8'), raw.encode('utf-8'), hashlib.sha256).hexdigest()
            headers = {
                "X-BAPI-API-KEY": self.api_key, "X-BAPI-SIGN": sig,
                "X-BAPI-TIMESTAMP": timestamp, "X-BAPI-RECV-WINDOW": "5000"
            }
            async with self.session.get(f"{self.base_url}/v5/position/list?{params}", headers=headers) as resp:
                data = await resp.json()
                if data['retCode'] == 0:
                    for p in data['result']['list']:
                        if p['positionIdx'] == 1 and side == "Buy": return 1
                        if p['positionIdx'] == 2 and side == "Sell": return 2
        except: pass
        return 0

class TradingBot:
    def __init__(self, name, config_dict, custom_parser=None):
        self.name = name
        self.cfg = config_dict
        self.custom_parser = custom_parser
        
        self.api_id = self.cfg['TELEGRAM_API_ID']
        self.api_hash = self.cfg['TELEGRAM_API_HASH']
        self.channel_id = self.cfg['CHANNEL_ID']
        self.bybit_key = self.cfg['API_KEY']
        self.bybit_secret = self.cfg['API_SECRET']
        self.testnet = self.cfg['TESTNET']
        
        self.risk_mode = self.cfg['RISK_MODE']
        self.risk_factor = float(self.cfg['RISK_FACTOR'])
        self.risk_fixed = float(self.cfg['RISK_AMOUNT'])
        self.max_pos = float(self.cfg['MAX_POS'])
        self.ladder = self.cfg['LADDER']
        
        self.partial_tp = float(self.cfg.get('PARTIAL_TP', 0.0))
        self.tp_target = float(self.cfg.get('TP_TARGET', 0.8))
        self.use_trailing = self.cfg.get('USE_TRAILING', False)

        # Sync Session for pre-loading, Async for trading
        self.sess = HTTP(testnet=self.testnet, api_key=self.bybit_key, api_secret=self.bybit_secret)
        self.async_exec = AsyncBybit(self.bybit_key, self.bybit_secret, self.testnet)
        self.client = TelegramClient(f'session_{self.name.lower()}', self.api_id, self.api_hash)
        
        self.instrument_cache = {}
        self.price_cache = {}
        self.wallet_balance = 0.0
        self.data_lock = threading.Lock()
        self.last_trade_time = {}

    def log(self, msg):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{self.name}] {msg}")

    def decimals(self, n):
        s = "{:.10f}".format(n).rstrip('0')
        return len(s.split('.')[1]) if '.' in s else 0

    def update_instrument(self, d):
        s = d['symbol']
        self.instrument_cache[s] = {
            'q': float(d['lotSizeFilter']['qtyStep']),
            't': float(d['priceFilter']['tickSize']),
            'q_dec': self.decimals(float(d['lotSizeFilter']['qtyStep'])),
            't_dec': self.decimals(float(d['priceFilter']['tickSize']))
        }

    # --- RESTORED: Pre-load Logic ---
    def load_instruments(self):
        self.log("📦 Pre-loading Instruments...")
        try:
            # Fetch all linear USDT pairs at once
            r = self.sess.get_instruments_info(category="linear", limit=1000)
            if r['retCode'] == 0:
                count = 0
                for i in r['result']['list']:
                    if i['quoteCoin'] == 'USDT':
                        self.update_instrument(i)
                        count += 1
                self.log(f"✅ Cached {count} instruments.")
        except Exception as e:
            self.log(f"⚠️ Cache Init Failed: {e}")

    def get_instrument(self, sym):
        # Instant lookup, no API call
        return self.instrument_cache.get(sym)

    def rnd(self, p, d_obj): return "{:.{prec}f}".format(p, prec=d_obj['t_dec'])
    def qty_str(self, q, d_obj): return "{:.{prec}f}".format(q, prec=d_obj['q_dec'])

    def default_parser(self, text):
        return None 

    def normalize_price(self, price, market_price):
        if not price or price <= 0: return price
        if market_price == 0: return price
        while price > (market_price * 2): price /= 10.0
        while price < (market_price / 10): price *= 10.0
        return price

    async def execute_trade(self, sig):
        # --- RESTORED: GC Disable for critical path ---
        gc.disable()
        
        t_start = time.perf_counter()
        sym = sig['sym']
        now = time.time()
        
        if sym in self.last_trade_time and (now - self.last_trade_time[sym] < 10): 
            gc.enable(); self.log(f"⏳ Skipped Duplicate: {sym}"); return
        self.last_trade_time[sym] = now

        d = self.get_instrument(sym)
        if not d: 
            # Fallback fetch if missing
            try:
                r = await self.async_exec._post("/v5/market/instruments-info", {"category":"linear","symbol":sym})
                if r['retCode']==0: 
                    self.update_instrument(r['result']['list'][0])
                    d = self.instrument_cache[sym]
            except: pass
        if not d: gc.enable(); self.log(f"❌ Instrument {sym} not found."); return

        # --- RESTORED: Better Price Proxy (Ask/Bid) ---
        market_price = 0
        with self.data_lock: 
            # If we have streamer data, use specific side if available
            ticker = self.price_cache.get(sym)
            if isinstance(ticker, dict):
                 market_price = ticker['ask1Price'] if sig['side'] == "Buy" else ticker['bid1Price']
            elif isinstance(ticker, float):
                 market_price = ticker

        if market_price == 0:
            # Fallback API
            try:
                r = await self.async_exec.session.get(f"{self.async_exec.base_url}/v5/market/tickers?category=linear&symbol={sym}")
                data = await r.json()
                item = data['result']['list'][0]
                market_price = float(item['ask1Price']) if sig['side'] == "Buy" else float(item['bid1Price'])
            except: pass
        
        if market_price == 0: gc.enable(); self.log(f"❌ No price for {sym}"); return

        # Normalize
        if sig['sl']: sig['sl'] = self.normalize_price(sig['sl'], market_price)
        if sig['tp']: sig['tp'] = self.normalize_price(sig['tp'], market_price)
        
        if sig['entry'] != -1:
            sig['entry'] = self.normalize_price(sig['entry'], market_price)
        else:
            sig['entry'] = market_price

        if 'entries' in sig and sig['entries']:
            sig['entries'] = [self.normalize_price(p, market_price) for p in sig['entries'] if p != -1]
        if 'tps' in sig and sig['tps']:
            sig['tps'] = [self.normalize_price(p, market_price) for p in sig['tps']]

        # Risk
        risk_dollars = self.risk_fixed
        if self.risk_mode == "PERCENTAGE":
            with self.data_lock:
                if self.wallet_balance > 0: risk_dollars = self.wallet_balance * self.risk_factor

        signal_entry = sig['entry']
        sl_price = sig['sl']
        
        total_risk_factor = 0.0
        steps_to_execute = []
        
        # Calculate Steps
        if 'entries' in sig and len(sig['entries']) > 0:
            for i, price in enumerate(sig['entries']):
                 dist = abs(price - sl_price)
                 total_risk_factor += (dist * 1.0)
                 steps_to_execute.append({'price': price, 'weight': 1.0, 'pos': 0})
        else:
            for step in self.ladder:
                step_price = market_price + (signal_entry - market_price) * step['pos']
                dist = abs(step_price - sl_price)
                total_risk_factor += (dist * step['weight'])
                steps_to_execute.append({'price': step_price, 'weight': step['weight'], 'pos': step['pos']})

        if total_risk_factor == 0: gc.enable(); return

        base_unit_qty = risk_dollars / total_risk_factor
        self.log(f"🚀 {sig['side']} {sym} | Risk: ${risk_dollars:.2f} | Entry: {signal_entry}")

        # --- RESTORED: BATCH ORDER EXECUTION ---
        batch_payload = []
        market_payload = None
        final_filled_qty = 0
        
        for i, step in enumerate(steps_to_execute):
            step_qty_val = base_unit_qty * step['weight']
            step_qty_final = (step_qty_val // d['q']) * d['q']
            if step_qty_final <= 0: continue
            final_filled_qty += step_qty_final

            order_args = {
                "symbol": sym, "side": sig['side'], 
                "orderType": "Limit", "qty": self.qty_str(step_qty_final, d), 
                "price": self.rnd(step['price'], d), "timeInForce": "GTC",
                "stopLoss": self.rnd(sl_price, d)
            }

            # Check for Market Execution
            pct_diff = abs(market_price - step['price']) / market_price
            if step.get('pos') == 0.0 or pct_diff < 0.002:
                order_args["orderType"] = "Market"
                del order_args["price"]
                market_payload = order_args # Market must be sent individually usually or first
            else:
                batch_payload.append(order_args)

        # 1. Fire Market Order (Immediate)
        if market_payload:
             resp = await self.async_exec.place_order(category="linear", **market_payload)
             if resp.get('retCode') == 0: self.log(f"   ⚡ MARKET FILLED: {market_payload['qty']}")
             else: self.log(f"   ❌ Market Fail: {resp.get('retMsg')}")

        # 2. Fire Batch Limits (Immediate)
        if batch_payload:
             # Split into chunks of 10 if necessary (Bybit limit)
             resp = await self.async_exec.place_batch_order("linear", batch_payload)
             if resp.get('retCode') == 0:
                 self.log(f"   🪜 BATCH PLACED: {len(batch_payload)} Limit Orders")
             else:
                 self.log(f"   ❌ Batch Fail: {resp.get('retMsg')}")

        t_end = time.perf_counter()
        # self.log(f"   ⏱️ Exec Time: {(t_end - t_start)*1000:.2f}ms")
        
        # --- Critical Section End ---
        gc.enable()

        # 5. EXITS (Separated from critical path)
        tp_side = "Sell" if sig['side'] == "Buy" else "Buy"

        if 'tps' in sig and len(sig['tps']) > 0:
            tps = sorted(sig['tps'], reverse=(sig['side']=="Sell"))
            qty_per_step = (final_filled_qty * self.partial_tp // d['q']) * d['q']
            qty_placed = 0
            tp_batch = []
            
            for i, price in enumerate(tps):
                is_last = (i == len(tps) - 1)
                q = final_filled_qty - qty_placed if is_last else qty_per_step
                if q > 0:
                    tp_batch.append({
                        "symbol": sym, "side": tp_side, "orderType": "Limit",
                        "qty": self.qty_str(q, d), "price": self.rnd(price, d),
                        "reduceOnly": True, "timeInForce": "GTC"
                    })
                    qty_placed += q
            
            if tp_batch:
                await self.async_exec.place_batch_order("linear", tp_batch)
                self.log(f"   🎯 Batch TPs Set ({len(tp_batch)})")

        elif self.partial_tp > 0 and self.tp_target > 0:
            avg_entry = market_price
            risk_dist = abs(avg_entry - sl_price)
            tp1_price = avg_entry + (risk_dist * self.tp_target) if sig['side'] == "Buy" else avg_entry - (risk_dist * self.tp_target)
            
            tp1_qty = (final_filled_qty * self.partial_tp // d['q']) * d['q']
            tp2_qty = final_filled_qty - tp1_qty
            
            tp_batch = []
            if tp1_qty > 0:
                 tp_batch.append({"symbol": sym, "side": tp_side, "orderType": "Limit", "qty": self.qty_str(tp1_qty, d), "price": self.rnd(tp1_price, d), "reduceOnly": True})
            if tp2_qty > 0:
                 tp_batch.append({"symbol": sym, "side": tp_side, "orderType": "Limit", "qty": self.qty_str(tp2_qty, d), "price": self.rnd(sig['tp'], d), "reduceOnly": True})
            
            if tp_batch:
                await self.async_exec.place_batch_order("linear", tp_batch)
                self.log("   🎯 Pro Split TPs Placed (Batch)")
        else:
            await self.async_exec.place_order(category="linear", symbol=sym, side=tp_side, orderType="Limit", qty=self.qty_str(final_filled_qty, d), price=self.rnd(sig['tp'], d), reduceOnly=True)

        if self.use_trailing:
             r_dist = abs(market_price - sl_price)
             tick_size = d['t']
             if r_dist > (tick_size * 2):
                 activation_dist = r_dist * 0.8
                 activate_p = market_price + activation_dist if sig['side'] == "Buy" else market_price - activation_dist
                 pidx = await self.async_exec.get_position_idx(sym, sig['side'])
                 await self.async_exec.set_trading_stop(
                     category="linear", symbol=sym, 
                     trailingStop=self.rnd(r_dist, d), 
                     activePrice=self.rnd(activate_p, d),
                     positionIdx=pidx
                 )
                 self.log(f"   🛡️ Trailing Stop Armed (Idx {pidx})")

        try:
            with open("trades_log.csv", "a") as f: f.write(f"{time.time()},{sym},{self.name}\n")
        except: pass

    def background_streamer(self):
        self.log("🚀 Streamer Started...")
        last_balance = 0
        while True:
            try:
                r = self.sess.get_tickers(category="linear")
                if 'result' in r:
                    with self.data_lock:
                        for i in r['result']['list']: 
                            # Cache full dict for Ask/Bid access
                            self.price_cache[i['symbol']] = {
                                'lastPrice': float(i['lastPrice']),
                                'ask1Price': float(i['ask1Price']),
                                'bid1Price': float(i['bid1Price'])
                            }
                if time.time() - last_balance > 10:
                    try:
                        b = self.sess.get_wallet_balance(accountType="UNIFIED", coin="USDT")
                        if b['retCode'] == 0:
                            equity = float(b['result']['list'][0]['totalEquity'])
                            with self.data_lock: self.wallet_balance = equity
                            last_balance = time.time()
                    except: pass
                time.sleep(1) # Fast ticker update
            except: time.sleep(5)

    async def heartbeat_loop(self):
        self.log("💓 HEARTBEAT Monitor Started (4h)")
        while True:
            try:
                await asyncio.sleep(14400) 
                try: await self.client(functions.PingRequest(ping_id=random.randint(0, 10000)))
                except: pass
                self.log(f"💓 HEARTBEAT: Bot is still listening...")
            except asyncio.CancelledError: break
            except: await asyncio.sleep(60)

    async def run(self):
        self.log(f"🚀 ACTIVE (v9.0 Platinum - Batch/GC/Preload)")
        # --- Pre-load Instruments ---
        self.load_instruments()
        
        await self.async_exec.init_session()
        threading.Thread(target=self.background_streamer, daemon=True).start()
        
        asyncio.create_task(self.heartbeat_loop())
        
        @self.client.on(events.NewMessage(chats=self.channel_id))
        async def handler(event):
            if not event.text: return
            text = event.raw_text.replace('**', '').replace('__', '')
            
            preview = text.replace('\n', ' ')[:50]
            self.log(f"📩 HEARD: {preview}...")

            if self.custom_parser: sig = self.custom_parser(text)
            else: sig = self.default_parser(text)
            
            if sig:
                self.log(f"✅ PARSED: {sig['sym']} {sig['side']}")
                await self.execute_trade(sig)
            else:
                self.log("⚠️ IGNORED: No signal found")

        await self.client.start()
        self.log(f"🌍 Listening to Channel {self.channel_id}...")
        await self.client.run_until_disconnected()

def start_bot(name, config_dict, parser=None):
    bot = TradingBot(name, config_dict, custom_parser=parser)
    asyncio.run(bot.run())
