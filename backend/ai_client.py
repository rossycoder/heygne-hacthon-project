import os

PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()


def _call_claude(prompt: str, max_tokens: int = 1024) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def _call_gemini(prompt: str, max_tokens: int = 1024) -> str:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=max_tokens)
    )
    return response.text


def _call_openai(prompt: str, max_tokens: int = 1024) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content


def _call_groq(prompt: str, max_tokens: int = 1024) -> str:
    from openai import OpenAI
    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content


def ask_ai(prompt: str, max_tokens: int = 1024) -> str:
    if PROVIDER == "gemini":
        return _call_gemini(prompt, max_tokens)
    if PROVIDER == "openai":
        return _call_openai(prompt, max_tokens)
    if PROVIDER == "groq":
        return _call_groq(prompt, max_tokens)
    return _call_claude(prompt, max_tokens)
