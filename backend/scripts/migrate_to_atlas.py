import os
import sys
import time
import pymongo
from pymongo import MongoClient

LOCAL_URI = os.getenv("LOCAL_MONGODB_URL", "mongodb://localhost:27017")
ATLAS_URI = os.getenv("ATLAS_MONGODB_URL") or os.getenv("MONGODB_URL")
DB_NAME = os.getenv("MONGODB_DB_NAME", "paimana_intelligence")

def migrate():
    if not ATLAS_URI:
        print("ERROR: ATLAS_MONGODB_URL or MONGODB_URL environment variable is required.")
        print("Usage: ATLAS_MONGODB_URL='mongodb+srv://<user>:<pwd>@cluster...' python migrate_to_atlas.py")
        sys.exit(1)

    print("Connecting to Local MongoDB...")
    local_client = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=5000)
    local_db = local_client[DB_NAME]

    print("Connecting to MongoDB Atlas Cluster...")
    atlas_client = MongoClient(ATLAS_URI, serverSelectionTimeoutMS=10000)
    atlas_db = atlas_client[DB_NAME]

    collections_to_migrate = [
        'users',
        'projects',
        'project_snapshots',
        'alerts',
        'investigations',
        'project_features',
        'otp_codes'
    ]

    print("\n--- Starting Data Migration to MongoDB Atlas ---")
    start_time = time.time()

    for col_name in collections_to_migrate:
        local_col = local_db[col_name]
        atlas_col = atlas_db[col_name]

        count = local_col.count_documents({})
        print(f"\nMigrating collection '{col_name}': {count} documents...")

        if count == 0:
            print(f"  Skipping '{col_name}' (empty)")
            continue

        atlas_col.delete_many({})

        cursor = local_col.find({})
        batch = []
        batch_size = 1000
        migrated_count = 0

        for doc in cursor:
            batch.append(doc)
            if len(batch) >= batch_size:
                atlas_col.insert_many(batch, ordered=False)
                migrated_count += len(batch)
                print(f"  Inserted {migrated_count}/{count} docs...")
                batch = []

        if batch:
            atlas_col.insert_many(batch, ordered=False)
            migrated_count += len(batch)
            print(f"  Inserted {migrated_count}/{count} docs...")

        atlas_count = atlas_col.count_documents({})
        print(f"  ✓ Verified '{col_name}' in Atlas: {atlas_count} documents.")

    print("\n--- Creating Indexes on Atlas ---")
    try:
        atlas_db.users.create_index([("username", pymongo.ASCENDING)], unique=True)
        atlas_db.users.create_index([("email", pymongo.ASCENDING)])
        atlas_db.projects.create_index([("project_id", pymongo.ASCENDING)], unique=True)
        atlas_db.project_snapshots.create_index([("project_id", pymongo.ASCENDING), ("month_index", pymongo.ASCENDING)])
        atlas_db.alerts.create_index([("alert_id", pymongo.ASCENDING)], unique=True)
        print("  ✓ Indexes created successfully.")
    except Exception as e:
        print("  Index creation notice:", e)

    elapsed = round(time.time() - start_time, 2)
    print(f"\n🎉 Migration Complete in {elapsed}s!")
    print("Databases in Atlas:", atlas_client.list_database_names())
    print("Collections in database:", atlas_db.list_collection_names())
    for c in atlas_db.list_collection_names():
        print(f"  {c}: {atlas_db[c].count_documents({})} documents")

if __name__ == '__main__':
    migrate()
