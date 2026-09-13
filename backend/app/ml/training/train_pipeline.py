import os
import asyncio
import numpy as np
import pandas as pd
import xgboost as xgb
from motor.motor_asyncio import AsyncIOMotorClient
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from app.config.settings import settings
from app.services.feature_service import engineer_features, FEATURE_COLUMNS
from app.ml.models.cost_model import cost_model
from app.ml.models.delay_model import delay_model
from app.ml.models.risk_model import risk_model
from app.config.logging import logger

async def train_all_models():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]

    print("Retrieving projects and snapshots for time-aware training...")
    projects = await db.projects.find({}, {"_id": 0}).to_list(length=3000)
    if not projects:
        print("No projects found in DB to train on!")
        client.close()
        return

    # Assemble training dataset
    X_rows = []
    y_cost = []
    y_delay = []
    y_risk = []

    for p in projects:
        pid = p["project_id"]
        snaps = await db.project_snapshots.find({"project_id": pid}, {"_id": 0}).sort("snapshot_date", 1).to_list(length=60)
        if len(snaps) < 3:
            continue

        # Split temporally: use first 8 months to build features, predict final outcome in month 12
        train_snaps = snaps[:8]
        final_snap = snaps[-1]

        features = engineer_features(p, train_snaps)
        X_rows.append([features.get(col, 0.0) for col in FEATURE_COLUMNS])

        # Targets
        orig_cost = float(p.get("cost", {}).get("original", 1000.0) or 1000.0)
        rev_cost = float(p.get("cost", {}).get("revised", orig_cost) or orig_cost)
        actual_overrun_pct = max(0.0, ((rev_cost - orig_cost) / orig_cost) * 100.0)
        y_cost.append(actual_overrun_pct)

        slip = features.get("deadline_slip_months", 0.0)
        y_delay.append(slip)

        is_critical = 1 if p.get("risk_level") in ("critical", "high") else 0
        y_risk.append(is_critical)

    client.close()

    X = np.array(X_rows)
    y_cost = np.array(y_cost)
    y_delay = np.array(y_delay)
    y_risk = np.array(y_risk)

    print(f"Dataset compiled: {len(X)} samples with {len(FEATURE_COLUMNS)} features.")

    # 80/20 Train-Val split
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_cost_train, y_cost_val = y_cost[:split_idx], y_cost[split_idx:]
    y_delay_train, y_delay_val = y_delay[:split_idx], y_delay[split_idx:]
    y_risk_train, y_risk_val = y_risk[:split_idx], y_risk[split_idx:]

    # 1. Train Cost Overrun Model
    print("Training Cost Overrun XGBoost Regressor...")
    cost_model.model = xgb.XGBRegressor(n_estimators=120, max_depth=4, learning_rate=0.06, random_state=42)
    cost_model.model.fit(X_train, y_cost_train)
    cost_preds = cost_model.model.predict(X_val)
    cost_mae = mean_absolute_error(y_cost_val, cost_preds)
    cost_r2 = r2_score(y_cost_val, cost_preds)
    cost_model.save()
    print(f"✓ Cost Model Trained — Validation MAE: {cost_mae:.2f}%, R2: {cost_r2:.3f}")

    # 2. Train Schedule Delay Model
    print("Training Schedule Delay XGBoost Regressor...")
    delay_model.model = xgb.XGBRegressor(n_estimators=120, max_depth=4, learning_rate=0.06, random_state=42)
    delay_model.model.fit(X_train, y_delay_train)
    delay_preds = delay_model.model.predict(X_val)
    delay_mae = mean_absolute_error(y_delay_val, delay_preds)
    delay_model.save()
    print(f"✓ Delay Model Trained — Validation MAE: {delay_mae:.2f} months")

    # 3. Train Overall Risk Model
    print("Training Overall Risk XGBoost Classifier...")
    risk_model.model = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.08, random_state=42)
    risk_model.model.fit(X_train, y_risk_train)
    risk_model.save()
    print("✓ Overall Risk Classifier Trained and Artifacts Saved.")

if __name__ == "__main__":
    asyncio.run(train_all_models())
