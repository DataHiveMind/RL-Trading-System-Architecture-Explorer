import pytest
import numpy as np
from qts_core.portfolio.ledger import PortfolioLedger

def test_ledger_initialization():
    """Test that the ledger starts with correct initial values."""
    ledger = PortfolioLedger(initial_capital=100000.0, transaction_fee_pct=0.001)
    
    assert ledger.cash == 100000.0
    assert ledger.positions["asset"] == 0.0
    assert ledger.total_equity == 100000.0
    assert ledger.max_drawdown == 0.0

def test_execute_trade_long():
    """Test executing a 50% long position."""
    ledger = PortfolioLedger(initial_capital=100000.0, transaction_fee_pct=0.001)
    
    # Target 50% weight at price $100
    # Expected position: $50,000 / $100 = 500 shares
    # Trade value: $50,000. Fee: $50,000 * 0.001 = $50
    step_return, step_pnl = ledger.execute_trade(current_price=100.0, target_weight=0.5)
    
    assert ledger.positions["asset"] == 500.0
    assert ledger.cash == 49950.0  # 100k - 50k - 50 fee
    assert ledger.total_equity == 99950.0 # 49950 cash + 50000 position
    assert step_pnl == -50.0 # Only lost the fee on the initial step

def test_drawdown_tracking():
    """Test that max drawdown is calculated correctly during losses."""
    ledger = PortfolioLedger(initial_capital=100000.0, transaction_fee_pct=0.0) # Ignore fees for simplicity
    
    # Buy 100% long at $100 (1000 shares)
    ledger.execute_trade(current_price=100.0, target_weight=1.0)
    
    # Hold position, price drops to $80 (Equity becomes $80,000)
    ledger.execute_trade(current_price=80.0, target_weight=1.0)
    
    assert ledger.total_equity == 80000.0
    assert ledger.peak_equity == 100000.0
    assert ledger.max_drawdown == 0.20 # 20% drop