from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama
import json

from agents.itinerary_schema import markdown_from_itinerary_data, parse_and_validate_itinerary


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
        else (
            "- No confirmed hotel was provided. Do not invent a hotel, do not mention a hotel anchor, "
            "and plan each day around geographically clustered areas in the destination."
        )
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
    Do not include a markdown field. Do not include multi-line string values.
    The JSON object must use this schema:
    {{
      "title": "string",
      "summary": "string",
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
    - The days/items data must include every major attraction and restaurant needed for later map lookup.
    - Include morning, afternoon, evening, dining options, downtime, and brief transport notes.
    - Keep every string value short and single-line so the JSON remains valid.
    """
    try:
        itinerary_data = None
        errors = []
        for attempt in range(2):
            retry_instruction = ""
            if attempt == 1:
                retry_instruction = (
                    "\nYour previous response failed validation for these reasons:\n"
                    f"{json.dumps(errors, indent=2)}\n"
                    "Return corrected JSON only."
                )

            result = llm.invoke([HumanMessage(content=prompt + retry_instruction)]).content
            itinerary_data, errors = parse_and_validate_itinerary(result)
            if itinerary_data:
                break

        if not itinerary_data:
            return {
                "itinerary": "",
                "itinerary_data": {},
                "warning": "The itinerary could not be generated as valid structured JSON after retry. Please try again.",
            }

        markdown = markdown_from_itinerary_data(itinerary_data)
        return {"itinerary": markdown.strip(), "itinerary_data": itinerary_data}
    except Exception as e:
        return {"itinerary": "", "itinerary_data": {}, "warning": str(e)}
