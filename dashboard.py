import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Set page config
st.set_page_config(
    page_title="QuantLogix Dashboard",
    page_icon="📈",
    layout="wide"
)

# Main dashboard content
st.title("QuantLogix Trading Dashboard")

# Sidebar
st.sidebar.header("Settings")
timeframe = st.sidebar.selectbox(
    "Select Timeframe",
    ["1D", "1W", "1M", "3M", "6M", "1Y", "YTD"]
)

# Mock data for demonstration
@st.cache_data
def generate_mock_data():
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    portfolio_value = np.random.uniform(9000, 11000, size=100).cumsum()
    return pd.DataFrame({
        'Date': dates,
        'Portfolio Value': portfolio_value
    })

data = generate_mock_data()

# Main content area
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Portfolio Value",
        f"${data['Portfolio Value'].iloc[-1]:,.2f}",
        f"{((data['Portfolio Value'].iloc[-1] / data['Portfolio Value'].iloc[-2]) - 1) * 100:.2f}%"
    )

with col2:
    st.metric(
        "Daily P&L",
        f"${data['Portfolio Value'].iloc[-1] - data['Portfolio Value'].iloc[-2]:,.2f}",
        "4.5%"
    )

with col3:
    st.metric(
        "Active Positions",
        "5",
        "2 new"
    )

# Portfolio Performance Chart
st.subheader("Portfolio Performance")
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=data['Date'],
        y=data['Portfolio Value'],
        mode='lines',
        name='Portfolio Value',
        line=dict(color='#00ff00', width=2)
    )
)
fig.update_layout(
    template='plotly_dark',
    xaxis_title="Date",
    yaxis_title="Value ($)",
    height=400
)
st.plotly_chart(fig, use_container_width=True)

# Active Positions Table
st.subheader("Active Positions")
positions_data = {
    'Symbol': ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'AMZN'],
    'Quantity': [100, 50, 200, 150, 75],
    'Entry Price': [150.25, 2800.50, 750.75, 285.25, 3300.50],
    'Current Price': [155.50, 2850.25, 760.00, 290.75, 3350.25],
    'P&L': [525.00, 2487.50, 1850.00, 825.00, 3731.25]
}
positions_df = pd.DataFrame(positions_data)
positions_df['P&L %'] = ((positions_df['Current Price'] - positions_df['Entry Price']) / positions_df['Entry Price'] * 100).round(2)
st.dataframe(positions_df, use_container_width=True)
