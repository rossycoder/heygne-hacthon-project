import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import NewsTicker from '../components/NewsTicker'
import LoadingScreen from '../components/LoadingScreen'
import NewsPreview from '../components/NewsPreview'
import LiveNewsFeed from '../components/LiveNewsFeed'
import AnchorSelector from '../components/AnchorSelector'
import ScriptEditor from '../components/ScriptEditor'
import BroadcastHistory from '../components/BroadcastHistory'
import { generateBroadcast, getNewsFeed } from '../api'
import './HomePage.css'

const LANGUAGES = ['English', 'Urdu', 'Arabic', 'Hindi', 'French', 'Spanish']
const TOPICS = ['World', 'Tech', 'Pakistan', 'Business', 'Sports', 'Health', 'Science']
const CITY_LANG_HINTS = {
  pakistan: 'Urdu', lahore: 'Urdu', karachi: 'Urdu', islamabad: 'Urdu',
  'azad kashmir': 'Urdu', multan: 'Urdu', peshawar: 'Urdu',
  india: 'Hindi', delhi: 'Hindi', mumbai: 'Hindi',
  dubai: 'Arabic', 'saudi arabia': 'Arabic', uae: 'Arabic',
  france: 'French', paris: 'French', spain: 'Spanish', mexico: 'Spanish',
}
const HOW_IT_WORKS = [
  { icon: '🌐', step: '01', title: 'Fetch', desc: 'AI pulls top stories filtered by your city and topics.' },
  { icon: '✍️', step: '02', title: 'Script', desc: 'Claude AI writes a personalized script. You can edit it before generating.' },
  { icon: '🎬', step: '03', title: 'Broadcast', desc: 'HeyGen Avatar delivers your video in your chosen language.' },
]


export default function HomePage() {
  const navigate = useNavigate()

  const [name, setName] = useState('')
  const [city, setCity] = useState('')
  const [language, setLanguage] = useState('English')
  const [topics, setTopics] = useState(['World', 'Tech'])
  const [langHint, setLangHint] = useState('')
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [videoLoading, setVideoLoading] = useState(false)
  const [sessionId, setSessionId] = useState('')
  const [error, setError] = useState('')
  const [previewing, setPreviewing] = useState(false)
  const [previewStories, setPreviewStories] = useState(null)
  const [previewLang, setPreviewLang] = useState('')
  const [scriptPhase, setScriptPhase] = useState(false)
  const [generatedScript, setGeneratedScript] = useState('')
  const [anchor, setAnchor] = useState({
    mode: 'avatar', avatarId: null, voiceId: null, imageAssetId: null, burnCaptions: false
  })

  function toggleTopic(t) {
    setTopics(prev => prev.includes(t) ? prev.filter(x => x !== t) : [...prev, t])
  }

  function handleCityChange(val) {
    setCity(val)
    const hint = CITY_LANG_HINTS[val.toLowerCase().trim()]
    setLangHint(hint || '')
    if (hint && language === 'English') setLanguage(hint)
  }

  async function handlePreview() {
    if (!city.trim()) return
    setPreviewing(true); setError(''); setPreviewStories([])
    try {
      const data = await getNewsFeed({ city: city.trim(), language, topics })
      setPreviewStories(data.stories); setPreviewLang(data.language)
    } catch (err) {
      setError(err.message || 'Could not fetch news.')
      setPreviewStories(null)
    } finally { setPreviewing(false) }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!name.trim() || !city.trim()) return
    setError(''); setLoading(true); setStep(0); setScriptPhase(false)
    try {
      const timer = setInterval(() => setStep(s => s < 3 ? s + 1 : s), 3000)
      const data = await generateBroadcast({
        name: name.trim(), city: city.trim(), language, topics,
        avatarId: anchor.avatarId, voiceId: anchor.voiceId,
        imageAssetId: anchor.imageAssetId, anchorMode: anchor.mode,
        burnCaptions: anchor.burnCaptions, scriptOnly: true,
      })
      clearInterval(timer)
      setGeneratedScript(data.script)
      setScriptPhase(true)
    } catch (err) {
      setError(err.message || 'Something went wrong.')
    } finally { setLoading(false) }
  }

  async function handleGenerateVideo(finalScript) {
    // Generate session ID upfront so LoadingScreen can connect to SSE immediately
    const sid = crypto.randomUUID()
    setSessionId(sid)
    setVideoLoading(true); setError(''); setStep(4)
    try {
      const data = await generateBroadcast({
        name: name.trim(), city: city.trim(), language, topics,
        avatarId: anchor.avatarId, voiceId: anchor.voiceId,
        imageAssetId: anchor.imageAssetId, anchorMode: anchor.mode,
        burnCaptions: anchor.burnCaptions, customScript: finalScript,
        sessionId: sid,
      })
      navigate('/broadcast', {
        state: { data, name: name.trim(), city: city.trim(), language: data.detected_language || language }
      })
    } catch (err) {
      setError(err.message || 'Video generation failed.')
      setSessionId('')
    } finally { setVideoLoading(false) }
  }

  return (
    <>
      {(loading || videoLoading) && <LoadingScreen name={name} sessionId={sessionId} />}
      <div className="home">
        <Navbar />
        <NewsTicker />

        <section className="hero">
          <div className="hero__badge">
            <span className="hero__dot" aria-hidden="true" />
            AI-Powered · Personalized · Real-Time
          </div>
          <h1 className="hero__title">
            Your Personal<br />
            <span className="hero__accent">AI News Anchor</span>
          </h1>
          <p className="hero__sub">
            Same global news. Your name. Your city. Your language.<br />
            Ready in under 60 seconds.
          </p>
        </section>

        <section className="form-section" aria-label="Generate your broadcast">
          <div className="form-card">
            <h2 className="form-card__title">Generate My Broadcast</h2>
            <form onSubmit={handleSubmit} noValidate>
              <div className="form-row">
                <div className="field">
                  <label htmlFor="name">Your Name</label>
                  <input id="name" type="text" placeholder="e.g. Rozeena"
                    value={name} onChange={e => setName(e.target.value)}
                    required autoComplete="given-name" />
                </div>
                <div className="field">
                  <label htmlFor="city">Your City</label>
                  <input id="city" type="text" placeholder="e.g. Lahore, New York"
                    value={city} onChange={e => handleCityChange(e.target.value)}
                    required autoComplete="address-level2" />
                  {langHint && language === langHint && (
                    <span className="field__auto-lang">🌐 Auto-detected: {langHint}</span>
                  )}
                </div>
              </div>

              <div className="field">
                <label htmlFor="language">Language</label>
                <select id="language" value={language} onChange={e => setLanguage(e.target.value)}>
                  {LANGUAGES.map(l => <option key={l} value={l}>{l}</option>)}
                </select>
              </div>

              <div className="field">
                <label>Topics<span className="field__hint"> — select what matters to you</span></label>
                <div className="chips" role="group" aria-label="Topic selection">
                  {TOPICS.map(t => (
                    <button key={t} type="button"
                      className={`chip ${topics.includes(t) ? 'chip--active' : ''}`}
                      onClick={() => toggleTopic(t)} aria-pressed={topics.includes(t)}>
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              {city.trim() && (
                <button type="button" className="btn-preview" onClick={handlePreview} disabled={previewing}>
                  {previewing ? '⏳ Fetching stories...' : '👁 Preview My News Feed'}
                </button>
              )}

              {error && <p className="form-error" role="alert">{error}</p>}

              <AnchorSelector onAnchorChange={setAnchor} />

              {scriptPhase && (
                <ScriptEditor
                  script={generatedScript}
                  onConfirm={handleGenerateVideo}
                  loading={videoLoading}
                />
              )}

              {!scriptPhase && (
                <button type="submit" className="btn-generate"
                  disabled={loading || !name.trim() || !city.trim()}>
                  <span>✍️</span> Generate Script First
                </button>
              )}
            </form>
          </div>

          {previewStories !== null && (
            <NewsPreview stories={previewStories} city={city}
              language={previewLang || language} loading={previewing}
              onClose={() => setPreviewStories(null)} />
          )}

          <LiveNewsFeed city={city} language={language} />
          <BroadcastHistory />
        </section>

        <section className="how-section" aria-labelledby="how-title">
          <h2 id="how-title" className="how-section__title">How It Works</h2>
          <div className="how-steps">
            {HOW_IT_WORKS.map((item, i) => (
              <div key={i} className="how-step">
                <div className="how-step__icon" aria-hidden="true">{item.icon}</div>
                <div className="how-step__num">{item.step}</div>
                <h3 className="how-step__title">{item.title}</h3>
                <p className="how-step__desc">{item.desc}</p>
                {i < HOW_IT_WORKS.length - 1 && (
                  <div className="how-step__arrow" aria-hidden="true">→</div>
                )}
              </div>
            ))}
          </div>
        </section>

        <footer className="home-footer">
          <p>Powered by <strong>Claude AI</strong> &amp; <strong>HeyGen Avatars</strong></p>
        </footer>
      </div>
    </>
  )
}
