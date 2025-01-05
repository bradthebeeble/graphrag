# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Relationship type generation module for fine-tuning."""

from fnllm import ChatLLM
from pydantic import BaseModel

from graphrag.prompt_tune.defaults import DEFAULT_TASK
from graphrag.prompt_tune.prompt.relationship_types import (
    RELATIONSHIP_TYPE_GENERATION_JSON_PROMPT,
    RELATIONSHIP_TYPE_GENERATION_PROMPT,
)


class RelationshipTypesResponse(BaseModel):
    """Relationship types response model."""

    relationship_types: list[str]


async def generate_relationship_types(
    llm: ChatLLM,
    domain: str,
    persona: str,
    entity_types: list[str] | str | None,
    docs: str | list[str],
    task: str = DEFAULT_TASK,
    json_mode: bool = False,
) -> str | list[str]:
    """
    Generate relationship type categories between entities from a given set of (small) documents.

    Example Output:
    "relationship_types": ['commands', 'belongs_to', 'located_in', 'participated_in', 'occurred_on', 'uses']
    """
    formatted_task = task.format(domain=domain)

    docs_str = "\n".join(docs) if isinstance(docs, list) else docs

    relationship_types_prompt = (
        RELATIONSHIP_TYPE_GENERATION_JSON_PROMPT
        if json_mode
        else RELATIONSHIP_TYPE_GENERATION_PROMPT
    ).format(
        task=formatted_task,
        input_text=docs_str,
        entity_types=", ".join(entity_types) if entity_types else "any entities"
    )

    history = [{"role": "system", "content": persona}]

    if json_mode:
        response = await llm(
            relationship_types_prompt, history=history, json_model=RelationshipTypesResponse
        )
        model = response.parsed_json
        return model.relationship_types if model else []

    response = await llm(relationship_types_prompt, history=history, json=json_mode)
    return str(response.output.content)
