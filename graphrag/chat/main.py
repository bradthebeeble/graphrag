import json
from typing import Annotated, Any, cast
import uuid
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from graphrag.chat.query_tools_defs import  global_query, local_query
from graphrag.cli.query import run_question_generator
from graphrag.config.load_config import load_config
from pathlib import Path
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.logger.base import ProgressLogger
import logging
from graphrag.logger.factory import LoggerFactory
from graphrag.logger.types import LoggerType
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langgraph.graph import START, END, StateGraph
from langchain_core.runnables.config import RunnableConfig
from typing import TypedDict
from langgraph.types import Command
from rich.console import Console
from rich.markdown import Markdown
from graphrag.chat.awel_logo import AWEL_LOGO
from graphrag.chat.grid_graph import grid_subgraph

class ExtendedMessagesState(TypedDict):
    config_filepath: Path | None
    root_dir: Path 
    messages: Annotated[list, add_messages]
    next_questions_candidates: list[str] 
    dimensions: list[dict[str, Any]]


log = logging.getLogger(__name__)
console = Console()


def _logger(logger: ProgressLogger):
    def info(msg: str, verbose: bool = False):
        log.info(msg)
        if verbose:
            logger.info(msg)

    def error(msg: str, verbose: bool = False):
        log.error(msg)
        if verbose:
            logger.error(msg)

    def success(msg: str, verbose: bool = False):
        log.info(msg)
        if verbose:
            logger.success(msg)

    return info, error, success

progress_logger: ProgressLogger | None = LoggerFactory().create_logger(LoggerType(LoggerType.NONE))
info, error, success = _logger(progress_logger)

workflow = StateGraph(state_schema=ExtendedMessagesState)
SYSTEM_PROMPT = "You are a helpful assistant. Answer the user's question in the context of the given conversation."
openai_api_key: str | None = ""
config: GraphRagConfig  = GraphRagConfig()
llm: ChatOpenAI | None = None
llm_with_tools = None
THREAD_ID = uuid.uuid4()
grid_dimensions: list = []

# Tools call node
def call_tools(state: ExtendedMessagesState):
    tools_by_name = {"local_query": local_query, "global_query": global_query}
    messages = state["messages"]
    last_message = messages[-1] 
    output_messages = []
    for tool_call in last_message.tool_calls:
        try:
            selected_tool = tools_by_name[tool_call["name"].lower()]
            tool_call["args"].update({"config_filepath": state["config_filepath"], "root_dir": state["root_dir"]})
            tool_msg = selected_tool.invoke(tool_call["args"])
            tool_call["args"].pop("config_filepath", None)
            tool_call["args"].pop("root_dir", None)
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
# Define the function that calls the model
def call_model(state: ExtendedMessagesState):
    global llm_with_tools, openai_api_key, _config_filepath, _root_dir
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    if llm_with_tools is None:
        error("OpenAI API key not configured in LLM settings")
    else:
        return {
            "messages": [llm_with_tools.invoke(messages)],
            "config_filepath" : _config_filepath,
            "root_dir" : _root_dir
            }

def call_grid(state: ExtendedMessagesState):
    global grid_dimensions, graph_config, subgraph_config
    # Find the most recent HumanMessage
    recent_human_message = next(
        (msg for msg in reversed(state["messages"]) if isinstance(msg, HumanMessage)),
        None
    )
    from graphrag.awel.templates.dealership import (
        Customer, VehicleModel, CustomerReviewOfVehicle, DealershipVenue,
        DealerNetwork, Insight, SalesMetric, VehicleCategory, MonthYear
    )
    import json

    json_schema = json.dumps({
        "Customer": Customer.model_json_schema(),
        "VehicleModel": VehicleModel.model_json_schema(),
        "CustomerReviewOfVehicle": CustomerReviewOfVehicle.model_json_schema(),
        "DealershipVenue": DealershipVenue.model_json_schema(),
        "DealerNetwork": DealerNetwork.model_json_schema(),
        "Insight": Insight.model_json_schema(),
        "SalesMetric": SalesMetric.model_json_schema(),
        "VehicleCategory": VehicleCategory.model_json_schema(),
        "MonthYear": MonthYear.model_json_schema()
    })

    console.print("[bold red]AWEL:[/bold red] Analyzing data for grid display")

    try:
        response = grid_subgraph.invoke({
            "query": recent_human_message.content if recent_human_message else "",
            "response": state["messages"][-1].content,
            "json_schema": json_schema,
            "model" : llm
        }, config=subgraph_config)
        print("Returned without an exception")
    except Exception as e:
        grid_dimensions = e.args[0][0].value["dimensions"]

    

def call_candidate_fup_questions(state: ExtendedMessagesState):
    is_tool_message = isinstance(state["messages"][-2], ToolMessage) if len(state["messages"]) > 1 else False
    history = []
    next_questions_candidates = []
    if is_tool_message:
        history = [
            msg.content for i, msg in enumerate(state["messages"][:-1])
            if isinstance(msg, HumanMessage) and isinstance(state["messages"][i + 2], ToolMessage)
        ]
        config_filepath = state["config_filepath"]
        root_dir = state["root_dir"]
        console.print("[bold red]AWEL:[/bold red] Generating follow-up candidate questions")
        next_questions_candidates = run_question_generator(
                config_filepath,
                data_dir=None,
                root_dir=root_dir,
                community_level=2,
                query=cast(list[str],history)
            )
    return {
        "next_questions_candidates": next_questions_candidates
    }
def route_tools(
    state: ExtendedMessagesState,
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
        return "tools"
    return END

def command_router(
    state: ExtendedMessagesState,
):
    # for now, just return call_model
    return "call_model"

def display_results(state: ExtendedMessagesState):
    should_fup_with_questions = True

    console.print("[bold magenta]AI:[/bold magenta]")
    import re
    def clean_markdown(raw_markdown):
        # Remove surrounding quotes
        cleaned = raw_markdown.strip('"').strip("'")
        # Replace literal "\n" with actual newlines
        cleaned = cleaned.replace("\\n", "\n")
        # Optionally, normalize whitespace
        cleaned = re.sub(r'\s+\n', '\n', cleaned).strip()
        return cleaned
    markdown = clean_markdown(state['messages'][-1].content)
    console.print(Markdown(markdown))
    if should_fup_with_questions:
        if state["next_questions_candidates"] is not None: # update to check if key "next_questions_candidates" exists. AI!
            console.print("\n\n[bold blue]You can followup with any of these questions by using the /fup [[id]] command[/bold blue]")
            for idx, question in enumerate(state["next_questions_candidates"], start=1):
                console.print(f"[{idx}]: {question}")
    else:
        should_fup_with_questions = True
    
    if grid_dimensions:
        console.print("\n[bold blue]You can ask me to display a grid across any of these dimensions by using /grid [[id]]?[/bold blue]")
        for idx, dimension in enumerate(grid_dimensions, start=1):
            dimension_name = dimension.get("dimension", "Unknown Dimension")
            values = dimension.get("values", [])
            console.print(f"[{idx}] [bold green]{dimension_name}:[/bold green] {', '.join(values[:5])}...")

    console.print("\n\n=======================================================================================\n\n")

# Define the node and edge
workflow.add_node("call_model", call_model)
workflow.add_node("display_results", display_results)
workflow.add_conditional_edges(START, command_router)

workflow.add_edge("call_model", "display_results")

# Add simple in-memory checkpointer
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

INITIAL_RESPONSE_FORMAT = "A single paragraph"
INIITAL_USER_PROMPT = f"Summarize the key points in this body of knowledge. Use global_query tool, and {INITIAL_RESPONSE_FORMAT} as the response type"



def run_chat_loop(root_dir: Path,
                  config_filepath: Path | None):
    """Run an interactive chat loop that echoes user input."""
    global llm, openai_api_key, llm_with_tools, _config_filepath, _root_dir, graph_config, subgraph_config

    _config_filepath = config_filepath
    _root_dir = root_dir
    llm = ChatOpenAI(api_key=SecretStr(str(openai_api_key)), model=config.llm.model)
    llm_with_tools = llm.bind_tools([local_query, global_query])
    graph_config = RunnableConfig({
        "configurable": 
            {"thread_id": THREAD_ID}
            })
    subgraph_config = RunnableConfig({
        "configurable": 
            {"thread_id": uuid.uuid4()}
    })
    console.print("\nEnter your messages (available commands: /summarize , /fup [question id], /dd [cell id]. type /exit to quit):")

    while True:
        try:
            state = app.get_state(graph_config)
            user_input = console.input("\n[bold yellow]You:[/bold yellow] ").strip()

            if user_input.lower() == "/exit":
                print("Goodbye!")
                break
            if user_input.lower().startswith("/fup"):
                try:
                    fup_index = int(user_input.split()[1]) - 1
                    user_input = state.values["next_questions_candidates"][fup_index]
                except (IndexError, ValueError):
                    print("Invalid follow-up command. Please use /fup [question id].")
                    continue
            elif user_input.lower().startswith("/grid"):
                try:
                    grid_index = int(user_input.split()[1]) - 1
                    print(f"Grid index {grid_index}")
                    grid_subgraph.invoke(Command(resume=3), config=subgraph_config)
                except (IndexError, ValueError):
                    print("Invalid grid command. Please use /grid [option id].")
                    continue
            elif user_input.lower().startswith("/summarize"):
                should_fup_with_questions = False
                user_input = "Summarize key themes of data. Use global query tool. Respond in a single short paragraph."

            if user_input:
                ai_msg = app.invoke(
                    {
                        "messages": [
                            HumanMessage(
                                content=user_input
                            ),
                        ],
                    },
                    config=graph_config,
                )
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break
                                                    
def chat_cli(
    root_dir: Path,
    config_filepath: Path | None,
):
    global openai_api_key
    """Run the pipeline with the given config."""
    config = load_config(root_dir, config_filepath)

    openai_api_key = config.llm.api_key
    if not openai_api_key:
        error("OpenAI API key not configured in LLM settings")
    else:
        success("Starting chat")
        console.print(AWEL_LOGO)
        run_chat_loop(root_dir, config_filepath)
