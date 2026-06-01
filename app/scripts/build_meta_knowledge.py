import argparse
import asyncio

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.mysql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.core.log import logger
from pathlib import Path
from app.clients.es_client_manager import es_client_manager
from app.repositories.es.value_es_repository import ValueESRepository

from app.repositories.mysql.dw.dw_mysql_repositories import DWMySQLRepositories
from app.repositories.mysql.meta.meta_mysql_repositories import MetaMySQLRepositories
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repositories import MetricQdrantRepository
from app.services.meta_knowledge_service import MetaKnowledgeService


# python -m app.scripts.build_meta_knowledge 执行脚本使用python -m，会把根目录加入path
async def build(config_path: Path):
    meta_mysql_client_manager.init()
    dw_mysql_client_manager.init()
    qdrant_client_manager.init()
    embedding_client_manager.init()
    es_client_manager.init()

    async with meta_mysql_client_manager.session_factory() as meta_session, dw_mysql_client_manager.session_factory() as dw_session:
        meta_mysql_repositories = MetaMySQLRepositories(meta_session)
        dw_mysql_repositories = DWMySQLRepositories(dw_session)

        column_qdrant_repository = ColumnQdrantRepository(qdrant_client_manager.client)

        value_es_repository = ValueESRepository(es_client_manager.client)

        metric_qdrant_repository = MetricQdrantRepository(qdrant_client_manager.client)

        meta_knowledge_service = MetaKnowledgeService(meta_mysql_repositories=meta_mysql_repositories,
                                                      dw_mysql_repositories=dw_mysql_repositories,
                                                      column_qdrant_repository=column_qdrant_repository,
                                                      embedding_client=embedding_client_manager.client,
                                                      value_es_repository=value_es_repository,
                                                      metric_qdrant_repository=metric_qdrant_repository
                                                      )

        await meta_knowledge_service.build(Path(config_path))

        logger.info("Building docker image...")

    await meta_mysql_client_manager.close()
    await dw_mysql_client_manager.close()
    await qdrant_client_manager.close()
    await es_client_manager.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", '--conf')
    # parser.add_argument("--age", type=int, help="输入你的年龄", default=18)
    # parser.add_argument("--debug", action="store_true", help="是否开启调试模式")

    # 3. 解析参数
    args = parser.parse_args()
    # 4. 使用参数
    config_path = args.conf

    asyncio.run(build(Path(config_path)))
