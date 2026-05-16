import httpx
import os
import asyncio

BASE = "https://api.heygen.com"


def _headers():
    return {
        "x-api-key": os.getenv("HEYGEN_API_KEY", ""),
        "Content-Type": "application/json",
    }


async def list_videos(limit: int = 20) -> list:
    """Fetch all previously generated videos from HeyGen dashboard"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{BASE}/v1/video.list",
            params={"limit": limit},
            headers=_headers(),
        )
        _raise_for_heygen_error(resp, "list videos")
        data = resp.json().get("data", {})
        videos = data.get("videos", [])
        
        result = []
        for v in videos:
            if v.get("status") == "completed" and v.get("video_url"):
                result.append({
                    "video_id":   v.get("id", ""),
                    "title":      v.get("title", "Untitled Broadcast"),
                    "video_url":  v.get("video_url", ""),
                    "thumbnail":  v.get("thumbnail_url", ""),
                    "duration":   v.get("duration", 0),
                    "created_at": v.get("created_at", ""),
                    "status":     v.get("status", ""),
                })
        return result


async def upload_asset(file_bytes, media_type, filename):
    # HeyGen uses a separate upload domain
    # Ensure filename extension matches the actual content type
    ext_map = {
        "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
        "audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/ogg": ".ogg",
        "audio/mp4": ".mp4", "audio/webm": ".webm",
    }
    ext = ext_map.get(media_type, "")
    if ext and not filename.lower().endswith(ext):
        # Strip old extension and add correct one
        base = filename.rsplit(".", 1)[0] if "." in filename else filename
        filename = f"{base}{ext}"

    upload_headers = {
        "x-api-key": os.getenv("HEYGEN_API_KEY", ""),
        "Content-Type": media_type,
        "X-File-Name": filename,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://upload.heygen.com/v1/asset",
            content=file_bytes,
            headers=upload_headers,
        )
        _raise_for_heygen_error(resp, "upload asset")
        data = resp.json()
        return data.get("data", data).get("asset_id", "")


async def list_voices():
    """Fetch all available voices with preview audio URLs."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{BASE}/v2/voices", headers=_headers())
        if resp.status_code != 200:
            return []
        voices_raw = resp.json().get("data", {}).get("voices", [])
        return [
            {
                "voice_id":    v.get("voice_id", ""),
                "name":        v.get("display_name", v.get("name", "")),
                "language":    v.get("language", ""),
                "gender":      v.get("gender", ""),
                "preview_url": v.get("preview_audio", v.get("preview_url", "")),
            }
            for v in voices_raw
        ]


async def list_avatars():
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            resp = await client.get(f"{BASE}/v2/avatars", headers=_headers())
        except Exception:
            return []
        if resp.status_code != 200:
            return []
        data = resp.json()
        avatars_raw = data.get("data", {}).get("avatars", [])

        # Fetch voices quickly with short timeout
        voices_map = {}
        try:
            vresp = await client.get(f"{BASE}/v2/voices", headers=_headers())
            if vresp.status_code == 200:
                for v in vresp.json().get("data", {}).get("voices", []):
                    vid = v.get("voice_id", "")
                    voices_map[vid] = {
                        "voice_id":    vid,
                        "name":        v.get("display_name", v.get("name", "")),
                        "language":    v.get("language", ""),
                        "preview_url": v.get("preview_audio", v.get("preview_url", "")),
                        "gender":      v.get("gender", ""),
                    }
        except Exception:
            pass

        result = []
        for a in avatars_raw:
            avatar_id  = a.get("avatar_id", "")
            voice_id   = a.get("voice_id", "")
            name       = a.get("avatar_name", a.get("name", ""))
            gender     = a.get("gender", "")
            if not gender:
                nl = name.lower()
                if any(w in nl for w in ["female","woman","girl","abigail","sofia","emily","sarah","anna","maria","priya","aisha","fatima","zara","layla"]):
                    gender = "female"
                elif any(w in nl for w in ["male","man","boy","aditya","james","john","david","michael","ali","omar","ahmed","rayan","carlos"]):
                    gender = "male"
            result.append({
                "avatar_id":   avatar_id,
                "name":        name,
                "preview_url": a.get("preview_image_url", a.get("preview_url", "")),
                "gender":      gender,
                "type":        a.get("type", "studio_avatar"),
                "voice_id":    voice_id,
                "voice":       voices_map.get(voice_id),
            })
        return result


async def create_avatar_video(script, language, avatar_id=None, voice_id=None, burn_captions=False, progress_callback=None):
    _avatar_id = avatar_id or os.getenv("HEYGEN_AVATAR_ID", "Abigail_standing_office_front")
    _voice_id  = voice_id  or ""

    # List of fallback avatars that support v3 API (prioritize female avatars for female voice)
    fallback_avatars = [
        "Abigail_standing_office_front",
        "Abigail_sitting_sofa_front",
        "Abigail_standing_office_side",
        "Aditya_public_4",
        "Aditya_public_1",
    ]

    payload = {
        "type": "avatar",
        "title": "NewsGen Broadcast",
        "avatar_id": _avatar_id,
        "script": script,
        "voice_id": _voice_id,
        "voice_settings": {"speed": 1.1},  # Slightly faster speech
        "resolution": "720p",  # Faster generation than 1080p
        "aspect_ratio": "16:9",
        "background": {"type": "color", "value": "#0d0d1a"},
    }
    if burn_captions:
        payload["caption"] = {"file_format": "srt", "style": "default"}

    if progress_callback:
        await progress_callback(5, "Submitting video request...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{BASE}/v3/videos", json=payload, headers=_headers())
        
        # If avatar doesn't support Avatar IV, try fallback avatars
        if resp.status_code in [400, 404]:
            try:
                body = resp.json()
                err = body.get("error", {})
                msg = err.get("message", "") or str(body)
            except Exception:
                msg = resp.text
            
            if "Avatar IV" in msg or "does not support" in msg or "not found" in msg.lower():
                print(f"Avatar {_avatar_id} doesn't support v3 API, trying fallbacks...")
                if progress_callback:
                    await progress_callback(10, "Trying alternative avatar...")
                for fallback in fallback_avatars:
                    if fallback == _avatar_id:
                        continue  # Skip if it's the same avatar we just tried
                    payload["avatar_id"] = fallback
                    resp = await client.post(f"{BASE}/v3/videos", json=payload, headers=_headers())
                    if resp.status_code == 200:
                        print(f"Successfully using fallback avatar: {fallback}")
                        break
                    await asyncio.sleep(0.5)
        
        _raise_for_heygen_error(resp, "create avatar video")
        video_id = resp.json()["data"]["video_id"]

    if progress_callback:
        await progress_callback(15, "Video queued, rendering...")

    return await _poll_video_status(video_id, progress_callback)


async def create_image_video(script, image_asset_id, voice_id=None, burn_captions=False, progress_callback=None):
    _voice_id = voice_id or ""

    if progress_callback:
        await progress_callback(5, "Preparing custom avatar...")

    payload = {
        "type": "image",
        "title": "NewsGen Custom Anchor",
        "image": {"type": "asset_id", "asset_id": image_asset_id},
        "script": script,
        "voice_id": _voice_id,
        "voice_settings": {"speed": 1.0},
        "resolution": "1080p",
        "aspect_ratio": "16:9",
        "expressiveness": "medium",
    }
    if burn_captions:
        payload["caption"] = {"file_format": "srt", "style": "default"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{BASE}/v3/videos", json=payload, headers=_headers())
        _raise_for_heygen_error(resp, "create image video")
        video_id = resp.json()["data"]["video_id"]

    if progress_callback:
        await progress_callback(15, "Video queued, rendering...")

    return await _poll_video_status(video_id, progress_callback)


async def get_video_status(video_id: str) -> dict:
    """Check HeyGen video status. Returns { status, video_url, error }"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{BASE}/v1/video_status.get",
            params={"video_id": video_id},
            headers=_headers(),
        )
        _raise_for_heygen_error(resp, "get video status")
        data = resp.json()["data"]
        return {
            "video_id":  video_id,
            "status":    data.get("status", "processing"),   # processing | completed | failed
            "video_url": data.get("video_url", ""),
            "error":     data.get("error", ""),
        }


async def submit_avatar_video(script, language, avatar_id=None, voice_id=None, burn_captions=False, news_stories=None) -> str:
    """Submit video to HeyGen v3 and return video_id immediately (no polling).
    Note: v3 does not support multi-scene. Single scene with burn_captions for subtitles.
    """
    _avatar_id = avatar_id or os.getenv("HEYGEN_AVATAR_ID", "Abigail_standing_office_front")
    _voice_id  = voice_id or ""

    payload = {
        "type": "avatar",
        "title": "NewsGen Broadcast",
        "avatar_id": _avatar_id,
        "script": script,
        "voice_id": _voice_id,
        "voice_settings": {"speed": 1.1},
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "background": {"type": "color", "value": "#0d0d1a"},
        "caption": {"file_format": "srt", "style": "default"},  # Always burn subtitles
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{BASE}/v3/videos", json=payload, headers=_headers())

        if resp.status_code in [400, 404]:
            try:
                msg = resp.json().get("error", {}).get("message", "") or resp.text
            except Exception:
                msg = resp.text

            needs_fallback = (
                "Avatar IV" in msg or
                "does not support" in msg or
                "not found" in msg.lower()
            )

            if needs_fallback:
                print(f"Avatar {_avatar_id} rejected by HeyGen ({msg}), trying default fallback...")
                fallback = os.getenv("HEYGEN_AVATAR_ID", "Abigail_standing_office_front")
                if fallback == _avatar_id:
                    fallback = "Abigail_standing_office_front"
                payload["avatar_id"] = fallback
                resp = await client.post(f"{BASE}/v3/videos", json=payload, headers=_headers())

        _raise_for_heygen_error(resp, f"submit avatar video (avatar_id={_avatar_id})")
        return resp.json()["data"]["video_id"]


async def submit_image_video(script, image_asset_id, voice_id=None, burn_captions=False) -> str:
    """Submit image-based video and return video_id immediately."""
    payload = {
        "type": "image",
        "title": "NewsGen Custom Anchor",
        "image": {"type": "asset_id", "asset_id": image_asset_id},
        "script": script,
        "voice_id": voice_id or "",
        "voice_settings": {"speed": 1.0},
        "resolution": "1080p",
        "aspect_ratio": "16:9",
        "expressiveness": "medium",
    }
    if burn_captions:
        payload["caption"] = {"file_format": "srt", "style": "default"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{BASE}/v3/videos", json=payload, headers=_headers())
        _raise_for_heygen_error(resp, "submit image video")
        return resp.json()["data"]["video_id"]


async def _poll_video_status(video_id, progress_callback=None, max_attempts=100):
    async with httpx.AsyncClient(timeout=15.0) as client:
        for attempt in range(max_attempts):
            # First few checks are faster, then slow down
            wait_time = 3 if attempt < 5 else 5
            await asyncio.sleep(wait_time)
            
            try:
                resp = await client.get(
                    f"{BASE}/v1/video_status.get",
                    params={"video_id": video_id},
                    headers=_headers(),
                )
                _raise_for_heygen_error(resp, "poll video status")
                data   = resp.json()["data"]
                status = data.get("status")
                
                # Calculate progress (15% to 100%)
                progress_pct = 15 + int((attempt / max_attempts) * 85)
                
                # Log progress
                if attempt % 5 == 0:
                    print(f"Video generation status: {status} (attempt {attempt + 1}/{max_attempts})")
                    if progress_callback:
                        await progress_callback(progress_pct, f"Rendering video... {progress_pct}%")
                
                if status == "completed":
                    print(f"Video completed successfully!")
                    if progress_callback:
                        await progress_callback(100, "Video ready!")
                    return {"video_id": video_id, "video_url": data["video_url"]}
                elif status == "failed":
                    raise RuntimeError(f"HeyGen video failed: {data.get('error', 'unknown')}")
                    
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                print(f"Network error on attempt {attempt + 1}: {e}")
                if progress_callback:
                    await progress_callback(15 + int((attempt / max_attempts) * 85), f"Connection issue, retrying... (attempt {attempt + 1})")
                
                # If we're near the end and still having network issues, give up
                if attempt > max_attempts * 0.8:
                    raise RuntimeError(f"Network connectivity issues prevented video completion. Please check your internet connection and try again.")
                
                # Wait longer on network errors
                await asyncio.sleep(10)
                continue
                
    raise TimeoutError(f"Video {video_id} timed out after {max_attempts} attempts")


async def clone_voice_from_asset(audio_asset_id, voice_name, language="en"):
    payload = {
        "audio": {"type": "asset_id", "asset_id": audio_asset_id},
        "voice_name": voice_name,
        "language": language,
        "remove_background_noise": True,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{BASE}/v3/voices/clone", json=payload, headers=_headers())
        _raise_for_heygen_error(resp, "clone voice")
        voice_clone_id = resp.json()["data"]["voice_clone_id"]

    return await _poll_voice_clone(voice_clone_id)


async def _poll_voice_clone(voice_clone_id, max_attempts=24):
    async with httpx.AsyncClient(timeout=15.0) as client:
        for _ in range(max_attempts):
            await asyncio.sleep(5)
            resp = await client.get(
                f"{BASE}/v3/voices/{voice_clone_id}",
                headers=_headers(),
            )
            _raise_for_heygen_error(resp, "poll voice clone")
            data   = resp.json()["data"]
            status = data.get("status")
            if status == "complete":
                return data.get("voice_id", voice_clone_id)
            elif status == "failed":
                raise RuntimeError("Voice clone failed")
    raise TimeoutError("Voice clone timed out")


async def create_lipsync(video_url, audio_url, mode="precision"):
    payload = {
        "video": {"type": "url", "url": video_url},
        "audio": {"type": "url", "url": audio_url},
        "mode": mode,
        "enable_speech_enhancement": True,
        "enable_dynamic_duration": True,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{BASE}/v3/lipsyncs", json=payload, headers=_headers())
        _raise_for_heygen_error(resp, "create lipsync")
        lipsync_id = resp.json()["data"]["lipsync_id"]
    return await _poll_lipsync_status(lipsync_id)


async def _poll_lipsync_status(lipsync_id, max_attempts=40):
    async with httpx.AsyncClient(timeout=15.0) as client:
        for _ in range(max_attempts):
            await asyncio.sleep(5)
            resp = await client.get(f"{BASE}/v3/lipsyncs/{lipsync_id}", headers=_headers())
            _raise_for_heygen_error(resp, "poll lipsync")
            data   = resp.json()["data"]
            status = data.get("status")
            if status == "completed":
                return {"lipsync_id": lipsync_id, "video_url": data["video_url"]}
            elif status == "failed":
                raise RuntimeError(f"Lipsync failed: {data.get('error', 'unknown')}")
    raise TimeoutError(f"Lipsync {lipsync_id} timed out")


async def translate_video(video_id, target_language):
    payload = {
        "video_id": video_id,
        "output_language": target_language,
        "translate_audio_only": False,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{BASE}/v2/video_translate", json=payload, headers=_headers())
        _raise_for_heygen_error(resp, "translate video")
        translation_id = resp.json()["data"]["translation_id"]
    return await _poll_translation_status(translation_id)


async def _poll_translation_status(translation_id, max_attempts=40):
    async with httpx.AsyncClient(timeout=15.0) as client:
        for _ in range(max_attempts):
            await asyncio.sleep(5)
            resp = await client.get(
                f"{BASE}/v2/video_translate/{translation_id}", headers=_headers()
            )
            _raise_for_heygen_error(resp, "poll translation")
            data   = resp.json()["data"]
            status = data.get("status")
            if status == "completed":
                return {"translation_id": translation_id, "video_url": data["video_url"]}
            elif status == "failed":
                raise RuntimeError(f"Translation failed: {data.get('error', 'unknown')}")
    raise TimeoutError(f"Translation {translation_id} timed out")


def _raise_for_heygen_error(resp, context):
    if resp.status_code == 200:
        return
    try:
        err  = resp.json().get("error", {})
        msg  = err.get("message", resp.text)
        code = err.get("code", str(resp.status_code))
    except Exception:
        msg  = resp.text
        code = str(resp.status_code)

    if resp.status_code == 401:
        raise PermissionError(f"HeyGen auth failed ({context}): check HEYGEN_API_KEY")
    elif resp.status_code == 429:
        raise RuntimeError(f"HeyGen rate limit exceeded ({context}). Retry later.")
    elif resp.status_code == 400:
        raise ValueError(f"HeyGen bad request ({context}): {msg} [code={code}]")
    else:
        raise RuntimeError(f"HeyGen error {resp.status_code} ({context}): {msg}")
