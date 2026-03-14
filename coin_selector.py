"""
[Step 7] Claude AI 기반 종목 선정
분석 결과를 Claude에게 전달하고 최적 투자 종목 1개를 선정받음
"""
import json
import requests
from config import ANTHROPIC_API_KEY, TICKERS, TEST_MODE


def _build_prompt(analysis: dict, keywords: list) -> str:
    """Claude 프롬프트 구성"""
    lines = []
    for ticker, data in analysis.items():
        ind = data["indicators"]
        lines.append(
            f"- {ticker}: 현재가={ind['current_price']:,.0f}원, "
            f"등락={ind['change_pct']:+.2f}%, RSI={ind['rsi']}, "
            f"BB위치={ind['bb_pct']}%, MACD히스토={ind['macd_hist']:.4f}, "
            f"거래량비={ind['vol_ratio']}x, 캔들={data['pattern']}, "
            f"신호={data['signal']}"
        )
    summary = "\n".join(lines)

    s      = list(analysis.values())[0]["sentiment"]
    kw_str = ", ".join(k for k, _ in keywords[:10])

    return f"""당신은 암호화폐 투자 전문가입니다.
아래 기술적 분석 데이터와 뉴스 감성 분석을 바탕으로
오늘 무한매수법(10만원 / 20분할 / +10% 익절)을 적용할
최적의 코인 1개를 선정하고 투자 전략을 제시해주세요.

## 분석 대상 코인
{summary}

## 뉴스 감성
- 종합: {s['verdict']} ({s['score']}점)
- 긍정 키워드: {', '.join(s['positive']) or '없음'}
- 부정 키워드: {', '.join(s['negative']) or '없음'}
- 주요 키워드: {kw_str}

## 무한매수법 최적 종목 선정 기준
1. RSI 50 이하 (매수 여력 확보)
2. 뉴스 감성 중립 이상
3. 거래량 평균 이상 (vol_ratio > 1.0)
4. 볼린저밴드 하단 근처 (bb_pct 50 이하)
5. 과도한 하락세보다는 횡보/반등 국면 선호

반드시 아래 JSON 형식으로만 응답하세요. 마크다운 없이 JSON만:
{{
  "selected": "XRP",
  "reason": "선정 이유 2~3문장으로 구체적으로",
  "risk_level": "낮음/중간/높음",
  "strategy": "오늘 매수 전략 한 줄",
  "caution": "주의사항 한 줄"
}}"""


def select_coin_real(analysis: dict, keywords: list) -> dict:
    """Claude API 실제 호출 (claude-sonnet-4-20250514)"""
    prompt = _build_prompt(analysis, keywords)

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key"        : ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type"     : "application/json",
        },
        json={
            "model"     : "claude-sonnet-4-20250514",
            "max_tokens": 1024,
            "messages"  : [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    response.raise_for_status()
    text = response.json()["content"][0]["text"].strip()

    # 마크다운 코드블록 제거 (혹시 있으면)
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("```").strip()

    return json.loads(text)


def select_coin_mock(analysis: dict, keywords: list) -> dict:
    """테스트용 목 결과: 신호가 가장 좋은 코인 자동 선정"""
    signal_priority = {
        "강력 매수 ⚡": 5, "매수 🟢": 4,
        "중립 ➡️"    : 3, "관망 🟡": 2, "매도/회피 🔴": 1,
    }
    best   = max(analysis.items(),
                 key=lambda x: signal_priority.get(x[1]["signal"], 0))
    ticker = best[0]
    ind    = best[1]["indicators"]
    return {
        "selected"  : ticker,
        "reason"    : (f"RSI {ind['rsi']}로 매수 여력이 있으며 "
                       f"BB위치 {ind['bb_pct']}%로 진입에 유리한 구간. "
                       f"뉴스 감성 긍정적으로 단기 반등 기대."),
        "risk_level": "중간",
        "strategy"  : "슬롯 1/20부터 분할 매수 시작, 평단 +10% 익절 목표",
        "caution"   : "시장 전반 급락 시 쿼터손절 기준 철저히 준수",
    }


def select_coin(analysis: dict, keywords: list) -> dict:
    """설정에 따라 실제 Claude API / 목 선정 결과 반환"""
    try:
        if TEST_MODE or not ANTHROPIC_API_KEY:
            result = select_coin_mock(analysis, keywords)
            print("  모드: 🧪 목 선정")
        else:
            result = select_coin_real(analysis, keywords)
            print("  모드: 🤖 Claude AI")

        print(f"  ✅ 선정 종목: {result['selected']}")
        print(f"  이유: {result['reason']}")
        print(f"  리스크: {result['risk_level']}")
        return result

    except Exception as e:
        print(f"  ❌ 종목 선정 실패: {e}, 기본값 XRP 사용")
        return {
            "selected"  : "XRP",
            "reason"    : "선정 오류로 기본값 적용",
            "risk_level": "중간",
            "strategy"  : "기본 무한매수법 적용",
            "caution"   : "수동으로 종목 재확인 필요",
        }


if __name__ == "__main__":
    print("=" * 50)
    print("Step 7: Claude AI 종목 선정")
    print("=" * 50)
    from mock_data import MOCK_OHLCV, MOCK_NEWS
    from news_collector import extract_keywords
    from analyzer import analyze_all

    kw       = extract_keywords(MOCK_NEWS)
    analysis = analyze_all(MOCK_OHLCV, kw)
    result   = select_coin(analysis, kw)

    print("\n[선정 결과]")
    for k, v in result.items():
        print(f"  {k:12s}: {v}")
