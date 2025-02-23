import pandas as pd
import yfinance as yf
import pymongo

# Hardcoded NASDAQ-100 list (approx. late 2023)
NASDAQ_100_TICKERS = [
    "AAPL", "ABNB", "ADBE", "ADI", "ADP", "ADSK", "AEP", "ALGN", "AMAT",
    "AMD", "AMGN", "AMZN", "ANSS", "ASML", "AVGO", "BIDU",
    "BIIB", "BKNG", "CDNS", "CDW", "CEG", "CHKP", "CHTR",
    "CMCSA", "COST", "CPRT", "CRWD", "CSCO", "CSX", "CTAS", "CTSH",
    "DDOG", "DLTR", "DOCU", "DXCM", "EA", "EBAY", "EXC", "FAST",
    "FTNT", "FOX", "FOXA", "GILD", "GOOG", "GOOGL", "HON", "IDXX",
    "ILMN", "INCY", "INTC", "INTU", "ISRG", "JD", "KDP", "KHC", "KLAC",
    "LRCX", "LULU", "MAR", "MCHP", "MDLZ", "MELI", "META", "MNST",
    "MRNA", "MRVL", "MSFT", "MTCH", "MU", "NFLX", "NTES", "NVDA", "NXPI",
    "OKTA", "ORLY", "PANW", "PAYX", "PCAR", "PDD", "PEP", "PYPL",
    "QCOM", "REGN", "ROST", "SBUX", "SIRI", "SNPS",
    "SWKS", "TEAM", "TMUS", "TSLA", "TXN", "VRSK", "VRSN", "VRTX",
    "WBA", "WDAY", "XEL", "ZM"
]

def fetch_close_prices(tickers, start_date, end_date):
    """
    Fetch daily closing prices for the given tickers within [start_date, end_date] using yfinance.
    Returns a DataFrame of 'Close' prices.
    """
    print(f"Fetching data from {start_date} to {end_date} for {len(tickers)} tickers...")
    stock_data = yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        group_by="ticker"
    )

    close_df = pd.DataFrame()
    valid_tickers = []

    for ticker in tickers:
        try:
            close_df[ticker] = stock_data[ticker]['Close']
            valid_tickers.append(ticker)
        except KeyError:
            print(f"Warning: No 'Close' data for {ticker}, skipping.")

    print(f"Successfully fetched 'Close' prices for {len(valid_tickers)} / {len(tickers)} tickers.")
    return close_df

def compute_correlation_dict(close_df, threshold=0.4):
    """
    1. Computes daily percentage returns from a 'Close' price DataFrame.
    2. Calculates correlation matrix.
    3. Builds and returns a dict: {ticker: [correlated tickers above threshold]}
    """
    # Compute daily returns
    returns_df = close_df.pct_change().dropna(how="all", axis=0)

    # Calculate correlation matrix
    correlation_matrix = returns_df.corr()

    # Build dictionary
    correlation_dict = {}
    for ticker in correlation_matrix.columns:
        correlated_series = correlation_matrix[ticker][correlation_matrix[ticker] > threshold]

        # Remove the ticker itself if present
        correlated_series = correlated_series.drop(labels=[ticker], errors='ignore')

        # Convert the index to a list
        correlation_dict[ticker] = correlated_series.index.tolist()

    return correlation_dict

def store_correlations_in_db(correlation_dict, mongo_uri, db_name, collection_name, drop_existing=False):
    """
    Connects to MongoDB, optionally drops the existing collection, 
    then inserts each ticker's correlations as a separate document.
    """
    client = pymongo.MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    if drop_existing:
        collection.drop()
        print(f"Dropped existing collection: {collection_name}")

    insert_count = 0
    for ticker, corr_list in correlation_dict.items():
        doc = {
            "ticker": ticker,
            "correlations": corr_list
        }
        collection.insert_one(doc)
        insert_count += 1

    print(f"Inserted {insert_count} documents into '{collection_name}' collection.")
