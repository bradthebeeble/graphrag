"""RSS fetching and document processing functionality."""

import feedparser
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import shutil
from typing import Optional

from graphrag.logger.types import LoggerType

async def fetch_rss_documents(
    rss_url: str,
    max_links: int,
    dom_element: str,
    output_dir: Path
) -> None:
    """Fetch documents from RSS feed and save them.
    
    Args:
        rss_url: URL of the RSS feed
        max_links: Maximum number of links to process
        dom_element: DOM element to extract text from
        output_dir: Directory to save documents to
    """
    feed = feedparser.parse(rss_url)
    
    for i, entry in enumerate(feed.entries[:max_links]):
        if hasattr(entry, 'link'):
            try:
                response = requests.get(entry.link)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract text from specified DOM element
                if dom_element.upper() == "<HTML>":
                    content = soup.get_text()
                else:
                    elements = soup.select(dom_element)
                    content = "\n".join(elem.get_text() for elem in elements)
                
                # Save to file
                output_file = output_dir / f"doc_{i+1}.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(content)
                    
            except Exception as e:
                print(f"Error processing {entry.link}: {str(e)}")

async def setup_project(
    root_dir: Path,
    project_name: str,
    index_name: str,
    rss_url: str,
    dom_element: str = "<HTML>",
    max_links: int = 10,
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
    from graphrag.cli.initialize import initialize_project_at
    from graphrag.cli.prompt_tune import prompt_tune
    from graphrag.cli.index import index_cli
    from graphrag.cli.load import load_cli
    from graphrag.prompt_tune.types import DocSelectionType
    
    # Create project directory
    project_dir = root_dir / f"{project_name}-{index_name}"
    input_dir = project_dir / "input"
    if project_dir.exists():
        if not input_dir.exists():
            input_dir.mkdir(parents=True)
    else:
        project_dir.mkdir(parents=True)
        input_dir.mkdir(parents=True)
    
    # Fetch RSS content
    await fetch_rss_documents(
        rss_url=rss_url,
        max_links=max_links,
        dom_element=dom_element,
        output_dir=input_dir
    )
    
    # Initialize project
    initialize_project_at(project_dir)
    
    # Copy .env if provided
    if env_file:
        shutil.copy2(env_file, project_dir / ".env")
    
    # Run prompt tuning
    await prompt_tune(
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
    
    # Run indexing
    index_cli(
        root_dir=project_dir,
        verbose=True,
        resume=None,
        memprofile=False,
        cache=True,
        logger=LoggerType.RICH,
        config_filepath=None,
        dry_run=False,
        skip_validation=False,
        output_dir=None
    )
    
    # Load into Neo4j
    load_cli(
        root_dir=project_dir,
        verbose=True,
        logger=LoggerType.RICH,
        config_filepath=None,
        output_dir=None,
        load_communities=False
    )
    
    return project_dir
