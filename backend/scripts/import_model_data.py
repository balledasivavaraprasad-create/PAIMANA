import asyncio
import os
import zlib
import numpy as np
import pandas as pd
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

CSV_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "paimana_model_extracted",
    "PAIMANA_predictive_early_warning_final",
    "data",
    "3_final_project_health_scores.csv"
)

STATE_COORDINATES = {
    "Maharashtra": (19.7515, 75.7139),
    "Uttar Pradesh": (26.8467, 80.9462),
    "Gujarat": (22.2587, 71.1924),
    "Andhra Pradesh": (15.9129, 79.7400),
    "Bihar": (25.0961, 85.3131),
    "Tamil Nadu": (11.1271, 78.6569),
    "Madhya Pradesh": (22.9734, 78.6569),
    "Rajasthan": (27.0238, 74.2179),
    "Karnataka": (15.3173, 75.7139),
    "West Bengal": (22.9868, 87.8550),
    "Odisha": (20.9517, 85.0985),
    "Telangana": (18.1124, 79.0193),
    "Kerala": (10.8505, 76.2711),
    "Jharkhand": (23.6102, 85.2799),
    "Assam": (26.2006, 92.9376),
    "Punjab": (31.1471, 75.3412),
    "Haryana": (29.0588, 76.0856),
    "Chhattisgarh": (21.2787, 81.8661),
    "Uttarakhand": (30.0668, 79.0193),
    "Himachal Pradesh": (31.1048, 77.1734),
    "Jammu and Kashmir": (33.7782, 76.5762),
    "Jammu & Kashmir": (33.7782, 76.5762),
    "Goa": (15.2993, 74.1240),
    "Delhi": (28.7041, 77.1025),
    "Tripura": (23.9408, 91.9882),
    "Meghalaya": (25.4670, 91.3662),
    "Manipur": (24.6637, 93.9063),
    "Nagaland": (26.1584, 94.5624),
    "Mizoram": (23.1645, 92.9376),
    "Arunachal Pradesh": (28.2180, 94.7278),
    "Sikkim": (27.5330, 88.5122),
    "Puducherry": (11.9416, 79.8083),
    "Chandigarh": (30.7333, 76.7794),
    "Andaman & Nicobar": (11.7401, 92.6586),
    "Ladakh": (34.1526, 77.5771),
}

DEFAULT_COORDS = (22.5, 78.5)

def get_jittered_coords(state_name: str, code: str):
    base_lat, base_lng = DEFAULT_COORDS
    for s_key, coords in STATE_COORDINATES.items():
        if s_key.lower() in str(state_name).lower():
            base_lat, base_lng = coords
            break

    # Deterministic pseudo-random offset based on project_code
    h = zlib.crc32(str(code).encode('utf-8'))
    lat_offset = ((h % 1000) / 1000.0 - 0.5) * 1.8
    lng_offset = (((h // 1000) % 1000) / 1000.0 - 0.5) * 1.8

    lat = round(max(8.5, min(35.5, base_lat + lat_offset)), 4)
    lng = round(max(69.0, min(96.0, base_lng + lng_offset)), 4)
    return lat, lng

async def main():
    print(f"Reading {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, low_memory=False)
    print(f"Loaded {len(df)} records across {df['project_code'].nunique()} projects.")

    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]

    # Sort so latest snapshot is last
    df = df.sort_values(["project_code", "report_month"]).reset_index(drop=True)

    # 1. Prepare snapshots
    snapshots_to_insert = []
    for _, row in df.iterrows():
        p_code = str(row["project_code"]).strip()
        snap_doc = {
            "project_id": p_code,
            "snapshot_date": f"{row['report_month']}-01",
            "physical_progress": float(row.get("physical_progress_pct", 0.0) or 0.0),
            "financial_progress": float(row.get("cumulative_expenditure_cr", 0.0) or 0.0) / max(1.0, float(row.get("revised_cost_cr", 1.0) or 1.0)) * 100.0,
            "cumulative_expenditure": float(row.get("cumulative_expenditure_cr", 0.0) or 0.0),
            "cost_overrun_pct": float(row.get("cost_overrun_pct", 0.0) or 0.0),
            "schedule_slippage_months": float(row.get("schedule_slippage_months", 0.0) or 0.0),
            "dphis": float(row.get("DPHIS_score", 50.0) or 50.0),
            "risk_tier": str(row.get("risk_tier", "Watch")),
            "T_time_risk": float(row.get("T_time_risk", 0.34) or 0.34),
            "C_cost_risk": float(row.get("C_cost_risk", 0.10) or 0.10),
            "P_progress_risk": float(row.get("P_progress_risk", 0.30) or 0.30),
            "F_financial_risk": float(row.get("F_financial_risk", 0.30) or 0.30),
            "ML_combined_risk": float(row.get("ML_combined_risk", 0.27) or 0.27),
            "created_at": datetime.utcnow()
        }
        snapshots_to_insert.append(snap_doc)

    # 2. Prepare projects (latest state of each project)
    latest_df = df.groupby("project_code").last().reset_index()
    projects_to_insert = []
    for _, row in latest_df.iterrows():
        p_code = str(row["project_code"]).strip()
        p_name = str(row.get("project_name", f"Infrastructure Asset {p_code}")).strip()
        ministry = str(row.get("ministry", "Central Infrastructure")).strip()
        sector = str(row.get("sector", "Infrastructure")).strip()
        state = str(row.get("state", "India")).strip()
        agency = str(row.get("implementing_agency", "Statutory Project Authority")).strip()

        orig_cost = float(row.get("original_cost_cr", 1000.0) or 1000.0)
        rev_cost = float(row.get("revised_cost_cr", orig_cost) or orig_cost)
        cum_exp = float(row.get("cumulative_expenditure_cr", 0.0) or 0.0)
        phys_prog = float(row.get("physical_progress_pct", 0.0) or 0.0)
        cost_overrun = float(row.get("cost_overrun_pct", 0.0) or 0.0)
        slip_months = float(row.get("schedule_slippage_months", 0.0) or 0.0)
        dphis = float(row.get("DPHIS_score", 50.0) or 50.0)
        tier = str(row.get("risk_tier", "Watch")).lower()

        if tier == "critical":
            risk_level = "critical"
        elif tier == "high":
            risk_level = "high"
        elif tier in ("medium", "watch"):
            risk_level = "moderate"
        else:
            risk_level = "low"

        lat, lng = get_jittered_coords(state, p_code)

        proj_doc = {
            "project_id": p_code,
            "project_name": p_name,
            "ministry": ministry,
            "department": f"{sector} Directorate",
            "sector": sector,
            "state": state,
            "implementing_agency": agency,
            "location": {
                "latitude": lat,
                "longitude": lng,
                "district": state,
                "state": state
            },
            "cost": {
                "original": orig_cost,
                "revised": rev_cost,
                "cumulative_expenditure": cum_exp,
                "currency": "INR_CR"
            },
            "schedule": {
                "original_start": "2022-04-01",
                "original_end": "2026-03-31",
                "revised_end": f"20{26 + int(slip_months // 12):02d}-{int(slip_months % 12) + 1:02d}-28" if slip_months > 0 else "2026-03-31"
            },
            "physical_progress_pct": phys_prog,
            "cost_overrun_pct": cost_overrun,
            "schedule_slippage_months": slip_months,
            "dphis": round(dphis, 1),
            "risk_level": risk_level,
            "risk_tier": row.get("risk_tier", "Watch"),
            "risk_transition": str(row.get("risk_transition", "Stable")),
            "rapid_deterioration_flag": int(row.get("rapid_deterioration_flag", 0) or 0),
            "data_quality_score": round(float(row.get("data_quality_score", 0.85) or 0.85) * 100, 1),
            "confidence_score": round(float(row.get("confidence_score", 75.0) or 75.0), 1),
            "T_time_risk": float(row.get("T_time_risk", 0.34) or 0.34),
            "C_cost_risk": float(row.get("C_cost_risk", 0.10) or 0.10),
            "P_progress_risk": float(row.get("P_progress_risk", 0.30) or 0.30),
            "F_financial_risk": float(row.get("F_financial_risk", 0.30) or 0.30),
            "ML_combined_risk": float(row.get("ML_combined_risk", 0.27) or 0.27),
            "current_risk_score": float(row.get("current_risk_score_0_100", dphis) or dphis),
            "emerging_risk_score": float(row.get("emerging_risk_score_0_100", 50.0) or 50.0),
            "risk_velocity_1m": float(row.get("risk_velocity_1m", 0.0) or 0.0),
            "risk_acceleration_1m": float(row.get("risk_acceleration_1m", 0.0) or 0.0),
            "report_month": str(row["report_month"]),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        projects_to_insert.append(proj_doc)

    print(f"Total projects to load: {len(projects_to_insert)}")
    print(f"Total snapshots to load: {len(snapshots_to_insert)}")

    # Clear old mock projects and snapshots
    print("Clearing previous mock data in projects and project_snapshots...")
    await db.projects.delete_many({})
    await db.project_snapshots.delete_many({})

    # Insert projects in batches
    batch_size = 1000
    for i in range(0, len(projects_to_insert), batch_size):
        await db.projects.insert_many(projects_to_insert[i:i + batch_size])
        print(f"Inserted projects {i} to {min(i + batch_size, len(projects_to_insert))}")

    # Insert snapshots in batches
    for i in range(0, len(snapshots_to_insert), batch_size):
        await db.project_snapshots.insert_many(snapshots_to_insert[i:i + batch_size])
        print(f"Inserted snapshots {i} to {min(i + batch_size, len(snapshots_to_insert))}")

    # Create indexes for fast querying
    try:
        await db.projects.create_index("project_id", unique=True)
        await db.projects.create_index("ministry")
        await db.projects.create_index("dphis")
        await db.projects.create_index("risk_level")
        await db.project_snapshots.create_index([("project_id", 1), ("snapshot_date", 1)], unique=True)
    except Exception as e:
        print(f"Index creation note: {e}")

    # Also generate sample initial alerts for projects with rapid deterioration or critical DPHIS
    await db.alerts.delete_many({})
    alerts_to_insert = []
    critical_or_deteriorating = [p for p in projects_to_insert if p["dphis"] >= 70 or p["rapid_deterioration_flag"] == 1]
    for p in critical_or_deteriorating[:25]:
        reason = "RAPID_DETERIORATION" if p["rapid_deterioration_flag"] == 1 else "DPHIS_THRESHOLD_EXCEEDED"
        alerts_to_insert.append({
            "alert_id": f"ALT-{p['project_id']}",
            "project_id": p["project_id"],
            "project_name": p["project_name"],
            "severity": p["risk_level"].upper(),
            "previous_severity": "MODERATE",
            "trigger": reason,
            "dphis": p["dphis"],
            "message": f"CRITICAL ESCALATION: {p['project_name']} reached DPHIS {p['dphis']} (Velocity: {p['risk_velocity_1m']:+.1f} pts/mo). Trigger: {reason}.",
            "status": "PENDING",
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })

    if alerts_to_insert:
        await db.alerts.insert_many(alerts_to_insert)
        print(f"Inserted {len(alerts_to_insert)} high-priority DPHIS alerts.")

    print("Database sync complete!")


if __name__ == "__main__":
    asyncio.run(main())
