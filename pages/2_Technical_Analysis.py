"""
Technical Analysis Page - WRDS Data Only
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_fetcher import get_kline_data, get_stock_info

st.set_page_config(page_title="Technical Analysis", page_icon="📉")

st.title("📉 Technical Analysis")

st.markdown("""
Technical analysis uses historical price and volume data to predict future stock price movements.
This tool provides common technical indicator analysis.

**Data Source**: WRDS CRSP Historical Data
""")

st.divider()

# Input
col1, col2 = st.columns(2)

default_tickers = ["AAPL", "MSFT", "JNJ", "XOM", "JPM", "WMT", "PG", "KO"]

with col1:
    ticker = st.selectbox("Ticker", default_tickers, index=0)

with col2:
    indicator = st.selectbox(
        "Select Indicator",
        ["Candlestick + MA", "MACD", "RSI", "Bollinger Bands", "All Indicators"]
    )

# Display stock info
stock_info = get_stock_info(ticker)
if stock_info.get('success'):
    st.info(f"📌 {ticker} - {stock_info.get('name', 'N/A')}")

st.divider()

if st.button("📊 Get Analysis", type="primary"):
    with st.spinner("Fetching data..."):
        df = get_kline_data(ticker, days=365)

        if not df.empty:
            # Calculate technical indicators
            close = df['close'].astype(float)

            # Moving Averages
            df['MA5'] = close.rolling(5).mean()
            df['MA10'] = close.rolling(10).mean()
            df['MA20'] = close.rolling(20).mean()
            df['MA60'] = close.rolling(60).mean()

            # MACD
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            df['MACD'] = ema12 - ema26
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['Histogram'] = df['MACD'] - df['Signal']

            # RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Bollinger Bands
            df['BB_Middle'] = close.rolling(20).mean()
            df['BB_Upper'] = df['BB_Middle'] + 2 * close.rolling(20).std()
            df['BB_Lower'] = df['BB_Middle'] - 2 * close.rolling(20).std()

            # Candlestick Chart
            if indicator in ["Candlestick + MA", "All Indicators"]:
                st.subheader(f"📈 {ticker} Candlestick Chart")

                fig = go.Figure()

                fig.add_trace(go.Candlestick(
                    x=df['date'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='Candlestick'
                ))

                fig.add_trace(go.Scatter(x=df['date'], y=df['MA5'], name='MA5', line=dict(color='yellow', width=1)))
                fig.add_trace(go.Scatter(x=df['date'], y=df['MA10'], name='MA10', line=dict(color='orange', width=1)))
                fig.add_trace(go.Scatter(x=df['date'], y=df['MA20'], name='MA20', line=dict(color='blue', width=1)))

                fig.update_layout(
                    title=f'{ticker} Candlestick with Moving Averages',
                    xaxis_title='Date',
                    yaxis_title='Price ($)',
                    height=500,
                    xaxis_rangeslider_visible=False
                )

                st.plotly_chart(fig, width='stretch')

            # MACD
            if indicator in ["MACD", "All Indicators"]:
                st.subheader("MACD")

                fig_macd = go.Figure()
                fig_macd.add_trace(go.Bar(x=df['date'], y=df['Histogram'], name='Histogram', marker_color='gray'))
                fig_macd.add_trace(go.Scatter(x=df['date'], y=df['MACD'], name='MACD', line=dict(color='blue')))
                fig_macd.add_trace(go.Scatter(x=df['date'], y=df['Signal'], name='Signal', line=dict(color='orange')))
                fig_macd.update_layout(height=300, title="MACD Indicator")
                st.plotly_chart(fig_macd, width='stretch')

            # RSI
            if indicator in ["RSI", "All Indicators"]:
                st.subheader("RSI (Relative Strength Index)")

                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(x=df['date'], y=df['RSI'], name='RSI', line=dict(color='purple')))
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
                fig_rsi.update_layout(height=300, yaxis=dict(range=[0, 100]), title="RSI Indicator")
                st.plotly_chart(fig_rsi, width='stretch')

            # Bollinger Bands
            if indicator in ["Bollinger Bands", "All Indicators"]:
                st.subheader("Bollinger Bands")

                fig_bb = go.Figure()
                fig_bb.add_trace(go.Scatter(x=df['date'], y=df['BB_Upper'], name='Upper Band', line=dict(color='red')))
                fig_bb.add_trace(go.Scatter(x=df['date'], y=df['BB_Middle'], name='Middle Band', line=dict(color='blue')))
                fig_bb.add_trace(go.Scatter(x=df['date'], y=df['BB_Lower'], name='Lower Band', line=dict(color='green')))
                fig_bb.add_trace(go.Scatter(x=df['date'], y=close, name='Close Price', line=dict(color='black')))
                fig_bb.update_layout(height=400, title="Bollinger Bands")
                st.plotly_chart(fig_bb, width='stretch')

            st.success(f"✅ Data fetched successfully, {len(df)} days of records")

        else:
            st.error("Unable to fetch data, please check ticker symbol")

st.sidebar.markdown("""
### Technical Indicators Guide
| Indicator | Description |
|-----------|-------------|
| MA | Moving Average |
| MACD | Trend Following Indicator |
| RSI | Overbought/Oversold Indicator |
| BOLL | Price Volatility Range |
""")
