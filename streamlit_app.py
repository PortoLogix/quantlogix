import streamlit as st

# Basic page config
st.set_page_config(
    page_title="QuantLogix",
    page_icon="📈"
)

# Main content
st.title("QuantLogix Dashboard")
st.write("Welcome to the QuantLogix Trading Dashboard!")

# Simple metric
st.metric(
    label="Sample Portfolio Value",
    value="$10,000",
    delta="5%"
)

# Basic text input
symbol = st.text_input("Enter a stock symbol:", value="AAPL")
st.write(f"You entered: {symbol}")

# Add a simple note
st.info("This is a test deployment of the dashboard.")
