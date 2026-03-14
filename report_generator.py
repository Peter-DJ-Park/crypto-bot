"""
[Step 4] 일일 분석 리포트 텍스트 생성
텔레그램 HTML 포맷으로 출력
"""
from datetime import datetime


def generate_report(analysis: dict, news_list: list,
                    keywords: list, selected: dict = None) -> str:
    today = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    sep   = "─" * 28

    lines = [
        f"📊 <b>암호화폐 일일 리포트</b>",
        f"📅 {today}",
        sep,
    ]

    # ── 뉴스 감성 ──────────────────────────────────
    s = list(analysis.values())[0]["sentiment"]
    lines += [
        "",
        f"📰 <b>뉴스 감성 분석</b>",
        f"  종합: {s['verdict']}  (점수: {s['score']})",
        f"  긍정 키워드: {', '.join(s['positive']) or '없음'}",
        f"  부정 키워드: {', '.join(s['negative']) or '없음'}",
        f"  주요 키워드: {', '.join(k for k,_ in keywords[:6])}",
    ]

    # ── 코인별 분석 ────────────────────────────────
    lines += ["", f"📈 <b>코인별 분석</b>"]
    for ticker, data in analysis.items():
        ind  = data["indicators"]
        chg  = ind["change_pct"]
        icon = "🔺" if chg > 0 else "🔻"
        lines += [
            "",
            f"  <b>[{ticker}]</b>  {icon} {chg:+.2f}%",
            f"  현재가 : {ind['current_price']:>15,.0f}원",
            f"  RSI    : {ind['rsi']}  |  BB위치: {ind['bb_pct']}%",
            f"  MACD히스토그램: {ind['macd_hist']:.4f}",
            f"  거래량 비율: {ind['vol_ratio']}x",
            f"  캔들   : {data['pattern']}",
            f"  📌 {data['signal']}",
        ]

    # ── 주요 뉴스 ──────────────────────────────────
    lines += ["", sep, "", "📰 <b>오늘의 주요 뉴스</b>"]
    for item in news_list[:4]:
        lines.append(f"  · {item['title']}")

    # ── AI 종목 선정 결과 (있으면) ─────────────────
    if selected:
        lines += [
            "",
            sep,
            "",
            "🤖 <b>AI 종목 선정 결과</b>",
            f"  선정 종목: <b>{selected.get('selected', '?')}</b>",
            f"  선정 이유: {selected.get('reason', '')}",
            f"  리스크   : {selected.get('risk_level', '')}",
            f"  전략     : {selected.get('strategy', '')}",
        ]

    return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 50)
    print("Step 4: 리포트 생성")
    print("=" * 50)
    from mock_data import MOCK_OHLCV, MOCK_NEWS
    from news_collector import extract_keywords
    from analyzer import analyze_all

    kw       = extract_keywords(MOCK_NEWS)
    analysis = analyze_all(MOCK_OHLCV, kw)
    selected = {
        "selected"  : "XRP",
        "reason"    : "RSI 과매도 구간 + 긍정 뉴스 우세 + 거래량 증가",
        "risk_level": "중간",
        "strategy"  : "오늘부터 분할 매수 시작, 슬롯 1/20",
    }
    report = generate_report(analysis, MOCK_NEWS, kw, selected)
    # 태그 제거해서 콘솔 출력
    import re
    print(re.sub(r"<[^>]+>", "", report))
