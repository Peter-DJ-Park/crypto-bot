"""
전체 설정값 관리
환경변수로 API 키를 주입받습니다.
"""
import os

# ── 빗썸 API ─────────────────────────────────────────────
BITHUMB_ACCESS  = os.getenv("BITHUMB_ACCESS", "")
BITHUMB_SECRET  = os.getenv("BITHUMB_SECRET", "")

# ── 분석 대상 코인 ────────────────────────────────────────
TICKERS = ["BTC", "XRP", "ETH", "SOL", "DOGE"]

# ── 무한매수법 설정 ───────────────────────────────────────
TOTAL_SEED    = 100_000          # 총 시드 (원)
SPLIT         = 20               # 분할 수
BASE_AMOUNT   = TOTAL_SEED / SPLIT  # 1회 기본 매수금액 (5,000원)
TARGET_PROFIT = 0.10             # 익절 목표 (+10%)
QUARTER_SELL  = 0.25             # 쿼터손절 비율 (1/4)

# 매수 비중 테이블: (평단 대비 하락률 기준, 매수 배율)
BUY_RATIO_TABLE = [
    ( 0.00, 0.5),   # 평단 이상      → 0.5배
    (-0.03, 1.0),   # -3%  이내     → 1.0배
    (-0.07, 1.5),   # -7%  이내     → 1.5배
    (-0.10, 2.0),   # -10% 이내     → 2.0배
    (-0.99, 2.5),   # -10% 초과     → 2.5배
]

# ── 네이버 뉴스 API ──────────────────────────────────────
NAVER_CLIENT_ID     = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
NEWS_QUERY          = "비트코인 암호화폐"
NEWS_COUNT          = 20

# ── Claude (Anthropic) API ───────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── 텔레그램 ─────────────────────────────────────────────
TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHATID = os.getenv("TELEGRAM_CHATID", "")

# ── 기타 ─────────────────────────────────────────────────
STATE_FILE = "state.json"
CHART_DIR  = "charts"

# API 키가 없으면 자동으로 테스트 모드 (목데이터 사용)
TEST_MODE = not bool(BITHUMB_ACCESS and BITHUMB_SECRET)
