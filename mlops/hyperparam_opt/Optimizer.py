from typing import Any

import ray
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.env import register_env

try:
    import gymnasium as gym  # type: ignore[import]
except ImportError:
    gym = None  # type: ignore[assignment]


# Note: In a real run, import your env_creator from qts_core.models.trainer
def dummy_env_creator(config: dict[str, Any]) -> Any:
    if gym is None:
        import gymnasium as gym  # type: ignore[import]
    return gym.make("CartPole-v1") # Placeholder for EnterpriseTradingEnv

def run_optimization(experiment_name: str = "PPO_Hyper_Tuning") -> None:
    """
    Launches a distributed hyperparameter sweep using Ray Tune.
    """
    ray.init(ignore_reinit_error=True)
    register_env("TradingEnv-v0", dummy_env_creator)

    # Define the search space
    config = (
        PPOConfig()
        .environment("TradingEnv-v0")
        .framework("torch")
        .training(
            lr=tune.loguniform(1e-5, 1e-3),
            gamma=tune.choice([0.95, 0.99, 0.999]),
            clip_param=tune.uniform(0.1, 0.3),
            train_batch_size=tune.choice([2000, 4000, 8000])
        )
    )

    tuner = tune.Tuner(
        "PPO",
        param_space=config,
        tune_config=tune.TuneConfig(
            metric="episode_reward_mean",
            mode="max",
            num_samples=10, # Number of parallel trials
        ),
        run_config=ray.train.RunConfig(
            name=experiment_name,
            stop={"training_iteration": 50}
        )
    )

    results = tuner.fit()
    print(f"Best hyperparameters found: {results.get_best_result().config}")

if __name__ == "__main__":
    run_optimization()
