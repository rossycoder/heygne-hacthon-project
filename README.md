---
title: NewsGen AI
emoji: 📡
colorFrom: red
colorTo: purple
sdk: docker
pinned: false
---

# NewsGen AI — Your Personal AI News Anchor

Personalized AI news broadcasts powered by HeyGen avatars, Claude/Groq AI, and real-time news.

## Features
- 🌐 Real-time personalized news by city
- 🎙️ AI-generated anchor scripts
- 🎬 HeyGen avatar video generation
- 🌍 Multi-language support
- 📱 Share on WhatsApp, LinkedIn, Twitter

## Setup
Copy `.env.example` to `.env` and add your API keys.

## Run Locally
```bash
# Backend
cd backend
pip install -r ../requirements.txt
uvicorn app:app --reload --port 8000

# Frontend
cd newsgen-react
npm install
npm run dev
```
