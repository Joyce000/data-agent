import asyncio

from app.conf.app_config import DBConfig,app_config
from sqlalchemy.ext.asyncio import create_async_engine,AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from sqlalchemy.pool import NullPool
class MySQLManager:
    def __init__(self, config: DBConfig):
        self.engine: AsyncEngine | None = None
        self.session_factory = None
        self.config = config

    def _get_url(self):
        return f"mysql+asyncmy://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}?charset=utf8mb4"
    def init(self):
        self.engine = create_async_engine(self._get_url(), poolclass=NullPool, pool_pre_ping=True)#测试脚本不用连接池，可以避免连接池里残留连接 ,正式使用时使用pool_size=10,。
        self.session_factory = async_sessionmaker(self.engine, autoflush=True, expire_on_commit=False)

    async def close(self):
        await self.engine.dispose()
        await asyncio.sleep(0.2)

meta_mysql_client_manager = MySQLManager(app_config.db_meta)
dw_mysql_client_manager = MySQLManager(app_config.db_dw)

if __name__ == '__main__':
    dw_mysql_client_manager.init()
    engine = dw_mysql_client_manager.engine

    async def test():
        async with dw_mysql_client_manager.session_factory() as session:
        #=AsyncSession(engine, autoflush=True, expire_on_commit=False),.session_factory()调用__call__即调用对象
        # session_factory() 返回 AsyncSession
        # async with 进入 session 上下文，请求结束后自动关闭 session

            sql = "select * from fact_order limit 10"
            result = await session.execute(text(sql))

            rows = result.mappings().fetchall()
            print(rows)
            print(type(rows))
            print(type(rows[1]))
            print(rows[1])
            #print(rows[1]['order_id'])

        await dw_mysql_client_manager.engine.dispose()
    asyncio.run(test())
