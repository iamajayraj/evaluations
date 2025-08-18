from openevals.llm import create_llm_as_judge
from openevals.prompts import CORRECTNESS_PROMPT
from openevals.prompts import HALLUCINATION_PROMPT
from dotenv import load_dotenv
load_dotenv()



correctness_evaluator = create_llm_as_judge(
    prompt=CORRECTNESS_PROMPT,
    feedback_key="correctness",
    model="openai:o3-mini",
    continuous=True
)

hallunicination_evaluator = create_llm_as_judge(
    prompt=HALLUCINATION_PROMPT,
    feedback_key="hallucination",
    model="openai:o3-mini",
    continuous=True
)

def correctness(input, output, reference_outputs):
    correctness_evaluator = create_llm_as_judge(
    prompt=CORRECTNESS_PROMPT,
    feedback_key="correctness",
    model="openai:o3-mini",
    continuous=True
    )
    return correctness_evaluator(inputs=input, 
                           outputs=output,
                           reference_outputs=reference_outputs)

def hallucination(input, output, context, reference_outputs=""):
    hallunicination_evaluator = create_llm_as_judge(
    prompt=HALLUCINATION_PROMPT,
    feedback_key="hallucination",
    model="openai:o3-mini",
    continuous=True
    )
    return hallunicination_evaluator(inputs=input, 
                           outputs=output,
                           context=context,
                           reference_outputs=reference_outputs)

