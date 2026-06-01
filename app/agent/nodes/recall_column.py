import asyncio

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.entities.column_info import ColumnInfo
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger

async def recall_column(state: DataAgentState, runtime: Runtime[DataAgentContext]) -> dict:
    writer = runtime.stream_writer
    writer({
        "type": "progress",
        "step": "召回字段",
        "status": "running"
    })

    try:
        keywords = state["keywords"]
        query = state["query"]

        column_qdrant_repository = runtime.context["column_qdrant_repository"]
        embedding_client = runtime.context["embedding_client"]

        # 借助LLM扩展关键词
        """
        1.生成提示词prompt，将promp传递给llm进行input
        2.拿到llm的输出并进行解析（结构化输出），传递到下一个结点
        chain = prompt | llm | output_parser    # langchain中的链式，Runnable调用
        """
        prompt = PromptTemplate(
            input_variables=["query"],
            template=load_prompt("extend_keywords_for_column_recall"),
        )

        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke({'query': query})

        keywords = list(set(keywords + result))

        # 从qdrant检索字段信息
        column_info_map:dict[str, ColumnInfo] = {}   # 用于去除重复关键字信息
        for keyword in keywords:
            #先对keyword进行向量化Embedding
            keyword_embedding = await embedding_client.aembed_query(keyword)
            current_column_infos:list[ColumnInfo] = await column_qdrant_repository.search(keyword_embedding)
            for column_info in current_column_infos:
                if column_info.id not in column_info_map:
                    column_info_map[column_info.id] = column_info

        retrieved_column_infos: list[ColumnInfo] = list(column_info_map.values())

        writer({
            "type": "progress",
            "step": "召回字段",
            "status": "success"
        })

        logger.info(f"检索到字段信息：{list(column_info_map.keys())}")
        return {"retrieved_column_infos": retrieved_column_infos}
    except Exception as e:
        logger.error(f"召回字段出错：{e}")
        writer({
            "type": "progress",
            "step": "召回字段",
            "status": "error"
        })
        raise
