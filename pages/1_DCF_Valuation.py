"""
DCF Valuation Page - WRDS Data Only
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_fetcher import get_stock_info, get_free_cash_flow, calculate_dcf, sensitivity_analysis

st.set_page_config(page_title="DCF Valuation", page_icon="💰")

st.title("💰 DCF Valuation")

st.markdown("""
DCF (Discounted Cash Flow) valuation is a method to calculate a company's intrinsic value
by forecasting future free cash flows and discounting them to present value.

**Data Source**: WRDS Compustat Financial Data
""")

st.divider()

# Input parameters
st.subheader("📝 Input Parameters")

col1, col2, col3, col4 = st.columns(4)

# Popular tickers
default_tickers = ["AAPL", "MSFT", "JNJ", "XOM", "JPM", "WMT", "PG", "KO", "GE", "IBM"]

with col1:
    ticker = st.selectbox("Ticker", default_tickers, index=0)

with col2:
    wacc = st.number_input("WACC (%)", value=10.0, min_value=5.0, max_value=20.0, step=0.5) / 100

with col3:
    perpetual_growth = st.number_input("Perpetual Growth (%)", value=2.5, min_value=1.0, max_value=5.0, step=0.5) / 100

with col4:
    forecast_years = st.slider("Forecast Years", 3, 10, 5)

with st.expander("⚙️ Advanced Parameters"):
    earnings_growth = st.number_input("Earnings Growth (%)", value=5.0, min_value=0.0, max_value=30.0, step=0.5) / 100

st.divider()

# Display stock info
stock_info = get_stock_info(ticker)
if stock_info.get('success'):
    st.info(f"📌 {ticker} - {stock_info.get('name', 'N/A')}")

# Display historical FCF
fcf_data = get_free_cash_flow(ticker, years=5)
if not fcf_data.empty:
    with st.expander("📊 Historical Free Cash Flow Data"):
        st.dataframe(fcf_data, width='stretch')

st.divider()

# Calculate button
if st.button("🚀 Run DCF Valuation", type="primary"):
    with st.spinner("Calculating DCF valuation..."):
        result = calculate_dcf(
            ticker=ticker,
            wacc=wacc,
            perpetual_growth=perpetual_growth,
            forecast_years=forecast_years,
            earnings_growth=earnings_growth
        )

        if result.get('success'):
            st.success(f"✅ {ticker} DCF Valuation Complete")

            # Key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "DCF Price",
                    f"${result['share_price']:.2f}",
                    delta=f"Current: ${result.get('current_price', 0):.2f}"
                )

            with col2:
                upside = result.get('upside', 0)
                st.metric("Upside", f"{upside:.1f}%", delta_color="normal")

            with col3:
                ev = result.get('enterprise_value', 0)
                st.metric("Enterprise Value", f"${ev/1e3:.2f}B")

            with col4:
                eq = result.get('equity_value', 0)
                st.metric("Equity Value", f"${eq/1e3:.2f}B")

            st.divider()

            # Cash flow forecast table
            st.subheader("📊 Cash Flow Forecast")

            unit = "Billion USD"
            div = 1e3

            forecast_df = pd.DataFrame({
                'Year': [f'Year {i}' for i in range(1, forecast_years + 1)],
                f'Forecast FCF ({unit})': [f/div for f in result['forecast_fcf']],
                f'Discounted FCF ({unit})': [f/div for f in result['discounted_fcf']]
            })

            st.dataframe(forecast_df.style.format({f'Forecast FCF ({unit})': '${:.2f}', f'Discounted FCF ({unit})': '${:.2f}'}), width='stretch')

            # Visualization
            st.subheader("📈 Cash Flow Visualization")

            fig = go.Figure()

            fig.add_trace(go.Bar(
                name='Forecast FCF',
                x=[f'Year {i}' for i in range(1, forecast_years + 1)],
                y=[f/div for f in result['forecast_fcf']],
                marker_color='#3498db'
            ))

            fig.add_trace(go.Bar(
                name='Discounted FCF',
                x=[f'Year {i}' for i in range(1, forecast_years + 1)],
                y=[f/div for f in result['discounted_fcf']],
                marker_color='#2ecc71'
            ))

            fig.update_layout(
                title='Future Cash Flow Forecast vs Discounted',
                xaxis_title='Year',
                yaxis_title=f'Amount ({unit})',
                barmode='group',
                height=400
            )

            st.plotly_chart(fig, width='stretch')

            # Sensitivity analysis
            st.divider()
            st.subheader("🎯 Sensitivity Analysis")

            st.markdown("Impact of WACC vs Perpetual Growth Rate on Valuation:")

            sensitivity_df = sensitivity_analysis(result)

            st.dataframe(
                sensitivity_df.style.format('${:.2f}', subset=sensitivity_df.columns[1:]).background_gradient(cmap='RdYlGn'),
                width='stretch'
            )

            st.info("💡 Note: Rows represent WACC, columns represent perpetual growth rate, values are DCF estimated share price")

        else:
            st.error(f"Calculation failed: {result.get('error', 'Unknown error')}")

# Explanation
st.divider()
with st.expander("📖 DCF Valuation Guide"):
    st.markdown("""
    ### Data Source
    - **Free Cash Flow**: From WRDS Compustat database
    - **Formula**: FCF = Operating Cash Flow - Capital Expenditure

    ### Parameter Description
    - **WACC**: Weighted Average Cost of Capital (8-12%)
    - **Perpetual Growth Rate**: Long-term growth rate (2-3%)
    - **Forecast Years**: Typically 5-10 years

    ### Interpretation
    - Upside > 0: Stock may be undervalued
    - Upside < 0: Stock may be overvalued
    """)

# Sidebar stock list
st.sidebar.markdown("""
### Popular Stocks
| Ticker | Name |
|--------|------|
| AAPL | Apple |
| MSFT | Microsoft |
| JNJ | Johnson & Johnson |
| XOM | Exxon Mobil |
| JPM | JPMorgan Chase |
| WMT | Walmart |
| PG | Procter & Gamble |
| KO | Coca-Cola |
""")
