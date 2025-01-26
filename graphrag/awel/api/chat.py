from langchain_openai import ChatOpenAI

OPENAI_KEY = "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"
OPENAI_MODEL = "gpt-4o-mini"

def process_query(query: str):
    """Accepts a query and prints it."""
    print(query)

