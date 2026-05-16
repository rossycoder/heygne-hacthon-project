"""
Feature 1: Personalized News Feed
- City + topics se news filter hoti hai
- Language auto-detect: Pakistan/Urdu cities → Urdu-relevant news, etc.
- GNews se real images bhi fetch hoti hain
"""
import json
import httpx
import os
from ai_client import ask_ai

GNEWS_KEY  = os.getenv("GNEWS_API_KEY", "")
GNEWS_BASE = "https://gnews.io/api/v4"

# Category → Unsplash fallback image (jab GNews image na ho)
CATEGORY_IMAGES = {
    "world":    "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&q=80",
    "tech":     "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80",
    "business": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80",
    "health":   "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800&q=80",
    "sports":   "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800&q=80",
    "science":  "https://images.unsplash.com/photo-1507413245164-6160d8298b31?w=800&q=80",
    "pakistan": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80",
    "default":  "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&q=80",
}

def _category_image(category: str) -> str:
    return CATEGORY_IMAGES.get(category.lower(), CATEGORY_IMAGES["default"])

# City → default language mapping
CITY_LANGUAGE_MAP = {
    "pakistan": "Urdu", "lahore": "Urdu", "karachi": "Urdu",
    "islamabad": "Urdu", "rawalpindi": "Urdu", "peshawar": "Urdu",
    "azad kashmir": "Urdu", "multan": "Urdu", "faisalabad": "Urdu",
    "india": "Hindi", "delhi": "Hindi", "mumbai": "Hindi",
    "saudi arabia": "Arabic", "dubai": "Arabic", "uae": "Arabic",
    "france": "French", "paris": "French",
    "spain": "Spanish", "mexico": "Spanish",
    "china": "Chinese", "beijing": "Chinese",
    "germany": "German", "berlin": "German",
    "brazil": "Portuguese", "portugal": "Portuguese",
    "russia": "Russian", "moscow": "Russian",
}

def detect_language_for_city(city: str, requested_language: str) -> str:
    """Return requested language, but if 'English' was default, auto-suggest from city."""
    city_lower = city.lower()
    for key, lang in CITY_LANGUAGE_MAP.items():
        if key in city_lower:
            # Only override if user didn't explicitly pick a non-English language
            if requested_language == "English":
                return lang
    return requested_language


async def fetch_personalized_news(
    city: str,
    language: str,
    topics: list[str] | None = None
) -> list[dict]:
    """
    Fetch top 5 news stories personalized by city + topics.
    Returns list of: { headline, summary, category, relevance_score, image_url }
    """
    topics_str = ", ".join(topics) if topics else "World, Technology, Health, Business"

    prompt = f"""You are a professional news curator for a personalized AI news channel.

User profile:
- City: {city}
- Preferred topics: {topics_str}
- Language: {language}

Task: Provide exactly 5 top news stories that are:
1. Highly relevant to someone in {city} based on their topic preferences
2. Real, credible, factual — no fake or speculative news
3. Diverse — no two stories from the same sub-topic
4. Prioritize local/regional news for {city} when available, then global

For each story provide:
- headline: punchy, under 12 words
- summary: 2-3 sentences, factual and clear
- category: one of [{topics_str}]
- relevance: "local" | "regional" | "global"
- search_query: 3-4 word English search query to find a news image for this story

Return ONLY a valid JSON array, no markdown, no extra text:
[
  {{"headline": "...", "summary": "...", "category": "...", "relevance": "...", "search_query": "..."}}
]"""

    text = ask_ai(prompt, max_tokens=1500)

    try:
        stories = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("[")
        end   = text.rfind("]") + 1
        if start != -1 and end > start:
            stories = json.loads(text[start:end])
        else:
            raise ValueError(f"AI returned invalid JSON: {text[:200]}")

    # Fetch real images from GNews for each story
    stories_with_images = await _attach_images(stories, city)
    return stories_with_images


async def _attach_images(stories: list[dict], city: str) -> list[dict]:
    """Fetch a news image for each story using GNews search."""
    if not GNEWS_KEY:
        # No API key — use Unsplash fallbacks
        for s in stories:
            s["image_url"] = _category_image(s.get("category", "default"))
        return stories

    async with httpx.AsyncClient(timeout=8.0) as client:
        for s in stories:
            query = s.get("search_query") or s.get("headline", "")
            try:
                resp = await client.get(
                    f"{GNEWS_BASE}/search",
                    params={"q": query, "lang": "en", "max": 3, "apikey": GNEWS_KEY},
                )
                if resp.status_code == 200:
                    articles = resp.json().get("articles", [])
                    # Find first article with an image
                    image_url = None
                    for art in articles:
                        if art.get("image"):
                            image_url = art["image"]
                            break
                    s["image_url"] = image_url or _category_image(s.get("category", "default"))
                else:
                    s["image_url"] = _category_image(s.get("category", "default"))
            except Exception:
                s["image_url"] = _category_image(s.get("category", "default"))

    return stories


async def fetch_and_filter_news(city: str, language: str) -> list[dict]:
    """Backward-compatible wrapper."""
    return await fetch_personalized_news(city, language)
