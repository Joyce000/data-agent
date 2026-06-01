import asyncio
import uuid
from dataclasses import asdict
from pathlib import Path
from omegaconf import OmegaConf

from app.conf.meta_config import MetaConfig
from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.entities.value_info import ValueInfo
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repositories import DWMySQLRepositories

from app.repositories.mysql.meta.meta_mysql_repositories import MetaMySQLRepositories
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings

from app.repositories.qdrant.metric_qdrant_repositories import MetricQdrantRepository
from app.core.log import logger


class MetaKnowledgeService:
    def __init__(self,
                 meta_mysql_repositories: MetaMySQLRepositories,
                 dw_mysql_repositories: DWMySQLRepositories,
                 column_qdrant_repository: ColumnQdrantRepository,
                 embedding_client: HuggingFaceEndpointEmbeddings,
                 value_es_repository: ValueESRepository,
                 metric_qdrant_repository: MetricQdrantRepository
                 ):

        self.meta_mysql_repositories: MetaMySQLRepositories = meta_mysql_repositories
        self.dw_mysql_repositories: DWMySQLRepositories = dw_mysql_repositories
        self.column_qdrant_repository: ColumnQdrantRepository = column_qdrant_repository
        self.embedding_client: HuggingFaceEndpointEmbeddings = embedding_client
        self.value_es_repository: ValueESRepository = value_es_repository
        self.metric_qdrant_repository: MetricQdrantRepository = metric_qdrant_repository

    async def _save_tables_to_meta_db(self, meta_config: MetaConfig) -> list[ColumnInfo]:
        table_infos: list[TableInfo] = []
        column_infos: list[ColumnInfo] = []
        # 2.1将表信息和字段信息保存meta数据库中
        for table in meta_config.tables:
            # table -> table_info
            table_info = TableInfo(id=table.name,
                                   name=table.name,
                                   role=table.role,
                                   description=table.description)
            table_infos.append(table_info)

            # 查询字段类型
            column_types = await self.dw_mysql_repositories.get_column_type(table.name)

            for column in table.columns:
                # 查询字段取值示例
                column_values = await self.dw_mysql_repositories.get_column_values(table.name, column.name)

                # column -> column_info
                column_info = ColumnInfo(id=f"{table.name}.{column.name}",
                                         name=column.name,
                                         type=column_types[column.name],
                                         role=column.role,
                                         examples=column_values,
                                         description=column.description,
                                         alias=column.alias,
                                         table_id=table.name
                                         )

                column_infos.append(column_info)
        # 开启一个异步数据库事务（自动管理提交/回滚）
        async with self.meta_mysql_repositories.session.begin():  # 事务回滚，begin()方法有自己的生命周期
            self.meta_mysql_repositories.save_table_info(table_infos)
            self.meta_mysql_repositories.save_column_info(column_infos)
        return column_infos

    async def _save_colunmns_to_qdrant(self, column_infos: list[ColumnInfo]):
        await self.column_qdrant_repository.ensure_collection()

        points: list[dict] = []

        for column_info in column_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.name,
                "payload": asdict(column_info)
            })

            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.description,
                "payload": asdict(column_info)
            })

            for alias in column_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alias,
                    "payload": asdict(column_info)
                })
        # 批量插入向量索引
        embeddings: list[list[float]] = []
        embedding_texts = [point['embedding_text'] for point in points]
        embedding_bach_size = 10
        for i in range(0, len(points), embedding_bach_size):
            batch_embeddings_texts = embedding_texts[i:i + embedding_bach_size]
            batch_embeddings = await self.embedding_client.aembed_documents(batch_embeddings_texts)
            embeddings.extend(batch_embeddings)

        ids = [point['id'] for point in points]
        payloads = [point['payload'] for point in points]
        await self.column_qdrant_repository.upsert(ids, embeddings, payloads)
        await asyncio.sleep(0.5)

    async def _save_values_to_es(self, meta_config: MetaConfig):
        await self.value_es_repository.ensure_index()

        values_infos: list[ValueInfo] = []

        for table in meta_config.tables:
            for column in table.columns:
                if column.sync:  # 该字段是否要建立全文索引
                    current_values: list[str] = await self.dw_mysql_repositories.get_column_values(table.name,
                                                                                                   column.name,
                                                                                                   limit=100000)
                    current_column_infos = [ValueInfo(id=f"{table.name}.{column.name}.{current_column_value}",
                                                      value=current_column_value,
                                                      column_id=f"{table.name}.{column.name}") for
                                            current_column_value in current_values]
                    values_infos.extend(current_column_infos)

        await self.value_es_repository.upsert(values_infos)

    async def _save_metrics_to_meta_db(self, meta_config: MetaConfig) -> list[MetricInfo]:
        metric_infos: list[MetricInfo] = []
        column_metrics: list[ColumnMetric] = []

        for metric in meta_config.metrics:
            # metric->MetricInfo
            metric_info = MetricInfo(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias
            )
            metric_infos.append(metric_info)
            for column in metric.relevant_columns:
                # column->ColumnMetric
                column_metric = ColumnMetric(
                    column_id=column,
                    metric_id=metric.name
                )
                column_metrics.append(column_metric)
        async with self.meta_mysql_repositories.session.begin():
            self.meta_mysql_repositories.save_metric_info(metric_infos)
            self.meta_mysql_repositories.save_column_metric(column_metrics)

        return metric_infos

    async def _save_metrics_to_qdrant(self, metric_infos: list[MetricInfo]):
        await self.metric_qdrant_repository.ensure_collection()

        points: list[dict] = []

        for metric_info in metric_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.name,
                "payload": asdict(metric_info)
            })

            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.description,
                "payload": asdict(metric_info)
            })

            for alias in metric_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alias,
                    "payload": asdict(metric_info)
                })
        # 批量插入向量索引
        embeddings: list[list[float]] = []
        embedding_texts = [point['embedding_text'] for point in points]
        embedding_bach_size = 10
        for i in range(0, len(points), embedding_bach_size):
            batch_embeddings_texts = embedding_texts[i:i + embedding_bach_size]
            batch_embeddings = await self.embedding_client.aembed_documents(batch_embeddings_texts)
            embeddings.extend(batch_embeddings)

        ids = [point['id'] for point in points]
        payloads = [point['payload'] for point in points]
        await self.column_qdrant_repository.upsert(ids, embeddings, payloads)
        await asyncio.sleep(0.5)

        await self.metric_qdrant_repository.upsert(ids, embeddings, payloads)

    async def build(self, config_path: Path):
        # 1.读配置文件
        context = OmegaConf.load(config_path)
        schema = OmegaConf.structured(MetaConfig)
        meta_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))
        logger.info("加载配置文件成功")

        # 2.根据配置文件同步指定的表信息
        if meta_config.tables:
            column_infos = await self._save_tables_to_meta_db(meta_config)
            logger.info("保存表信息和字段信息到数据库成功")
            # 2.2对字段信息建立向量索引
            await self._save_colunmns_to_qdrant(column_infos)
            logger.info("保存字段信息到向量索引成功")

            # 2.3对指定的维度字段建立全文索引
            await self._save_values_to_es(meta_config)
            logger.info("保存字段值信息到全文索引成功")

        # 3.根据配置文件同步指定的指标信息
        if meta_config.metrics:
            # 3.1将表信息和字段信息保存meta数据库中
            metric_infos = await self._save_metrics_to_meta_db(meta_config)
            logger.info("保存指标信息到数据库成功")

            # 3.2对字段信息建立向量索引
            await self._save_metrics_to_qdrant(metric_infos)
            logger.info("保存指标信息到向量索引成功")