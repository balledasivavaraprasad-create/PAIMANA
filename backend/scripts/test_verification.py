import httpx
from pymongo import MongoClient

BASE_URL = "http://localhost:8000/api/v1"

print("--- 1. Testing Public Risk Overview Endpoint ---")
r = httpx.get(f"{BASE_URL}/projects/public-risk-overview")
assert r.status_code == 200, f"Failed: {r.status_code}"
data = r.json()
print("Total projects in DB:", data["total_projects"])
print("Total capex:", data["total_capex_lakh_cr"], "Lakh Cr")
print("At risk count:", data["at_risk_count"])
print("Critical count:", data["critical_count"])
print("Sectors count:", data["sectors_count"])
print("Top sectors sample:", data["top_sectors"][:4])
print("Risk watchlist length:", len(data["risk_watchlist"]))

allowed_keys = {"project_name", "sector", "state", "dphis", "risk_level", "cost_revised_cr", "schedule_slippage_months"}
for item in data["risk_watchlist"]:
    extra_keys = set(item.keys()) - allowed_keys
    assert not extra_keys, f"Forbidden keys exposed in public response: {extra_keys}"
print("Column restriction check passed: strictly allowed columns exposed.")

print("\n--- 2. Testing User-Specific Projects for Dr. Ramesh Kumar (MoRTH) ---")
r2 = httpx.get(f"{BASE_URL}/projects/my-projects?username=ramesh.kumar")
assert r2.status_code == 200
projects_ramesh = r2.json()
print(f"Ramesh Kumar assigned corridors: {len(projects_ramesh)}")
for p in projects_ramesh[:3]:
    p_id = p.get("project_id")
    p_name = p.get("project_name")
    p_min = p.get("ministry")
    print(f"  - [{p_id}] {p_name} ({p_min})")
assert all("Road Transport" in p["ministry"] for p in projects_ramesh)
print("All projects for Ramesh Kumar belong strictly to Road Transport & Highways.")

print("\n--- 3. Testing User-Specific Projects for Siva (Housing & Urban Affairs) ---")
r3 = httpx.get(f"{BASE_URL}/projects/my-projects?username=balledasivavaraprasad")
assert r3.status_code == 200
projects_siva = r3.json()
print(f"Siva assigned corridors: {len(projects_siva)}")
for p in projects_siva[:3]:
    p_id = p.get("project_id")
    p_name = p.get("project_name")
    p_min = p.get("ministry")
    print(f"  - [{p_id}] {p_name} ({p_min})")
assert all("Housing & Urban Affairs" in p["ministry"] for p in projects_siva)
print("All projects for Siva belong strictly to Housing & Urban Affairs.")

print("\n--- 4. Testing Auto-Assignment on User Registration ---")
reg_payload = {
    "fullName": "Railway Officer Sharma",
    "email": "sharma.railways@gov.in",
    "ministryId": 2,
    "designation": "Executive Director",
    "password": "Password1234!",
    "termsAccepted": True,
    "aiAckAccepted": True
}
db = MongoClient("mongodb://localhost:27017/")["paimana_intelligence"]
db.users.delete_one({"email": "sharma.railways@gov.in"})

r4 = httpx.post(f"{BASE_URL}/auth/register", json=reg_payload)
assert r4.status_code == 200, f"Registration failed: {r4.text}"
user_sharma = db.users.find_one({"email": "sharma.railways@gov.in"})
assert user_sharma is not None
assigned_count = len(user_sharma.get("assigned_projects", []))
print(f"New user registered: {user_sharma.get('username')}, assigned projects count: {assigned_count}")
assert assigned_count == 8
print("New user automatically assigned 8 projects from Ministry of Railways!")

db.users.delete_one({"email": "sharma.railways@gov.in"})
print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")
