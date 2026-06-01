from app.conf.app_config import app_config
from qdrant_client.http.models import PointStruct
from qdrant_client.models import VectorParams, Distance
from qdrant_client import AsyncQdrantClient

from app.entities.column_info import ColumnInfo


class ColumnQdrantRepository:
    collections_name = "column_info_collection"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def ensure_collection(self):
        if not await self.client.collection_exists(self.collections_name):
            await self.client.create_collection(
                collection_name=self.collections_name,
                vectors_config=VectorParams(size=app_config.qdrant.embedding_size, distance=Distance.COSINE),
            )

    async def upsert(self, ids: list[str], embeddings: list[list[float]], payloads: list[dict], batch_size: int = 10):
        points: list[PointStruct] = [PointStruct(id=id, vector=embedding, payload=payload) for id, embedding, payload in
                                     zip(ids, embeddings, payloads)]
        await self.client.upsert(collection_name=self.collections_name, points=points)

        for i in range(0, len(points), batch_size):
            await self.client.upsert(collection_name=self.collections_name, points=points[i:i + batch_size])

    async def search(self, keyword_embedding: list[float], score_threshold: float=0.6, limit: int = 10) -> list[ColumnInfo]:
        search_result = await self.client.query_points(
            collection_name=self.collections_name,
            query=keyword_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        return [ColumnInfo(**point.payload) for point in search_result.points]
        


