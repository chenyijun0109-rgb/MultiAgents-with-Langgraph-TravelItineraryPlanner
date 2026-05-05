from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama
import json

from agents.generate_itinerary import _extract_json_object, _fallback_markdown_from_data


def revise_itinerary(state):
    llm = ChatOllama(model="llama3.2", base_url="http://localhost:11434")
    preferences = state.get("preferences", {})
    current_itinerary_data = state.get("itinerary_data", {})
    current_itinerary = state.get("itinerary", "")
    revision_request = state.get("user_question", "")

    hotel = preferences.get("hotel")
    hotel_rule = (
        "- Keep the confirmed hotel as the route anchor when practical."
        if hotel
        else "- No confirmed hotel was provided. Do not invent or add a hotel anchor."
    )

    prompt = f"""
    Revise the existing travel itinerary according to the user's request.

    Confirmed preferences:
    {json.dumps(preferences, indent=2)}

    Current structured itinerary:
    {json.dumps(current_itinerary_data, indent=2)}

    Current readable itinerary:
    {current_itinerary}

    User revision request:
    {revision_request}

    Hard rules:
    - Keep the confirmed destination. Do not invent, replace, or autocorrect the destination.
    - Preserve the same trip dates and duration unless the user explicitly asks to change dates.
    {hotel_rule}
    - Make the requested change directly in the itinerary.
    - Keep the route geographically practical and avoid unnecessary backtracking.

    Return only one valid JSON object. Do not wrap it in markdown fences.
    Do not include a markdown field. Do not include multi-line string values.
    The JSON object must use this schema:
    {{
      "title": "string",
      "summary": "string",
      "revision_summary": "brief explanation of what changed",
      "days": [
        {{
          "day": 1,
          "date": "YYYY-MM-DD",
          "title": "string",
          "items": [
            {{
              "time": "Morning/Afternoon/Evening or HH:MM",
              "name": "place or activity name",
              "type": "attraction|restaurant|hotel|transport|activity|downtime",
              "description": "string",
              "transport_note": "string"
            }}
          ],
          "dining": "string",
          "downtime": "string"
        }}
      ]
    }}

    Requirements:
    - Include every major attraction and restaurant needed for later map lookup.
    - Keep every string value short and single-line so the JSON remains valid.
    """

    try:
        result = llm.invoke([HumanMessage(content=prompt)]).content
        itinerary_data = _extract_json_object(result)
        if not itinerary_data:
            return {
                "chat_response": "I tried to update the itinerary, but the revised plan could not be parsed. Please try rephrasing the change.",
                "warning": "The revised itinerary could not be parsed as structured JSON.",
            }

        markdown = _fallback_markdown_from_data(itinerary_data)
        revision_summary = itinerary_data.get("revision_summary", "Updated the itinerary based on your request.")
        return {
            "itinerary": markdown.strip(),
            "itinerary_data": itinerary_data,
            "revision_summary": revision_summary,
            "latest_revision_request": revision_request,
            "chat_response": f"Updated your itinerary: {revision_summary}",
        }
    except Exception as e:
        return {
            "chat_response": "",
            "warning": str(e),
        }
