"""
[Step 1] 빗썸 일봉 OHLCV 데이터 수집
TEST_MODE=True 이면 목데이터 자동 사용
"""
import pandas as pd
from config import TICKERS, TEST_MODE


def get_ohlcv_real(ticker: str, count: int = 30) -> pd.DataFrame:
    """빗썸 실제 API로 일봉 데이터 수집"""
    import pybithumb
    df = pybithumb.get_candlestick(ticker, chart_intervals="24h")
    if df is None or df.empty:
        raise ValueError(f"{ticker} 데이터 없음")
    df.columns = ["open", "close", "high", "low", "volume"]
    df = df.tail(count).copy()
    df.index = pd.to_datetime(df.index)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def get_ohlcv_mock(ticker: str, count: int = 30) -> pd.DataFrame:
    """테스트용 목데이터 반환"""
    from mock_data import MOCK_OHLCV
    return MOCK_OHLCV[ticker].tail(count).copy()


def get_ohlcv(ticker: str, count: int = 30) -> pd.DataFrame:
    """설정에 따라 실제/목 데이터 반환"""
    return get_ohlcv_mock(ticker, count) if TEST_MODE else get_ohlcv_real(ticker, count)


def get_all_ohlcv() -> dict:
    """전체 분석 대상 코인 데이터 일괄 수집"""
    result = {}
    mode = "🧪 목데이터" if TEST_MODE else "🌐 빗썸 API"
    print(f"  모드: {mode}")
    for ticker in TICKERS:
        try:
            result[ticker] = get_ohlcv(ticker)
            latest = result[ticker]["close"].iloc[-1]
            print(f"  ✅ {ticker:5s} | {latest:>15,.0f}원 | {len(result[ticker])}일치")
        except Exception as e:
            print(f"  ❌ {ticker} 실패: {e}")
    return result


if __name__ == "__main__":
    print("=" * 50)
    print("Step 1: 빗썸 일봉 데이터 수집")
    print("=" * 50)
    data = get_all_ohlcv()
    print(f"\n✅ 수집 완료: {len(data)}개 코인")
    if "BTC" in data:
        print("\n[BTC 최근 5일]")
        print(data["BTC"].tail(5).to_string())
