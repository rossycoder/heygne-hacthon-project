import { useLocation, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import Navbar from '../components/Navbar'
import NewsTicker from '../components/NewsTicker'
import ShareBroadcast from '../components/ShareBroadcast'
import './BroadcastPage.css'

const CATEGORY_COLORS = {
  WORLD: '#3b82f6', TECH: '#8b5cf6', BUSINESS: '#f59e0b',
  HEALTH: '#10b981', SPORTS: '#f97316', SCIENCE: '#06b6d4', PAKISTAN: '#22c55e',
}
const getCategoryColor = (cat = '') => CATEGORY_COLORS[cat.toUpperCase()] || '#888899'

export default function BroadcastPage() {
  const { state } = useLocation()
  const navigate  = useNavigate()

  useEffect(() => {
    if (!state?.data) navigate('/', { replace: true })
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
            {data.video_url ? (
              <video className="player-video" src={data.video_url}
                controls autoPlay playsInline
                aria-label={`Personalized news broadcast for ${name}`} />
            ) : (
              <div className="player-placeholder">
                <div className="player-placeholder__icon">📺</div>
                <p>Your broadcast is ready</p>
              </div>
            )}
          </div>

          <div className="player-meta">
            <div className="player-meta__name">
              <span className="live-badge">● LIVE</span>
              Broadcast for <strong>{name}</strong> · {city}
            </div>
            <div className="player-meta__date">{dateStr} · {timeStr}</div>
          </div>

          {/* Action buttons */}
          <div className="player-actions">
            {data.video_url && (
              <a className="btn-download"
                href={data.video_url}
                download={`newsgen-${name.toLowerCase().replace(/\s+/g, '-')}.mp4`}>
                ⬇ Download
              </a>
            )}
          </div>

          {/* Share bar */}
          {data.video_url && (
            <ShareBroadcast
              videoUrl={data.video_url}
              name={name}
              city={city}
              language={language}
            />
          )}

          {/* Script preview */}
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

      {/* Stats bar */}
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
