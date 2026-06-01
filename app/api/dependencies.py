from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.services.query_service import QueryService

from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repositories import DWMySQLRepositories
from app.repositories.mysql.meta.meta_mysql_repositories import MetaMySQLRepositories
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repositories import MetricQdrantRepository

from typing import Annotated

from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession


# """
# 官方
# meta = MetaSession()
# try:
#     yield meta_session
# finally
#     meta.close()
# """
async def get_meta_session():
    async with meta_mysql_client_manager.session_factory() as meta_session:
        yield meta_session


async def get_dw_session():
    async with dw_mysql_client_manager.session_factory() as dw_session:
        yield dw_session


async def get_meta_mysql_repository(
        session: Annotated[AsyncSession, Depends(get_meta_session)]) -> MetaMySQLRepositories:
    return MetaMySQLRepositories(session)


async def get_dw_mysql_repository(session: Annotated[AsyncSession, Depends(get_dw_session)]) -> DWMySQLRepositories:
    return DWMySQLRepositories(session)


async def get_column_qdrant_repository() -> ColumnQdrantRepository:
    return ColumnQdrantRepository(qdrant_client_manager.client)


async def get_metric_qdrant_repository() -> MetricQdrantRepository:
    return MetricQdrantRepository(qdrant_client_manager.client)


async def get_value_es_repository() -> ValueESRepository:
    return ValueESRepository(es_client_manager.client)


async def get_embedding_client() -> HuggingFaceEndpointEmbeddings:
    return embedding_client_manager.client


# 子依赖项注入
async def get_query_service(meta_mysql_repository: Annotated[MetaMySQLRepositories, Depends(get_meta_mysql_repository)],
                            dw_mysql_repository: Annotated[DWMySQLRepositories, Depends(get_dw_mysql_repository)],
                            column_qdrant_repository: Annotated[
                                ColumnQdrantRepository, Depends(get_column_qdrant_repository)],
                            metric_qdrant_repository: Annotated[
                                MetricQdrantRepository, Depends(get_metric_qdrant_repository)],
                            value_es_repository: Annotated[ValueESRepository, Depends(get_value_es_repository)],
                            embedding_client: Annotated[HuggingFaceEndpointEmbeddings, Depends(get_embedding_client)],
                            ) -> QueryService:
    return QueryService(
        meta_mysql_repository=meta_mysql_repository,
        dw_mysql_repository=dw_mysql_repository,
        column_qdrant_repository=column_qdrant_repository,
        metric_qdrant_repository=metric_qdrant_repository,
        value_es_repository=value_es_repository,
        embedding_client=embedding_client
    )
