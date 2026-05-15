import { useState, useRef, useEffect } from 'react'
import './AnchorSel.css'

// Direct backend URL for file uploads (multipart doesn't work through Vercel proxy)
const API_BASE = import.meta.env.VITE_API_URL || '/api'

const TABS = [
  { id: 'avatar', label: '🎭 HeyGen Avatar' },
  { id: 'photo',  label: '🤳 My Photo'      },
  { id: 'voice',  label: '🎙️ My Voice'      },
]

const GENDER_FILTERS = [
  { id: 'all',    label: 'All'       },
  { id: 'female', label: '👩 Female' },
  { id: 'male',   label: '👨 Male'   },
]

export default function AnchorSelector({ onAnchorChange }) {
  const [tab,            setTab]            = useState('avatar')
  const [avatars,        setAvatars]        = useState([])
  const [voices,         setVoices]         = useState([])
  const [avatarLoad,     setAvatarLoad]     = useState(false)
  const [avatarsLoaded,  setAvatarsLoaded]  = useState(false)
  const [selectedAvatar, setSelectedAvatar] = useState(null)
  const [selectedVoice,  setSelectedVoice]  = useState(null)
  const [genderFilter,   setGenderFilter]   = useState('all')
  const [playingVoice,   setPlayingVoice]   = useState(null)
  const [burnCaptions,   setBurnCaptions]   = useState(false)
  const [showVoicePicker, setShowVoicePicker] = useState(false)
  const audioRef = useRef(null)

  // Photo
  const [photoPreview,   setPhotoPreview]   = useState(null)
  const [photoAssetId,   setPhotoAssetId]   = useState(null)
  const [photoUploading, setPhotoUploading] = useState(false)
  const [photoError,     setPhotoError]     = useState('')
  const photoInputRef = useRef()

  // Voice clone
  const [voiceName,      setVoiceName]      = useState('My Voice')
  const [voiceId,        setVoiceId]        = useState(null)
  const [voiceUploading, setVoiceUploading] = useState(false)
  const [voiceError,     setVoiceError]     = useState('')
  const [recording,      setRecording]      = useState(false)
  const [mediaRec,       setMediaRec]       = useState(null)
  const [recordedBlob,   setRecordedBlob]   = useState(null)
  const [recordSecs,     setRecordSecs]     = useState(0)
  const voiceInputRef = useRef()
  const timerRef = useRef(null)

  // Load avatars — deduplicate by avatar_id
  useEffect(() => {
    if (tab !== 'avatar' || avatarsLoaded) return
    setAvatarLoad(true)
    fetch(`${API_BASE}/avatars`)
      .then(r => r.json())
      .then(d => {
        const raw = d.avatars || []
        // Deduplicate by avatar_id
        const seen = new Set()
        const unique = raw.filter(a => {
          if (seen.has(a.avatar_id)) return false
          seen.add(a.avatar_id)
          return true
        })
        setAvatars(unique)
        setAvatarsLoaded(true)
        setAvatarLoad(false)
      })
      .catch(() => { setAvatarsLoaded(true); setAvatarLoad(false) })
  }, [tab, avatarsLoaded])

  // Load voices for voice picker
  useEffect(() => {
    if (!showVoicePicker || voices.length > 0) return
    fetch(`${API_BASE}/voices`)
      .then(r => r.json())
      .then(d => setVoices(d.voices || []))
      .catch(() => {})
  }, [showVoicePicker])

  // Notify parent on any change
  useEffect(() => {
    const activeVoiceId = selectedVoice?.voice_id || selectedAvatar?.voice_id || null
    if (tab === 'avatar') {
      onAnchorChange({
        mode: 'avatar',
        avatarId:     selectedAvatar?.avatar_id || null,
        voiceId:      activeVoiceId,
        imageAssetId: null,
        burnCaptions,
      })
    } else if (tab === 'photo') {
      onAnchorChange({ mode: 'photo', avatarId: null, voiceId: voiceId || activeVoiceId, imageAssetId: photoAssetId, burnCaptions })
    } else {
      onAnchorChange({ mode: 'avatar', avatarId: null, voiceId, imageAssetId: null, burnCaptions })
    }
  }, [tab, selectedAvatar, selectedVoice, voiceId, photoAssetId, burnCaptions])

  const filtered = avatars.filter(a => genderFilter === 'all' || a.gender === genderFilter)

  function playAudio(url, id) {
    if (playingVoice === id) {
      audioRef.current?.pause()
      setPlayingVoice(null)
      return
    }
    audioRef.current?.pause()
    const audio = new Audio(url)
    audioRef.current = audio
    audio.play().catch(() => {})
    audio.onended = () => setPlayingVoice(null)
    setPlayingVoice(id)
  }

  function toggleVoicePreview(av, e) {
    e.stopPropagation()
    const url = av.voice?.preview_url
    if (!url) return
    playAudio(url, av.avatar_id)
  }

  // Photo upload
  async function handlePhotoChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setPhotoError('')
    setPhotoPreview(URL.createObjectURL(file))
    setPhotoAssetId(null)
    setPhotoUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch(`${API_BASE}/upload/photo`, { method: 'POST', body: fd })
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail) }
      setPhotoAssetId((await res.json()).asset_id)
    } catch (err) {
      setPhotoError(err.message || 'Upload failed')
    } finally {
      setPhotoUploading(false)
    }
  }

  // Voice clone upload
  async function uploadVoiceFile(file) {
    setVoiceUploading(true); setVoiceError(''); setVoiceId(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('voice_name', voiceName)
      fd.append('language', 'en')
      const res = await fetch(`${API_BASE}/upload/voice`, { method: 'POST', body: fd })
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail) }
      setVoiceId((await res.json()).voice_id)
    } catch (err) {
      setVoiceError(err.message || 'Voice clone failed')
    } finally {
      setVoiceUploading(false)
    }
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      const chunks = []
      mr.ondataavailable = e => chunks.push(e.data)
      mr.onstop = () => {
        setRecordedBlob(new Blob(chunks, { type: 'audio/webm' }))
        stream.getTracks().forEach(t => t.stop())
        clearInterval(timerRef.current)
      }
      mr.start()
      setMediaRec(mr); setRecording(true); setRecordSecs(0)
      timerRef.current = setInterval(() => setRecordSecs(s => s + 1), 1000)
    } catch { setVoiceError('Microphone access denied') }
  }

  function stopRecording() {
    mediaRec?.stop(); setRecording(false); setMediaRec(null)
    clearInterval(timerRef.current)
  }

  const fmtSecs = s => `${Math.floor(s/60).toString().padStart(2,'0')}:${(s%60).toString().padStart(2,'0')}`

  const SubtitleToggle = () => (
    <div className="subtitle-toggle">
      <span className="subtitle-toggle__label">Subtitles</span>
      <div className="subtitle-opts">
        <button type="button"
          className={`subtitle-btn ${!burnCaptions ? 'subtitle-btn--active' : ''}`}
          onClick={() => setBurnCaptions(false)}>Off</button>
        <button type="button"
          className={`subtitle-btn ${burnCaptions ? 'subtitle-btn--active' : ''}`}
          onClick={() => setBurnCaptions(true)}>Burn In</button>
      </div>
      <span className="subtitle-toggle__hint">
        {burnCaptions ? 'Captions burned into video' : 'No captions'}
      </span>
    </div>
  )

  return (
    <div className="anchor-sel">
      <div className="anchor-sel__label">Choose Your Anchor</div>

      <div className="anchor-sel__tabs" role="tablist">
        {TABS.map(t => (
          <button key={t.id} role="tab" type="button"
            aria-selected={tab === t.id}
            className={`anchor-tab ${tab === t.id ? 'anchor-tab--active' : ''}`}
            onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── AVATAR TAB ── */}
      {tab === 'avatar' && (
        <div className="anchor-panel">
          {!avatarLoad && avatars.length > 0 && (
            <div className="gender-filter" role="group" aria-label="Filter by gender">
              {GENDER_FILTERS.map(g => (
                <button key={g.id} type="button"
                  className={`gender-btn ${genderFilter === g.id ? 'gender-btn--active' : ''}`}
                  onClick={() => setGenderFilter(g.id)}>
                  {g.label}
                  <span className="gender-btn__count">
                    {g.id === 'all' ? avatars.length : avatars.filter(a => a.gender === g.id).length}
                  </span>
                </button>
              ))}
            </div>
          )}

          {avatarLoad && (
            <div className="anchor-avatars">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="avatar-card avatar-card--skeleton">
                  <div className="skeleton" style={{width:72,height:72,borderRadius:10}} />
                  <div className="skeleton" style={{width:60,height:10,marginTop:4}} />
                </div>
              ))}
            </div>
          )}

          {!avatarLoad && avatars.length === 0 && (
            <p className="anchor-hint">No avatars found. Make sure <code>HEYGEN_API_KEY</code> is set.</p>
          )}

          {!avatarLoad && filtered.length > 0 && (
            <div className="anchor-avatars">
              {filtered.map(av => {
                const isSelected = selectedAvatar?.avatar_id === av.avatar_id
                const hasVoice   = !!av.voice?.preview_url
                const isPlaying  = playingVoice === av.avatar_id
                return (
                  <button key={av.avatar_id} type="button"
                    className={`avatar-card ${isSelected ? 'avatar-card--selected' : ''}`}
                    onClick={() => setSelectedAvatar(av)}
                    aria-pressed={isSelected} title={av.name}>
                    <div className="avatar-card__img-wrap">
                      {av.preview_url
                        ? <img src={av.preview_url} alt={av.name} className="avatar-card__img" />
                        : <div className="avatar-card__placeholder">
                            {av.gender === 'female' ? '👩' : av.gender === 'male' ? '👨' : '👤'}
                          </div>
                      }
                      {av.gender && (
                        <span className={`gender-badge gender-badge--${av.gender}`}>
                          {av.gender === 'female' ? '♀' : '♂'}
                        </span>
                      )}
                      {hasVoice && (
                        <button type="button"
                          className={`voice-preview-btn ${isPlaying ? 'voice-preview-btn--playing' : ''}`}
                          onClick={e => toggleVoicePreview(av, e)}
                          aria-label={isPlaying ? 'Stop' : 'Preview voice'}>
                          {isPlaying ? '⏹' : '▶'}
                        </button>
                      )}
                    </div>
                    <span className="avatar-card__name">{av.name}</span>
                    {isSelected && <span className="avatar-card__check" aria-hidden="true">✓</span>}
                  </button>
                )
              })}
            </div>
          )}

          {/* Selected avatar info + voice picker */}
          {selectedAvatar && (
            <div className="selected-avatar-info">
              {selectedAvatar.preview_url && (
                <img src={selectedAvatar.preview_url} alt={selectedAvatar.name}
                  className="selected-avatar-info__img"
                  onError={e => { e.target.style.display='none' }} />
              )}
              <div style={{flex:1}}>
                <p className="selected-avatar-info__name">{selectedAvatar.name}</p>
                <div className="selected-avatar-info__sub">
                  {selectedAvatar.gender && <span className="gender-pill">{selectedAvatar.gender}</span>}

                  {/* Voice selector */}
                  <button type="button" className="voice-pick-btn"
                    onClick={() => setShowVoicePicker(v => !v)}>
                    🎙️ {selectedVoice ? selectedVoice.name : 'Default Voice'} ▾
                  </button>
                  {selectedVoice && (
                    <button type="button" className="voice-clear-btn"
                      onClick={() => setSelectedVoice(null)}>✕ Reset</button>
                  )}
                </div>

                {/* Voice dropdown */}
                {showVoicePicker && (
                  <div className="voice-picker">
                    <div className="voice-picker__header">
                      <span>Choose a Voice</span>
                      <button type="button" onClick={() => setShowVoicePicker(false)}>✕</button>
                    </div>
                    {voices.length === 0 && <p className="voice-picker__loading">Loading voices...</p>}
                    <div className="voice-picker__list">
                      {voices.map(v => (
                        <div key={v.voice_id}
                          className={`voice-picker__item ${selectedVoice?.voice_id === v.voice_id ? 'voice-picker__item--active' : ''}`}
                          onClick={() => { setSelectedVoice(v); setShowVoicePicker(false) }}>
                          <div className="voice-picker__item-info">
                            <span className="voice-picker__name">{v.name}</span>
                            <span className="voice-picker__meta">{v.language} · {v.gender}</span>
                          </div>
                          {v.preview_url && (
                            <button type="button" className="voice-picker__play"
                              onClick={e => { e.stopPropagation(); playAudio(v.preview_url, v.voice_id) }}>
                              {playingVoice === v.voice_id ? '⏹' : '▶'}
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <span className="selected-avatar-info__check">✓ Selected</span>
            </div>
          )}

          <SubtitleToggle />
        </div>
      )}

      {/* ── PHOTO TAB ── */}
      {tab === 'photo' && (
        <div className="anchor-panel">
          <div className="photo-instructions">
            <div className="photo-tip"><span>✅</span><span>Clear face, good lighting, front-facing</span></div>
            <div className="photo-tip"><span>❌</span><span>No sunglasses, no group photos, no blur</span></div>
          </div>
          <div className={`photo-drop ${photoPreview ? 'photo-drop--has-img' : ''}`}
            onClick={() => photoInputRef.current?.click()}
            onDragOver={e => e.preventDefault()}
            onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handlePhotoChange({ target: { files: [f] } }) }}
            role="button" tabIndex={0} aria-label="Upload your photo">
            {photoPreview ? (
              <div className="photo-drop__preview-wrap">
                <img src={photoPreview} alt="Your photo" className="photo-drop__preview" />
                <div className="photo-drop__overlay">Click to change</div>
              </div>
            ) : (
              <div className="photo-drop__empty">
                <span className="photo-drop__icon">🤳</span>
                <span className="photo-drop__text">Drop your photo here</span>
                <span className="photo-drop__sub">or click to browse</span>
                <span className="photo-drop__formats">JPEG · PNG · WebP · max 10MB</span>
              </div>
            )}
          </div>
          <input ref={photoInputRef} type="file" accept="image/jpeg,image/png,image/webp"
            className="sr-only" onChange={handlePhotoChange} />
          {photoUploading && <div className="upload-progress"><div className="upload-progress__bar" /><span>Uploading...</span></div>}
          {photoAssetId && !photoUploading && <div className="anchor-status anchor-status--ok">✓ Photo ready</div>}
          {photoError && <div className="anchor-status anchor-status--err">⚠ {photoError}</div>}
          <SubtitleToggle />
        </div>
      )}

      {/* ── VOICE TAB ── */}
      {tab === 'voice' && (
        <div className="anchor-panel">
          <p className="anchor-hint">Record 30+ seconds of clear speech or upload an audio file to clone your voice.</p>
          <div className="voice-name-row">
            <label htmlFor="vname" className="anchor-voice-label">Voice name</label>
            <input id="vname" type="text" value={voiceName}
              onChange={e => setVoiceName(e.target.value)}
              className="voice-name-input" placeholder="e.g. My News Voice" />
          </div>
          <div className="record-section">
            <div className="record-section__header">
              <span className="record-section__title">🎙️ Record</span>
              {recording && (
                <span className="record-timer" aria-live="polite">
                  <span className="rec-dot" aria-hidden="true" />{fmtSecs(recordSecs)}
                </span>
              )}
            </div>
            <div className="voice-actions">
              {!recording
                ? <button type="button" className="btn-record" onClick={startRecording}>Start Recording</button>
                : <button type="button" className="btn-record btn-record--stop" onClick={stopRecording}>Stop Recording</button>
              }
              {recordedBlob && !recording && !voiceUploading && !voiceId && (
                <button type="button" className="btn-use-rec"
                  onClick={() => uploadVoiceFile(new File([recordedBlob], 'recording.webm', { type: 'audio/webm' }))}>
                  ✓ Use This Recording
                </button>
              )}
            </div>
          </div>
          <div className="upload-section">
            <span className="record-section__title">📁 Upload File</span>
            <div className="voice-actions">
              <button type="button" className="btn-upload-voice" onClick={() => voiceInputRef.current?.click()}>
                Choose Audio File
              </button>
              <span className="anchor-hint-sm">MP3, WAV, OGG, WebM</span>
            </div>
            <input ref={voiceInputRef} type="file" accept="audio/mpeg,audio/wav,audio/ogg,audio/webm"
              className="sr-only"
              onChange={e => { const f = e.target.files?.[0]; if (f) uploadVoiceFile(f) }} />
          </div>
          {voiceUploading && <div className="upload-progress"><div className="upload-progress__bar upload-progress__bar--pulse" /><span>Cloning your voice... (~30s)</span></div>}
          {voiceId    && <div className="anchor-status anchor-status--ok">✓ Voice cloned and ready!</div>}
          {voiceError && <div className="anchor-status anchor-status--err">⚠ {voiceError}</div>}
          <SubtitleToggle />
        </div>
      )}
    </div>
  )
}
