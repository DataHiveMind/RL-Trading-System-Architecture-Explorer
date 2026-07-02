import gymnasium as gym
import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict, Any

from qts_core.portfolio.ledger import PortfolioLedger
from qts_core.risk.manager import RiskManager

class TradingEnv(gym.Env):
    """
    The orchestrator. It wraps the data pipeline, the risk manager, and the ledger 
    into a standard Gymnasium interface for RL training.
    """
    
    def __init__(self, data: pd.DataFrame, initial_capital: float = 100000.0):
        super().__init__()
        self.data = data
        self.current_step = 0
        
        # Instantiate Core Submodules
        self.ledger = PortfolioLedger(initial_capital=initial_capital)
        self.risk_manager = RiskManager(max_drawdown_limit=0.15, max_leverage=1.0)
        
        # Action Space: Target portfolio weight [-1.0, 1.0]
        # -1.0 is 100% short, 0.0 is 100% cash, 1.0 is 100% long
        self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)
        
        # Observation Space: All data columns (features) + current portfolio weight
        # Assumes 'close' is the price column, everything else is an alpha feature
        self.obs_features = [col for col in data.columns if col != 'close']
        self.observation_space = gym.spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(len(self.obs_features) + 1,), 
            dtype=np.float32
        )

    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        self.current_step = 0
        
        # Reset submodules
        self.ledger.reset()
        self.risk_manager.reset()
        
        # Initialize price to the first step
        self.ledger.update_price(self.data.iloc[self.current_step]['close'])
        
        return self._get_observation(), self.ledger.get_telemetry()

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        target_weight = float(action[0])
        
        # 1. Update Market Price
        current_price = self.data.iloc[self.current_step]['close']
        self.ledger.update_price(current_price)
        
        # 2. Risk Manager Intercepts Action
        current_drawdown = self.ledger.max_drawdown
        # Unpacking the tuple returning from our updated RiskManager
        safe_weight, risk_telemetry = self.risk_manager.enforce_limits(target_weight, current_drawdown)
        
        # 3. Ledger Executes Trade
        old_value = self.ledger.get_portfolio_value()
        transaction_cost = self.ledger.execute_target_weight(safe_weight)
        new_value = self.ledger.get_portfolio_value()
        
        # 4. Advance Time
        self.current_step += 1
        done = self.current_step >= len(self.data) - 1
        
        # 5. Calculate Reward (Differential Log Return minus transaction costs)
        # Using log returns for stability in neural network training
        if old_value > 0:
            reward = np.log(new_value / old_value)
        else:
            reward = -1.0 # Severe penalty for going bankrupt
            done = True
            
        # 6. Gather Telemetry (To be streamed via WebSockets to Dashboard)
        info = self.ledger.get_telemetry()
        info.update(risk_telemetry) # Merge risk breach data with ledger data
        info["safe_weight_executed"] = safe_weight
        info["transaction_cost"] = transaction_cost
        info["circuit_breaker_tripped"] = self.risk_manager.circuit_breaker_tripped
        
        return self._get_observation(), reward, done, False, info

    def _get_observation(self) -> np.ndarray:
        """Constructs the state array observed by the agent."""
        # Get raw feature values from the data pipeline
        row_features = self.data.iloc[self.current_step][self.obs_features].values
        
        # The agent MUST know its current allocation to make delta decisions
        portfolio_val = self.ledger.get_portfolio_value()
        current_weight = (self.ledger.positions * self.ledger.current_price) / portfolio_val if portfolio_val > 0 else 0.0
        
        obs = np.append(row_features, current_weight)
        return obs.astype(np.float32)