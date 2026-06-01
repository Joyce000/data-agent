from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from langchain_core.prompts import PromptTemplate
from app.core.log import logger
from app.entities.metric_info import MetricInfo
from app.prompt.prompt_loader import load_prompt
from langchain_core.output_parsers import JsonOutputParser
from app.repositories.qdrant.metric_qdrant_repositories import MetricQdrantRepository


async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({
        "type": "progress",
        "step": "召回指标信息",
        "status": "running"
    })

    try:
        # await asyncio.sleep(1)

        query = state["query"]
        keywords = state["keywords"]
        metric_qdrant_repository = runtime.context["metric_qdrant_repository"]
        embedding_client = runtime.context["embedding_client"]

        # 借助LLM扩展关键词
        prompt = PromptTemplate(
            input_variables=["query"],
            template=load_prompt("extend_keywords_for_metric_recall"),
        )

        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke({'query': query})

        keywords = list(set(keywords + result))
        # 借助关键词检索指标信息
        # 从qdrant检索字段信息
        metric_info_map: dict[str, MetricInfo] = {}  # 用于去除重复关键字信息
        for keyword in keywords:
            # 先对keyword进行向量化Embedding
            keyword_embedding = await embedding_client.aembed_query(keyword)
            current_metric_infos: list[MetricInfo] = await metric_qdrant_repository.search(keyword_embedding)
            for metric_info in current_metric_infos:
                if metric_info.id not in metric_info_map:
                    metric_info_map[metric_info.id] = metric_info

        retrieved_metric_infos: list[MetricInfo] = list(metric_info_map.values())

        writer({
            "type": "progress",
            "step": "召回指标信息",
            "status": "success"
        })

        logger.info(f"检索到指标信息：{list(metric_info_map.keys())}")
        return {"retrieved_metric_infos": retrieved_metric_infos}
    except Exception as e:
        logger.error(f"召回指标信息出错：{e}")
        writer({
            "type": "progress",
            "step": "召回指标信息",
            "status": "error"
        })
        raise
