from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from graphrag.chat.query_tools_defs import global_query, local_query
from graphrag.config.load_config import load_config
from pathlib import Path
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.logger.base import ProgressLogger
import logging

from graphrag.logger.factory import LoggerFactory
from graphrag.logger.types import LoggerType
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

log = logging.getLogger(__name__)


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

workflow = StateGraph(state_schema=MessagesState)
SYSTEM_PROMPT = "You are a helpful assistant. Answer the user's question in the context of the given conversation."
openai_api_key: str | None = ""
config: GraphRagConfig  = GraphRagConfig()
llm: ChatOpenAI | None = None
llm_with_tools = None

# Define the function that calls the model
def call_model(state: MessagesState):
    global llm_with_tools, openai_api_key
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    if llm_with_tools is None:
        error("OpenAI API key not configured in LLM settings")
    else:
        response: AIMessage = llm_with_tools.invoke(messages)  # convert to AIMessage. AI!
        print(response.tool_calls)
        return {"messages": response}

# Define the node and edge
workflow.add_node("model", call_model)
workflow.add_edge(START, "model")

# Add simple in-memory checkpointer
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

def run_chat_loop():
    """Run an interactive chat loop that echoes user input."""
    global llm, openai_api_key, llm_with_tools
    llm = ChatOpenAI(api_key=SecretStr(str(openai_api_key)), model=config.llm.model)
    llm_with_tools = llm.bind_tools([local_query, global_query])

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
                    config={"configurable": {"thread_id": "1"}},
                )
                print(f"AI: {ai_msg['messages'][-1].content}")

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
        run_chat_loop()
