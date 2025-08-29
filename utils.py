import httpx
import os
import asyncio
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
load_dotenv()

RETELL_BASE_URL = os.getenv("RETELL_BASE_URL")
RETELL_API_KEY = os.getenv("RETELL_API_KEY")

async def get_calls(limit: int, agent_id: str, duration_min: int, duration_max: int, batch_ids: Optional[List[str]]) -> List[Dict[str, Any]]:
    
    """Fetches calls from Retell API."""

    payload = {
        "sort_order" : "descending",
        "limit": int(limit),
        "filter_criteria": {
            "agent_id": [agent_id],
            "batch_call_id": batch_ids,
            "call_status": ["ended"],
            "disconnection_reason": ["user_hangup","agent_hangup","call_transfer","max_duration_reached"],
            "duration_ms": {
                "upper_threshold": int(duration_max)*1000,
                "lower_threshold": int(duration_min)*1000
            }
        }
    }

    headers = {"authorization": f"Bearer {RETELL_API_KEY}",
           "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{RETELL_BASE_URL}/v2/list-calls", headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch call: {response.status_code} - {response.text}")


def filter_voicemail_calls(calls):
    new_batch = []
    for call in calls:
        if "in_voicemail" in call["call_analysis"]:
            if call["call_analysis"]["in_voicemail"] == False:
                new_batch.append(call)

        else:
            new_batch.append(call)
    
    return new_batch

        