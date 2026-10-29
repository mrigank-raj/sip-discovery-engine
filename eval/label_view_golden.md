# Golden set: items to label

Fill: is_relevant, sip_action, action_reason, journey_stage, investor_experience, belief_at_action, belief_quote. For no belief, write null.

## 1

Source: appstore
Title: Portfolio Analytics Need Major Improvement

> INDmoney’s investment tracking needs significant improvement. It does not display XIRR for investments held for less than one year, making it difficult to accurately evaluate short-term investment performance.
>
> More importantly, there is no consolidated portfolio-level view showing metrics such as XIRR and total Gain/Loss across the entire portfolio, including both Stocks and Mutual Funds. Users should not have to analyze each investment category separately to understand their overall performance.
>
> A comprehensive portfolio dashboard with consolidated XIRR, absolute returns, total invested amount, current value, and overall Gain/Loss would make the app far more useful for tracking investments.

## 2

Source: play

> Your app shows me only historic XIRR returns of entire MF portfolio but not able to see my last 3M, 6M, 1Y, 3Y XIRR returns in MF . Kindly add this like other apps Zerodha, Groww.

## 3

Source: reddit
Title: How a bank manager sold a legal scam to my friend’s family. SBI Life Smart Platina Plus, broken down.

> Also honorable mention is the GST charged on each premium payment. Conveniently, nobody talks about that, and not even in your calculations. Add it, IIRC 4.5% on first premium payment, and 2.5% on subsequent payments, and your XIRR drops by 2-3% more.

## 4

Source: tradingqna
Title: Building Tools with Mutual Fund Data: A Quick Guide

> You can also refer to some more below 
>
> Mutual Fund API (mfapi.in)
>
> Direct API link: https://mfapi.in/
>
> Features:
>
> Free REST API for Indian Mutual Funds
>
> Get historical NAV data
>
> Search schemes by name/code
>
> Example Usage:
>
> pythonCopy# Get NAV for a specific scheme
> scheme_code = '119598'  # Example: SBI Blue Chip Fund-Direct Plan-Growth
> api_url = f'https://api.mfapi.in/mf/{scheme_code}'
>
> SIP Calculator
>
> Zerodha Calculators
>
> MF Algo test
>
> https://mf.algotest.in/
>
> Tijori Finance
>
> Link: https://tijorifinance.com/
>
> Features:
>
> Portfolio tracking
>
> Fund screener with advanced filters
>
> Performance comparison
>
> MoneyControl Mutual Fund Tools
>
> link: Mutual Funds Investment Online | Updated List of Mutual Funds | Best Performing Mutual Funds in India - Moneycontrol
>
> Tools available:
>
> Fund Screener
>
> Returns Calculator
>
> Fund Comparison
>
> RupeeVest Research Tools
>
> Link: https://www.rupeevest.com/Mutual-Funds
>
> Features:
>
> Compare multiple funds
>
> Risk analysis
>
> Portfolio overlap checker
>
> Python Library - mftool
>
> GitHub: GitHub - NayakwadiS/mftool: ⚡ Python library for getting publically available Mutual Funds data in India · GitHub
>
> pythonCopyfrom mftool import Mftool
> mf = Mftool()
> # Get scheme details
> scheme_info = mf.get_scheme_details('119598')
>
> Kuvera’s Analysis Tools
>
> Link: Kuvera by CRED
>
> Features:
>
> Portfolio Overlap
>
> Fund comparison
>
> Direct vs Regular comparison
>
> MarketsMojo
>
> Link: https://www.marketsmojo.com/mutualfund
>
> Features:
>
> Fund ratings
>
> Risk analysis
>
> Portfolio health check
>
> Further, I was trying to do something related to the analysis tool and ended up creating something using AI.
>
> Setting Up the Analysis Environment
>
> Python environment with necessary libraries:
>
> pip install mftool pandas numpy matplotlib streamlit plotly requests
>
> Basic Data Extraction Script
>
> from mftool import Mftool
> import pandas as pd
> import numpy as np
> from datetime import datetime, timedelta
> import plotly.graph_objects as go
>
> class MFAnalyzer:
>     def __init__(self):
>         self.mf = Mftool()
>
>     def get_scheme_data(self, scheme_code):
>         """Fetch scheme data and convert to DataFrame"""
>         scheme_data = self.mf.get_scheme_historical_nav(scheme_code)
>         if scheme_data is None:
>             return None
>
>         df = pd.DataFrame(scheme_data['data'])
>         df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
>         df['nav'] = pd.to_numeric(df['nav'])
>         return df.sort_values('date')
>
>     def calculate_returns(self, df):
>         """Calculate various return metrics"""
>         latest_nav = df['nav'].iloc[-1]
>         year_ago_nav = df[df['date'] >= (datetime.now() - timedelta(days=365))]['nav'].iloc[0]
>
>         returns = {
>             'one_year_return': ((latest_nav - year_ago_nav) / year_ago_nav) * 100,
>             'volatility': df['nav'].pct_change().std() * np.sqrt(252) * 100,
>             'latest_nav': latest_nav
>         }
>         return returns
>
> # Usage Example
> analyzer = MFAnalyzer()
> scheme_code = '119598'  # SBI Blue Chip Fund-Direct Plan-Growth
> df = analyzer.get_scheme_data(scheme_code)
> returns = analyzer.calculate_returns(df)
> print(f"One Year Return: {returns['one_year_return']:.2f}%")
> print(f"Volatility: {returns['volatility']:.2f}%")
>
> Building a Fund Comparison tool
>
> class MFComparator:
>     def __init__(self):
>         self.analyzer = MFAnalyzer()
>
>     def compare_funds(self, scheme_codes):
>         """Compare multiple funds"""
>         comparison_data = []
>
>         for code in scheme_codes:
>             scheme_info = self.analyzer.mf.get_scheme_details(code)
>             df = self.analyzer.get_scheme_data(code)
>             returns = self.analyzer.calculate_returns(df)
>
>             comparison_data.append({
>                 'scheme_name': scheme_info['scheme_name'],
>                 'one_year_return': returns['one_year_return'],
>                 'volatility': returns['volatility'],
>                 'latest_nav': returns['latest_nav'],
>                 'category': scheme_info['scheme_category']
>             })
>
>         return pd.DataFrame(comparison_data)
>
>     def plot_comparison(self, scheme_codes):
>         """Create comparison plot"""
>         fig = go.Figure()
>
>         for code in scheme_codes:
>             df = self.analyzer.get_scheme_data(code)
>             scheme_info = self.analyzer.mf.get_scheme_details(code)
>
>             # Normalize NAV values
>             normalized_nav = (df['nav'] / df['nav'].iloc[0]) * 100
>
>             fig.add_trace(go.Scatter(
>                 x=df['date'],
>                 y=normalized_nav,
>                 name=scheme_info['scheme_name']
>             ))
>
>         fig.update_layout(
>             title='Fund Comparison (Normalized Returns)',
>             xaxis_title='Date',
>             yaxis_title='Normalized NAV'
>         )
>         return fig
>
> # Usage Example
> comparator = MFComparator()
> funds_to_compare = ['119598', '119727']  # Add your fund codes
> comparison_df = comparator.compare_funds(funds_to_compare)
> comparison_plot = comparator.plot_comparison(funds_to_compare)
>
> Creating an Interactive Dashboard
>
> Dashboard to visualize the analysis:
>
> import streamlit as st
>
> def create_dashboard():
>     st.title('Mutual Fund Analysis Dashboard')
>
>     # Sidebar for fund selection
>     st.sidebar.header('Select Funds to Analyze')
>     selected_funds = st.sidebar.multiselect(
>         'Choose funds',
>         ['119598', '119727', '120503'],  # Add more fund codes
>         default=['119598']
>     )
>
>     if selected_funds:
>         comparator = MFComparator()
>
>         # Show comparison table
>         st.subheader('Fund Comparison')
>         comparison_df = comparator.compare_funds(selected_funds)
>         st.dataframe(comparison_df)
>
>         # Show comparison plot
>         st.subheader('Performance Comparison')
>         comparison_plot = comparator.plot_comparison(selected_funds)
>         st.plotly_chart(comparison_plot)
>
>         # Add risk metrics
>         st.subheader('Risk Metrics')
>         for fund in selected_funds:
>             df = comparator.analyzer.get_scheme_data(fund)
>             returns = comparator.analyzer.calculate_returns(df)
>             st.write(f"**{comparator.analyzer.mf.get_scheme_details(fund)['scheme_name']}**")
>             st.write(f"Volatility: {returns['volatility']:.2f}%")
>
> # Run dashboard
> if __name__ == '__main__':
>     create_dashboard()
>
> Advanced Analytics Features
>
> Portfolio Overlap Analysis
>
> def calculate_portfolio_overlap(scheme1_code, scheme2_code):
>     """Calculate portfolio overlap between two schemes"""
>     mf = Mftool()
>
>     # Get portfolio holdings
>     scheme1_info = mf.get_scheme_details(scheme1_code)
>     scheme2_info = mf.get_scheme_details(scheme2_code)
>
>     # Extract stock names
>     scheme1_stocks = set(holding['stock_name'] for holding in scheme1_info.get('portfolio_holdings', []))
>     scheme2_stocks = set(holding['stock_name'] for holding in scheme2_info.get('portfolio_holdings', []))
>
>     # Calculate overlap
>     common_stocks = scheme1_stocks.intersection(scheme2_stocks)
>     overlap_percentage = (len(common_stocks) / min(len(scheme1_stocks), len(scheme2_stocks))) * 100
>
>     return {
>         'overlap_percentage': overlap_percentage,
>         'common_stocks': list(common_stocks)
>     }
>
> Risk-Adjusted Returns Analysis
>
> def calculate_risk_metrics(df):
>     """Calculate advanced risk metrics"""
>     returns = df['nav'].pct_change()
>     risk_free_rate = 0.04  # Assume 4% risk-free rate
>
>     # Sharpe Ratio
>     excess_returns = returns - (risk_free_rate/252)
>     sharpe_ratio = np.sqrt(252) * excess_returns.mean() / returns.std()
>
>     # Maximum Drawdown
>     cumulative_returns = (1 + returns).cumprod()
>     rolling_max = cumulative_returns.expanding().max()
>     drawdowns = cumulative_returns/rolling_max - 1
>     max_drawdown = drawdowns.min()
>
>     return {
>         'sharpe_ratio': sharpe_ratio,
>         'max_drawdown': max_drawdown,
>         'annualized_volatility': returns.std() * np.sqrt(252)
>     }
>
> Implementing the System
>
> To use this complete system:
>
> Save the code in separate files (e.g., analyzer.py, comparator.py, dashboard.py)
>
> Install required dependencies
>
> Run the dashboard:streamlit run dashboard.py
>
> Key Features of this tool:
>
> Data Extraction
>
> Historical NAV data
>
> Scheme details
>
> Portfolio holdings
>
> Analysis Capabilities
>
> Returns calculation
>
> Risk metrics
>
> Portfolio overlap
>
> Performance comparison
>
> Visualization
>
> Interactive plots
>
> Comparison charts
>
> Risk-return scatter plots
>
> Dashboard Features
>
> Fund selection
>
> Performance metrics
>
> Risk analysis
>
> Portfolio comparison
>
> References and Resources
>
> mftool Documentation: GitHub - NayakwadiS/mftool: ⚡ Python library for getting publically available Mutual Funds data in India · GitHub
>
> Streamlit Documentation: https://docs.streamlit.io/
>
> Plotly Documentation: Open Source Python Graphing & Data Visualization Library | Plotly
>
> Additional data sources:
>
> Money Control API
>
> RupeeVest API
>
> Value Research API

## 5

Source: youtube
Title: SIP 📈माइनस में जा रहा है क्या करें | गिरते हुए Market में SIP करें या रोक दें | Mutual Fund SIP Loss

> Agar har month sip kar rahe hai to aage chal kar agar return nahi dega to jo paisa invest kiye hai wo to milega na

## 6

Source: appstore
Title: Love the simplicity

> Lot of people raising concerns here , probably don’t know use case of this app. They need to understand difference between demat mutual fund and buying from other platforms. Great app overall , love the stability

## 7

Source: play

> mf does not have weekly stp option

## 8

Source: reddit
Title: Need suggestion whether to enhance Emergency Fund or continue with current plan

> Might be easier to start another SIP in a liquid or ultra short duration fund and put a portion of your monthly investment there until you reach your target amount.
>
>
>       Then you can close to keep that as your emergency fund or withdraw it as a while and put it in an FD.

## 9

Source: tradingqna
Title: [Feature request] Need option to select only mutual funds in Console

> [Feature request] Need option to select only mutual funds in Console
>
> Currently we see option to exclude the mutual funds in “Holdings” page which enables to select just stocks.
>
> Similarly I am looking for option to select just MF holdings for sector wise allocation and stocks they are holding.

## 10

Source: youtube
Title: How I Turned ₹30k/Month SIP into ₹1 Crore 😱🔥 #investing #wealthcreation  #sanjaykathuria

> DSP Small Cap Fund - Direct Plan - Growth

## 11

Source: appstore
Title: Redemptions not working, fake success status

> Groww has made a blunder in my friend’s bank account. As a result, withdrawals go ‘on hold’. Groww wrongly shows redemption successful, and there is no way of reporting the issue to customer care. Customers realise this when there is no money in account after 10-15 days.
>
> The only way of getting money, is to go through the bank account modification procedure to be done in person for each folio separately, which takes 10-15 days. Removal of hold takes another 10 days. In total, redemption takes 6-8 weeks of rigorous efforts because they messed up in their DB.
>
> We have used several other apps. Never seen this happening elsewhere.

## 12

Source: play

> if you r using groww for only mf don't upgrade to dmat. otherwise u will redeem your money only thg Grow. that fund's app redeem money more faster than grow. grow takes 2 day more time

## 13

Source: reddit
Title: Veterans who have been in the Indian market for 20+ years: How did you handle historical crashes without stopping your SIPs?

> 2020 was the first major crash in my investment journey. And like everyone I freaked out as well. My portfolio was down 60%. But somehow I endured all and never stopped my SIP's and never took out any money. Then I saw the fruits of those in the consecutive years where my XIRR touched 15-16%.

## 14

Source: tradingqna
Title: My MF Central account is showing unregistered folios - "Please Note: Due to availability of multiple Email IDs, the following folios could not be registered under MFCentral "

> Does it give detailed  CG statement with for each quarter as mandated by tax forms?

## 15

Source: youtube
Title: Angel One me SIP Kaise Cancel Kare? How to Stop SIP in Angel One App in Hindi

> Once we cancel the SIP, can we restart it when we want?

## 16

Source: appstore
Title: Minimal Features and a very basic app

> App barely has any features, xirr functionality works sometimes. Haven’t seen the app get any meaningful update in the last few years. Even filters to search for mutual funds are so so basic.

## 17

Source: play

> Groww offers mutual funds with competitive returns. Top funds: Groww Value Fund (18.69% 5-year return), ELSS Tax Saver Fund, Largecap Fund. Zero commission, SIP ₹500. Expense ratios: 0.9%. AUM: ₹66 Cr (Value Fund). Risk: High. Consult a financial advisor. Check current NAV.

## 18

Source: reddit
Title: Veterans who have been in the Indian market for 20+ years: How did you handle historical crashes without stopping your SIPs?

> What did you feel in 2020. I remember my Covid days when market was dropping like crazy, my xirr went negative and out of fear I didn't broke my FD and invest in lumpsum. A big mistake

## 19

Source: tradingqna
Title: Mutual Fund CAGR Graph - Before or After Deduction of Expense Ratio

> Hi @thethinker, The CAGR returns that you see for mutual funds on Coin/Console or other platforms are shown after deduction of the expense ratio. This is because the NAV (Net Asset Value) of a mutual fund, which is used to calculate returns and CAGR, is declared after accounting for the expense ratio.
>
> So, any return, whether it’s the daily change or long-term CAGR like 1Y, 3Y, or 5Y, that you see based on NAVs is already net of the expense ratio.

## 20

Source: youtube
Title: Secret Trick that gives better returns than SIP

> I am purchasing additional units  in mutual fund, only when market falls. This will avoid purchase of units with higher NAV. So far all my mutual funds are doing well even after continuous fall of market.
