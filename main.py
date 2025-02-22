import compute_stock_relation
import sentiment_analysis
import predict_stock_price
from polygon import RESTClient
import pymongo
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
# Retrieve sensitive data from environment variables
polygon_api_key = os.getenv("POLYGON_API_KEY")
mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME")
collection_sentiment = os.getenv("COLLECTION_SENTIMENT")
collection_corelation = os.getenv("COLLECTION_CORELEATION")
# Initialize Polygon Client
client = RESTClient(api_key=polygon_api_key)
# Initialize MongoDB Client
client1 = pymongo.MongoClient(mongo_uri)
db = client1[db_name]
collection_sentiment_db = db[collection_sentiment]
collection_corelation_db = db[collection_corelation]


sample_ticker = "AAPL"
related_stocks = []
predicted_closing_rate = {}  # Dictionary to store predicted closing prices
sentiment_analysis_results = {}  # Dictionary to store sentiment analysis results


#===========get the trikker from frontend request

#Pass the extracted trikker to extract list of co-related stocks

result = collection_corelation_db.find_one({"ticker": sample_ticker})
if result:
    print(f"\nSample correlations for '{sample_ticker}':")
    # 'related_stocks' is expected to be a list of tickers, e.g. ["AAPL", "MSFT", ...]
    related_stocks = result["correlations"]
else:
    print(f"Ticker '{sample_ticker}' not found in MongoDB.")

related_stocks.append(sample_ticker)
print("related stocks = ",related_stocks)



# Fetch sentiment data and predicted stock price
for trikker in related_stocks:
    # Fetch and store predicted price for trikker
    # predicted_closing_rate[trikker] = predict_stock_price.predict_stock_close_price(trikker)

    # Fetch and store sentiment analysis results
    sentiment_analysis_results[trikker] = sentiment_analysis.get_sentiment_by_ticker(
        mongo_uri, db, collection_sentiment_db, trikker
    )
print(sentiment_analysis_results)