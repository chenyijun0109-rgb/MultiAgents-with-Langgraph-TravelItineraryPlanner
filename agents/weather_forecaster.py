from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama

def weather_forecaster(state):
    llm = ChatOllama(model="llama3.2", base_url="http://localhost:11434")
    preferences = state.get("preferences", {})
    prompt = f"""
    Based on the destination, travel start date, and duration, provide likely seasonal weather guidance for travelers.
    Destination: {preferences.get('destination', '')}
    Travel Start Date: {preferences.get('start_date', '')}
    Duration: {preferences.get('duration', '')} days

    Include temperature range, precipitation expectations, and practical clothing or timing advice.
    """
    try:
        result = llm.invoke([HumanMessage(content=prompt)]).content
        return {"weather_forecast": result.strip()}
    except Exception as e:
        return {"weather_forecast": "", "warning": str(e)}
