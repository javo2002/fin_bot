import csv
import os
import logging
from datetime import datetime
from src.database import init_db, save_transaction, save_balance_snapshot, clear_db

# Initialize DB structure immediately
init_db()

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class CSVBank:
    def __init__(self, pnc_file="pnc.csv", capone_file="capone.csv", reset_db=False):
        """
        Initializes the CSV Bank Loader.
        
        Args:
            pnc_file (str): Path to PNC CSV.
            capone_file (str): Path to Capital One CSV.
            reset_db (bool): If True, wipes the database before loading. 
                             CRITICAL: Only set this to True on explicit user action (e.g. upload).
        """
        self.accounts = {}
        self.pnc_path = pnc_file
        self.capone_path = capone_file
        
        if reset_db:
            clear_db()
        
        self.load_data()

    def load_data(self):
        # 1. Process PNC
        self._process_account("PNC Checking", self.pnc_path)

        # 2. Process Capital One
        self._process_account("Capital One Checking", self.capone_path)

        # 3. Ally (Manual/Goal)
        self.accounts["Ally Savings"] = {
            "balance": 0.00, 
            "type": "savings",
            "transactions": []
        }

    def _process_account(self, account_name, filepath):
        """Reads CSV, updates Memory (DB), and populates runtime Bank object."""
        if os.path.exists(filepath):
            try:
                balance = self._get_real_balance(filepath)
                txs = self._parse_csv(filepath)
                
                # --- MEMORY LAYER ---
                if balance != 0.0:
                    save_balance_snapshot(account_name, balance)
                
                new_count = 0
                for tx in txs:
                    # STRICT RULE: Do not save $0.00 transactions
                    if tx['amount'] != 0.0:
                        is_new = save_transaction(
                            tx['date'], 
                            tx['desc'], 
                            tx['amount'], 
                            tx['category'], 
                            account_name
                        )
                        if is_new: new_count += 1
                
                if new_count > 0:
                    logging.info(f"💾 Saved {new_count} new transactions for {account_name}.")
                # --------------------

                self.accounts[account_name] = {
                    "balance": balance,
                    "type": "checking",
                    "transactions": txs
                }
            except Exception as e:
                logging.error(f"Failed to load {filepath}: {e}")
                self.accounts[account_name] = {"balance": 0.0, "transactions": []}
        else:
            self.accounts[account_name] = {"balance": 0.0, "transactions": []}

    def _clean_amount(self, value_str):
        """Standardizes currency strings."""
        if not value_str: return 0.0
        # Remove '$', ',', ' ' (spaces), and '+'
        clean = str(value_str).replace('$', '').replace(',', '').replace(' ', '').replace('+', '').replace('USD', '')
        
        # Handle accounting negative format: (50.00) -> -50.00
        if '(' in clean and ')' in clean:
            clean = '-' + clean.replace('(', '').replace(')', '')
            
        try:
            return float(clean)
        except ValueError:
            return 0.0

    def _get_real_balance(self, filepath):
        """Finds the Balance column using fuzzy matching."""
        try:
            with open(filepath, mode='r', encoding='utf-8-sig', errors='replace') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames: return 0.0
                
                # Normalize headers
                fieldnames = [x.lower().strip() for x in reader.fieldnames]
                
                # Look for 'balance', 'current balance', 'available balance'
                balance_header = next((h for h in fieldnames if 'balance' in h), None)
                
                if balance_header:
                    for row in reader:
                        # Find the matching key in the row
                        for key, val in row.items():
                            if key and key.lower().strip() == balance_header:
                                return self._clean_amount(val)
                        break # Only check the first row (most recent)
        except Exception:
            pass
        return 0.0

    def _parse_csv(self, filepath):
        transactions = []
        try:
            with open(filepath, mode='r', encoding='utf-8-sig', errors='replace') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames: return []
                
                # Normalize headers map
                headers = [h.lower().strip() for h in reader.fieldnames]
                
                # Identify the Amount Column
                amount_col = None
                if 'amount' in headers: amount_col = 'amount'
                elif 'transaction amount' in headers: amount_col = 'transaction amount'
                elif 'amt' in headers: amount_col = 'amt'
                
                # Identify Debit/Credit columns (common in Capital One)
                debit_col = next((h for h in headers if 'debit' in h), None)
                credit_col = next((h for h in headers if 'credit' in h), None)
                
                # Identify Transaction Type column (Capital One often uses this)
                type_col = next((h for h in headers if 'type' in h and 'transaction' in h), None)

                for row in reader:
                    # Create a normalized lookup dict for this row
                    clean_row = {k.lower().strip(): v for k, v in row.items() if k}
                    
                    amount = 0.0
                    
                    # LOGIC 1: Single Amount Column
                    if amount_col and amount_col in clean_row:
                        amount = self._clean_amount(clean_row[amount_col])
                    
                    # LOGIC 2: Debit/Credit Columns (Overrides single column if present and non-empty)
                    if debit_col and clean_row.get(debit_col):
                        val = self._clean_amount(clean_row[debit_col])
                        if val != 0: amount = -abs(val) # Force negative
                    
                    if credit_col and clean_row.get(credit_col):
                        val = self._clean_amount(clean_row[credit_col])
                        if val != 0: amount = abs(val) # Force positive

                    # LOGIC 3: Transaction Type (Capital One Correction)
                    # If we found an amount but it's positive, check if it's marked as "Debit"
                    if type_col and type_col in clean_row:
                        trans_type = clean_row[type_col].lower()
                        if 'debit' in trans_type and amount > 0:
                            amount = -amount # Flip positive debits to negative (spending)

                    # Extract Meta
                    category = clean_row.get('category', 'Uncategorized')
                    
                    # Fuzzy find Description
                    desc_candidates = ['description', 'merchant', 'transaction description', 'payee']
                    desc = 'Unknown'
                    for cand in desc_candidates:
                        if cand in clean_row:
                            desc = clean_row[cand]
                            break

                    # Fuzzy find Date
                    date_candidates = ['date', 'transaction date', 'posted date']
                    date = datetime.now().strftime('%Y-%m-%d')
                    for cand in date_candidates:
                        if cand in clean_row and clean_row[cand]:
                            date = clean_row[cand]
                            break
                    
                    if amount != 0.0:
                        transactions.append({
                            "date": date, 
                            "desc": desc, 
                            "amount": amount,
                            "category": category
                        })
        except Exception as e:
            logging.error(f"Error parsing {filepath}: {e}")
            pass
        
        return transactions

    def get_data(self):
        return self.accounts

    def transfer_funds(self, from_acc, to_acc, amount):
        return f"SIMULATED REAL TRANSFER: Moved ${amount} from {from_acc} to {to_acc}."