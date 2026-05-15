import './NewsTicker.css'

const HEADLINES = [
  'BREAKING: Global AI summit reaches landmark agreement on safety standards',
  'MARKETS: Tech stocks surge as inflation data comes in lower than expected',
  'WORLD: UN Security Council convenes emergency session on regional tensions',
  'SCIENCE: Researchers announce breakthrough in quantum computing efficiency',
  'HEALTH: WHO issues updated guidelines on respiratory illness prevention',
  'SPORTS: Record-breaking performance stuns crowds at international championship',
  'TECH: Major social platform rolls out AI-powered content moderation tools',
  'CLIMATE: Arctic ice levels reach historic low, scientists warn of acceleration',
]

export default function NewsTicker() {
  const repeated = [...HEADLINES, ...HEADLINES]

  return (
    <div className="ticker" role="marquee" aria-label="Breaking news ticker">
      <div className="ticker__label" aria-hidden="true">
        <span>BREAKING</span>
      </div>
      <div className="ticker__track">
        <div className="ticker__inner" aria-live="off">
          {repeated.map((h, i) => (
            <span key={i} className="ticker__item">
              {h}
              <span className="ticker__sep" aria-hidden="true">◆</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
