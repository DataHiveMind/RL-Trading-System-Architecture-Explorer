from abc import ABC, abstractmethod
import numpy as np

class BaseSlippageModel(ABC):
    """
    Abstract base class for calculating execution slippage and market impact.
    """
    @abstractmethod
    def calculate_slippage(self, trade_quantity: float, current_price: float, market_volume: float) -> float:
        """
        Calculates the per-share price penalty incurred by executing a trade.
        """
        pass

class VolumeShareSlippageModel(BaseSlippageModel):
    """
    Realistic slippage model: The larger the trade relative to the market bar's volume,
    the worse the fill price. Based on standard market impact formulas.
    """
    
    def __init__(self, price_impact_constant: float = 0.1):
        """
        Args:
            price_impact_constant: Tunable parameter based on historical fill data.
        """
        self.impact_constant = price_impact_constant
        
    def calculate_slippage(self, trade_quantity: float, current_price: float, market_volume: float) -> float:
        if market_volume == 0 or trade_quantity == 0:
            return 0.0
            
        # Percentage of the bar's volume we are trying to consume
        volume_share = abs(trade_quantity) / market_volume
        
        # Quadratic impact: trying to take 10% of volume hurts much more than 1%
        impact_penalty = self.impact_constant * (volume_share ** 2)
        
        # The penalty is returned as a percentage of the price
        return current_price * impact_penalty

class FixedBasisPointSlippage(BaseSlippageModel):
    """Simple, constant slippage (e.g., always pay 5 bps per trade)."""
    
    def __init__(self, basis_points: float = 5.0):
        self.bps_penalty = basis_points / 10000.0
        
    def calculate_slippage(self, trade_quantity: float, current_price: float, market_volume: float) -> float:
        return current_price * self.bps_penalty