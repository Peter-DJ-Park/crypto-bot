"""
[Step 5] 캔들차트 + 볼린저밴드 + 거래량 + 지표 차트 생성
다크 테마 / PNG 파일 저장
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd
import numpy as np

from config import CHART_DIR


def _ensure_dir():
    os.makedirs(CHART_DIR, exist_ok=True)


def draw_chart(ticker: str, df: pd.DataFrame,
               indicators: dict, save_path: str = None) -> str:
    """
    캔들차트 + 볼린저밴드 + RSI + 거래량 통합 차트 생성
    Returns: 저장된 파일 경로
    """
    _ensure_dir()
    if save_path is None:
        save_path = os.path.join(CHART_DIR, f"chart_{ticker.lower()}.png")

    close = df["close"]
    dates = list(range(len(df)))

    # ── 지표 계산 ─────────────────────────────────
    bb_mid   = close.rolling(20).mean()
    bb_std   = close.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    ma5      = close.rolling(5).mean()

    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rsi   = 100 - (100 / (1 + gain / loss.replace(0, 1e-9)))

    # ── 레이아웃 ──────────────────────────────────
    BG    = "#1a1a2e"
    PANEL = "#16213e"
    UP    = "#26a69a"
    DOWN  = "#ef5350"
    TEXT  = "#e0e0e0"

    fig = plt.figure(figsize=(14, 9), facecolor=BG)
    gs  = gridspec.GridSpec(3, 1, height_ratios=[3, 1, 1],
                            hspace=0.06, figure=fig)

    ax1 = fig.add_subplot(gs[0])  # 캔들
    ax2 = fig.add_subplot(gs[1], sharex=ax1)  # RSI
    ax3 = fig.add_subplot(gs[2], sharex=ax1)  # 거래량

    for ax in [ax1, ax2, ax3]:
        ax.set_facecolor(PANEL)
        ax.tick_params(colors=TEXT, labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333355")
        ax.grid(color="#223", linestyle="--", linewidth=0.4, alpha=0.6)

    # ── 캔들차트 ──────────────────────────────────
    for i, (_, row) in enumerate(df.iterrows()):
        color = UP if row["close"] >= row["open"] else DOWN
        ax1.plot([i, i], [row["low"], row["high"]], color=color, lw=0.8)
        ax1.bar(i, abs(row["close"] - row["open"]),
                bottom=min(row["open"], row["close"]),
                color=color, width=0.6, alpha=0.9)

    # 볼린저밴드
    ax1.plot(dates, bb_upper, color="#90caf9", lw=0.8, ls="--", label="BB Upper")
    ax1.plot(dates, bb_mid,   color="#ffeb3b", lw=1.0,           label="MA20")
    ax1.plot(dates, bb_lower, color="#90caf9", lw=0.8, ls="--", label="BB Lower")
    ax1.fill_between(dates, bb_upper, bb_lower, alpha=0.04, color="#90caf9")

    # MA5
    ax1.plot(dates, ma5, color="#ff9800", lw=1.0, label="MA5")

    ax1.set_title(f"{ticker} / KRW  |  Daily Chart  |  RSI: {indicators['rsi']}  |  BB%: {indicators['bb_pct']}%",
                  color=TEXT, fontsize=11, pad=8)
    ax1.set_ylabel("Price (KRW)", color=TEXT, fontsize=9)
    legend = ax1.legend(facecolor="#223", labelcolor=TEXT, fontsize=7,
                         loc="upper left", framealpha=0.7)

    # 현재가 수평선
    current = indicators["current_price"]
    ax1.axhline(current, color="#fff176", lw=0.7, ls=":")
    ax1.text(len(df) - 0.5, current, f" {current:,.0f}",
             color="#fff176", fontsize=7, va="center")

    # 신호 박스
    signal_colors = {
        "강력 매수": "#26a69a", "매수": "#80cbc4",
        "중립": "#aaaaaa", "관망": "#ffb74d", "매도": "#ef5350",
    }
    signal_text  = indicators.get("signal", "중립 ➡️")
    signal_color = next((v for k, v in signal_colors.items()
                         if k in signal_text), "#aaaaaa")
    ax1.text(0.99, 0.97, signal_text, transform=ax1.transAxes,
             color=signal_color, fontsize=9, ha="right", va="top",
             bbox=dict(facecolor="#111122", alpha=0.7, edgecolor=signal_color, pad=3))

    # ── RSI 패널 ──────────────────────────────────
    ax2.plot(dates, rsi, color="#ce93d8", lw=1.2, label="RSI(14)")
    ax2.axhline(70, color=DOWN, lw=0.7, ls="--", alpha=0.6)
    ax2.axhline(30, color=UP,   lw=0.7, ls="--", alpha=0.6)
    ax2.fill_between(dates, rsi, 70, where=(rsi >= 70),
                     color=DOWN, alpha=0.15)
    ax2.fill_between(dates, rsi, 30, where=(rsi <= 30),
                     color=UP,   alpha=0.15)
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("RSI", color=TEXT, fontsize=8)
    ax2.text(0.01, 0.85, f"RSI: {indicators['rsi']}", transform=ax2.transAxes,
             color="#ce93d8", fontsize=8)

    # ── 거래량 패널 ───────────────────────────────
    vol_avg = df["volume"].rolling(5).mean()
    for i, (_, row) in enumerate(df.iterrows()):
        color = UP if row["close"] >= row["open"] else DOWN
        ax3.bar(i, row["volume"], color=color, alpha=0.7, width=0.6)
    ax3.plot(dates, vol_avg, color="#ffeb3b", lw=0.8, ls="--", label="Vol MA5")
    ax3.set_ylabel("Volume", color=TEXT, fontsize=8)
    ax3.set_xlabel(f"Recent {len(df)} Days", color=TEXT, fontsize=8)

    plt.setp(ax1.get_xticklabels(), visible=False)
    plt.setp(ax2.get_xticklabels(), visible=False)

    plt.savefig(save_path, dpi=150, bbox_inches="tight",
                facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"  ✅ {ticker} 차트 저장: {save_path}")
    return save_path


def draw_all_charts(ohlcv_data: dict, analysis: dict) -> list:
    """전체 코인 차트 일괄 생성"""
    paths = []
    for ticker, df in ohlcv_data.items():
        ind = analysis[ticker]["indicators"]
        ind["signal"] = analysis[ticker]["signal"]
        path = draw_chart(ticker, df, ind)
        paths.append(path)
    return paths


if __name__ == "__main__":
    print("=" * 50)
    print("Step 5: 차트 생성")
    print("=" * 50)
    from mock_data import MOCK_OHLCV, MOCK_NEWS
    from news_collector import extract_keywords
    from analyzer import analyze_all

    kw       = extract_keywords(MOCK_NEWS)
    analysis = analyze_all(MOCK_OHLCV, kw)
    paths    = draw_all_charts(MOCK_OHLCV, analysis)
    print(f"\n✅ 차트 생성 완료: {len(paths)}개")
    for p in paths:
        print(f"  → {p}")
