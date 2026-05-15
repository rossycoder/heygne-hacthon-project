import './SkeletonLoader.css'

/** Generic skeleton block */
export function Skeleton({ width = '100%', height = '14px', radius = '6px', style = {} }) {
  return (
    <div
      className="skeleton"
      style={{ width, height, borderRadius: radius, ...style }}
      aria-hidden="true"
    />
  )
}

/** Skeleton for a single news card */
export function NewsCardSkeleton() {
  return (
    <div className="skeleton-card" aria-hidden="true">
      <div className="skeleton-card__top">
        <Skeleton width="58px" height="18px" radius="4px" />
        <Skeleton width="40px" height="12px" />
      </div>
      <Skeleton width="88%" height="14px" />
      <Skeleton width="100%" height="11px" />
      <Skeleton width="72%" height="11px" />
    </div>
  )
}

/** Full news feed skeleton — 5 cards */
export function NewsFeedSkeleton({ count = 5 }) {
  return (
    <div className="skeleton-feed" aria-label="Loading news stories" aria-busy="true">
      {Array.from({ length: count }).map((_, i) => (
        <NewsCardSkeleton key={i} />
      ))}
    </div>
  )
}

/** Skeleton for the broadcast headline sidebar */
export function HeadlineSidebarSkeleton({ count = 5 }) {
  return (
    <div className="skeleton-sidebar" aria-label="Loading headlines" aria-busy="true">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton-card">
          <div className="skeleton-card__top">
            <Skeleton width="52px" height="16px" radius="4px" />
            <Skeleton width="24px" height="12px" />
          </div>
          <Skeleton width="90%" height="13px" />
          <Skeleton width="100%" height="10px" />
          <Skeleton width="65%" height="10px" />
        </div>
      ))}
    </div>
  )
}
