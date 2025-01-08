from pydantic import BaseModel
from typing import Optional
import requests
import os
from dotenv import load_dotenv
from langchain.agents import Tool


load_dotenv()
location_key = os.getenv("LOCATION_KEY")
api_key = os.getenv("ACU_WEATHER_API_KEY")

class Temperature(BaseModel):
    Value: float
    Unit: str
    UnitType: int

class Weather(BaseModel):
    LocalObservationDateTime: str
    EpochTime: int
    WeatherText: str
    WeatherIcon: int
    HasPrecipitation: bool
    PrecipitationType: Optional[str]
    IsDayTime: bool
    Temperature: dict
    MobileLink: str
    Link: str

def get_weather(input: str) -> Weather:
    input = input.lower()
    url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}?apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    weather = Weather(**data[0])  # Transformer le premier élément de la liste en objet Weather
    return weather


weather_tool = Tool(
        name="get_weather",
        func=get_weather,
        description="""This tool can fetch the current weather in Montréal.
                        You will get a Weather object with the following attributes:
                        - LocalObservationDateTime: str
                        - EpochTime: int
                        - WeatherText: str
                        - WeatherIcon: int
                        - HasPrecipitation: bool
                        - PrecipitationType: Optional[str]
                        - IsDayTime: bool
                        - Temperature: dict
                        - MobileLink: str
                        - Link: str

                        you will respond to the user with the sentence: 
                        'The weather is currently: weather.WeatherText with a temperature of 
                        weather.Temperature['Metric']['Value'] degrees Celsius.'
                        """,
    )

