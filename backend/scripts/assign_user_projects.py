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

    # 1. 10 Urban & Infrastructure corridors for User Account (exactly 10 projects)
    user_10_ids = [
        'N28000157', 'N28000122', 'N28000135', '702639', '701766', 
        '702958', 'N28000058', '702637', '617225', 'N28000144'
    ]

    # 2. Flagship Sovereign Projects for MoSPI Admin (28 projects, 25+)
    admin_28_ids = [
        '604795', 'N28000157', 'N28000122', 'N28000135', 'N30000002', 'N28000058',
        'N16000434', '702637', '617225', 'N28000144', 'N28000148', 'N28000086',
        '701415', 'N22000464', '705237', '82792908', 'PRJ_1913', 'N16000513',
        '701263', 'N22000463', 'N16000518', '617321', 'N22000406', '705728',
        '298178', '709798', '705429', '702668'
    ]

    user_assignments = {
        "ramesh.kumar": user_10_ids,
        "pardhu.r25": user_10_ids,
        "balledasivavaraprasad": user_10_ids,
        "balledasivavaraprasad@gmail.com": user_10_ids,
        "balledasivavaraprasad123": user_10_ids,
        "analyst": admin_28_ids,
        "admin": admin_28_ids
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
