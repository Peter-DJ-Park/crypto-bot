import os

# 내 컴퓨터(로컬)에서는 .env를 읽고, 깃허브 액션에서는 에러 없이 넘어갑니다.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── 빗썸 API ─────────────────────────────────────────────
BITHUMB_ACCESS  = os.getenv("BITHUMB_ACCESS", "")
BITHUMB_SECRET  = os.getenv("BITHUMB_SECRET", "")

# ── 분석 대상 코인 ────────────────────────────────────────
TICKERS = ["BTC", "XRP", "ETH", "SOL"]

# ── 무한매수법 설정 ───────────────────────────────────────
TOTAL_SEED    = 100_000
SPLIT         = 20
BASE_AMOUNT   = TOTAL_SEED / SPLIT
TARGET_PROFIT = 0.10
QUARTER_SELL  = 0.25

BUY_RATIO_TABLE = [
    ( 0.00, 0.5),
    (-0.03, 1.0),
    (-0.07, 1.5),
    (-0.10, 2.0),
    (-0.99, 2.5),
]

# ── 네이버 뉴스 API ──────────────────────────────────────
NAVER_CLIENT_ID     = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
NEWS_QUERY          = "비트코인 암호화폐"
NEWS_COUNT          = 20


# ── 텔레그램 ─────────────────────────────────────────────
TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHATID = os.getenv("TELEGRAM_CHATID", "")

# ── 기타 ─────────────────────────────────────────────────
STATE_FILE = "state.json"
CHART_DIR  = "charts"

# ── 모드 설정 ────────────────────────────────────────────
# 빗썸 키가 없으면 목데이터(테스트) 모드
TEST_MODE  = not bool(BITHUMB_ACCESS and BITHUMB_SECRET)

# 빗썸 키가 정상적으로 있으면 실거래 모드 켜짐!
TRADE_MODE = bool(BITHUMB_ACCESS and BITHUMB_SECRET)

# ── Gemini API (무료) ───────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
