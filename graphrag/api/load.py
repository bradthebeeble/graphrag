from pydantic import BaseModel
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.logger.base import ProgressLogger
import pandas as pd
from neo4j import Driver, GraphDatabase, Query
import time
import logging

from graphrag.logger.factory import LoggerFactory
from graphrag.logger.types import LoggerType

# Loading the music and dealership templates
import graphrag.awel.templates.music as music
import graphrag.awel.templates.dealership as dealership

import inspect


log = logging.getLogger(__name__)

def get_all_models(module):
    return [
        obj for name, obj in inspect.getmembers(module)
        if inspect.isclass(obj) 
        and issubclass(obj, BaseModel) 
        and obj != BaseModel
    ]
    
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

def load_data(
    config: GraphRagConfig,
    dataframe_dict: dict[str, pd.DataFrame],
    progress_logger: ProgressLogger | None = None,
    should_load_communities: bool = False,
) -> bool:
    """Run the pipeline with the given configuration.

    Parameters
    ----------
    config : GraphRagConfig
        The configuration.
    progress_logger : ProgressLogger | None default=None
        The progress logger.

    Returns
    -------
    bool
        True if the pipeline ran successfully
    """

    driver: Driver


    def batched_import(statement, df, batch_size=1000):
        """
        Import a dataframe into Neo4j using a batched approach.
        Parameters: statement is the Cypher query to execute, df is the dataframe to import, and batch_size is the number of rows to import in each batch.
        """
        total = len(df)
        start_s = time.time()
        for start in range(0,total, batch_size):
            batch = df.iloc[start: min(start+batch_size,total)]
            result = driver.execute_query("UNWIND $rows AS value " + statement,
                                        rows=batch.to_dict('records'),
                                        database_=NEO4J_DATABASE)
            print(result.summary.counters)
        print(f'{total} rows in { time.time() - start_s} s.')
        return total
    
    def create_db_constraints():
        """
        create constraints, idempotent operation
        """
        statements = """
            create constraint chunk_id if not exists for (c:__Chunk__) require c.id is unique;
            create constraint document_id if not exists for (d:__Document__) require d.id is unique;
            create constraint entity_id if not exists for (c:__Community__) require c.community is unique;
            create constraint entity_id if not exists for (e:__Entity__) require e.id is unique;
            create constraint entity_title if not exists for (e:__Covariate__) require e.title is unique;
            create constraint related_id if not exists for ()-[rel:RELATED]->() require rel.id is unique;
            """.split(";")

        for statement in statements:
            if len((statement or "").strip()) > 0:
                driver.execute_query(statement)

    def import_documents(df: pd.DataFrame):
        """
        Import documents into the database.
        """

        statement = """
                    MERGE (d:__Document__ {id:value.id})
                    SET d += value {.title}
                    """

        print(f"Importing {len(df)} documents")
        batched_import(statement, df)
    
    def load_text_units(df: pd.DataFrame):
        """
        Load text units into the database.
        """

        statement = """
                    MERGE (c:__Chunk__ {id:value.id})
                    SET c += value {.text, .n_tokens}
                    WITH c, value
                    UNWIND value.document_ids AS document
                    MATCH (d:__Document__ {id:document})
                    MERGE (c)-[:PART_OF]->(d)
                    """
        print(f"Loading {len(df)} text units")
        batched_import(statement, df)

    def load_nodes(df: pd.DataFrame):
        """
        Load nodes into the database.
        """

        statement = """
                    MERGE (e:__Entity__ {id:value.id})
                    SET e += value {.human_readable_id, .description, title:replace(value.title,'"','')}
                    WITH e, value
                    CALL apoc.create.addLabels(e, case when coalesce(value.type,"") = "" then [] else [apoc.text.upperCamelCase(replace(value.type,'"',''))] end) yield node
                    UNWIND value.text_unit_ids AS text_unit
                    MATCH (c:__Chunk__ {id:text_unit})
                    MERGE (c)-[:HAS_ENTITY]->(e)
                    """
        print(f"Loading {len(df)} entity nodes")
        batched_import(statement, df)
    
    def load_relationships(df: pd.DataFrame):
        """
        Load relationships into the database.
        """

        statement = """
                    MATCH (source:__Entity__ {title: replace(value.source, '"', '')})
                    MATCH (target:__Entity__ {title: replace(value.target, '"', '')})
                    UNWIND split(value.type, ',') AS rel_type
                    CALL apoc.merge.relationship(
                        source,
                        rel_type,
                        {id: value.id},
                        value {.rank, .combined_degree, .human_readable_id, .description, .text_unit_ids},
                        target
                    ) YIELD rel
                    RETURN count(*) AS createdRels
                    """
        print(f"Loading {len(df)} relationships (edges)")
        batched_import(statement, df)

    def load_communities(df: pd.DataFrame):
        """
        Load communities into the database.
        """

        statement = """
                    MATCH (start:__Entity__)-[r]->(end:__Entity__)
                    WHERE r.id IN value.relationship_ids
                    WITH DISTINCT value, collect(DISTINCT r) as rels, 
                         collect(DISTINCT start) as starts, 
                         collect(DISTINCT end) as ends
                    MERGE (c:__Community__ {community: value.community})
                    ON CREATE SET c += value {.level, .title}
                    ON MATCH SET c += value {.level, .title}
                    WITH c, starts, ends
                    UNWIND starts + ends as node
                    MERGE (node)-[:IN_COMMUNITY]->(c)
                    """
        print(f"Loading {len(df)} communities")
        batched_import(statement, df)

    def load_communities_reports(df: pd.DataFrame):
        """
        Load community reports into the database.
        """

        statement = """
                    MERGE (c:__Community__ {community:value.community})
                    SET c += value {.level, .title, .rank, .rank_explanation, .full_content, .summary}
                    WITH c, value
                    UNWIND range(0, size(value.findings)-1) AS finding_idx
                    WITH c, value, finding_idx, value.findings[finding_idx] as finding
                    MERGE (c)-[:HAS_FINDING]->(f:Finding {id:finding_idx})
                    SET f += finding
                    """
        print(f"Loading {len(df)} communities reports")
        batched_import(statement, df)

    def update_entites_with_properties(models: list, df: pd.DataFrame):
        
        """
        Uses LLM Strctured Output, to extract properties from the description property, and update the db
        """
        from pydantic import SecretStr
        from langchain_openai import ChatOpenAI

        all_updated_records = pd.DataFrame()
        if not models:
            error("No models provided")
            return all_updated_records
            
        
        for model in models:
            query = f"""
                MATCH (n:{model.__name__})
                RETURN n AS node
            """
            try:
                records = driver.execute_query(query, database_=NEO4J_DATABASE)
                
                if not records.records:
                    info(f"No {model.__name__} records found in database")
                    continue
                # Convert records to DataFrame and filter for dirty/null records
                df = pd.DataFrame([dict(record["node"]) for record in records.records])
                if 'dirty' in df.columns:
                    df = df[df['dirty'].isna() | df['dirty'] == True]
                print(f"Found {len(df)} dirty {model.__name__} nodes")
            
            except Exception as e:
                error(f"Error fetching records: {e}")
                return pd.DataFrame()
            # Process records in batches
            
            
            openai_api_key = config.llm.api_key
            if not openai_api_key:
                error("OpenAI API key not configured in LLM settings")
                return pd.DataFrame()
            try:
                llm = ChatOpenAI(
                    model=config.llm.model,
                    api_key=SecretStr(openai_api_key),
                )
                structured_llm = llm.with_structured_output(getattr(dealership, f"ListOf{model.__name__}s"))
                
                
                # Process DataFrame in batches of 10
                batch_size = 35
                total_records = len(df)
                updated_records = 0
                
                for start_idx in range(0, total_records, batch_size):
                    end_idx = min(start_idx + batch_size, total_records)
                    batch_df = df.iloc[start_idx:end_idx]
                    
                    # Process batch through LLM
                    list_of_items = structured_llm.invoke(batch_df.to_string())
                    list_of_dicts = [vars(obj) for obj in list_of_items.items]
                    df_batch_updated = pd.DataFrame(list_of_dicts)
                    
                    # Create the SET clause dynamically
                    fields = model.model_fields.keys()
                    set_statements = [
                        f"n.{field} = value.{field}"
                        for field in fields
                    ]
                    set_statements.append("n.dirty = false")
                    set_clause = ",\n                ".join(set_statements)
                    
                    # Create and execute the query for this batch
                    statement = f"""
                        MATCH (n:{model.__name__} {{human_readable_id: value.human_readable_id}})
                        WHERE n.dirty IS NULL OR n.dirty = true 
                        SET {set_clause}
                    """
                    
                    batched_import(statement, df_batch_updated)
                    updated_records += len(df_batch_updated)
                    print(f"Processed batch {start_idx//batch_size + 1}, updated {updated_records}/{total_records} {model.__name__} nodes")
                    all_updated_records = pd.concat([all_updated_records, df_batch_updated], ignore_index=True)
            except Exception as e:
                info(f"Error initializing LLM: {e}")
                continue

    if progress_logger is None:
            progress_logger = LoggerFactory().create_logger(LoggerType(LoggerType.RICH))

    info, error, success = _logger(progress_logger)


    # Load neo4j config
    NEO4J_URI = config.neo4j.uri
    NEO4J_USERNAME = config.neo4j.username
    NEO4J_PASSWORD = config.neo4j.password
    NEO4J_DATABASE = config.neo4j.database
    # Check if any neo4j config is not initialized
    if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD or not NEO4J_DATABASE:
        raise ValueError("Neo4j configuration is incomplete. Please provide all required parameters.")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        driver.verify_connectivity()
        info("Neo4j driver initialized successfully.")
        # Get all models from dealership.py
        dealership_models = get_all_models(dealership)

        # Filter out ListOf models
        dealership_models = [model for model in dealership_models if not model.__name__.startswith('ListOf')]
       
        create_db_constraints()
        import_documents(dataframe_dict["create_final_documents"][["id", "title"]])
        load_text_units(dataframe_dict["create_final_text_units"][["id","text","n_tokens","document_ids"]])
        load_nodes(dataframe_dict["create_final_entities"][["title","type","description","human_readable_id","id","text_unit_ids"]])
        load_relationships(dataframe_dict["create_final_relationships"][["source","target","id","type","combined_degree","weight","human_readable_id","description","text_unit_ids"]])
        if should_load_communities:
            load_communities(dataframe_dict["create_final_communities"][["id","level","title","text_unit_ids","relationship_ids", "community"]])
            load_communities_reports(dataframe_dict["create_final_community_reports"][["id","community","level","title","summary", "findings","rank","rank_explanation","full_content"]])
        # update_entites_with_properties(dealership_models, dataframe_dict["create_final_entities"][["id","human_readable_id", "description"]])

        return True
    except Exception as e:
        error(f"Failed to connect to the database: {e}")
        return False
