from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
DATABASE_URL = os.getenv("DATABASE_URL")

# App and CORS setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# SQLAlchemy model
class WeatherEntry(Base):
    __tablename__ = "weather"
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True)
    temperature = Column(Float)
    condition = Column(String)
    humidity = Column(Float)
    wind_speed = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Pydantic schema
class WeatherResponse(BaseModel):
    city: str
    temperature: float
    condition: str
    humidity: float
    wind_speed: float

# Help endpoint
@app.get("/help")
def get_help():
    return {
        "description": "This API returns current weather data for a given city.",
        "usage": "/weather?city=CityName",
        "example": "/weather?city=London",
    }

# Weather endpoint
@app.get("/weather", response_model=WeatherResponse)
def get_weather(city: str):
    """Fetch weather details for a given city and store in the database."""
    try:
        response = requests.get(WEATHER_API_URL, params={
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": "metric"
        })
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather data: {e}")

    data = response.json()
    weather_info = WeatherResponse(
        city=city,
        temperature=data['main']['temp'],
        condition=data['weather'][0]['description'],
        humidity=data['main']['humidity'],
        wind_speed=data['wind']['speed']
    )

    try:
        with SessionLocal() as db:
            weather_entry = WeatherEntry(**weather_info.dict())
            db.add(weather_entry)
            db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    return weather_info
