import json
import re


VALID_ITEM_TYPES = {"attraction", "restaurant", "hotel", "transport", "activity", "downtime"}


def extract_json_object(text: str) -> dict | None:
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


def validate_itinerary_data(data: dict) -> list[str]:
    errors = []
    if not isinstance(data, dict):
        return ["Itinerary data must be a JSON object."]

    if not isinstance(data.get("title"), str) or not data.get("title", "").strip():
        errors.append("Missing title.")

    if not isinstance(data.get("summary"), str):
        errors.append("Missing summary.")

    days = data.get("days")
    if not isinstance(days, list) or not days:
        errors.append("Missing days list.")
        return errors

    for day_index, day in enumerate(days, start=1):
        if not isinstance(day, dict):
            errors.append(f"Day {day_index} must be an object.")
            continue

        if not isinstance(day.get("day"), int):
            errors.append(f"Day {day_index} is missing numeric day.")
        if not isinstance(day.get("date"), str) or not day.get("date", "").strip():
            errors.append(f"Day {day_index} is missing date.")
        if not isinstance(day.get("title"), str):
            errors.append(f"Day {day_index} is missing title.")

        items = day.get("items")
        if not isinstance(items, list) or not items:
            errors.append(f"Day {day_index} is missing items.")
            continue

        for item_index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                errors.append(f"Day {day_index} item {item_index} must be an object.")
                continue

            if not isinstance(item.get("time"), str) or not item.get("time", "").strip():
                errors.append(f"Day {day_index} item {item_index} is missing time.")
            if not isinstance(item.get("name"), str) or not item.get("name", "").strip():
                errors.append(f"Day {day_index} item {item_index} is missing name.")

            item_type = item.get("type")
            if item_type not in VALID_ITEM_TYPES:
                errors.append(f"Day {day_index} item {item_index} has invalid type: {item_type}.")

            for optional_field in ["description", "transport_note"]:
                if optional_field in item and not isinstance(item.get(optional_field), str):
                    errors.append(f"Day {day_index} item {item_index} has invalid {optional_field}.")

        for optional_field in ["dining", "downtime"]:
            if optional_field in day and not isinstance(day.get(optional_field), str):
                errors.append(f"Day {day_index} has invalid {optional_field}.")

    return errors


def markdown_from_itinerary_data(data: dict) -> str:
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
            lines.append(f"### {time_label}: {name}")
            lines.append(f"*{item_type.title()}*")
            if description:
                lines.append(description)
            if transport:
                lines.append(f"Transport: {transport}")
            lines.append("")

        dining = day.get("dining")
        if dining:
            lines.extend(["**Dining**", dining, ""])

        downtime = day.get("downtime")
        if downtime:
            lines.extend(["**Downtime**", downtime, ""])

    return "\n".join(lines).strip()


def parse_and_validate_itinerary(text: str) -> tuple[dict | None, list[str]]:
    data = extract_json_object(text)
    if not data:
        return None, ["The model response could not be parsed as JSON."]

    errors = validate_itinerary_data(data)
    if errors:
        return None, errors

    return data, []
