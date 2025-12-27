import os
import json
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from flask import Flask, render_template_string, request, jsonify
from src.config import PLAID_CLIENT_ID, PLAID_SECRET, PLAID_ENV

app = Flask(__name__)

# 1. Initialize Plaid Client
configuration = plaid.Configuration(
    host=getattr(plaid.Environment, PLAID_ENV.capitalize()),
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET,
    }
)
api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# HTML Template for the Login Page
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
<title>Connect Bank</title>
<style>
    body { font-family: sans-serif; background: #111; color: #fff; text-align: center; padding-top: 50px; }
    button { background: #fff; color: #000; border: none; padding: 15px 30px; font-size: 18px; cursor: pointer; font-weight: bold; }
</style>
</head>
<body>
    <h1>Financial Architect Setup</h1>
    <p>Click below to securely connect your bank via Plaid.</p>
    <button id="link-button">Connect Bank Account</button>
    <div id="result" style="margin-top: 20px;"></div>

    <script type="text/javascript">
    document.getElementById('link-button').onclick = async function() {
        // 1. Get Link Token from Python
        const response = await fetch('/create_link_token', { method: 'POST' });
        const data = await response.json();
        
        // 2. Open Plaid Link
        const handler = Plaid.create({
            token: data.link_token,
            onSuccess: async function(public_token, metadata) {
                // 3. Send Public Token to Python to exchange for Access Token
                document.getElementById('result').innerText = 'Processing...';
                const exchange = await fetch('/exchange_public_token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ public_token: public_token })
                });
                const result = await exchange.json();
                document.getElementById('result').innerText = '✅ Success! Token saved. You can close this tab.';
            },
            onExit: function(err, metadata) {
                if (err) console.log(err);
            }
        });
        handler.open();
    };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/create_link_token', methods=['POST'])
def create_link_token():
    try:
        request = LinkTokenCreateRequest(
            products=[Products('transactions')],
            client_name="Financial Architect",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(client_user_id='user_123')
        )
        response = client.link_token_create(request)
        return jsonify(response.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/exchange_public_token', methods=['POST'])
def exchange_public_token():
    public_token = request.json['public_token']
    try:
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        access_token = exchange_response['access_token']
        
        # SAVE TOKEN TO FILE
        token_data = {}
        if os.path.exists("plaid_tokens.json"):
            with open("plaid_tokens.json", "r") as f:
                token_data = json.load(f)
        
        # Append new token (using item_id as key to avoid overwriting if multiple banks)
        item_id = exchange_response['item_id']
        token_data[item_id] = access_token
        
        with open("plaid_tokens.json", "w") as f:
            json.dump(token_data, f)
            
        return jsonify({'status': 'success', 'item_id': item_id})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("🚀 Server running! Go to http://localhost:5000 to connect your bank.")
    app.run(port=5000)