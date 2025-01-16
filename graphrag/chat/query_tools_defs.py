
from langchain_core.tools import tool

@tool
def local_query(query: str) -> str:
    """
        Local search method generates answers by combining relevant data from the AI-extracted knowledge-graph with text chunks of the raw documents.
        Use this tool as the default tool, unless the question includes q request for aggregated or summarization data.
        This method is suitable for questions that require an understanding of specific entities mentioned in the documents
        (e.g. What are the healing properties of chamomile?).
    """

    return "Local bears are everywhere"

@tool
def global_query(query: str) -> str:
    """
        Global search method generates answers by searching over all AI-generated community reports in a map-reduce fashion.
        Use this tool as a second priroty, for questions that are of an aggregated or summarization nature.
        This is a resource-intensive method, but often gives good responses for questions that require an understanding of the dataset as a whole
        (e.g. What are the most significant values of the herbs mentioned in this notebook?).
    """

    return "Global bees are where can be"