import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# Function to fetch data from the API
def fetch_data():
    url = "https://api.thingspeak.com/channels/1596152/feeds.json?results=100"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch data. HTTP Status Code: {response.status_code}")
        return {}

# Function to process the fetched data
def process_data(data):
    feeds = data.get('feeds', [])
    if not feeds:
        st.error("No data available in feeds.")
        return pd.DataFrame()

    df = pd.DataFrame(feeds)

    # Debugging: Display raw data to inspect structure
    st.write("Raw API Data:", df)

    # Ensure 'created_at' column exists and is a proper timestamp
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        if df['created_at'].isnull().all():
            st.error("All 'created_at' values are invalid. Check the API response.")
            return pd.DataFrame()
    else:
        st.error("Error: 'created_at' column not found in the data.")
        return pd.DataFrame()

    # Convert numeric fields to float for visualization
    numeric_fields = ['field1', 'field2', 'field3', 'field4', 'field5', 'field6']
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors='coerce')
        else:
            st.warning(f"Field '{field}' is missing in the data.")

    # Drop rows where all numeric fields are NaN
    df = df.dropna(subset=numeric_fields, how='all')
    if df.empty:
        st.warning("All numeric fields are empty. No data to display.")

    return df

# Streamlit app
st.title("Real-Time Air Quality Dashboard")

# Sidebar settings
st.sidebar.header("Settings")
refresh_rate = st.sidebar.selectbox("Refresh Rate (seconds)", [5, 10, 30, 60])
st.sidebar.write(f"Current refresh rate: {refresh_rate} seconds")

# Main dashboard
placeholder = st.empty()

while True:
    with placeholder.container():
        # Fetch and process data
        data = fetch_data()
        df = process_data(data)

        # Display the latest readings
        st.subheader("Latest Readings")
        if not df.empty:
            latest_reading = df.iloc[-1]
            st.write(f"**PM2.5:** {latest_reading.get('field1', 'N/A')} µg/m³")
            st.write(f"**PM10:** {latest_reading.get('field2', 'N/A')} µg/m³")
            st.write(f"**Ozone:** {latest_reading.get('field3', 'N/A')} ppb")
            st.write(f"**Humidity:** {latest_reading.get('field4', 'N/A')} %")
            st.write(f"**Temperature:** {latest_reading.get('field5', 'N/A')} °C")
            st.write(f"**CO:** {latest_reading.get('field6', 'N/A')} ppm")
            st.write(f"**Timestamp:** {latest_reading.get('created_at', 'N/A')}")
        else:
            st.warning("No data available.")

        # Display historical data
        st.subheader("Historical Data")
        if not df.empty:
            try:
                # Ensure the DataFrame has valid data for the chart
                st.line_chart(
                    df[['created_at', 'field1', 'field2', 'field3', 'field4', 'field5', 'field6']]
                    .set_index('created_at')
                )
            except Exception as e:
                st.error(f"Error displaying the graph: {e}")
                st.write("Ensure 'created_at' exists and numeric fields contain valid data.")
        else:
            st.warning("No historical data available.")

        # Display the last updated time
        st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Pause for the refresh rate before updating the data
    time.sleep(refresh_rate)
