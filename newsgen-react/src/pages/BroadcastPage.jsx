import { useLocation, useNavigate } from 'react-router-dom'
import { useEffect, useState, useRef } from 'react'
import Navbar from '../components/Navbar'
import NewsTicker from '../components/NewsTicker'
import ShareBroadcast from '../components/ShareBroadcast'
import { checkVideoStatus, getBroadcastHistory } from '../api'
import './BroadcastPage.css'

const CATEGORY_COLORS = {
  WORLD: '#3b82f6', TECH: '#8b5cf6', BUSINESS: '#f59e0b',
  HEALTH: '#10b981', SPORTS: '#f97316', SCIENCE: '#06b6d4', PAKISTAN: '#22c55e',
}
const getCategoryColor = (cat = '') => CATEGORY_COLORS[cat.toUpperCase()] || '#888899'

export default function BroadcastPage() {
  const { state } = useLocation()
  const navigate  = useNavigate()

  const [videoUrl, setVideoUrl]     = useState(state?.data?.video_url || '')
  const [videoReady, setVideoReady] = useState(!!state?.data?.video_url)
  const [pollMsg, setPollMsg]       = useState('')
  const [pollError, setPollError]   = useState('')
  const pollRef = useRef(null)

  useEffect(() => {
    if (!state?.data) { navigate('/', { replace: true }); return }

    const videoId = state.data.video_id
    const isPending = state.data.status === 'pending' && videoId && !state.data.video_url

    if (!isPending) return

    // Start polling every 5 seconds
    setPollMsg('⏳ Your video is rendering on HeyGen...')
    let attempts = 0
    const MAX = 120  // 10 minutes max

    pollRef.current = setInterval(async () => {
      attempts++
      try {
        const result = await checkVideoStatus(videoId)

        if (result.status === 'completed' && result.video_url) {
          clearInterval(pollRef.current)
          setVideoUrl(result.video_url)
          setVideoReady(true)
          setPollMsg('✅ Your video is ready!')
          // Save to broadcast history
          try {
            await fetch('/api/broadcasts/save-video', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                name: state.name,
                city: state.city,
                language: state.language,
                script: state.data.script,
                video_url: result.video_url,
                news_stories: state.data.news_stories || [],
                video_id: videoId,
                avatar_id: null,
                topics: [],
              })
            })
          } catch (_) {}
        } else if (result.status === 'failed') {
          clearInterval(pollRef.current)
          setPollError(`Video generation failed: ${result.error || 'Unknown error'}`)
          setPollMsg('')
        } else {
          const mins = Math.floor((attempts * 5) / 60)
          const secs = (attempts * 5) % 60
          setPollMsg(`⏳ Rendering... ${mins > 0 ? `${mins}m ` : ''}${secs}s elapsed`)
        }
      } catch (err) {
        console.warn('Poll error:', err)
      }

      if (attempts >= MAX) {
        clearInterval(pollRef.current)
        setPollError('Video is taking too long. Check HeyGen dashboard.')
        setPollMsg('')
      }
    }, 5000)

    return () => clearInterval(pollRef.current)
  }, [state, navigate])

  if (!state?.data) return null

  const { data, name, city, language } = state
  const stories = data.news_stories || []
  const now     = new Date()
  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  const dateStr = now.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' })

  return (
    <div className="broadcast">
      <Navbar />
      <NewsTicker />

      <div className="broadcast__body">
        {/* Left: video player */}
        <section className="broadcast__player" aria-label="News broadcast video">
          <div className="player-wrap">
            {videoUrl ? (
              <video className="player-video" src={videoUrl}
                controls autoPlay playsInline
                aria-label={`Personalized news broadcast for ${name}`} />
            ) : (
              <div className="player-placeholder">
                <div className="player-placeholder__icon">
                  {pollError ? '❌' : '🎬'}
                </div>
                {pollError ? (
                  <p className="poll-error">{pollError}</p>
                ) : (
                  <>
                    <p className="poll-msg">{pollMsg || 'Preparing your broadcast...'}</p>
                    <div className="poll-spinner" aria-label="Loading" />
                    <p className="poll-hint">You can leave this page — come back to Broadcast History when ready.</p>
                  </>
                )}
              </div>
            )}
          </div>

          {videoReady && (
            <div className="video-ready-banner" role="status">
              🎉 Your video is ready!
            </div>
          )}

          <div className="player-meta">
            <div className="player-meta__name">
              <span className="live-badge">● LIVE</span>
              Broadcast for <strong>{name}</strong> · {city}
            </div>
            <div className="player-meta__date">{dateStr} · {timeStr}</div>
          </div>

          <div className="player-actions">
            {videoUrl && (
              <a className="btn-download"
                href={videoUrl}
                download={`newsgen-${name.toLowerCase().replace(/\s+/g, '-')}.mp4`}>
                ⬇ Download
              </a>
            )}
          </div>

          {videoUrl && (
            <ShareBroadcast videoUrl={videoUrl} name={name} city={city} language={language} />
          )}

          {data.script && (
            <details className="script-preview">
              <summary className="script-preview__toggle">📝 View Script</summary>
              <p className="script-preview__text">{data.script}</p>
            </details>
          )}
        </section>

        {/* Right: headlines */}
        <aside className="broadcast__headlines" aria-label="Today's top headlines">
          <h2 className="headlines__title">
            <span className="headlines__dot" aria-hidden="true" />
            Today's Top Stories
          </h2>

          {stories.length > 0 ? (
            <ol className="headlines__list">
              {stories.map((story, i) => (
                <li key={i} className="headline-card">
                  <div className="headline-card__top">
                    <span className="headline-card__cat"
                      style={{ background: getCategoryColor(story.category) }}>
                      {story.category || 'NEWS'}
                    </span>
                    <span className="headline-card__num">#{i + 1}</span>
                  </div>
                  <h3 className="headline-card__title">{story.headline}</h3>
                  <p className="headline-card__summary">{story.summary}</p>
                </li>
              ))}
            </ol>
          ) : (
            <div className="script-card">
              <h3 className="script-card__title">📝 Your Script</h3>
              <p className="script-card__text">{data.script}</p>
            </div>
          )}
        </aside>
      </div>

      <footer className="broadcast__stats" aria-label="Broadcast statistics">
        <div className="stat">
          <span className="stat__val">{stories.length || data.news_count || '—'}</span>
          <span className="stat__label">Stories</span>
        </div>
        <div className="stat-divider" />
        <div className="stat">
          <span className="stat__val">{language}</span>
          <span className="stat__label">Language</span>
        </div>
        <div className="stat-divider" />
        <div className="stat">
          <span className="stat__val">~90s</span>
          <span className="stat__label">Duration</span>
        </div>
        <div className="stat-divider" />
        <div className="stat">
          <span className="stat__val">{timeStr}</span>
          <span className="stat__label">Generated</span>
        </div>
        <button className="btn-new" onClick={() => navigate('/')}>
          + New Broadcast
        </button>
      </footer>
    </div>
  )
}
