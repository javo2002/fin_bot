import webbrowser

# Replace these with the direct "Export Data" URLs for your banks if possible
# Otherwise, just use the login page URLs
PNC_URL = "https://www.pnc.com/en/personal-banking/banking/online-banking.html"
CAPONE_URL = "https://verified.capitalone.com/auth/signin"

print("🚀 Opening Bank Portals...")
webbrowser.open(PNC_URL)
webbrowser.open(CAPONE_URL)
print("✅ Tabs opened. Log in and download your CSVs!")