"""Project setup functionality."""

import asyncio
from pathlib import Path
from typing import Optional

from graphrag.cli.initialize import initialize_project_at
from graphrag.cli.prompt_tune import prompt_tune
from graphrag.cli.index import index_cli
from graphrag.cli.load import load_cli
from graphrag.prompt_tune.types import DocSelectionType
from graphrag.logger.types import LoggerType
from graphrag.cli.rss_fetcher import fetch_rss_documents

def setup_project(
    root_dir: Path,
    project_name: str,
    index_name: str,
    rss_url: str,
    dom_element: str = "<HTML>",
    max_links: int = 10,
    start: int = 0,
    env_file: Optional[Path] = None,
    domain: Optional[str] = None
) -> Path:
    """Set up a new project with RSS data.
    
    Args:
        project_name: Name of the project
        index_name: Name of the index
        rss_url: URL of the RSS feed
        dom_element: DOM element to extract text from
        max_links: Maximum number of links to process
        env_file: Optional path to .env file
        domain: Optional domain name for prompt tuning
        
    Returns:
        Path to the project directory
    """
    
    # Create project directory
    is_project_exist = False
    project_dir = root_dir / f"{project_name}-{index_name}"
    input_dir = project_dir / "input"
    if project_dir.exists():
        is_project_exist = True
        if not input_dir.exists():
            input_dir.mkdir(parents=True)
    else:
        project_dir.mkdir(parents=True)
        input_dir.mkdir(parents=True)
    
    # Fetch RSS content
    print("Fetching documents...")
    fetch_rss_documents(
        rss_url=rss_url,
        max_links=max_links,
        start=start,
        dom_element=dom_element,
        output_dir=input_dir
    )
    
    # # Initialize projectno
    if not is_project_exist:
        print("Initializing project...")
        initialize_project_at(project_dir)
    
    # Copy .env if provided
    if env_file:
        import shutil
        print("Copying .env file...")
        shutil.copy2(env_file, project_dir / ".env")
    
    # Run prompt tuning
    if not is_project_exist:
        print("Starting prompt tuning operation...")
        prompt_tune(
            root=project_dir,
            config=None,
            domain=domain,
            selection_method=DocSelectionType.RANDOM,
            limit=15,
            max_tokens=1000,
            chunk_size=500,
            language=None,
            discover_entity_types=True,
            output=project_dir / "prompts",
            n_subset_max=100,
            k=5,
            min_examples_required=2
        )
    
    print("Starting indexing operation...")
    # Run indexing
    index_errors = index_cli(
        root_dir=project_dir,
        verbose=True,
        resume=None,
        memprofile=False,
        cache=True,
        logger=LoggerType.PRINT,
        config_filepath=None,
        dry_run=False,
        skip_validation=False,
        output_dir=None
    )
    
    if index_errors:
        print("Indexing failed, skipping Neo4j load")
        return project_dir
            
    print("Starting Neo4j loading operation...")
    # Load into Neo4j
    loaded = load_cli(
        root_dir=project_dir,
        verbose=True,
        logger=LoggerType.PRINT,
        config_filepath=None,
        output_dir=None,
        load_communities=False
    )
    return project_dir
        
