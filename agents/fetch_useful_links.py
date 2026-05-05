from langchain_community.utilities import GoogleSerperAPIWrapper

def fetch_useful_links(state):
    search = GoogleSerperAPIWrapper()
    preferences = state.get('preferences', {})
    destination = preferences.get('destination', '')
    start_date = preferences.get('start_date', '')
    query = f"Travel tips and guides for {destination} around {start_date}"
    try:
        search_results = search.results(query)
        organic_results = search_results.get("organic", [])
        links = [
            {"title": result.get("title", "No title"), "link": result.get("link", "")}
            for result in organic_results[:5]
        ]
        return {"useful_links": links}
    except Exception as e:
        return {"useful_links": [], "warning": f"Failed to fetch links: {str(e)}"}
