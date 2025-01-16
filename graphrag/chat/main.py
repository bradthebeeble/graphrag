import json
from typing import Annotated, cast
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

from rich.console import Console
from rich.markdown import Markdown
from graphrag.chat.awel_logo import AWEL_LOGO

class ExtendedMessagesState(TypedDict):
    config_filepath: Path | None
    root_dir: Path 
    messages: Annotated[list, add_messages]
    next_questions_candidates: list[str]

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
THREAD_ID = 1

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
    response_messages: list[BaseMessage] = []
    if llm_with_tools is None:
        error("OpenAI API key not configured in LLM settings")
    else:
        return {
            "messages": [llm_with_tools.invoke(messages)],
            "config_filepath" : _config_filepath,
            "root_dir" : _root_dir
            }
        
def call_candidate_fup_questions(state: ExtendedMessagesState):
    is_tool_message = isinstance(state["messages"][-2], ToolMessage) if len(state["messages"]) > 1 else False
    history = []
    if is_tool_message:
        history: list[str] = cast(list[str],[msg.content for msg in state["messages"] if isinstance(msg, HumanMessage)])
        config_filepath = state["config_filepath"]
        root_dir=state["root_dir"]
        next_questions_candidates = run_question_generator(
                config_filepath,
                data_dir=None,
                root_dir=root_dir,
                community_level=2,
                query=history,
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

# Define the node and edge
workflow.add_node("model", call_model)
workflow.add_node("tools", call_tools)
workflow.add_node("candidate_fup_questions", call_candidate_fup_questions)
workflow.add_edge(START, "model")
workflow.add_conditional_edges(
    "model",
    route_tools,
    {"tools": "tools", END: "candidate_fup_questions"},
)
workflow.add_edge("tools", "model")

workflow.add_edge("candidate_fup_questions", END)

# Add simple in-memory checkpointer
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)



def run_chat_loop(root_dir: Path,
                  config_filepath: Path | None):
    """Run an interactive chat loop that echoes user input."""
    global llm, openai_api_key, llm_with_tools, _config_filepath, _root_dir
    _config_filepath = config_filepath
    _root_dir = root_dir
    llm = ChatOpenAI(api_key=SecretStr(str(openai_api_key)), model=config.llm.model)
    llm_with_tools = llm.bind_tools([local_query, global_query])
    graph_config = RunnableConfig({
        "configurable": 
            {"thread_id": THREAD_ID}
            })
    print("\nEnter your messages (type /exit to quit):")

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() == "/exit":
                print("Goodbye!")
                break

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
                console.print("AI:")
                import re
                def clean_markdown(raw_markdown):
                    # Remove surrounding quotes
                    cleaned = raw_markdown.strip('"').strip("'")
                    # Replace literal "\n" with actual newlines
                    cleaned = cleaned.replace("\\n", "\n")
                    # Optionally, normalize whitespace
                    cleaned = re.sub(r'\s+\n', '\n', cleaned).strip()
                    return cleaned
                markdown = clean_markdown(ai_msg['messages'][-1].content)
                state = app.get_state(graph_config)
                if state.values["next_questions_candidates"] is not null: # fix. AI!

                console.print(Markdown(markdown))


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
