import streamlit as st
import pandas as pd
import requests
from urllib.parse import urlencode

def suggest_addresses(query):
    """Suggest addresses using Nominatim API."""
    if not query:
        return []
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "json", "addressdetails": 1, "limit": 5},
    )
    if response.status_code == 200 and response.json():
        return [result['display_name'] for result in response.json()]
    else:
        return []

def optimize_route_openrouteservice(patients):
    """Optimize the route using OpenRouteService API."""
    API_KEY = "5b3ce3597851110001cf62485eec9a40e7dd4df9a169b13343a6b343"  # Replace with your OpenRouteService API key
    base_url = "https://api.openrouteservice.org/v2/directions/driving-car"

    # Collect addresses and geocode them
    locations = []
    for patient in patients:
        address = patient['Adresse']
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

    # Construct the body for OpenRouteService API request
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "coordinates": locations,
        "geometry": True
    }
    response = requests.post(base_url, json=body, headers=headers)
    if response.status_code == 200:
        data = response.json()
        routes = data.get("routes", [])
        if routes:
            optimized_order = routes[0]["segments"]
            return optimized_order
        else:
            return "Aucun itinéraire trouvé."
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

            adresse_query = st.text_input("Adresse", key="adresse_query")
            suggestions = suggest_addresses(adresse_query)

            selected_address = st.selectbox("Suggestions d'adresses", suggestions) if suggestions else ""

            ajouter = st.form_submit_button("Ajouter")

            if ajouter:
                if nom and prenom and telephone and selected_address:
                    st.session_state["patients"].append({
                        "Nom": nom,
                        "Prénom": prenom,
                        "Téléphone": telephone,
                        "Adresse": selected_address
                    })
                    st.success("Patient ajouté avec succès !")
                else:
                    st.error("Veuillez remplir tous les champs et sélectionner une adresse valide !")

    # Display added patients
    st.header("Liste des Patients")
    if st.session_state["patients"]:
        df_patients = pd.DataFrame(st.session_state["patients"])
        st.table(df_patients)

        if st.button("Plannifier la tournée"):
            result = optimize_route_openrouteservice(st.session_state["patients"])
            if isinstance(result, str):
                st.error(result)
            else:
                st.success("Tournée optimisée avec succès ! Voici l'ordre des adresses optimisé :")
                for i, patient in enumerate(st.session_state["patients"]):
                    st.write(f"{i+1}. {patient['Nom']} {patient['Prénom']} - {patient['Adresse']}")

        if st.button("Réinitialiser la liste"):
            st.session_state["patients"] = []
            st.success("Liste des patients réinitialisée avec succès !")

    else:
        st.write("Aucun patient ajouté pour le moment.")

if __name__ == "__main__":
    main()
