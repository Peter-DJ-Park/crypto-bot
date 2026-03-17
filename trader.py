"""
[Step 8] 무한매수법 자동거래 실행 (빗썸 API 1.0)
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

# 코인별 소수점 자리수 (빗썸 규정)
COIN_DECIMAL = {
    "BTC" : 8,
    "ETH" : 8,
    "XRP" : 4,
    "SOL" : 4,
    "DOGE": 4,
}

def load_state() -> dict:
    default = {
        "ticker"    : "",
        "cycle"     : 1,
        "slot"      : 0,
        "avg_price" : 0.0,
        "total_qty" : 0.0,
        "total_cost": 0.0,
    }
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            saved = json.load(f)
            default.update(saved)
    return default


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def get_buy_ratio(current_price: float, avg_price: float) -> float:
    if avg_price == 0:
        return 1.0
    drop_rate = (current_price - avg_price) / avg_price
    for threshold, ratio in BUY_RATIO_TABLE:
        if drop_rate >= threshold:
            return ratio
    return 2.5


def update_avg(state: dict, buy_amount: float, price: float) -> dict:
    qty = buy_amount / price
    state["total_cost"] += buy_amount
    state["total_qty"]  += qty
    state["avg_price"]   = state["total_cost"] / state["total_qty"]
    state["slot"]       += 1
    return state


def reset_state(state: dict, ticker: str) -> dict:
    return {
        "ticker"    : ticker,
        "cycle"     : state.get("cycle", 0) + 1,
        "slot"      : 0,
        "avg_price" : 0.0,
        "total_qty" : 0.0,
        "total_cost": 0.0,
    }


class BithumbV1Client:
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url   = "https://api.bithumb.com"

    def _signature(self, endpoint, params):
        nonce     = str(int(time.time() * 1000))
        query_str = urlencode(params)
        data      = endpoint + chr(0) + query_str + chr(0) + nonce
        h = hmac.new(
            self.secret_key.encode("utf-8"),
            data.encode("utf-8"),
            hashlib.sha512
        )
        return {
            "Api-Key"     : self.access_key,
            "Api-Sign"    : base64.b64encode(
                                h.hexdigest().encode("utf-8")
                            ).decode("utf-8"),
            "Api-Nonce"   : nonce,
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def post_request(self, endpoint, params):
        headers = self._signature(endpoint, params)
        res = requests.post(
            self.base_url + endpoint,
            data=urlencode(params),
            headers=headers,
            timeout=10,
        )
        return res.json()


class BithumbAPI:
    def __init__(self):
        if TRADE_MODE:
            self.client = BithumbV1Client(BITHUMB_ACCESS, BITHUMB_SECRET)
            print("  ✅ 빗썸 실거래 연결 성공")
        else:
            self.client = None
            print("  🧪 시뮬레이션 모드")

    def get_price(self, ticker: str) -> float:
        try:
            res = requests.get(
                f"https://api.bithumb.com/public/ticker/{ticker}_KRW",
                timeout=5
            ).json()
            return float(res["data"]["closing_price"])
        except Exception as e:
            print(f"  ❌ 가격 조회 실패: {e}")
            return 0.0

    def get_balances(self, ticker: str):
        if not TRADE_MODE:
            return 100_000.0, 0.0
        try:
            params = {"endpoint": "/info/balance",
                      "currency": ticker.upper()}
            res = self.client.post_request("/info/balance", params)
            if res.get("status") == "0000":
                krw  = float(res["data"]["available_krw"])
                coin = float(res["data"].get(
                    f"available_{ticker.lower()}", 0))
                print(f"  💰 KRW 잔고: {krw:,.0f}원")
                return krw, coin
            else:
                print(f"  ⚠️ 잔고 조회 실패: {res}")
        except Exception as e:
            print(f"  ⚠️ 잔고 조회 예외: {e}")
        return 0.0, 0.0

    def buy(self, ticker: str, amount_krw: float):
        if not TRADE_MODE:
            print(f"  [시뮬레이션] {ticker} {amount_krw:,.0f}원 매수")
            return {"status": "0000"}

        price = self.get_price(ticker)
        if price <= 0:
            print("  ❌ 가격 조회 실패로 매수 중단")
            return None

        decimal = COIN_DECIMAL.get(ticker.upper(), 4)
        units   = round(amount_krw / price, decimal)

        if units <= 0:
            print(f"  ❌ 수량 계산 오류: {units}")
            return None

        print(f"  🔍 매수 시도: {ticker} {amount_krw:,.0f}원 / "
              f"{price:,.0f}원 = {units}개")

        # 방법 1: market_buy (order_currency 키 사용)
        params = {
            "endpoint"      : "/trade/market_buy",
            "units"         : str(units),
            "order_currency": ticker.upper(),
            "payment_currency": "KRW",
        }
        res = self.client.post_request("/trade/market_buy", params)
        print(f"  market_buy 응답: {res.get('status')} "
              f"{res.get('message','')}")

        if res.get("status") == "0000":
            print(f"  🔴 실거래 매수 완료: {ticker} "
                  f"{amount_krw:,.0f}원 ({units}개)")
            return res

        # 방법 2: place 지정가 (order_currency 키 사용)
        print(f"  ⚠️ market_buy 실패, place 주문 시도...")
        params2 = {
            "endpoint"        : "/trade/place",
            "order_currency"  : ticker.upper(),
            "payment_currency": "KRW",
            "units"           : str(units),
            "price"           : str(int(price)),
            "type"            : "bid",
        }
        res2 = self.client.post_request("/trade/place", params2)
        print(f"  place 응답: {res2.get('status')} "
              f"{res2.get('message','')}")

        if res2.get("status") == "0000":
            print(f"  🔴 place 매수 완료: {ticker} {amount_krw:,.0f}원")
            return res2

        print(f"  ❌ 매수 최종 실패: {res2}")
        return None

    def sell(self, ticker: str, qty: float):
        if not TRADE_MODE:
            print(f"  [시뮬레이션] {ticker} {qty}개 매도")
            return {"status": "0000"}
        decimal = COIN_DECIMAL.get(ticker.upper(), 4)
        params = {
            "endpoint"        : "/trade/market_sell",
            "order_currency"  : ticker.upper(),
            "payment_currency": "KRW",
            "units"           : str(round(qty, decimal)),
        }
        res = self.client.post_request("/trade/market_sell", params)
        if res.get("status") == "0000":
            print(f"  🔴 실거래 매도 완료: {ticker} {qty}개")
        else:
            print(f"  ❌ 매도 실패: {res}")
        return res


def run_trade(ticker: str) -> dict:
    api   = BithumbAPI()
    state = load_state()

    if state["ticker"] and state["ticker"] != ticker:
        print(f"  ⚠️ 종목 변경: {state['ticker']} → {ticker}")
        state = reset_state(state, ticker)
    state["ticker"] = ticker

    current           = api.get_price(ticker)
    krw_bal, coin_bal = api.get_balances(ticker)
    avg               = state["avg_price"]
    mode              = "🔴 실거래" if TRADE_MODE else "🧪 시뮬레이션"

    print(f"  종목: {ticker}  |  현재가: {current:,.0f}원  |  "
          f"평단: {avg:,.0f}원  |  슬롯: {state['slot']}/{SPLIT}")
    print(f"  거래모드: {mode}")

    # 1. 익절 체크
    if avg > 0 and current >= avg * (1 + TARGET_PROFIT):
        if coin_bal > 0:
            api.sell(ticker, coin_bal)
        profit_pct = (current - avg) / avg * 100
        profit_krw = (current - avg) * state["total_qty"]
        result = {
            "action"    : "sell",
            "ticker"    : ticker,
            "cycle"     : state["cycle"],
            "profit_pct": round(profit_pct, 2),
            "profit_krw": round(profit_krw, 0),
        }
        save_state(reset_state(state, ticker))
        print(f"  🎉 익절! +{profit_pct:.1f}% / +{profit_krw:,.0f}원")
        return result

    # 2. 쿼터손절 체크
    if state["slot"] >= SPLIT:
        sell_qty = coin_bal * QUARTER_SELL
        if sell_qty > 0:
            api.sell(ticker, sell_qty)
        state["total_qty"]  *= (1 - QUARTER_SELL)
        state["total_cost"] *= (1 - QUARTER_SELL)
        state["slot"]        = int(SPLIT * (1 - QUARTER_SELL))
        save_state(state)
        return {"action": "quarter_sell", "ticker": ticker,
                "total_slots": SPLIT}

    # 3. 분할 매수
    ratio      = get_buy_ratio(current, avg)
    buy_amount = min(BASE_AMOUNT * ratio, krw_bal)
    buy_amount = max(buy_amount, 5000)

    order = api.buy(ticker, buy_amount)
    if order and order.get("status") == "0000":
        state = update_avg(state, buy_amount, current)
        save_state(state)
        print(f"  ✅ 매수완료: {buy_amount:,.0f}원 (x{ratio}배) → "
              f"새 평단: {state['avg_price']:,.0f}원")
        return {
            "action"     : "buy",
            "ticker"     : ticker,
            "amount"     : buy_amount,
            "current"    : current,
            "avg_price"  : state["avg_price"],
            "target"     : state["avg_price"] * (1 + TARGET_PROFIT),
            "slot"       : state["slot"],
            "total_slots": SPLIT,
            "ratio"      : ratio,
        }
    return {"action": "fail", "ticker": ticker}
