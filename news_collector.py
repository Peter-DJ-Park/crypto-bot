"""
[Step 2] 네이버 뉴스 API로 암호화폐 뉴스 수집 + 키워드 분석
"""
import re
import requests
from collections import Counter
from config import (NAVER_CLIENT_ID, NAVER_CLIENT_SECRET,
                    NEWS_QUERY, NEWS_COUNT, TEST_MODE)


def get_naver_news(query: str = NEWS_QUERY) -> list:
    """네이버 뉴스 API 호출"""
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id"    : NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": query, "display": NEWS_COUNT, "sort": "date"}
    resp   = requests.get(url, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    items  = resp.json().get("items", [])
    return [
        {
            "title": re.sub(r"<[^>]+>", "", item["title"]),
            "desc" : re.sub(r"<[^>]+>", "", item["description"]),
            "date" : item["pubDate"],
        }
        for item in items
    ]


def get_news(query: str = NEWS_QUERY) -> list:
    """설정에 따라 실제/목 뉴스 반환"""
    if TEST_MODE:
        from mock_data import MOCK_NEWS
        return MOCK_NEWS
    return get_naver_news(query)


def extract_keywords(news_list: list, top_n: int = 15) -> list:
    """뉴스 제목 기반 주요 키워드 추출 (불용어 제거)"""
    STOP = {
        "의","을","를","이","가","은","는","에","서","도","로","과","와",
        "한","하","에서","으로","비트코인","암호화폐","코인","시장","투자",
        "가격","뉴스","최근","관련","기록","이후","통해","대한","위한",
    }
    words = []
    for item in news_list:
        tokens = re.findall(r"[가-힣a-zA-Z]{2,}", item["title"])
        words.extend(w for w in tokens if w not in STOP)
    return Counter(words).most_common(top_n)


if __name__ == "__main__":
    print("=" * 50)
    print("Step 2: 뉴스 수집 + 키워드 분석")
    print("=" * 50)
    news = get_news()
    print(f"\n✅ 수집 완료: {len(news)}건")
    print("\n[뉴스 헤드라인 Top5]")
    for i, n in enumerate(news[:5], 1):
        print(f"  {i}. {n['title']}")
    kw = extract_keywords(news)
    print(f"\n[주요 키워드 Top10]")
    for word, cnt in kw[:10]:
        print(f"  {word:10s}: {cnt}회")
