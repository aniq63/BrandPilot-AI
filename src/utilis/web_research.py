from langchain_tavily import TavilySearch

from src.utilis.logging import logger, log_calls

tavily_search = TavilySearch(
    max_results=3,
    search_depth="basic",
    topic="general"
)

@log_calls
def perform_web_research(search_queries: list[str]) -> str:
    """
    Executes multiple Tavily searches and combines their results.
    """

    research_results = []

    for query in search_queries:

        try:
            response = tavily_search.invoke({
                "query": query
            })

            results = response.get("results", [])

            for result in results:
                research_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", "")
                })

        except Exception as e:
            logger.warning("Search failed for '%s': %s", query, e)

    # Remove duplicate sources
    unique_results = {}

    for result in research_results:
        url = result.get("url")

        if url and url not in unique_results:
            unique_results[url] = result

    # Format sources for the LLM
    formatted_results = []

    for index, result in enumerate(unique_results.values(), start=1):
        formatted_results.append(
            f"""
            SOURCE {index}
            Title: {result['title']}
            URL: {result['url']}
            Content: {result['content'][:2000]}
            """
        )

    return "\n".join(formatted_results)