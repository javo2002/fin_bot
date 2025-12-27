import json
import os
from groq import Groq
from src.config import USE_REAL_LLM
from src.agent.prompts import SYSTEM_PROMPT

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "transfer_funds",
            "description": "Move money between accounts.",
            "parameters": {
                "type": "object",
                "properties": {
                    # CHANGE: Accept string to prevent "expected number" errors
                    "amount": {"type": "string", "description": "Amount to move (e.g. '50.00')"},
                    "from_account": {"type": "string", "enum": ["PNC Checking", "Capital One Checking", "Ally Savings"]},
                    "to_account": {"type": "string", "enum": ["PNC Checking", "Capital One Checking", "Ally Savings"]},
                    "reason": {"type": "string", "description": "Short reason for the move"}
                },
                "required": ["amount", "from_account", "to_account", "reason"]
            }
        }
    }
]

def run_financial_analysis(bank, user_query):
    financial_state = json.dumps(bank.get_data(), indent=2)

    print("\n[Debug] Financial State sent to AI:")
    print(financial_state)
    print("-----------------------------------")

    if GROQ_API_KEY:
        try:
            client = Groq(api_key=GROQ_API_KEY)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"USER QUERY: {user_query}\n\nFINANCIAL DATA:\n{financial_state}"}
            ]
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.1
            )
            
            message = response.choices[0].message
            tool_calls = message.tool_calls
            analysis_text = message.content
            
            if not analysis_text:
                analysis_text = "(The AI called a tool but provided no text summary.)"

            actions = []
            if tool_calls:
                for tool in tool_calls:
                    if tool.function.name == "transfer_funds":
                        args = json.loads(tool.function.arguments)
                        
                        # ROBUSTNESS: Handle string or number input
                        raw_amount = args.get("amount", 0)
                        try:
                            amount = float(raw_amount)
                        except ValueError:
                            amount = 0.0
                        
                        print(f"[Debug] AI attempted tool call: Move ${amount} ({args.get('reason')})")

                        if amount > 0:
                            actions.append({
                                "type": "TRANSFER",
                                "amount": amount,
                                "from": args.get("from_account"),
                                "to": args.get("to_account"),
                                "reason": args.get("reason")
                            })
                        else:
                            print(f"[Debug] 🚫 Filtered out $0.00 transfer.")

            return {
                "analysis": analysis_text,
                "proposed_actions": actions
            }

        except Exception as e:
            return {"error": f"Groq Connection Failed: {e}", "raw": ""}
    else:
        return {"error": "No API Key found."}