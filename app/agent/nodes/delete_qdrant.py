import asyncio

from app.clients.qdrant_client_manager import qdrant_client_manager

qdrant_client_manager.init()
client = qdrant_client_manager.client


async def main():
    dirty_ids = []
    offset = None
    while True:
        points, offset = await client.scroll(
            collection_name="column_info_collection",
            limit=120,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            payload = point.payload or {}
            if "relevant_columns" in payload:
                print("发现脏数据:", point.id, payload)
                dirty_ids.append(point.id)

        if offset is None:
            break

    print("脏数据数量:", len(dirty_ids))
    print("脏数据 IDs:", dirty_ids)
    if dirty_ids:
        await client.delete(
            collection_name="column_info_collection",
            points_selector=dirty_ids,
        )

    await qdrant_client_manager.close()
