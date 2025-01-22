# A subgraph to handle grid-related GenAI

from typing import Any, TypedDict
from langgraph.graph import START, StateGraph
from graphrag.chat.prompts import DIMENTION_EXTRACTION
from langchain_core.prompts import PromptTemplate
from langgraph.types import interrupt
from langgraph.checkpoint.memory import MemorySaver


class GridSubgraphState(TypedDict):
    query: str # the query from the user
    response: str # the response of LLM to the query
    json_schema: str # a stringified version of the schema user to store data in the graph db
    dimensions: list[dict[str, Any]]
    fup_dimension_index: int
    model: Any


# this function should throw an exception (on the interrupt line), that shoud be caught by the function that calls it (in main.py) file. AI!
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
    json_content = response.content.strip().strip('```').strip('json').strip()
    state["dimensions"] = json.loads(json_content) 
    try:
        fup_dimension_index = interrupt({"message" : "Hello World"})
    except  Exception as e:
        return e.args[0][0].value

def generate_fup_query(state: GridSubgraphState):
    print(f"Dimension choses in {state['fup_dimension_index']}")

memory = MemorySaver()

subgraph_builder = StateGraph(GridSubgraphState)
subgraph_builder.add_node(retrieve_candidate_dimensions)
subgraph_builder.add_node(generate_fup_query)
subgraph_builder.add_edge(START, "retrieve_candidate_dimensions")
subgraph_builder.add_edge("retrieve_candidate_dimensions","generate_fup_query")
grid_subgraph = subgraph_builder.compile(checkpointer=memory)

