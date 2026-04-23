"""
DCF估值模块 - 现金流折现模型
使用Financial Modeling Prep API获取数据
"""
import pandas as pd
import numpy as np
import requests
from typing import Dict

# FMP API配置
FMP_API_KEY = "MsrVwz3TFRE28mlmXNkwFWbcia2noFns"
FMP_BASE_URL = "https://financialmodelingprep.com/stable"


def calculate_dcf(
    ticker: str,
    wacc: float = 0.10,
    perpetual_growth: float = 0.025,
    forecast_years: int = 5,
    earnings_growth: float = 0.05
) -> Dict:
    """
    DCF估值计算 - 使用FMP API

    参数:
        ticker: 股票代码 (如 AAPL, MSFT)
        wacc: 加权平均资本成本 (默认10%)
        perpetual_growth: 永续增长率 (默认2.5%)
        forecast_years: 预测年数 (默认5年)
        earnings_growth: 盈利增长率 (默认5%)

    返回:
        dict: 包含企业价值、股权价值、每股价格等
    """
    ticker = ticker.upper()

    try:
        # 获取实时报价
        quote_url = f"{FMP_BASE_URL}/quote"
        quote_params = {"symbol": ticker, "apikey": FMP_API_KEY}
        quote_r = requests.get(quote_url, params=quote_params, timeout=10)

        if quote_r.status_code == 402:
            return {
                'ticker': ticker,
                'error': '需要FMP Premium订阅 (402) - 某些股票不在免费范围内)',
                'success': False
            }
        if quote_r.status_code != 200:
            return {
                'ticker': ticker,
                'error': f'API返回状态码 {quote_r.status_code}',
                'success': False
            }

        quote_data = quote_r.json()
        if not quote_data:
            return {'ticker': ticker, 'error': '未找到股票数据', 'success': False}

        quote = quote_data[0]
        current_price = quote.get('price', 0)
        market_cap = quote.get('marketCap', 0)
        shares = market_cap / current_price if current_price > 0 else 1e9

        # 获取现金流数据
        cf_url = f"{FMP_BASE_URL}/cash-flow-statement"
        cf_params = {"symbol": ticker, "apikey": FMP_API_KEY}
        cf_r = requests.get(cf_url, params=cf_params, timeout=10)

        if cf_r.status_code != 200:
            return {
                'ticker': ticker,
                'error': '无法获取现金流数据',
                'success': False
            }

        cf_data = cf_r.json()
        if not cf_data:
            return {'ticker': ticker, 'error': '无现金流数据', 'success': False}

        latest_cf = cf_data[0]

        # 提取FCF组成部分
        net_income = latest_cf.get('netIncome', 0) or 0
        depreciation = latest_cf.get('depreciation', 0) or 0
        capex = abs(latest_cf.get('capitalExpenditure', 0) or 0)
        change_nwc = latest_cf.get('changeInWorkingCapital', 0) or 0  # 营运资本变化

        # 简化FCF计算: FCF = Net Income + D&A - CapEx + Change in NWC
        fcf = net_income + depreciation - capex + change_nwc

        # 如果FCF为负或0，使用Net Income作为估计
        if fcf <= 0:
            fcf = net_income * 0.8  # 假设FCF约为NI的80%

        # 预测未来现金流
        future_fcf = []
        for year in range(1, forecast_years + 1):
            fcf_forecast = fcf * (1 + earnings_growth) ** year
            future_fcf.append(fcf_forecast)

        # 折现计算
        discounted_fcf = [fcf_val / (1 + wacc) ** i for i, fcf_val in enumerate(future_fcf, 1)]
        pv_sum = sum(discounted_fcf)

        # 终值计算 (Gordon Growth Model)
        terminal_fcf = future_fcf[-1] * (1 + perpetual_growth)
        terminal_value = terminal_fcf / (wacc - perpetual_growth) if wacc > perpetual_growth else 0
        terminal_pv = terminal_value / (1 + wacc) ** forecast_years

        # 企业价值
        enterprise_value = pv_sum + terminal_pv

        # 股权价值 (简化)
        equity_value = enterprise_value

        # 每股价格
        share_price = equity_value / shares if shares else 0

        # 上涨空间
        upside = ((share_price / current_price) - 1) * 100 if current_price else 0

        return {
            'ticker': ticker,
            'name': quote.get('name', ticker),
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
            'success': True
        }

    except Exception as e:
        return {
            'ticker': ticker,
            'error': str(e),
            'success': False
        }


def sensitivity_analysis(
    base_dcf: Dict,
    wacc_range: list = None,
    growth_range: list = None
) -> pd.DataFrame:
    """
    敏感性分析 - WACC vs 永续增长率
    """
    if wacc_range is None:
        wacc_range = [0.06, 0.08, 0.10, 0.12, 0.14]

    if growth_range is None:
        growth_range = [0.01, 0.02, 0.03, 0.04, 0.05]

    results = []

    for wacc in wacc_range:
        row = {'WACC': f"{wacc*100:.0f}%"}
        for growth in growth_range:
            result = calculate_dcf(
                ticker=base_dcf.get('ticker', ''),
                wacc=wacc,
                perpetual_growth=growth,
                forecast_years=base_dcf.get('forecast_years', 5),
                earnings_growth=0.05
            )
            if result.get('success'):
                row[f'{growth*100:.0f}%'] = result.get('share_price', 0)
            else:
                row[f'{growth*100:.0f}%'] = 0

        results.append(row)

    return pd.DataFrame(results)


def calculate_valuation_multiples(ticker: str) -> Dict:
    """
    计算估值倍数 - 使用FMP API
    """
    ticker = ticker.upper()

    try:
        url = f"{FMP_BASE_URL}/quote"
        params = {"symbol": ticker, "apikey": FMP_API_KEY}
        r = requests.get(url, params=params, timeout=10)

        if r.status_code != 200:
            return {}

        data = r.json()
        if not data:
            return {}

        stock = data[0]

        return {
            'P/E': stock.get('priceAvg50', 0),  # 使用50日均价作为参考
            'Market Cap': stock.get('marketCap', 0),
            'Price': stock.get('price', 0),
            'Beta': stock.get('beta', 0),
        }
    except Exception as e:
        print(f"Multiples calculation failed: {e}")
        return {}