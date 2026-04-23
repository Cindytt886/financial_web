"""
Company Comparison Page - WRDS Data Only
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_fetcher import get_stock_info, get_free_cash_flow, get_kline_data, get_shares_outstanding

st.set_page_config(page_title="Company Comparison", page_icon="📊")

st.title("📊 Company Comparison Analysis")

st.markdown("""
Select multiple companies to compare historical financial data and quickly assess relative valuation.
""")

st.divider()

# Popular tickers
default_tickers = ["AAPL", "MSFT", "JNJ", "XOM", "JPM", "WMT", "PG", "KO"]

st.subheader("📝 Select Stocks")

tickers_input = st.multiselect(
    "Select stocks to compare",
    default_tickers,
    default=["AAPL", "MSFT", "JNJ"]
)

if st.button("🔍 Start Comparison", type="primary"):
    if len(tickers_input) < 2:
        st.warning("Please select at least 2 stocks for comparison")
    else:
        with st.spinner("Fetching data..."):
            results = []

            for ticker in tickers_input:
                # Get basic info
                info = get_stock_info(ticker)

                # Get recent price from kline
                kline = get_kline_data(ticker, days=30)
                current_price = kline['close'].iloc[-1] if not kline.empty else 0

                # Get shares outstanding
                shares = get_shares_outstanding(ticker)  # in millions

                # Get FCF
                fcf = get_free_cash_flow(ticker, years=5)
                avg_fcf = fcf['free_cash_flow'].mean() if not fcf.empty else 0

                # Calculate actual market cap (shares * price, shares is in millions)
                market_cap = shares * 1e6 * current_price if shares and current_price else 0

                if info.get('success'):
                    results.append({
                        'Ticker': ticker,
                        'Name': info.get('name', ''),
                        'Current Price': current_price,
                        'Shares (M)': shares,
                        'Avg FCF (M)': avg_fcf / 1e6 if avg_fcf else 0,
                        'Market Cap (B)': market_cap / 1e9 if market_cap else 0
                    })

            if results:
                df = pd.DataFrame(results)

                st.success(f"✅ Successfully fetched data for {len(results)} stocks")

                # Display table
                st.subheader("📈 Data Comparison")

                st.dataframe(
                    df.style.format({
                        'Current Price': '${:.2f}',
                        'Shares (M)': '{:.2f}M',
                        'Avg FCF (M)': '${:.2f}M',
                        'Market Cap (B)': '${:.2f}B'
                    }),
                    width='stretch'
                )

                # Price comparison chart
                st.subheader("📊 Price Comparison")

                fig = px.bar(
                    df,
                    x='Ticker',
                    y='Current Price',
                    color='Ticker',
                    title="Stock Price Comparison ($)",
                    text_auto='$:.2f'
                )
                st.plotly_chart(fig, width='stretch')

                # Market Cap comparison
                st.subheader("💵 Market Cap Comparison")

                fig3 = px.bar(
                    df,
                    x='Ticker',
                    y='Market Cap (B)',
                    color='Ticker',
                    title="Market Cap Comparison (Billion USD)",
                    text_auto='$:.1fB'
                )
                st.plotly_chart(fig3, width='stretch')

                # FCF comparison
                st.subheader("💰 Average Free Cash Flow Comparison")

                fig2 = px.bar(
                    df,
                    x='Ticker',
                    y='Avg FCF (M)',
                    color='Ticker',
                    title="Average FCF Comparison (Million USD)",
                    text_auto='$:.1fM'
                )
                st.plotly_chart(fig2, width='stretch')

            else:
                st.error("Unable to fetch stock data")

# Tips
st.divider()
st.info("💡 Preset Stocks: AAPL, MSFT, JNJ, XOM, JPM, WMT, PG, KO")

st.sidebar.markdown("""
### Data Source
- Price Data: CRSP Historical Data
- Financial Data: Compustat Database
""")
