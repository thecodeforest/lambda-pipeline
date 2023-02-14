import requests


def get_weather(city: str, api_key: str) -> dict:
    """Get the weather for a city."""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Error: Failed to retrieve weather data.")
        return None


def extract_weather_data(data: dict) -> list:
    """Convert the JSON response to a Pandas DataFrame."""
    temperature = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    description = data["weather"][0]["description"]
    return [temperature, humidity, description]


def convert_celcius_to_fahrenheit(celcius: float) -> float:
    """Convert Celcius to Fahrenheit."""
    return celcius * 9 / 5 + 32
