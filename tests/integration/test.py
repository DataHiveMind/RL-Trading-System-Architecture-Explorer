import numpy as np
import pandas as pd
from qts_core.envs.trading_env import TradingEnv


def test_full_environment_loop() -> None:
    """
    Tests the integration of Data -> Environment -> Risk Manager -> Ledger.
    """
    # 1. Mock Data Pipeline Output
    dates = pd.date_range("2023-01-01", periods=100)
    mock_data = pd.DataFrame({
        "close": np.linspace(100, 150, 100),  # Upward trending price
        "momentum_14": np.random.randn(100),
        "volatility_20": np.random.randn(100),
    }, index=dates)

    # 2. Initialize Environment
    env = TradingEnv(data=mock_data, initial_capital=100000.0)
    _, info = env.reset()

    # 3. Run a mock episode
    done = False
    total_reward = 0.0
    steps = 0

    while not done:
        # Agent outputs a constant long action
        action = np.array([0.5], dtype=np.float32)

        _, reward, done, _, info = env.step(action)
        total_reward += reward
        steps += 1

        # Verify Risk Manager and Ledger are communicating
        assert "portfolio_value" in info
        assert "circuit_breaker_tripped" in info

    # 4. Verify End State
    assert steps == 99  # 100 data points = 99 transitions
    assert info["portfolio_value"] > 0
