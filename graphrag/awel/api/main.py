from typing import Optional, Union

from fastapi import FastAPI, Response

from graphrag.awel.api.chat import process_query

app = FastAPI()


@app.get("/")
def read_root(greeting: Optional[str] = None):
    res = "Hello Alex, How can I help you?"
    if greeting:
        res = greeting
    return {"title": res}

@app.get("/chat")
def process_chat(thread_id: str, query: str):
    ai_result = process_query(thread_id, query)
    return {"response" : ai_result}