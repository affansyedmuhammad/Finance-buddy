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


sample_ticker = "GOOG"
related_stocks = []
sentiment_analysis_results = []

#===========get the trikker from frontend request

#Pass the extracted trikker to extract list of co-related stocks

result = collection_corelation_db.find_one({"ticker": sample_ticker})
if result:
    print(f"\nSample correlations for '{sample_ticker}':")

    # 'related_stocks' is expected to be a list of tickers, e.g. ["AAPL", "MSFT", ...]
    related_stocks = result["correlations"]
    print(related_stocks)

    # if not related_stocks:
    #     print("No correlated stocks found.")
    # else:
    #     print("Correlated tickers:\n")
    #     # Here we print them all. If you only want the top 5, do: for idx, ticker in enumerate(related_stocks[:5], start=1):
    #     for idx, ticker in enumerate(related_stocks, start=1):
    #         print(f"{idx}. {ticker}")

else:
    print(f"Ticker '{sample_ticker}' not found in MongoDB.")

related_stocks.append(sample_ticker)
print(related_stocks)
# #===========pass the list of trikkers to both function below
# #fetch and print predicted price for tikker
# predict_stock_price.predict_stock_close_price(sample_ticker)

# Fetch sentiment data
for trikker in related_stocks:
    # sentiment_analysis.fetch_sentiment_data(client, ['AAPL'], days=5) //to be used with API access for polygon.ai
    sentiment_analysis_results.append(sentiment_analysis.get_sentiment_by_ticker(mongo_uri, db, collection_sentiment_db,trikker ))
# print(sentiment_analysis.get_sentiment_by_ticker(mongo_uri, db, collection_sentiment_db,sample_ticker ))
# print(sentiment_analysis_results)