from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
import os
import json
import asyncio

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

from news_fetcher import fetch_personalized_news, detect_language_for_city
from script_generator import generate_anchor_script, summarize_story, generate_headline_only
from heygen_client import (
    create_avatar_video, create_image_video,
    translate_video, upload_asset, list_avatars, list_voices,
    clone_voice_from_asset, list_videos,
)
from live_news import fetch_live_news
from broadcast_history import (
    save_broadcast, get_broadcast_history, get_broadcast_by_id, 
    delete_broadcast, find_similar_broadcast
)

app = FastAPI(title="NewsGen AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LANGUAGE_CODES = {
    "English": "en", "Urdu": "ur", "Arabic": "ar",
    "Spanish": "es", "French": "fr", "Hindi": "hi",
    "Chinese": "zh", "German": "de", "Portuguese": "pt", "Russian": "ru",
}

# Progress tracking
progress_store = {}

async def update_progress(session_id: str, stage: str, progress: int, message: str):
    """Update progress for a session"""
    progress_store[session_id] = {
        "stage": stage,
        "progress": progress,
        "message": message
    }
    await asyncio.sleep(0.1)  # Small delay to ensure updates are sent

# ── Models ─────────────────────────────────────────────────────────────────

class BroadcastRequest(BaseModel):
    name: str
    city: str
    language: str
    topics: Optional[list[str]] = None
    avatar_id:      Optional[str] = None
    voice_id:       Optional[str] = None
    image_asset_id: Optional[str] = None
    anchor_mode:    str = "avatar"
    burn_captions:  bool = False
    script_only:    bool = False
    custom_script:  Optional[str] = None
    session_id:     Optional[str] = None  # frontend-provided session ID for SSE progress

class BroadcastResponse(BaseModel):
    script: str
    video_url: str = ""
    news_stories: list[dict]
    news_count: int
    detected_language: str
    session_id: str = ""  # For progress tracking

class NewsFeedRequest(BaseModel):
    city: str
    language: str
    topics: Optional[list[str]] = None

class SummarizeRequest(BaseModel):
    raw_text: str
    language: str = "English"

class HeadlineRequest(BaseModel):
    topic: str
    city: str
    language: str = "English"

# ── Progress SSE endpoint ──────────────────────────────────────────────────

@app.get("/api/progress/{session_id}")
async def progress_stream(session_id: str):
    """Server-Sent Events endpoint for real-time progress updates"""
    async def event_generator():
        try:
            while True:
                if session_id in progress_store:
                    data = progress_store[session_id]
                    yield f"data: {json.dumps(data)}\n\n"
                    
                    # Clean up if completed
                    if data.get("progress", 0) >= 100:
                        await asyncio.sleep(1)
                        if session_id in progress_store:
                            del progress_store[session_id]
                        break
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            if session_id in progress_store:
                del progress_store[session_id]
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ── Broadcast pipeline ─────────────────────────────────────────────────────

@app.post("/api/generate", response_model=BroadcastResponse)
async def generate_broadcast(req: BroadcastRequest):
    """
    Full pipeline: news → AI script → HeyGen video.
    Supports three anchor modes:
      - avatar:  use a HeyGen avatar (default or user-selected)
      - photo:   animate user's uploaded photo
    
    Checks history first to avoid regenerating similar broadcasts and save API costs.
    """
    if not req.name.strip() or not req.city.strip():
        raise HTTPException(status_code=400, detail="Name and city are required")

    # Use frontend-provided session ID or generate one
    import uuid
    session_id = req.session_id if req.session_id else str(uuid.uuid4())
    
    await update_progress(session_id, "init", 5, "Starting broadcast generation...")

    language = detect_language_for_city(req.city, req.language)
    if language not in LANGUAGE_CODES:
        language = "English"
    lang_code = LANGUAGE_CODES[language]

    # Check if we have a similar broadcast in history to save API costs
    if not req.script_only and not req.custom_script:
        await update_progress(session_id, "checking", 10, "Checking for existing broadcasts...")
        similar_broadcast = find_similar_broadcast(req.name, req.city, language, req.topics)
        
        if similar_broadcast:
            await update_progress(session_id, "found", 100, "Found existing broadcast!")
            return BroadcastResponse(
                script=similar_broadcast["script"],
                video_url=similar_broadcast["video_url"],
                news_stories=similar_broadcast["news_stories"],
                news_count=similar_broadcast["news_count"],
                detected_language=language,
                session_id=session_id,
            )

    # Step 1: Personalized news
    await update_progress(session_id, "news", 15, "Fetching personalized news...")
    news_stories = await fetch_personalized_news(req.city, language, req.topics)
    
    await update_progress(session_id, "news", 30, f"Found {len(news_stories)} news stories")

    # Step 2: AI script (or use custom script if provided)
    await update_progress(session_id, "script", 40, "Generating anchor script...")
    if req.custom_script and req.custom_script.strip():
        script = req.custom_script.strip()
    else:
        script = await generate_anchor_script(req.name, req.city, language, news_stories)

    await update_progress(session_id, "script", 50, "Script ready")

    # Script-only mode — return without generating video
    if req.script_only:
        await update_progress(session_id, "complete", 100, "Script generated")
        return BroadcastResponse(
            script=script, video_url="",
            news_stories=news_stories, news_count=len(news_stories),
            detected_language=language,
            session_id=session_id,
        )

    # Step 3: Generate video
    await update_progress(session_id, "video", 55, "Creating video with AI avatar...")
    
    try:
        if req.anchor_mode == "photo" and req.image_asset_id:
            video_result = await create_image_video(
                script=script,
                image_asset_id=req.image_asset_id,
                voice_id=req.voice_id,
                burn_captions=req.burn_captions,
                progress_callback=lambda p, m: asyncio.create_task(update_progress(session_id, "video", 55 + int(p * 0.35), m))
            )
        else:
            # Use user-selected avatar — only block known-broken IDs
            _INVALID_AVATARS = {"Anna_public_3", "Daisy-inskirt-20220818", "Tyler-incasualsuit-20220721",
                                "Eric_public_pro1", "Susan_public_2_20240328", "Justin_public_pro2_20230714",
                                # Our fake mock avatar IDs
                                "Sarah_professional", "Emma_business", "Sophia_casual",
                                "Michael_suit", "James_blue", "David_casual",
                                "Alex_formal", "Ryan_professional", "Priya_anchor", "Ahmed_news"}
            safe_avatar_id = req.avatar_id if req.avatar_id and req.avatar_id not in _INVALID_AVATARS else None
            video_result = await create_avatar_video(
                script=script,
                language=language,
                avatar_id=safe_avatar_id,
                voice_id=req.voice_id,
                burn_captions=req.burn_captions,
                progress_callback=lambda p, m: asyncio.create_task(update_progress(session_id, "video", 55 + int(p * 0.35), m))
            )

        await update_progress(session_id, "video", 90, "Video generated successfully")

        # Step 4: Translate if non-English (skip if network unavailable)
        final_url = video_result["video_url"]
        if lang_code != "en":
            try:
                await update_progress(session_id, "translate", 92, "Translating video...")
                translated = await translate_video(video_result["video_id"], lang_code)
                final_url  = translated["video_url"]
                await update_progress(session_id, "translate", 98, "Translation complete")
            except Exception as te:
                print(f"Translation skipped (network issue): {te}")
                await update_progress(session_id, "translate", 98, "Translation skipped, using original video")

        # Save to history immediately after video is ready
        await update_progress(session_id, "saving", 99, "Saving broadcast...")
        try:
            save_broadcast(
                name=req.name, city=req.city, language=language,
                script=script, video_url=final_url,
                news_stories=news_stories, avatar_id=req.avatar_id, topics=req.topics
            )
        except Exception as se:
            print(f"History save failed (non-critical): {se}")

        await update_progress(session_id, "complete", 100, "Broadcast ready!")

        return BroadcastResponse(
            script=script,
            video_url=final_url,
            news_stories=news_stories,
            news_count=len(news_stories),
            detected_language=language,
            session_id=session_id,
        )
        
    except Exception as e:
        error_msg = str(e)
        if "getaddrinfo failed" in error_msg or "ConnectError" in error_msg:
            error_msg = "Network connection issue. Please check your internet connection and try again."
        elif "timeout" in error_msg.lower():
            error_msg = "Video generation timed out. Please try again with a shorter script."
        
        await update_progress(session_id, "error", 100, f"Error: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

# ── Avatar list ────────────────────────────────────────────────────────────

@app.get("/api/avatars")
async def get_avatars():
    """Return HeyGen avatars. Uses mock data if API key not set or unreachable."""
    default_id    = os.getenv("HEYGEN_AVATAR_ID", "")
    default_voice = os.getenv("HEYGEN_VOICE_ID", "")

    # Try real API only if explicitly enabled (disabled by default for speed)
    if os.getenv("HEYGEN_USE_LIVE_AVATARS", "true").lower() == "true":
        try:
            import asyncio
            avatars = await asyncio.wait_for(list_avatars(), timeout=10.0)
            if avatars and len(avatars) > 0:
                return {"avatars": avatars, "count": len(avatars)}
        except Exception as e:
            # Silently fall through to mock avatars
            pass

    # Always return mock avatars so UI never shows "No avatars found"
    mock = []
    if default_id:
        mock.append({
            "avatar_id": default_id, "name": "My Anchor (Default)",
            "preview_url": "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face", 
            "gender": "female", "type": "studio_avatar",
            "voice_id": default_voice, "voice": None
        })
    mock += [
        {"avatar_id": "Abigail_expressive_2024112501", "name": "Abigail", "gender": "female",
         "preview_url": "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face", 
         "type": "studio_avatar", "voice_id": "", "voice": None},
        {"avatar_id": "Abigail_standing_office_front", "name": "Abigail Office", "gender": "female",
         "preview_url": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face", 
         "type": "studio_avatar", "voice_id": "", "voice": None},
        {"avatar_id": "Abigail_sitting_sofa_front", "name": "Abigail Sofa", "gender": "female",
         "preview_url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&h=150&fit=crop&crop=face", 
         "type": "studio_avatar", "voice_id": "", "voice": None},
        {"avatar_id": "Aditya_public_4", "name": "Aditya Brown", "gender": "male",
         "preview_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face", 
         "type": "studio_avatar", "voice_id": "", "voice": None},
        {"avatar_id": "Aditya_public_1", "name": "Aditya Blue", "gender": "male",
         "preview_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face", 
         "type": "studio_avatar", "voice_id": "", "voice": None},
        {"avatar_id": "Aditya_public_2", "name": "Aditya T-shirt", "gender": "male",
         "preview_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&h=150&fit=crop&crop=face", 
         "type": "studio_avatar", "voice_id": "", "voice": None},
        {"avatar_id": "Aditya_public_5", "name": "Aditya Shirt", "gender": "male",
         "preview_url": "https://images.unsplash.com/photo-1519345182560-3f2917c472ef?w=150&h=150&fit=crop&crop=face", 
         "type": "studio_avatar", "voice_id": "", "voice": None},
        {"avatar_id": "Aditya_public_3", "name": "Aditya Beige", "gender": "male",
         "preview_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150&h=150&fit=crop&crop=face", 
         "type": "studio_avatar", "voice_id": "", "voice": None},
    ]
    return {"avatars": mock, "count": len(mock), "is_mock": True}


@app.get("/api/voices")
async def get_voices():
    """Return all HeyGen voices with preview audio URLs."""
    try:
        voices = await list_voices()
        return {"voices": voices, "count": len(voices)}
    except Exception as e:
        return {"voices": [], "count": 0, "error": str(e)}

# ── File upload: photo ─────────────────────────────────────────────────────

@app.post("/api/upload/photo")
async def upload_photo(file: UploadFile = File(...)):
    """
    Upload a user photo to HeyGen asset storage.
    Returns { asset_id } to use in /api/generate with anchor_mode='photo'.
    Accepts: image/jpeg, image/png, image/webp (max 10MB)
    """
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Image must be JPEG, PNG or WebP. Got: {file.content_type}")

    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be under 10MB")

    asset_id = await upload_asset(data, file.content_type, file.filename or "photo.jpg")
    return {"asset_id": asset_id, "filename": file.filename}

# ── File upload: voice ─────────────────────────────────────────────────────

@app.post("/api/upload/voice")
async def upload_voice(
    file: UploadFile = File(...),
    voice_name: str = Form(default="My Voice"),
    language: str   = Form(default="en"),
):
    """
    Upload a voice recording → clone it via HeyGen.
    Returns { voice_id } to use in /api/generate.
    Accepts: audio/mpeg (mp3), audio/wav, audio/ogg (min 10s, max 5MB)
    """
    allowed = {"audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4", "audio/webm"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Audio must be MP3, WAV or OGG. Got: {file.content_type}")

    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio must be under 5MB")

    # Upload audio file first
    asset_id = await upload_asset(data, file.content_type, file.filename or "voice.mp3")

    # Clone the voice — returns voice_id
    voice_id = await clone_voice_from_asset(asset_id, voice_name, language)
    return {"voice_id": voice_id, "voice_name": voice_name}

# ── Other endpoints ────────────────────────────────────────────────────────

@app.post("/api/news-feed")
async def get_news_feed(req: NewsFeedRequest):
    if not req.city.strip():
        raise HTTPException(status_code=400, detail="City is required")
    language = detect_language_for_city(req.city, req.language)
    stories  = await fetch_personalized_news(req.city, language, req.topics)
    return {"city": req.city, "language": language, "topics": req.topics,
            "stories": stories, "count": len(stories)}

@app.post("/api/summarize")
async def summarize_news(req: SummarizeRequest):
    if not req.raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text is required")
    return await summarize_story(req.raw_text, req.language)

@app.post("/api/headline")
async def quick_headline(req: HeadlineRequest):
    headline = await generate_headline_only(req.topic, req.city, req.language)
    return {"headline": headline}

@app.get("/api/live-news")
async def live_news(
    city: str = Query(...),
    language: str = Query("English"),
):
    if not city.strip():
        raise HTTPException(status_code=400, detail="City is required")
    return await fetch_live_news(city.strip(), language)

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "ai_provider": os.getenv("AI_PROVIDER", "claude"),
        "features": ["personalized-news", "ai-summary", "custom-voice", "custom-photo", "avatar-select"],
    }

# ── Broadcast History ──────────────────────────────────────────────────────

@app.get("/api/heygen-videos")
async def get_heygen_videos(limit: int = 20):
    """Fetch all previously generated videos directly from HeyGen dashboard"""
    try:
        videos = await list_videos(limit)
        return {"videos": videos, "count": len(videos)}
    except Exception as e:
        return {"videos": [], "count": 0, "error": str(e)}


@app.get("/api/broadcasts")
async def get_broadcasts(limit: int = 20):
    """Get broadcast history to show previously generated videos"""
    history = get_broadcast_history(limit)
    return {"broadcasts": history, "count": len(history)}

@app.get("/api/broadcasts/{broadcast_id}")
async def get_broadcast(broadcast_id: str):
    """Get a specific broadcast by ID"""
    broadcast = get_broadcast_by_id(broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    return broadcast

@app.delete("/api/broadcasts/{broadcast_id}")
async def delete_broadcast_endpoint(broadcast_id: str):
    """Delete a broadcast from history"""
    success = delete_broadcast(broadcast_id)
    if not success:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    return {"message": "Broadcast deleted successfully"}
