from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama
import json
import re


def _extract_json_object(text: str) -> dict | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        return json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None


def _fallback_markdown_from_data(data: dict) -> str:
    lines = [f"# {data.get('title', 'Travel Itinerary')}", ""]
    if data.get("summary"):
        lines.extend([data["summary"], ""])

    for day in data.get("days", []):
        heading = f"## Day {day.get('day', '')}: {day.get('date', '')}"
        if day.get("title"):
            heading += f" - {day['title']}"
        lines.extend([heading, ""])

        for item in day.get("items", []):
            time_label = item.get("time", "Flexible")
            name = item.get("name", "Activity")
            item_type = item.get("type", "activity")
            description = item.get("description", "")
            transport = item.get("transport_note", "")
            lines.append(f"- **{time_label} | {name}** ({item_type})")
            if description:
                lines.append(f"  {description}")
            if transport:
                lines.append(f"  Transport: {transport}")
        lines.append("")

        dining = day.get("dining")
        if dining:
            lines.extend(["Dining:", dining, ""])

        downtime = day.get("downtime")
        if downtime:
            lines.extend(["Downtime:", downtime, ""])

    return "\n".join(lines).strip()


def generate_itinerary(state):
    llm = ChatOllama(model="llama3.2", base_url="http://localhost:11434")
    preferences = state.get("preferences", {})

    if not preferences.get("destination_confirmed") or not preferences.get("destination"):
        return {
            "itinerary": "",
            "warning": "Destination is not confirmed. Please choose a valid destination before generating an itinerary.",
        }

    hotel = preferences.get("hotel")
    hotel_rule = (
        "- Use the confirmed hotel object as the daily route anchor. Start and end days near this hotel when practical.\n"
        "- Use the hotel's address and coordinates to reduce unnecessary travel between distant areas."
        if hotel
        else "- No confirmed hotel was provided, so choose sensible central daily route anchors."
    )

    prompt = f"""
    Create a practical travel itinerary using only the confirmed user preferences below.
    {json.dumps(preferences, indent=2)}

    Hard rules:
    - Use only the confirmed destination in the preferences.
    - Do not invent, replace, or autocorrect the destination.
    - If the destination is missing, invalid, or unconfirmed, do not create an itinerary.
    - Base the plan on the exact travel start date and duration.
    {hotel_rule}
    - Avoid unnecessary cross-city backtracking.

    Return only one valid JSON object. Do not wrap it in markdown fences.
    The JSON object must use this schema:
    {{
      "title": "string",
      "summary": "string",
      "markdown": "A complete readable itinerary in Markdown",
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
    - The markdown field must be ready to display to the user.
    - The days/items data must include every major attraction and restaurant needed for later map lookup.
    - Include morning, afternoon, evening, dining options, downtime, and brief transport notes.
    """
    try:
        result = llm.invoke([HumanMessage(content=prompt)]).content
        itinerary_data = _extract_json_object(result)
        if not itinerary_data:
            return {
                "itinerary": result.strip(),
                "itinerary_data": {},
                "warning": "The itinerary was generated, but it could not be parsed as structured JSON.",
            }

        markdown = itinerary_data.get("markdown") or _fallback_markdown_from_data(itinerary_data)
        return {"itinerary": markdown.strip(), "itinerary_data": itinerary_data}
    except Exception as e:
        return {"itinerary": "", "itinerary_data": {}, "warning": str(e)}
