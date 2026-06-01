# from app.conf.app_config import EmbeddingConfig, app_config
# from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings
#
# class EmbeddingClientManager:
#     def __init__(self, config: EmbeddingConfig):
#         self.client: HuggingFaceEndpointEmbeddings | None = None
#         self.config = config
#
#     def _get_url(self):
#         return f"http://{self.config.host}:{self.config.port}"
#
#     def init(self):
#         self.client = HuggingFaceEndpointEmbeddings(model=self._get_url())
#
# embedding_client_manager = EmbeddingClientManager(app_config.embedding)
#
# if __name__ == '__main__':
#     embedding_client_manager.init()
#     client = embedding_client_manager.client
#
#     async def test():
#         text = "What is deep learning?"
#         query_result = await client.aembed_query(text)
#         query_result[:3]
import asyncio

import requests
from langchain_core.embeddings import Embeddings
from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings

from app.conf.app_config import EmbeddingConfig, app_config


class TEIEmbeddings(Embeddings):
    def __init__(self, base_url: str):
        self.url = base_url.rstrip("/") + "/embed"
        self.session = requests.Session()
        self.session.trust_env = False

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = self.session.post(
            self.url,
            json={"inputs": texts},
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class EmbeddingClientManager:
    def __init__(self, config: EmbeddingConfig):
        self.client: HuggingFaceEndpointEmbeddings | None = None
        self.config = config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = TEIEmbeddings(base_url=self._get_url())


embedding_client_manager = EmbeddingClientManager(app_config.embedding)

if __name__ == "__main__":
    embedding_client_manager.init()
    client = embedding_client_manager.client

    async def test():
        text = "What is deep learning?"
        query_result = await client.aembed_query(text)
        print("first 3:", query_result[:3])


    asyncio.run(test())
