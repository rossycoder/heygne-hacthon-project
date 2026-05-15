"""
Feature 2: AI News Summary Pipeline
- Long news → short anchor script
- Headline generator
- Voice-ready script (natural speech patterns, no symbols)
"""
from ai_client import ask_ai


async def summarize_story(raw_text: str, language: str = "English") -> dict:
    """
    Compress a long news article into:
    - headline (punchy, under 12 words)
    - summary (2-3 sentences)
    - voice_line (1 sentence, anchor-ready)
    """
    prompt = f"""You are an expert news editor. Compress this news into broadcast format.

Raw news:
{raw_text}

Output language: {language}

Return ONLY valid JSON (no markdown):
{{
  "headline": "under 12 words, punchy",
  "summary": "2-3 factual sentences",
  "voice_line": "1 natural sentence an anchor would say on air"
}}"""

    text = ask_ai(prompt, max_tokens=512)
    import json
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end   = text.rfind("}") + 1
        return json.loads(text[start:end])


async def generate_anchor_script(
    name: str,
    city: str,
    language: str,
    news_stories: list[dict]
) -> str:
    """
    Feature 2 core: Generate a voice-ready personalized anchor script.
    - Natural speech (no bullet points, no symbols, no markdown)
    - Smooth transitions between stories
    - Personalized open + close
    """
    # Build story block with relevance context
    stories_block = ""
    for i, s in enumerate(news_stories, 1):
        relevance = s.get("relevance", "global")
        tag = f"[{s.get('category','NEWS').upper()} · {relevance.upper()}]"
        stories_block += f"\nStory {i} {tag}\nHeadline: {s['headline']}\nDetails: {s['summary']}\n"

    prompt = f"""You are a professional TV news anchor scriptwriter.

Write a personalized broadcast script for:
- Viewer name: {name}
- City: {city}
- Language: {language}

News stories to cover:
{stories_block}

Script rules:
1. Open: warm greeting using "{name}" and "{city}" — feel personal, not generic
2. Cover all {len(news_stories)} stories with smooth anchor transitions
   ("Meanwhile...", "Turning to...", "In other news...", "Closer to home...")
3. For LOCAL/REGIONAL stories, add a line connecting it to {city}
4. Voice-ready: no bullet points, no symbols, no markdown, no stage directions
5. Natural spoken rhythm — short sentences, easy to read aloud
6. Total length: ~200 words (under 90 seconds when spoken)
7. Close: warm sign-off mentioning "{name}" by name
8. Write ENTIRELY in {language}

Output ONLY the script text, nothing else."""

    return ask_ai(prompt, max_tokens=1200).strip()


async def generate_headline_only(topic: str, city: str, language: str = "English") -> str:
    """Quick headline generator for a given topic."""
    prompt = f"""Generate a punchy news headline (under 12 words) about "{topic}" 
relevant to {city}. Write in {language}. Return ONLY the headline, nothing else."""
    return ask_ai(prompt, max_tokens=64).strip().strip('"')
