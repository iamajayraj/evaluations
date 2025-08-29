
get_questions_answers_prompt = """
You are given a call transcript between a User (customer) and a Voice Agent (AI assistant).
Your task is to extract all the questions asked by the User and the answers given by the Voice Agent.

Requirements:

- Only include questions where the User is seeking information (not greetings, confirmations, or small talk).

- Both the question and the answer must be in fully resolved, context-complete form so that anyone reading them understands exactly:

- What information is being asked (intent)

- All relevant details (location, time, quantity, names, product/service, etc.)

- Replace all pronouns, placeholders, or vague references with their actual noun or value based on the context from the transcript.

- Only extract questions that are asked by the User and answers that are given by the Voice Agent.

Example:

Transcript: "Where is it located?" → Question: "Where is California located?"

Transcript: "He gave me 20 dollars" → Answer: "The customer gave me 20 dollars."

Please provide the answer in the given format only.

This is the input transcript: \n\n{transcript}\n\n
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