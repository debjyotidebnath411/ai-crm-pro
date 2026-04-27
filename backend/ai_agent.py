
from dotenv import load_dotenv
import os
import json
import re
from typing import TypedDict
from datetime import datetime, timedelta

from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

from config import INTERACTION_TYPES

load_dotenv()

# ==========================================
# LLM CONFIG
# ==========================================
llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name=os.getenv("MODEL_NAME"),
    temperature=0
)

# ==========================================
# STATE
# ==========================================
class AgentState(TypedDict):
    user_input: str
    current_form: dict
    intent: str
    result: dict

# ==========================================
# DATE HELPERS
# ==========================================
def today_date():
    return datetime.today().strftime("%Y-%m-%d")


def yesterday_date():
    return (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")


def normalize_date(value):
    if not value:
        return ""

    val = str(value).strip().lower()

    if val == "today":
        return today_date()

    if val == "yesterday":
        return yesterday_date()

    # already valid yyyy-mm-dd
    if re.match(r"^\d{4}-\d{2}-\d{2}$", val):
        return val

    return ""


# ==========================================
# HELPERS
# ==========================================
def clean_json(text):
    if not text:
        return {}

    text = str(text).strip()

    # Remove markdown wrappers
    text = text.replace("```json", "")
    text = text.replace("```python", "")
    text = text.replace("```", "").strip()

    # Try to extract first JSON object
    match = re.search(r"\{[\s\S]*\}", text)

    if not match:
        return {}

    raw = match.group(0).strip()

    # Attempt 1: direct parse
    try:
        return json.loads(raw)
    except Exception:
        pass

    # Attempt 2: fix smart quotes / quotes issues
    cleaned = raw
    cleaned = cleaned.replace("“", '"').replace("”", '"')
    cleaned = cleaned.replace("‘", "'").replace("’", "'")

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Attempt 3: remove trailing commas before } or ]
    cleaned = re.sub(r",\s*}", "}", cleaned)
    cleaned = re.sub(r",\s*]", "]", cleaned)

    try:
        return json.loads(cleaned)
    except Exception:
        return {}
# ==========================================
# TOOL 1: DETECT INTENT
# ==========================================

def detect_intent_tool(text, current_form=None):
    prompt = f"""
You are an AI CRM router.

Current Form Data:
{json.dumps(current_form or {}, indent=2)}

User Message:
{text}

Decide the user's intent.

Return ONLY one exact token from:

log_interaction
edit_interaction
sentiment_check
suggest_followup
hcp_insights

Rules:
- If user provides a fresh meeting/note, choose log_interaction
- If user updates or adds to existing form data, choose edit_interaction
- If asking sentiment only, choose sentiment_check
- If asking next action, choose suggest_followup
- If asking summary/insight, choose hcp_insights
- Never return explanation text.
"""

    try:
        res = llm.invoke(prompt)
        intent = res.content.strip().lower()

        valid_intents = [
            "log_interaction",
            "edit_interaction",
            "sentiment_check",
            "suggest_followup",
            "hcp_insights"
        ]

        return intent if intent in valid_intents else "log_interaction"

    except:
        return "log_interaction"


# ==========================================
# TOOL 2: LOG INTERACTION
# ==========================================



def log_interaction_tool(text):
    prompt = f"""
You are an AI CRM assistant for pharmaceutical field representatives.

Analyze the user interaction note and extract structured HCP interaction details.

REFERENCE DATES:
TODAY = {today_date()}
YESTERDAY = {yesterday_date()}

Your tasks:
1. Understand the message naturally using business context
2. Extract HCP / doctor name if mentioned
3. Identify interaction type
4. Detect date if mentioned
5. Detect time if mentioned
6. Summarize discussion topics professionally
7. Detect attendees if present
8. Infer sentiment from full context
9. Infer likely business outcome
10. Suggest best next follow-up action
11. Detect materials shared only if explicitly mentioned
12. Detect samples only if explicitly mentioned

RULES:
- Return ONLY valid JSON
- No markdown
- No explanation text
- Use exact keys below
- date format must be YYYY-MM-DD
- time format must be HH:MM (24-hour)

- If date not mentioned, return empty string
- If time not mentioned, return empty string
- If interaction type is unclear, return empty string

- sentiment must be one of:
  Positive
  Neutral
  Negative

- Infer sentiment using overall tone and context, not keywords only

- outcomes should be concise professional business results based on context

- follow_up should be concise practical next actions based on context

- topics must be concise and professional

- Only include materials if explicitly mentioned
- Only include samples if explicitly mentioned

- Do NOT invent unsupported facts
- If unknown, return empty string

RETURN JSON:

{{
  "hcp_name": "",
  "interaction_type": "",
  "date": "",
  "time": "",
  "attendees": "",
  "topics": "",
  "materials": "",
  "samples": "",
  "sentiment": "Neutral",
  "outcomes": "",
  "follow_up": ""
}}

TEXT:
{text}
"""

    res = llm.invoke(prompt)
    data = clean_json(res.content)

    # -------------------------
    # Clean extracted fields
    # -------------------------
    data["hcp_name"] = clean_doctor_name(data.get("hcp_name", ""))

    valid_types = INTERACTION_TYPES

    itype = str(data.get("interaction_type", "")).title().strip()

    if itype in valid_types:
        data["interaction_type"] = itype
    else:
        detect_prompt = f"""
    Identify interaction type from this note.

    Return only one word from:
    {chr(10).join(INTERACTION_TYPES)}

    TEXT:
    {text}
    """
        try:
            guessed = llm.invoke(detect_prompt).content.strip().title()
            data["interaction_type"] = guessed if guessed in valid_types else ""
        except:
            data["interaction_type"] = ""

    data["attendees"] = data.get("attendees", "")
    data["topics"] = data.get("topics", "")
    data["materials"] = data.get("materials", "")
    data["samples"] = data.get("samples", "")

    # -------------------------
    # Sentiment
    # -------------------------
    sent = str(data.get("sentiment", "")).strip()

    valid_sentiments = ["Positive", "Neutral", "Negative"]

    if sent in valid_sentiments:
        data["sentiment"] = sent
    else:
        try:
            data["sentiment"] = sentiment_tool(text)
        except:
            data["sentiment"] = "Neutral"

        
    # -------------------------
    # Outcomes
    # -------------------------
    outcome = str(data.get("outcomes", "")).strip()

    if not outcome:
        try:
            outcome_prompt = f"""
    You are an AI CRM assistant.

    Based on this HCP interaction, provide the most likely business outcome.

    Return ONLY one concise professional sentence.

    Examples:
    Doctor showed interest in product efficacy.
    Requested more clinical evidence.
    Raised pricing concerns.
    No clear commitment provided.

    TEXT:
    {text}
    """
            outcome = llm.invoke(outcome_prompt).content.strip()
        except:
            outcome = ""

    data["outcomes"] = outcome


    # -------------------------
    # Follow-up
    # -------------------------
    follow = str(data.get("follow_up", "")).strip()

    if not follow:
        try:
            follow_prompt = f"""
    You are an AI CRM assistant.

    Suggest the best next follow-up action for the field representative.

    Return ONLY one concise professional sentence.

    Examples:
    Share clinical study summary next week.
    Schedule revisit after two weeks.
    Send requested brochure by email.
    Address objection in next meeting.

    TEXT:
    {text}
    """
            follow = llm.invoke(follow_prompt).content.strip()
        except:
            follow = ""

    data["follow_up"] = follow

    # -------------------------
    # Normalize date
    # -------------------------
    data["date"] = normalize_date(data.get("date"))

    if not data["date"]:
        data["date"] = today_date()

    # -------------------------
    # Normalize time
    # -------------------------
    if not data.get("time"):
        data["time"] = datetime.now().strftime("%H:%M")

    # -------------------------
    # Keep only frontend keys
    # -------------------------
    final_data = {
        "hcp_name": data["hcp_name"],
        "interaction_type": data["interaction_type"],
        "date": data["date"],
        "time": data["time"],
        "attendees": data["attendees"],
        "topics": data["topics"],
        "materials": data["materials"],
        "samples": data["samples"],
        "sentiment": data["sentiment"],
        "outcomes": data["outcomes"],
        "follow_up": data["follow_up"]
    }

    return final_data






# ==========================================
# HELPER: CLEAN DOCTOR NAME
# ==========================================
def clean_doctor_name(name):
    if not name:
        return ""

    name = name.strip()

    # normalize doctor prefix
    name = name.replace("Dr.", "Dr. ")
    name = name.replace("Dr ", "Dr. ")

    # remove double spaces
    name = " ".join(name.split())

    return name


# ==========================================
# TOOL 3: EDIT INTERACTION
# ==========================================
def edit_interaction_tool(text, current_form):
    prompt = f"""
You are editing an existing CRM interaction form.

Current Form:
{json.dumps(current_form)}

IMPORTANT:
- Preserve all unchanged values.
- Update only fields requested by user.
- Preserve every other field exactly.
- Use same JSON keys as current form.
- Return date ONLY in YYYY-MM-DD format.
- today = {today_date()}
- yesterday = {yesterday_date()}
- Return time in HH:MM

Return ONLY updated JSON object.

USER REQUEST:
{text}
"""

    res = llm.invoke(prompt)
    data = clean_json(res.content)

    cleaned = {
        k: v for k, v in data.items()
        if str(v).strip() != ""
    }

    merged = {**current_form, **cleaned}

    merged["hcp_name"] = clean_doctor_name(
    merged.get("hcp_name", "")
)

    merged["topics"] = merged.get("topics", "") or merged.get("topics_discussed", "")
    merged["materials"] = merged.get("materials", "") or merged.get("materials_shared", "")
    merged["samples"] = merged.get("samples", "") or merged.get("samples_distributed", "")
    merged["follow_up"] = merged.get("follow_up", "") or merged.get("follow_up_actions", "")

    merged["date"] = normalize_date(merged.get("date"))

    if not merged.get("time"):
        merged["time"] = datetime.now().strftime("%H:%M")

    return merged


# ==========================================
# TOOL 4: SENTIMENT
# ==========================================
def sentiment_tool(text):
    prompt = f"""
You are an expert CRM sentiment analyzer.

Classify the overall healthcare professional sentiment from this interaction.

Return ONLY one word:

Positive
Neutral
Negative

TEXT:
{text}
"""
    res = llm.invoke(prompt)
    ans = res.content.strip().title()

    return ans if ans in ["Positive", "Neutral", "Negative"] else "Neutral"


# ==========================================
# TOOL 5: FOLLOWUP
# ==========================================
def followup_tool(text):
    prompt = f"""
Suggest one professional next step for healthcare sales representative.

Return short sentence only.

TEXT:
{text}
"""
    res = llm.invoke(prompt)
    return res.content.strip()


# ==========================================
# TOOL 6: INSIGHTS
# ==========================================
def insights_tool(text):
    prompt = f"""
Provide one concise HCP engagement insight.

TEXT:
{text}
"""
    res = llm.invoke(prompt)
    return {"insight": res.content.strip()}

# ==========================================
# VOICE NOTE AI TOOL
# ==========================================

def run_voice_agent(text):
    today = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
You are an AI CRM assistant for pharmaceutical field representatives.

A noisy speech transcript from a doctor meeting is provided.

Your tasks:
1. Correct grammar and likely speech recognition mistakes
2. Correct doctor names, medicine names, and business terms when obvious
3. Convert casual speech into clean professional CRM notes
4. Extract structured CRM fields accurately

STRICT RULES:
- Return ONLY valid JSON
- No markdown
- No explanation text
- Keep output concise and professional
- If transcript says "today", use date: {today}
- If no date mentioned, return empty string
- If no time mentioned, return empty string
- Date format must be YYYY-MM-DD
Time format must be HH:MM (24-hour)
- Sentiment must be one of:
Positive / Neutral / Negative
- Only fill materials if explicitly mentioned
- Only fill samples if explicitly mentioned
- Do NOT assume brochure/sample/shared material
- If field missing, return empty string

Return JSON exactly in this format:

{{
"hcp_name": "",
"interaction_type": "",
"date": "",
"time": "",
"attendees": "",
"topics": "",
"outcomes": "",
"follow_up": "",
"sentiment": "Neutral",
"materials": "",
"samples": ""
}}

VOICE TRANSCRIPT:
{text}
"""

    try:
        res = llm.invoke(prompt)
        data = clean_json(res.content)

        return {
            "hcp_name": str(data.get("hcp_name", "")).strip(),
            "interaction_type": str(data.get("interaction_type", "")).strip() or "",
            "date": str(data.get("date", "")).strip(),
            "time": str(data.get("time", "")).strip(),
            "attendees": str(data.get("attendees", "")).strip(),
            "topics": str(data.get("topics", "")).strip(),
            "outcomes": str(data.get("outcomes", "")).strip(),
            "follow_up": str(data.get("follow_up", "")).strip(),
            "sentiment": str(data.get("sentiment", "Neutral")).strip() or "Neutral",
            "materials": str(data.get("materials", "")).strip(),
            "samples": str(data.get("samples", "")).strip()
        }

    except Exception:
        return {
            "hcp_name": "",
            "interaction_type": "",
            "date": today if "today" in text.lower() else "",
            "time": "",
            "attendees": "",
            "topics": text.strip(),
            "outcomes": "",
            "follow_up": "",
            "sentiment": "Neutral",
            "materials": "",
            "samples": ""
        }

# ==========================================
# ROUTER NODE
# ==========================================

def route_node(state):
    return {
        "intent": detect_intent_tool(
            state["user_input"],
            state.get("current_form", {})
        )
    }

# ==========================================
# GRAPH NODES
# ==========================================


def log_node(state):
    data = log_interaction_tool(state["user_input"])

    if not data.get("sentiment"):
        data["sentiment"] = sentiment_tool(state["user_input"])

    if not data.get("follow_up"):
        data["follow_up"] = followup_tool(state["user_input"])

    return {"result": data}


def edit_node(state):
    data = edit_interaction_tool(
        state["user_input"],
        state.get("current_form", {})
    )
    return {"result": data}


def sentiment_node(state):
    return {
        "result": {
            "sentiment": sentiment_tool(state["user_input"])
        }
    }


def followup_node(state):
    return {
        "result": {
            "follow_up": followup_tool(state["user_input"])
        }
    }


def insights_node(state):
    return {
        "result": insights_tool(state["user_input"])
    }


# ==========================================
# CONDITIONAL ROUTING
# ==========================================
def decide_route(state):
    intent = str(state.get("intent", "")).strip().lower()

    route_map = {
        "log_interaction": "log",
        "edit_interaction": "edit",
        "sentiment_check": "sentiment",
        "suggest_followup": "followup",
        "hcp_insights": "insights"
    }

    return route_map.get(intent, "log")


# ==========================================
# BUILD GRAPH
# ==========================================
builder = StateGraph(AgentState)

builder.add_node("router", route_node)
builder.add_node("log", log_node)
builder.add_node("edit", edit_node)
builder.add_node("sentiment", sentiment_node)
builder.add_node("followup", followup_node)
builder.add_node("insights", insights_node)

builder.set_entry_point("router")

builder.add_conditional_edges(
    "router",
    decide_route,
    {
        "log": "log",
        "edit": "edit",
        "sentiment": "sentiment",
        "followup": "followup",
        "insights": "insights"
    }
)

builder.add_edge("log", END)
builder.add_edge("edit", END)
builder.add_edge("sentiment", END)
builder.add_edge("followup", END)
builder.add_edge("insights", END)

graph = builder.compile()


# ==========================================
# MAIN FUNCTION
# ==========================================
def run_agent(user_text, current_form=None):
    result = graph.invoke({
        "user_input": user_text,
        "current_form": current_form or {}
    })

    return result["result"]