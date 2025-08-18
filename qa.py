import asyncio
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
import os
import httpx
import json

from prompts import get_questions_answers_prompt

load_dotenv()

DIFY_API_KEY = os.getenv("DIFY_API_KEY")

class QuestionAnswer(BaseModel):
    question: str = Field(..., description="A fully-resolved, context-complete form question")
    answer: str = Field(..., description="A short and concise answer to the question")

class MultipleQuestionsAnswers(BaseModel):
    items: List[QuestionAnswer] = Field(..., description="List of all question-answer pairs")

call_data = {
    "transcript": "User: How are you?\nAgent: I am fine, thank you.\nUser: What is the weather like today?\nAgent: It is sunny.\nUser: What is the time?\nAgent: It is 10:00 AM."
}

async def get_questions_answers(call_data):
    """Extracts questions and answers using the LLM."""

    prompt = get_questions_answers_prompt.format(transcript=call_data["transcript"])
    
    messages = [
        SystemMessage(prompt)
    ]

    llm = ChatOpenAI(model="gpt-4o").with_structured_output(MultipleQuestionsAnswers)
    response = await llm.ainvoke(messages)
    return response


async def get_context_answers(url, ques):

    prompt = f"""Please generate short, concise and to-the-point answers of the given questions using the context provided.
    If answer to a question is not available in context, return 'Answer not present in given context'.
    Do NOT make any changes in the given questions.
    This is the provided context: \n\n{fetch_webpage_as_markdown(url)}\n\n
    These are the questions: \n\n{ques}\n\n"""

    messages = [
        SystemMessage(prompt)
    ]

    llm = ChatOpenAI(model="gpt-4o").with_structured_output(MultipleQuestionsAnswers)
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

    #result = requests.post(chat_url, headers=header, json=data)
    res = json.loads(result.content.decode("utf-8"))
    return res
