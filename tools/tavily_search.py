from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from utils.logger import get_logger
logger = get_logger("web_search_tool")

@tool
def web_search_tool(query: str) -> str:
    """Search web for supplementary spiritual information."""
    logger.info(f"[EXEC] web_search_tool | query={query}")

    tavily_tool = TavilySearchResults(max_results=3)
    results = tavily_tool.run(query)

    summarized = "\n".join(
        r["content"] for r in results[:3]
    )
    
    logger.info(
            f"[RESULT] web_search_tool size={len(str(summarized))} chars"
        )

    return summarized

