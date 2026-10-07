from typing import Any, Dict, List, Optional
from pymongo import ReturnDocument
from app.db.mongodb import get_database


def _strip_id(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    doc = dict(doc)
    doc.pop("_id", None)
    return doc


class MongoRepository:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    def _col(self):
        db = get_database()
        if db is None:
            return None
        return db[self.collection_name]

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        col = self._col()
        if col is None:
            return None
        return _strip_id(await col.find_one(query, {"_id": 0}))

    async def find_many(
        self,
        query: Dict[str, Any],
        *,
        sort: Optional[List] = None,
        skip: int = 0,
        limit: int = 200,
        projection: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, Any]]:
        col = self._col()
        if col is None:
            return []
        proj = {"_id": 0}
        if projection:
            proj.update(projection)
        cursor = col.find(query, proj)
        if sort:
            cursor = cursor.sort(sort)
        cursor = cursor.skip(skip).limit(limit)
        rows = await cursor.to_list(length=limit)
        for row in rows:
            row.pop("_id", None)
        return rows

    async def insert_one(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        col = self._col()
        payload = dict(doc)
        if col is not None:
            await col.insert_one(payload)
        payload.pop("_id", None)
        return payload

    async def insert_many(self, docs: List[Dict[str, Any]]) -> int:
        col = self._col()
        if col is None or not docs:
            return 0
        await col.insert_many(list(docs))
        return len(docs)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        col = self._col()
        if col is None:
            return None
        doc = await col.find_one_and_update(
            query,
            {"$set": update},
            return_document=ReturnDocument.AFTER,
            projection={"_id": 0},
        )
        return _strip_id(doc)

    async def count(self, query: Dict[str, Any]) -> int:
        col = self._col()
        if col is None:
            return 0
        return await col.count_documents(query)

    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        col = self._col()
        if col is None:
            return []
        return await col.aggregate(pipeline).to_list(length=5000)
