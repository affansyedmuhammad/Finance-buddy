import compute_stock_relation
import sentiment_analysis
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
collection_name = os.getenv("COLLECTION_NAME")

# Initialize Polygon Client
client = RESTClient(api_key=polygon_api_key)

# Initialize MongoDB Client
client1 = pymongo.MongoClient(mongo_uri)
db = client1[db_name]
collection = db[collection_name]

# Fetch and print sentiment data
# print(sentiment_analysis.fetch_sentiment_data(client, ['AAPL'], days=5))
print(sentiment_analysis.get_sentiment_by_ticker(mongo_uri, db, collection, 'AAPL'))