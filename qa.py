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



async def get_questions_answers(call_data):
    """Extracts questions and answers using the LLM."""

    prompt = get_questions_answers_prompt.format(transcript=call_data["transcript"])
    
    messages = [
        SystemMessage(prompt)
    ]

    llm = ChatOpenAI(model="gpt-4o").with_structured_output(MultipleQuestionsAnswers).with_retry(stop_after_attempt=3)
    response = await llm.ainvoke(messages)
    return response


async def get_context_answers(question, context):

    prompt = f"""You are tasked with answering the following questions strictly based on the provided context.  

                - Use only the information contained in the context.  
                - If the answer to a question is not explicitly available in the context, respond exactly with:  
                  "Answer not present in given context" without any additional information. 
                - Do NOT alter, rephrase, or interpret the given questions in any way.  
                - Keep your answers brief and directly tied to the context.

                Questions:  
                \n\n{question}\n\n  

                Context:  
                \n\n{context}\n\n  
                """

    messages = [
        SystemMessage(prompt)
    ]

    llm = ChatOpenAI(model="gpt-4o")
    response = await llm.ainvoke(messages)
    return response.content

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
