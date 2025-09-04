

get_questions_answers_prompt = """
You are given a call transcript between a User (customer) and a Voice Agent (AI assistant).
Your task is to extract all information-seeking questions asked by the User and the corresponding answers provided by the Voice Agent.

Requirements:

1. Focus only on information-seeking questions

- Include only questions where the User is genuinely requesting information, clarification, or details.

- Exclude greetings, confirmations, acknowledgments, or small talk.

2. Detailed and Context-Rich Outputs

- Both questions and answers must be rewritten in a complete, self-contained, and context-rich form so that anyone can fully understand them without seeing the transcript.

Include all necessary details such as location, date, time, quantity, names, services, products, or other contextual information.

3. Resolve Vague References

- Replace all pronouns, placeholders, or vague references (e.g., “it,” “there,” “he,” “yesterday,” “tomorrow”) with their explicit meaning based on the transcript context.

- For time references like "yesterday" or "tomorrow," replace them with the actual day of the week or date if available.

4. Strict Role Attribution

- Only extract questions explicitly asked by the User.

- Only include answers explicitly provided by the Voice Agent.

- Do not infer or create information not present in the transcript.

5. Clarity and Consistency

- Ensure the final text is grammatically correct, uses full sentences, and is easy to read.

6. Only extract questions that are asked by the user.

7. Only include answers that are given by the voice agent.

Provide the output in the specified format below.

This is the input transcript: \n\n{transcript}\n\n
"""

new_get_questions_answers_prompt = """

**Task:** Analyze the provided transcript of a conversation between a User and a Voice Agent. Your goal is to extract pairs where the **User asks a question** and the **Voice Agent provides a direct answer**. The final output must be optimized for a Retrieval-Augmented Generation (RAG) system to verify the accuracy of the agent's responses, meaning every question and answer pair must be completely self-contained and unambiguous.

**Instructions:**

**Step 1: Identification & Pairing**
*   Identify every question asked by the **User** where the intent is to seek information, request a service, ask for clarification, or inquire about details (e.g., "What are your hours?", "Can you help me book a flight?").
*   **Exclude** rhetorical questions and social chit-chat (e.g., "How are you today?").
*   For each identified User question, extract the direct and complete **answer provided by the Voice Agent** that immediately addresses it.

**Step 2: Contextual Enrichment & Explicit Reference Replacement**
*   For both the user's question and the agent's answer, replace all pronouns, vague references, and implied context with their specific meanings directly from the conversation. This is critical for the RAG context.
    *   **Pronouns & Demonstratives:** Replace "it," "they," "that," "there" with the specific entity (e.g., "the vacuum cleaner," "the technician," "at the Broadway branch").
    *   **Temporal References:** Replace "yesterday," "today," "tomorrow," "next week" with the actual date (e.g., "on Monday, October 26th") or a specific day of the week inferred from the transcript's context and timestamp.
    *   **Vague Terms:** Replace terms like "the thing," "the person" with explicit names, products, or service details.
*   **Apply this enrichment to both the original question and the agent's answer.**

**Step 3: Question Reformating (Critical for RAG)**
*   Reformulate each original user question into a complete, context-rich, and standalone format. The goal is that the question alone contains all necessary entities and specifics for a knowledge base to retrieve the correct answer without any prior conversation history.
*   **Follow these formatting rules:**
    *   **Always include the primary subject/entity** (e.g., the business name, service, or product) explicitly in the question, even if it was only implied in the original transcript.
    *   **Incorporate all key contextual details** like location, date, time, product name, and user-specific parameters (e.g., child's age, membership type) directly into the question structure.
    *   **Rephrase for clarity and directness** while preserving the original user's intent and all factual details.

   **Examples of Reformating:**
    *   Original: "Do you have a trampoline park there?"
      → **Formatted:** "Does [Location] have a trampoline park?"
    *   Original: "Are you open on that Monday holiday?"
      → **Formatted:** "Is [Location] open on Monday, [Date], which is Labor Day?"
    *   Original: "How much is it for a five-year-old?"
      → **Formatted:** "What is the admission price for a five-year-old child at [Location]?"

**Step 4: Final Output Format**
*   Present your final extraction as a list of JSON objects.
*   Each JSON object must have two keys:
    1.  `"question"`: The completely reformatted, context-rich, and explicit version of the question, built for RAG retrieval.
    2.  `"answer"`: The Voice Agent's explicit and context-enriched answer to that specific question, **after applying Step 2 (enrichment)**.

**Transcript for Analysis:**
\n\n{transcript}\n\n

"""

get_metrics_prompt = """
You are given a transcript of a conversation between a **user** and a **voice agent**.
Your task is to analyze the conversation and extract **four key performance metrics**: **Intent Accuracy**, **Fallback Rate (with scenarios)**, **Sentiment Analysis**, and **Out-of-Scope Queries**.

This is the input transcription between the user and agent: \n\n {transcript} \n\n.

### **1. Intent Accuracy**

**Definition:** Measures how accurately the agent identifies the user’s intention.

* Give a score between 0 and 1 based on how accurately the agent captures the user query intent.
    - 1 if the agent’s interpreted intent matches the user’s actual intent.
    - 0 if misunderstood, clueless or ignored the query.

**Output fields:**

* `actual_intent` (context-complete)
* `agent_interpreted_intent`
* `intent_score` (score between 0 and 1)
* `explanation` (one liner explanation of score)

---

### **2. Fallback Rate**

**Definition:** Percentage of times the agent fails to understand the user and triggers fallback responses (e.g., “Sorry, I didn’t catch that,” “Can you repeat that?”).

**Steps:**

1. Identify each fallback event.
2. For each fallback, capture:

   * `user_utterance` (that triggered fallback)
   * `fallback_response` (exact text from the agent)
   * `reason_inferred` (brief explanation why fallback might have occurred).


### **3. Sentiment Analysis**

**Definition:** Analyze the overall conversation, provide the sentiment of the user experience based on the conversation.

* Categories: Positive, Neutral, Confused, Frustrated, Annoyed, Angry, Happy, Other (specify).
* Provide a brief reason for sentiment label.

---

### **4. Out-of-Scope Queries**

**Definition:** Those user questions the bot wasn’t trained to handle. Strictly consider information seeking questions only
where user is asking for some form of information that is unavailable to the agent.

* Mark as out-of-scope if the agent gives an unrelated answer, says it doesn’t know, or avoids the question.

---

### **5. Escalation Reason**

**Definition:** When the voice agent had to transfer the call to a human due to user request, confusion, error, or user dissatisfaction..

* Mark as call escalated if the agent transfers the call to a human agent. 
* Assign a category based on the reason behind the call transfer. Also, extract the user query in context complete form which led the call transfer.
* If no call transfer occurred, assign 'Not Applicable' to escalation_category and 'No Call Transfer' to escalation_reason.

---

### **Output Format (JSON)**

```json
{{
  "intent_accuracy": [
    {{
      "actual_intent": "<fully-resolved context complete intent>",
      "agent_interpreted_intent": "<perceived intent>",
      "intent_score": " a score between 0 and 1",
      "explanation": "<one line reason behind given score>"
    }}
  ],
  "fallback_rate":  [
      {{
        "user_utterance": "<user text in context complete form that triggered fallback>",
        "fallback_response": "<exact fallback reply from agent>",
        "reason_inferred": "<possible cause of fallback>"
      }}
    ]
  ,
  "sentiment_analysis":
    {{
      "sentiment": "<call sentiment category>",
      "reason": "<brief justification>"
    }}
    ,
  "out_of_scope_queries": [
      "<user query in fully-resolved context complete form that was out-of-scope>"
    ],
  "escalation": {{
      "escalation_category":"<Category of the reason behind call transfer, assign 'Not Applicable' if no call transfer>",
      "escalation_reason":"<User query in context complete form due to which the call was transferred>"
    }}
}}
"""

get_context_answers_prompt = """
Role: You are an AI assistant designed to provide accurate and helpful answers based exclusively on the context provided below. Your primary goal is to be truthful and avoid speculation.

Context:
\n\n{context}\n\n

User Question:
\n\n{question}\n\n

Instructions:

Understand & Analyze: Carefully read the user's question to understand what is being asked.

Ground Your Answer: Your answer must be grounded 100% in the provided context. Do not use any pre-existing knowledge, assumptions, or beliefs.

Reasoning Process:

If the answer is explicitly stated in the context, summarize it clearly.

If the answer is not stated but can be inferred from the context (e.g., using logic, combining multiple pieces of information, applying general rules to specific cases), you must show your reasoning.

Example: "Based on the context which states [Rule A] and the user's question about [Specific Case B], the answer is inferred to be [Answer C]."

If the context is contradictory, point out the contradiction and present the different pieces of information.

If the context is insufficient or completely missing the information needed to answer the question, state this clearly. Do not attempt to make up an answer. A good response is: "Based on the provided context, I cannot confirm this information. The document does not contain details about [topic of question]."

Final Answer Structure:

Provide a direct, concise answer to the user's question first.

Then, in a separate section labeled "Source and Reasoning:", explain how you arrived at that answer. Cite the relevant parts of the context or describe the logic of your inference. This builds trust and allows users to verify the information.

Unanswerable Questions: If the question cannot be answered from the context at all, politely decline to answer and explain why. For example, "I cannot answer this question as it requires information not found in the provided documents."

Output Format:

```json
{{
  "answer": "<direct, concise answer to the question>",
  "source_and_reasoning": "<how you arrived at the answer, citing relevant context or explaining inference logic>"
}}
```

"""