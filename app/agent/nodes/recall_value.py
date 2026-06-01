from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime

from app.entities.value_info import ValueInfo
from app.prompt.prompt_loader import load_prompt
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.core.log import logger


async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({
        "type": "progress",
        "step": "召回字段取值",
        "status": "running"
    })

    try:
        query = state["query"]
        keywords = state["keywords"]
        value_es_repository = runtime.context["value_es_repository"]
        # 借助LLM扩展关键词
        prompt = PromptTemplate(
            input_variables=["query"],
            template=load_prompt("extend_keywords_for_value_recall"),
        )
        output_parser = JsonOutputParser()

        chain = prompt | llm | output_parser

        result = await chain.ainvoke({'query': query})

        keywords = list(set(keywords + result))
        # 借助关键词检索指标信息
        value_infos_maps: dict[str, ValueInfo] = {}  # 用于去除重复关键字信息
        for keyword in keywords:
            current_value_infos: list[ValueInfo] = await value_es_repository.search(keyword)
            for current_value_info in current_value_infos:
                if current_value_info.id not in value_infos_maps:
                    value_infos_maps[current_value_info.id] = current_value_info

        retrieved_value_infos: list[ValueInfo] = list(value_infos_maps.values())

        writer({
            "type": "progress",
            "step": "召回字段取值",
            "status": "success"
        })

        logger.info(f"检索到字段取值信息：{list(value_infos_maps.keys())}")
        return {"retrieved_value_infos": retrieved_value_infos}
    except Exception as e:
        logger.error(f"召回字段取值出错：{e}")
        writer({
            "type": "progress",
            "step": "召回字段取值",
            "status": "error"
        })
        raise