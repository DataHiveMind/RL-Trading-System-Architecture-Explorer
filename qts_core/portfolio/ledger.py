import numpy as np
from typing import Dict, Tuple

class PortfolioLedger:
    """
    A strict ledger for tracking portfolio state independently of the RL environment.
    This ensures that PnL calculations, transaction costs, and equity curves
    are deterministic and can be unit-tested without needing a neural network.
    """

    def __init__(self, initial_capital: float = 100000.0, transaction_fee_pct: float = 0.001):
        """
        Initializes the portfolio ledger.
        
        Args:
            initial_capital: Starting cash balance.
            transaction_fee_pct: Cost per transaction as a percentage (e.g., 0.001 = 0.1%).
        """
        self.initial_capital = initial_capital
        self.transaction_fee_pct = transaction_fee_pct
        self.reset()

    def reset(self) -> None:
        """Resets the ledger to its initial state for a new episode."""
        self.cash = self.initial_capital
        self.positions: Dict[str, float] = {"asset": 0.0}
        self.total_equity = self.initial_capital
        
        # Telemetry tracking for the dashboard
        self.equity_curve = [self.initial_capital]
        self.peak_equity = self.initial_capital
        self.max_drawdown = 0.0

    def execute_trade(self, current_price: float, target_weight: float) -> Tuple[float, float]:
        """
        Executes a trade to reach a target portfolio weight.
        
        Args:
            current_price: The current market price of the asset.
            target_weight: Desired portfolio allocation [-1.0 (short) to 1.0 (long)].
            
        Returns:
            Tuple of (Reward, Step PnL).
        """
        # 1. Calculate the target value of the position based on total equity
        # Clip weight to strict risk limits [-1, 1]
        target_weight = np.clip(target_weight, -1.0, 1.0)
        target_position_value = self.total_equity * target_weight
        
        # 2. Calculate the target quantity of shares/contracts
        target_quantity = target_position_value / current_price
        
        # 3. Calculate trade delta (how much we need to buy/sell)
        current_quantity = self.positions["asset"]
        trade_quantity = target_quantity - current_quantity
        
        # 4. Apply transaction costs (slippage/commissions)
        trade_value = abs(trade_quantity * current_price)
        transaction_cost = trade_value * self.transaction_fee_pct
        
        # 5. Update cash and positions
        self.cash -= (trade_quantity * current_price) + transaction_cost
        self.positions["asset"] = target_quantity
        
        # 6. Calculate new equity and update risk metrics
        previous_equity = self.total_equity
        self.total_equity = self.cash + (self.positions["asset"] * current_price)
        
        self.equity_curve.append(self.total_equity)
        self._update_drawdown()
        
        # 7. Calculate Step Reward (Log Return of the step, minus transaction costs)
        # Using log returns provides a symmetric reward signal for the RL agent
        if previous_equity > 0:
            step_return = np.log(self.total_equity / previous_equity)
        else:
            step_return = -1.0 # Severe penalty for bankruptcy
            
        return step_return, (self.total_equity - previous_equity)

    def _update_drawdown(self) -> None:
        """Internal helper to track maximum drawdown in real-time."""
        if self.total_equity > self.peak_equity:
            self.peak_equity = self.total_equity
            
        current_drawdown = (self.peak_equity - self.total_equity) / self.peak_equity
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown

    def get_telemetry(self) -> Dict[str, float]:
        """Returns financial metrics for logging to MLflow / Dashboard."""
        return {
            "total_equity": self.total_equity,
            "total_return_pct": ((self.total_equity / self.initial_capital) - 1.0) * 100,
            "max_drawdown_pct": self.max_drawdown * 100,
            "current_position": self.positions["asset"]
        }