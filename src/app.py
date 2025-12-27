import streamlit as st
import os
import sys
import pandas as pd
import altair as alt
from dotenv import load_dotenv

# --- 1. SETUP ENVIRONMENT & PATHS (Must be first) ---
current_dir = os.path.dirname(os.path.abspath(__file__)) # path to src/
project_root = os.path.dirname(current_dir)            # path to project root
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# FIX: Force the new supported Groq model explicitly at the top level
# We set this BEFORE loading dotenv to ensure it takes precedence over any cached .env values
new_model = "llama-3.3-70b-versatile"
os.environ["GROQ_MODEL"] = new_model
os.environ["GROQ_LLM_MODEL"] = new_model # specific alias sometimes used

# Load Environment Variables
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)
if not os.getenv("GROQ_API_KEY"):
    load_dotenv()

# --- 2. IMPORT LOCAL MODULES (After env vars are set) ---
from src.ui.plaid_widget import render_plaid_sidebar
from src.ui.chat_interface import render_advisor_chat
from src.logic.financial_math import TaxGuardrail, FinancialProfile

def load_csv_data(uploaded_file):
    """
    Simple CSV parser to standardize bank exports for the Agent.
    Assumes columns like 'Date', 'Description', 'Amount'.
    """
    try:
        df = pd.read_csv(uploaded_file)
        # normalize column names to lower case
        df.columns = df.columns.str.lower()
        
        # Basic field mapping (adjust based on your bank's specific csv format)
        date_col = next((col for col in df.columns if 'date' in col), 'date')
        desc_col = next((col for col in df.columns if 'desc' in col or 'merchant' in col), 'description')
        amt_col = next((col for col in df.columns if 'amount' in col), 'amount')
        
        # Ensure amount is numeric for visuals
        df[amt_col] = pd.to_numeric(df[amt_col], errors='coerce').fillna(0.0)
        
        # Convert to list of strings for the Agent context
        transactions = []
        for _, row in df.iterrows():
            date_val = row[date_col] if pd.notna(row[date_col]) else "Unknown"
            amt_val = row[amt_col]
            desc_val = row[desc_col] if pd.notna(row[desc_col]) else "Unknown"
            transactions.append(f"{date_val} | ${amt_val} | {desc_val}")
            
        return transactions, df
    except Exception as e:
        st.error(f"Error reading CSV {uploaded_file.name}: {e}")
        return [], None

def render_bank_targets(profile: FinancialProfile):
    """
    Visualizes the 3-Bank Strategy targets.
    """
    st.subheader("🏦 Bank Balances vs. Targets")
    
    col1, col2, col3 = st.columns(3)
    
    # --- 1. PNC (Safety Net & Bills) ---
    with col1:
        st.markdown("### 📘 PNC (Fixed)")
        st.caption("Rent, Bills, Safety Net")
        
        # MOCK DATA (Replace with real Plaid/CSV sum later)
        current_pnc = 2500.0 
        target_pnc = 4000.0  # User Goal: $4k Safety Net
        
        st.metric(
            "Current Balance", 
            f"${current_pnc:,.0f}", 
            delta=f"${current_pnc - target_pnc:,.0f} to goal",
            delta_color="normal" # Red if negative is good context here
        )
        # Progress bar (0.0 to 1.0)
        progress = min(current_pnc / target_pnc, 1.0)
        st.progress(progress)
        st.caption(f"🎯 Goal: ${target_pnc:,.0f} (Safety Net)")

    # --- 2. Ally (Tax Vault) ---
    with col2:
        st.markdown("### 💜 Ally (Tax Vault)")
        st.caption("Do NOT Touch")
        
        # Goal: ~30% of income buffer. Let's say 3 months of tax saving (~$2k * 3)
        monthly_tax_need = (profile.annual_income / 12) * 0.30
        target_ally = monthly_tax_need * 3 
        current_ally = 4500.0 # Mock
        
        st.metric("Current Balance", f"${current_ally:,.0f}")
        st.progress(min(current_ally / target_ally, 1.0))
        st.caption(f"🎯 Goal: ${target_ally:,.0f} (3mo Buffer)")

    # --- 3. Capital One (Fun Money) ---
    with col3:
        st.markdown("### 💳 Capital One (Fun)")
        st.caption("Guilt-Free Spending")
        
        current_cap1 = 120.0 # Mock
        target_cap1 = 500.0  # User Goal: $500 buffer
        
        st.metric("Current Balance", f"${current_cap1:,.0f}", delta=f"${current_cap1 - target_cap1:,.0f}")
        st.progress(min(current_cap1 / target_cap1, 1.0))
        st.caption(f"🎯 Goal: ${target_cap1:,.0f} (Refill)")

def render_paycheck_splitter(profile: FinancialProfile):
    """
    Calculator to tell user how to split their specific paycheck.
    """
    st.markdown("---")
    st.subheader("💸 Incoming Paycheck Splitter")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        paycheck = st.number_input("Enter Check Amount:", value=6666.0, step=100.0)
    
    with c2:
        if paycheck > 0:
            # 30% to Taxes
            tax_cut = paycheck * 0.30
            # Estimate fixed costs (Rent ~1300 + Bills) - adjust logic as needed
            fixed_needs = 2000 
            # Remainder is Fun
            fun_money = paycheck - tax_cut - fixed_needs
            
            st.info(f"""
            **Action Plan for ${paycheck:,.0f}:**
            1. 💜 **Ally:** Transfer **${tax_cut:,.0f}** immediately. (Tax Stash)
            2. 📘 **PNC:** Keep **${fixed_needs:,.0f}** for bills/rent.
            3. 💳 **Capital One:** Move **${fun_money:,.0f}** for spending.
            """)

def render_transaction_db():
    """
    Searchable DB view.
    """
    st.subheader("🔎 Database Entries")
    
    if 'latest_txns_df' in st.session_state and st.session_state['latest_txns_df'] is not None:
        df = st.session_state['latest_txns_df']
        
        # Search Bar
        search = st.text_input("Search (e.g., 'Netflix', 'Rent')", key="txn_search")
        
        display_df = df
        if search:
            # Filter rows where any column contains the search term
            mask = df.apply(lambda x: x.astype(str).str.contains(search, case=False)).any(axis=1)
            display_df = df[mask]
        
        st.dataframe(
            display_df, 
            use_container_width=True, 
            hide_index=True
        )
        st.caption(f"Showing {len(display_df)} transactions.")
    else:
        st.info("📂 Upload CSVs in the sidebar to populate the database.")

def render_visuals_page():
    """
    Charts for spending/subscriptions.
    """
    st.subheader("📊 Money Maps")
    
    if 'latest_txns_df' in st.session_state:
        df = st.session_state['latest_txns_df']
        # Check if we have data
        if df is not None and not df.empty:
            # Attempt to find amount column
            amt_col = next((c for c in df.columns if 'amount' in c), None)
            desc_col = next((c for c in df.columns if 'desc' in c), None)
            
            if amt_col and desc_col:
                # 1. Top Spending by Description (Simple Bar)
                st.markdown("**Top Transactions**")
                chart_data = df.nlargest(10, amt_col)[[desc_col, amt_col]]
                st.bar_chart(chart_data.set_index(desc_col))
            else:
                st.warning("Could not identify Amount/Description columns for charting.")
        else:
            st.warning("No data found.")
    else:
        st.info("Waiting for data...")

def main():
    st.set_page_config(
        page_title="Financial Architect AI",
        page_icon="🏦",
        layout="wide"
    )

    # Inject model into session state as a backup for any UI components checking it
    if "groq_model" not in st.session_state:
        st.session_state["groq_model"] = os.environ["GROQ_MODEL"]

    # --- Sidebar ---
    with st.sidebar:
        st.title("⚙️ Data Source")
        
        # DEBUG/RESET: Button to clear cache if the old model persists
        if st.button("🔄 Reset App & Cache"):
            st.cache_resource.clear()
            st.rerun()
        
        st.caption(f"🤖 Model: {os.environ.get('GROQ_MODEL')}") # Visual confirmation

        data_source = st.radio("Select Input:", ["🔌 Connect Banks", "📂 Upload CSVs"])
        
        if data_source == "📂 Upload CSVs":
            st.info("Upload exports from **PNC, Capital One, and Ally**.")
            uploaded_files = st.file_uploader(
                "Drop all CSVs here", 
                type=['csv'], 
                accept_multiple_files=True
            )
            
            if uploaded_files:
                all_txns = []
                all_dfs = []
                for file in uploaded_files:
                    txns, df = load_csv_data(file)
                    all_txns.extend(txns)
                    if df is not None:
                        all_dfs.append(df)
                
                # Merge all DFs for the visualizer
                if all_dfs:
                    full_df = pd.concat(all_dfs, ignore_index=True)
                    st.session_state['latest_txns_df'] = full_df
                
                st.session_state['latest_txns'] = all_txns
                st.success(f"Merged {len(all_txns)} transactions.")
                
        else:
            render_plaid_sidebar(db_manager=None)

        st.divider()
        
        # Setup Guide in Sidebar
        with st.expander("🛠️ 3-Bank Setup Guide"):
            st.markdown("""
            1. **Income -> PNC:** Set Direct Deposit here.
            2. **Auto-Transfer:** Schedule 30% to Ally on payday.
            3. **Spending:** Move allowance to CapOne.
            """)

    # --- Main Content ---
    
    # 1. Define Profile
    user_profile = FinancialProfile(annual_income=80_000, is_contractor=True, state_tax_rate=0.066)
    
    # 2. Main Dashboard Tabs
    tab1, tab2, tab3 = st.tabs(["🏦 Dashboard", "🔎 Database", "📊 Visuals"])
    
    with tab1:
        st.markdown("## 🦅 Your Financial Control Center")
        render_bank_targets(user_profile)
        render_paycheck_splitter(user_profile)
        
    with tab2:
        render_transaction_db()
        
    with tab3:
        render_visuals_page()
    
    # 3. Chat Interface (Always visible at bottom or integrated)
    st.markdown("---")
    render_advisor_chat()

if __name__ == "__main__":
    main()