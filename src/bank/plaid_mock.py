import random
from datetime import datetime, timedelta
from src.database import save_transaction, save_balance_snapshot

class PlaidMock:
    def __init__(self):
        print("👻 PLAID MOCK MODE: Simulating bank connection...")
        self.accounts = {}

    def load_data(self):
        """Generates fake data to test the pipeline."""
        
        # 1. Simulate Accounts
        # We simulate your exact setup so the Agent logic holds up
        mock_accounts = [
            {"name": "PNC Checking", "balance": 4120.50, "type": "checking"},
            {"name": "Capital One Checking", "balance": 350.00, "type": "checking"},
            {"name": "Ally Savings", "balance": 9100.00, "type": "savings"}
        ]

        for acc in mock_accounts:
            # Save Snapshot to DB
            save_balance_snapshot(acc['name'], acc['balance'])
            
            self.accounts[acc['name']] = {
                "balance": acc['balance'],
                "type": acc['type'],
                "transactions": []
            }

        # 2. Simulate Recent Transactions (Ghost Data)
        # We generate random spending to see if the AI catches it
        vendors = [
            ("Netflix", 15.99, "Subscription"),
            ("Shell Gas", 45.00, "Transport"),
            ("Trader Joes", 82.50, "Food"),
            ("Spotify", 10.99, "Subscription"),
            ("Affirm Payment", 50.00, "Loans"),
            ("Direct Deposit", -2300.00, "Income") # Negative because logic flips it
        ]

        # Generate 5 random transactions for "Yesterday"
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        for _ in range(5):
            vendor, amount, cat = random.choice(vendors)
            # Add some randomness to amount
            final_amount = round(amount * random.uniform(0.9, 1.1), 2)
            
            # Save to DB
            # We treat positive numbers as spend here to match Plaid's native format
            # But remember your DB expects "Dashboard Format" (Spend = Positive)
            save_transaction(yesterday, vendor, final_amount, cat, "Capital One Checking")
            
            # Add to memory
            self.accounts["Capital One Checking"]["transactions"].append({
                "date": yesterday,
                "desc": vendor,
                "amount": final_amount,
                "category": cat
            })

    def get_data(self):
        return self.accounts