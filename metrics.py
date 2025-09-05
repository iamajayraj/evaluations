from pydantic import Field, BaseModel
from typing import Literal, List
from langchain_openai import ChatOpenAI
from prompts import get_metrics_prompt
from dotenv import load_dotenv
load_dotenv()
import os
import requests
import asyncio

RETELL_BASE_URL = os.getenv("RETELL_BASE_URL")
RETELL_API_KEY = os.getenv("RETELL_API_KEY")



def get_calls(limit: int, agent_id: str, duration_min: int, duration_max: int):
    # do your http/db fetch here
    """Fetches calls from Retell API."""

    payload = {
        "sort_order" : "descending",
        "limit": int(limit),
        "filter_criteria": {
            "agent_id": [agent_id],
            "call_status": ["ended"],
            "duration_ms": {
                "upper_threshold": int(duration_max)*1000,
                "lower_threshold": int(duration_min)*1000
            }
        }
    }

    headers = {"authorization": f"Bearer {RETELL_API_KEY}",
           "Content-Type": "application/json"}

    
    response = requests.post(f"{RETELL_BASE_URL}/v2/list-calls", headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch call: {response.status_code} - {response.text}")

SentimentCategory = Literal["Positive", 
                             "Neutral", 
                             "Confused", 
                             "Frustrated", 
                             "Annoyed", 
                             "Angry", 
                             "Happy", 
                             "Other"]

CallTransferCategory = Literal[
    "Urgent or Emergency Situations",
    "Complaint or Dissatisfaction",
    "Billing or Payment Issues",
    "Sensitive or Confidential Information",
    "Technical Support Required",
    "Policy Exceptions or Approvals",
    "Special Requests or Custom Orders",
    "Complex Inquiry or Escalation",
    "Language or Communication Barrier",
    "Customer Preference for Human Interaction",
    "Not Applicable"
]

class IntentDetection(BaseModel):
    actual_intent: str = Field(..., description="The actual query intent of the user in a fully-resolved context complete form.")
    agent_interpreted_intent: str = Field(..., description="The intent interpreted by the agent from the user query")
    score: float = Field(..., description="An intent detection score between 0 and 1")
    comment: str = Field(..., description="A one-line description providing the clarification behind the given intent score")

class Fallback(BaseModel):
    user_utterance: str = Field(..., description="User query in context complete form that triggered fallback")
    fallback_response: str = Field(..., description="Exact fallback reply given by the agent")
    reason_inferred: str = Field(..., description="possible cause of fallback")

class SentimentAnalysis(BaseModel):
    sentiment: SentimentCategory = Field(..., description="Overall sentiment category of the user experience with the agent")
    reason: str = Field(..., description="A brief explanation providing the reasoning behind the given sentiment")

class Escalation(BaseModel):
    escalation_category: CallTransferCategory = Field("Not Applicable", description="Category of the reason behind call transfer, assign 'Not Applicable' if no call transfer"),
    escalation_reason: str = Field("No Call Transfer", description="User query in context complete form due to which the call was transferred")

class MainClass(BaseModel):
    intent_accuracy: List[IntentDetection]
    fallback_rate: List[Fallback]
    sentiment_analysis: SentimentAnalysis
    out_of_scope_queries: List[str] = Field(..., description="A list of out-of-scope queries in context complete form")
    escalation: Escalation

async def get_metrics(transcript):

    prompt = get_metrics_prompt.format(transcript = transcript)

    llm = ChatOpenAI(model="gpt-4o").with_structured_output(MainClass).with_retry(stop_after_attempt=3)
    result = await llm.ainvoke(prompt)

    return result

