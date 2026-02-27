from geopy.geocoders import Nominatim
import streamlit as st

# =====================================================
# CACHE GEOCODER (VERY IMPORTANT)
# =====================================================
@st.cache_resource
def get_geolocator():
    return Nominatim(user_agent="food_donation_app")


# =====================================================
# FUNCTION USED BY APP
# =====================================================
def geocode_address(address):
    """
    Convert address → latitude & longitude
    Used during signup & profile update
    """

    geolocator = get_geolocator()

    try:
        location = geolocator.geocode(address, timeout=10)

        if location:
            return location.latitude, location.longitude

    except Exception as e:
        print("Geocode error:", e)

    return None, None