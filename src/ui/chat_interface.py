import streamlit as st
from src.agent.chat_engine import FinancialChatEngine

def render_advisor_chat():
    st.header("💬 Financial Architect Agent")
    
    # 1. Initialize Session State for Chat History
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": "I am online. I see you are planning for 2026. How can I help with the EV purchase or your tax strategy?"}
        ]

    # 2. Display Chat History
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 3. Handle New User Input
    if prompt := st.chat_input("Ask about affordability, taxes, or allocation..."):
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state["messages"].append({"role": "user", "content": prompt})

        # 4. Generate Response
        with st.chat_message("assistant"):
            with st.spinner("Calculating tax implications..."):
                
                # Retrieve transactions from the Plaid step (Phase 2)
                # Ensure they are in list-of-strings format
                raw_txns = st.session_state.get('latest_txns', [])
                formatted_txns = []
                
                # Quick formatting if raw Plaid data exists
                if raw_txns and isinstance(raw_txns[0], dict):
                    # Simple formatter if Plaid object, otherwise assume string
                    formatted_txns = [f"{t['date']} | ${t['amount']} | {t['name']}" for t in raw_txns]
                
                # Initialize Engine
                engine = FinancialChatEngine(transactions=formatted_txns)
                
                # Get response
                response = engine.process_message(
                    user_message=prompt, 
                    chat_history=st.session_state["messages"]
                )
                
                st.markdown(response)
        
        # Save assistant response to history
        st.session_state["messages"].append({"role": "assistant", "content": response})