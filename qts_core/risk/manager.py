import logging
import numpy as np
from typing import Any, Tuple, Dict

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Enterprise-grade Risk Manager.
    Acts as an absolute circuit breaker and position sizing constraint 
    between the RL agent and the Portfolio Ledger.
    """

    def __init__(
        self, 
        max_drawdown_limit: float = 0.15, 
        max_leverage: float = 1.0,
        max_position_size: float = 1.0
    ):
        """
        Args:
            max_drawdown_limit: The maximum allowed peak-to-trough drop (e.g., 0.15 = 15%).
            max_leverage: Maximum gross exposure (e.g., 1.0 means no margin/leverage).
            max_position_size: Max allocation to a single position (e.g. 0.5 = 50% max).
        """
        self.max_drawdown_limit = max_drawdown_limit
        self.max_leverage = max_leverage
        self.max_position_size = max_position_size
        self.circuit_breaker_tripped = False
        self.breach_history: list[str] = []

    def enforce_limits(self, target_weight: float, current_drawdown: float) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluates the agent's requested action against hard risk limits.

        Args:
            target_weight: The raw portfolio allocation requested by the agent.
            current_drawdown: The current maximum drawdown from the ledger.

        Returns:
            Tuple containing:
            - safe_weight (float): The constrained, safe portfolio weight to execute.
            - risk_telemetry (Dict): Metadata about limit breaches for the dashboard.
        """
        telemetry = {
            "raw_target": target_weight,
            "drawdown_breach": False,
            "leverage_breach": False,
            "concentration_breach": False
        }

        # 1. Global Circuit Breaker (Max Drawdown)
        if self.circuit_breaker_tripped or current_drawdown >= self.max_drawdown_limit:
            if not self.circuit_breaker_tripped:
                logger.error(f"FATAL RISK BREACH: Drawdown {current_drawdown*100:.2f}% exceeds {self.max_drawdown_limit*100:.2f}% limit. Liquidating portfolio.")
                self.circuit_breaker_tripped = True
                self.breach_history.append("MAX_DRAWDOWN")

            telemetry["drawdown_breach"] = True
            return 0.0, telemetry

        # 2. Enforce Leverage Limits (Gross Exposure)
        safe_weight = np.clip(target_weight, -self.max_leverage, self.max_leverage)
        if safe_weight != target_weight:
            telemetry["leverage_breach"] = True
            logger.debug(f"Leverage limit constrained weight from {target_weight:.2f} to {safe_weight:.2f}")

        # 3. Enforce Concentration Limits (Max Position Size)
        # Example: Even if leverage is 2.0, we might cap a single asset at 0.5 (50%)
        constrained_weight = np.clip(safe_weight, -self.max_position_size, self.max_position_size)
        if constrained_weight != safe_weight:
            telemetry["concentration_breach"] = True
            logger.debug(f"Concentration limit constrained weight from {safe_weight:.2f} to {constrained_weight:.2f}")

        return float(constrained_weight), telemetry

    def reset(self) -> None:
        """Resets the risk manager state for a new episode."""
        self.circuit_breaker_tripped = False
        self.breach_history.clear()
        logger.info("Risk Manager limits reset for new episode.")