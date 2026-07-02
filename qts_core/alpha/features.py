from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class BaseAlpha(ABC):
    """
    Abstract base class for all Alpha factors.
    Enforces a strict contract for generating features to prevent look-ahead bias
    and ensure compatibility with the feature store.
    """
    
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def compute(self, data: pd.DataFrame) -> pd.Series:
        """
        Computes the alpha factor. 
        Args:
            data: Standardized OHLCV dataframe.
        Returns:
            pd.Series containing the computed factor, indexed identically to input data.
        """
        pass

class MomentumAlpha(BaseAlpha):
    """Calculates time-series momentum (rate of change)."""
    
    def __init__(self, lookback_period: int = 14):
        super().__init__(name=f"momentum_{lookback_period}")
        self.lookback = lookback_period
        
    def compute(self, data: pd.DataFrame) -> pd.Series:
        if 'close' not in data.columns:
            raise ValueError("MomentumAlpha requires a 'close' column.")
            
        # Log return over the lookback period
        return np.log(data['close'] / data['close'].shift(self.lookback))

class VolatilityAlpha(BaseAlpha):
    """Calculates rolling standard deviation of returns."""
    
    def __init__(self, window: int = 20):
        super().__init__(name=f"volatility_{window}")
        self.window = window
        
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        return returns.rolling(window=self.window).std()