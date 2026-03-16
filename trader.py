"""
[Step 8] 무한매수법 자동거래 실행 (빗썸 API 1.0 - 규격 엄격 준수 버전)
"""
import json
import os
import time
import hmac
import hashlib
import base64
import requests
from urllib.parse import urlencode

from config import (BITHUMB_ACCESS, BITHUMB_SECRET, STATE_FILE,
                    SPLIT, BASE_AMOUNT, TARGET_PROFIT, QUARTER_SELL,
                    BUY_RATIO_TABLE, TEST_MODE, TRADE_MODE)

# --- 유틸리티 함수 (기존과 동일) ---
def load_state() -> dict:
    default = {"ticker": "", "cycle": 1, "slot": 0, "avg_price": 0.0, "total_qty": 0.0, "total_cost": 0.0}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            saved = json.load(f)
            default.update(saved)
    return default

def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def get_buy_ratio(current_price: float, avg_price: float) -> float:
    if avg_price == 0: return 1.0
    drop_rate = (current_price - avg_price) / avg_price
    for threshold, ratio in BUY_RATIO_TABLE:
        if drop_rate >= threshold: return ratio
    return 2.5

def update_avg(state: dict, buy_amount: float, price: float) -> dict:
    qty = buy_amount / price
    state["total_cost"] += buy_amount
    state["total_qty"]  += qty
    state["avg_price"]   = state["total_cost"] / state["total_qty"]
    state["slot"]       += 1
    return state

def reset_state(state: dict, ticker: str) -> dict:
    return {"ticker": ticker, "cycle": state.get("cycle", 0) + 1, "slot": 0, "avg_price": 0.0, "total_qty": 0.0, "total_cost": 0.0}

# --- 빗썸 API 1.0 클라이언트 ---
class BithumbV1Client:
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = "https://api.bithumb.com"

    def _signature(self, endpoint, params):
        nonce = str(int(time.time() * 1000))
        query_str = urlencode(params)
        data = endpoint + chr(0) + query_str + chr(0) + nonce
        h = hmac.new(self.secret_key.encode('utf-8'), data.encode('utf-8'), hashlib.sha512)
        return {
            "Api-Key": self.access_key,
            "Api-Sign": base64.b64encode(h.hexdigest().encode('utf-8')).decode('utf-8'),
            "Api-Nonce": nonce,
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def post_request(self, endpoint, params):
        headers = self._signature(endpoint, params)
        res = requests.post(self.base_url + endpoint, data=urlencode(params), headers=headers, timeout=10)
        return res.json()

class BithumbAPI:
    def __init__(self):
        self.api = BithumbV1Client(BITHUMB_ACCESS, BITHUMB_SECRET) if TRADE_MODE else None

    def get_price(self, ticker: str) -> float:
        try:
            res = requests.get(f"https://api.bithumb.com/public/ticker/{ticker}_KRW").json()
            return float(res['data']['closing_price'])
        except: return 0.0

    def get_balances(self, ticker: str):
        if not TRADE_MODE: return 100000.0, 0.0
        try:
            params = {"endpoint": "/info/balance", "currency": ticker.upper()}
            res = self.api.post_request("/info/balance", params)
            if res.get('status') == '0000':
                return float(res['data']['available_krw']), float(res['data'][f"available_{ticker.lower()}"])
        except: pass
        return 0.0, 0.0

    def buy(self, ticker, amount_krw):
        if not TRADE_MODE: return {"status": "0000"}
        price = self.get_price(ticker)
        if price == 0: return None
        
        # 💡 핵심 수정: DOGE 등은 소수점 자릿수에 매우 민감함. 안전하게 소수점 2자리로 제한.
        units = float(f"{amount_krw / price:.2f}")
        
        # 💡 빗썸 1.0 시장가 매수 표준 파라미터 구성
        params = {
            "endpoint": "/trade/market_buy",
            "units": units,
            "currency": ticker.upper()
        }
        
        res = self.api.post_request("/trade/market_buy", params)
        
        # 만약 여전히 실패하면, 수량을 더 단순화(정수형)해서 마지막으로 시도
        if res.get('status') == '5500':
            print("  ⚠️ 소수점 units 실패, 정수형 units로 최종 시도...")
            params["units"] = int(units)
            res = self.api.post_request("/trade/market_buy", params)
            
        if res.get('status') == '0000':
            print(f"  🔴 매수 성공: {params['units']} {ticker}")
            return res
        
        print(f"  ❌ 매수 실패: {res}")
        return None

    def sell(self, ticker, qty):
        if not TRADE_MODE: return {"status": "0000"}
        params = {
            "endpoint": "/trade/market_sell",
            "units": float(f"{qty:.2f}"),
            "currency": ticker.upper()
        }
        return self.api.post_request("/trade/market_sell", params)

def run_trade(ticker: str) -> dict:
    api = BithumbAPI()
    state = load_state()
    if state["ticker"] and state["ticker"] != ticker:
        state = reset_state(state, ticker)
    state["ticker"] = ticker

    current = api.get_price(ticker)
    krw_bal, coin_bal = api.get_balances(ticker)
    avg = state["avg_price"]
    
    result = {"action": "hold", "ticker": ticker, "amount": 0, "current": current, "avg_price": avg, "slot": state["slot"], "total_slots": SPLIT}

    if avg > 0 and current >= avg * (1 + TARGET_PROFIT):
        if coin_bal > 0: api.sell(ticker, coin_bal)
        save_state(reset_state(state, ticker))
        result.update({"action": "sell", "profit_pct": (current-avg)/avg*100})
        return result

    ratio = get_buy_ratio(current, avg)
    buy_amount = max(min(BASE_AMOUNT * ratio, krw_bal), 5000)
    
    order = api.buy(ticker, buy_amount)
    if order and order.get('status') == '0000':
        state = update_avg(state, buy_amount, current)
        save_state(state)
        result.update({"action": "buy", "amount": buy_amount, "avg_price": state["avg_price"], "slot": state["slot"]})
    else:
        result["action"] = "fail"
    
    return result
