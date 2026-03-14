"""
[Step 8] 무한매수법 자동거래 실행
"""
import json
import os
from config import (BITHUMB_ACCESS, BITHUMB_SECRET, STATE_FILE,
                    SPLIT, BASE_AMOUNT, TARGET_PROFIT, QUARTER_SELL,
                    BUY_RATIO_TABLE, TEST_MODE, TRADE_MODE)

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
    qty              = buy_amount / price
    state["total_cost"] += buy_amount
    state["total_qty"]  += qty
    state["avg_price"]   = state["total_cost"] / state["total_qty"]
    state["slot"]       += 1
    return state


def reset_state(state: dict, ticker: str) -> dict:
    return {
        "ticker"    : ticker,
        "cycle"     : state["cycle"] + 1,
        "slot"      : 0,
        "avg_price" : 0.0,
        "total_qty" : 0.0,
        "total_cost": 0.0,
    }


class BithumbAPI:
    def __init__(self):
        if not TEST_MODE:
            import pybithumb
            self.api = pybithumb.Bithumb(BITHUMB_ACCESS, BITHUMB_SECRET)
        else:
            self.api = None

    def get_price(self, ticker: str) -> float:
        if TEST_MODE:
            from mock_data import MOCK_PRICES
            import random
            base = MOCK_PRICES.get(ticker, 1000)
            return base * (1 + random.uniform(-0.02, 0.02))
        import pybithumb
        return float(pybithumb.get_current_price(ticker))

    def get_krw_balance(self, ticker: str) -> float:
        if TEST_MODE:
            return 100_000.0
        return float(self.api.get_balance(ticker)[2])

    def get_coin_balance(self, ticker: str) -> float:
        if TEST_MODE:
            return 0.0
        return float(self.api.get_balance(ticker)[0])

    def buy(self, ticker: str, amount_krw: float):
        if TEST_MODE:
            print(f"  [시뮬레이션] {ticker} {amount_krw:,.0f}원 매수")
            return True
        return self.api.buy_market_order(ticker, amount_krw)

    def sell(self, ticker: str, qty: float):
        if TEST_MODE:
            print(f"  [시뮬레이션] {ticker} {qty:.6f} 매도")
            return True
        return self.api.sell_market_order(ticker, qty)


def run_trade(ticker: str) -> dict:
    api   = BithumbAPI()
    state = load_state()

    if state["ticker"] and state["ticker"] != ticker:
        print(f"  ⚠️ 종목 변경: {state['ticker']} → {ticker}")
        state = reset_state(state, ticker)
    state["ticker"] = ticker

    current = api.get_price(ticker)
    avg     = state["avg_price"]

    print(f"  종목: {ticker}  |  현재가: {current:,.0f}원  |  "
          f"평단: {avg:,.0f}원  |  슬롯: {state['slot']}/{SPLIT}")

    if avg > 0 and current >= avg * (1 + TARGET_PROFIT):
        qty        = api.get_coin_balance(ticker)
        api.sell(ticker, qty)
        profit_pct = (current - avg) / avg * 100
        profit_krw = (current - avg) * state["total_qty"]
        result     = {
            "action"    : "sell",
            "ticker"    : ticker,
            "cycle"     : state["cycle"],
            "profit_pct": round(profit_pct, 2),
            "profit_krw": round(profit_krw, 0),
        }
        save_state(reset_state(state, ticker))
        print(f"  🎉 익절! +{profit_pct:.1f}% / +{profit_krw:,.0f}원")
        return result

    if state["slot"] >= SPLIT:
        qty      = api.get_coin_balance(ticker)
        sell_qty = qty * QUARTER_SELL
        api.sell(ticker, sell_qty)
        state["total_qty"]  *= (1 - QUARTER_SELL)
        state["total_cost"] *= (1 - QUARTER_SELL)
        state["slot"]        = int(SPLIT * (1 - QUARTER_SELL))
        save_state(state)
        return {"action": "quarter_sell", "ticker": ticker, "total_slots": SPLIT}

    ratio      = get_buy_ratio(current, avg)
    krw_bal    = api.get_krw_balance(ticker)
    buy_amount = min(BASE_AMOUNT * ratio, krw_bal)
    buy_amount = max(buy_amount, 1000)

    api.buy(ticker, buy_amount)
    state = update_avg(state, buy_amount, current)
    save_state(state)

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
