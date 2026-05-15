"""
Run this script to get your HeyGen Avatar IDs and Voice IDs.
Usage: python get_heygen_ids.py
"""
import urllib.request
import json

API_KEY = "sk_V2_hgu_k4XCALxOKjP_MCxtNJUVvqk9KGY2WXzvNuZOoT8EHcGS"
HEADERS = {"x-api-key": API_KEY, "Content-Type": "application/json"}

def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

print("\n=== AVATARS ===")
try:
    data = get("https://api.heygen.com/v2/avatars")
    avatars = data.get("data", {}).get("avatars", [])
    print(f"Found {len(avatars)} avatars (v2):\n")
    for a in avatars[:10]:
        print(f"  AVATAR_ID : {a.get('avatar_id')}")
        print(f"  Name      : {a.get('avatar_name', a.get('name', ''))}")
        print()
except Exception as e:
    print(f"Error (v2): {e}")

try:
    data = get("https://api.heygen.com/v1/avatar.list")
    avatars = data.get("data", {}).get("avatars", [])
    print(f"Found {len(avatars)} avatars (v1):\n")
    for a in avatars[:10]:
        print(f"  AVATAR_ID : {a.get('avatar_id')}")
        print(f"  Name      : {a.get('avatar_name', a.get('name', ''))}")
        print()
except Exception as e:
    print(f"Error (v1): {e}")

print("\n=== VOICES ===")
try:
    data = get("https://api.heygen.com/v2/voices")
    voices = data.get("data", {}).get("voices", [])
    print(f"Found {len(voices)} voices:\n")
    for v in voices[:10]:
        print(f"  VOICE_ID  : {v.get('voice_id')}")
        print(f"  Name      : {v.get('display_name', v.get('name', ''))}")
        print(f"  Language  : {v.get('language', '')}")
        print()
except Exception as e:
    print(f"Error: {e}")

print("\nCopy the IDs above into your .env file:")
print("  HEYGEN_AVATAR_ID=<avatar_id from above>")
print("  HEYGEN_VOICE_ID=<voice_id from above>")
