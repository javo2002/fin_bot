import requests
import os
from dotenv import load_dotenv

# Load keys
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print(f"Token: {TOKEN[:5]}..." if TOKEN else "❌ Token Missing")
print(f"Chat ID: {CHAT_ID}" if CHAT_ID else "❌ Chat ID Missing")

if TOKEN and CHAT_ID:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "✅ Financial Architect: Connection Successful!",
        "parse_mode": "Markdown"
    }
    
    print("\nAttempting to send message...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n🎉 SUCCESS! Check your phone.")
        elif response.status_code == 401:
            print("\n❌ ERROR: Your BOT TOKEN is wrong.")
        elif response.status_code == 400:
            print("\n❌ ERROR: Your CHAT ID is wrong (or you haven't clicked START).")
            print("Action: Search for your bot username and click START.")
    except Exception as e:
        print(f"Connection Error: {e}")