import './Navbar.css'

export default function Navbar() {
  return (
    <nav className="navbar" role="banner">
      <div className="navbar__logo">
        <span className="navbar__icon">📡</span>
        <span className="navbar__name">NewsGen <span className="navbar__ai">AI</span></span>
      </div>
      <div className="navbar__live" aria-label="Live broadcast indicator">
        <span className="live-dot" aria-hidden="true" />
        <span className="live-label">LIVE</span>
      </div>
    </nav>
  )
}
