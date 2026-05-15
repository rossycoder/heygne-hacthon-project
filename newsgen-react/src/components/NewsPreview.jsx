import { NewsFeedSkeleton } from './SkeletonLoader'
import './NewsPreview.css'

const RELEVANCE_ICONS = { local: '📍', regional: '🗺️', global: '🌐' }
const CATEGORY_COLORS = {
  WORLD: '#3b82f6', TECH: '#8b5cf6', PAKISTAN: '#22c55e',
  BUSINESS: '#f59e0b', SPORTS: '#f97316', HEALTH: '#10b981',
  SCIENCE: '#06b6d4',
}

export default function NewsPreview({ stories, city, language, loading = false, onClose }) {
  return (
    <div className="news-preview" aria-label="Personalized news preview">
      <div className="news-preview__header">
        <div className="news-preview__meta">
          <span className="news-preview__live" aria-label="Live">● LIVE</span>
          <span>
            {loading
              ? `Fetching stories for ${city}...`
              : <>Your feed for <strong>{city}</strong> · {language}</>
            }
          </span>
        </div>
        <button className="news-preview__close" onClick={onClose} aria-label="Close preview">✕</button>
      </div>

      {loading ? (
        <NewsFeedSkeleton count={5} />
      ) : (
        <>
          <ol className="news-preview__list">
            {stories.map((story, i) => {
              const cat   = (story.category || 'NEWS').toUpperCase()
              const color = CATEGORY_COLORS[cat] || '#888'
              const rel   = story.relevance || 'global'
              return (
                <li key={i} className="preview-card">
                  <div className="preview-card__top">
                    <span className="preview-card__cat" style={{ background: color }}>{cat}</span>
                    <span className="preview-card__rel" title={rel}>
                      {RELEVANCE_ICONS[rel]} {rel}
                    </span>
                  </div>
                  <h3 className="preview-card__headline">{story.headline}</h3>
                  <p className="preview-card__summary">{story.summary}</p>
                </li>
              )
            })}
          </ol>
          <p className="news-preview__note">
            ✅ {stories.length} stories ready · AI will summarize these into your broadcast script
          </p>
        </>
      )}
    </div>
  )
}
