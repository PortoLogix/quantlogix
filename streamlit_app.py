import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import logging
import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "quantlogix2025":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Please enter the password", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Please enter the password", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="QuantLogix",
    page_icon="📈",
    layout="wide"
)

if check_password():
    # Main dashboard content
    st.title("QuantLogix Trading Dashboard")

    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize Alpaca API
        api_key = os.getenv("APCA_API_KEY_ID")
        api_secret = os.getenv("APCA_API_SECRET_KEY")
        base_url = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
        
        if not api_key or not api_secret:
            st.warning("API credentials not found. Running in demo mode.")
            demo_mode = True
        else:
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
                demo_mode = True

        # Sidebar for controls
        with st.sidebar:
            st.header("Trading Controls")
            
            if not demo_mode:
                # Add Liquidate All section
                st.subheader("🚨 Liquidate All Positions")
                liquidate_type = st.radio("Liquidation Type", ["Market", "Limit"], horizontal=True)
                
                if liquidate_type == "Limit":
                    col1, col2 = st.columns(2)
                    with col1:
                        price_type = st.radio("Price Type", ["Current", "Custom"], horizontal=True)
                    with col2:
                        price_offset = st.number_input("Price Offset (%)", 
                            value=-0.5, 
                            min_value=-10.0, 
                            max_value=10.0, 
                            step=0.1,
                            help="Percentage offset from current price. Negative for below market, positive for above market."
                        )
                
                if st.button("Liquidate All Positions", type="primary"):
                    try:
                        # Get all positions
                        positions = api.list_positions()
                        if not positions:
                            st.warning("No positions to liquidate")
                        else:
                            # Show positions that will be liquidated
                            st.write("Positions to liquidate:")
                            position_data = []
                            for position in positions:
                                current_price = float(position.current_price)
                                if liquidate_type == "Limit":
                                    if price_type == "Current":
                                        limit_price = current_price * (1 + price_offset/100)
                                    else:
                                        limit_price = st.number_input(
                                            f"Limit price for {position.symbol}",
                                            value=float(current_price),
                                            step=0.01,
                                            format="%.2f"
                                        )
                                position_data.append({
                                    "Symbol": position.symbol,
                                    "Quantity": position.qty,
                                    "Current Price": f"${float(position.current_price):.2f}",
                                    "Market Value": f"${float(position.market_value):.2f}",
                                    "Limit Price": f"${limit_price:.2f}" if liquidate_type == "Limit" else "Market"
                                })
                            
                            # Display positions in a table
                            st.table(pd.DataFrame(position_data))
                            
                            # Confirmation button
                            if st.button("⚠️ Confirm Liquidation"):
                                for position in positions:
                                    side = 'sell' if float(position.qty) > 0 else 'buy'
                                    qty = abs(float(position.qty))
                                    
                                    if liquidate_type == "Market":
                                        api.submit_order(
                                            symbol=position.symbol,
                                            qty=qty,
                                            side=side,
                                            type='market',
                                            time_in_force='gtc'
                                        )
                                    else:
                                        if price_type == "Current":
                                            limit_price = float(position.current_price) * (1 + price_offset/100)
                                        else:
                                            limit_price = float(st.session_state.get(f"limit_price_{position.symbol}", position.current_price))
                                        
                                        api.submit_order(
                                            symbol=position.symbol,
                                            qty=qty,
                                            side=side,
                                            type='limit',
                                            time_in_force='gtc',
                                            limit_price=limit_price
                                        )
                                
                                st.success(f"Successfully submitted orders to liquidate {len(positions)} positions")
                    except Exception as e:
                        st.error(f"Error liquidating positions: {str(e)}")
                
                st.divider()  # Add a visual separator

        # Main content area
        if demo_mode:
            # Generate mock data
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
                'Symbol': ['AAPL', 'GOOGL', 'TSLA'],
                'Quantity': [100, 50, 200],
                'Entry Price': [150.25, 2800.50, 750.75],
                'Current Price': [155.50, 2850.25, 760.00],
                'P&L': [525.00, 2487.50, 1850.00]
            }
            positions_df = pd.DataFrame(positions_data)
            
        else:
            try:
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
            except Exception as e:
                st.error(f"Error fetching account data: {str(e)}")
                st.stop()

        # Display metrics
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

        # Transaction History
        if not demo_mode:
            st.subheader("Recent Transactions")
            try:
                # Get recent orders
                orders = api.list_orders(
                    status='all',
                    limit=10,
                    nested=True  # Include nested multi-leg orders
                )
                
                if orders:
                    orders_data = []
                    for order in orders:
                        orders_data.append({
                            'Symbol': order.symbol,
                            'Side': order.side.upper(),
                            'Type': order.type.upper(),
                            'Quantity': order.qty,
                            'Status': order.status.upper(),
                            'Filled At': order.filled_at if order.filled_at else 'N/A',
                            'Fill Price': f"${float(order.filled_avg_price):.2f}" if order.filled_avg_price else 'N/A'
                        })
                    st.dataframe(pd.DataFrame(orders_data), use_container_width=True)
                else:
                    st.info("No recent transactions")
            except Exception as e:
                st.warning(f"Could not load transaction history: {str(e)}")

    except Exception as e:
        st.error("An error occurred while running the dashboard:")
        st.code(str(e))
        logger.exception("Error in app:")
