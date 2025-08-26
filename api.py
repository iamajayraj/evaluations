from operator import le
from fastapi import FastAPI, Depends, Request, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, Dict, List
import asyncio
import httpx
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
from starlette.responses import Content
from qa import get_questions_answers, get_context_answers, get_hk_chatbot_answer
from evaluators import hallucination
from metrics import get_metrics
from silence import get_silence_time
import warnings
from pydantic.json_schema import PydanticJsonSchemaWarning
from document_processor import bytes_to_markdown, parse_pdf, get_text_retriever, get_table_retriever, get_context


warnings.filterwarnings("ignore", category=PydanticJsonSchemaWarning)

load_dotenv()


RETELL_BASE_URL = os.getenv("RETELL_BASE_URL")
RETELL_API_KEY = os.getenv("RETELL_API_KEY")

# --- ENV VALIDATION ---
if not RETELL_BASE_URL:
    raise RuntimeError("RETELL_BASE_URL is missing")
parsed = urlparse(RETELL_BASE_URL)
if not parsed.scheme or parsed.scheme not in {"http", "https"}:
    raise RuntimeError("RETELL_BASE_URL must start with http:// or https://")

if not RETELL_API_KEY:
    raise RuntimeError("RETELL_API_KEY is missing")



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # any origin
    allow_credentials=False,      # must be False when using "*"
    allow_methods=["*"],          # or list: ["GET","POST","PUT","DELETE","OPTIONS"]
    allow_headers=["*"],          # or list: ["Content-Type","Authorization",...]
    max_age=600,                  # cache preflight (seconds)
)

class CallPayload(BaseModel):
    limit: int = Field(gt=0, le=200, description="Max calls to fetch (1-200)")
    agent_id: str = Field(min_length=1, description="Retell agent id")
    duration_min: int = Field(gt=59, description="Min duration in seconds")
    duration_max: int = Field(le=1200, description="Max duration in seconds")

    @classmethod
    def as_form(
        cls,
        limit: int = Form(...),
        agent_id: str = Form(...),
        duration_min: int = Form(...),
        duration_max: int = Form(...),
    ):
        return cls(
            limit=limit,
            agent_id=agent_id,
            duration_min=duration_min,
            duration_max=duration_max,
        )

# ---- Fake data fetcher (replace with your real get_calls) ----
async def get_calls(limit: int, agent_id: str, duration_min: int, duration_max: int) -> List[Dict[str, Any]]:
    # do your http/db fetch here
    """Fetches calls from Retell API."""

    payload = {
        "sort_order" : "descending",
        "limit": int(limit),
        "filter_criteria": {
            "agent_id": [agent_id],
            "call_status": ["ended"],
            "disconnection_reason": ["user_hangup","agent_hangup","call_transfer"],
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

@app.get("/")
def index():
    return {"message": "API TAKA-TAK KAAM KAR RHI HAI"}

@app.post("/correctness")
async def correctness(payload: CallPayload):
    # Your logic; example returns first item
    batch = await get_calls(payload.limit, payload.agent_id, payload.duration_min, payload.duration_max)
    tasks = [get_questions_answers(call_data) for call_data in batch]
    results = await asyncio.gather(*tasks)
    if not results:
        raise HTTPException(status_code=404, detail="No calls found")

    batch_ques_ans = [
    {"call_id": call_data["call_id"], "qa_pairs": qa_pairs}
    for call_data, qa_pairs in zip(batch, results)
    ]

    questions_answers = {"questions":[], "answers": []}

    for call in batch_ques_ans:
        for item in call["qa_pairs"].items:
            questions_answers["questions"].append(item.question)
            questions_answers["answers"].append(item.answer)

    all_answers = []
    concurrent_limit = 10
    for question in range(0, len(questions_answers["questions"]), concurrent_limit):
        batch = questions_answers["questions"][question:question + concurrent_limit]
        tasks = [get_hk_chatbot_answer(question) for question in batch]
        results = await asyncio.gather(*tasks)
        answers = [result["answer"] for result in results]
        all_answers += answers

    questions_answers["context_answers"] = all_answers

    hallucination_result = []
    for i in range(len(questions_answers["questions"])):
        hal_res = hallucination(input=questions_answers["questions"][i], output=questions_answers["answers"][i], context=questions_answers["context_answers"][i])
        score = hal_res["score"]
        comment = hal_res["comment"]
        hallucination_result.append({
            "question": questions_answers["questions"][i],
            "answer": questions_answers["answers"][i],
            "context_answer": questions_answers["context_answers"][i],
            "score": score, 
            "comment": comment
            })

    return hallucination_result


@app.post("/metrics")
async def metrics(payload: CallPayload):
    batch = await get_calls(payload.limit, payload.agent_id, payload.duration_min, payload.duration_max)
    
    final_payload = {}
    final_payload["call_id"] = [call_data["call_id"] for call_data in batch]

    #silence time
    individual_silence_time_percall = []
    total_silence_time_percall = []
    for call_data in batch:
        silence_time_data = get_silence_time(call_data)
        individual = [silence_time["duration"] for silence_time in silence_time_data]
        individual_silence_time_percall.append(individual)
        total = sum(individual)
        total_silence_time_percall.append(total)
    total_call_time_percall = [call_data["duration_ms"]/1000 for call_data in batch]
    final_payload["silence_time"] = {}
    final_payload["silence_time"]["per_call"] = total_silence_time_percall
    final_payload["silence_time"]["total_call_time"] = total_call_time_percall
    if sum(total_call_time_percall)>0 and sum(total_silence_time_percall)>0:
        final_payload["silence_time"]["avg_silence_time_per_min"] = sum(total_silence_time_percall)/((sum(total_call_time_percall))/60)
    else:
        final_payload["silence_time"]["avg_silence_time_per_min"] = 0

    final_payload["silence_time"]['individual_silence_time_percall'] = individual_silence_time_percall

    individual_silence_time_count = {
    "silence time more than 5 seconds": 0,
    "silence time more than 4 seconds": 0,
    "silence time more than 3 seconds": 0,
    "silence time more than 2 seconds": 0,
    "silence time more than 1 seconds": 0,
    }

    for call in individual_silence_time_percall:
        for time in call:
            if time > 5.0:
                individual_silence_time_count["silence time more than 5 seconds"] += 1
            elif time > 4.0 and time <= 5.0:
                individual_silence_time_count["silence time more than 4 seconds"] += 1
            elif time > 3.0 and time <= 4.0:
                individual_silence_time_count["silence time more than 3 seconds"] += 1
            elif time > 2.0 and time <= 3.0:   
                individual_silence_time_count["silence time more than 2 seconds"] += 1
            elif time > 1.0 and time <= 2.0:
                individual_silence_time_count["silence time more than 1 seconds"] += 1


    final_payload["silence_time"]["individual_silence_time_count"] = individual_silence_time_count


    #get metrics
    tasks = [get_metrics(call_data["transcript"]) for call_data in batch]
    all_metrics = await asyncio.gather(*tasks)

    #metrics payload preparation
    final_payload["intent_detection"] = []
    final_payload["fallback_rate"] = []
    final_payload["sentiment_analysis"] = []
    final_payload["out_of_scope_queries"] = []
    final_payload["escalation"] = []

    for call in all_metrics:

        #intent detection
        for intent in call.intent_accuracy:
            final_payload["intent_detection"].append({
                "actual_intent": intent.actual_intent,
                "agent_interpreted_intent": intent.agent_interpreted_intent,
                "intent_score": intent.score,
                "explanation": intent.comment
            })

        #fallback rate
        for fallback in call.fallback_rate:
            final_payload["fallback_rate"].append({
                "user_utterance": fallback.user_utterance,
                "fallback_response": fallback.fallback_response,
                "reason_inferred": fallback.reason_inferred
            })
        
        #sentiment analysis
        final_payload["sentiment_analysis"].append({
            "sentiment": call.sentiment_analysis.sentiment,
            "reason": call.sentiment_analysis.reason
        })

        #out of scope queries
        final_payload["out_of_scope_queries"] += call.out_of_scope_queries

        #escalation
        final_payload["escalation"].append({
            "escalation_category": call.escalation.escalation_category,
            "escalation_reason": call.escalation.escalation_reason
        })
            

    return final_payload

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".pdf"}

@app.post("/factual-correctness")
async def upload_file(payload: CallPayload = Depends(CallPayload.as_form), file: UploadFile = File(...)):

    filename = file.filename
    extension = os.path.splitext(filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Upload file with a valid file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content into memory
    content = await file.read()

    # Validate content
    if not content or len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty or content not available"
        )

    # Your logic; example returns first item
    batch = await get_calls(payload.limit, payload.agent_id, payload.duration_min, payload.duration_max)
    tasks = [get_questions_answers(call_data) for call_data in batch]
    results = await asyncio.gather(*tasks)
    if not results:
        raise HTTPException(status_code=404, detail="No calls found")

    batch_ques_ans = [
    {"call_id": call_data["call_id"], "qa_pairs": qa_pairs}
    for call_data, qa_pairs in zip(batch, results)
    ]

    questions_answers = {"questions":[], "answers": [], "contextual_answers": [], "retrieved_context": []}

    for call in batch_ques_ans:
        for item in call["qa_pairs"].items:
            questions_answers["questions"].append(item.question)
            questions_answers["answers"].append(item.answer)

    if extension == ".pdf":
        full_text = ""
        for page in parse_pdf(content):
            page_text = page["page_text"] + "\n\n"
            full_text += page_text
        text_retriever = get_text_retriever(full_text)

        tables = []
        for page in parse_pdf(content):
            for table in page["page_tables"]:
                tables.append(table["table"])
        table_retriever = get_table_retriever(tables)

        for question in questions_answers["questions"]:
            textual_context = get_context(question, text_retriever)
            tabular_context = get_context(question, table_retriever)

            full_context = textual_context + "\n\n" + tabular_context

            context_answer = await get_context_answers(question, full_context)

            questions_answers["contextual_answers"].append(context_answer)
            questions_answers["retrieved_context"].append(full_context)
            
        return questions_answers

    elif extension in [".csv", ".xlsx", ".xls"]:
        md_text = bytes_to_markdown(content, extension)
        columns = md_text.split("\n")[0]
        text_retriever = get_text_retriever(md_text)

        for question in questions_answers["questions"]:
            textual_context = get_context(question, text_retriever)

            full_context = columns + "\n\n" + textual_context

            context_answer = await get_context_answers(question, full_context)

            questions_answers["contextual_answers"].append(context_answer)
            questions_answers["retrieved_context"].append(full_context)

        return questions_answers