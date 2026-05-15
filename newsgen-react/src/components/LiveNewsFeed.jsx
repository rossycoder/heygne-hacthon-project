import { useState, useEffect } from 'react'
import { getLiveNews } from '../api'
import './LiveNewsFeed.css'

export default function LiveNewsFeed({ city, language }) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  useEffect(() => {
    if (!city?.trim()) return
    let cancelled = false

    async function load() {
      setLoading(true)
      setError('')
      setData(null)
      try {
        const result = await getLiveNews({ city: city.trim(), language })
        if (!cancelled) setData(result)
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    // Debounce — wait 600ms after city stops changing
    const t = setTimeout(load, 600)
    return () => { cancelled = true; clearTimeout(t) }
  }, [city, language])

  if (!city?.trim()) return null

  return (
    <div className="lnf" aria-label="Live news feed">
      <div className="lnf__header">
        <div className="lnf__title">
          <span className="lnf__dot" aria-hidden="true" />
          Live News
          {data && <span className="lnf__location"> — {data.city}, {data.country}</span>}
        </div>
        {data?.sources?.length > 0 && (
          <div className="lnf__sources" aria-label="News sources">
            {data.sources.map((s, i) => (
              <a key={i} href={s.url} target="_blank" rel="noopener noreferrer"
                 className="lnf__source-badge" title={s.name}>
                <img src={s.favicon} alt={s.name} width={14} height={14}
                     onError={e => { e.target.style.display = 'none' }} />
                {s.name}
              </a>
            ))}
          </div>
        )}
      </div>

      {/* Loading skeleton */}
      {loading && (
        <div className="lnf__list">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="lnf__skeleton">
              <div className="skeleton lnf__sk-img" />
              <div className="lnf__sk-body">
                <div className="skeleton lnf__sk-title" />
                <div className="skeleton lnf__sk-desc" />
                <div className="skeleton lnf__sk-meta" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <p className="lnf__error">⚠ {error}</p>
      )}

      {/* Articles */}
      {data && !loading && (
        <>
          {data.is_mock && (
            <div className="lnf__mock-notice">
              📌 Add <code>GNEWS_API_KEY</code> in <code>.env</code> for real live articles.
              Get free key at <a href="https://gnews.io" target="_blank" rel="noopener noreferrer">gnews.io</a>
            </div>
          )}
          <ol className="lnf__list">
            {data.articles.map((art, i) => (
              <li key={i} className="lnf__card" style={{ animationDelay: `${i * 0.05}s` }}>
                {art.image && (
                  <a href={art.url} target="_blank" rel="noopener noreferrer"
                     className="lnf__card-img-wrap" tabIndex={-1} aria-hidden="true">
                    <img src={art.image} alt="" className="lnf__card-img"
                         onError={e => { e.target.parentElement.style.display = 'none' }} />
                  </a>
                )}
                <div className="lnf__card-body">
                  <a href={art.url} target="_blank" rel="noopener noreferrer"
                     className="lnf__card-title">
                    {art.title}
                  </a>
                  {art.description && (
                    <p className="lnf__card-desc">{art.description}</p>
                  )}
                  <div className="lnf__card-meta">
                    <span className="lnf__card-source">
                      <img src={art.source_favicon} alt="" width={12} height={12}
                           onError={e => { e.target.style.display = 'none' }} />
                      {art.source_name}
                    </span>
                    {art.time_ago && (
                      <span className="lnf__card-time">{art.time_ago}</span>
                    )}
                    <a href={art.url} target="_blank" rel="noopener noreferrer"
                       className="lnf__card-read">
                      Read →
                    </a>
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  )
}
