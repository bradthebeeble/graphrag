# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Relationship type generation prompts."""

RELATIONSHIP_TYPE_GENERATION_PROMPT = """
The goal is to study the connections and relations between entities to understand how they interact and relate to each other in the text.
The user's task is to {task}.
As part of the analysis, you want to identify the relationship types that exist between {entity_types}.
The relationship types must be relevant to the user task and describe meaningful connections between the entities.
Avoid general relationship types such as "related_to" or "associated_with".
This is VERY IMPORTANT: Do not generate redundant or overlapping relationship types. For example, if the text suggests both "manages" and "supervises", you should return only one of them.
Don't worry about quantity, always choose quality over quantity. And make sure EVERY relationship type in your answer is relevant to connecting the entities in the context.
Return the relationship types as a list of comma separated strings, using snake_case format (e.g., belongs_to, works_for).
=====================================================================
EXAMPLE SECTION: The following section includes example output. These examples **must be excluded from your answer**.

EXAMPLE 1
Task: Determine the connections and organizational hierarchy within the specified community.
Text: Example_Org_A is a company in Sweden. Example_Org_A's director is Example_Individual_B. The company employs 500 people.
Entity Types: organization, person, location
RESPONSE:
headquartered_in, directs, employs
END OF EXAMPLE 1

EXAMPLE 2
Task: Identify the key concepts, principles, and arguments shared among different philosophical schools of thought.
Text: Rationalism, developed by René Descartes, influenced later philosophical movements. The school emphasizes deductive reasoning as its core principle.
Entity Types: concept, person, school of thought
RESPONSE:
developed_by, influences, emphasizes
END OF EXAMPLE 2

EXAMPLE 3
Task: Identify the full range of basic forces, factors, and trends that would indirectly shape an issue.
Text: Panasonic invests heavily in battery research. Their new technology powers Tesla vehicles. The company operates manufacturing plants in Asia.
Entity Types: organization, technology, sectors
RESPONSE:
invests_in, develops, manufactures, supplies_to
END OF EXAMPLE 3
======================================================================

======================================================================
REAL DATA: The following section is the real data. You should use only this real data to prepare your answer. Generate Relationship Types only.
Task: {task}
Text: {input_text}
RESPONSE:
{{<relationship_types>}}
"""

RELATIONSHIP_TYPE_GENERATION_JSON_PROMPT = """
The goal is to study the connections and relations between entities to understand how they interact and relate to each other in the text.
The user's task is to {task}.
As part of the analysis, you want to identify the relationship types that exist between {entity_types}.
The relationship types must be relevant to the user task and describe meaningful connections between the entities.
Avoid general relationship types such as "related_to" or "associated_with".
This is VERY IMPORTANT: Do not generate redundant or overlapping relationship types. For example, if the text suggests both "manages" and "supervises", you should return only one of them.
Don't worry about quantity, always choose quality over quantity. And make sure EVERY relationship type in your answer is relevant to connecting the entities in the context.
Return the relationship types in JSON format with "relationship_types" as the key and the relationship types as an array of strings in snake_case format.
=====================================================================
EXAMPLE SECTION: The following section includes example output. These examples **must be excluded from your answer**.

EXAMPLE 1
Task: Determine the connections and organizational hierarchy within the specified community.
Text: Example_Org_A is a company in Sweden. Example_Org_A's director is Example_Individual_B. The company employs 500 people.
Entity Types: organization, person, location
JSON RESPONSE:
{{"relationship_types": ["headquartered_in", "directs", "employs"]}}
END OF EXAMPLE 1

EXAMPLE 2
Task: Identify the key concepts, principles, and arguments shared among different philosophical schools of thought.
Text: Rationalism, developed by René Descartes, influenced later philosophical movements. The school emphasizes deductive reasoning as its core principle.
Entity Types: concept, person, school of thought
JSON RESPONSE:
{{"relationship_types": ["developed_by", "influences", "emphasizes"]}}
END OF EXAMPLE 2

EXAMPLE 3
Task: Identify the full range of basic forces, factors, and trends that would indirectly shape an issue.
Text: Panasonic invests heavily in battery research. Their new technology powers Tesla vehicles. The company operates manufacturing plants in Asia.
Entity Types: organization, technology, sectors
JSON RESPONSE:
{{"relationship_types": ["invests_in", "develops", "manufactures", "supplies_to"]}}
END OF EXAMPLE 3
======================================================================

======================================================================
REAL DATA: The following section is the real data. You should use only this real data to prepare your answer. Generate Relationship Types only.
Task: {task}
Text: {input_text}
JSON response:
{{"relationship_types": [<relationship_types>]}}
"""
