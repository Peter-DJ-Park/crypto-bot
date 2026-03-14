# 🤖 암호화폐 무한매수법 자동매매봇

빗썸 API + Claude AI + 네이버 뉴스를 활용한 암호화폐 자동매매 시스템

---

## 📋 주요 기능

| 단계 | 기능 | 설명 |
|------|------|------|
| 1 | 데이터 수집 | 빗썸 일봉 OHLCV (BTC, XRP, ETH, SOL, DOGE) |
| 2 | 뉴스 수집 | 네이버 뉴스 API 암호화폐 뉴스 수집 |
| 3 | 기술적 분석 | RSI, MACD, 볼린저밴드, 캔들패턴 |
| 4 | 리포트 생성 | 일일 분석 리포트 텍스트 생성 |
| 5 | 차트 생성 | 다크테마 캔들차트 + 지표 이미지 |
| 6 | 텔레그램 발송 | 리포트 + 차트 이미지 자동 발송 |
| 7 | AI 종목 선정 | Claude AI가 최적 매수 종목 선정 |
| 8 | 자동거래 | 무한매수법 기반 자동 매수/매도 |

---

## 🔧 무한매수법 설정

```
총 시드    : 100,000원
분할 수    : 20분할 (1회 기본 5,000원)
익절 목표  : 평단가 +10%
쿼터손절   : 20슬롯 소진 시 보유량 1/4 매도
매수 주기  : 매일 오전 9시 (KST)
```

### 매수 비중 테이블

| 현재가 vs 평단 | 매수 배율 | 매수금액 |
|--------------|---------|---------|
| 평단 이상 | 0.5배 | 2,500원 |
| -3% 이내 | 1.0배 | 5,000원 |
| -7% 이내 | 1.5배 | 7,500원 |
| -10% 이내 | 2.0배 | 10,000원 |
| -10% 초과 | 2.5배 | 12,500원 |

---

## 📁 파일 구조

```
crypto-bot/
├── config.py              # 전체 설정값
├── mock_data.py           # 테스트용 목데이터
├── data_collector.py      # 빗썸 일봉 수집
├── news_collector.py      # 네이버 뉴스 수집
├── analyzer.py            # 기술적 지표 분석
├── report_generator.py    # 리포트 생성
├── chart_generator.py     # 차트 이미지 생성
├── telegram_sender.py     # 텔레그램 발송
├── coin_selector.py       # Claude AI 종목 선정
├── trader.py              # 무한매수법 자동거래
├── main.py                # 전체 파이프라인
├── requirements.txt
└── .github/
    └── workflows/
        └── trading_bot.yml  # GitHub Actions 스케줄
```

---

## 🚀 설치 및 실행

### 1. 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정 (.env)

```
BITHUMB_ACCESS=빗썸_Connect_Key
BITHUMB_SECRET=빗썸_Secret_Key
NAVER_CLIENT_ID=네이버_Client_ID
NAVER_CLIENT_SECRET=네이버_Client_Secret
ANTHROPIC_API_KEY=Claude_API_Key
TELEGRAM_TOKEN=텔레그램_봇_토큰
TELEGRAM_CHATID=텔레그램_채팅_ID
```

### 3. 로컬 실행

```bash
# 전체 파이프라인
python main.py

# 단계별 테스트
python data_collector.py
python news_collector.py
python analyzer.py
python chart_generator.py
python coin_selector.py
python trader.py
```

---

## ☁️ GitHub Actions 자동배포

### GitHub Secrets 등록 (8개)

| Name | 설명 |
|------|------|
| `BITHUMB_ACCESS` | 빗썸 Connect Key |
| `BITHUMB_SECRET` | 빗썸 Secret Key |
| `NAVER_CLIENT_ID` | 네이버 Client ID |
| `NAVER_CLIENT_SECRET` | 네이버 Client Secret |
| `ANTHROPIC_API_KEY` | Claude API Key |
| `TELEGRAM_TOKEN` | 텔레그램 봇 토큰 |
| `TELEGRAM_CHATID` | 텔레그램 채팅 ID |
| `GH_PAT` | GitHub Personal Access Token |
| `STATE_JSON` | `{}` (초기값) |

### 실행 스케줄

```
매일 KST 오전 9시 자동 실행
수동 실행: Actions 탭 → Run workflow
```

---

## 📱 텔레그램 알림 예시

```
📊 암호화폐 일일 리포트
📅 2025년 03월 14일 09:00

📰 뉴스 감성: 긍정적 📈 (70점)

📈 코인별 분석
[XRP] 🔺 +2.3%
현재가: 3,800원
RSI: 38.5 | BB: 22%
신호: 강력 매수 ⚡

🤖 AI 종목 선정: XRP

✅ 매수 완료
매수금액: 7,500원 (x1.5배)
현재가: 3,800원
평단가: 3,850원
목표가: 4,235원 (+10%)
슬롯: 3/20
```

---

## ⚠️ 주의사항

- 본 봇은 투자 참고용이며 투자 손실에 대한 책임은 본인에게 있습니다
- 처음엔 소액(1만원)으로 테스트 후 실제 시드 투입 권장
- 빗썸 API 키는 **거래 권한만** 부여하고 출금 권한은 부여하지 마세요
- `state.json` 은 매매 상태를 저장하므로 임의로 삭제하지 마세요

---

## 🔑 API 키 발급 위치

| API | 발급 위치 |
|-----|---------|
| 빗썸 | [pc.bithumb.com](https://pc.bithumb.com) → 마이페이지 → Open API |
| 네이버 | [developers.naver.com](https://developers.naver.com) → 앱 등록 → 검색 API |
| Claude | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| 텔레그램 | 텔레그램 @BotFather → /newbot |
