"""
Feature 1: Personalized News Feed
- City + topics se news filter hoti hai
- Language auto-detect: Pakistan/Urdu cities → Urdu-relevant news, etc.
"""
import json
from ai_client import ask_ai

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
    Returns list of: { headline, summary, category, relevance_score }
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

Return ONLY a valid JSON array, no markdown, no extra text:
[
  {{"headline": "...", "summary": "...", "category": "...", "relevance": "..."}}
]"""

    text = ask_ai(prompt, max_tokens=1500)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("[")
        end   = text.rfind("]") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
        raise ValueError(f"AI returned invalid JSON: {text[:200]}")


async def fetch_and_filter_news(city: str, language: str) -> list[dict]:
    """Backward-compatible wrapper."""
    return await fetch_personalized_news(city, language)
