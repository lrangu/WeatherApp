from fastapi import FastAPI, HTTPException
import requests
import os
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# API Key
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

app = FastAPI()

DATABASE_URL = "postgresql://user:password@localhost/weather_db"
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
    response = requests.get(WEATHER_API_URL, params={
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    })
    
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="City not found")
    
    data = response.json()
    weather_info = {
        "city": city,
        "temperature": f"{data['main']['temp']}°C",
        "condition": data['weather'][0]['description'],
        "humidity": f"{data['main']['humidity']}%",
        "wind_speed": f"{data['wind']['speed']} m/s"
    }
    
    db = SessionLocal()
    weather_entry = WeatherEntry(**weather_info)
    db.add(weather_entry)
    db.commit()
    db.close()
    
    return weather_info
