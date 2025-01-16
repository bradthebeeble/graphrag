from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from graphrag.config.load_config import load_config
from pathlib import Path
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.logger.base import ProgressLogger
import logging

from graphrag.logger.factory import LoggerFactory
from graphrag.logger.types import LoggerType
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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

SYSTEM_PROMPT = "You are a helpful assistant. Answer the user's question in the context of the given conversation."

def run_chat_loop(
    openai_api_key: str,
    config: GraphRagConfig,
):
    """Run an interactive chat loop that echoes user input."""
    llm = ChatOpenAI(
        model=config.llm.model,
        api_key=SecretStr(openai_api_key),
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=SYSTEM_PROMPT,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    chain = prompt | llm

    print("\nEnter your messages (type /exit to quit):")

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() == "/exit":
                print("Goodbye!")
                break

            if user_input:
                # create an effect of running dots while the invoke function is running. Then print the AI response. AI!
                ai_msg = chain.invoke(
                    {
                        "messages": [
                            HumanMessage(
                                content=user_input
                            ),
                        ],
                    }
                )
                print(f"AI: {ai_msg.content}")

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
    """Run the pipeline with the given config."""
    config = load_config(root_dir, config_filepath)

    openai_api_key = config.llm.api_key
    if not openai_api_key:
        error("OpenAI API key not configured in LLM settings")
    else:
        success("Starting chat")
        run_chat_loop(openai_api_key, config)