import graphrag.api as api
from graphrag.index.typing import PipelineRunResult
from graphrag.config.create_graphrag_config import create_graphrag_config
import yaml
import pandas as pd


PROJECT_ROOT = "../awel-demo1/"

def init():
    global graphrag_config, final_nodes, final_entities, final_communities, final_community_reports
    settings = yaml.safe_load(open(f"{PROJECT_ROOT}/settings.yaml"))
    graphrag_config = create_graphrag_config(
        values=settings, root_dir=PROJECT_ROOT
    )

    final_nodes = pd.read_parquet(f"{PROJECT_ROOT}/output/create_final_nodes.parquet")
    final_entities = pd.read_parquet(
        f"{PROJECT_ROOT}/output/create_final_entities.parquet"
    )
    final_communities = pd.read_parquet(
        f"{PROJECT_ROOT}/output/create_final_communities.parquet"
    )
    final_community_reports = pd.read_parquet(
        f"{PROJECT_ROOT}/output/create_final_community_reports.parquet"
    )

# place everything below in an async function. AI!
response, context = await api.global_search(
    config=graphrag_config,
    nodes=final_nodes,
    entities=final_entities,
    communities=final_communities,
    community_reports=final_community_reports,
    community_level=2,
    dynamic_community_selection=False,
    response_type="Multiple Paragraphs",
    query="Who is Scrooge and what are his main relationships?",
)
