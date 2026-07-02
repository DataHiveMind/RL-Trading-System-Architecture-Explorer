import logging
from data_platform.connectors.binance import BinanceConnector
from data_platform.feature_store.registry import FeatureRegistry
from qts_core.alpha.features import MomentumAlpha, VolatilityAlpha

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_daily_pipeline():
    """
    Orchestrates the daily data ingestion and feature generation.
    In production, this is triggered by Airflow, Prefect, or a CRON job.
    """
    logger.info("Starting daily data pipeline...")
    
    # 1. Ingest Raw Data
    connector = BinanceConnector()
    raw_data = connector.fetch_historical_data(symbol="BTCUSDT", interval="1d", limit=500)
    
    # 2. Initialize Feature Store
    registry = FeatureRegistry()
    registry.register_alpha(MomentumAlpha(lookback_period=14))
    registry.register_alpha(VolatilityAlpha(window=20))
    
    # 3. Compute and Cache Features
    features_df = registry.generate_features(raw_data, dataset_id="BTCUSDT_1d_prod")
    
    logger.info(f"Pipeline complete. Generated {len(features_df.columns)} features over {len(features_df)} timesteps.")
    return features_df

if __name__ == "__main__":
    run_daily_pipeline()