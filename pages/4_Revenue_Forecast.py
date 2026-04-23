"""
Revenue Forecast Page - WRDS Data Only
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Revenue Forecast", page_icon="📈")

st.title("📈 Revenue Forecast")

st.markdown("""
Forecast future revenue growth based on historical revenue data using various methods.
**Data Source**: WRDS Compustat Financial Data
""")

st.divider()

# Input parameters
st.subheader("📝 Input Parameters")

col1, col2, col3 = st.columns(3)

default_tickers = ["AAPL", "MSFT", "JNJ", "XOM", "JPM", "WMT", "PG", "KO", "GE", "IBM"]

with col1:
    ticker = st.selectbox("Ticker", default_tickers, index=0)

with col2:
    forecast_years = st.slider("Forecast Years", 3, 10, 5)

with col3:
    base_growth = st.number_input("Base Growth Rate (%)", value=5.0, min_value=-10.0, max_value=30.0, step=0.5) / 100

st.divider()

# Display stock info
from utils.data_fetcher import get_stock_info
stock_info = get_stock_info(ticker)
if stock_info.get('success'):
    st.info(f"📌 {ticker} - {stock_info.get('name', 'N/A')}")

# Get revenue data
def get_revenue_data(ticker: str, years: int = 10) -> pd.DataFrame:
    """Fetch revenue data from WRDS"""
    from utils.data_fetcher import get_wrds_connection
    conn = get_wrds_connection()
    if not conn:
        return pd.DataFrame()

    ticker = ticker.upper()

    try:
        # Use DISTINCT to avoid duplicate rows and sort by year descending to get latest
        query = f"""
            SELECT DISTINCT ON (fyear)
                fyear as year,
                sale as revenue,
                cogs as cost_of_goods_sold,
                oibdp as operating_income,
                ebit,
                at as total_assets
            FROM comp.funda
            WHERE tic = '{ticker}'
            AND sale IS NOT NULL
            AND fyear >= EXTRACT(YEAR FROM CURRENT_DATE) - {years}
            ORDER BY fyear ASC, datadate DESC
        """
        df = conn.raw_sql(query, date_cols=[])
        if df is not None and len(df) > 0:
            return df
    except Exception as e:
        print(f"Revenue data error: {e}")

    return pd.DataFrame()

# Get historical revenue data
revenue_df = get_revenue_data(ticker, years=10)

if not revenue_df.empty:
    with st.expander("📊 Historical Revenue Data"):
        st.dataframe(revenue_df, width='stretch')

    # Calculate historical growth rate
    if len(revenue_df) > 1:
        revenue_df['growth_rate'] = revenue_df['revenue'].pct_change()

        # Historical average growth rate
        avg_growth = revenue_df['growth_rate'].iloc[1:].mean()
        median_growth = revenue_df['growth_rate'].iloc[1:].median()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Historical Avg Growth", f"{avg_growth*100:.1f}%")
        with col2:
            st.metric("Historical Median Growth", f"{median_growth*100:.1f}%")
        with col3:
            st.metric("Latest Revenue", f"${revenue_df['revenue'].iloc[-1]/1e3:.2f}B")

    st.divider()

    # Forecast button
    if st.button("🔮 Start Revenue Forecast", type="primary"):
        with st.spinner("Calculating forecast..."):
            last_revenue = revenue_df['revenue'].iloc[-1]  # in millions
            last_year = revenue_df['year'].iloc[-1]

            # Generate forecast data
            forecast_data = []
            for i in range(1, forecast_years + 1):
                # Declining growth rate (mean reversion)
                declining_growth = base_growth * (0.95 ** (i-1))
                forecast_revenue = last_revenue * (1 + declining_growth) ** i

                forecast_data.append({
                    'year': last_year + i,
                    'forecast_revenue': forecast_revenue,
                    'growth_rate': declining_growth
                })

            forecast_df = pd.DataFrame(forecast_data)

            # Merge historical and forecast
            historical = revenue_df[['year', 'revenue']].copy()
            historical['type'] = 'Historical'

            forecast_only = forecast_df[['year', 'forecast_revenue']].copy()
            forecast_only.columns = ['year', 'revenue']
            forecast_only['type'] = 'Forecast'

            combined = pd.concat([historical, forecast_only], ignore_index=True)

            # Display forecast table
            st.subheader("📊 Revenue Forecast Results")

            display_df = forecast_df.copy()
            display_df['forecast_revenue'] = display_df['forecast_revenue'] / 1e3  # Convert millions to billions
            display_df['growth_rate'] = display_df['growth_rate'] * 100
            display_df.columns = ['Year', 'Forecast Revenue (B)', 'Growth Rate (%)']

            st.dataframe(
                display_df.style.format({
                    'Forecast Revenue (B)': '${:.2f}B',
                    'Growth Rate (%)': '{:.1f}%'
                }),
                width='stretch'
            )

            # Visualization
            st.subheader("📈 Revenue Trend Forecast")

            fig = go.Figure()

            # Historical data
            fig.add_trace(go.Scatter(
                x=revenue_df['year'],
                y=revenue_df['revenue'] / 1e3,  # Convert millions to billions
                mode='lines+markers',
                name='Historical Revenue',
                line=dict(color='#3498db', width=3)
            ))

            # Forecast data
            fig.add_trace(go.Scatter(
                x=forecast_df['year'],
                y=forecast_df['forecast_revenue'] / 1e3,  # Convert millions to billions
                mode='lines+markers',
                name='Forecast Revenue',
                line=dict(color='#e74c3c', width=3, dash='dash')
            ))

            # Connect historical and forecast
            fig.add_trace(go.Scatter(
                x=[revenue_df['year'].iloc[-1], forecast_df['year'].iloc[0]],
                y=[revenue_df['revenue'].iloc[-1]/1e3, forecast_df['forecast_revenue'].iloc[0]/1e3],
                mode='lines',
                showlegend=False,
                line=dict(color='#e74c3c', width=2, dash='dot')
            ))

            fig.update_layout(
                title=f'{ticker} Revenue Forecast (Billion USD)',
                xaxis_title='Year',
                yaxis_title='Revenue (Billion USD)',
                height=450,
                hovermode='x unified'
            )

            st.plotly_chart(fig, width='stretch')

            # Sensitivity analysis
            st.divider()
            st.subheader("🎯 Sensitivity Analysis")

            st.markdown("Revenue forecast under different growth rate assumptions:")

            growth_rates = [base_growth - 0.02, base_growth, base_growth + 0.02]
            sensitivity_data = []

            for gr in growth_rates:
                row = {'Assumed Growth': f"{gr*100:.1f}%"}
                for i in range(1, forecast_years + 1):
                    declining_growth = gr * (0.95 ** (i-1))
                    forecast_revenue = last_revenue * (1 + declining_growth) ** i
                    row[f'Year {i}'] = forecast_revenue / 1e3  # Convert millions to billions
                sensitivity_data.append(row)

            sensitivity_df = pd.DataFrame(sensitivity_data)

            st.dataframe(
                sensitivity_df.style.format({
                    **{f'Year {i}': '${:.2f}B' for i in range(1, forecast_years + 1)}
                }),
                width='stretch'
            )

            st.info("💡 Note: Revenue forecasts are based on historical growth and assumed rates, actual results may vary")

else:
    st.warning("No revenue data available")

# Explanation
st.divider()
with st.expander("📖 Revenue Forecast Method Guide"):
    st.markdown("""
    ### Forecast Methods

    1. **Growth Rate Method**: Forecast future revenue based on historical average growth rate
    2. **Mean Reversion**: Assume growth rate gradually returns to reasonable levels over time
    3. **Sensitivity Analysis**: Show result ranges under different growth rate assumptions

    ### Data Source

    - **Revenue (sale)**: Sales revenue field from Compustat database
    - Historical data: Last 10 years

    ### Notes

    - Forecasts are for reference only and do not constitute investment advice
    - Actual revenue may be affected by many factors
    """)

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
