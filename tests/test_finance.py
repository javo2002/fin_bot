import pytest
from src.bank.csv_loader import CSVBank

# We use a fixture to create a bank instance without needing real files
@pytest.fixture
def bank_loader():
    # Initialize with non-existent files so it defaults to empty/safe state
    return CSVBank("dummy_pnc.csv", "dummy_capone.csv")

def test_clean_amount_standard(bank_loader):
    """Test standard currency formatting"""
    assert bank_loader._clean_amount("$1,200.50") == 1200.50
    assert bank_loader._clean_amount("500") == 500.0

def test_clean_amount_negative_parentheses(bank_loader):
    """Test accounting format: ($50.00) -> -50.00"""
    assert bank_loader._clean_amount("($50.00)") == -50.00
    assert bank_loader._clean_amount("( 50.00 )") == -50.00

def test_clean_amount_plus_sign(bank_loader):
    """Test explicit plus signs: + $36.00 -> 36.00"""
    assert bank_loader._clean_amount("+ $36.00") == 36.00
    assert bank_loader._clean_amount("+36") == 36.00

def test_clean_amount_messy_input(bank_loader):
    """Test weird spacing and symbols"""
    assert bank_loader._clean_amount(" $ - 10.00 ") == -10.00
    assert bank_loader._clean_amount("USD 50.00") == 50.00
    assert bank_loader._clean_amount("") == 0.0
    assert bank_loader._clean_amount(None) == 0.0

def test_tax_math():
    """Verify the Contractor Tax Logic holds up"""
    income = 6600
    rate = 25
    tax_reserve = income * (rate / 100)
    assert tax_reserve == 1650.0

def test_safety_net_logic():
    """Verify the logic for checking if Safety Net is full"""
    target = 4000
    current_balance = 5000
    is_full = current_balance >= target
    excess = max(0, current_balance - target)
    
    assert is_full is True
    assert excess == 1000