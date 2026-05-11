# Exposure Manager

Quantitative financial dashboard for tracking market breadth, sector rotation, and seasonality.

## Features
- **Sentiment & Breadth:** % Stocks > SMA 20/50/200, Net New Highs/Lows, Volume Breadth, and a custom Fear/Greed Proxy Score.
- **Sector Rotation:** Tracking performance and SMA distance for 11 SPDR Sector ETFs to identify institutional capital flows.
- **Seasonality Hunter:** Historical win rate and average return analysis (Monthly/Weekly) for any ticker.

## Tech Stack
- Python 3.9+
- Streamlit
- Pandas & NumPy
- Plotly
- Yahoo Finance (yfinance)
- TradingView Scanner API (Direct POST)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/eliavra/trading-hints.git
   cd trading-hints
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## Architecture
- `data.py`: Data ingestion from Wikipedia, TradingView, and yfinance.
- `calculations.py`: Mathematical models, normalization, and statistical analysis.
- `app.py`: Streamlit dashboard and visualizations.
