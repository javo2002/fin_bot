class MockBank:
    def __init__(self):
        self.accounts = {
            # 1. THE HUB (Empty - Waiting for Job to Start)
            "PNC Checking": {
                "balance": 50.00, 
                "type": "checking",
                "transactions": []
            },
            # 2. THE WALLET (Empty)
            "Capital One Checking": {
                "balance": 10.00, 
                "type": "checking",
                "transactions": []
            },
            # 3. THE CAR FUND (Empty)
            "Ally Savings": {
                "balance": 0.00, 
                "type": "savings",
                "transactions": [] 
            }
        }

    def get_data(self):
        return self.accounts

    def transfer_funds(self, from_acc, to_acc, amount):
        # Even mock transfers fail if no money!
        if self.accounts[from_acc]["balance"] >= amount:
            self.accounts[from_acc]["balance"] -= amount
            self.accounts[to_acc]["balance"] += amount
            return f"SUCCESS: Moved ${amount} from {from_acc} to {to_acc}."
        else:
            return "ERROR: Insufficient funds."