import streamlit as st
from src.bank.plaid_manager import PlaidConnector

def render_plaid_sidebar(db_manager):
    """
    Renders the Plaid connection status in the sidebar.
    Arguments:
        db_manager: Your existing SQLite database class to save the token.
    """
    st.sidebar.header("🔌 Bank Connection")
    
    # Check if we already have a token in DB (You need to implement get_access_token)
    # existing_token = db_manager.get_access_token(user_id="default")
    existing_token = None # Placeholder until DB is updated
    
    if existing_token:
        st.sidebar.success("✅ Bank Linked")
        if st.sidebar.button("Sync Now"):
            with st.spinner("Fetching latest transactions..."):
                pm = PlaidConnector()
                txns = pm.fetch_transactions(existing_token)
                st.session_state['latest_txns'] = txns
                st.sidebar.info(f"Synced {len(txns)} transactions!")
    else:
        st.sidebar.warning("⚠️ No Bank Linked")
        
        # INSTRUCTION FOR USER:
        # Since Streamlit + Plaid Link requires a dedicated frontend component,
        # for this local MVP, we will simulate the connection in Sandbox mode.
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔗 Connect (Sandbox Mode)")
        
        # This is a simulation for the MVP. 
        # In production, you would use a React component here.
        if st.sidebar.button("Simulate Bank Connection"):
            try:
                pm = PlaidConnector()
                # In a real app, we would generate a link_token here and open the JS modal.
                # For this Agent MVP, we will authenticate automatically using the
                # Plaid Sandbox 'custom_user' feature if available, or instruct the user.
                
                st.sidebar.info("In a full web app, this button opens the Plaid Pop-up.")
                st.sidebar.code("Plaid Link Token Generated!", language="bash")
                st.sidebar.markdown("**To finish setup:** Add your `PLAID_CLIENT_ID` and `SECRET` to your `.env` file.")
                
            except Exception as e:
                st.sidebar.error(f"Plaid Connection Error: {e}")