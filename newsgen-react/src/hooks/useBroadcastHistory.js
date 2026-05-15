import { useState, useEffect } from 'react'

const KEY     = 'newsgen_history'
const MAX     = 5

export function useBroadcastHistory() {
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(localStorage.getItem(KEY) || '[]') }
    catch { return [] }
  })

  function addBroadcast({ name, city, language, videoUrl, script, newsCount, timestamp }) {
    const entry = { id: Date.now(), name, city, language, videoUrl, script, newsCount, timestamp: timestamp || new Date().toISOString() }
    setHistory(prev => {
      const next = [entry, ...prev].slice(0, MAX)
      localStorage.setItem(KEY, JSON.stringify(next))
      return next
    })
  }

  function clearHistory() {
    localStorage.removeItem(KEY)
    setHistory([])
  }

  return { history, addBroadcast, clearHistory }
}
