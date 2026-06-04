import requests
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
GNEWS_API_KEY = os.getenv('GNEWS_API_KEY', '')

SUPPLY_CHAIN_QUERIES = [
    'supply chain disruption',
    'semiconductor shortage',
    'oil price shock',
    'shipping crisis port',
    'trade restriction tariff',
    'climate disaster flood earthquake',
    'currency crisis devaluation',
]

def fetch_newsapi(query, page_size=10):
    """Fetch from NewsAPI"""
    if not NEWS_API_KEY:
        return []
    url = 'https://newsapi.org/v2/everything'
    params = {
        'q': query,
        'pageSize': page_size,
        'language': 'en',
        'sortBy': 'publishedAt',
        'apiKey': NEWS_API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get('articles', [])
    except Exception as e:
        print(f"NewsAPI error: {e}")
    return []

def fetch_gnews(query, max_results=10):
    """Fetch from GNews as fallback"""
    if not GNEWS_API_KEY:
        return []
    url = 'https://gnews.io/api/v4/search'
    params = {
        'q': query,
        'max': max_results,
        'lang': 'en',
        'token': GNEWS_API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            articles = data.get('articles', [])
            # Normalize GNews format to NewsAPI format
            normalized = []
            for a in articles:
                normalized.append({
                    'title': a.get('title', ''),
                    'description': a.get('description', ''),
                    'url': a.get('url', ''),
                    'publishedAt': a.get('publishedAt', ''),
                    'source': {'name': a.get('source', {}).get('name', 'GNews')}
                })
            return normalized
    except Exception as e:
        print(f"GNews error: {e}")
    return []

def fetch_all_news():
    """Fetch news from all sources across all supply chain queries"""
    all_articles = []
    seen_titles = set()

    for query in SUPPLY_CHAIN_QUERIES:
        articles = fetch_newsapi(query, page_size=5)
        if not articles:
            articles = fetch_gnews(query, max_results=5)

        for a in articles:
            title = a.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                all_articles.append(a)

    return all_articles

def parse_date(date_str):
    """Parse ISO date string safely and convert to IST"""
    if not date_str:
        return datetime.now(IST)

    try:
        # handle Zulu time safely
        if date_str.endswith("Z"):
            date_str = date_str.replace("Z", "+00:00")

        dt = datetime.fromisoformat(date_str)

        # ensure timezone aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))

        return dt.astimezone(IST)

    except:
        return datetime.now(IST)