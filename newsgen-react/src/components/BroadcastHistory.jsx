import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getBroadcastHistory, deleteBroadcast } from '../api'
import './BroadcastHistory.css'

const LS_KEY = 'newsgen_history'

export default function BroadcastHistory() {
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadHistory() }, [])

  async function loadHistory() {
    setLoading(true)
    try {
      const result = await getBroadcastHistory(20)
      let items = result.broadcasts || []

      // Fallback: migrate old localStorage entries if backend is empty
      if (items.length === 0) {
        const local = JSON.parse(localStorage.getItem(LS_KEY) || '[]')
        items = local.map(e => ({
          id: e.id || String(e.timestamp),
          name: e.name, city: e.city, language: e.language,
          script: e.script || '',
          video_url: e.videoUrl || e.video_url || '',
          news_stories: [], news_count: e.newsCount || 0,
          topics: [], created_at: e.timestamp || new Date().toISOString(),
          _local: true,
        }))
      }
      setHistory(items)
    } catch (_) {
      try {
        const local = JSON.parse(localStorage.getItem(LS_KEY) || '[]')
        setHistory(local.map(e => ({
          id: e.id || String(e.timestamp),
          name: e.name, city: e.city, language: e.language,
          script: e.script || '',
          video_url: e.videoUrl || e.video_url || '',
          news_stories: [], news_count: e.newsCount || 0,
          topics: [], created_at: e.timestamp || new Date().toISOString(),
          _local: true,
        })))
      } catch (_) {}
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(entry) {
    if (!confirm('Delete this broadcast?')) return
    try {
      if (!entry._local) {
        await deleteBroadcast(entry.id)
      } else {
        const local = JSON.parse(localStorage.getItem(LS_KEY) || '[]')
        localStorage.setItem(LS_KEY, JSON.stringify(
          local.filter(e => String(e.id) !== String(entry.id))
        ))
      }
      setHistory(prev => prev.filter(b => b.id !== entry.id))
    } catch (_) {
      alert('Failed to delete')
    }
  }

  function timeAgo(iso) {
    if (!iso) return ''
    const diff = Date.now() - new Date(iso).getTime()
    const m = Math.floor(diff / 60000)
    if (m < 1)  return 'just now'
    if (m < 60) return `${m}m ago`
    const h = Math.floor(m / 60)
    if (h < 24) return `${h}h ago`
    return `${Math.floor(h / 24)}d ago`
  }

  function watch(entry) {
    navigate('/broadcast', {
      state: {
        data: {
          video_url: entry.video_url,
          script: entry.script,
          news_stories: entry.news_stories || [],
          news_count: entry.news_count || 0,
        },
        name: entry.name,
        city: entry.city,
        language: entry.language,
      }
    })
  }

  if (loading) {
    return (
      <div className="bh">
        <div className="bh__header">
          <span className="bh__title">🕐 Recent Broadcasts</span>
        </div>
        <div className="bh__loading">Loading...</div>
      </div>
    )
  }

  if (!history.length) {
    return (
      <div className="bh">
        <div className="bh__header">
          <span className="bh__title">🕐 Recent Broadcasts</span>
        </div>
        <div className="bh__empty">
          <p>No broadcasts yet. Generate your first one!</p>
          <p><small>💡 Saved broadcasts avoid re-generating and save API costs</small></p>
        </div>
      </div>
    )
  }

  return (
    <div className="bh" aria-label="Broadcast history">
      <div className="bh__header">
        <span className="bh__title">🕐 Recent Broadcasts ({history.length})</span>
        <button type="button" className="bh__refresh" onClick={loadHistory}>↻ Refresh</button>
      </div>

      <div className="bh__list">
        {history.map(entry => (
          <div key={entry.id} className="bh__card">
            <div className="bh__card-info">
              <span className="bh__card-name">{entry.name}</span>
              <span className="bh__card-meta">{entry.city} · {entry.language}</span>
              <span className="bh__card-time">{timeAgo(entry.created_at)}</span>
              {entry.news_count > 0 && (
                <span className="bh__card-count">{entry.news_count} stories</span>
              )}
            </div>
            <div className="bh__card-actions">
              <button type="button" className="bh__rewatch" onClick={() => watch(entry)}>
                ▶ Watch
              </button>
              <button type="button" className="bh__delete" onClick={() => handleDelete(entry)}>
                🗑
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="bh__footer">
        <small>💰 Reusing broadcasts saves HeyGen API costs</small>
      </div>
    </div>
  )
}
