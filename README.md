# AI Travel Itinerary Planner

This project is an upgraded version of the original **MultiAgents-with-Langgraph-TravelItineraryPlanner**. It keeps the original Streamlit + LangGraph + Ollama multi-agent structure, but extends it into a more realistic travel planning tool with Google Places validation, hotel-aware planning, structured itineraries, maps, photos, real routes, dynamic chat revisions, and richer PDF export.

Original repository:

```text
https://github.com/vikrambhat2/MultiAgents-with-Langgraph-TravelItineraryPlanner
```

## What Changed From the Original Project

The original project generated a travel itinerary from free-form inputs such as destination, month, duration, number of people, holiday type, and budget type. This version focuses on making the itinerary more realistic, verifiable, and editable.

Major changes include:

- Replaced free-text destination handling with **Google Places Autocomplete**.
- Added destination validation through **Google Place Details**.
- Removed less useful early-stage fields: `Holiday Type`, `Budget Type`, and `Number of People`.
- Replaced `Month of Travel` with an exact `Travel Start Date`.
- Added optional `Hotel Name` input.
- If a hotel is provided, the trip is planned around the confirmed hotel location.
- If no hotel is provided, the app does not invent a hotel and plans around city areas instead.
- Added structured JSON itinerary generation.
- Stopped displaying raw model JSON on the page.
- Added JSON schema validation and one automatic retry when the model output is invalid.
- Added Google Places lookup for attractions, restaurants, and activities.
- Added a `pydeck` map with colored daily points, labels, tooltips, and routes.
- Added Google Directions API support for real daily routes.
- Added Google Maps route links for each day.
- Added Google Places Photos support for major places.
- Added dynamic chat-based itinerary revision.
- Added itinerary version tracking.
- Enhanced PDF export with route links, place links, and available place photos.
- Temporarily hidden the packing list feature so the app can focus on itinerary planning.

## Current Features

- Validated destination autocomplete powered by Google Places.
- Exact travel date and trip duration inputs.
- Optional hotel-aware itinerary planning.
- Structured day-by-day itinerary generation.
- Attractions, restaurants, and activities extracted from the itinerary.
- Google Places geocoding for map points.
- Google Directions routes for each day.
- Interactive `pydeck` map with:
  - daily colors,
  - type markers,
  - hover tooltips,
  - real route paths when available,
  - fallback straight lines when Directions fails.
- Place photos from Google Places Photos.
- Chat interface for:
  - asking questions about the itinerary,
  - revising the itinerary dynamically.
- Itinerary version tracking after generation and revisions.
- Supporting agents for:
  - activity suggestions,
  - useful links,
  - weather guidance,
  - food and culture information.
- PDF export with:
  - itinerary text,
  - daily route links,
  - place links,
  - available place photos.

## Project Structure

```text
.
├── agents/
│   ├── chat_agent.py
│   ├── classify_chat_intent.py
│   ├── fetch_useful_links.py
│   ├── food_culture_recommender.py
│   ├── generate_itinerary.py
│   ├── itinerary.py
│   ├── itinerary_schema.py
│   ├── packing_list_generator.py
│   ├── recommend_activities.py
│   ├── revise_itinerary.py
│   └── weather_forecaster.py
├── services/
│   ├── __init__.py
│   └── google_maps_service.py
├── travel_agent.py
├── utils_export.py
├── requirements.txt
├── PROJECT_CURRENT_PROGRESS_PLAN_CN.md
└── README.md
```

## Main Files

- `travel_agent.py`  
  Main Streamlit application. Handles the UI, LangGraph workflow, Google Places results, maps, photos, chat revision flow, and export actions.

- `agents/generate_itinerary.py`  
  Generates the initial structured itinerary.

- `agents/itinerary_schema.py`  
  Extracts, validates, and renders itinerary JSON.

- `agents/classify_chat_intent.py`  
  Classifies chat input as either a normal question or an itinerary revision request.

- `agents/revise_itinerary.py`  
  Revises the existing itinerary based on user chat instructions.

- `services/google_maps_service.py`  
  Wraps Google Maps Platform calls:
  - Places Autocomplete,
  - Place Details,
  - Text Search,
  - Place Photos,
  - Directions API,
  - Google Maps links.

- `utils_export.py`  
  Exports the itinerary to PDF with route links, place links, and available photos.

## Requirements

- Python 3.8+
- Ollama running locally
- `llama3.2` model installed in Ollama
- Google Serper API key
- Google Maps Platform API key

Google APIs used:

- Places API
- Directions API

The app also builds Google Maps URLs, which do not require an API key.

## Environment Variables

Create a `.env` file in the project root:

```text
SERPER_API_KEY=your_serper_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

Make sure the following are enabled in Google Cloud:

- Places API
- Directions API

You also need billing enabled for Google Maps Platform.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/vikrambhat2/MultiAgents-with-Langgraph-TravelItineraryPlanner.git
cd MultiAgents-with-Langgraph-TravelItineraryPlanner
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Pull the Ollama model:

```bash
ollama pull llama3.2
```

4. Start Ollama:

```bash
ollama serve
```

5. Run the Streamlit app:

```bash
streamlit run travel_agent.py
```

Then open the local Streamlit URL shown in the terminal, usually:

```text
http://localhost:8501
```

## How to Use

1. Enter a destination.
2. Select a destination from the Google Places suggestions.
3. Choose a travel start date.
4. Choose the number of travel days.
5. Optionally enter a hotel name.
6. Add preferences such as:
   - relaxed pace,
   - museums,
   - local food,
   - shopping,
   - fewer long walks.
7. Click `Generate Itinerary`.
8. Review the itinerary, map, route links, place links, and photos.
9. Use the chat panel to ask questions or revise the itinerary.
10. Export the final itinerary as a PDF.

Example revision request:

```text
Replace the museums on day 2 with shopping streets and cafes.
```

The app will update the main itinerary, refresh the map, refresh route links, and update photos.

## Current Limitations

- Google Directions routes are available only when the Directions API succeeds; otherwise the app falls back to straight-line route display.
- Chat revision works, but version history UI and undo controls are still planned.
- PDF export is functional but visually simple.
- Google Places photo attribution is noted generally, but detailed attribution handling can be improved.
- The packing list agent still exists in the codebase, but the UI entry point is currently hidden.

## Current Development Plan

The latest planning document is:

```text
PROJECT_CURRENT_PROGRESS_PLAN_CN.md
```

Next recommended improvements:

- Add itinerary version history UI.
- Add undo / restore previous version.
- Improve route mode selection.
- Improve PDF layout and image attribution.
- Strengthen JSON schema validation further.

## Acknowledgements

This project builds on the original LangGraph travel planner and extends it with more realistic location-aware planning.

Core technologies:

- Streamlit
- LangGraph
- LangChain
- Ollama
- Google Maps Platform
- Google Serper
- PyDeck
- FPDF
