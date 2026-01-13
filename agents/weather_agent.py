"""
Weather Agent - A specialized agent for fetching weather information.

This agent uses the Google ADK LlmAgent with custom tools to provide
weather forecasts and current conditions for any location.
"""

import os
import httpx
from typing import Optional
from google.adk.agents import Agent


def get_weather(location: str, unit: str = "celsius") -> dict:
    """
    Get current weather information for a specific location.
    
    Args:
        location: The city or location name (e.g., "London", "New York", "Tokyo")
        unit: Temperature unit - either "celsius" or "fahrenheit" (default: celsius)
    
    Returns:
        A dictionary containing weather information including:
        - temperature: Current temperature
        - description: Weather condition description
        - humidity: Humidity percentage
        - wind_speed: Wind speed
        - location: The queried location
    """
    # Check for OpenWeatherMap API key for real data
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    
    if api_key and api_key != "your_openweathermap_api_key":
        try:
            # Use real API if key is available
            units = "metric" if unit == "celsius" else "imperial"
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": location,
                "appid": api_key,
                "units": units
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                return {
                    "location": location,
                    "temperature": f"{data['main']['temp']}°{'C' if unit == 'celsius' else 'F'}",
                    "description": data['weather'][0]['description'].title(),
                    "humidity": f"{data['main']['humidity']}%",
                    "wind_speed": f"{data['wind']['speed']} {'m/s' if unit == 'celsius' else 'mph'}",
                    "feels_like": f"{data['main']['feels_like']}°{'C' if unit == 'celsius' else 'F'}",
                    "source": "OpenWeatherMap API"
                }
        except Exception as e:
            # Fall back to mock data on error
            pass
    
    # Mock weather data for demonstration when no API key is available
    mock_weather_data = {
        "london": {"temp_c": 12, "temp_f": 54, "desc": "Partly Cloudy", "humidity": 78, "wind": 15},
        "new york": {"temp_c": 8, "temp_f": 46, "desc": "Sunny", "humidity": 55, "wind": 12},
        "tokyo": {"temp_c": 18, "temp_f": 64, "desc": "Clear Sky", "humidity": 62, "wind": 8},
        "paris": {"temp_c": 14, "temp_f": 57, "desc": "Overcast", "humidity": 80, "wind": 10},
        "sydney": {"temp_c": 25, "temp_f": 77, "desc": "Sunny", "humidity": 45, "wind": 18},
        "berlin": {"temp_c": 6, "temp_f": 43, "desc": "Light Rain", "humidity": 85, "wind": 20},
        "madrid": {"temp_c": 22, "temp_f": 72, "desc": "Clear", "humidity": 40, "wind": 14},
        "dubai": {"temp_c": 35, "temp_f": 95, "desc": "Hot and Sunny", "humidity": 30, "wind": 12},
    }
    
    # Normalize location for lookup
    location_key = location.lower().strip()
    
    if location_key in mock_weather_data:
        weather = mock_weather_data[location_key]
        temp = weather["temp_c"] if unit == "celsius" else weather["temp_f"]
        unit_symbol = "C" if unit == "celsius" else "F"
        
        return {
            "location": location.title(),
            "temperature": f"{temp}°{unit_symbol}",
            "description": weather["desc"],
            "humidity": f"{weather['humidity']}%",
            "wind_speed": f"{weather['wind']} km/h",
            "source": "Mock Data (set OPENWEATHERMAP_API_KEY for real data)"
        }
    else:
        # Generate plausible data for unknown locations
        import random
        temp_c = random.randint(5, 30)
        temp = temp_c if unit == "celsius" else int(temp_c * 9/5 + 32)
        unit_symbol = "C" if unit == "celsius" else "F"
        conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Clear"]
        
        return {
            "location": location.title(),
            "temperature": f"{temp}°{unit_symbol}",
            "description": random.choice(conditions),
            "humidity": f"{random.randint(30, 90)}%",
            "wind_speed": f"{random.randint(5, 25)} km/h",
            "source": "Generated Mock Data (set OPENWEATHERMAP_API_KEY for real data)"
        }


# Create the Weather Agent using Google ADK
weather_agent = Agent(
    name="weather_agent",
    model="gemini-2.0-flash",
    description="A specialized agent that provides current weather information and forecasts for any location worldwide. Use this agent when users ask about weather, temperature, climate conditions, or forecasts.",
    instruction="""You are a helpful weather assistant. Your role is to:

1. Use the get_weather tool to fetch current weather data for any location
2. Present weather information in a clear, friendly, and informative way
3. Offer to convert between Celsius and Fahrenheit if requested
4. Provide context about the weather conditions (e.g., "Perfect day for outdoor activities!")
5. If asked about forecasts, explain that you provide current conditions

When responding:
- Always mention the location name
- Include temperature, conditions, humidity, and wind speed
- Add a brief comment about what the weather means for activities
- Be conversational and helpful

Example response format:
"The weather in [Location] is currently [temperature] with [conditions]. 
Humidity is at [humidity]% and wind speeds are [wind_speed].
[Brief helpful comment about the weather]"
""",
    tools=[get_weather],
)
