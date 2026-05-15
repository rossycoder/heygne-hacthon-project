import { useState, useEffect } from 'react'
import './ScriptEditor.css'

const WORDS_PER_MINUTE = 130

export default function ScriptEditor({ script, onScriptChange, onConfirm, loading }) {
  const [text,    setText]    = useState(script || '')
  const [edited,  setEdited]  = useState(false)

  useEffect(() => { setText(script || '') }, [script])

  const wordCount = text.trim().split(/\s+/).filter(Boolean).length
  const estSecs   = Math.round((wordCount / WORDS_PER_MINUTE) * 60)
  const estMin    = Math.floor(estSecs / 60)
  const estSec    = estSecs % 60
  const duration  = estMin > 0 ? `~${estMin}m ${estSec}s` : `~${estSec}s`

  function handleChange(e) {
    setText(e.target.value)
    setEdited(e.target.value !== script)
    onScriptChange?.(e.target.value)
  }

  function handleReset() {
    setText(script)
    setEdited(false)
    onScriptChange?.(script)
  }

  return (
    <div className="script-editor">
      <div className="script-editor__header">
        <span className="script-editor__title">📝 Review & Edit Script</span>
        <div className="script-editor__meta">
          <span className="script-meta">{wordCount} words</span>
          <span className="script-meta script-meta--dur">{duration}</span>
          {edited && (
            <button type="button" className="btn-reset-script" onClick={handleReset}>
              ↩ Reset
            </button>
          )}
        </div>
      </div>

      <textarea
        className="script-editor__textarea"
        value={text}
        onChange={handleChange}
        rows={8}
        aria-label="Edit your broadcast script"
        placeholder="Your AI-generated script will appear here..."
      />

      {edited && (
        <p className="script-editor__hint">
          ✏️ Script edited — changes will be used in your video
        </p>
      )}

      <button
        type="button"
        className="btn-generate-video"
        onClick={() => onConfirm(text)}
        disabled={loading || !text.trim()}
      >
        {loading ? '⏳ Generating Video...' : '🎬 Generate Video with This Script'}
      </button>
    </div>
  )
}
