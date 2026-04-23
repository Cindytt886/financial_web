"""
Financial Modeling Web App - WRDS Data Source Only
"""
import streamlit as st
import pandas as pd
from utils.data_fetcher import get_stock_info, get_kline_data, get_free_cash_flow, calculate_dcf

# Page config
st.set_page_config(
    page_title="Home",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styles
st.markdown("""
<style>
    .main { background-color: #f5f5f5; }
    .stButton > button { background-color: #4CAF50; color: white; }
</style>
""", unsafe_allow_html=True)


def format_value(value: float) -> str:
    """Format numerical values"""
    if abs(value) >= 1e9:
        return f"${value/1e9:.2f}B"
    elif abs(value) >= 1e6:
        return f"${value/1e6:.2f}M"
    elif abs(value) >= 1e3:
        return f"${value/1e3:.2f}K"
    return f"${value:.2f}"


def main():
    # Sidebar
    with st.sidebar:
        st.title("📈 Financial Modeling Tool")
        st.divider()
        st.info("💡 Data Source: WRDS (Wharton)")
        st.info("💡 Based on Historical Data")
        st.divider()

        # Stock selection
        st.subheader("Select Stock")
        default_tickers = ["AAPL", "MSFT", "JNJ", "XOM", "JPM", "WMT", "PG", "KO"]
        ticker = st.selectbox("Ticker", default_tickers)
        st.session_state['ticker'] = ticker

        st.divider()
        st.markdown("""
        ### Navigation
        - 💰 DCF Valuation - Cash Flow Discounting
        - 📈 Revenue Forecast - Growth Projection
        - 📊 Company Comparison - Multi-company Analysis
        - 📉 Technical Analysis - K-line Research
        """)

    # Main page
    st.title("WRDS-Based Financial Modeling Tool")

    # Check WRDS connection
    from utils.data_fetcher import is_connected
    if not is_connected():
        st.error("❌ WRDS not connected. Please check network or VPN")
        return

    # Display stock info
    stock_info = get_stock_info(ticker)
    if stock_info.get('success'):
        st.success(f"✅ Loaded {ticker} - {stock_info.get('name', '')}")

    st.markdown("""
    ## Features Overview

    | Module | Function | Data Source |
    |--------|----------|-------------|
    | 💰 DCF Valuation | Discounted Cash Flow Model | Compustat (WRDS) |
    | 📈 Revenue Forecast | Revenue Growth Projection | Compustat (WRDS) |
    | 📊 Company Comparison | Multi-company Financials | Compustat (WRDS) |
    | 📉 Technical Analysis | Historical K-line Analysis | CRSP (WRDS) |
    """)

    st.divider()

    # Quick FCF display
    st.subheader("📊 Historical Free Cash Flow")

    fcf_data = get_free_cash_flow(ticker, years=10)
    if not fcf_data.empty:
        fcf_display = fcf_data.copy()
        fcf_display['free_cash_flow'] = fcf_display['free_cash_flow'].apply(format_value)
        fcf_display['net_income'] = fcf_display['net_income'].apply(format_value)
        fcf_display.columns = ['Year', 'Net Income', 'Operating CF', 'CapEx', 'Free Cash Flow']
        st.dataframe(fcf_display, width='stretch')
    else:
        st.warning("No FCF data available")

    st.divider()

    # Quick start links
    st.subheader("📝 Quick Start")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.info("""
        ### 1. DCF Valuation
        Calculate intrinsic value using DCF model.

        [Go to DCF Valuation →](1_DCF_Valuation)
        """)

    with col2:
        st.info("""
        ### 2. Revenue Forecast
        Project future revenue based on historical data.

        [Go to Revenue Forecast →](4_Revenue_Forecast)
        """)

    with col3:
        st.info("""
        ### 3. Company Comparison
        Compare financial metrics across companies.

        [Go to Company Comparison →](3_Company_Comparison)
        """)

    with col4:
        st.info("""
        ### 4. Technical Analysis
        K-line and technical indicators analysis.

        [Go to Technical Analysis →](2_Technical_Analysis)
        """)

    st.divider()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>Financial Modeling Tool | Data Source: WRDS (Wharton Research Data Services)</p>
        <p>⚠️ Risk Warning: This tool is for educational reference only and does not constitute investment advice</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
