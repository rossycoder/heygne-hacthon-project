"""
Live News Fetcher — GNews API
Fetches real articles with source name, URL, image, published time
filtered by city + country.
"""
import httpx
import os
from datetime import datetime, timezone

GNEWS_KEY = os.getenv("GNEWS_API_KEY", "")
GNEWS_BASE = "https://gnews.io/api/v4"

# City → (country_code, country_name, search_terms)
CITY_MAP = {
    # Pakistan
    "lahore":        ("pk", "Pakistan", ["Lahore", "Pakistan"]),
    "karachi":       ("pk", "Pakistan", ["Karachi", "Pakistan"]),
    "islamabad":     ("pk", "Pakistan", ["Islamabad", "Pakistan"]),
    "rawalpindi":    ("pk", "Pakistan", ["Rawalpindi", "Pakistan"]),
    "peshawar":      ("pk", "Pakistan", ["Peshawar", "Pakistan"]),
    "multan":        ("pk", "Pakistan", ["Multan", "Pakistan"]),
    "faisalabad":    ("pk", "Pakistan", ["Faisalabad", "Pakistan"]),
    "azad kashmir":  ("pk", "Pakistan", ["Azad Kashmir", "Pakistan"]),
    "pakistan":      ("pk", "Pakistan", ["Pakistan"]),
    # India
    "delhi":         ("in", "India", ["Delhi", "India"]),
    "mumbai":        ("in", "India", ["Mumbai", "India"]),
    "bangalore":     ("in", "India", ["Bangalore", "India"]),
    "india":         ("in", "India", ["India"]),
    # USA
    "new york":      ("us", "USA", ["New York", "USA"]),
    "los angeles":   ("us", "USA", ["Los Angeles", "USA"]),
    "chicago":       ("us", "USA", ["Chicago", "USA"]),
    "usa":           ("us", "USA", ["United States"]),
    # UK
    "london":        ("gb", "UK", ["London", "UK"]),
    "manchester":    ("gb", "UK", ["Manchester", "UK"]),
    "uk":            ("gb", "UK", ["United Kingdom"]),
    # UAE
    "dubai":         ("ae", "UAE", ["Dubai", "UAE"]),
    "abu dhabi":     ("ae", "UAE", ["Abu Dhabi", "UAE"]),
    "uae":           ("ae", "UAE", ["UAE"]),
    # Saudi Arabia
    "riyadh":        ("sa", "Saudi Arabia", ["Riyadh", "Saudi Arabia"]),
    "jeddah":        ("sa", "Saudi Arabia", ["Jeddah", "Saudi Arabia"]),
    "saudi arabia":  ("sa", "Saudi Arabia", ["Saudi Arabia"]),
    # Others
    "paris":         ("fr", "France", ["Paris", "France"]),
    "berlin":        ("de", "Germany", ["Berlin", "Germany"]),
    "beijing":       ("cn", "China", ["Beijing", "China"]),
    "tokyo":         ("jp", "Japan", ["Tokyo", "Japan"]),
    "toronto":       ("ca", "Canada", ["Toronto", "Canada"]),
    "vancouver":     ("ca", "Canada", ["Vancouver", "Canada"]),
    "montreal":      ("ca", "Canada", ["Montreal", "Canada"]),
    "canada":        ("ca", "Canada", ["Canada"]),
    "sydney":        ("au", "Australia", ["Sydney", "Australia"]),
    "melbourne":     ("au", "Australia", ["Melbourne", "Australia"]),
    "australia":     ("au", "Australia", ["Australia"]),
}

LANG_MAP = {
    "English": "en", "Urdu": "ur", "Arabic": "ar",
    "Hindi": "hi", "French": "fr", "Spanish": "es",
    "Chinese": "zh", "German": "de",
}


def _time_ago(published: str) -> str:
    """Convert ISO timestamp to '2h ago' style."""
    try:
        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        diff = datetime.now(timezone.utc) - dt
        mins = int(diff.total_seconds() / 60)
        if mins < 60:
            return f"{mins}m ago"
        elif mins < 1440:
            return f"{mins // 60}h ago"
        else:
            return f"{mins // 1440}d ago"
    except Exception:
        return ""


async def fetch_live_news(city: str, language: str = "English", max_articles: int = 10) -> dict:
    """
    Fetch real news articles for a city + country using GNews API.
    Returns { city, country, articles: [...], sources: [...] }
    """
    city_key = city.lower().strip()
    info = CITY_MAP.get(city_key)

    # Fuzzy match — check if city_key contains any known key
    if not info:
        for key, val in CITY_MAP.items():
            if key in city_key or city_key in key:
                info = val
                break

    if info:
        country_code, country_name, search_terms = info
    else:
        country_code = None
        country_name = city
        search_terms = [city]

    lang_code = LANG_MAP.get(language, "en")

    # Build query: "Lahore OR Pakistan"
    query = " OR ".join(f'"{t}"' for t in search_terms)

    params = {
        "q": query,
        "lang": lang_code if lang_code != "ur" else "en",  # GNews doesn't support Urdu, use English
        "max": max_articles,
        "sortby": "publishedAt",
        "apikey": GNEWS_KEY,
    }
    if country_code:
        params["country"] = country_code

    articles = []
    sources_seen = set()
    sources = []

    if not GNEWS_KEY:
        # No API key — return mock data so frontend still works
        return _mock_news(city, country_name)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{GNEWS_BASE}/search", params=params)
            resp.raise_for_status()
            data = resp.json()

        for art in data.get("articles", []):
            src_name = art.get("source", {}).get("name", "Unknown")
            src_url  = art.get("source", {}).get("url", "#")

            articles.append({
                "title":       art.get("title", ""),
                "description": art.get("description", ""),
                "url":         art.get("url", "#"),
                "image":       art.get("image"),
                "published":   art.get("publishedAt", ""),
                "time_ago":    _time_ago(art.get("publishedAt", "")),
                "source_name": src_name,
                "source_url":  src_url,
                "source_favicon": f"https://www.google.com/s2/favicons?domain={src_url}&sz=32",
            })

            if src_name not in sources_seen:
                sources_seen.add(src_name)
                sources.append({"name": src_name, "url": src_url,
                                 "favicon": f"https://www.google.com/s2/favicons?domain={src_url}&sz=32"})

    except Exception as e:
        # Fallback to mock if API fails
        return _mock_news(city, country_name)

    return {
        "city": city,
        "country": country_name,
        "language": language,
        "articles": articles,
        "sources": sources[:6],
        "total": len(articles),
    }


def _mock_news(city: str, country: str) -> dict:
    """Fallback mock articles when no API key is set."""
    mock = [
        {"title": f"Breaking: Major development in {city} today",
         "description": f"Latest updates from {city} as authorities respond to ongoing situation.",
         "url": "https://www.bbc.com/news", "image": None,
         "published": "", "time_ago": "1h ago",
         "source_name": "BBC News", "source_url": "https://bbc.com",
         "source_favicon": "https://www.google.com/s2/favicons?domain=bbc.com&sz=32"},
        {"title": f"{country} economy shows strong growth signals",
         "description": f"Economic indicators from {country} point to positive trends this quarter.",
         "url": "https://www.reuters.com", "image": None,
         "published": "", "time_ago": "2h ago",
         "source_name": "Reuters", "source_url": "https://reuters.com",
         "source_favicon": "https://www.google.com/s2/favicons?domain=reuters.com&sz=32"},
        {"title": f"Weather update: {city} forecast for this week",
         "description": f"Meteorological department issues forecast for {city} residents.",
         "url": "https://www.dawn.com", "image": None,
         "published": "", "time_ago": "3h ago",
         "source_name": "Dawn", "source_url": "https://dawn.com",
         "source_favicon": "https://www.google.com/s2/favicons?domain=dawn.com&sz=32"},
        {"title": f"Tech industry in {country} attracts record investment",
         "description": "Startups and tech companies see unprecedented funding rounds.",
         "url": "https://techcrunch.com", "image": None,
         "published": "", "time_ago": "4h ago",
         "source_name": "TechCrunch", "source_url": "https://techcrunch.com",
         "source_favicon": "https://www.google.com/s2/favicons?domain=techcrunch.com&sz=32"},
        {"title": f"Sports: {city} team advances to national finals",
         "description": f"Local sports team from {city} secures spot in national championship.",
         "url": "https://www.espn.com", "image": None,
         "published": "", "time_ago": "5h ago",
         "source_name": "ESPN", "source_url": "https://espn.com",
         "source_favicon": "https://www.google.com/s2/favicons?domain=espn.com&sz=32"},
    ]
    return {
        "city": city, "country": country, "language": "English",
        "articles": mock, "sources": [
            {"name": "BBC News",    "url": "https://bbc.com",       "favicon": "https://www.google.com/s2/favicons?domain=bbc.com&sz=32"},
            {"name": "Reuters",     "url": "https://reuters.com",   "favicon": "https://www.google.com/s2/favicons?domain=reuters.com&sz=32"},
            {"name": "Dawn",        "url": "https://dawn.com",      "favicon": "https://www.google.com/s2/favicons?domain=dawn.com&sz=32"},
            {"name": "Geo News",    "url": "https://geo.tv",        "favicon": "https://www.google.com/s2/favicons?domain=geo.tv&sz=32"},
            {"name": "Al Jazeera",  "url": "https://aljazeera.com", "favicon": "https://www.google.com/s2/favicons?domain=aljazeera.com&sz=32"},
            {"name": "TechCrunch",  "url": "https://techcrunch.com","favicon": "https://www.google.com/s2/favicons?domain=techcrunch.com&sz=32"},
        ],
        "total": len(mock),
        "is_mock": True,
    }
