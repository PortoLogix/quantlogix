import streamlit as st
import hmac

# Must be the first Streamlit command
st.set_page_config(
    page_title="QuantLogix Dashboard",
    page_icon="📈",
    layout="wide"
)

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], "QuantLogix2025!"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # First run or password not correct
    if "password_correct" not in st.session_state:
        st.text_input(
            "Password", type="password", key="password",
            on_change=password_entered
        )
        st.write("Please enter the password to access the dashboard.")
        return False
    
    # Password correct
    elif st.session_state["password_correct"]:
        return True

# If password is correct, show the app
if check_password():
    import pandas as pd
    import plotly.graph_objects as go
    import alpaca_trade_api as tradeapi
    from datetime import datetime, timedelta
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Initialize Alpaca API using environment variables or secrets
    api_key = os.getenv("APCA_API_KEY_ID") or st.secrets.get("PAPER_API_KEY")
    api_secret = os.getenv("APCA_API_SECRET_KEY") or st.secrets.get("PAPER_API_SECRET")
    base_url = os.getenv("ALPACA_PAPER_URL") or st.secrets.get("PAPER_BASE_URL", "https://paper-api.alpaca.markets")

    try:
        api = tradeapi.REST(
            key_id=api_key,
            secret_key=api_secret,
            base_url=base_url
        )
    except Exception as e:
        st.error(f"Error connecting to Alpaca API: {str(e)}")
        st.stop()

    # Title
    st.title("QuantLogix Trading Dashboard")

    # Sidebar for controls
    with st.sidebar:
        st.header("Trading Controls")
        
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
        
        symbol = st.text_input("Symbol", value="AAPL")
        quantity = st.number_input("Quantity", min_value=1, value=100)
        order_type = st.selectbox("Order Type", ["Market", "Limit"])
        
        if order_type == "Limit":
            limit_price = st.number_input("Limit Price", min_value=0.01, value=100.00, format="%.2f")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Buy"):
                try:
                    if order_type == "Market":
                        api.submit_order(
                            symbol=symbol,
                            qty=quantity,
                            side='buy',
                            type='market',
                            time_in_force='gtc'
                        )
                        st.success(f"Bought {quantity} shares of {symbol}")
                    else:
                        api.submit_order(
                            symbol=symbol,
                            qty=quantity,
                            side='buy',
                            type='limit',
                            time_in_force='gtc',
                            limit_price=limit_price
                        )
                        st.success(f"Placed limit order to buy {quantity} shares of {symbol}")
                except Exception as e:
                    st.error(f"Error placing buy order: {str(e)}")
        
        with col2:
            if st.button("Sell"):
                try:
                    if order_type == "Market":
                        api.submit_order(
                            symbol=symbol,
                            qty=quantity,
                            side='sell',
                            type='market',
                            time_in_force='gtc'
                        )
                        st.success(f"Sold {quantity} shares of {symbol}")
                    else:
                        api.submit_order(
                            symbol=symbol,
                            qty=quantity,
                            side='sell',
                            type='limit',
                            time_in_force='gtc',
                            limit_price=limit_price
                        )
                        st.success(f"Placed limit order to sell {quantity} shares of {symbol}")
                except Exception as e:
                    st.error(f"Error placing sell order: {str(e)}")

    try:
        # Get account information
        account = api.get_account()
        portfolio_value = float(account.portfolio_value)
        cash = float(account.cash)
        
        # Get today's PnL using portfolio history
        end = datetime.now()
        start = end - timedelta(days=1)
        portfolio_hist = api.get_portfolio_history(
            date_start=start.strftime('%Y-%m-%d'),
            date_end=end.strftime('%Y-%m-%d'),
            timeframe='1D'
        )
        
        # Calculate daily P&L and return
        if portfolio_hist.timestamp and len(portfolio_hist.timestamp) > 0:
            today_pl = portfolio_hist.profit_loss[-1] if portfolio_hist.profit_loss else 0
            daily_return = portfolio_hist.profit_loss_pct[-1] if portfolio_hist.profit_loss_pct else 0
        else:
            today_pl = 0
            daily_return = 0
        
        # Main metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Portfolio Value",
                f"${portfolio_value:,.2f}",
                f"{daily_return:.2f}%" if daily_return != 0 else None
            )
        with col2:
            st.metric(
                "Daily P&L",
                f"${today_pl:,.2f}" if today_pl != 0 else "$0.00",
                f"{daily_return:.2f}%" if daily_return != 0 else None
            )
        with col3:
            st.metric(
                "Cash Available",
                f"${cash:,.2f}",
                f"{(cash/portfolio_value)*100:.2f}% of Portfolio" if portfolio_value > 0 else None
            )

        # Portfolio chart
        st.subheader("Portfolio Performance")
        end = datetime.now()
        start = end - timedelta(days=30)
        
        portfolio_hist = api.get_portfolio_history(
            date_start=start.strftime('%Y-%m-%d'),
            date_end=end.strftime('%Y-%m-%d'),
            timeframe='1D'
        )
        
        if portfolio_hist.timestamp and len(portfolio_hist.timestamp) > 0:
            df_hist = pd.DataFrame({
                'Date': pd.to_datetime(portfolio_hist.timestamp, unit='s'),
                'Equity': portfolio_hist.equity
            })
            
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df_hist['Date'],
                    y=df_hist['Equity'],
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
        else:
            st.info("No portfolio history data available")

        # Current positions
        st.subheader("Current Positions")
        positions = api.list_positions()
        if positions:
            positions_data = []
            for position in positions:
                current_price = float(position.current_price)
                avg_entry = float(position.avg_entry_price)
                market_value = float(position.market_value)
                cost_basis = float(position.cost_basis)
                unrealized_pl = market_value - cost_basis
                unrealized_plpc = (unrealized_pl / cost_basis) * 100 if cost_basis != 0 else 0
                
                positions_data.append({
                    'Symbol': position.symbol,
                    'Quantity': int(position.qty),
                    'Entry Price': f"${avg_entry:.2f}",
                    'Current Price': f"${current_price:.2f}",
                    'Market Value': f"${market_value:.2f}",
                    'Unrealized P&L': f"${unrealized_pl:.2f}",
                    'Return': f"{unrealized_plpc:.2f}%"
                })
            
            df_positions = pd.DataFrame(positions_data)
            st.dataframe(df_positions, use_container_width=True)
        else:
            st.info("No active positions")

        # Recent orders
        st.subheader("Recent Orders")
        orders = api.list_orders(
            status='all',
            limit=10,
            nested=True
        )
        
        if orders:
            orders_data = []
            for order in orders:
                orders_data.append({
                    'Time': pd.to_datetime(order.submitted_at).strftime('%Y-%m-%d %H:%M:%S'),
                    'Symbol': order.symbol,
                    'Side': order.side.upper(),
                    'Type': order.type,
                    'Quantity': order.qty,
                    'Status': order.status
                })
            
            df_orders = pd.DataFrame(orders_data)
            st.dataframe(df_orders, use_container_width=True)
        else:
            st.info("No recent orders")

    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        import traceback
        st.write("Debug: Full error traceback:")
        st.code(traceback.format_exc())
