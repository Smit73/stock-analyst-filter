import streamlit as st
import pandas as pd

# 1. Load Data
st.set_page_config(page_title="Analyst Upside Finder", layout="wide")
st.title("📈 Stock Analyst Upside Finder")

# NEW: Load Data Function with Caching & Clear Logic
@st.cache_data(ttl="2h") # Cache data for 2 hours automatically
def load_data():
    try:
        # Read the CSV
        return pd.read_csv("stock_data.csv")
    except FileNotFoundError:
        return None

# Sidebar "Reset" Button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear() # Wipes the memory
    st.rerun() # Restarts the app instantly

df = load_data() # Use the function instead of direct pd.read_csv

if df is None:
    st.error("Data file not found. Please run 'fetch_data.py' first!")
    st.stop()

# 2. Sidebar Filters
st.sidebar.header("Filter Options")

# Filter: Sector (New)
available_sectors = sorted(df['Sector'].dropna().unique())
selected_sectors = st.sidebar.multiselect(
    "Filter by Sector",
    options=available_sectors,
    default=available_sectors
)

# Filter: Minimum Number of Analysts
min_analysts = st.sidebar.slider(
    "Minimum No. of Analysts", 
    min_value=0, 
    max_value=int(df['Num_Analysts'].max()), 
    value=0
)

# Filter: Upside Potential
min_upside = st.sidebar.number_input(
    "Minimum Upside Potential (%)", 
    value=0.0
)
min_div = st.sidebar.number_input("Minimum Dividend Yield (%)", value=0.0)
# Filter: Rating
rating_filter = st.sidebar.multiselect(
    "Filter by Rating Label",
    options=df['Rating'].unique(),
    default=df['Rating'].unique()
)

# 3. Apply Filters
filtered_df = df[
    (df['Num_Analysts'] >= min_analysts) &
    (df['Upside_Potential'] >= min_upside) &
    (df['Dividend_Yield'] >= min_div) &
    (df['Rating'].isin(rating_filter)) &
    (df['Sector'].isin(selected_sectors))
]

# 4. Sorting Logic
sort_col = st.radio(
    "Sort By:", 
    ["Upside_Potential", "Num_Analysts", "Forward_PE", "Trailing_PE"], 
    horizontal=True,
    index=0
)

# Handle sorting with NaN values (put missing P/E at bottom usually desired, but standard sort puts them last)
sorted_df = filtered_df.sort_values(by=sort_col, ascending=(sort_col in ["Forward_PE", "Trailing_PE"]))
# Note: Usually you want Upside Descending (High to Low), but P/E Ascending (Low to High). 
# The logic above flips the sort order: False for Upside (High first), True for P/E (Low first).

# 5. Display Data
st.metric("Stocks Found", len(sorted_df))

st.dataframe(
    sorted_df,
    column_config={
        "Upside_Potential": st.column_config.NumberColumn("Upside %", format="%.2f %%"),
        "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
        "Target_Price": st.column_config.NumberColumn("Target", format="$%.2f"),
        "Trailing_PE": st.column_config.NumberColumn("Trailing P/E", format="%.1f"),
        "Forward_PE": st.column_config.NumberColumn("Forward P/E", format="%.1f"),
        "Sector": "Sector",
        "Rating": "Rating",
        "Num_Analysts": "Analysts",
        "Strong_Buy": st.column_config.NumberColumn("Strong Buy", format="%d 🟢"),
        "Buy": st.column_config.NumberColumn("Buy", format="%d 🟢"),
        "Hold": st.column_config.NumberColumn("Hold", format="%d 🟡"),
        "Sell": st.column_config.NumberColumn("Sell", format="%d 🔴"),
        "Strong_Sell": st.column_config.NumberColumn("Strong Sell", format="%d 🔴"),
        "Dividend_Yield": st.column_config.NumberColumn("Div Yield", format="%.2f %%"),
    },
    use_container_width=True,
    hide_index=True
)
