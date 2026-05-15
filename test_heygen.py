#!/usr/bin/env python3
import asyncio
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE = "https://api.heygen.com"

def _headers():
    return {
        "x-api-key": os.getenv("HEYGEN_API_KEY", ""),
        "Content-Type": "application/json",
    }

async def test_heygen_api():
    print(f"API Key: {os.getenv('HEYGEN_API_KEY', 'NOT_SET')[:20]}...")
    
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            print(f"Making request to {BASE}/v2/avatars")
            resp = await client.get(f"{BASE}/v2/avatars", headers=_headers())
            print(f"Response status: {resp.status_code}")
            print(f"Response headers: {dict(resp.headers)}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Response data keys: {list(data.keys())}")
                avatars = data.get("data", {}).get("avatars", [])
                print(f"Found {len(avatars)} avatars")
                if avatars:
                    print(f"First avatar: {avatars[0]}")
            else:
                print(f"Error response: {resp.text}")
                
        except Exception as e:
            print(f"Exception: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_heygen_api())