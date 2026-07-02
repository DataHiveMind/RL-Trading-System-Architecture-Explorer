import logging
from typing import Any, Dict, TYPE_CHECKING

import mlflow
import pandas as pd
import ray
from ray.rllib.algorithms.algorithm import Algorithm
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env

logger = logging.getLogger(__name__)

# Note: We import the TradingEnv inside the creator to avoid circular dependencies in Ray worker nodes
if TYPE_CHECKING:
    # Import for type checking only to satisfy linters/IDE. Actual import happens at runtime
    # inside env_creator to avoid circular dependencies in Ray worker nodes.
    from qts_core.envs.trading_env import TradingEnv  # noqa: F401


def env_creator(env_config: Dict[str, Any]) -> Any:
    from qts_core.envs.trading_env import TradingEnv

    # In production, data is fetched via the data_platform. Here we expect it in the config.
    data = env_config.get("data")
    if data is None:
        raise ValueError("Must provide historical 'data' (DataFrame) in env_config.")

    return TradingEnv(data=data, initial_capital=env_config.get("initial_capital", 100000.0))

class RLTrainer:
    """
    Manages the distributed RL training lifecycle using Ray RLlib.
    """
    def __init__(self, env_name: str = "EnterpriseTradingEnv-v0"):
        self.env_name = env_name

        # Initialize Ray if not already running
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)

        # Register the custom Gym environment with Ray
        register_env(self.env_name, env_creator)

    def build_ppo_config(self, train_data: pd.DataFrame) -> PPOConfig:
        """
        Builds an institutional-grade PPO configuration.
        """
        config = (
            PPOConfig()
            .environment(
                env=self.env_name,
                env_config={
                    "data": train_data,
                    "initial_capital": 100000.0,
                },
            )
            .framework("torch")
            # --- Distributed Compute Settings ---
            .rollouts(num_rollout_workers=4, num_envs_per_worker=2)
            # --- PPO Specific Hyperparameters ---
            .training(
                gamma=0.99,
                lr=3e-4,
                clip_param=0.2,
                entropy_coeff=0.01,
                train_batch_size=4000,
                sgd_minibatch_size=128,
                num_sgd_iter=10,
            )
            # --- MLOps & Telemetry ---
            .debugging(log_level="INFO")
        )
        return config

    def train(
        self,
        config: PPOConfig,
        training_iterations: int = 100,
        checkpoint_freq: int = 10,
        experiment_name: str = "Enterprise_RL_Trading",
    ) -> Algorithm:
        """Executes the training loop with MLflow tracking and automated checkpointing."""
        logger.info(f"Starting training for {training_iterations} iterations...")
        algo = config.build()

        # Set up MLflow tracking
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run():
            # Log critical hyperparameters to recreate this exact run
            mlflow.log_params(
                {
                    "learning_rate": config.lr,
                    "gamma": config.gamma,
                    "train_batch_size": config.train_batch_size,
                    "clip_param": config.clip_param,
                    "entropy_coeff": config.entropy_coeff,
                }
            )

            for i in range(1, training_iterations + 1):
                results = algo.train()

                # Safely extract metrics (Ray 2.x API structure)
                mean_reward = results.get("episode_reward_mean", 0)
                episode_len = results.get("episode_len_mean", 0)

                logger.info(
                    f"Iteration: {i:03d} | Mean Reward: {mean_reward:.4f} | "
                    f"Episode Len: {episode_len:.1f}"
                )

                # Push telemetry to MLflow dashboard
                mlflow.log_metrics(
                    {
                        "episode_reward_mean": mean_reward,
                        "episode_len_mean": episode_len,
                        "total_loss": results
                        .get("info", {})
                        .get("learner", {})
                        .get("default_policy", {})
                        .get("learner_stats", {})
                        .get("total_loss", 0.0),
                    },
                    step=i,
                )

                # Create hard checkpoints so the model can be paused/resumed or deployed
                if i % checkpoint_freq == 0:
                    checkpoint_dir = algo.save()
                    logger.info(f"Checkpoint saved successfully at: {checkpoint_dir}")

        # Gracefully shut down the workers to free up RAM/VRAM
        algo.stop()
        logger.info("Training complete and worker nodes spun down.")

        return algo
