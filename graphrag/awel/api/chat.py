from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

from pydantic import SecretStr

from graphrag.awel.api.graphrag import init_graph, perform_global_search

OPENAI_KEY = "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"
OPENAI_MODEL = "gpt-4o-mini"

# Define a new graph
workflow = StateGraph(state_schema=MessagesState)
model = ChatOpenAI(model=OPENAI_MODEL, api_key=SecretStr(OPENAI_KEY))


# Define the function that calls the model
def call_model(state: MessagesState):
    global model
    # Pick up the last message in state["messages"]
    last_message = state["messages"][-1]
    
    # Send it to async function perform_global_search. perform it as an asynchio call. AI!
    response = await perform_global_search(query=last_message.content)
    
    return {"messages": response}


# Define the (single) node in the graph
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

# Add memory
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
init_graph()

def process_query(thread_id: str, query: str):
    global model
    config = {"configurable": {"thread_id": thread_id}}
    input_messages = [HumanMessage(query)]
    output = app.invoke({"messages": input_messages}, config)
    response = output["messages"][-1]
    return response.content


