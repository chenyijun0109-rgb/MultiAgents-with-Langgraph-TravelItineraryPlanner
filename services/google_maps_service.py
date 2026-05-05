import json
import os
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
from urllib.request import urlopen


AUTOCOMPLETE_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"
DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"


def get_google_maps_api_key() -> str:
    return os.getenv("GOOGLE_MAPS_API_KEY", "").strip()


def _get_json(url: str) -> dict:
    with urlopen(url, timeout=10) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def autocomplete_cities(query: str, language: str = "en") -> tuple[list[dict], str | None]:
    api_key = get_google_maps_api_key()
    if not api_key:
        return [], "GOOGLE_MAPS_API_KEY is not configured."

    if not query.strip():
        return [], None

    params = {
        "input": query.strip(),
        "types": "(cities)",
        "language": language,
        "key": api_key,
    }
    try:
        data = _get_json(f"{AUTOCOMPLETE_URL}?{urlencode(params)}")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
        return [], f"Google Places autocomplete request failed: {e}"
    status = data.get("status")

    if status in {"OK", "ZERO_RESULTS"}:
        predictions = [
            {
                "description": prediction.get("description", ""),
                "place_id": prediction.get("place_id", ""),
            }
            for prediction in data.get("predictions", [])
            if prediction.get("description") and prediction.get("place_id")
        ]
        return predictions, None

    return [], data.get("error_message") or f"Google Places autocomplete failed: {status}"


def get_place_details(place_id: str, language: str = "en") -> tuple[dict | None, str | None]:
    api_key = get_google_maps_api_key()
    if not api_key:
        return None, "GOOGLE_MAPS_API_KEY is not configured."

    if not place_id:
        return None, "No place_id was provided."

    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,geometry,place_id",
        "language": language,
        "key": api_key,
    }
    try:
        data = _get_json(f"{DETAILS_URL}?{urlencode(params)}")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
        return None, f"Google Place Details request failed: {e}"
    status = data.get("status")

    if status != "OK":
        return None, data.get("error_message") or f"Google Place Details failed: {status}"

    result = data.get("result", {})
    location = result.get("geometry", {}).get("location", {})
    return {
        "name": result.get("name", ""),
        "address": result.get("formatted_address", ""),
        "place_id": result.get("place_id", place_id),
        "lat": location.get("lat"),
        "lng": location.get("lng"),
    }, None


def make_maps_url(name: str, address: str = "") -> str:
    query = " ".join(part for part in [name, address] if part).strip()
    return f"https://www.google.com/maps/search/?api=1&{urlencode({'query': query})}"


def make_photo_url(photo_reference: str, max_width: int = 800) -> str:
    api_key = get_google_maps_api_key()
    if not api_key or not photo_reference:
        return ""

    params = {
        "maxwidth": str(max_width),
        "photo_reference": photo_reference,
        "key": api_key,
    }
    return f"{PHOTO_URL}?{urlencode(params)}"


def _format_route_location(location: dict) -> str:
    place_id = location.get("place_id")
    if place_id:
        return f"place_id:{place_id}"
    return f"{location['lat']},{location['lng']}"


def _format_maps_url_location(location: dict) -> str:
    if location.get("name"):
        return location["name"]
    return f"{location['lat']},{location['lng']}"


def make_directions_url(locations: list[dict], travel_mode: str = "walking") -> str:
    if len(locations) < 2:
        return ""

    origin = _format_maps_url_location(locations[0])
    destination = _format_maps_url_location(locations[-1])
    waypoints = "|".join(_format_maps_url_location(location) for location in locations[1:-1][:9])
    params = {
        "api": "1",
        "origin": origin,
        "destination": destination,
        "travelmode": travel_mode,
    }
    if waypoints:
        params["waypoints"] = waypoints
    return f"https://www.google.com/maps/dir/?{urlencode(params)}"


def decode_polyline(polyline: str) -> list[list[float]]:
    index = 0
    lat = 0
    lng = 0
    coordinates = []

    while index < len(polyline):
        result = 0
        shift = 0
        while True:
            byte = ord(polyline[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        lat += ~(result >> 1) if result & 1 else result >> 1

        result = 0
        shift = 0
        while True:
            byte = ord(polyline[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        lng += ~(result >> 1) if result & 1 else result >> 1

        coordinates.append([lng * 1e-5, lat * 1e-5])

    return coordinates


def get_directions_route(
    locations: list[dict],
    travel_mode: str = "walking",
    language: str = "en",
) -> tuple[dict | None, str | None]:
    api_key = get_google_maps_api_key()
    if not api_key:
        return None, "GOOGLE_MAPS_API_KEY is not configured."

    if len(locations) < 2:
        return None, None

    params = {
        "origin": _format_route_location(locations[0]),
        "destination": _format_route_location(locations[-1]),
        "mode": travel_mode,
        "language": language,
        "key": api_key,
    }
    waypoints = [_format_route_location(location) for location in locations[1:-1]]
    if waypoints:
        params["waypoints"] = "|".join(waypoints)

    try:
        data = _get_json(f"{DIRECTIONS_URL}?{urlencode(params)}")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
        return None, f"Google Directions request failed: {e}"

    status = data.get("status")
    if status == "ZERO_RESULTS":
        return None, "No route found for this day."
    if status != "OK":
        return None, data.get("error_message") or f"Google Directions failed: {status}"

    route = data.get("routes", [{}])[0]
    encoded_polyline = route.get("overview_polyline", {}).get("points", "")
    if not encoded_polyline:
        return None, "Google Directions did not return a route polyline."

    legs = route.get("legs", [])
    distance_meters = sum(leg.get("distance", {}).get("value", 0) for leg in legs)
    duration_seconds = sum(leg.get("duration", {}).get("value", 0) for leg in legs)
    return {
        "path": decode_polyline(encoded_polyline),
        "distance_meters": distance_meters,
        "duration_seconds": duration_seconds,
        "summary": route.get("summary", ""),
        "warnings": route.get("warnings", []),
        "copyrights": route.get("copyrights", ""),
        "maps_url": make_directions_url(locations, travel_mode),
    }, None


def search_hotel(
    hotel_name: str,
    destination_name: str,
    destination_lat: float | None = None,
    destination_lng: float | None = None,
    language: str = "en",
) -> tuple[dict | None, str | None]:
    api_key = get_google_maps_api_key()
    if not api_key:
        return None, "GOOGLE_MAPS_API_KEY is not configured."

    if not hotel_name.strip():
        return None, None

    query = f"{hotel_name.strip()} hotel {destination_name}".strip()
    params = {
        "query": query,
        "type": "lodging",
        "language": language,
        "key": api_key,
    }
    if destination_lat is not None and destination_lng is not None:
        params["location"] = f"{destination_lat},{destination_lng}"
        params["radius"] = "50000"

    try:
        data = _get_json(f"{TEXT_SEARCH_URL}?{urlencode(params)}")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
        return None, f"Google Places hotel search request failed: {e}"

    status = data.get("status")
    if status == "ZERO_RESULTS":
        return None, "No matching hotel was found. Please check the hotel name or leave it blank."

    if status != "OK":
        return None, data.get("error_message") or f"Google Places hotel search failed: {status}"

    result = next((item for item in data.get("results", []) if item.get("place_id")), None)
    if not result:
        return None, "No matching hotel was found. Please check the hotel name or leave it blank."

    location = result.get("geometry", {}).get("location", {})
    name = result.get("name", hotel_name.strip())
    address = result.get("formatted_address", "")
    photos = result.get("photos", [])
    photo_reference = photos[0].get("photo_reference") if photos else ""
    return {
        "name": name,
        "address": address,
        "place_id": result.get("place_id"),
        "lat": location.get("lat"),
        "lng": location.get("lng"),
        "maps_url": make_maps_url(name, address),
        "photo_url": make_photo_url(photo_reference),
    }, None


def search_place(
    place_name: str,
    destination_name: str,
    destination_lat: float | None = None,
    destination_lng: float | None = None,
    language: str = "en",
) -> tuple[dict | None, str | None]:
    api_key = get_google_maps_api_key()
    if not api_key:
        return None, "GOOGLE_MAPS_API_KEY is not configured."

    if not place_name.strip():
        return None, None

    query = f"{place_name.strip()} {destination_name}".strip()
    params = {
        "query": query,
        "language": language,
        "key": api_key,
    }
    if destination_lat is not None and destination_lng is not None:
        params["location"] = f"{destination_lat},{destination_lng}"
        params["radius"] = "50000"

    try:
        data = _get_json(f"{TEXT_SEARCH_URL}?{urlencode(params)}")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
        return None, f"Google Places search request failed: {e}"

    status = data.get("status")
    if status == "ZERO_RESULTS":
        return None, None

    if status != "OK":
        return None, data.get("error_message") or f"Google Places search failed: {status}"

    result = next((item for item in data.get("results", []) if item.get("place_id")), None)
    if not result:
        return None, None

    location = result.get("geometry", {}).get("location", {})
    name = result.get("name", place_name.strip())
    address = result.get("formatted_address", "")
    photos = result.get("photos", [])
    photo_reference = photos[0].get("photo_reference") if photos else ""
    return {
        "name": name,
        "address": address,
        "place_id": result.get("place_id"),
        "lat": location.get("lat"),
        "lng": location.get("lng"),
        "maps_url": make_maps_url(name, address),
        "photo_url": make_photo_url(photo_reference),
    }, None
