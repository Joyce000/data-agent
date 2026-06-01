import asyncio

import yaml

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, TableInfoState, DBInfoState, MetricInfoState, DateInfoState
from langgraph.runtime import Runtime
from langgraph.config import get_stream_writer
from app.prompt.prompt_loader import load_prompt
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.log import logger


async def correct_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({
        "type": "progress",
        "step": "校正sql",
        "status": "running"
    })

    try:
        sql = state["sql"]
        query = state["query"]
        table_infos: list[TableInfoState] = state["table_infos"]
        metric_infos: list[MetricInfoState] = state["metric_infos"]
        db_infos: list[DBInfoState] = state["db_infos"]
        date_infos: list[DateInfoState] = state["date_infos"]
        error = state["error"]

        prompt = PromptTemplate(
            input_variables=["query", "table_infos", "metric_infos", "db_infos", "date_infos", "error"],
            template=load_prompt("correct_sql"),
        )
        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser


        result = await chain.ainvoke({'query': query,
                                      'table_infos': yaml.safe_dump(table_infos, allow_unicode=True, sort_keys=False),
                                      'metric_infos': yaml.safe_dump(metric_infos, allow_unicode=True, sort_keys=False),
                                      'db_infos': yaml.safe_dump(db_infos, allow_unicode=True, sort_keys=False),
                                      'date_infos': yaml.safe_dump(date_infos, allow_unicode=True, sort_keys=False),
                                      'error': error
                                      }
                                     )

        writer({
            "type": "progress",
            "step": "校正sql",
            "status": "success"
        })

        logger.info(f"校正SQL：{result}")
        return {"sql": result}
    except Exception as e:
        logger.error(f"校正SQL出错：{e}")
        writer({
            "type": "progress",
            "step": "校正sql",
            "status": "error"
        })
        raise
