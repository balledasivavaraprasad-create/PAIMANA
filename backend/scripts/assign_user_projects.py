import re
import pymongo

def main():
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["paimana_intelligence"]

    print("=== ASSIGNING USER-PROJECT ASSOCIATIONS IN MONGODB ===")

    # 1. MoRTH projects for Dr. Ramesh Kumar and Pardhu
    morth_projects = list(db.projects.find(
        {"ministry": re.compile(r"Road Transport", re.IGNORECASE)},
        {"project_id": 1, "project_name": 1, "state": 1}
    ).sort("dphis", -1).limit(30))

    ramesh_ids = [p["project_id"] for p in morth_projects[:12]]
    pardhu_ids = [p["project_id"] for p in morth_projects[10:20]]

    # 2. Urban Affairs projects for Siva and Siva123
    urban_projects = list(db.projects.find(
        {"ministry": re.compile(r"Housing & Urban Affairs", re.IGNORECASE)},
        {"project_id": 1, "project_name": 1, "state": 1}
    ).sort("dphis", -1).limit(30))

    siva_ids = [p["project_id"] for p in urban_projects[:12]]
    siva123_ids = [p["project_id"] for p in urban_projects[8:18]]

    # 3. National high-risk portfolio for Lead Risk Analyst
    risk_projects = list(db.projects.find(
        {"risk_level": {"$in": ["high", "critical"]}},
        {"project_id": 1, "project_name": 1, "ministry": 1}
    ).sort("dphis", -1).limit(15))
    analyst_ids = [p["project_id"] for p in risk_projects]

    # 4. Flagship Sovereign Projects for MoSPI Admin
    flagship_projects = list(db.projects.find(
        {},
        {"project_id": 1, "project_name": 1, "cost.revised": 1}
    ).sort("cost.revised", -1).limit(20))
    admin_ids = [p["project_id"] for p in flagship_projects]

    user_assignments = {
        "ramesh.kumar": ramesh_ids,
        "pardhu.r25": pardhu_ids,
        "balledasivavaraprasad": siva_ids,
        "balledasivavaraprasad123": siva123_ids,
        "analyst": analyst_ids,
        "admin": admin_ids
    }

    # Reset any existing assigned_users on projects
    db.projects.update_many({}, {"$set": {"assigned_users": []}})

    for username, proj_ids in user_assignments.items():
        res = db.users.update_one(
            {"username": username},
            {"$set": {"assigned_projects": proj_ids}}
        )
        # Also tag projects with assigned_users
        db.projects.update_many(
            {"project_id": {"$in": proj_ids}},
            {"$addToSet": {"assigned_users": username}}
        )
        print(f"Assigned {len(proj_ids)} projects to user '{username}' (matched in users: {res.matched_count})")

    # Verify
    print("\nVerification:")
    for u in db.users.find({}, {"username": 1, "ministry": 1, "assigned_projects": 1}):
        p_count = len(u.get("assigned_projects", []))
        print(f"User: {u.get('username'):<25} | Ministry: {u.get('ministry'):<30} | Assigned Projects: {p_count}")

if __name__ == "__main__":
    main()
