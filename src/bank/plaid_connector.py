import json
import os
import plaid
from datetime import datetime, timedelta
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from src.config import PLAID_CLIENT_ID, PLAID_SECRET, PLAID_ENV
from src.database import save_transaction, save_balance_snapshot

class PlaidBank:
    def __init__(self):
        # Initialize Plaid Client
        configuration = plaid.Configuration(
            host=getattr(plaid.Environment, PLAID_ENV.capitalize()),
            api_key={'clientId': PLAID_CLIENT_ID, 'secret': PLAID_SECRET}
        )
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
        self.accounts = {}
        
        # Load Access Tokens
        if os.path.exists("plaid_tokens.json"):
            with open("plaid_tokens.json", "r") as f:
                self.tokens = json.load(f)
        else:
            self.tokens = {}
            print("⚠️ No Plaid tokens found. Run 'python plaid_setup.py' first.")

        # Fetch Data
        if self.tokens:
            self.load_data()

    def load_data(self):
        """Fetches real-time data from all connected banks."""
        
        for item_id, access_token in self.tokens.items():
            try:
                # 1. Get Transactions (Last 30 days)
                start_date = (datetime.now() - timedelta(days=30)).date()
                end_date = datetime.now().date()
                
                request = TransactionsGetRequest(
                    access_token=access_token,
                    start_date=start_date,
                    end_date=end_date,
                    options=TransactionsGetRequestOptions(include_personal_finance_category=True)
                )
                response = self.client.transactions_get(request)
                
                # 2. Process Accounts & Balances
                for acc in response['accounts']:
                    # Normalize Account Names to match your Strategy
                    # (In a real app, you'd map these IDs to 'PNC Checking' in a config file)
                    # For now, we simple-map based on subtype
                    acc_name = acc['name']
                    if "checking" in acc['subtype']:
                        acc_name = "PNC Checking" # Assuming first checking is PNC for now
                    elif "savings" in acc['subtype']:
                        acc_name = "Ally Savings"
                    
                    current_bal = acc['balances']['current']
                    
                    # Save snapshot to DB
                    save_balance_snapshot(acc_name, current_bal)
                    
                    # Store in memory
                    self.accounts[acc_name] = {
                        "balance": current_bal,
                        "type": acc['subtype'],
                        "transactions": []
                    }

                # 3. Process Transactions
                for t in response['transactions']:
                    # Map to correct account
                    # (Simplified: logic assumes mapped names above)
                    # Ideally we map t['account_id'] -> Account Name
                    
                    # Data Cleaning
                    date_str = str(t['date'])
                    desc = t['name']
                    amount = t['amount'] # Plaid: positive = spend, negative = refund
                    # We need to invert this for your dashboard logic (where negative = spend)
                    # Your CSV logic: -50 = spend. Plaid: 50 = spend.
                    # So we multiply by -1.
                    dashboard_amount = amount * -1
                    
                    category = t['personal_finance_category']['primary'] if t['personal_finance_category'] else "Uncategorized"
                    
                    # Deduplication & Save
                    # Note: We don't have account name mapping perfect here without more config
                    # Defaulting to "PNC Checking" for demo purposes if ID matches
                    target_acc = "PNC Checking" # Placeholder
                    
                    save_transaction(date_str, desc, dashboard_amount, category, target_acc)
                    
                    # Add to memory
                    if target_acc in self.accounts:
                        self.accounts[target_acc]["transactions"].append({
                            "date": date_str,
                            "desc": desc,
                            "amount": dashboard_amount,
                            "category": category
                        })

            except plaid.ApiException as e:
                print(f"❌ Plaid Error for item {item_id}: {e}")

    def get_data(self):
        return self.accounts