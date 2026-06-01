import asyncio

from elasticsearch import AsyncElasticsearch

from app.conf.app_config import app_config, ESConfig


class ESClientManager:
    def __init__(self, config: ESConfig):
        self.client: AsyncElasticsearch | None = None
        self.config: ESConfig = config #保存配置（host/port 等）

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncElasticsearch(hosts=[self._get_url()])
    async def close(self):
        await self.client.close()

# 创建全局唯一的 ES 客户端管理器
es_client_manager = ESClientManager(app_config.es)

if __name__ == "__main__":
    es_client_manager.init()
    client = es_client_manager.client

    async def test():
        # await client.indices.create(
        #     index="books",
        # )

        await client.index(
            index="books",
            document={
                "name": "Snow Crash",
                "author": "Neal Stephenson",
                "release_date": "1992-06-01",
                "page_count": 470
            },
        )

        resp = await client.search(
            index="books",
        )
        print(resp)
        await es_client_manager.close()

    asyncio.run(test())