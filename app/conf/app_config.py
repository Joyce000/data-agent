# 日志配置
from dataclasses import dataclass
from pathlib import Path

from omegaconf import OmegaConf

# ======================
# 日志配置结构
# ======================
@dataclass
class File:
    enable: bool
    level: str
    path: str
    rotation: str
    retention: str

@dataclass
class Console:
    enable: bool
    level: str

@dataclass
class LoggingConfig:
    file: File
    console: Console

# ======================
# 数据库配置结构
# ======================
@dataclass
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

# ======================
# 向量库 Qdrant
# ======================
@dataclass
class QdrantConfig:
    host: str
    port: int
    embedding_size: int

# ======================
# Embedding 服务
# ======================
@dataclass
class EmbeddingConfig:
    host: str
    port: int
    model: str

# ======================
# ElasticSearch
# ======================
@dataclass
class ESConfig:
    host: str
    port: int
    index_name: str

# ======================
# LLM 大模型
# ======================
@dataclass
class LLMConfig:
    model_name: str
    api_key: str
    base_url: str

# ======================
# 总配置（聚合所有）
# ======================
@dataclass
class AppConfig:
    logging: LoggingConfig
    db_meta: DBConfig
    db_dw: DBConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    es: ESConfig
    llm: LLMConfig

# ======================
# 加载 YAML 并映射到 dataclass
# ======================
config_file = Path(__file__).parents[2] / 'conf' / 'app_config.yaml'
context = OmegaConf.load(config_file)
schema = OmegaConf.structured(AppConfig)
app_config: AppConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))
