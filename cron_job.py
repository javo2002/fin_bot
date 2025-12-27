import os
import logging
from src.bank.csv_loader import CSVBank
from src.agent.core import run_financial_analysis
from src.notifications.telegram_service import TelegramNotifier
from src.database import init_db
from src.config import PLAID_CLIENT_ID, PLAID_SECRET

# Feature Flag: Use Plaid if keys exist, otherwise CSV/Mock
HAS_PLAID = bool(PLAID_CLIENT_ID and PLAID_SECRET)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='financial_agent.log'
)

def run_headless_audit():
    logging.info("🚀 Starting Headless Audit...")
    init_db()
    notifier = TelegramNotifier()
    
    if not notifier.is_configured():
        logging.error("❌ Telegram keys missing. Cannot send report.")
        return

    # --- DATA LOADING STRATEGY ---
    bank = None
    
    if HAS_PLAID:
        try:
            from src.bank.plaid_connector import PlaidBank
            logging.info("🔌 Connecting to Real Plaid...")
            bank = PlaidBank()
        except Exception as e:
            logging.error(f"Plaid Connection Failed: {e}")
    
    # Fallback 1: CSVs
    if not bank and os.path.exists("pnc.csv"):
        logging.info("📂 Loading CSVs...")
        bank = CSVBank("pnc.csv", "capone.csv")
    
    # Fallback 2: The Stunt Double (Mock Plaid)
    if not bank:
        logging.info("👻 No Real Data found. Switching to MOCK PLAID Mode.")
        from src.bank.plaid_mock import PlaidMock
        bank = PlaidMock()
        bank.load_data()

    try:
        # Context
        context = "Income: $6600/mo. Tax Rate: 25%. Status: Contractor."
        
        logging.info("🧠 Running AI Analysis...")
        result = run_financial_analysis(bank, f"Daily Audit: Analyze my financial status. {context}")
        
        analysis_text = result.get("analysis", "No analysis generated.")
        actions = result.get("proposed_actions", [])
        
        logging.info("📱 Sending Telegram Report...")
        notifier.send_report(analysis_text, actions)
        
        logging.info("✅ Audit Complete.")

    except Exception as e:
        logging.error(f"❌ Critical Error: {e}")
        notifier.send_message(f"⚠️ Agent Error: {str(e)}")

if __name__ == "__main__":
    run_headless_audit()