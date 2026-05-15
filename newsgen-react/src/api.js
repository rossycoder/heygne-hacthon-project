const BASE = import.meta.env.VITE_API_URL || '/api'

/**
 * Fetch real live news articles for a city (with source links).
 * Returns { city, country, articles, sources, total }
 */
export async function getLiveNews({ city, language = 'English' }) {
  const params = new URLSearchParams({ city, language })
  const res = await fetch(`${BASE}/live-news?${params}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Live news error ${res.status}`)
  }
  return res.json()
}

// ── Feature 1: Personalized News Feed ─────────────────────────────────────

/**
 * Get personalized news stories for a city + topics (no video generation).
 * Returns { city, language, stories: [...], count }
 */
export async function getNewsFeed({ city, language, topics }) {
  const res = await fetch(`${BASE}/news-feed`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ city, language, topics }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `News feed error ${res.status}`)
  }
  return res.json()
}

// ── Feature 2: AI News Summary ─────────────────────────────────────────────

/**
 * Summarize raw long-form news text into { headline, summary, voice_line }
 */
export async function summarizeNews({ rawText, language = 'English' }) {
  const res = await fetch(`${BASE}/summarize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ raw_text: rawText, language }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Summarize error ${res.status}`)
  }
  return res.json()
}

/**
 * Generate a quick punchy headline for a topic.
 * Returns { headline }
 */
export async function generateHeadline({ topic, city, language = 'English' }) {
  const res = await fetch(`${BASE}/headline`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, city, language }),
  })
  if (!res.ok) throw new Error(`Headline error ${res.status}`)
  return res.json()
}

// ── Full broadcast pipeline ────────────────────────────────────────────────

/**
 * Full pipeline: personalized news → AI script → HeyGen video.
 * Returns { script, video_url, news_stories, news_count, detected_language }
 */
export async function generateBroadcast({ name, city, language, topics, avatarId, voiceId, imageAssetId, anchorMode, burnCaptions, scriptOnly, customScript, sessionId }) {
  const res = await fetch(`${BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name, city, language, topics,
      avatar_id:      avatarId      || null,
      voice_id:       voiceId       || null,
      image_asset_id: imageAssetId  || null,
      anchor_mode:    anchorMode    || 'avatar',
      burn_captions:  burnCaptions  || false,
      script_only:    scriptOnly    || false,
      custom_script:  customScript  || null,
      session_id:     sessionId     || null,
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Server error ${res.status}`)
  }
  return res.json()
}

/**
 * Fetch all previously generated videos from HeyGen dashboard
 */
export async function getHeyGenVideos(limit = 20) {
  const res = await fetch(`${BASE}/heygen-videos?limit=${limit}`)
  if (!res.ok) throw new Error(`HeyGen videos error ${res.status}`)
  return res.json()
}

/**
 * Get broadcast history
 */
export async function getBroadcastHistory(limit = 20) {
  const res = await fetch(`${BASE}/broadcasts?limit=${limit}`)
  if (!res.ok) throw new Error(`History error ${res.status}`)
  return res.json()
}

/**
 * Get a specific broadcast by ID
 */
export async function getBroadcast(broadcastId) {
  const res = await fetch(`${BASE}/broadcasts/${broadcastId}`)
  if (!res.ok) throw new Error(`Broadcast error ${res.status}`)
  return res.json()
}

/**
 * Delete a broadcast from history
 */
export async function deleteBroadcast(broadcastId) {
  const res = await fetch(`${BASE}/broadcasts/${broadcastId}`, {
    method: 'DELETE'
  })
  if (!res.ok) throw new Error(`Delete error ${res.status}`)
  return res.json()
}

/**
 * Poll HeyGen video status.
 * Returns { video_id, status, video_url, error }
 * status: 'processing' | 'completed' | 'failed'
 */
export async function checkVideoStatus(videoId) {
  const res = await fetch(`${BASE}/video-status/${videoId}`)
  if (!res.ok) throw new Error(`Status check error ${res.status}`)
  return res.json()
}
