import re
import os
import pymongo
from dotenv import load_dotenv

load_dotenv("backend/.env")
mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
db_name = os.getenv("MONGODB_DB_NAME", "paimana_intelligence")

def main():
    print(f"Connecting to MongoDB: {mongo_url[:35]}... db: {db_name}")
    client = pymongo.MongoClient(mongo_url)
    db = client[db_name]

    print("=== ASSIGNING USER-PROJECT ASSOCIATIONS IN MONGODB ===")

    # 1. MoRTH projects for Dr. Ramesh Kumar and Pardhu
    morth_projects = list(db.projects.find(
        {"ministry": re.compile(r"Road Transport", re.IGNORECASE)},
        {"project_id": 1, "project_name": 1, "state": 1}
    ).sort("dphis", -1).limit(30))

    ramesh_ids = [p["project_id"] for p in morth_projects[:12]]
    pardhu_ids = [p["project_id"] for p in morth_projects[10:20]]

    # 2. Urban Affairs projects for Siva and Siva123 (17 assigned projects for user demo)
    siva_ids = [
        'N28000157', 'N28000122', 'N28000135', '702639', '701766', 
        '702958', 'N28000058', '702637', '617225', 'N28000144', 
        'N28000148', 'N28000086', 'PRJ_1913', '82792908', '617321', 
        'N22000464', '705237'
    ]
    siva123_ids = siva_ids[:10]

    # 3. National high-risk portfolio for Lead Risk Analyst
    risk_projects = list(db.projects.find(
        {"risk_level": {"$in": ["high", "critical"]}},
        {"project_id": 1, "project_name": 1, "ministry": 1}
    ).sort("dphis", -1).limit(15))
    analyst_ids = [p["project_id"] for p in risk_projects]

    # 4. Flagship Sovereign Projects for MoSPI Admin (28 projects, 25+)
    admin_ids = [
        '82792908', '617321', 'N22000464', '705237', 'N22000463', 
        '705728', '701263', 'N16000513', '702668', 'N30000002', 
        '701415', 'N16000518', '709798', 'N22000406', '705429', 
        '298178', 'N28000086', '702637', '604795', 'N16000434',
        'N28000157', 'N28000122', 'N28000135', '617225', 'N28000144', 
        'N28000148', 'N28000058', 'PRJ_1913'
    ]

    user_assignments = {
        "ramesh.kumar": ramesh_ids,
        "pardhu.r25": pardhu_ids,
        "balledasivavaraprasad": siva_ids,
        "balledasivavaraprasad@gmail.com": siva_ids,
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
