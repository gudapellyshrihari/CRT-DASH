import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# Function to fetch data from the API
def fetch_data():
    url = f"https://api.thingspeak.com/channels/1596152/feeds.json?results=100&_={int(time.time())}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get('feeds'):
            return data
        else:
            st.error("No feeds available in the API response.")
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
                # Filter for the latest 10 values
                df_latest = df.tail(10)

                # Ensure x-axis uses time only
                df_latest['time'] = df_latest['created_at'].dt.strftime('%H:%M:%S')

                # Plot separate line charts for each field
                st.write("**PM2.5 Levels (field1):**")
                st.line_chart(data=df_latest.set_index('time')['field1'], use_container_width=True, height=300)

                st.write("**PM10 Levels (field2):**")
                st.line_chart(data=df_latest.set_index('time')['field2'], use_container_width=True, height=300)

                st.write("**Ozone Levels (field3):**")
                st.line_chart(data=df_latest.set_index('time')['field3'], use_container_width=True, height=300)

                st.write("**Humidity Levels (field4):**")
                st.line_chart(data=df_latest.set_index('time')['field4'], use_container_width=True, height=300)

                st.write("**Temperature Levels (field5):**")
                st.line_chart(data=df_latest.set_index('time')['field5'], use_container_width=True, height=300)

                st.write("**CO Levels (field6):**")
                st.line_chart(data=df_latest.set_index('time')['field6'], use_container_width=True, height=300)
            except Exception as e:
                st.error(f"Error displaying the graphs: {e}")
                st.write("Ensure 'created_at' exists and numeric fields contain valid data.")
        else:
            st.warning("No historical data available.")

        # Display the last updated time
        st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Pause for the refresh rate before updating the data
    time.sleep(refresh_rate)
