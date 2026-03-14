"""
테스트용 목(Mock) 데이터
실제 API 키 없이도 전체 파이프라인 테스트 가능
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def make_ohlcv(base_price: float, days: int = 30,
               volatility: float = 0.03, seed: int = 42) -> pd.DataFrame:
    """현실적인 OHLCV 목데이터 생성"""
    np.random.seed(seed)
    dates  = [datetime.today() - timedelta(days=days - i) for i in range(days)]
    prices = [base_price]
    for _ in range(days - 1):
        prices.append(prices[-1] * (1 + np.random.normal(0, volatility)))

    rows = []
    for p in prices:
        o = p * (1 + np.random.uniform(-0.01,  0.01))
        c = p * (1 + np.random.uniform(-0.01,  0.01))
        h = max(o, c) * (1 + np.random.uniform(0,    0.015))
        l = min(o, c) * (1 - np.random.uniform(0,    0.015))
        v = np.random.uniform(50, 500)
        rows.append({"open": o, "close": c, "high": h, "low": l, "volume": v})

    df = pd.DataFrame(rows, index=pd.DatetimeIndex(dates))
    return df


# 코인별 기준가 (2025년 3월 기준 근사값)
MOCK_PRICES = {
    "BTC" : 130_000_000,
    "XRP" :       3_800,
    "ETH" :   5_200_000,
    "SOL" :     320_000,
    "DOGE":       1_100,
}

MOCK_OHLCV = {
    ticker: make_ohlcv(price, seed=i*10)
    for i, (ticker, price) in enumerate(MOCK_PRICES.items())
}

MOCK_NEWS = [
    {"title": "비트코인 1억3천만원 돌파, 상승세 지속",         "desc": "강한 매수세로 급등했습니다.", "date": "2025-03-13"},
    {"title": "리플 SEC 소송 최종 합의 임박, XRP 강세",        "desc": "규제 리스크 해소 기대감 급등.", "date": "2025-03-13"},
    {"title": "이더리움 ETF 승인 기대감 상승",                 "desc": "기관 자금 유입 가능성 언급.", "date": "2025-03-13"},
    {"title": "글로벌 암호화폐 시장 회복세",                   "desc": "전반적 상승 추세 지속.", "date": "2025-03-13"},
    {"title": "솔라나 디파이 생태계 급성장, TVL 신고가",        "desc": "TVL 사상 최고치 경신.", "date": "2025-03-13"},
    {"title": "미국 연준 금리 동결, 암호화폐 호재",            "desc": "위험자산 선호심리 회복.", "date": "2025-03-13"},
    {"title": "도지코인 일론 머스크 언급 후 급등",             "desc": "SNS 발언에 강한 반응.", "date": "2025-03-13"},
    {"title": "암호화폐 규제 강화 우려로 일부 하락",           "desc": "일부 국가 규제 강화 움직임.", "date": "2025-03-12"},
    {"title": "비트코인 신고가 돌파 도전",                     "desc": "기술적 저항선 돌파 주목.", "date": "2025-03-12"},
    {"title": "기관 투자자 암호화폐 매수세 강화, ETF 유입 최고", "desc": "ETF 유입액 역대 최고 기록.", "date": "2025-03-12"},
]
