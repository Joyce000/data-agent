from dataclasses import dataclass
from typing import Optional

@dataclass
class ColumnConfig:
    name: str
    role: str
    description: str
    alias: list[str]
    sync: bool

@dataclass
class TableConfig:
    name: str
    role: str
    description: str
    columns: list[ColumnConfig]

@dataclass
class MetricConfig:
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]

@dataclass
class MetaConfig:
    # 所有表配置（可选）
    tables: Optional[list[TableConfig]] = None
    # 所有指标配置（可选）
    metrics: Optional[list[MetricConfig]] = None