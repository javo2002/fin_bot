import requests
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class TelegramNotifier:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def is_configured(self):
        return bool(self.token and self.chat_id)

    def send_message(self, text):
        """Sends a simple raw text message."""
        if not self.is_configured(): return "Config Error"
        
        payload = {"chat_id": self.chat_id, "text": text}
        try:
            requests.post(self.base_url, json=payload)
            return "Sent"
        except:
            return "Error"

    def send_report(self, analysis_text, actions):
        """Formats the Financial Report and sends it to your phone."""
        if not self.is_configured():
            return "Telegram keys not found in .env"

        # 1. Format the Message
        message = "💰 FINANCIAL ARCHITECT REPORT 💰\n\n"
        
        # Add Analysis
        clean_analysis = analysis_text.replace("### ", "").replace("**", "")
        message += "📝 STRATEGY:\n"
        message += clean_analysis
        
        # Add Actions
        if actions:
            message += "\n\n🚀 ACTION ITEMS:\n"
            for act in actions:
                message += f"• Move ${act['amount']} to {act['to']}\n"
        else:
            message += "\n\n✅ No transfers needed today."

        # 2. Send Request
        payload = {
            "chat_id": self.chat_id,
            "text": message
        }
        
        try:
            response = requests.post(self.base_url, json=payload)
            if response.status_code == 200:
                return "✅ Sent to phone!"
            else:
                return f"❌ Telegram Error: {response.text}"
        except Exception as e:
            return f"❌ Connection Error: {e}"