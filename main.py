import os
from src.bank.mock import MockBank
from src.bank.csv_loader import CSVBank
from src.agent.core import run_financial_analysis

def main():
    print("💰 Financial Agent Started...")
    print("--------------------------------")

    # INTELLIGENT BANK SWITCHING
    # If pnc.csv exists, we assume user wants to use Real Data mode.
    if os.path.exists("pnc.csv") or os.path.exists("capone.csv"):
        print("[System] 📂 Real Data Detected (CSV Files Found). Loading...")
        bank = CSVBank("pnc.csv", "capone.csv")
    else:
        print("[System] 🧪 No CSVs found. Using Mock Data for Simulation.")
        bank = MockBank()
    
    # Run the Agent (The Brain)
    query = "Analyze my real spending and apply the 3-bucket strategy."
    plan = run_financial_analysis(bank, query)

    # Display Results
    if "error" in plan:
        print(f"❌ Error: {plan['error']}")
        return

    print(f"\n🧠 AI Analysis: {plan.get('analysis', 'No analysis provided')}")
    
    actions = plan.get("proposed_actions", [])
    if not actions:
        print("\n✅ No actions needed. Your finances are optimized!")
        return

    # Execute Actions (The Hands)
    print(f"\n📋 Proposed Actions ({len(actions)}):")
    for i, action in enumerate(actions, 1):
        print(f"   {i}. Move ${action['amount']} :: {action['from']} -> {action['to']}")
        print(f"      Reason: {action['reason']}")

    confirm = input("\n👉 Do you want to execute these transfers? (yes/no): ")
    if confirm.lower() == "yes":
        print("\n🚀 Executing Transfers...")
        for action in actions:
            result = bank.transfer_funds(action['from'], action['to'], action['amount'])
            print(f"   - {result}")
    else:
        print("\n🛑 Operation Cancelled.")

if __name__ == "__main__":
    main()