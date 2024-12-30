import streamlit as st
import pandas as pd
import requests
from urllib.parse import urlencode

def get_optimized_route_osrm(patients):
    """Get optimized route using OSRM API."""
    # Collect addresses
    addresses = [patient["Adresse"] for patient in patients]
    if len(addresses) < 2:
        return "Veuillez entrer au moins deux patients pour l'optimisation."

    # Base URL for OSRM public server
    base_url = "https://router.project-osrm.org/trip/v1/driving/"

    # Geocoding addresses using Nominatim API (OpenStreetMap)
    coordinates = []
    for address in addresses:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json"},
        )
        if response.status_code == 200 and response.json():
            location = response.json()[0]
            coordinates.append(f"{location['lon']},{location['lat']}")
        else:
            return f"Erreur lors de la géolocalisation de l'adresse : {address}"

    # Construct the OSRM request URL
    coordinates_str = ";".join(coordinates)
    osrm_url = f"{base_url}{coordinates_str}?source=first&destination=last&roundtrip=false"

    response = requests.get(osrm_url)
    if response.status_code == 200:
        data = response.json()
        ordered_waypoints = data.get("waypoints", [])
        ordered_addresses = [addresses[wp["waypoint_index"]] for wp in ordered_waypoints]
        return ordered_addresses
    else:
        return "Erreur lors de la récupération des données OSRM."

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
            adresse = st.text_input("Adresse")
            ajouter = st.form_submit_button("Ajouter")

            if ajouter:
                if nom and prenom and telephone and adresse:
                    st.session_state["patients"].append({
                        "Nom": nom,
                        "Prénom": prenom,
                        "Téléphone": telephone,
                        "Adresse": adresse
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
            optimized_route = get_optimized_route_osrm(st.session_state["patients"])
            if isinstance(optimized_route, list):
                st.success("Tournée optimisée ! Voici l'ordre des adresses :")
                for i, address in enumerate(optimized_route):
                    st.write(f"{i+1}. {address}")

                    # Generate Waze link
                    waze_url = f"https://www.waze.com/ul?{urlencode({'q': address})}"
                    st.markdown(f"[Ouvrir dans Waze]({waze_url})")
            else:
                st.error(optimized_route)
    else:
        st.write("Aucun patient ajouté pour le moment.")

if __name__ == "__main__":
    main()
