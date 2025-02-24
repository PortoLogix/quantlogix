# QuantLogix Trading Dashboard

A real-time trading dashboard built with Streamlit and Alpaca API.

## Features

- Real-time portfolio metrics
- Trading controls (Market and Limit orders)
- Portfolio performance chart
- Current positions table
- Recent orders tracking

## Deployment Instructions

1. Fork this repository
2. Go to [Streamlit Cloud](https://share.streamlit.io)
3. Click "New app"
4. Select this repository and the `streamlit_app.py` file
5. Add the following secrets in your Streamlit Cloud dashboard:

```toml
# .streamlit/secrets.toml
PAPER_API_KEY = "your_alpaca_paper_api_key"
PAPER_API_SECRET = "your_alpaca_paper_api_secret"
PAPER_BASE_URL = "https://paper-api.alpaca.markets"
```

## Local Development

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.streamlit/secrets.toml` file with your Alpaca API credentials
4. Run the dashboard:
```bash
streamlit run streamlit_app.py
```

## Environment Variables

The dashboard can use either environment variables or Streamlit secrets for API credentials:

- `APCA_API_KEY_ID`: Your Alpaca API key
- `APCA_API_SECRET_KEY`: Your Alpaca API secret
- `ALPACA_PAPER_URL`: The Alpaca paper trading API URL
