import dataclasses
from typing import Dict, Optional, Tuple

@dataclasses.dataclass
class FinancialProfile:
    annual_income: float
    is_contractor: bool
    filing_status: str = "single"
    state_tax_rate: float = 0.05  # Approximate, adjust for your state

class TaxGuardrail:
    """
    Hard-coded logic to prevent LLM hallucinations regarding 
    Contractor Taxes and Tax Credits.
    """
    
    @staticmethod
    def calculate_contractor_net(gross_deposit: float) -> Dict[str, float]:
        """
        Takes a raw deposit amount and splits it according to the '30% Rule'
        for 1099 contractors.
        """
        # Self-employment tax (15.3%) + Income Tax Buffer (~15%)
        # standard safe rule for 1099 is 30% set aside
        tax_reserve = gross_deposit * 0.30
        safe_to_spend = gross_deposit - tax_reserve
        
        return {
            "gross": gross_deposit,
            "tax_vault_contribution": tax_reserve,
            "real_disposable": safe_to_spend,
            "warning": "REMINDER: Do not spend the 'tax_vault' portion. Transfer to HYSA immediately."
        }

    @staticmethod
    def check_ev_credit_eligibility(
        car_price: float, 
        adjusted_gross_income: float, 
        is_used: bool = True
    ) -> Dict[str, any]:
        """
        Checks eligibility for Federal Used EV Tax Credit (IRC 25E).
        """
        # 2024/2025 Limits for Used EVs
        PRICE_CAP = 25_000
        INCOME_CAP_SINGLE = 75_000
        CREDIT_MAX = 4_000
        
        eligible = True
        reasons = []
        
        if is_used:
            if car_price > PRICE_CAP:
                eligible = False
                reasons.append(f"Price ${car_price:,} exceeds the ${PRICE_CAP:,} limit for used EV credit.")
            
            if adjusted_gross_income > INCOME_CAP_SINGLE:
                eligible = False
                reasons.append(f"Income ${adjusted_gross_income:,} exceeds the ${INCOME_CAP_SINGLE:,} AGI limit.")
        
        return {
            "eligible": eligible,
            "credit_estimate": CREDIT_MAX if eligible else 0,
            "disqualifiers": reasons,
            "advice": "Consider contributing to a Solo 401k to lower AGI below $75k." if adjusted_gross_income > INCOME_CAP_SINGLE else None
        }

    @staticmethod
    def analyze_car_affordability(monthly_net: float, car_payment: float, insurance: float, charging: float) -> str:
        """
        Standard affordability check: Total car costs should not exceed 15% of net.
        """
        total_car_cost = car_payment + insurance + charging
        ratio = (total_car_cost / monthly_net) * 100
        
        status = "SAFE"
        if ratio > 20:
            status = "DANGEROUS"
        elif ratio > 15:
            status = "CAUTION"
            
        return f"Car Cost: ${total_car_cost}/mo ({ratio:.1f}% of net). Status: {status}. (Goal: <15%)"

# --- Example Usage for Testing ---
if __name__ == "__main__":
    # Test your 2026 Scenario
    monthly_gross = 6666.00  # $80k / 12
    tax_calc = TaxGuardrail.calculate_contractor_net(monthly_gross)
    
    print(f"--- Monthly Paycheck Analysis ---")
    print(f"Gross: ${tax_calc['gross']}")
    print(f"Safe to Spend: ${tax_calc['real_disposable']}")
    print(f"Tax Vault: ${tax_calc['tax_vault_contribution']}")
    
    # Test EV Scenario ($45k car, $80k income)
    ev_check = TaxGuardrail.check_ev_credit_eligibility(car_price=45000, adjusted_gross_income=80000)
    print(f"\n--- EV Credit Check ---")
    print(f"Eligible: {ev_check['eligible']}")
    print(f"Issues: {ev_check['disqualifiers']}")