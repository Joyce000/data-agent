import yaml

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, MetricInfoState
from langgraph.runtime import Runtime
from app.prompt.prompt_loader import load_prompt
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.core.log import logger


async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({
        "type": "progress",
        "step": "过滤指标信息",
        "status": "running"
    })

    try:
        metric_infos: list[MetricInfoState] = state["metric_infos"]
        query = state["query"]

        prompt = PromptTemplate(
            input_variables=["query", "metric_infos"],
            template=load_prompt("filter_metric_info"),
        )

        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke({'query': query,
                                      'metric_infos': yaml.safe_dump(metric_infos, allow_unicode=True, sort_keys=False)}
                                     )

        filtered_metric_infos = [metric_info for metric_info in metric_infos if metric_info["name"] in result]

        writer({
            "type": "progress",
            "step": "过滤指标信息",
            "status": "success"
        })

        logger.info(f"过滤指标信息：{[filtered_metric_info['name'] for filtered_metric_info in filtered_metric_infos]}")
        return {"metric_infos": filtered_metric_infos}
    except Exception as e:
        logger.error(f"过滤指标信息出错：{e}")
        writer({
            "type": "progress",
            "step": "过滤指标信息",
            "status": "error"
        })
        raise
