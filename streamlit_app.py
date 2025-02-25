import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px  # Using plotly express instead of graph_objects for simpler charts
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page config with minimal settings
st.set_page_config(
    page_title="QuantLogix",
    page_icon="📈",
    layout="wide"
)

# Initialize demo mode
demo_mode = True

try:
    # Main dashboard content
    st.title("QuantLogix Trading Dashboard")
    
    # Generate demo data
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    portfolio_value = np.random.uniform(9000, 11000, size=100).cumsum()
    data = pd.DataFrame({
        'Date': dates,
        'Portfolio Value': portfolio_value
    })
    
    # Display metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Portfolio Value",
            f"${data['Portfolio Value'].iloc[-1]:,.2f}",
            f"{((data['Portfolio Value'].iloc[-1] / data['Portfolio Value'].iloc[-2]) - 1) * 100:.2f}%"
        )
    
    with col2:
        st.metric(
            "Daily Change",
            f"${data['Portfolio Value'].iloc[-1] - data['Portfolio Value'].iloc[-2]:,.2f}",
            None
        )

    # Portfolio chart using plotly express
    st.subheader("Portfolio Performance")
    fig = px.line(
        data,
        x='Date',
        y='Portfolio Value',
        title='Portfolio Value Over Time'
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Sample positions
    st.subheader("Demo Positions")
    positions_data = {
        'Symbol': ['AAPL', 'GOOGL', 'TSLA'],
        'Quantity': [100, 50, 200],
        'Price': [150.25, 2800.50, 750.75],
        'Value': [15025.00, 140025.00, 150150.00]
    }
    st.dataframe(pd.DataFrame(positions_data), use_container_width=True)

    # Add a note about demo mode
    st.info("🚀 This is a demo version. Connect your Alpaca account to access live trading features.")

except Exception as e:
    st.error("An error occurred in the dashboard:")
    st.code(str(e))
    logger.exception("Dashboard error:")
