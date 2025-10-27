import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Your credentials from Zoom Developer Portal
ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")

def get_zoom_token():
    """Get Server-to-Server OAuth token"""
    url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={ACCOUNT_ID}"
    
    response = requests.post(
        url,
        auth=(CLIENT_ID, CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Token obtained: {token[:20]}...")
        return token
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def list_recordings(token):
    """Test API by listing recent recordings"""
    url = "https://api.zoom.us/v2/users/me/recordings"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        recordings = response.json()
        print(f"✅ Found {len(recordings.get('meetings', []))} recordings")
        return recordings
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("Testing Zoom API connection...")
    token = get_zoom_token()
    if token:
        list_recordings(token)
