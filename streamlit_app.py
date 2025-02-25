import streamlit as st
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="QuantLogix Dashboard",
    page_icon="📈",
    layout="wide"
)

# Main dashboard content
st.title("QuantLogix Trading Dashboard")

try:
    # Initialize in demo mode by default
    demo_mode = True
    
    try:
        import os
        from dotenv import load_dotenv
        # Try to load environment variables
        load_dotenv()
    except ImportError:
        st.warning("python-dotenv not installed. Running in demo mode.")
    
    try:
        import alpaca_trade_api as tradeapi
        # Initialize Alpaca API if credentials are available
        api_key = os.getenv("APCA_API_KEY_ID")
        api_secret = os.getenv("APCA_API_SECRET_KEY")
        base_url = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
        
        if api_key and api_secret:
            try:
                api = tradeapi.REST(
                    key_id=api_key,
                    secret_key=api_secret,
                    base_url=base_url
                )
                # Test API connection
                account = api.get_account()
                demo_mode = False
                st.sidebar.success("✅ Connected to Alpaca API")
            except Exception as e:
                st.warning(f"Could not connect to Alpaca API. Running in demo mode. Error: {str(e)}")
        else:
            st.info("No API credentials found. Running in demo mode.")
    except ImportError:
        st.warning("alpaca-trade-api not installed. Running in demo mode.")

    # Sidebar
    st.sidebar.header("Settings")
    timeframe = st.sidebar.selectbox(
        "Select Timeframe",
        ["1D", "1W", "1M", "3M", "6M", "1Y", "YTD"]
    )

    if demo_mode:
        # Mock data for demonstration
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        portfolio_value = np.random.uniform(9000, 11000, size=100).cumsum()
        data = pd.DataFrame({
            'Date': dates,
            'Portfolio Value': portfolio_value
        })
        
        portfolio_value = data['Portfolio Value'].iloc[-1]
        daily_change = data['Portfolio Value'].iloc[-1] - data['Portfolio Value'].iloc[-2]
        daily_change_pct = ((data['Portfolio Value'].iloc[-1] / data['Portfolio Value'].iloc[-2]) - 1) * 100
        
        positions_data = {
            'Symbol': ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'AMZN'],
            'Quantity': [100, 50, 200, 150, 75],
            'Entry Price': [150.25, 2800.50, 750.75, 285.25, 3300.50],
            'Current Price': [155.50, 2850.25, 760.00, 290.75, 3350.25],
            'P&L': [525.00, 2487.50, 1850.00, 825.00, 3731.25]
        }
        positions_df = pd.DataFrame(positions_data)
        
    else:
        # Get real data from Alpaca
        portfolio_value = float(account.portfolio_value)
        daily_change = float(account.portfolio_value) - float(account.last_equity)
        daily_change_pct = (daily_change / float(account.last_equity)) * 100 if float(account.last_equity) > 0 else 0
        
        # Get positions
        positions = api.list_positions()
        if positions:
            positions_data = []
            for position in positions:
                positions_data.append({
                    'Symbol': position.symbol,
                    'Quantity': int(position.qty),
                    'Entry Price': float(position.avg_entry_price),
                    'Current Price': float(position.current_price),
                    'P&L': float(position.unrealized_pl)
                })
            positions_df = pd.DataFrame(positions_data)
        else:
            positions_df = pd.DataFrame(columns=['Symbol', 'Quantity', 'Entry Price', 'Current Price', 'P&L'])

    # Main content area
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Portfolio Value",
            f"${portfolio_value:,.2f}",
            f"{daily_change_pct:.2f}%"
        )

    with col2:
        st.metric(
            "Daily P&L",
            f"${daily_change:,.2f}",
            None
        )

    with col3:
        st.metric(
            "Active Positions",
            str(len(positions_df)),
            None
        )

    # Portfolio Performance Chart
    st.subheader("Portfolio Performance")
    fig = go.Figure()
    
    if demo_mode:
        fig.add_trace(
            go.Scatter(
                x=data['Date'],
                y=data['Portfolio Value'],
                mode='lines',
                name='Portfolio Value',
                line=dict(color='#00ff00', width=2)
            )
        )
    else:
        try:
            # Get historical portfolio value
            end = datetime.now()
            start = end - timedelta(days=30)
            portfolio_history = api.get_portfolio_history(
                timeframe="1D",
                start=start.strftime('%Y-%m-%d'),
                end=end.strftime('%Y-%m-%d')
            )
            
            fig.add_trace(
                go.Scatter(
                    x=portfolio_history.timestamp,
                    y=portfolio_history.equity,
                    mode='lines',
                    name='Portfolio Value',
                    line=dict(color='#00ff00', width=2)
                )
            )
        except Exception as e:
            st.warning(f"Could not load portfolio history: {str(e)}")

    fig.update_layout(
        template='plotly_dark',
        xaxis_title="Date",
        yaxis_title="Value ($)",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    # Active Positions Table
    st.subheader("Active Positions")
    if len(positions_df) > 0:
        positions_df['P&L %'] = ((positions_df['Current Price'] - positions_df['Entry Price']) / positions_df['Entry Price'] * 100).round(2)
        st.dataframe(positions_df, use_container_width=True)
    else:
        st.info("No active positions")

    # Add liquidate button in sidebar if we have positions and are not in demo mode
    if not demo_mode and len(positions_df) > 0:
        if st.sidebar.button("🚨 Liquidate All"):
            confirm = st.sidebar.button("Confirm Liquidation")
            if confirm:
                try:
                    for _, position in positions_df.iterrows():
                        api.submit_order(
                            symbol=position['Symbol'],
                            qty=position['Quantity'],
                            side='sell',
                            type='market',
                            time_in_force='day'
                        )
                    st.sidebar.success("Liquidation orders submitted!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error submitting orders: {str(e)}")

except Exception as e:
    st.error("An error occurred while running the dashboard:")
    st.code(str(e))
    logger.exception("Error in app:")
