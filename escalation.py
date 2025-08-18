from typing import Literal
from pydantic import BaseModel, Field
import asyncio
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from dotenv import load_dotenv
load_dotenv()

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
    "Customer Preference for Human Interaction"
]

class CallTransferReason(BaseModel):
    category: CallTransferCategory = Field(..., description="Category of transfer")



async def get_escalation_rate(trancript):

    #prompt for extracting transfer reasons
    prompt = f"""You are given a call transcript between a user and a voice agent.
    Your task is to extract the transfer reasons from the transcript.
    This is the input trancript: \n\n{trancript}\n\n"""
    
    messages = [
        SystemMessage(prompt)
    ]

    llm = ChatOpenAI(model="gpt-4o").with_structured_output(CallTransferReason)
    response = await llm.ainvoke(messages)
    return response

