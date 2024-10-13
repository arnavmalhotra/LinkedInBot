import streamlit as st
from linkedin_api import Linkedin
import requests
import pandas as pd
import io
import re

HUNTER_API_URL = "https://api.hunter.io/v2/email-finder"

# Helper Functions
def search_email_with_hunter(api_key, domain, first_name, last_name):
    params = {
        "api_key": api_key,
        "domain": domain,
        "first_name": first_name,
        "last_name": last_name,
    }
    response = requests.get(HUNTER_API_URL, params=params)
    if response.status_code == 200:
        data = response.json().get("data", {})
        return data.get("email"), data.get("score", 0)
    return None, None

def infer_domain(company_name):
    """Generate possible domain patterns from a company name."""
    clean_name = re.sub(r"[^a-zA-Z0-9]", "", company_name).lower()
    possible_domains = [
        f"{clean_name}.com", f"{clean_name}.ca", f"{clean_name}.org",
        f"{clean_name}.edu", f"{clean_name}.net", f"{clean_name}.co", "gmail.com"
    ]
    return possible_domains

def get_profile_details(api, urn_id):
    profile = api.get_profile(urn_id=urn_id)
    return {
        "name": f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip(),
        "headline": profile.get("headline", "N/A"),
        "location": profile.get("locationName", "N/A"),
        "company": profile.get("experience", [{}])[0].get("companyName", "N/A"),
        "email": profile.get("email", None)
    }

def export_data_to_csv(profiles):
    """Convert profile data to CSV using BytesIO."""
    csv_buffer = io.BytesIO()
    df = pd.DataFrame(profiles)
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_buffer.seek(0)
    return csv_buffer

# Initialize results variable to avoid scope errors
results = []

# Tabs Setup
tab1, tab2, tab3 = st.tabs(["How to Use", "Find People", "Search Results"])

with tab1:
    st.title("How to Use")
    st.markdown("""
    - Use the **Find People** tab to search for LinkedIn profiles.
    - Enter the **Hunter API Key** to enable email search.
    - Check the **Search Results** tab for profiles.
    - If no email is found, use the **Search with Hunter** option.
    - Use the **Export All Data** button to download all profiles as a CSV.
    """)

with tab2:
    st.title("Find People")

    username = st.text_input("LinkedIn Username")
    password = st.text_input("LinkedIn Password", type="password")
    hunter_api_key = st.text_input("Hunter API Key", type="password")
    keywords = st.text_input("Keywords (e.g., Software Engineer)")

    # Multi-select for Network Depth
    network_depth_options = st.multiselect(
        "Network Depth (Optional, select one or more)",
        ["1st", "2nd", "3+"],
        default=[]
    )

    # Map the user-friendly network depth to LinkedIn API values
    network_depth_map = {"1st": "F", "2nd": "S", "3+": "O"}
    selected_network_depths = [
        network_depth_map[depth] for depth in network_depth_options
    ] if network_depth_options else None  # Optional field

    limit = st.slider("Number of Results", 1, 200, 10)

    if st.button("Search"):
        try:
            api = Linkedin(username, password)
            search_params = {"keywords": keywords, "limit": limit}

            if selected_network_depths:
                search_params["network_depths"] = selected_network_depths

            results = api.search_people(**search_params)
            st.success("Search complete! Check the Search Results tab.")
        except Exception as e:
            st.error(f"Error: {e}")

with tab3:
    st.title("Search Results")

    if results:
        profiles_with_email = []
        profiles_without_email = []

        for person in results:
            urn_id = person["urn_id"]
            profile = get_profile_details(api, urn_id)

            if profile["email"]:
                profiles_with_email.append(profile)
            else:
                profiles_without_email.append(profile)

        # Display Profiles with Email
        st.subheader("Profiles with Email")
        for profile in profiles_with_email:
            with st.container():
                st.markdown(f"""
                <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px; border-radius:8px; background-color:#f9f9f9;">
                    <strong>Name:</strong> {profile['name']}<br>
                    <strong>Role:</strong> {profile['headline']}<br>
                    <strong>Location:</strong> {profile['location']}<br>
                    <strong>Company:</strong> {profile['company']}<br>
                    <strong>Email:</strong> <a href="mailto:{profile['email']}">{profile['email']}</a>
                </div>
                """, unsafe_allow_html=True)

        # Display Profiles without Email with Hunter Option
        st.subheader("Profiles without Email")
        for profile in profiles_without_email:
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"""
                <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px; border-radius:8px;">
                    <strong>Name:</strong> {profile['name']}<br>
                    <strong>Role:</strong> {profile['headline']}<br>
                    <strong>Location:</strong> {profile['location']}<br>
                    <strong>Company:</strong> {profile['company']}
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if hunter_api_key:
                    with st.expander(f"Search with Hunter - {profile['name']}"):
                        domains = infer_domain(profile["company"])
                        email_found = False
                        for domain in domains:
                            email, score = search_email_with_hunter(
                                hunter_api_key, domain, profile["name"].split()[0], profile["name"].split()[-1]
                            )
                            if email:
                                st.success(f"Found: {email} (Score: {score}%)")
                                profile["email"] = email
                                email_found = True
                                break
                        if not email_found:
                            st.warning("No email found via Hunter.")

        # Export All Data to CSV
        if profiles_with_email or profiles_without_email:
            all_profiles = profiles_with_email + profiles_without_email
            csv_buffer = export_data_to_csv(all_profiles)
            st.download_button(
                label="Export All Data to CSV",
                data=csv_buffer,
                file_name="linkedin_profiles.csv",
                mime="text/csv",
            )
    else:
        st.info("No search results found. Please perform a search first.")
