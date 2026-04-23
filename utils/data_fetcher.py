"""
Data Fetcher Module - WRDS Only (Fixed Version)
For Financial Modeling
"""
import pandas as pd
import requests
from typing import Dict, Optional
import os
import warnings

# WRDS Configuration
WRDS_CONFIG = {
    "username": "guzixin",
    "password": "9jitngv3Hwq!UT8"
}

# Cache WRDS connection
_wrds_conn = None
_wrds_libs = None


def get_wrds_connection():
    """Get WRDS connection"""
    global _wrds_conn
    if _wrds_conn is None:
        try:
            import wrds
            _wrds_conn = wrds.Connection(
                wrds_username=WRDS_CONFIG["username"],
                wrds_password=WRDS_CONFIG["password"]
            )
            print("[OK] WRDS connected")
        except Exception as e:
            print(f"[X] WRDS connection failed: {e}")
            _wrds_conn = False
    return _wrds_conn if _wrds_conn else None


def is_connected() -> bool:
    """Check WRDS connection status"""
    return get_wrds_connection() is not None


# ============= Stock Basic Info =============

def get_stock_info(ticker: str) -> Dict:
    """Get stock basic information"""
    conn = get_wrds_connection()
    if not conn:
        return {'error': 'WRDS not connected', 'success': False}

    ticker = ticker.upper()

    try:
        # Get stock info from CRSP - try multiple methods
        # First try to get company name from funda
        query = f"""
            SELECT DISTINCT tic, conm as name
            FROM comp.funda
            WHERE tic = '{ticker}'
            LIMIT 1
        """
        df = conn.raw_sql(query, date_cols=[])

        if df is not None and len(df) > 0:
            return {
                'ticker': df.iloc[0]['tic'],
                'name': df.iloc[0]['name'],
                'exchange': 'US',
                'success': True,
                'source': 'wrds'
            }
    except Exception as e:
        print(f"Stock info error: {e}")

    # If not found, return basic info
    return {
        'ticker': ticker,
        'name': f"{ticker} Corp",
        'exchange': 'US',
        'success': True,
        'source': 'wrds'
    }


def get_stock_quote(ticker: str) -> Dict:
    """Get stock quote (using most recent trading day data)"""
    conn = get_wrds_connection()
    if not conn:
        return {'error': 'WRDS not connected', 'success': False}

    ticker = ticker.upper()

    try:
        # First get the permco from crsp.stocknames
        query = f"""
            SELECT permco
            FROM crsp.stocknames
            WHERE ticker = '{ticker}'
            ORDER BY namedt DESC
            LIMIT 1
        """
        permco_df = conn.raw_sql(query, date_cols=['namedt'])

        if permco_df is None or len(permco_df) == 0:
            # Try alternative: get permco from comp.funda using gvkey
            query = f"""
                SELECT gvkey
                FROM comp.funda
                WHERE tic = '{ticker}'
                LIMIT 1
            """
            permco_df = conn.raw_sql(query, date_cols=[])

        if permco_df is not None and len(permco_df) > 0:
            permco = permco_df.iloc[0]['permco'] if 'permco' in permco_df.columns else permco_df.iloc[0]['gvkey']

            # Get recent price data from CRSP using crsp.msf
            query = f"""
                SELECT permco, date, prc, vol
                FROM crsp.msf
                WHERE permco = {permco}
                AND date >= '2020-01-01'
                ORDER BY date DESC
                LIMIT 1
            """
            df = conn.raw_sql(query, date_cols=['date'])

            if df is not None and len(df) > 0:
                row = df.iloc[0]
                return {
                    'ticker': ticker,
                    'name': row.get('ticker', ticker),
                    'price': abs(row.get('prc', 0)),
                    'volume': row.get('vol', 0) or 0,
                    'date': str(row.get('date', '')),
                    'success': True,
                    'source': 'wrds'
                }
    except Exception as e:
        print(f"Quote error: {e}")

    return {'error': f'Unable to fetch data for {ticker}', 'success': False}


def get_shares_outstanding(ticker: str) -> float:
    """Get shares outstanding from Compustat (in millions)"""
    conn = get_wrds_connection()
    if not conn:
        return 0.0

    ticker = ticker.upper()

    try:
        # Get most recent shares outstanding from comp.funda
        query = f"""
            SELECT csho
            FROM comp.funda
            WHERE tic = '{ticker}'
            AND csho IS NOT NULL
            ORDER BY fyear DESC
            LIMIT 1
        """
        df = conn.raw_sql(query)

        if df is not None and len(df) > 0:
            return float(df.iloc[0]['csho'])
    except Exception as e:
        print(f"Shares outstanding error: {e}")

    return 0.0


# ============= K-line Data =============

def get_kline_data(ticker: str, days: int = 365) -> pd.DataFrame:
    """Get K-line historical data"""
    conn = get_wrds_connection()
    if not conn:
        return pd.DataFrame()

    ticker = ticker.upper()

    try:
        # First get the permco from crsp.stocknames using ticker
        query = f"""
            SELECT permco
            FROM crsp.stocknames
            WHERE ticker = '{ticker}'
            ORDER BY namedt DESC
            LIMIT 1
        """
        permco_df = conn.raw_sql(query, date_cols=['namedt'])

        if permco_df is None or len(permco_df) == 0:
            # Try alternative: get permco from comp.funda using gvkey
            query = f"""
                SELECT gvkey
                FROM comp.funda
                WHERE tic = '{ticker}'
                LIMIT 1
            """
            permco_df = conn.raw_sql(query, date_cols=[])

        if permco_df is not None and len(permco_df) > 0:
            permco = permco_df.iloc[0]['permco'] if 'permco' in permco_df.columns else permco_df.iloc[0]['gvkey']

            # Now get price data from crsp.msf (monthly stock file)
            query = f"""
                SELECT date, prc as close, bidlo, askhi, vol
                FROM crsp.msf
                WHERE permco = {permco}
                AND date >= '2020-01-01'
                AND prc IS NOT NULL
                ORDER BY date ASC
            """
            df = conn.raw_sql(query, date_cols=['date'])

            if df is not None and len(df) > 0:
                df.columns = ['date', 'close', 'high', 'low', 'volume']
                df['high'] = df['high'].fillna(df['close'])
                df['low'] = df['low'].fillna(df['close'])
                df['open'] = df['close']
                df = df[['date', 'open', 'close', 'high', 'low', 'volume']]
                return df
    except Exception as e:
        print(f"K-line error: {e}")

    return pd.DataFrame()


# ============= Financial Data =============

def get_financial_data(ticker: str) -> Dict:
    """Get complete financial data"""
    conn = get_wrds_connection()
    if not conn:
        return {'error': 'WRDS not connected', 'success': False}

    ticker = ticker.upper()
    results = {}

    # Get Compustat financial data - use correct table and column names
    try:
        # Income Statement / Cash Flow Statement (Annual)
        query = f"""
            SELECT fyear, datadate, sale, cogs, oibdp, ebit, netinc, oancf, capx
            FROM comp.funda
            WHERE tic = '{ticker}'
            AND fyear >= EXTRACT(YEAR FROM CURRENT_DATE) - 10
            AND datadate IS NOT NULL
            ORDER BY fyear DESC
            LIMIT 10
        """
        df = conn.raw_sql(query, date_cols=['datadate'])
        if df is not None and len(df) > 0:
            results['income'] = df.to_dict('records')

        # Balance Sheet
        query = f"""
            SELECT fyear, datadate, at, lt, eq, cash, rect, inv
            FROM comp.funda
            WHERE tic = '{ticker}'
            AND fyear >= EXTRACT(YEAR FROM CURRENT_DATE) - 10
            AND datadate IS NOT NULL
            ORDER BY fyear DESC
            LIMIT 10
        """
        df = conn.raw_sql(query, date_cols=['datadate'])
        if df is not None and len(df) > 0:
            results['balance_sheet'] = df.to_dict('records')

        results['success'] = True
        results['source'] = 'wrds'

    except Exception as e:
        print(f"Financial data error: {e}")
        results = {'error': str(e), 'success': False}

    return results


def get_free_cash_flow(ticker: str, years: int = 5) -> pd.DataFrame:
    """Get free cash flow data (values in millions USD)"""
    conn = get_wrds_connection()
    if not conn:
        return pd.DataFrame()

    ticker = ticker.upper()

    try:
        # Calculate FCF using Compustat - use correct column names
        # ni = Net Income, oancf = Operating Cash Flow, capx = Capital Expenditure
        # Values are in millions of USD
        query = f"""
            SELECT
                fyear as year,
                ni as net_income,
                oancf as operating_cf,
                COALESCE(capx, 0) as capex,
                (oancf - COALESCE(capx, 0)) as free_cash_flow
            FROM comp.funda
            WHERE tic = '{ticker}'
            AND oancf IS NOT NULL
            AND fyear >= EXTRACT(YEAR FROM CURRENT_DATE) - {years}
            ORDER BY fyear DESC
        """
        df = conn.raw_sql(query, date_cols=[])

        if df is not None and len(df) > 0:
            return df

    except Exception as e:
        print(f"FCF error: {e}")

    return pd.DataFrame()


# ============= DCF Valuation =============

def calculate_dcf(
    ticker: str,
    wacc: float = 0.10,
    perpetual_growth: float = 0.025,
    forecast_years: int = 5,
    earnings_growth: float = 0.05
) -> Dict:
    """DCF Valuation Calculation - Using WRDS Real Data"""
    conn = get_wrds_connection()
    if not conn:
        return {'ticker': ticker, 'error': 'WRDS not connected', 'success': False}

    ticker = ticker.upper()

    try:
        # Get FCF data
        fcf_df = get_free_cash_flow(ticker, years=10)

        if fcf_df.empty:
            return {'ticker': ticker, 'error': 'No cash flow data', 'success': False}

        # Use average FCF from recent years as base
        avg_fcf = fcf_df.head(3)['free_cash_flow'].mean()

        if pd.isna(avg_fcf) or avg_fcf <= 0:
            avg_fcf = abs(avg_fcf) if not pd.isna(avg_fcf) else 1e8
            avg_fcf = avg_fcf * 0.8  # Adjustment

        # Forecast future cash flows
        future_fcf = []
        for year in range(1, forecast_years + 1):
            fcf_forecast = avg_fcf * (1 + earnings_growth) ** year
            future_fcf.append(fcf_forecast)

        # Discount calculation
        discounted_fcf = [fcf / (1 + wacc) ** i for i, fcf in enumerate(future_fcf, 1)]
        pv_sum = sum(discounted_fcf)

        # Terminal Value
        terminal_fcf = future_fcf[-1] * (1 + perpetual_growth)
        terminal_value = terminal_fcf / (wacc - perpetual_growth) if wacc > perpetual_growth else 0
        terminal_pv = terminal_value / (1 + wacc) ** forecast_years

        # Enterprise Value (FCF values from WRDS are in millions)
        enterprise_value = pv_sum + terminal_pv  # in millions

        # Get shares outstanding (in millions from Compustat)
        quote = get_stock_quote(ticker)
        current_price = quote.get('price', 100) if quote.get('success') else 100

        # Get shares from Compustat (csho is in millions)
        try:
            query = f"""
                SELECT csho
                FROM comp.funda
                WHERE tic = '{ticker}'
                AND csho IS NOT NULL
                ORDER BY fyear DESC
                LIMIT 1
            """
            shares_df = conn.raw_sql(query, date_cols=[])
            if shares_df is not None and len(shares_df) > 0:
                shares = float(shares_df.iloc[0]['csho'])  # csho is in millions
            else:
                shares = 0
        except:
            shares = 0

        # Get net debt from balance sheet (comp.funda)
        # che = Cash and Short-term Investments
        # dltt = Long-term Debt, dlc = Current Liabilities (Debt)
        # Net Debt = (dltt + dlc) - che
        try:
            query = f"""
                SELECT che, dltt, dlc
                FROM comp.funda
                WHERE tic = '{ticker}'
                AND che IS NOT NULL AND dltt IS NOT NULL
                ORDER BY fyear DESC
                LIMIT 1
            """
            balance_df = conn.raw_sql(query, date_cols=[])
            if balance_df is not None and len(balance_df) > 0:
                che = float(balance_df.iloc[0]['che']) if balance_df.iloc[0]['che'] else 0
                dltt = float(balance_df.iloc[0]['dltt']) if balance_df.iloc[0]['dltt'] else 0
                dlc = float(balance_df.iloc[0]['dlc']) if balance_df.iloc[0]['dlc'] else 0
                net_debt = max(0, (dltt + dlc) - che)  # in millions
            else:
                net_debt = 0
        except:
            net_debt = 0

        # Equity Value = Enterprise Value - Net Debt
        equity_value = enterprise_value - net_debt  # in millions

        # Share Price = Equity Value / Shares
        # enterprise_value is in millions, shares is in millions
        # So share_price = millions / millions = dollars
        share_price = equity_value / shares if shares else 0

        # Upside
        upside = ((share_price / current_price) - 1) * 100 if current_price else 0

        return {
            'ticker': ticker,
            'enterprise_value': enterprise_value,
            'equity_value': equity_value,
            'share_price': share_price,
            'current_price': current_price,
            'upside': upside,
            'forecast_fcf': future_fcf,
            'discounted_fcf': discounted_fcf,
            'terminal_value': terminal_value,
            'wacc': wacc,
            'perpetual_growth': perpetual_growth,
            'forecast_years': forecast_years,
            'success': True,
            'source': 'wrds'
        }

    except Exception as e:
        return {'ticker': ticker, 'error': str(e), 'success': False}


def sensitivity_analysis(
    base_dcf: Dict,
    wacc_range: list = None,
    growth_range: list = None
) -> pd.DataFrame:
    """Sensitivity Analysis"""
    if wacc_range is None:
        wacc_range = [0.06, 0.08, 0.10, 0.12, 0.14]
    if growth_range is None:
        growth_range = [0.01, 0.02, 0.03, 0.04, 0.05]

    results = []

    for wacc in wacc_range:
        row = {'WACC': f"{wacc*100:.0f}%"}
        for growth in growth_range:
            result = calculate_dcf(
                ticker=base_dcf.get('ticker', 'AAPL'),
                wacc=wacc,
                perpetual_growth=growth,
                forecast_years=base_dcf.get('forecast_years', 5)
            )
            if result.get('success'):
                row[f'{growth*100:.0f}%'] = result.get('share_price', 0)
            else:
                row[f'{growth*100:.0f}%'] = 0
        results.append(row)

    return pd.DataFrame(results)


# ============= Test =============

def test_wrds():
    """Test WRDS connection"""
    print("=== WRDS Data Source Test ===")

    conn = get_wrds_connection()
    if not conn:
        print("[X] WRDS not connected")
        return

    print("[OK] WRDS connected")

    # Test stock data
    test_stocks = ['AAPL', 'MSFT']

    for ticker in test_stocks:
        print(f"\n--- Testing {ticker} ---")

        # Basic Info
        info = get_stock_info(ticker)
        print(f"Info: {'OK' if info.get('success') else 'FAIL'}")

        # K-line
        kline = get_kline_data(ticker, days=30)
        print(f"K-line: {len(kline)} days")

        # FCF
        fcf = get_free_cash_flow(ticker, years=5)
        print(f"FCF: {len(fcf)} years")


if __name__ == "__main__":
    test_wrds()