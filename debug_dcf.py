from utils.data_fetcher import get_free_cash_flow, get_stock_quote, get_shares_outstanding

# Get FCF
fcf = get_free_cash_flow('AAPL', years=10)
print('FCF values:')
print(fcf)
print()

# Get avg
avg_fcf = fcf.head(3)['free_cash_flow'].mean()
print(f'Avg FCF: {avg_fcf}')
print(f'Avg FCF (billions): {avg_fcf/1000}')
print()

# Get shares
shares = get_shares_outstanding('AAPL')
print(f'Shares: {shares}')
print()

# Get quote
quote = get_stock_quote('AAPL')
print(f'Current Price: {quote.get("price")}')
