from langchain_openai import ChatOpenAI
from graphrag.config.load_config import load_config
from pathlib import Path
from graphrag.logger.base import ProgressLogger
import logging

from graphrag.logger.factory import LoggerFactory
from graphrag.logger.types import LoggerType

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

progress_logger: ProgressLogger | None = LoggerFactory().create_logger(LoggerType(LoggerType.RICH))
info, error, success = _logger(progress_logger)


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
        # create an interactive loop where a user writes a prompt in the CLI and the program for now just echoes the message back. Exit on "/exit". Do it in a speerate function in this same file. AI!