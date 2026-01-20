"""
Simple MCP Weather Server - Returns mock weather forecast for any city.
"""

import asyncio
import random
from fastmcp import FastMCP

mcp = FastMCP("Weather")

@mcp.tool(title="Get Weather Forecast")
def get_weather_forecast(city: str) -> str:
    """Today's weather forecast for any city."""
    random.seed(hash(city) % 1000)
    condition = random.choice(["sunny", "cloudy", "rainy", "snowy"])
    temp = random.randint(70, 90)
    forecast = f"Today's Weather Forecast for {city}: {condition.title()}, {temp}°F\n"
    return forecast

if __name__ == "__main__":
    asyncio.run(mcp.run_http_async(host="0.0.0.0", port=8000))