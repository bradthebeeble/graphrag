# A subgraph to handle grid-related GenAI

from typing import Any, TypedDict
from langgraph.graph import START, StateGraph
from graphrag.chat.prompts import DIMENTION_EXTRACTION
from langchain_core.prompts import PromptTemplate

class GridSubgraphState(TypedDict):
    query: str # the query from the user
    response: str # the response of LLM to the query
    json_schema: str # a stringified version of the schema user to store data in the graph db
    dimensions: list[dict[str, Any]]
    model: Any



def retrieve_candidate_dimensions(state: GridSubgraphState):
    llm = state["model"]
    prompt_template = PromptTemplate.from_template(DIMENTION_EXTRACTION)
    prompt = prompt_template.invoke({
        "user_query" : state["query"],
        "response" : state["response"],
        "json_schema" : state["json_schema"]
    })
    response = llm.invoke(prompt)
    import json
    response_content = json.loads(response.content)
    print(response_content)
    return {"query": "What is your name?"}


subgraph_builder = StateGraph(GridSubgraphState)
subgraph_builder.add_node(retrieve_candidate_dimensions)
subgraph_builder.add_edge(START, "retrieve_candidate_dimensions")
grid_subgraph = subgraph_builder.compile()
