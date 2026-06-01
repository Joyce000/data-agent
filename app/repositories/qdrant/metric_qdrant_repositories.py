from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance
from qdrant_client.http.models import PointStruct
from app.conf.app_config import app_config
from app.entities.metric_info import MetricInfo


class MetricQdrantRepository:
    collection_name = "metric_info_collection"
    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def ensure_collection(self):
        if not await self.client.collection_exists(self.collection_name):
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=app_config.qdrant.embedding_size, distance=Distance.COSINE)
            )

    async def upsert(self, ids: list[str], embeddings: list[list[float]], payloads: list[dict], batch_size: int = 10):
        points: list[PointStruct] = [PointStruct(id=id, vector=embedding, payload=payload) for id, embedding, payload in
                                     zip(ids, embeddings, payloads)]
        await self.client.upsert(collection_name=self.collection_name, points=points)

        for i in range(0, len(points), batch_size):
            await self.client.upsert(collection_name=self.collection_name, points=points[i:i + batch_size])

    async def search(self, keyword_embedding: list[float], score_threshold: float=0.6, limit: int = 10)-> list[MetricInfo]:
        search_result = await self.client.query_points(
            collection_name=self.collection_name,
            query=keyword_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        return [MetricInfo(**point.payload) for point in search_result.points]