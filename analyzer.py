"""
[Step 3] 기술적 지표 분석
- RSI(14), MACD(12,26,9), 볼린저밴드(20,2)
- 캔들 패턴 감지
- 뉴스 감성 점수 산출
- 종합 매매 신호 생성
"""
import numpy as np
import pandas as pd


# ── 기술적 지표 계산 ────────────────────────────────────────
def calc_indicators(df: pd.DataFrame) -> dict:
    close = df["close"]

    # RSI(14)
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rsi   = 100 - (100 / (1 + gain / loss.replace(0, 1e-9)))

    # 이동평균
    ma5  = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()

    # 볼린저밴드(20, ±2σ)
    bb_mid   = close.rolling(20).mean()
    bb_std   = close.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    # 현재가의 밴드 내 위치 (0~100%)
    bb_pct = (close - bb_lower) / (bb_upper - bb_lower + 1e-9)

    # MACD(12, 26, 9)
    ema12       = close.ewm(span=12, adjust=False).mean()
    ema26       = close.ewm(span=26, adjust=False).mean()
    macd        = ema12 - ema26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    macd_hist   = macd - macd_signal

    # 거래량 비율 (당일 vs 5일 평균)
    vol_avg   = df["volume"].rolling(5).mean().iloc[-1]
    vol_ratio = df["volume"].iloc[-1] / (vol_avg + 1e-9)

    return {
        "current_price": round(float(close.iloc[-1]), 2),
        "change_pct"   : round((float(close.iloc[-1]) / float(close.iloc[-2]) - 1) * 100, 2),
        "rsi"          : round(float(rsi.iloc[-1]), 2),
        "ma5"          : round(float(ma5.iloc[-1]), 2),
        "ma20"         : round(float(ma20.iloc[-1]), 2),
        "bb_upper"     : round(float(bb_upper.iloc[-1]), 2),
        "bb_lower"     : round(float(bb_lower.iloc[-1]), 2),
        "bb_pct"       : round(float(bb_pct.iloc[-1]) * 100, 1),
        "macd"         : round(float(macd.iloc[-1]), 4),
        "macd_signal"  : round(float(macd_signal.iloc[-1]), 4),
        "macd_hist"    : round(float(macd_hist.iloc[-1]), 4),
        "vol_ratio"    : round(float(vol_ratio), 2),
    }


# ── 캔들 패턴 감지 ──────────────────────────────────────────
def detect_pattern(df: pd.DataFrame) -> str:
    o = float(df["open"].iloc[-1])
    c = float(df["close"].iloc[-1])
    h = float(df["high"].iloc[-1])
    l = float(df["low"].iloc[-1])

    body       = abs(c - o)
    upper_tail = h - max(o, c)
    lower_tail = min(o, c) - l
    total      = h - l + 1e-9

    if body < total * 0.1:
        return "도지 (방향 불명) ↔️"
    if c > o:
        if body > total * 0.7:       return "강한 양봉 🟢"
        if lower_tail > body * 2:    return "망치형 (반등신호) 🔨"
        return "양봉 🟢"
    else:
        if body > total * 0.7:       return "강한 음봉 🔴"
        if upper_tail > body * 2:    return "역망치형 (하락신호) 🔻"
        return "음봉 🔴"


# ── 종합 매매 신호 ──────────────────────────────────────────
def trade_signal(ind: dict) -> str:
    """RSI, MACD, BB, 거래량, MA 를 종합해 매매 신호 산출"""
    score = 0

    # RSI 기준
    if   ind["rsi"] < 30:  score += 3
    elif ind["rsi"] < 45:  score += 1
    elif ind["rsi"] > 70:  score -= 2

    # MACD 기준
    if ind["macd_hist"] > 0:                              score += 1
    if ind["macd"] > ind["macd_signal"]:                  score += 1

    # 볼린저밴드 위치
    if   ind["bb_pct"] < 20:  score += 2
    elif ind["bb_pct"] < 40:  score += 1
    elif ind["bb_pct"] > 80:  score -= 1

    # 거래량
    if ind["vol_ratio"] > 1.5:  score += 1

    # 이동평균 정배열
    if ind["current_price"] > ind["ma5"] > ind["ma20"]:  score += 1

    if score >= 5:   return "강력 매수 ⚡"
    if score >= 3:   return "매수 🟢"
    if score >= 1:   return "중립 ➡️"
    if score >= -1:  return "관망 🟡"
    return "매도/회피 🔴"


# ── 뉴스 감성 분석 ──────────────────────────────────────────
def sentiment_score(keywords: list) -> dict:
    POSITIVE = {"상승","급등","돌파","신고가","매수","호재","강세","회복",
                "기대","합의","승인","성장","반등","최고","강화","긍정"}
    NEGATIVE = {"하락","급락","붕괴","매도","악재","약세","공포","규제",
                "위기","소송","제재","경고","손실","부정","폭락"}

    pos, neg = 0, 0
    pos_words, neg_words = [], []
    for word, cnt in keywords:
        if word in POSITIVE:   pos += cnt; pos_words.append(word)
        elif word in NEGATIVE: neg += cnt; neg_words.append(word)

    total = pos + neg + 1
    score = round((pos - neg) / total * 100, 1)
    return {
        "score"   : score,
        "positive": pos_words,
        "negative": neg_words,
        "verdict" : "긍정적 📈" if score > 10 else "부정적 📉" if score < -10 else "중립 ➡️",
    }


# ── 통합 분석 ───────────────────────────────────────────────
def analyze_all(ohlcv_data: dict, keywords: list) -> dict:
    """전체 코인 분석 통합 실행"""
    sentiment = sentiment_score(keywords)
    result    = {}
    for ticker, df in ohlcv_data.items():
        ind     = calc_indicators(df)
        pattern = detect_pattern(df)
        signal  = trade_signal(ind)
        result[ticker] = {
            "indicators": ind,
            "pattern"   : pattern,
            "signal"    : signal,
            "sentiment" : sentiment,
        }
    return result


if __name__ == "__main__":
    print("=" * 50)
    print("Step 3: 기술적 분석")
    print("=" * 50)
    from mock_data import MOCK_OHLCV, MOCK_NEWS
    from news_collector import extract_keywords

    kw       = extract_keywords(MOCK_NEWS)
    analysis = analyze_all(MOCK_OHLCV, kw)

    for ticker, data in analysis.items():
        ind = data["indicators"]
        print(f"\n{'─'*40}")
        print(f"  [{ticker}]  {ind['change_pct']:+.2f}%")
        print(f"  현재가  : {ind['current_price']:>15,.0f}원")
        print(f"  RSI     : {ind['rsi']}  |  BB위치: {ind['bb_pct']}%")
        print(f"  MACD    : {ind['macd']:.4f}  |  거래량비: {ind['vol_ratio']}x")
        print(f"  캔들    : {data['pattern']}")
        print(f"  신호    : {data['signal']}")

    s = list(analysis.values())[0]["sentiment"]
    print(f"\n{'─'*40}")
    print(f"  뉴스감성: {s['verdict']} ({s['score']}점)")
    print(f"  긍정: {s['positive']}  |  부정: {s['negative']}")
