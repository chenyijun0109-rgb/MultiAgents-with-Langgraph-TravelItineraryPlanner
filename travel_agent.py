from datetime import date
from typing import Annotated, TypedDict

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOllama
from langchain_community.utilities import GoogleSerperAPIWrapper
from langgraph.graph import END, StateGraph

from agents import (
    chat_agent,
    fetch_useful_links,
    food_culture_recommender,
    generate_itinerary,
    recommend_activities,
    weather_forecaster,
)
from services.google_maps_service import (
    autocomplete_cities,
    get_google_maps_api_key,
    get_place_details,
    search_place,
    search_hotel,
)
from utils_export import export_to_pdf


load_dotenv()

st.set_page_config(page_title="AI Travel Planner", layout="wide")


try:
    llm = ChatOllama(model="llama3.2", base_url="http://localhost:11434")
except Exception as e:
    st.error(f"LLM initialization failed: {str(e)}")
    st.stop()


try:
    search = GoogleSerperAPIWrapper()
except Exception as e:
    st.error(f"Serper API initialization failed: {str(e)}")
    st.stop()


class GraphState(TypedDict):
    preferences_text: str
    preferences: dict
    itinerary: str
    itinerary_data: dict
    map_points: list[dict]
    map_warnings: list[str]
    activity_suggestions: str
    useful_links: list[dict]
    weather_forecast: str
    packing_list: str
    food_culture_info: str
    chat_history: Annotated[list[dict], "List of question-response pairs"]
    user_question: str
    chat_response: str


@st.cache_data(ttl=300, show_spinner=False)
def cached_city_autocomplete(query: str) -> tuple[list[dict], str | None]:
    return autocomplete_cities(query)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_place_details(place_id: str) -> tuple[dict | None, str | None]:
    return get_place_details(place_id)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_hotel_search(
    hotel_name: str,
    destination_name: str,
    destination_lat: float | None,
    destination_lng: float | None,
) -> tuple[dict | None, str | None]:
    return search_hotel(hotel_name, destination_name, destination_lat, destination_lng)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_place_search(
    place_name: str,
    destination_name: str,
    destination_lat: float | None,
    destination_lng: float | None,
) -> tuple[dict | None, str | None]:
    return search_place(place_name, destination_name, destination_lat, destination_lng)


def build_map_points(preferences: dict, itinerary_data: dict) -> tuple[list[dict], list[str]]:
    points = []
    warnings = []

    hotel = preferences.get("hotel")
    if hotel and hotel.get("lat") is not None and hotel.get("lng") is not None:
        points.append(
            {
                "day": 0,
                "name": hotel.get("name", "Hotel"),
                "type": "hotel",
                "lat": hotel.get("lat"),
                "lng": hotel.get("lng"),
                "address": hotel.get("address", ""),
                "maps_url": hotel.get("maps_url", ""),
                "photo_url": hotel.get("photo_url", ""),
            }
        )

    searchable_types = {"attraction", "restaurant", "activity"}
    seen = {point["name"].lower() for point in points}
    destination = preferences.get("destination", "")
    destination_lat = preferences.get("destination_lat")
    destination_lng = preferences.get("destination_lng")

    for day in itinerary_data.get("days", []):
        for item in day.get("items", []):
            item_type = item.get("type", "").lower()
            name = item.get("name", "").strip()
            if not name or item_type not in searchable_types or name.lower() in seen:
                continue

            place, error = cached_place_search(name, destination, destination_lat, destination_lng)
            if error:
                warnings.append(f"{name}: {error}")
                continue
            if not place or place.get("lat") is None or place.get("lng") is None:
                continue

            points.append(
                {
                    "day": day.get("day"),
                    "name": place.get("name", name),
                    "type": item_type,
                    "lat": place.get("lat"),
                    "lng": place.get("lng"),
                    "address": place.get("address", ""),
                    "maps_url": place.get("maps_url", ""),
                    "photo_url": place.get("photo_url", ""),
                }
            )
            seen.add(name.lower())

            if len(points) >= 25:
                return points, warnings

    return points, warnings


workflow = StateGraph(GraphState)
workflow.add_node("generate_itinerary", generate_itinerary.generate_itinerary)
workflow.set_entry_point("generate_itinerary")
workflow.add_edge("generate_itinerary", END)
graph = workflow.compile()


st.markdown("# AI-Powered Travel Itinerary Planner")

if "state" not in st.session_state:
    st.session_state.state = {
        "preferences_text": "",
        "preferences": {},
        "itinerary": "",
        "itinerary_data": {},
        "map_points": [],
        "map_warnings": [],
        "activity_suggestions": "",
        "useful_links": [],
        "weather_forecast": "",
        "packing_list": "",
        "food_culture_info": "",
        "chat_history": [],
        "user_question": "",
        "chat_response": "",
    }


if not get_google_maps_api_key():
    st.warning("GOOGLE_MAPS_API_KEY is not configured. Destination autocomplete needs Google Places API.")

destination_query = st.text_input(
    "Destination",
    placeholder="Start typing a city, e.g. Shanghai or shang",
)

destination_predictions = []
destination_error = None
if destination_query.strip():
    destination_predictions, destination_error = cached_city_autocomplete(destination_query.strip())

selected_prediction = None
if destination_error:
    st.error(destination_error)
elif destination_predictions:
    prediction_labels = [prediction["description"] for prediction in destination_predictions]
    selected_label = st.selectbox("Destination Suggestions", prediction_labels)
    selected_prediction = next(
        prediction
        for prediction in destination_predictions
        if prediction["description"] == selected_label
    )
    st.caption("Powered by Google Places")
elif destination_query.strip():
    st.error("No matching city found. Please check the spelling or keep typing.")


with st.form("travel_form"):
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Travel Start Date", value=date.today())
        duration = st.slider("Number of Days", 1, 30, 7)
    with col2:
        hotel_name = st.text_input("Hotel Name", placeholder="Optional")
        comments = st.text_area("Additional Preferences")

    submit_btn = st.form_submit_button("Generate Itinerary")


if submit_btn:
    if not destination_query.strip():
        st.error("Please enter a destination before generating an itinerary.")
        st.stop()

    if destination_error:
        st.error(destination_error)
        st.stop()

    if not selected_prediction:
        st.error("Please choose a destination from the Google Places suggestions before generating an itinerary.")
        st.stop()

    destination_details, details_error = cached_place_details(selected_prediction["place_id"])
    if details_error or not destination_details:
        st.error(details_error or "Could not confirm this destination with Google Places.")
        st.stop()

    destination_name = destination_details.get("name") or selected_prediction["description"]
    destination_address = destination_details.get("address") or selected_prediction["description"]
    hotel = None

    if hotel_name.strip():
        hotel, hotel_error = cached_hotel_search(
            hotel_name.strip(),
            destination_name,
            destination_details.get("lat"),
            destination_details.get("lng"),
        )
        if hotel_error or not hotel:
            st.error(hotel_error or "Could not confirm this hotel with Google Places.")
            st.stop()

    preferences_text = (
        f"Confirmed Destination: {destination_name}\n"
        f"Destination Address: {destination_address}\n"
        f"Travel Start Date: {start_date.isoformat()}\n"
        f"Duration: {duration} days\n"
        f"Hotel: {hotel['name'] if hotel else 'Not provided'}\n"
        f"Hotel Address: {hotel['address'] if hotel else 'Not provided'}\n"
        f"Additional Preferences: {comments or 'None'}"
    )
    preferences = {
        "destination_input": destination_query,
        "destination": destination_name,
        "destination_address": destination_address,
        "destination_confirmed": True,
        "destination_place_id": destination_details.get("place_id"),
        "destination_lat": destination_details.get("lat"),
        "destination_lng": destination_details.get("lng"),
        "start_date": start_date.isoformat(),
        "duration": duration,
        "hotel_name": hotel_name,
        "hotel": hotel,
        "comments": comments,
    }

    st.session_state.state.update(
        {
            "preferences_text": preferences_text,
            "preferences": preferences,
            "chat_history": [],
            "user_question": "",
            "chat_response": "",
            "activity_suggestions": "",
            "itinerary_data": {},
            "map_points": [],
            "map_warnings": [],
            "useful_links": [],
            "weather_forecast": "",
            "packing_list": "",
            "food_culture_info": "",
        }
    )

    with st.spinner("Generating itinerary..."):
        result = graph.invoke(st.session_state.state)
        st.session_state.state.update(result)
        if result.get("itinerary"):
            map_points, map_warnings = build_map_points(
                st.session_state.state["preferences"],
                st.session_state.state.get("itinerary_data", {}),
            )
            st.session_state.state["map_points"] = map_points
            if map_warnings:
                st.session_state.state["map_warnings"] = map_warnings
            else:
                st.session_state.state["map_warnings"] = []
            st.success("Itinerary Created")
        else:
            st.error(result.get("warning") or "Failed to generate itinerary.")


if st.session_state.state.get("itinerary"):
    col_itin, col_chat = st.columns([3, 2])

    with col_itin:
        st.markdown("### Travel Itinerary")
        st.markdown(st.session_state.state["itinerary"])

        if st.session_state.state.get("map_points"):
            st.markdown("### Map Overview")
            map_df = pd.DataFrame(st.session_state.state["map_points"])
            st.map(map_df, latitude="lat", longitude="lng")
            with st.expander("Map Places", expanded=False):
                for point in st.session_state.state["map_points"]:
                    label = f"Day {point['day']}" if point.get("day") else "Hotel"
                    if point.get("maps_url"):
                        st.markdown(f"- **{label}**: [{point['name']}]({point['maps_url']})")
                    else:
                        st.markdown(f"- **{label}**: {point['name']}")

            photo_points = [
                point
                for point in st.session_state.state["map_points"]
                if point.get("photo_url") and point.get("type") in {"attraction", "restaurant", "activity"}
            ]
            if photo_points:
                st.markdown("### Place Photos")
                photos_by_day = {}
                for point in photo_points:
                    photos_by_day.setdefault(point.get("day", "Other"), []).append(point)

                for day, points in photos_by_day.items():
                    st.markdown(f"#### Day {day}")
                    columns = st.columns(min(len(points), 3))
                    for index, point in enumerate(points[:3]):
                        with columns[index % len(columns)]:
                            st.image(point["photo_url"], caption=point["name"], use_column_width=True)

        # Packing list is intentionally hidden for now so the app stays focused on itinerary planning.
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        with col_btn1:
            if st.button("Get Activity Suggestions"):
                with st.spinner("Fetching activity suggestions..."):
                    result = recommend_activities.recommend_activities(st.session_state.state)
                    st.session_state.state.update(result)
        with col_btn2:
            if st.button("Get Useful Links"):
                with st.spinner("Fetching useful links..."):
                    result = fetch_useful_links.fetch_useful_links(st.session_state.state)
                    st.session_state.state.update(result)
        with col_btn3:
            if st.button("Get Weather Forecast"):
                with st.spinner("Fetching weather forecast..."):
                    result = weather_forecaster.weather_forecaster(st.session_state.state)
                    st.session_state.state.update(result)
        with col_btn4:
            if st.button("Get Food & Culture Info"):
                with st.spinner("Fetching food and culture info..."):
                    result = food_culture_recommender.food_culture_recommender(st.session_state.state)
                    st.session_state.state.update(result)

        if st.session_state.state.get("activity_suggestions"):
            with st.expander("Activity Suggestions", expanded=False):
                st.markdown(st.session_state.state["activity_suggestions"])

        if st.session_state.state.get("useful_links"):
            with st.expander("Useful Links", expanded=False):
                for link in st.session_state.state["useful_links"]:
                    st.markdown(f"- [{link['title']}]({link['link']})")

        if st.session_state.state.get("weather_forecast"):
            with st.expander("Weather Forecast", expanded=False):
                st.markdown(st.session_state.state["weather_forecast"])

        if st.session_state.state.get("food_culture_info"):
            with st.expander("Food & Culture Info", expanded=False):
                st.markdown(st.session_state.state["food_culture_info"])

        if st.button("Export as PDF"):
            pdf_path = export_to_pdf(st.session_state.state["itinerary"])
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    st.download_button("Download Itinerary PDF", f, file_name="itinerary.pdf")

    with col_chat:
        st.markdown("### Chat About Your Itinerary")
        for chat in st.session_state.state["chat_history"]:
            with st.chat_message("user"):
                st.markdown(chat["question"])
            with st.chat_message("assistant"):
                st.markdown(chat["response"])

        if user_input := st.chat_input("Ask something about your itinerary"):
            st.session_state.state["user_question"] = user_input
            with st.spinner("Generating response..."):
                result = chat_agent.chat_node(st.session_state.state)
                st.session_state.state.update(result)
                st.rerun()
else:
    st.info("Fill the form and generate an itinerary to begin.")
