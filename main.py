from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from sqlalchemy import create_engine, Column, String, Integer, DateTime
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
    allow_origins=["*"],  # Change to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

class WeatherEntry(Base):
    __tablename__ = "weather"
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True)
    temperature = Column(String)
    condition = Column(String)
    humidity = Column(String)
    wind_speed = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

@app.get("/weather")
def get_weather(city: str):
    """Fetch weather details for a given city."""
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
    weather_info = {
        "city": city,
        "temperature": f"{data['main']['temp']}°C",
        "condition": data['weather'][0]['description'],
        "humidity": f"{data['main']['humidity']}%",
        "wind_speed": f"{data['wind']['speed']} m/s"
    }

    try:
        db = SessionLocal()
        weather_entry = WeatherEntry(**weather_info)
        db.add(weather_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        db.close()

    return weather_info
