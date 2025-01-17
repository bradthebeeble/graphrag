# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI entrypoint."""

import os
import re
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from graphrag.chat.main import chat_cli
from graphrag.logger.types import LoggerType
from graphrag.prompt_tune.defaults import (
    MAX_TOKEN_COUNT,
    MIN_CHUNK_SIZE,
    N_SUBSET_MAX,
    K,
)
from graphrag.prompt_tune.types import DocSelectionType

INVALID_METHOD_ERROR = "Invalid method"

app = typer.Typer(
    help="GraphRAG: A graph-based retrieval-augmented generation (RAG) system.",
    no_args_is_help=True,
)


# A workaround for typer's lack of support for proper autocompletion of file/directory paths
# For more detail, watch
#   https://github.com/fastapi/typer/discussions/682
#   https://github.com/fastapi/typer/issues/951
def path_autocomplete(
    file_okay: bool = True,
    dir_okay: bool = True,
    readable: bool = True,
    writable: bool = False,
    match_wildcard: str | None = None,
) -> Callable[[str], list[str]]:
    """Autocomplete file and directory paths."""

    def wildcard_match(string: str, pattern: str) -> bool:
        regex = re.escape(pattern).replace(r"\?", ".").replace(r"\*", ".*")
        return re.fullmatch(regex, string) is not None

    from pathlib import Path

    def completer(incomplete: str) -> list[str]:
        # List items in the current directory as Path objects
        items = Path().iterdir()
        completions = []

        for item in items:
            # Filter based on file/directory properties
            if not file_okay and item.is_file():
                continue
            if not dir_okay and item.is_dir():
                continue
            if readable and not os.access(item, os.R_OK):
                continue
            if writable and not os.access(item, os.W_OK):
                continue

            # Append the name of the matching item
            completions.append(item.name)

        # Apply wildcard matching if required
        if match_wildcard:
            completions = filter(
                lambda i: wildcard_match(i, match_wildcard)
                if match_wildcard
                else False,
                completions,
            )

        # Return completions that start with the given incomplete string
        return [i for i in completions if i.startswith(incomplete)]

    return completer


class SearchType(Enum):
    """The type of search to run."""

    LOCAL = "local"
    GLOBAL = "global"
    DRIFT = "drift"
    BASIC = "basic"

    def __str__(self):
        """Return the string representation of the enum value."""
        return self.value




@app.command("index")
def _index_cli(
    config: Annotated[
        Path | None,
        typer.Option(
            help="The configuration to use.", exists=True, file_okay=True, readable=True, show_default=True
        ),
    ] = None,
    root: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            exists=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(
                file_okay=False, dir_okay=True, writable=True, match_wildcard="*"
            ),
        ),
    ] = Path(),  # set default to current directory
    verbose: Annotated[
        bool, typer.Option(help="Run the indexing pipeline with verbose logging")
    ] = False,
    memprofile: Annotated[
        bool, typer.Option(help="Run the indexing pipeline with memory profiling")
    ] = False,
    resume: Annotated[
        str | None, typer.Option(help="Resume a given indexing run")
    ] = None,
    logger: Annotated[
        LoggerType, typer.Option(help="The progress logger to use.")
    ] = LoggerType.RICH,
    dry_run: Annotated[
        bool,
        typer.Option(
            help="Run the indexing pipeline without executing any steps to inspect and validate the configuration.", show_default=True
        ),
    ] = False,
    cache: Annotated[bool, typer.Option(help="Use LLM cache.")] = True,
    skip_validation: Annotated[
        bool,
        typer.Option(
            help="Skip any preflight validation. Useful when running no LLM steps.", show_default=True
        ),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            help="Indexing pipeline output directory. Overrides storage.base_dir in the configuration file.", show_default=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = None,
):
    """Build a knowledge graph index."""
    from graphrag.cli.index import index_cli

    index_cli(
        root_dir=root,
        verbose=verbose,
        resume=resume,
        memprofile=memprofile,
        cache=cache,
        logger=LoggerType(logger),
        config_filepath=config,
        dry_run=dry_run,
        skip_validation=skip_validation,
        output_dir=output,
    )


@app.command("update")
def _update_cli(
    config: Annotated[
        Path | None,
        typer.Option(
            help="The configuration to use.", exists=True, file_okay=True, readable=True
        ),
    ] = None,
    root: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            exists=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = Path(),  # set default to current directory
    verbose: Annotated[
        bool, typer.Option(help="Run the indexing pipeline with verbose logging")
    ] = False,
    memprofile: Annotated[
        bool, typer.Option(help="Run the indexing pipeline with memory profiling")
    ] = False,
    logger: Annotated[
        LoggerType, typer.Option(help="The progress logger to use.")
    ] = LoggerType.RICH,
    cache: Annotated[bool, typer.Option(help="Use LLM cache.")] = True,
    skip_validation: Annotated[
        bool,
        typer.Option(
            help="Skip any preflight validation. Useful when running no LLM steps."
        ),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            help="Indexing pipeline output directory. Overrides storage.base_dir in the configuration file.",
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = None,
):
    """
    Update an existing knowledge graph index.

    Applies a default storage configuration (if not provided by config), saving the new index to the local file system in the `update_output` folder.
    """
    from graphrag.cli.index import update_cli

    update_cli(
        root_dir=root,
        verbose=verbose,
        memprofile=memprofile,
        cache=cache,
        logger=LoggerType(logger),
        config_filepath=config,
        skip_validation=skip_validation,
        output_dir=output,
    )

@app.command("load")
def _load_cli(
    config: Annotated[
        Path | None,
        typer.Option(
            help="The configuration to use.", exists=True, file_okay=True, readable=True
        ),
    ] = None,
    root: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            exists=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(
                file_okay=False, dir_okay=True, writable=True, match_wildcard="*"
            ),
        ),
    ] = Path(),  # set default to current directory
    verbose: Annotated[
        bool, typer.Option(help="Run the indexing pipeline with verbose logging")
    ] = False,
    logger: Annotated[
        LoggerType, typer.Option(help="The progress logger to use.")
    ] = LoggerType.RICH,
    output: Annotated[
        Path | None,
        typer.Option(
            help="Indexing pipeline output directory. Overrides storage.base_dir in the configuration file.",
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = None,
    load_communities: Annotated[
        bool, typer.Option(help="Load communities data into the graph db.")
    ] = False,
):
    """Build a knowledge graph index."""
    from graphrag.cli.load import load_cli

    loaded = load_cli(
        root_dir=root,
        verbose=verbose,
        logger=LoggerType(logger),
        config_filepath=config,
        output_dir=output,
        load_communities=load_communities
    )

@app.command("prompt-tune")
def _prompt_tune_cli(
    root: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            exists=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(
                file_okay=False, dir_okay=True, writable=True, match_wildcard="*"
            ),
        ),
    ] = Path(),  # set default to current directory
    config: Annotated[
        Path | None,
        typer.Option(
            help="The configuration to use.",
            exists=True,
            file_okay=True,
            readable=True,
            autocompletion=path_autocomplete(
                file_okay=True, dir_okay=False, match_wildcard="*"
            ),
        ),
    ] = None,
    domain: Annotated[
        str | None,
        typer.Option(
            help="The domain your input data is related to. For example 'space science', 'microbiology', 'environmental news'. If not defined, a domain will be inferred from the input data.", show_default=True
        ),
    ] = None,
    selection_method: Annotated[
        DocSelectionType, typer.Option(help="The text chunk selection method.")
    ] = DocSelectionType.RANDOM,
    n_subset_max: Annotated[
        int,
        typer.Option(
            help="The number of text chunks to embed when --selection-method=auto.", show_default=True
        ),
    ] = N_SUBSET_MAX,
    k: Annotated[
        int,
        typer.Option(
            help="The maximum number of documents to select from each centroid when --selection-method=auto.", show_default=True
        ),
    ] = K,
    limit: Annotated[
        int,
        typer.Option(
            help="The number of documents to load when --selection-method={random,top}.", show_default=True
        ),
    ] = 15,
    max_tokens: Annotated[
        int, typer.Option(help="The max token count for prompt generation.")
    ] = MAX_TOKEN_COUNT,
    min_examples_required: Annotated[
        int,
        typer.Option(
            help="The minimum number of examples to generate/include in the entity extraction prompt.", show_default=True
        ),
    ] = 2,
    chunk_size: Annotated[
        int, typer.Option(help="The max token count for prompt generation.")
    ] = MIN_CHUNK_SIZE,
    language: Annotated[
        str | None,
        typer.Option(
            help="The primary language used for inputs and outputs in graphrag prompts.", show_default=True
        ),
    ] = None,
    discover_entity_types: Annotated[
        bool, typer.Option(help="Discover and extract unspecified entity types.")
    ] = True,
    output: Annotated[
        Path,
        typer.Option(
            help="The directory to save prompts to, relative to the project root directory.", show_default=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = Path("prompts"),
):
    """Generate custom graphrag prompts with your own data (i.e. auto templating)."""

    from graphrag.cli.prompt_tune import prompt_tune

    prompt_tune(
        root=root,
        config=config,
        domain=domain,
        selection_method=selection_method,
        limit=limit,
        max_tokens=max_tokens,
        chunk_size=chunk_size,
        language=language,
        discover_entity_types=discover_entity_types,
        output=output,
        n_subset_max=n_subset_max,
        k=k,
        min_examples_required=min_examples_required,
    )

@app.command("chat")
def _chat_cli(
    root: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            exists=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(
                file_okay=False, dir_okay=True, writable=True, match_wildcard="*"
            ),
        ),
    ] = Path(),  # set default to current directory
    config: Annotated[
        Path | None,
        typer.Option(
            help="The configuration to use.",
            exists=True,
            file_okay=True,
            readable=True,
            autocompletion=path_autocomplete(
                file_okay=True, dir_okay=False, match_wildcard="*"
            ),
        ),
    ] = None,
):
    """Run the top-level Chat logic"""
    print("********************** WELCOME TO THE AWEL DEMO APP **********************")
    chat_cli(root_dir=root, config_filepath=config)



@app.command("query")
def _query_cli(
    method: Annotated[SearchType, typer.Option(help="The query algorithm to use.")],
    query: Annotated[str, typer.Option(help="The query to execute.")],
    debug: Annotated[bool, typer.Option(help="Enable debug logging")] = False,
    config: Annotated[
        Path | None,
        typer.Option(
            help="The configuration to use.",
            exists=True,
            file_okay=True,
            readable=True,
            autocompletion=path_autocomplete(
                file_okay=True, dir_okay=False, match_wildcard="*"
            ),
        ),
    ] = None,
    data: Annotated[
        Path | None,
        typer.Option(
            help="Indexing pipeline output directory (i.e. contains the parquet files).",
            exists=True,
            dir_okay=True,
            readable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(
                file_okay=False, dir_okay=True, match_wildcard="*"
            ),
        ),
    ] = None,
    root: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            exists=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(
                file_okay=False, dir_okay=True, match_wildcard="*"
            ),
        ),
    ] = Path(),  # set default to current directory
    community_level: Annotated[
        int,
        typer.Option(
            help="The community level in the Leiden community hierarchy from which to load community reports. Higher values represent reports from smaller communities.", show_default=True
        ),
    ] = 2,
    dynamic_community_selection: Annotated[
        bool,
        typer.Option(help="Use global search with dynamic community selection."),
    ] = False,
    response_type: Annotated[
        str,
        typer.Option(
            help="Free form text describing the response type and format, can be anything, e.g. Multiple Paragraphs, Single Paragraph, Single Sentence, List of 3-7 Points, Single Page, Multi-Page Report. Default: Multiple Paragraphs", show_default=True
        ),
    ] = "Multiple Paragraphs",
    streaming: Annotated[
        bool, typer.Option(help="Print response in a streaming manner.")
    ] = False,
):
    if debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        breakpoint()
    if debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    """Query a knowledge graph index."""
    from graphrag.cli.query import (
        run_basic_search,
        run_drift_search,
        run_global_search,
        run_local_search,
    )

    match method:
        case SearchType.LOCAL:
            run_local_search(
                config_filepath=config,
                data_dir=data,
                root_dir=root,
                community_level=community_level,
                response_type=response_type,
                streaming=streaming,
                query=query,
            )
        case SearchType.GLOBAL:
            run_global_search(
                config_filepath=config,
                data_dir=data,
                root_dir=root,
                community_level=community_level,
                dynamic_community_selection=dynamic_community_selection,
                response_type=response_type,
                streaming=streaming,
                query=query,
            )
        case SearchType.DRIFT:
            run_drift_search(
                config_filepath=config,
                data_dir=data,
                root_dir=root,
                community_level=community_level,
                streaming=False,  # Drift search does not support streaming (yet)
                query=query,
            )
        case SearchType.BASIC:
            run_basic_search(
                config_filepath=config,
                data_dir=data,
                root_dir=root,
                streaming=streaming,
                query=query,
            )
        case _:
            raise ValueError(INVALID_METHOD_ERROR)

@app.command("new")
def _new_cli(
    root: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            dir_okay=True,
            writable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(
                file_okay=False, dir_okay=True, writable=True, match_wildcard="*"
            ),
        ),
    ] , 
    env: Annotated[
        Path,
        typer.Option(
            help="Path to .env file",
            exists=True,
            file_okay=True,
            readable=True,
        ),
    ],
    project_name: Annotated[
        str | None,
        typer.Option(help="Name of the project", show_default=True),
    ],
    index_name: Annotated[
        str | None,
        typer.Option(help="Name of the index", show_default=True),
    ],
    rss_url: Annotated[
        str | None,
        typer.Option(help="URL of the RSS feed", show_default=True),
    ],
    dom_element: Annotated[
        str,
        typer.Option(help="DOM element for scraping", show_default=True),
    ],
    max_links: Annotated[
        int,
        typer.Option(help="Maximum number of links to fetch", show_default=True),
    ],
    start: Annotated[
        int,
        typer.Option(help="Starting index for fetching links", show_default=True),
    ],
    domain: Annotated[
        str | None,
        typer.Option(help="Domain name for prompt tuning", show_default=True),
    ],
):
    """Create a new project from RSS feed."""
    import asyncio
    from graphrag.cli.new import setup_project
    
    # Interactive prompts for missing required parameters
    if project_name is None:
        project_name = typer.prompt("Enter project name")
    
    if index_name is None:
        index_name = typer.prompt("Enter index name")
    
    if rss_url is None:
        rss_url = typer.prompt("Enter RSS feed URL")

    if dom_element is None:
        dom_element = typer.prompt("Enter DOM element", default="<HTML>")
    
    if max_links is None:
        max_links = typer.prompt("Enter maximum links to fetch", default=10, type=int)
    
    if start is None:
        start = typer.prompt("Enter index to start from", default=0, type=int)

    if domain is None:
        domain = typer.prompt("Enter domain name", default="")
    
    if not env.exists():
        typer.echo(f"Warning: Environment file {env} does not exist")
        return
    if not project_name or not index_name or not rss_url:
        typer.echo("Error: Missing required parameters")
        return
    
    # Construct full env file path
    env_file_path = env / ".env"

    project_dir = setup_project(
        root_dir=root,
        project_name=project_name,
        index_name=index_name,
        rss_url=rss_url,
        dom_element=dom_element,
        max_links=max_links,
        start=start,
        env_file=env_file_path,
        domain=domain
    )
    print(f"Project created at: {project_dir}")
    # from graphrag.cli.initialize import initialize_project_at

    # initialize_project_at(project_dir)

@app.command("init")
def _initialize_cli(
    root: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            dir_okay=True,
            writable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(
                file_okay=False, dir_okay=True, writable=True, match_wildcard="*"
            ),
        ),
    ],
):
    """Generate a default configuration file."""
    from graphrag.cli.initialize import initialize_project_at

    initialize_project_at(path=root)

@app.command("generate")
def _generate_cli(
    history: Annotated[
        list[str],
        typer.Option(
            help="History of past questions from the user",
            show_default=True
        ),
    ] = [],
    config: Annotated[
        Path | None,
        typer.Option(
            help="The configuration to use.",
            exists=True,
            file_okay=True,
            readable=True,
            autocompletion=path_autocomplete(
                file_okay=True, dir_okay=False, match_wildcard="*"
            ),
        ),
    ] = None,
    data: Annotated[
        Path | None,
        typer.Option(
            help="Indexing pipeline output directory (i.e. contains the parquet files).",
            exists=True,
            dir_okay=True,
            readable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(
                file_okay=False, dir_okay=True, match_wildcard="*"
            ),
        ),
    ] = None,
    root: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            exists=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(
                file_okay=False, dir_okay=True, writable=True, match_wildcard="*"
            ),
        ),
    ] = Path(),  # set default to current directory
    community_level: Annotated[
        int,
        typer.Option(
            help="The community level in the Leiden community hierarchy from which to load community reports. Higher values represent reports from smaller communities."
        ),
    ] = 2,
):
    """Build a knowledge graph index."""
    from graphrag.cli.query import run_question_generator


    run_question_generator(
                config_filepath=config,
                data_dir=data,
                root_dir=root,
                community_level=community_level,
                query=history,
            )
