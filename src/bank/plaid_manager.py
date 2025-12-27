import os
import datetime
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

class PlaidConnector:
    def __init__(self):
        # Load credentials from environment variables for security
        self.client_id = os.getenv('PLAID_CLIENT_ID')
        self.secret = os.getenv('PLAID_SECRET')
        self.env = os.getenv('PLAID_ENV', 'sandbox')  # Default to sandbox

        if not self.client_id or not self.secret:
            raise ValueError("Missing PLAID_CLIENT_ID or PLAID_SECRET environment variables.")

        # Configure the client
        configuration = plaid.Configuration(
            host=plaid.Environment.Sandbox if self.env == 'sandbox' else plaid.Environment.Development,
            api_key={
                'clientId': self.client_id,
                'secret': self.secret,
            }
        )
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

    def create_link_token(self, user_id: str):
        """
        1. Generates a temporary token to initialize the Plaid Link UI (frontend).
        """
        request = LinkTokenCreateRequest(
            products=[Products('transactions')],
            client_name="Financial Architect AI",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(
                client_user_id=user_id
            )
        )
        response = self.client.link_token_create(request)
        return response['link_token']

    def exchange_public_token(self, public_token: str):
        """
        2. Swaps the temporary 'public_token' (from UI) for a permanent 'access_token'.
        Store this access_token securely (e.g., in your SQLite DB, not a file).
        """
        request = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        response = self.client.item_public_token_exchange(request)
        return response['access_token']

    def fetch_transactions(self, access_token: str, days_back: int = 30):
        """
        3. Fetches transactions for the last N days.
        """
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).date()
        end_date = datetime.datetime.now().date()

        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
            options=TransactionsGetRequestOptions(
                include_personal_finance_category=True # Use Plaid's AI categorization
            )
        )
        
        response = self.client.transactions_get(request)
        return response['transactions']

    def format_transactions_for_agent(self, transactions):
        """
        Helper to convert Plaid's complex JSON into the simple string format 
        your Financial Agent expects.
        """
        summary = []
        for t in transactions:
            amount = t['amount']
            # Plaid: positive amount = expense, negative = refund/deposit.
            # We invert this for intuitive reading if needed, or keep standard.
            # Let's label them clearly.
            flow = "OUTFLOW" if amount > 0 else "INFLOW"
            
            clean_date = t['date']
            merchant = t['merchant_name'] or t['name']
            category = t['personal_finance_category']['primary']
            
            summary.append(f"{clean_date} | {flow} | ${abs(amount):.2f} | {merchant} | {category}")
            
        return "\n".join(summary)