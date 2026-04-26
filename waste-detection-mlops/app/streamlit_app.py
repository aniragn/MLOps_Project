import streamlit as st, requests, folium
from streamlit_folium import st_folium
from datetime import datetime

API = "http://api:8000"

st.title("Waste Detection Dashboard")

# Model selector fed by API
models = [m["name"] for m in requests.get(f"{API}/models").json()]
model = st.selectbox("Select model", models)

# Upload + GPS
file = st.file_uploader("Upload image", type=["jpg","jpeg","png"])
lat = st.number_input("Latitude", value=48.8566)
lon = st.number_input("Longitude", value=2.3522)

if st.button("Detect") and file:
    r = requests.post(f"{API}/predict",
        data={"latitude": lat, "longitude": lon, "model_name": model},
        files={"file": file})
    if r.status_code == 200:
        d = r.json()
        st.success(f"Rubbish items: {d['rubbish']} | Confidence: {d['confiance']:.2f} | Model: {d['model_used']}")

# History map
history = requests.get(f"{API}/history").json()
m = folium.Map(location=[48.8566, 2.3522], zoom_start=5)

# Filters
sources = list({h["source"] for h in history})
sel_sources = st.multiselect("Filter by source", sources, default=sources)
sel_models = st.multiselect("Filter by model", models, default=models)

for h in history:
    if h["source"] not in sel_sources: continue
    if h["model_name"] not in sel_models: continue
    color = "orange" if h["source"] == "drone_patrol" else "red"
    folium.Marker(
        [h["latitude"], h["longitude"]],
        popup=f"{h['model_name']} — {h['confiance']:.2f}",
        icon=folium.Icon(color=color)
    ).add_to(m)

st_folium(m, width=700)