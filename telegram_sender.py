"""
[Step 6] 텔레그램 발송
TEST_MODE 와 완전히 분리 - 텔레그램 키만 있으면 항상 실제 발송
"""
import re
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHATID

# 빗썸 키와 무관하게 텔레그램 키만 있으면 실제 발송
ENABLED = bool(TELEGRAM_TOKEN and TELEGRAM_CHATID)


def _clean(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def send_message(text: str) -> bool:
    if not ENABLED:
        print(f"\n[텔레그램 키 미등록]\n{_clean(text)}")
        return False
    try:
        url  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        resp = requests.post(url, data={
            "chat_id"   : TELEGRAM_CHATID,
            "text"      : text,
            "parse_mode": "HTML",
        }, timeout=15)
        ok = resp.status_code == 200
        if not ok:
            print(f"  ⚠️ 텔레그램 응답: {resp.status_code} {resp.text[:100]}")
        return ok
    except Exception as e:
        print(f"  ❌ 메시지 발송 실패: {e}")
        return False


def send_photo(image_path: str, caption: str = "") -> bool:
    if not ENABLED:
        print(f"  [텔레그램 키 미등록] {image_path}")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        with open(image_path, "rb") as f:
            resp = requests.post(url, data={
                "chat_id"   : TELEGRAM_CHATID,
                "caption"   : caption,
                "parse_mode": "HTML",
            }, files={"photo": f}, timeout=30)
        ok = resp.status_code == 200
        if not ok:
            print(f"  ⚠️ 이미지 응답: {resp.status_code} {resp.text[:100]}")
        return ok
    except Exception as e:
        print(f"  ❌ 이미지 발송 실패: {e}")
        return False


def send_report_with_charts(report_text: str, chart_paths: list):
    mode = "🌐 실제 발송" if ENABLED else "⚠️ 키 미등록"
    print(f"  텔레그램 모드: {mode}")

    ok = send_message(report_text)
    print(f"  {'✅' if ok else '❌'} 리포트 발송")

    for path in chart_paths:
        ticker  = path.split("chart_")[-1].replace(".png", "").upper()
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
        msg = f"ℹ️ 매매 없음"
    send_message(msg)
