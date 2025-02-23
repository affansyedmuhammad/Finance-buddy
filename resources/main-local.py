import compute_stock_relation
import sentiment_analysis
import predict_stock_price
from polygon import RESTClient
import pymongo
import os
from dotenv import load_dotenv
import google.generativeai as genai
import os
import json
import time

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
# Load environment variables from .env
load_dotenv()
# Retrieve sensitive data from environment variables
polygon_api_key = os.getenv("POLYGON_API_KEY")
mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME")
collection_sentiment = os.getenv("COLLECTION_SENTIMENT")
collection_corelation = os.getenv("COLLECTION_CORELEATION")
llm_api_key = os.getenv("LLM_API_KEY")
# Initialize Polygon Client
client = RESTClient(api_key=polygon_api_key)
# Initialize MongoDB Client
client1 = pymongo.MongoClient(mongo_uri)
db = client1[db_name]
collection_sentiment_db = db[collection_sentiment]
collection_corelation_db = db[collection_corelation]
genai.configure(api_key=llm_api_key)

def get_stock_details(user_input):
    prompt = (
        f"You are a stock trading assistant. Extract the NASDAQ-100 company ticker symbol "
        f"and the action the user wants to perform from the following input: '{user_input}'.\n\n"
        f"Return the output in *valid JSON format* with two fields:\n"
        f'{{"ticker": "<ticker>", "action": "<action>"}}\n\n'
        f"Examples:\n"
        f'"I want to invest in Tesla" → {{"ticker": "TSLA", "action": "buy"}}\n'
        f'"Should I sell my Amazon stock?" → {{"ticker": "AMZN", "action": "sell"}}\n'
        f'"Is Microsoft a good investment?" → {{"ticker": "MSFT", "action": "analyze"}}\n'
        f'"Should I hold onto my Nvidia shares?" → {{"ticker": "NVDA", "action": "hold"}}\n'
        f'"What is the latest update on Apple?" → {{"ticker": "AAPL", "action": "news"}}\n\n'
        f"Ensure the response is only valid JSON and nothing else."
    )

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)

        if response and response.candidates:
            json_response = response.candidates[0].content.parts[0].text.strip()
            return json_response  # Returns JSON as a string
        else:
            return "Error: No valid response from Gemini API."

    except Exception as e:
        return f"Error calling Gemini API: {e}"
    
def get_stock_recommendation(stock_name, predictions, sentiment_summary):
    """
    Sends structured stock data (T+5 predictions + sentiment) to LLM and gets an investment action recommendation.
    
    :param stock_name: Stock ticker symbol (e.g., "AAPL")
    :param predictions: List of T+5 price predictions (e.g., [174, 176, 180, 178, 185])
    :param sentiment_summary: Preprocessed key sentiment insights (e.g., "Apple reports record sales, demand strong")
    
    :return: JSON output with suggested action and reasoning.
    """
    
    prompt = (
        f"You are a stock trading assistant helping investors make decisions.\n"
        f"The user wants to make an investment decision for the stock '{stock_name}'.\n"
        f"Here is the T+5 price prediction for {stock_name}: {predictions}.\n"
        f"Here is a summary of recent sentiment analysis for {stock_name}:\n"
        f"'{sentiment_summary}'\n\n"
        f"Based on this prediction data and sentiment, provide a recommendation.\n"
        f"Return a JSON output in the format:\n"
        f'{{"stock_name": "<stock_ticker>", "action": "<buy/sell/hold>", "description": "<reasoning based on data>"}}\n\n'
        f"Make sure your response is only valid JSON and nothing else."
    )

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)

        if response and response.candidates:
            json_response = response.candidates[0].content.parts[0].text.strip()
            try:
                return json.loads(json_response)  # Convert to JSON dict
            except json.JSONDecodeError:
                return "Error: Gemini API did not return valid JSON."
        else:
            return "Error: No valid response from Gemini API."

    except Exception as e:
        return f"Error calling Gemini API: {e}"

sample_ticker = ""
related_stocks = []
predicted_closing_rate = {}  # Dictionary to store predicted closing prices
sentiment_analysis_results = {}  # Dictionary to store sentiment analysis results
request = "I want to invest in Google"


## logic for gpt to process frontend data and process to get trikker
result = json.loads(get_stock_details(request))
sample_ticker = result.get("ticker")  # Extracts the ticker symbol

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
    predicted_closing_rate[trikker] = predict_stock_price.predict_stock_close_price(trikker)

    # Fetch and store sentiment analysis results
    sentiment_analysis_results[trikker] = sentiment_analysis.get_sentiment_by_ticker(
        mongo_uri, db, collection_sentiment_db, trikker
    )
# print(predicted_closing_rate)
# print(sentiment_analysis_results)

## Add the logic for gpt to process predicted_closing_rate && sentiment_analysis_results and
## provide Buy or sell descison with reasoning

# Run LLM analysis for each stock
for stock in predicted_closing_rate.keys():
    print(f"Processing: {stock}")
    recommendation = get_stock_recommendation(stock, predicted_closing_rate[stock], sentiment_analysis_results[stock])
    print(json.dumps(recommendation, indent=4))
    print("-" * 50)
    time.sleep(5)