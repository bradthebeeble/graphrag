from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, MessagesState, StateGraph
from langchain_core.messages import  HumanMessage, SystemMessage ,ToolMessage
import json


from pydantic import SecretStr

from graphrag.awel.api.graph import init_graph, perform_global_search, perform_local_search

SYSTEM_PROMPT = "You are a helpful assistant. Answer the user's question in the context of the given conversation If it's a business querion, use tools."


# Define a new graph
workflow = StateGraph(state_schema=MessagesState)
model = ChatOpenAI(model=OPENAI_MODEL, api_key=SecretStr(OPENAI_KEY))
model_with_tools = model.bind_tools([perform_local_search, perform_global_search])


# Define the function that calls the model

def call_model(state: MessagesState):
    global model_with_tools
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    
    # Send it to async function perform_global_search. perform it as an asyncio call.
    response = model_with_tools.invoke(messages)
    
    return {"messages": response}

def route_tools(
    state: MessagesState,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "call_tools"
    return END

def call_tools(state: MessagesState):
    tools_by_name = {"MessagesState": perform_global_search, "perform_global_search": perform_global_search}
    messages = state["messages"]
    last_message = messages[-1] 
    output_messages = []
    for tool_call in last_message.tool_calls:
        try:
            selected_tool = tools_by_name[tool_call["name"].lower()]
            tool_msg = selected_tool.invoke(tool_call["args"])
            output_messages.append(
                ToolMessage(
                    content=json.dumps(tool_msg),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        except Exception as e:
            # Return the error if the tool call fails
            output_messages.append(
                ToolMessage(
                    content="",
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                    additional_kwargs={"error": e},
                )
            )
            
    return {"messages": output_messages}

def call_tool_response(state: MessagesState):
    last_message = state["messages"][-1]
    if not isinstance(last_message, ToolMessage):
        raise ValueError("Last message is not a ToolMessage")
    
    output_messages = [AIMessage(content=last_message.content)]
    return {"messages": output_messages}

# Define the (single) node in the graph
workflow.add_node("call_model", call_model)
workflow.add_node("call_tools", call_tools)
workflow.add_node("call_tool_response", call_tool_response)
workflow.add_edge(START, "call_model")
workflow.add_conditional_edges("call_model", route_tools)
workflow.add_edge("call_tools", "call_tool_response")


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


