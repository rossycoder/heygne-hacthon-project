# NewsGen AI — Your Personal AI News Anchor

> Type your name and city → get a broadcast-quality AI news video in your language in under 60 seconds.

Built for the **HeyGen Hackathon** using HeyGen Video Agent API + Claude/Groq AI + real-time news.

---

## What It Does

NewsGen AI fetches real breaking news, writes a personalized anchor script with AI, and delivers it as a professional news broadcast video using HeyGen avatars — in your language, with your name, for your city.

## HeyGen Features Used

| Feature | How Used |
|---|---|
| **Video Agent API** (`/v3/video-agents`) | Generates full multi-scene news broadcast with images, lower-thirds, captions, and background music |
| **Avatar Video** | AI anchor delivers personalized news |
| **Photo Avatar** | Users upload their own photo to become the anchor |
| **Voice Cloning** | Users clone their own voice for the broadcast |
| **Video Translation** | Broadcasts auto-translated into Urdu, Arabic, Hindi, French, Spanish |
| **Async Video Polling** | Real-time rendering status — "Your video is ready!" notification |

## Key Features

- 🌐 Real-time personalized news by city + topics
- 🎙️ AI-generated anchor script (Claude / Groq)
- 🎬 HeyGen Video Agent — news images as background, lower-third headlines, captions, background music
- 🌍 Multi-language: Urdu, Arabic, Hindi, French, Spanish, English
- 📺 Broadcast history — reuse videos to save API costs
- 🤳 Photo Avatar — become your own anchor
- 🎙️ Voice cloning — use your own voice
- 📱 Share on WhatsApp, LinkedIn, Twitter

## Tech Stack

- **Frontend:** React + Vite
- **Backend:** FastAPI (Python)
- **AI:** Groq (LLaMA) / Claude / Gemini
- **Video:** HeyGen Video Agent API
- **News:** GNews API + AI curation

## Run Locally

```bash
# 1. Copy env
cp .env.example .env
# Add: HEYGEN_API_KEY, GROQ_API_KEY or ANTHROPIC_API_KEY, GNEWS_API_KEY

# 2. Backend
cd backend
pip install -r ../requirements.txt
uvicorn app:app --reload --port 8000

# 3. Frontend
cd newsgen-react
npm install
npm run dev
```

## Demo

- YouTube: https://youtu.be/2HCzn1A8ir0
- GitHub: https://github.com/rossycoder/heygne-hacthon-project
