import asyncio
from datetime import date

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, DateInfoState, DBInfoState
from langgraph.runtime import Runtime
from app.core.log import logger

async def add_extra_context(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({
        "type": "progress",
        "step": "添加额外的上下文",
        "status": "running"
    })

    try:
        dw_mysql_repository = runtime.context["dw_mysql_repository"]

        today = date.today()    #得到日期
        date_str=today.strftime("%Y-%m-%d")      #格式化日期
        weekday = today.strftime("%A")  #得到星期
        quarter = f"Q{(today.month-1)//3 + 1}"  #得到季度

        date_infos = DateInfoState(date=date_str, weekday=weekday, quarter=quarter)

        db = await dw_mysql_repository.get_db_info()
        db_infos = DBInfoState(**db)

        writer({
            "type": "progress",
            "step": "添加额外的上下文",
            "status": "success"
        })

        logger.info(f"数据库信息：{db_infos}\n时间信息：{date_infos}")

        return {"date_infos": date_infos, "db_infos": db_infos}
    except Exception as e:
        logger.error(f"添加额外上下文出错：{e}")
        writer({
            "type": "progress",
            "step": "添加额外的上下文",
            "status": "error"
        })
        raise

