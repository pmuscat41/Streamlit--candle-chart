import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import ta

def fetch_stock_data(ticker, period, interval):
    end_date = datetime.now()
    if period == '1wk':
        start_date = end_date - timedelta(days=7)
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    else:
        data = yf.download(ticker, period=period, interval=interval)
    return data

def process_data(data):
    if data.index.tzinfo is None:
        data.index = data.index.tz_localize('UTC')
    data.index = data.index.tz_convert('US/Eastern')
    data.reset_index(inplace=True)
    return data

def add_technical_indicators(data):
    data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
    data['EMA_20'] = ta.trend.ema_indicator(data['Close'], window=20)
    return data

def calculate_metrics(data):
    last_close = data['Close'].iloc[-1]
    change = last_close - data['Open'].iloc[0]
    pct_change = (change / data['Open'].iloc[0]) * 100
    high = data['High'].max()
    low = data['Low'].min()
    volume = data['Volume'].sum()
    return last_close, change, pct_change, high, low, volume

# Sidebar
st.sidebar.header('Real-Time Stock Prices')
stock_symbols = ['AAPL', 'GOOGL', 'AMZN', 'MSFT', 'BTC-USD', 'ETH-USD']
for symbol in stock_symbols:
    real_time_data = fetch_stock_data(symbol, '1d', '1m')
    if not real_time_data.empty:
        real_time_data = process_data(real_time_data)
        last_price = real_time_data['Close'].iloc[-1].item()
        change = (last_price - real_time_data['Open'].iloc[0]).item()
        pct_change = ((change / real_time_data['Open'].iloc[0]) * 100).item()
        st.sidebar.metric(f"{symbol}", f"{last_price:.2f} USD", f"{change:.2f} ({pct_change:.2f}%)")
    else:
        st.sidebar.warning(f"No data available for {symbol}")

st.sidebar.subheader('About')
st.sidebar.info('This dashboard provides stock data and technical indicators for various time periods.')

ticker = st.sidebar.selectbox('Select Ticker', stock_symbols)
chart_type = st.sidebar.selectbox('Select Chart Type', ['Candlestick', 'Line'])
indicators = st.sidebar.multiselect('Select Technical Indicators', ['SMA 20', 'EMA 20'])

data = fetch_stock_data(ticker, '1y', '1d')
if data.empty:
    st.warning("No data available to display.")
else:
    data = process_data(data)
    data = add_technical_indicators(data)
    last_close, change, pct_change, high, low, volume = calculate_metrics(data)
    st.metric(label=f"{ticker} Last Price", value=f"{last_close:.2f} USD", delta=f"{change:.2f} ({pct_change:.2f}%)")
    col1, col2, col3 = st.columns(3)
    col1.metric("High", f"{high:.2f} USD")
    col2.metric("Low", f"{low:.2f} USD")
    col3.metric("Volume", f"{volume:,}")
    fig = go.Figure()
    if chart_type == 'Candlestick':
        fig.add_trace(go.Candlestick(x=data['Datetime'], open=data['Open'], high=data['High'], low=data['Low'], close=data['Close']))
    else:
        fig = px.line(data, x='Datetime', y='Close')
    for indicator in indicators:
        if indicator == 'SMA 20':
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data['SMA_20'], name='SMA 20'))
        elif indicator == 'EMA 20':
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data['EMA_20'], name='EMA 20'))
    st.plotly_chart(fig, use_container_width=True)