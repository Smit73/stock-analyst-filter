import yfinance as yf
import pandas as pd
import time
import random
import requests
from io import StringIO  # Added this to handle the HTML string safely

def get_sp500_tickers():
    """scrapes the tickers from wikipedia using a browser header"""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    # 1. Define headers to look like a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
    # 2. Fetch the content using 'requests' instead of direct pandas
     response = requests.get(url, headers=headers) #This sends the actual request to the website and downloads the raw HTML code of the page.

    # 3. Use StringIO to pass the HTML text to pandas
    # (This avoids warnings about passing raw strings)
     tables = pd.read_html(StringIO(response.text)) #returns list of all the tables found on the wiki page
     df = tables[0] #grabs the first table from that list (index 0) 
    #because on the wiki page the first table is the one that contains the list of S&P 500 companies.
     tickers = [t.replace('.', '-') for t in df['Symbol'].tolist()] #grabs only the Symbol column from the dataframe and converts that column into standard list/array
     return tickers
    except Exception as e:
        print(f"Error getting S&P 500 list: {e}")
        return []

def get_nasdaq100_tickers():
    """Scrapes the Nasdaq 100 (Top Tech Stocks)"""
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, headers=headers)
        tables = pd.read_html(StringIO(response.text))
        
        # Smart Search for the table with "Ticker" or "Symbol"
        target_df = None
        for df in tables:
            if 'Ticker' in df.columns or 'Symbol' in df.columns:
                target_df = df
                break
        
        if target_df is None: return []

        col = 'Ticker' if 'Ticker' in target_df.columns else 'Symbol'
        tickers = [t.replace('.', '-') for t in target_df[col].tolist()]
        return tickers
    except Exception as e:
        print(f"Error getting Nasdaq 100 list: {e}")
        return []

def get_russell1000_tickers():
    """Scrapes the Russell 1000 (Top 1000 US Companies)"""
    url = "https://en.wikipedia.org/wiki/Russell_1000_Index"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, headers=headers)
        tables = pd.read_html(StringIO(response.text))
        
        # Smart Search
        target_df = None
        for df in tables:
            if 'Symbol' in df.columns or 'Ticker' in df.columns:
                target_df = df
                break
        
        if target_df is None: return []

        col = 'Symbol' if 'Symbol' in target_df.columns else 'Ticker'
        tickers = [t.replace('.', '-') for t in target_df[col].tolist()]
        return tickers
    except Exception as e:
        # Russell wiki pages are sometimes unstable, so we fail silently if missing
        print(f"Note: Could not fetch Russell 1000 (Wiki table might be missing).")
        return []

def get_tsx_composite_tickers():
    """Scrapes the S&P/TSX Composite Index from the specific user-provided URL"""
    url = "https://en.wikipedia.org/wiki/S%26P/TSX_Composite_Index"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        tables = pd.read_html(StringIO(response.text))
        
        #  The data is in the 4th table (Index 3) although it looks like table 3
        if len(tables) < 3:
            print("Error: Fewer than 3 tables found on TSX page.")
            return []
        # The table is usually the first one on this page
        df = tables[3]
        
        # Robust column finding: Look for 'Ticker' or 'Symbol'
        # On this specific wiki page, the column is named "Ticker"
        possible_names = ['Ticker', 'Symbol', 'Ticker symbol']
        col_name = next((name for name in possible_names if name in df.columns), None)
        
        if not col_name:
            print(f"Could not find ticker column. Available columns: {df.columns}")
            return []

        clean_tickers = []
        for ticker in df[col_name].tolist():
            # 1. Clean whitespace
            t = str(ticker).strip()
            
            # 2. Handle Share Classes (e.g., "TECK.B" -> "TECK-B")
            # Yahoo needs dashes for share classes, NOT dots.
            t = t.replace('.', '-')
            
            # 3. Add Suffix (e.g., "TECK-B" -> "TECK-B.TO")
            # If it doesn't already have .TO, add it.
            if not t.endswith('.TO'):
                t = f"{t}.TO"
                
            clean_tickers.append(t)
        
        return clean_tickers

    except Exception as e:
        print(f"Error getting TSX Composite list: {e}")
        return []

def get_custom_tickers():
    """Add any specific stocks that might not be in the indices above"""
    return [
        "GME", "AMC", "PLTR", "HOOD", "COIN", "RIVN", "SOFI", 
        "ARKK", "SPY", "QQQ", "IWM", "APLD", "MARA", "CIFR", "IREN", "AEVA", "INOD", "NBIS"
    ]

def fetch_analyst_data(tickers):
    data_list = []
    total = len(tickers)
    
    print(f"Starting scan for {total} stocks (US & Canada)...")

    for i, ticker in enumerate(tickers):
        # Retry Logic for Canadian Stocks
        attempts = [ticker]
        if ticker.endswith('.TO'):
            attempts.append(ticker.replace('.TO', '.NE'))

        success = False
        
        for current_ticker in attempts:
            if success: break
            
            try:
                stock = yf.Ticker(current_ticker)
                info = stock.info
                
                # 1. Get Basic Data
                current_price = info.get('currentPrice')
                target_mean = info.get('targetMeanPrice')

                div_yield = info.get('dividendYield', 0) 
                if div_yield is None: div_yield = 0
                
                if current_price and target_mean:
                    upside = ((target_mean - current_price) / current_price) * 100
                
                if current_price and target_mean:
                    upside = ((target_mean - current_price) / current_price) * 100
                    
                    
                    # NEW: Fetch ALL Analyst Counts
                    
                    strong_buy = 0
                    buy = 0
                    hold = 0
                    sell = 0
                    strong_sell = 0
                    
                    try:
                        # Grab the recommendation table
                        recs = stock.recommendations
                        
                        if recs is not None and not recs.empty:
                            # Use the first row (latest data)
                            latest = recs.iloc[0]
                            
                            # Safely extract all 5 columns
                            strong_buy = latest.get('strongBuy', 0)
                            buy = latest.get('buy', 0)
                            hold = latest.get('hold', 0)
                            sell = latest.get('sell', 0)
                            strong_sell = latest.get('strongSell', 0)
                            
                    except Exception:
                        pass
                    # -------------------------------------------------------

                    data_list.append({
                        "Ticker": current_ticker,
                        "Price": current_price,
                        "Currency": info.get('currency', 'USD'),
                        "Target_Price": target_mean,
                        "Upside_Potential": round(upside, 2),
                        "Num_Analysts": info.get('numberOfAnalystOpinions', 0),
                        # ALL 5 CATEGORIES
                        "Strong_Buy": int(strong_buy),
                        "Buy": int(buy),
                        "Hold": int(hold),
                        "Sell": int(sell),
                        "Strong_Sell": int(strong_sell),
                        "Rating": info.get('recommendationKey', 'N/A'),
                        "Sector": info.get('sector', 'Unknown'),
                        "Trailing_PE": info.get('trailingPE'),
                        "Forward_PE": info.get('forwardPE'),
                        "Dividend_Yield": div_yield
                    })
                    
                    # Print detailed success message so its working
                    print(f"[{i+1}/{total}] ✅ {current_ticker}")
                    success = True
                else:
                    pass

            except Exception:
                pass
        
        if not success:
             # Just a small dot for failures to keep console clean
             print(f"[{i+1}/{total}] ❌ {ticker}")
        
        # Sleep is vital for scanning 1500+ stocks
        time.sleep(random.uniform(0.2, 0.5))

    return pd.DataFrame(data_list)

if __name__ == "__main__":
    # Gather Lists
    sp500 = get_sp500_tickers()
    nasdaq = get_nasdaq100_tickers()
    russell = get_russell1000_tickers()
    tsx = get_tsx_composite_tickers()
    custom = get_custom_tickers()

    print(f"Sources Found: S&P500({len(sp500)}), Nasdaq100({len(nasdaq)}), Russell1000({len(russell)}), TSX({len(tsx)})")

    # Combine and Remove Duplicates (The SET command!)
    # This creates a master list of unique tickers
    master_list = list(set(sp500 + nasdaq + russell + tsx + custom))
    
    print(f"Total Unique Stocks after deduplication: {len(master_list)}")

    # Run the Scan
    df = fetch_analyst_data(master_list)

    # Save
    df.to_csv("stock_data.csv", index=False)
    print("\n🎉 Success! Data saved to 'stock_data.csv'. Run 'streamlit run app.py' to view.")