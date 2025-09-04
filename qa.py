import asyncio
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
import os
import httpx
import json

from prompts import get_questions_answers_prompt, new_get_questions_answers_prompt, get_context_answers_prompt
from utils import get_trasnscript_with_tool_calls

load_dotenv()

DIFY_API_KEY = os.getenv("DIFY_API_KEY")

class QuestionAnswer(BaseModel):
    question: str = Field(..., description="A fully-resolved, context-complete form question")
    answer: str = Field(..., description="A short and concise answer to the question")

class MultipleQuestionsAnswers(BaseModel):
    items: List[QuestionAnswer] = Field(..., description="List of all question-answer pairs")

class ContextAnswer(BaseModel):
    answer: str = Field(..., description="A short and concise answer to the question")
    source_and_reasoning: str = Field(..., description="Source and reasoning for the answer")



async def get_questions_answers(call_data):
    """Extracts questions and answers using the LLM."""

    transcript = get_trasnscript_with_tool_calls(call_data)

    prompt = new_get_questions_answers_prompt.format(transcript=transcript)
    
    messages = [
        SystemMessage(prompt)
    ]

    llm = ChatOpenAI(model="gpt-4o").with_structured_output(MultipleQuestionsAnswers).with_retry(stop_after_attempt=3)
    response = await llm.ainvoke(messages)
    return response


async def get_context_answers(question, context):

    prompt = get_context_answers_prompt.format(question=question, context=context)

    messages = [
        SystemMessage(prompt)
    ]

    llm = ChatOpenAI(model="gpt-4o").with_structured_output(ContextAnswer).with_retry(stop_after_attempt=3)
    response = await llm.ainvoke(messages)
    return response

async def get_hk_chatbot_answer(query):
    chat_url = "https://api.dify.ai/v1/chat-messages"
    header = {"authorization": f"Bearer {DIFY_API_KEY}",
           "Content-Type": "application/json"}
    data = {
    "inputs": {},
    "query": f"""Please strictly answer the question without asking any follow-up questions.
    If you need additional information like location of numbers, give information about all the locations or give a range of numbers
    This is the query: {query}""",
    "response_mode": "blocking",
    "conversation_id": "",
    "user": "m-agent",
    "files": ""
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        result = await client.post(chat_url, headers=header, json=data)
        result.raise_for_status()

    #result = requests.post(chat_url, headers=header, json=data)
    res = json.loads(result.content.decode("utf-8"))
    return res
