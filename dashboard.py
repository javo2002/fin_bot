import streamlit as st
import pandas as pd
import plotly.express as px
from src.bank.csv_loader import CSVBank
from src.agent.core import run_financial_analysis
from src.notifications.telegram_service import TelegramNotifier
from src.utils.calendar_generator import create_transfer_reminders
from src.database import get_net_worth_history, get_all_transactions
from src.config import PLAID_CLIENT_ID

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Financial Architect", page_icon="▪️", layout="wide")
notifier = TelegramNotifier()

# Custom CSS for Premium UI
st.markdown("""
<style>
    /* Global Clean Dark Theme */
    .stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Inter', sans-serif; }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: #1E2329;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 15px;
    }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700; color: #FFFFFF !important; }
    div[data-testid="stMetricLabel"] { color: #8B949E !important; font-size: 0.9rem; }

    /* Buttons */
    div.stButton > button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 6px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
    }
    div.stButton > button:hover {
        background-color: #E0E0E0 !important;
        box-shadow: 0 4px 12px rgba(255,255,255,0.1);
    }

    /* Chat Styling */
    .stChatMessage { background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; }
    
    /* Tables */
    div[data-testid="stDataFrame"] { border: 1px solid #30363D; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA LOADING ---
if 'bank' not in st.session_state:
    if pd.io.common.file_exists("temp_pnc.csv"):
        st.session_state.bank = CSVBank("temp_pnc.csv", "temp_capone.csv")
    else:
        st.session_state.bank = None

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("Financial Architect")
    st.caption("v3.2 • Database Inspector")
    st.markdown("---")
    
    if PLAID_CLIENT_ID:
        st.success("🔌 Plaid Active")
    else:
        st.info("📂 Manual Mode")
        
    with st.expander("📥 Upload Data", expanded=True):
        uploaded_pnc = st.file_uploader("PNC CSV", type=["csv"])
        uploaded_capone = st.file_uploader("Capital One CSV", type=["csv"])
        
        if uploaded_pnc and uploaded_capone:
            with open("temp_pnc.csv", "wb") as f: f.write(uploaded_pnc.getbuffer())
            with open("temp_capone.csv", "wb") as f: f.write(uploaded_capone.getbuffer())
            st.session_state.bank = CSVBank("temp_pnc.csv", "temp_capone.csv")
            st.rerun()

    st.markdown("---")
    income = st.number_input("Monthly Income", value=6600, step=100)
    tax_pct = st.slider("Tax Rate %", 20, 35, 25)

# --- 4. MAIN APP ---
if st.session_state.bank:
    bank = st.session_state.bank
    data = bank.get_data()
    
    # Extract Data
    pnc_bal = data["PNC Checking"]["balance"]
    ally_bal = data["Ally Savings"]["balance"]
    cap_bal = data["Capital One Checking"]["balance"]
    
    # Top KPIS
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Safety Net (PNC)", f"${pnc_bal:,.2f}", f"${pnc_bal - 4000:,.0f}")
    c2.metric("Fun/Bills (CapOne)", f"${cap_bal:,.2f}", "Watch Bills")
    c3.metric("Car Fund", f"${ally_bal:,.2f}", f"${ally_bal - 9000:,.0f}")
    c4.metric("Tax Target", f"${income * (tax_pct/100):,.0f}", "Monthly")

    st.markdown("---")

    # TABS
    tabs = st.tabs(["🧠 Strategy", "📊 Visuals", "💾 DB Inspector", "💬 Chat"])

    # --- TAB 1: STRATEGY ---
    with tabs[0]:
        col_main, col_side = st.columns([2, 1])
        with col_main:
            if st.button("Run Smart Audit", type="primary", use_container_width=True):
                with st.spinner("Analyzing transaction dates & cashflow..."):
                    ctx = f"Income: ${income}. Tax: {tax_pct}%. Contractor."
                    st.session_state.analysis = run_financial_analysis(bank, f"Audit my finances. {ctx}")
            
            if "analysis" in st.session_state and st.session_state.analysis:
                res = st.session_state.analysis
                # Render Clean Markdown
                st.markdown(res.get("analysis", "No text generated."))
        
        with col_side:
            st.subheader("Moves")
            if "analysis" in st.session_state:
                moves = st.session_state.analysis.get("proposed_actions", [])
                if not moves:
                    st.info("✅ No transfers needed.")
                for m in moves:
                    st.warning(f"**MOVE ${m['amount']:,.2f}**\n\nTo: {m['to']}\n\n_{m['reason']}_")
            
            if notifier.is_configured():
                if st.button("📲 Send to Telegram"):
                    if "analysis" in st.session_state:
                        res = st.session_state.analysis
                        st.success(notifier.send_report(res.get("analysis", ""), res.get("proposed_actions", [])))
                    else:
                        st.warning("Run analysis first")

    # --- TAB 2: VISUALS ---
    with tabs[1]:
        st.subheader("Cash Flow Breakdown")
        
        # Prepare Data
        pnc_tx = data["PNC Checking"]["transactions"]
        cap_tx = data["Capital One Checking"]["transactions"]
        
        col_v1, col_v2 = st.columns(2)
        
        # Helper for Charts
        def render_pie(txs, title, color_scale):
            if not txs:
                st.warning(f"No data for {title}")
                return
            
            df = pd.DataFrame(txs)
            # Ensure Amount/Category exist
            if 'amount' not in df.columns: 
                st.error("Missing 'amount' column")
                return
            
            # Filter Spending (Negative amounts usually)
            # Adjust this logic if your CSV has positive amounts for spending
            spending = df.copy()
            spending['amount'] = spending['amount'].abs() # Treat all flow as magnitude
            
            fig = px.pie(spending, values='amount', names='category', title=title, 
                         color_discrete_sequence=getattr(px.colors.sequential, color_scale),
                         hole=0.4)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)

        with col_v1:
            render_pie(pnc_tx, "PNC (Safety Net)", "Blues_r")
        with col_v2:
            render_pie(cap_tx, "Capital One (Fun)", "Reds_r")

    # --- TAB 3: DB INSPECTOR (UPDATED) ---
    with tabs[2]:
        st.subheader("💾 Database Inspector")
        st.markdown("Raw data stored in `financial_memory.db`, split by account.")
        
        all_txs = get_all_transactions()
        
        if not all_txs.empty:
            # Create sub-tabs for each bank account
            # We get unique account names from the DB
            accounts = all_txs['account'].unique()
            # Add an 'All' tab
            tabs_list = ["All"] + list(accounts)
            db_tabs = st.tabs(tabs_list)
            
            # Filter Logic
            search = st.text_input("🔍 Search Transactions (e.g. 'Netflix')", key="db_search")
            
            # 1. ALL Tab
            with db_tabs[0]:
                view_df = all_txs
                if search:
                    view_df = view_df[view_df['description'].str.contains(search, case=False, na=False)]
                
                # Stats for All
                k1, k2, k3 = st.columns(3)
                k1.metric("Total Records", len(view_df))
                k2.metric("Date Range", f"{view_df['date'].min()} to {view_df['date'].max()}")
                k3.metric("Total Volume", f"${view_df['amount'].abs().sum():,.2f}")
                
                st.dataframe(view_df, use_container_width=True)

            # 2. Individual Account Tabs
            for i, acc_name in enumerate(accounts):
                with db_tabs[i+1]:
                    # Filter for specific account
                    acc_df = all_txs[all_txs['account'] == acc_name]
                    
                    if search:
                        acc_df = acc_df[acc_df['description'].str.contains(search, case=False, na=False)]
                    
                    # Stats for Account
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Records", len(acc_df))
                    if not acc_df.empty:
                        k2.metric("Latest", acc_df['date'].max())
                        k3.metric("Volume", f"${acc_df['amount'].abs().sum():,.2f}")
                    
                    st.dataframe(acc_df, use_container_width=True)

        else:
            st.info("Database is empty. Upload CSVs to populate.")

    # --- TAB 4: CHAT ---
    with tabs[3]:
        st.subheader("💬 Chat with Architect")
        
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Render History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Input
        if prompt := st.chat_input("Ask about your finances..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    ctx = f"Income: ${income}. Tax: {tax_pct}%. Contractor."
                    res = run_financial_analysis(bank, f"{prompt} Context: {ctx}")
                    reply = res.get("analysis", "I'm not sure.")
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})

else:
    st.title("Financial Architect")
    st.info("👈 Upload your CSV files in the sidebar to begin.")