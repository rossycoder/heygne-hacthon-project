import { useEffect, useState } from 'react'
import './LoadingScreen.css'

export default function LoadingScreen({ name, sessionId }) {
  const [dots, setDots] = useState('')
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState('Starting...')
  const [stage, setStage] = useState('init')

  useEffect(() => {
    const t = setInterval(() => setDots(d => d.length >= 3 ? '' : d + '.'), 500)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    if (!sessionId) return

    const eventSource = new EventSource(`http://localhost:8000/api/progress/${sessionId}`)
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setProgress(data.progress || 0)
        setMessage(data.message || '')
        setStage(data.stage || 'init')
      } catch (err) {
        console.error('Error parsing progress:', err)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
    }

    return () => eventSource.close()
  }, [sessionId])

  const STAGE_ICONS = {
    init: '🚀',
    news: '🌐',
    script: '✍️',
    video: '🎬',
    translate: '🌍',
    complete: '✅'
  }

  return (
    <div className="loading-overlay" role="status" aria-live="polite">
      <div className="loading-card">
        <div className="loading-logo">📡 NewsGen AI</div>

        <p className="loading-greeting">
          Good morning <strong>{name}</strong>, your broadcast is almost ready{dots}
        </p>

        <div className="loading-current-step">
          <span className="step-icon-large">{STAGE_ICONS[stage] || '⏳'}</span>
          <p className="step-message">{message}</p>
        </div>

        <div className="loading-progress" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
          <div className="loading-progress__bar" style={{ width: `${progress}%` }} />
        </div>
        <p className="loading-progress__label">{progress}% complete</p>
      </div>
    </div>
  )
}
