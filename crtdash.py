import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
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
st.set_page_config(page_title="Online Analytics Dashboard", layout="wide")
st.markdown(
    """
    <style>
    body {
        background-color: #141414;  /* Dark background like Netflix */
        color: white;  /* White text for contrast */
    }
    h1, h2, h3, h4, h5, h6 {
        color: #E50914;  /* Netflix red color */
    }
    .streamlit-expanderHeader {
        color: #E50914;
    }
    .st-bb {
        color: #E50914;
    }
    .stButton>button {
        background-color: #E50914; /* Netflix red button */
        color: white;
    }
    .stButton>button:hover {
        background-color: #b20710; /* Darker red on hover */
    }
    .stTextInput input {
        background-color: #333;  /* Dark background for input fields */
        color: white;
    }
    .stTextInput label {
        color: white;
    }
    .stSlider>div>div>div>div {
        background-color: #333;  /* Dark slider background */
    }
    .stSelectbox>div>div>div {
        background-color: #333;  /* Dark background for select boxes */
        color: white;
    }
    .stLineChart path {
        stroke: #E50914;  /* Red line color for charts */
    }
    </style>
    """, unsafe_allow_html=True)

st.title("Online Analytics Dashboard")

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

        # Display key performance indicators
        st.subheader("Key Performance Indicators")
        if not df.empty:
            total_items = df.shape[0]
            total_price = df['field1'].sum()
            max_price = df['field1'].max()
            min_price = df['field1'].min()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Items", total_items)
            col2.metric("Sum of Product Total Price USD", total_price)
            col3.metric("Maximum Price USD", max_price)
            col4.metric("Minimum Price USD", min_price)
        else:
            st.warning("No data available.")

        # Display visualizations for each field
        st.subheader("Field Visualizations")
        if not df.empty:
            try:
                # Ensure the latest 10 values for the x-axis
                df = df.tail(10)  # Take the last 10 entries

                # Create a simulated x-axis with real-time intervals (every 1 hour for example)
                current_time = datetime.now()
                time_intervals = [current_time - pd.Timedelta(hours=i) for i in range(len(df))]
                df['real_time'] = time_intervals[::-1]

                fields = ['field1', 'field2', 'field3', 'field4', 'field5', 'field6']
                field_names = ['PM2.5 (µg/m³)', 'PM10 (µg/m³)', 'Ozone (ppb)', 'Humidity (%)', 'Temperature (°C)', 'CO (ppm)']

                # Create the layout with 6 graphs (2 rows, 3 columns)
                col1, col2, col3 = st.columns(3)
                for idx, (field, name) in enumerate(zip(fields[:3], field_names[:3])):
                    with col1 if idx == 0 else col2 if idx == 1 else col3:
                        st.write(f"**{name} Levels:**")
                        st.line_chart(data=df.set_index('real_time')[field], use_container_width=True, height=300)

                col1, col2, col3 = st.columns(3)
                for idx, (field, name) in enumerate(zip(fields[3:], field_names[3:])):
                    with col1 if idx == 0 else col2 if idx == 1 else col3:
                        st.write(f"**{name} Levels:**")
                        st.line_chart(data=df.set_index('real_time')[field], use_container_width=True, height=300)

            except Exception as e:
                st.error(f"Error displaying the graphs: {e}")
                st.write("Ensure 'created_at' exists and numeric fields contain valid data.")
        else:
            st.warning("No historical data available.")

        # Display the last updated time
        st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Pause for the refresh rate before updating the data
    time.sleep(refresh_rate)
