import streamlit as st
import pandas as pd
import requests
from urllib.parse import urlencode

def suggest_addresses(query):
    """Suggest addresses using Nominatim API."""
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "json", "addressdetails": 1, "limit": 5},
    )
    if response.status_code == 200 and response.json():
        return [result['display_name'] for result in response.json()]
    else:
        return []

def geocode_address(address):
    """Geocode an address using Nominatim API and handle errors."""
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": address, "format": "json", "addressdetails": 1, "limit": 1},
    )
    if response.status_code == 200 and response.json():
        return response.json()  # Return the first result
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

    for index, address in enumerate(addresses):
        results = geocode_address(address)
        if results:
            # Use the first result for the address
            location = results[0]
            coordinates.append(f"{location['lon']},{location['lat']}")
            corrected_addresses.append(location['display_name'])
        else:
            return index  # Return index of the failing address

    # Construct the OSRM request URL
    coordinates_str = ";".join(coordinates)
    osrm_url = f"{base_url}{coordinates_str}?source=first&destination=last&roundtrip=false"

    response = requests.get(osrm_url)
    if response.status_code == 200:
        data = response.json()
        waypoints = data.get("waypoints", [])
        ordered_addresses = [corrected_addresses[wp["waypoint_index"]] for wp in waypoints]
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

            adresse_input = st.text_input("Adresse", key="adresse_input")
            suggestions = suggest_addresses(st.session_state.get("adresse_input", ""))

            if suggestions:
                selected_address = st.selectbox("Suggestions d'adresses", suggestions)
            else:
                selected_address = None

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

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Plannifier la tournée"):
                result = get_optimized_route_osrm(st.session_state["patients"])
                if isinstance(result, list):
                    st.success("Tournée optimisée ! Voici l'ordre des adresses :")
                    for i, address in enumerate(result):
                        st.write(f"{i+1}. {address}")

                        # Generate Waze link
                        waze_url = f"https://www.waze.com/ul?{urlencode({'q': address})}"
                        st.markdown(f"[Ouvrir dans Waze]({waze_url})")
                elif isinstance(result, int):
                    st.warning(f"Erreur de géolocalisation pour l'adresse : {st.session_state['patients'][result]['Adresse']}")

                    # Allow user to edit or delete
                    edit_address = st.text_input("Modifier l'adresse", value=st.session_state['patients'][result]['Adresse'], key=f"edit_{result}")
                    update_button = st.button("Mettre à jour", key=f"update_{result}")
                    delete_button = st.button("Supprimer ce patient", key=f"delete_{result}")

                    if update_button:
                        st.session_state['patients'][result]['Adresse'] = edit_address
                        st.experimental_rerun()

                    if delete_button:
                        del st.session_state['patients'][result]
                        st.experimental_rerun()
                else:
                    st.error(result)

        with col2:
            if st.button("Réinitialiser la liste"):
                st.session_state["patients"] = []
                st.success("Liste des patients réinitialisée avec succès !")

    else:
        st.write("Aucun patient ajouté pour le moment.")

if __name__ == "__main__":
    main()
