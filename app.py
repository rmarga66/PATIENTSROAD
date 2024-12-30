import streamlit as st
import pandas as pd
import requests
from urllib.parse import urlencode

def optimize_route_openrouteservice(patients):
    """Optimize the route using OpenRouteService API."""
    API_KEY = "YOUR_OPENROUTESERVICE_API_KEY"  # Replace with your OpenRouteService API key
    base_url = "https://api.openrouteservice.org/v2/matrix/driving-car"

    # Collect addresses and geocode them
    locations = []
    for patient in patients:
        address = f"{patient['Adresse']}, {patient['Code Postal']}, {patient['Ville']}"
        geocode_url = "https://nominatim.openstreetmap.org/search"
        response = requests.get(
            geocode_url, params={"q": address, "format": "json", "limit": 1}
        )
        if response.status_code == 200 and response.json():
            result = response.json()[0]
            lon, lat = float(result["lon"]), float(result["lat"])
            locations.append([lon, lat])
        else:
            return f"Erreur de géolocalisation pour l'adresse : {address}"

    if len(locations) < 2:
        return "Veuillez entrer au moins deux adresses valides pour optimiser."

    # Make the OpenRouteService API request
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "locations": locations,
        "metrics": ["duration", "distance"],
        "units": "km",
    }
    response = requests.post(base_url, json=body, headers=headers)
    if response.status_code == 200:
        data = response.json()
        distances = data.get("distances", [])
        durations = data.get("durations", [])
        return locations, distances, durations
    else:
        return "Erreur lors de la récupération des données OpenRouteService."

# Streamlit UI
def main():
    st.title("Plannificateur de Tournée")

    # Session state to store patients
    if "patients" not in st.session_state:
        st.session_state["patients"] = []

    with st.sidebar:
        st.header("Ajouter un patient")
        with st.form("add_patient_form", clear_on_submit=True):
            nom = st.text_input("Nom")
            prenom = st.text_input("Prénom")
            telephone = st.text_input("Numéro de téléphone")
            adresse = st.text_input("Adresse (Rue et numéro)")
            code_postal = st.text_input("Code Postal")
            ville = st.text_input("Ville")

            ajouter = st.form_submit_button("Ajouter")

            if ajouter:
                if nom and prenom and telephone and adresse and code_postal and ville:
                    st.session_state["patients"].append({
                        "Nom": nom,
                        "Prénom": prenom,
                        "Téléphone": telephone,
                        "Adresse": adresse,
                        "Code Postal": code_postal,
                        "Ville": ville
                    })
                    st.success("Patient ajouté avec succès !")
                else:
                    st.error("Veuillez remplir tous les champs !")

    # Display added patients
    st.header("Liste des Patients")
    if st.session_state["patients"]:
        df_patients = pd.DataFrame(st.session_state["patients"])
        st.table(df_patients)

        if st.button("Plannifier la tournée"):
            result = optimize_route_openrouteservice(st.session_state["patients"])
            if isinstance(result, tuple):
                locations, distances, durations = result
                st.success("Tournée optimisée avec succès ! Voici les résultats :")
                st.write("**Distances (km)**")
                st.write(distances)
                st.write("**Durées (minutes)**")
                st.write(durations)
                for i, loc in enumerate(locations):
                    st.write(f"Adresse {i + 1}: {loc}")
            else:
                st.error(result)

        if st.button("Réinitialiser la liste"):
            st.session_state["patients"] = []
            st.success("Liste des patients réinitialisée avec succès !")

    else:
        st.write("Aucun patient ajouté pour le moment.")

if __name__ == "__main__":
    main()
