from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama
import json


REVISION_KEYWORDS = [
    "change",
    "replace",
    "remove",
    "delete",
    "add",
    "revise",
    "update",
    "swap",
    "move",
    "reschedule",
    "instead",
    "don't want",
    "do not want",
    "改",
    "修改",
    "换",
    "替换",
    "不要",
    "删除",
    "去掉",
    "增加",
    "加上",
    "安排",
    "调整",
]


def classify_chat_intent(state):
    user_question = state.get("user_question", "").strip()
    lowered = user_question.lower()

    if any(keyword in lowered for keyword in REVISION_KEYWORDS):
        return {"chat_intent": "revise"}

    llm = ChatOllama(model="llama3.2", base_url="http://localhost:11434")
    prompt = f"""
    Classify the user message as either:
    - "revise": the user wants to change, replace, remove, add, or reschedule part of the itinerary.
    - "answer": the user is asking a question or wants explanation without changing the itinerary.

    Return only JSON:
    {{"intent": "revise"}}
    or
    {{"intent": "answer"}}

    User message:
    {user_question}
    """
    try:
        result = llm.invoke([HumanMessage(content=prompt)]).content
        parsed = json.loads(result.strip())
        intent = parsed.get("intent", "answer")
        if intent not in {"revise", "answer"}:
            intent = "answer"
        return {"chat_intent": intent}
    except Exception:
        return {"chat_intent": "answer"}
