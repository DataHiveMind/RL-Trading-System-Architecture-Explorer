import mlflow
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Interfaces with MLflow to track, fetch, and promote RL models.
    """
    def __init__(self, tracking_uri: str = "http://localhost:5000"):
        mlflow.set_tracking_uri(tracking_uri)
        self.client = mlflow.tracking.MlflowClient()

    def get_best_run(self, experiment_name: str, metric: str = "episode_reward_mean") -> Optional[str]:
        """
        Searches MLflow for the run with the highest reward.
        Returns the run_id.
        """
        experiment = self.client.get_experiment_by_name(experiment_name)
        if not experiment:
            logger.error(f"Experiment {experiment_name} not found.")
            return None
            
        runs = self.client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=[f"metrics.{metric} DESC"],
            max_results=1
        )
        
        if not runs:
            logger.warning("No runs found for this experiment.")
            return None
            
        best_run = runs[0]
        logger.info(f"Found best run: {best_run.info.run_id} with {metric}: {best_run.data.metrics.get(metric)}")
        return best_run.info.run_id

    def load_ray_checkpoint(self, run_id: str) -> str:
        """
        Downloads the Ray checkpoint artifact for a specific run so it can be loaded into an agent.
        """
        # In a real environment, this pulls the artifact from S3/GCS
        checkpoint_path = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path="checkpoint")
        logger.info(f"Checkpoint downloaded to {checkpoint_path}")
        return checkpoint_path