import streamlit as st
import pandas as pd
import requests
from urllib.parse import urlencode

def geocode_address(address):
    """Geocode an address using Nominatim API and handle errors."""
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": address, "format": "json", "addressdetails": 1, "limit": 3},
    )
    if response.status_code == 200 and response.json():
        return response.json()  # Return all potential results
    else:
        return None

def get_optimized_route_osrm(patients):
    """Get optimized route using OSRM API."""
    # Collect addresses
    addresses = [patient["Adresse"] for patient in patients]
    if len(addresses) < 2:
        return "Veuillez entrer au moins deux patients pour l'optimisation."

    # Base URL for OSRM public server
    base_url = "https://router.project-osrm.org/trip/v1/driving/"

    coordinates = []
    corrected_addresses = []

    for address in addresses:
        results = geocode_address(address)
        if results:
            # Use the first result for the address
            location = results[0]
            coordinates.append(f"{location['lon']},{location['lat']}")
            corrected_addresses.append(location['display_name'])
        else:
            return f"Erreur lors de la géolocalisation de l'adresse : {address}. Veuillez vérifier l'adresse."

    # Construct the OSRM request URL
    coordinates_str = ";".join(coordinates)
    osrm_url = f"{base_url}{coordinates_str}?source=first&destination=last&roundtrip=false"

    response = requests.get(osrm_url)
    if response.status_code == 200:
        data = response.json()
        waypoints
