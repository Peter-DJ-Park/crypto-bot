"""
[Step 6] 텔레그램 리포트 + 차트 이미지 발송
빗썸 키 무관하게 텔레그램은 항상 실제 발송
"""
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHATID

TELEGRAM_ENABLED = bool(TELEGRAM_TOKEN and TELEGRAM_CHATID)


def send_message(text: str) -> bool:
    if not TELEGRAM_ENABLED:
        print("\n[텔레그램 키 없음 - 시뮬레이션]")
        import re
        print(re.sub(r"<[^>]+>", "", text))
        return True
    try:
        url  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        resp = requests.post(url, data={
            "chat_id"   : TELEGRAM_CHATID,
            "text"      : text,
            "parse_mode": "HTML",
        }, timeout=15)
        return resp.status_code == 200
    except Exception as e:
        print(f"  ❌ 메시지 발송 실패: {e}")
        return False


def send_photo(image_path: str, caption: str = "") -> bool:
    if not TELEGRAM_ENABLED:
        print(f"  [이미지 키 없음 - 시뮬레이션] {image_path}")
        return True
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        with open(image_path, "rb") as f:
            resp = requests.post(url, data={
                "chat_id"   : TELEGRAM_CHATID,
                "caption"   : caption,
                "parse_mode": "HTML",
            }, files={"photo": f}, timeout=30)
        return resp.status_code == 200
    except Exception as e:
        print(f"  ❌ 이미지 발송 실패: {e}")
        return False


def send_report_with_charts(report_text: str, chart_paths: list):
    mode = "🌐 실제 발송" if TELEGRAM_ENABLED else "🧪 시뮬레이션"
    print(f"  모드: {mode}")

    ok = send_message(report_text)
    print(f"  {'✅' if ok else '❌'} 리포트 텍스트 발송")

    for path in chart_paths:
        ticker  = path.split("chart_")[-1].replace(".png","").upper()
        caption = f"📊 <b>{ticker}</b> 일봉 차트"
        ok = send_photo(path, caption)
        print(f"  {'✅' if ok else '❌'} {ticker} 차트 발송")


def send_trade_result(result: dict):
    action = result.get("action")
    if action == "buy":
        msg = (
            f"✅ <b>매수 완료</b>\n"
            f"종목: <b>{result['ticker']}</b>\n"
            f"매수금액: {result['amount']:,.0f}원\n"
            f"현재가: {result['current']:,.0f}원\n"
            f"평단가: {result['avg_price']:,.0f}원\n"
            f"목표가: {result['target']:,.0f}원 (+10%)\n"
            f"슬롯: {result['slot']}/{result['total_slots']}"
        )
    elif action == "sell":
        msg = (
            f"🎉 <b>익절 완료!</b>\n"
            f"종목: <b>{result['ticker']}</b>\n"
            f"수익률: +{result['profit_pct']:.1f}%\n"
            f"수익금: +{result['profit_krw']:,.0f}원\n"
            f"사이클 #{result['cycle']} 종료\n"
            f"▶ 사이클 #{result['cycle']+1} 시작"
        )
    elif action == "quarter_sell":
        msg = (
            f"⚠️ <b>쿼터손절 실행</b>\n"
            f"종목: <b>{result['ticker']}</b>\n"
            f"슬롯 {result['total_slots']}회 소진\n"
            f"보유량 1/4 매도 후 재개"
        )
    else:
        msg = f"ℹ️ 매매 없음: {result}"
    send_message(msg)
