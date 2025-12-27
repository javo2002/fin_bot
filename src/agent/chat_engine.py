import os
import datetime
from typing import List, Dict

# Import your modules
from src.logic.financial_math import TaxGuardrail, FinancialProfile
from src.agent.advisor_prompt import build_prompt

# Mocking the Groq client for the MVP structure
# In production, import your actual Groq client wrapper here
try:
    from groq import Groq
except ImportError:
    Groq = None

class FinancialChatEngine:
    def __init__(self, transactions: List[str] = None):
        """
        Args:
            transactions: List of strings formatted as "Date | Amount | Merchant"
                          (Output from PlaidConnector.format_transactions_for_agent)
        """
        self.transactions = transactions or []
        
        # Initialize the User's Profile (Hardcoded for MVP, fetch from DB later)
        self.user_profile = FinancialProfile(
            annual_income=80_000,
            is_contractor=True,
            filing_status="single"
        )
        
        # Initialize LLM Client
        api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key) if api_key and Groq else None

    def _analyze_intent_and_math(self, user_message: str) -> Dict:
        """
        Before asking the LLM, run the Python Math Guardrails based on keywords.
        """
        analysis = {}
        msg_lower = user_message.lower()

        # 1. Monthly Income / Tax Check
        # Run this context on every turn so the LLM remembers the 30% rule
        monthly_gross = self.user_profile.annual_income / 12
        tax_calc = TaxGuardrail.calculate_contractor_net(monthly_gross)
        analysis.update(tax_calc)

        # 2. Car Buying Intent
        if any(w in msg_lower for w in ["car", "tesla", "ev", "vehicle", "buy"]):
            # Extract price if mentioned (simple heuristic for MVP)
            # Defaulting to 45k if not found to trigger the check
            price = 45000 
            ev_check = TaxGuardrail.check_ev_credit_eligibility(
                car_price=price, 
                adjusted_gross_income=self.user_profile.annual_income
            )
            analysis['ev_status'] = ev_check
            
        return analysis

    def process_message(self, user_message: str, chat_history: List[Dict]) -> str:
        """
        Main pipeline: User Input -> Math Check -> System Prompt -> LLM -> Response
        """
        if not self.client:
            return "⚠️ Groq API Key missing. Please set GROQ_API_KEY in .env."

        # 1. Run Math Guardrails
        math_context = self._analyze_intent_and_math(user_message)

        # 2. Format Transaction Data (Last 5 for context, or summary)
        txn_summary = "\n".join(self.transactions[:10]) if self.transactions else "No recent transactions linked."

        # 3. Build the System Prompt
        system_instruction = build_prompt(txn_summary, math_context)

        # 4. Call LLM
        # We construct the messages array with the specialized System Prompt
        messages = [
            {"role": "system", "content": system_instruction}
        ]
        
        # Append limited history to keep context window clean
        messages.extend(chat_history[-4:]) 
        
        messages.append({"role": "user", "content": user_message})

        try:
            completion = self.client.chat.completions.create(
                model="llama3-70b-8192", # High intelligence model for advice
                messages=messages,
                temperature=0.5, # Lower temperature for stricter financial advice
                max_tokens=800
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"⚠️ Error reaching Agent: {str(e)}"