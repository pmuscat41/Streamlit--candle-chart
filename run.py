import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import ta

##########################################################################################
## PART 1: Define Functions for Pulling, Processing, and Creating Technical Indicators ##
##########################################################################################

# Fetch stock data based on the ticker, period, and interval
def fetch_stock_data(ticker, period, interval):
    try:
        end_date = datetime.now()
        if period == '1wk':
            start_date = end_date - timedelta(days=7)
            data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        else:
            data = yf.download(ticker, period=period, interval=interval)

        # Validate fetched data
        if data.empty:
            raise ValueError("No data returned from yfinance.")
        return data
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

# Process data to ensure it is timezone-aware and has the correct format
def process_data(data):
    try:
        if data.index.tzinfo is None:
            data.index = data.index.tz_localize('UTC')
        data.index = data.index.tz_convert('US/Eastern')
        data.reset_index(inplace=True)
        data.rename(columns={'Date': 'Datetime'}, inplace=True)
        return data
    except Exception as e:
        st.error(f"Error processing data: {e}")
        return pd.DataFrame()

# Calculate basic metrics from the stock data
def calculate_metrics(data):
    try:
        last_close = float(data['Close'].iloc[-1])
        prev_close = float(data['Close'].iloc[0])
        change = last_close - prev_close
        pct_change = (change / prev_close) * 100
        high = float(data['High'].max())
        low = float(data['Low'].min())
        volume = float(data['Volume'].sum())
        return last_close, change, pct_change, high, low, volume
    except Exception as e:
        st.error(f"Error calculating metrics: {e}")
        return 0, 0, 0, 0, 0, 0

# Add simple moving average (SMA) and exponential moving average (EMA) indicators
def add_technical_indicators(data):
    try:
        if 'Close' not in data.columns or data['Close'].isna().all():
            raise ValueError("Invalid data: 'Close' column is missing or contains only NaN values.")

        # Fill missing values
        data['Close'].fillna(method='ffill', inplace=True)
        data['Close'].fillna(method='bfill', inplace=True)

        # Add technical indicators
        data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
        data['EMA_20'] = ta.trend.ema_indicator(data['Close'], window=20)
        return data
    except Exception as e:
        st.error(f"Error adding technical indicators: {e}")
        return data

###############################################
## PART 2: Creating the Dashboard App Layout ##
###############################################

# Set up Streamlit page layout
st.set_page_config(layout="wide")
st.title('Real Time Stock Dashboard')

# Sidebar for user input parameters
st.sidebar.header('Chart Parameters')
ticker = st.sidebar.text_input('Ticker', 'ADBE')
time_period = st.sidebar.selectbox('Time Period', ['1d', '1wk', '1mo', '1y', 'max'])
chart_type = st.sidebar.selectbox('Chart Type', ['Candlestick', 'Line'])
indicators = st.sidebar.multiselect('Technical Indicators', ['SMA 20', 'EMA 20'])

# Mapping of time periods to data intervals
interval_mapping = {
    '1d': '1m',
    '1wk': '30m',
    '1mo': '1d',
    '1y': '1wk',
    'max': '1wk'
}

# Update the dashboard based on user input
if st.sidebar.button('Update'):
    try:
        # Fetch and process data
        data = fetch_stock_data(ticker, time_period, interval_mapping[time_period])
        if data.empty:
            st.error(f"No data available for {ticker} in the selected time period.")
            st.stop()

        data = process_data(data)
        data = add_technical_indicators(data)

        # Calculate metrics
        last_close, change, pct_change, high, low, volume = calculate_metrics(data)

        # Display metrics
        st.metric(label=f"{ticker} Last Price", value=f"{last_close:.2f} USD", delta=f"{change:.2f} ({pct_change:.2f}%)")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("High", f"{high:.2f} USD")
        col2.metric("Low", f"{low:.2f} USD")
        col3.metric("Volume", f"{volume:,}")

        # Plot the stock price chart
        fig = go.Figure()
        if chart_type == 'Candlestick':
            fig.add_trace(go.Candlestick(x=data['Datetime'],
                                         open=data['Open'],
                                         high=data['High'],
                                         low=data['Low'],
                                         close=data['Close']))
        else:
            fig = px.line(data, x='Datetime', y='Close')

        # Add selected technical indicators to the chart
        for indicator in indicators:
            if indicator == 'SMA 20' and 'SMA_20' in data.columns:
                fig.add_trace(go.Scatter(x=data['Datetime'], y=data['SMA_20'], name='SMA 20'))
            elif indicator == 'EMA 20' and 'EMA_20' in data.columns:
                fig.add_trace(go.Scatter(x=data['Datetime'], y=data['EMA_20'], name='EMA 20'))

        # Format graph
        fig.update_layout(title=f'{ticker} {time_period.upper()} Chart',
                          xaxis_title='Time',
                          yaxis_title='Price (USD)',
                          height=600)
        st.plotly_chart(fig, use_container_width=True)

        # Display historical data and technical indicators
        st.subheader('Historical Data')
        st.dataframe(data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']])
        
        if 'SMA_20' in data.columns and 'EMA_20' in data.columns:
            st.subheader('Technical Indicators')
            st.dataframe(data[['Datetime', 'SMA_20', 'EMA_20']])
    except Exception
