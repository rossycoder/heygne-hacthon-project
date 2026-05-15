"""
Broadcast History Manager
Saves generated broadcasts to avoid re-generating and save API costs
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "broadcast_history.json")

def _load_history() -> List[Dict]:
    """Load broadcast history from JSON file"""
    if not os.path.exists(HISTORY_FILE):
        return []
    
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception:
        return []

def _save_history(history: List[Dict]):
    """Save broadcast history to JSON file"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")

def save_broadcast(
    name: str,
    city: str, 
    language: str,
    script: str,
    video_url: str,
    news_stories: List[Dict],
    avatar_id: Optional[str] = None,
    topics: Optional[List[str]] = None
) -> str:
    """
    Save a completed broadcast to history
    Returns the broadcast ID
    """
    history = _load_history()
    
    broadcast_id = f"broadcast_{len(history) + 1}_{int(datetime.now().timestamp())}"
    
    broadcast = {
        "id": broadcast_id,
        "name": name,
        "city": city,
        "language": language,
        "topics": topics or [],
        "avatar_id": avatar_id,
        "script": script,
        "video_url": video_url,
        "news_stories": news_stories,
        "news_count": len(news_stories),
        "created_at": datetime.now().isoformat(),
        "timestamp": int(datetime.now().timestamp())
    }
    
    history.append(broadcast)
    _save_history(history)
    
    return broadcast_id

def get_broadcast_history(limit: int = 20) -> List[Dict]:
    """Get recent broadcast history"""
    history = _load_history()
    # Sort by timestamp (newest first)
    history.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    return history[:limit]

def get_broadcast_by_id(broadcast_id: str) -> Optional[Dict]:
    """Get a specific broadcast by ID"""
    history = _load_history()
    for broadcast in history:
        if broadcast.get('id') == broadcast_id:
            return broadcast
    return None

def delete_broadcast(broadcast_id: str) -> bool:
    """Delete a broadcast from history"""
    history = _load_history()
    original_length = len(history)
    history = [b for b in history if b.get('id') != broadcast_id]
    
    if len(history) < original_length:
        _save_history(history)
        return True
    return False

def find_similar_broadcast(name: str, city: str, language: str, topics: List[str] = None) -> Optional[Dict]:
    """
    Find a similar broadcast to avoid regenerating
    Matches by name, city, language and similar topics
    """
    history = _load_history()
    topics = topics or []
    
    for broadcast in history:
        # Check if basic parameters match
        if (broadcast.get('name', '').lower() == name.lower() and
            broadcast.get('city', '').lower() == city.lower() and
            broadcast.get('language', '').lower() == language.lower()):
            
            # Check topic similarity (at least 70% overlap)
            broadcast_topics = set(t.lower() for t in broadcast.get('topics', []))
            request_topics = set(t.lower() for t in topics)
            
            if not topics or not broadcast_topics:
                # If no topics specified, consider it a match
                return broadcast
            
            # Calculate topic overlap
            overlap = len(broadcast_topics.intersection(request_topics))
            total = len(broadcast_topics.union(request_topics))
            
            if total == 0 or overlap / total >= 0.7:
                return broadcast
    
    return None