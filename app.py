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

            adresse_query = st.text_input("Adresse (commencez à taper)", key="adresse_query")
            suggestions = suggest_addresses(adresse_query)

            selected_address = st.selectbox("Suggestions d'adresses", suggestions, key="address_suggestions") if suggestions else None

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

        if st.button("Réinitialiser la liste"):
            st.session_state["patients"] = []
            st.success("Liste des patients réinitialisée avec succès !")

    else:
        st.write("Aucun patient ajouté pour le moment.")

if __name__ == "__main__":
    main()
