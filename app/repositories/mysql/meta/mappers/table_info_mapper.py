from dataclasses import asdict

from app.entities.table_info import TableInfo
from app.models.table_info_mysql import TableInfoMySQL


class TableInfoMapper:
    @staticmethod
    def to_entity(table_info: TableInfoMySQL) -> TableInfo:
        return TableInfo(
            id=table_info.id,
            name=table_info.name,
            role=table_info.role,
            description=table_info.description
        )

    @staticmethod
    def to_model(table_info: TableInfo) -> TableInfoMySQL:
        return TableInfoMySQL(**asdict(table_info))