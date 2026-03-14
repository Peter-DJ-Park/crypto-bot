"""
메인 실행 파이프라인
Step 1~8 순서대로 실행

사용법:
  python main.py           # 전체 파이프라인 실행
  python main.py --step 3  # 특정 단계만 테스트
"""
import sys
import os
from datetime import datetime


def banner(step: int, title: str):
    print(f"\n{'='*50}")
    print(f"  [{step}] {title}")
    print(f"{'='*50}")


def main():
    start = datetime.now()
    print(f"\n🚀 암호화폐 분석봇 시작: {start.strftime('%Y-%m-%d %H:%M:%S')}")

    # ── Step 1: 빗썸 일봉 수집 ───────────────────────
    banner(1, "빗썸 일봉 데이터 수집")
    from data_collector import get_all_ohlcv
    ohlcv_data = get_all_ohlcv()
    if not ohlcv_data:
        print("❌ 데이터 수집 실패, 종료")
        return

    # ── Step 2: 뉴스 수집 ────────────────────────────
    banner(2, "네이버 뉴스 수집")
    from news_collector import get_news, extract_keywords
    news_list = get_news()
    keywords  = extract_keywords(news_list)
    print(f"  뉴스: {len(news_list)}건 | 키워드: {len(keywords)}개")
    print(f"  Top5: {', '.join(k for k,_ in keywords[:5])}")

    # ── Step 3: 분석 ─────────────────────────────────
    banner(3, "기술적 분석")
    from analyzer import analyze_all
    analysis = analyze_all(ohlcv_data, keywords)
    for ticker, data in analysis.items():
        ind = data["indicators"]
        print(f"  {ticker:5s} | RSI:{ind['rsi']:5.1f} | "
              f"BB:{ind['bb_pct']:5.1f}% | {data['signal']}")

    # ── Step 4: 리포트 생성 ───────────────────────────
    banner(4, "리포트 생성")
    from report_generator import generate_report
    # selected는 Step7 이후에 채워짐, 우선 None
    report_text = generate_report(analysis, news_list, keywords)
    print("  ✅ 리포트 생성 완료")

    # ── Step 5: 차트 생성 ────────────────────────────
    banner(5, "차트 생성")
    from chart_generator import draw_all_charts
    chart_paths = draw_all_charts(ohlcv_data, analysis)

    # ── Step 6: 1차 텔레그램 발송 (리포트 + 차트) ────
    banner(6, "텔레그램 발송 (리포트 + 차트)")
    from telegram_sender import send_report_with_charts, send_message, send_trade_result
    send_report_with_charts(report_text, chart_paths)

    # ── Step 7: Claude AI 종목 선정 ───────────────────
    banner(7, "Claude AI 종목 선정")
    from coin_selector import select_coin
    selected = select_coin(analysis, keywords)

    # AI 선정 결과를 포함한 추가 리포트 발송
    ai_msg = (
        f"🤖 <b>AI 종목 선정 결과</b>\n"
        f"선정 종목: <b>{selected['selected']}</b>\n"
        f"이유: {selected['reason']}\n"
        f"리스크: {selected['risk_level']}\n"
        f"전략: {selected['strategy']}\n"
        f"주의: {selected.get('caution','')}"
    )
    send_message(ai_msg)

    # ── Step 8: 자동거래 실행 ─────────────────────────
    banner(8, f"자동거래 실행 ({selected['selected']})")
    from trader import run_trade
    trade_result = run_trade(selected["selected"])
    send_trade_result(trade_result)

    # ── 완료 ─────────────────────────────────────────
    elapsed = (datetime.now() - start).seconds
    print(f"\n{'='*50}")
    print(f"  ✅ 전체 파이프라인 완료 ({elapsed}초 소요)")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    # --step N 옵션으로 개별 단계 테스트 가능
    if "--step" in sys.argv:
        idx   = sys.argv.index("--step")
        step  = int(sys.argv[idx + 1])
        mods  = [
            ("data_collector", "get_all_ohlcv"),
            ("news_collector", "get_news"),
            ("analyzer",       "analyze_all"),
            ("report_generator","generate_report"),
            ("chart_generator", "draw_all_charts"),
            ("telegram_sender", "send_message"),
            ("coin_selector",   "select_coin"),
            ("trader",          "run_trade"),
        ]
        module_name, func_name = mods[step - 1]
        os.system(f"python {module_name}.py")
    else:
        main()
