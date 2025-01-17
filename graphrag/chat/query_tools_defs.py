
from pathlib import Path
from langchain_core.tools import tool
import json
from rich.console import Console
from typing import Annotated

from graphrag.cli.query import run_global_search, run_local_search

console = Console()

@tool
def local_query(query: Annotated[str,"the query to be sent to the RAG tool"],
                config_filepath: Annotated[Path,"path for the configuration file"],
                root_dir: Annotated[Path,"path to the root directory"],
                response_type:Annotated[str,"a free text description of the expected response from the LLM. Defaults to 'Multiple Paragraphs'"]):
    """
        Local search method generates answers by combining relevant data from the AI-extracted knowledge-graph with text chunks of the raw documents.
        Use this tool as the default tool, unless the question includes requests for aggregated or summarization data.
        This method is suitable for questions that require an understanding of specific entities mentioned in the documents
        (e.g. What are the healing properties of chamomile?).
    """
    global console
    console.print(f"[bold red]AWEL:[/bold red] Conducting a local search...{query}")

    (response, context_data) = run_local_search(
        config_filepath,
        data_dir=None,
        root_dir=root_dir,
        community_level=2,
        response_type=response_type,
        streaming=False,
        query=query,
    )

    return response

@tool
def global_query(query: Annotated[str,"the query to be sent to the RAG tool"],
                config_filepath: Annotated[Path,"path for the configuration file"],
                root_dir: Annotated[Path,"path to the root directory"],
                response_type:Annotated[str,"a free text description of the expected response from the LLM. Defaults to 'Multiple Paragraphs'"]):
    """
        Global search method generates answers by searching over all AI-generated community reports in a map-reduce fashion.
        Use this tool as a second priroty, for questions that are of an aggregated or summarization nature.
        This is a resource-intensive method, but often gives good responses for questions that require an understanding of the dataset as a whole
        (e.g. What are the most significant values of the herbs mentioned in this notebook?).
    """
    global console
    console.print(f"[bold red]AWEL:[/bold red] Conducting a global search...{query}")

    (response, context_data) = run_global_search(
        config_filepath,
        data_dir=None,
        root_dir=root_dir,
        community_level=2,
        dynamic_community_selection = False,
        response_type=response_type,
        streaming=False,
        query=query,
    )

    return response
