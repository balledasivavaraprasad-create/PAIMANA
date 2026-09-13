import asyncio
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.services.feature_service import engineer_features
from app.services.dphis_service import calculate_dphis
from app.ml.models.cost_model import cost_model
from app.ml.models.delay_model import delay_model
from app.security.hashing import get_password_hash
from app.models.user import UserRole

STATES_DATA = [
    {"state": "Uttar Pradesh", "lat": 26.8467, "lng": 80.9462, "district": "Varanasi"},
    {"state": "Maharashtra", "lat": 19.0760, "lng": 72.8777, "district": "Mumbai Suburban"},
    {"state": "Tamil Nadu", "lat": 13.0827, "lng": 80.2707, "district": "Chennai"},
    {"state": "Rajasthan", "lat": 26.9124, "lng": 75.7873, "district": "Jaisalmer"},
    {"state": "Gujarat", "lat": 23.0225, "lng": 72.5714, "district": "Ahmedabad"},
    {"state": "Bihar", "lat": 25.5941, "lng": 85.1376, "district": "Patna"},
    {"state": "Andhra Pradesh", "lat": 16.5062, "lng": 80.6480, "district": "Visakhapatnam"},
    {"state": "Assam", "lat": 26.1445, "lng": 91.7362, "district": "Dibrugarh"},
    {"state": "Karnataka", "lat": 12.9716, "lng": 77.5946, "district": "Bengaluru Urban"},
    {"state": "West Bengal", "lat": 22.5726, "lng": 88.3639, "district": "Kolkata"},
    {"state": "Madhya Pradesh", "lat": 23.2599, "lng": 77.4126, "district": "Bhopal"},
    {"state": "Odisha", "lat": 20.2961, "lng": 85.8245, "district": "Puri"},
    {"state": "Kerala", "lat": 8.5241, "lng": 76.9366, "district": "Thiruvananthapuram"},
    {"state": "Telangana", "lat": 17.3850, "lng": 78.4867, "district": "Hyderabad"},
]

SECTORS = [
    ("Roads & Highways", "Ministry of Road Transport and Highways", "National Highway Expansion"),
    ("Railways & Freight", "Ministry of Railways", "Broad Gauge Doubling & Freight Corridor"),
    ("Urban Transit & Metro", "Ministry of Housing and Urban Affairs", "Metro Rail Phase Expansion"),
    ("Renewable Energy", "Ministry of New and Renewable Energy", "Ultra Mega Solar Power Grid"),
    ("Ports & Shipping", "Ministry of Ports, Shipping and Waterways", "Deepwater Container Terminal Modernisation"),
    ("Petrochemical & Gas", "Ministry of Petroleum and Natural Gas", "Cross-Country Natural Gas Pipeline"),
]

PROJECT_TEMPLATES = [
    "NH-48 Varanasi-Ranchi Expressway",
    "Chennai Metro Rail Phase III Viaduct",
    "Solar Energy Ultra Grid, Jaisalmer",
    "Visakhapatnam Deepwater Port Modernisation",
    "Bihar Broad Gauge Freight Corridor",
    "Mumbai Trans Harbour Corridor Extension",
    "Dedicated Western Freight Rail Segment",
    "Assam Brahmaputra Gas Cracker Complex",
    "Bangalore Suburban Rail Corridor 2",
    "Bhadla Solar Power Complex Phase IV",
    "Delhi-Dehradun Economic Expressway",
    "Chenab Rail Arch Bridge Segment",
    "Khavda Renewable Energy Hybrid Park",
    "JNPT Port Terminal Automated Wharf",
    "Kolkata East-West Metro Tunnel Package",
]

async def seed_database(num_projects: int = 1500):
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]

    print(f"Connecting to {settings.MONGODB_URL} -> Database: {settings.MONGODB_DB_NAME}")
    
    # 1. Clear existing demo data
    await db.projects.delete_many({})
    await db.project_snapshots.delete_many({})
    await db.users.delete_many({})
    await db.alerts.delete_many({})
    await db.investigations.delete_many({})

    # 2. Seed Default Users
    admin_user = {
        "username": "admin",
        "email": "admin@paimana.gov.in",
        "full_name": "Chief Executive Officer / MoSPI Lead",
        "role": UserRole.ADMIN,
        "hashed_password": get_password_hash("paimana2026"),
        "created_at": datetime.utcnow()
    }
    analyst_user = {
        "username": "analyst",
        "email": "analyst@paimana.gov.in",
        "full_name": "Senior Project Intelligence Analyst",
        "role": UserRole.MO_SPI_ANALYST,
        "hashed_password": get_password_hash("paimana2026"),
        "created_at": datetime.utcnow()
    }
    await db.users.insert_many([admin_user, analyst_user])
    print("Seeded default users: admin / analyst (password: paimana2026)")

    # 3. Generate 1,500 Projects with 12-Month Trajectory Snapshots
    projects_to_insert = []
    snapshots_to_insert = []

    # Pin P1024 as canonical critical hero project
    critical_pids = {"P1024", "P0847", "P1156", "P0392", "P0771"}

    print(f"Synthesizing {num_projects} realistic infrastructure projects across India...")

    for i in range(1, num_projects + 1):
        pid = f"P{i:04d}"
        state_info = random.choice(STATES_DATA)
        sector_name, ministry_name, default_prefix = random.choice(SECTORS)

        if i <= len(PROJECT_TEMPLATES):
            p_name = PROJECT_TEMPLATES[i - 1]
        else:
            p_name = f"{state_info['state']} {default_prefix} Segment {i}"

        # Jitter coordinates slightly around state center
        lat = round(state_info["lat"] + random.uniform(-0.8, 0.8), 4)
        lng = round(state_info["lng"] + random.uniform(-0.8, 0.8), 4)

        orig_cost = round(random.uniform(500.0, 15000.0), 1)

        is_critical = pid in critical_pids or (i % 18 == 0)
        is_high = not is_critical and (i % 8 == 0)

        if is_critical:
            rev_cost = round(orig_cost * random.uniform(1.15, 1.45), 1)
            planned_months = random.randint(24, 48)
            slip_months = random.randint(12, 32)
        elif is_high:
            rev_cost = round(orig_cost * random.uniform(1.06, 1.15), 1)
            planned_months = random.randint(24, 48)
            slip_months = random.randint(6, 14)
        else:
            rev_cost = round(orig_cost * random.uniform(1.0, 1.05), 1)
            planned_months = random.randint(24, 48)
            slip_months = random.randint(0, 5)

        start_dt = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365))
        orig_end = start_dt + timedelta(days=planned_months * 30)
        rev_end = orig_end + timedelta(days=slip_months * 30)

        # Build 12 monthly snapshots (2025-09 to 2026-08)
        project_snaps = []
        base_phys = random.uniform(10.0, 25.0)
        base_fin = base_phys + (random.uniform(15.0, 32.0) if is_critical else random.uniform(-2.0, 6.0))

        for month_idx in range(12):
            snap_dt = datetime(2025, 9, 1) + timedelta(days=month_idx * 30)
            date_str = snap_dt.strftime("%Y-%m-%d")

            # Progress increments: stagnates for critical in last 3 months
            if is_critical and month_idx >= 8:
                phys_inc = random.uniform(0.1, 0.4)  # Stagnation!
            else:
                phys_inc = random.uniform(1.0, 3.5)

            fin_inc = random.uniform(1.5, 4.0)

            base_phys = min(98.0, base_phys + phys_inc)
            base_fin = min(98.0, base_fin + fin_inc)
            cum_spend = round((base_fin / 100.0) * rev_cost, 1)

            total_m = random.randint(8, 20)
            delayed_m = random.randint(3, 7) if is_critical else random.randint(0, 2)
            comp_m = int((base_phys / 100.0) * total_m)

            snap_obj = {
                "project_id": pid,
                "snapshot_date": date_str,
                "physical_progress": round(base_phys, 1),
                "financial_progress": round(base_fin, 1),
                "cumulative_expenditure": cum_spend,
                "milestones": {
                    "completed": comp_m,
                    "delayed": delayed_m,
                    "pending": max(0, total_m - comp_m - delayed_m),
                    "total": total_m
                },
                "weather": {
                    "rainfall_mm": round(random.uniform(10.0, 140.0), 1),
                    "temperature_c": round(random.uniform(22.0, 38.0), 1),
                    "wind_speed_kmh": round(random.uniform(8.0, 25.0), 1),
                    "disruption_flag": bool(is_critical and random.random() < 0.3)
                },
                "created_at": snap_dt
            }
            project_snaps.append(snap_obj)
            snapshots_to_insert.append(snap_obj)

        # Engineer features and compute DPHIS
        proj_dict = {
            "project_id": pid,
            "project_name": p_name,
            "ministry": ministry_name,
            "department": f"{sector_name} Authority",
            "sector": sector_name,
            "state": state_info["state"],
            "location": {
                "latitude": lat,
                "longitude": lng,
                "district": state_info["district"],
                "state": state_info["state"]
            },
            "cost": {
                "original": orig_cost,
                "revised": rev_cost,
                "currency": "INR_CR"
            },
            "schedule": {
                "original_start": start_dt.strftime("%Y-%m-%d"),
                "original_end": orig_end.strftime("%Y-%m-%d"),
                "revised_end": rev_end.strftime("%Y-%m-%d")
            },
            "metadata": {
                "project_type": sector_name.split()[0],
                "implementing_agency": f"State PWD / Central {sector_name.split()[0]} Corp"
            }
        }

        features = engineer_features(proj_dict, project_snaps)
        c_res = cost_model.predict(features)
        d_res = delay_model.predict(features)

        # Previous DPHIS baseline
        prev_dphis = 75.0 if is_critical else 40.0
        dphis_obj = calculate_dphis(pid, features, c_res["cost_risk_score"], d_res["time_risk_score"], previous_dphis=prev_dphis)

        proj_dict["dphis"] = dphis_obj.dphis
        proj_dict["risk_level"] = dphis_obj.level.value
        proj_dict["data_quality_score"] = round(random.uniform(88.0, 99.0), 1)
        proj_dict["created_at"] = datetime.utcnow()
        proj_dict["updated_at"] = datetime.utcnow()

        projects_to_insert.append(proj_dict)

    # Batch insert into MongoDB
    print(f"Writing {len(projects_to_insert)} projects to MongoDB...")
    await db.projects.insert_many(projects_to_insert)

    print(f"Writing {len(snapshots_to_insert)} historical monthly snapshots to MongoDB...")
    # Insert in chunks of 5000 to keep it blazing fast
    chunk_size = 5000
    for i in range(0, len(snapshots_to_insert), chunk_size):
        await db.project_snapshots.insert_many(snapshots_to_insert[i:i + chunk_size])

    # 4. Generate initial alert for P1024
    sample_alert = {
        "alert_id": "ALT-P1024-CRIT",
        "project_id": "P1024",
        "project_name": "NH-48 Varanasi-Ranchi Expressway",
        "severity": "critical",
        "previous_severity": "high",
        "trigger": "DPHIS_ESCALATION",
        "dphis": 91.0,
        "message": "CRITICAL ESCALATION: NH-48 Varanasi-Ranchi Expressway reached DPHIS 91.0. Superstructure Phase 1 milestone delayed by 28 months.",
        "status": "PENDING",
        "webhook_dispatched": True,
        "created_at": datetime.utcnow()
    }
    await db.alerts.insert_one(sample_alert)

    print("\n✓ SUCCESS: PAIMANA Database seeded completely!")
    print(f"  • Total Projects: {await db.projects.count_documents({})}")
    print(f"  • Total Monthly Snapshots: {await db.project_snapshots.count_documents({})}")
    print(f"  • Critical Projects: {await db.projects.count_documents({'risk_level': 'critical'})}")
    print(f"  • High Risk Projects: {await db.projects.count_documents({'risk_level': 'high'})}")
    print(f"  • Moderate Risk Projects: {await db.projects.count_documents({'risk_level': 'moderate'})}")
    print(f"  • Low Risk Projects: {await db.projects.count_documents({'risk_level': 'low'})}")

    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database(1500))
