import ssl
import certifi
import geopy.geocoders
from geopy.geocoders import Nominatim

ctx = ssl.create_default_context(cafile=certifi.where())
geopy.geocoders.options.default_ssl_context = ctx

import streamlit as st
import requests
from datetime import datetime
import pytz
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="🌍 Weather Dashboard", page_icon="🌦", layout="wide")

# ---------- Custom Styling ----------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(rgba(0, 0, 0, 0.35), rgba(0, 0, 0, 0.45)),
                url('https://images.unsplash.com/photo-1501973801540-537f08ccae7b?auto=format&fit=crop&w=1920&q=80');
    background-size: cover;
    background-position: center;
}
[data-testid="stSidebar"] {
    background: rgba(30, 41, 59, 0.85);
    backdrop-filter: blur(8px);
}
.city-card {
    background: rgba(30, 41, 59, 0.8);
    border-radius: 20px;
    padding: 20px;
    color: white;
    box-shadow: 0 6px 15px rgba(0,0,0,0.4);
    transition: 0.3s ease-in-out;
    margin-bottom: 20px;
}
.city-card:hover {
    transform: scale(1.03);
    box-shadow: 0 8px 20px rgba(0,0,0,0.6);
}
h1, h3, p, label {
    color: white !important;
    text-shadow: 1px 1px 3px rgba(0,0,0,0.7);
}
</style>
""", unsafe_allow_html=True)

# ---------- Title ----------
st.title("❄️🍂Clima Sphere🌞☔")
st.caption("Live weather updates, forecasts & trends — powered by Open-Meteo API")

# ---------- Language ----------
language = st.selectbox("🌐 Choose language:", ["English", "Spanish", "French", "German", "Hindi", "Chinese", "Arabic"])

# ---------- City Input ----------
cities_input = st.text_input("🏙 Enter city names:", "New York, London, Tokyo")
cities = [c.strip() for c in cities_input.split(",") if c.strip()]

geolocator = Nominatim(user_agent="weather_app")

# ---------- Helper ----------
def deg_to_compass(deg):
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ix = round(deg / 45) % 8
    return dirs[ix]

def weather_icon(code):
    icons = {
        0: "☀", 1: "🌤", 2: "⛅", 3: "☁",
        45: "🌫", 48: "🌫", 51: "🌦", 61: "🌧",
        71: "❄", 80: "🌧", 95: "⛈"
    }
    return icons.get(code, "🌍")

# ---------- Loop for Cities ----------
cards_per_row = 3

for i in range(0, len(cities), cards_per_row):
    row_cities = cities[i:i + cards_per_row]
    cols = st.columns(len(row_cities))

    for j, city in enumerate(row_cities):
        with cols[j]:
            st.markdown("<div class='city-card'>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center;'>📍 {city}</h3>", unsafe_allow_html=True)

            location = geolocator.geocode(city)
            if not location:
                st.error("❌ City not found.")
                continue

            lat, lon = location.latitude, location.longitude

            try:
                url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset&hourly=relative_humidity_2m&timezone=auto"
                data = requests.get(url).json()
            except Exception:
                st.error("⚠ Failed to fetch weather data.")
                continue

            weather = data.get("current_weather", {})
            weekly = data.get("daily", {})

            if weather:
                timezone = data.get("timezone", "UTC")
                local_time = datetime.now(pytz.timezone(timezone)).strftime("%I:%M %p")

                icon = weather_icon(weather.get("weathercode", 0))
                st.markdown(f"<h1 style='text-align:center;'>{icon}</h1>", unsafe_allow_html=True)
                st.metric("🌡 Temperature", f"{weather['temperature']} °C")
                st.metric("💨 Wind Speed", f"{weather['windspeed']} m/s")
                st.metric("🧭 Direction", f"{deg_to_compass(weather['winddirection'])}")
                st.metric("🕒 Local Time", local_time)

                # 🌅 Sunrise & Sunset
                sunrise = weekly["sunrise"][0].split("T")[1]
                sunset = weekly["sunset"][0].split("T")[1]
                st.write(f"🌅 *Sunrise:* {sunrise} | 🌇 *Sunset:* {sunset}")

                # 💧 Humidity (current hour)
                humidity = data["hourly"]["relative_humidity_2m"][0]
                st.metric("💧 Humidity", f"{humidity}%")

                # 🗺 Map
                st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))

                # 📊 Weekly Graph
                if "time" in weekly:
                    days = [datetime.strptime(d, "%Y-%m-%d").strftime("%d %b") for d in weekly["time"]]
                    temp_max = weekly["temperature_2m_max"]
                    temp_min = weekly["temperature_2m_min"]

                    plt.style.use("dark_background")
                    fig, ax = plt.subplots(figsize=(4, 2))
                  # adjust bar width and positions for grouped bars
                    x = range(len(days))
                    width = 0.35 #width of borders

                    ax.bar([i - width/2 for i in x], temp_max, width, color="#ef4444", label="Max Temp")
                    ax.bar([i + width/2 for i in x], temp_min, width, color="#3b82f6", label="Min Temp")

                    ax.set_xticks(x)
                    ax.set_xticklabels(days, rotation=45, ha="right", fontsize=7)

                    ax.set_title("📊 Weekly Temperature Histogram", fontsize=9)
                    ax.legend(fontsize=7)
                    ax.set_ylabel("Temperature (°C)", fontsize=8)

                    plt.tight_layout()
                    st.pyplot(fig) 
                    
                    # 📤 Download CSV
                    df = pd.DataFrame({"Day": days, "Max Temp (°C)": temp_max, "Min Temp (°C)": temp_min})
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Download Weekly Data", data=csv, file_name=f"{city}_weather.csv", mime="text/csv")

            st.markdown("</div>", unsafe_allow_html=True)
