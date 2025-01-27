from typing import Annotated
import graphrag.api as api
from graphrag.cli.query import _resolve_output_files
from graphrag.config.create_graphrag_config import create_graphrag_config
import yaml
import pandas as pd
from langchain_core.tools import tool
import asyncio 
from pathlib import Path

from graphrag.config.load_config import load_config
from graphrag.config.resolve_path import resolve_paths



PROJECT_ROOT = "../awel-demo1/"

def get_model_config():
    return config.llm.api_key, config.llm.model


def init_graph():
    global config, final_nodes, final_entities, final_communities, final_community_reports, final_text_units, final_relationships, final_covariates
    
    root_dir = Path(PROJECT_ROOT)
    root = root_dir.resolve()
    config_filepath = Path(f"{PROJECT_ROOT}/settings.yaml")
    config = load_config(root, config_filepath)
    resolve_paths(config)

    final_nodes = pd.read_parquet(f"{PROJECT_ROOT}/output/create_final_nodes.parquet")
    final_communities = pd.read_parquet(f"{PROJECT_ROOT}/output/create_final_communities.parquet")
    final_community_reports = pd.read_parquet(f"{PROJECT_ROOT}/output/create_final_community_reports.parquet")
    final_text_units = pd.read_parquet(f"{PROJECT_ROOT}/output/create_final_text_units.parquet")
    final_relationships = pd.read_parquet(f"{PROJECT_ROOT}/output/create_final_relationships.parquet")
    final_entities = pd.read_parquet(f"{PROJECT_ROOT}/output/create_final_entities.parquet")
    covariates_path = f"{PROJECT_ROOT}/output/create_final_covariates.parquet"
    if Path(covariates_path).exists():
        final_covariates = pd.read_parquet(covariates_path)
    else:
        final_covariates = None


@tool
def perform_global_search(query: Annotated[str,"the query to be sent to the RAG tool"],
                                response_type:Annotated[str,"a free text description of the expected response from the LLM. Defaults to 'A Single Paragraphs. No more than 50 words.'"]
                                ):
    """
        Global search method generates answers by searching over all AI-generated community reports in a map-reduce fashion.
        Use this tool as a second priroty, for questions that are of an aggregated or summarization nature.
        This is a resource-intensive method, but often gives good responses for questions that require an understanding of the dataset as a whole
        (e.g. What are the most significant values of the herbs mentioned in this notebook?).
    """
    response, context = asyncio.run(api.global_search(
        config=config,
        nodes=final_nodes,
        entities=final_entities,
        communities=final_communities,
        community_reports=final_community_reports,
        community_level=2,
        dynamic_community_selection=False,
        response_type=response_type,
        query=query,
    ))
    return response

@tool
def perform_local_search(query: Annotated[str,"the query to be sent to the RAG tool"],
                                response_type:Annotated[str,"a free text description of the expected response from the LLM. Defaults to 'A Single Paragraphs. No more than 50 words.'"]
                                ):
    """
        Local search method generates answers by combining relevant data from the AI-extracted knowledge-graph with text chunks of the raw documents.
        Use this tool as the default tool, unless the question includes requests for aggregated or summarization data.
        This method is suitable for questions that require an understanding of specific entities mentioned in the documents
        (e.g. What are the healing properties of chamomile?).
    """
    response, context = asyncio.run(api.local_search(
        config=config,
        nodes=final_nodes,
        entities=final_entities,
        community_reports=final_community_reports,
        text_units=final_text_units,
        relationships=final_relationships,
        covariates=None,
        community_level=2,
        response_type=response_type,
        query=query,
    ))
    return response

