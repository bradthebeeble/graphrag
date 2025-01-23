import json
from typing import Annotated, Any, cast
import uuid
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr
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
from graphrag.chat.prompts import DIMENTION_EXTRACTION, QUERY_GENERATION
from langchain_core.prompts import PromptTemplate
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph


class ExtendedMessagesState(TypedDict):
    config_filepath: Path | None
    root_dir: Path 
    messages: Annotated[list, add_messages]
    next_questions_candidates: list[str] 
    dimensions: list[dict[str, Any]]
    next_command: str
    next_command_idx: int
    last_user_query: str
    last_response: str
    generated_db_query: str



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
SYSTEM_PROMPT = "You are a helpful assistant. Answer the user's question in the context of the given conversation If it's a business querion, use tools."
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
        response_message = llm_with_tools.invoke(messages)
        return_data = {
            "messages": [response_message],
            "config_filepath" : _config_filepath,
            "root_dir" : _root_dir
        }
        if not hasattr(response_message, "tool_calls") or len(response_message.tool_calls) == 0:
            return_data["last_response"] = response_message.content
        return return_data

def call_grid(state: ExtendedMessagesState):
    global llm, json_schema
    COUNT = 5
    prompt_template = PromptTemplate.from_template(QUERY_GENERATION)
    
    console.print("[bold red]AWEL:[/bold red] Generating grid query")
    idx = state["next_command_idx"]
    try:
        if idx is None:
            return
        prompt = prompt_template.invoke({
            "user_query" : state["last_user_query"],
            "response" : state["last_response"],
            "json_schema" : json_schema,
            "dimension" : state["dimensions"][idx],
            "count" : COUNT
        })
        response = llm.invoke(prompt)
        console.print(f"[bold green]Grid Query Result:[/bold green] {response.content}")
        return {
            "generated_db_query" : response.content
        }
    except Exception as e:
        log.error(f"Error generating grid query: {e}")
        return

def call_db(state: ExtendedMessagesState):
    global openai_api_key
    if not state.get("generated_db_query"):
        return
    graph = Neo4jGraph(url=neo4j_config.uri,
                        username=neo4j_config.username,
                        password=neo4j_config.password,
    )
    graph.refresh_schema()
    chain = GraphCypherQAChain.from_llm(
        ChatOpenAI(temperature=0, api_key=openai_api_key, model=config.llm.model),
          graph=graph, verbose=True,
          allow_dangerous_requests=True,
          return_direct=True,
    )
    response = chain.invoke({
        "query" : state["generated_db_query"]
    })
    import pandas as pd

    result_data = [item['dv'] for item in response["result"]]
    df = pd.DataFrame(result_data)
    row_header = [key for key in result_data[0].keys() if key not in {'title', 'human_readable_id', 'dirty', 'id'}]
    print(df)

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
        return "call_tools"
    return "call_fup_candidate_questions"

def call_retrieve_candidate_dimensions(state: ExtendedMessagesState):
    global llm, json_schema
    prompt_template = PromptTemplate.from_template(DIMENTION_EXTRACTION)
    
    console.print("[bold red]AWEL:[/bold red] Analyzing data for grid display")

    prompt = prompt_template.invoke({
        "user_query" : state["last_user_query"],
        "response" : state["last_response"],
        "json_schema" : json_schema
    })
    response = llm.invoke(prompt)
    json_content = response.content.strip().strip('```').strip('json').strip()
    return {"dimensions" :  json.loads(json_content) }

def command_router(
    state: ExtendedMessagesState,
):
    if state.get("next_command") is not None:
        if state["next_command"] == "grid":
            return "call_grid"
    return "call_model"

def display_results(state: ExtendedMessagesState):
    should_fup_with_questions = True

    console.print("[bold magenta]AI:[/bold magenta]")
    import re
    if state.get("next_command") == "grid":
        console.print("Grid Results")
    else:
        def clean_markdown(raw_markdown):
            # Remove surrounding quotes
            cleaned = raw_markdown.strip('"').strip("'")
            # Replace literal "\n" with actual newlines
            cleaned = cleaned.replace("\\n", "\n")
            # Optionally, normalize whitespace
            cleaned = re.sub(r'\s+\n', '\n', cleaned).strip()
            return cleaned
        llm_response = state['messages'][-1].content
        markdown = clean_markdown(llm_response)
        console.print(Markdown(markdown))
        if should_fup_with_questions:
            if "next_questions_candidates" in state and state["next_questions_candidates"] is not None:
                console.print("\n\n[bold blue]You can followup with any of these questions by using the /fup [[id]] command[/bold blue]")
                for idx, question in enumerate(state["next_questions_candidates"], start=1):
                    console.print(f"[{idx}]: {question}")
        else:
            should_fup_with_questions = True

        grid_dimensions = state["dimensions"]
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
workflow.add_node("call_tools", call_tools)
workflow.add_node("call_grid", call_grid)
workflow.add_node("call_db", call_db)
workflow.add_node("call_retrieve_candidate_dimensions", call_retrieve_candidate_dimensions)
workflow.add_node("call_fup_candidate_questions", call_candidate_fup_questions)
workflow.add_conditional_edges(START, command_router)
workflow.add_conditional_edges("call_model", route_tools)
workflow.add_edge("call_tools", "call_model")
workflow.add_edge("call_fup_candidate_questions", "call_retrieve_candidate_dimensions")
workflow.add_edge("call_retrieve_candidate_dimensions", "display_results")
workflow.add_edge("call_grid", "call_db")
workflow.add_edge("call_db", "display_results")



# Add simple in-memory checkpointer
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

INITIAL_RESPONSE_FORMAT = "A single paragraph"
INIITAL_USER_PROMPT = f"Summarize the key points in this body of knowledge. Use global_query tool, and {INITIAL_RESPONSE_FORMAT} as the response type"



def run_chat_loop(root_dir: Path,
                  config_filepath: Path | None):
    """Run an interactive chat loop that echoes user input."""
    global llm, openai_api_key, llm_with_tools, _config_filepath, _root_dir, graph_config, subgraph_config, json_schema

    _config_filepath = config_filepath
    _root_dir = root_dir
    llm = ChatOpenAI(api_key=SecretStr(str(openai_api_key)), model=config.llm.model)
    llm_with_tools = llm.bind_tools([local_query, global_query])
    graph_config = RunnableConfig({
        "configurable": 
            {"thread_id": THREAD_ID}
            })
    import json
    import inspect
    import graphrag.awel.templates.dealership as dealership
    json_schema = json.dumps({
        name: cls.model_json_schema()
        for name, cls in inspect.getmembers(dealership, inspect.isclass)
        if not name.startswith('ListOf')
        if issubclass(cls, BaseModel) and cls is not BaseModel
    })
   
    console.print("\nEnter your messages (available commands: /summarize , /fup [question id], /dd [cell id]. type /exit to quit):")

    while True:
        try:
            state = app.get_state(graph_config)
            user_input = console.input("\n[bold yellow]You:[/bold yellow] ").strip()
            command = None
            command_arg = None
            if user_input.startswith("/"):
                parts = user_input.split()
                command = parts[0][1:]
                if len(parts) > 1 and parts[1].isdigit():
                    command_arg = int(parts[1]) -1
            else:
                command = None
                command_arg = None

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
                        "next_command" : command,
                        "next_command_idx" : command_arg,
                        "last_user_query" : user_input
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
    global openai_api_key, neo4j_config
    """Run the pipeline with the given config."""
    config = load_config(root_dir, config_filepath)

    openai_api_key = config.llm.api_key
    neo4j_config = config.neo4j
    if not openai_api_key:
        error("OpenAI API key not configured in LLM settings")
    else:
        success("Starting chat")
        console.print(AWEL_LOGO)
        run_chat_loop(root_dir, config_filepath)
