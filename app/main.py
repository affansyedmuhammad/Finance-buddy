from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from polygon import RESTClient
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import yfinance as yf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import pymongo
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json

# Disable TensorFlow ONEDNN logs
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

MODEL_PATH = "./app/data/lstm_model.h5"  # Change this to your actual model path
model = load_model(MODEL_PATH)

# Load environment variables
load_dotenv()
polygon_api_key = os.getenv("POLYGON_API_KEY")
mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME")
collection_sentiment = os.getenv("COLLECTION_SENTIMENT")
collection_corelation = os.getenv("COLLECTION_CORELEATION")
llm_api_key = os.getenv("LLM_API_KEY")

# Initialize clients
client = RESTClient(api_key=polygon_api_key)
mongo_client = pymongo.MongoClient(mongo_uri)
db = mongo_client[db_name]
collection_sentiment_db = db[collection_sentiment]
collection_corelation_db = db[collection_corelation]
genai.configure(api_key=llm_api_key)

# Initialize FastAPI app
app = FastAPI()

# Request model for API input
class StockRequest(BaseModel):
    user_input: str

@app.get("/")
def health_check():
    """
    FastAPI endpoint for health check.
    """
    return {"status": "Stock recommendation service is running."}

@app.get("/stock_recommendation")
def stock_recommendation(user_input: str):
    """
    FastAPI endpoint that processes user input and returns a stock recommendation.
    """
    if not user_input:
        return "Please enter which stock you want to analyze?"
    try:
        # Extract ticker from user input using Gemini AI
        prompt = (
            f"You are a stock trading assistant. Extract the NASDAQ-100 company ticker symbol "
            f"and the action the user wants to perform from the following input: '{user_input}'.\n\n"
            f"Return the output in valid JSON format with two fields:\n"
            f'{{"ticker": "<ticker>", "action": "<action>"}}\n\n'
        )

        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        if response and response.candidates:
            json_response = response.candidates[0].content.parts[0].text.strip()
            stock_details = json.loads(json_response)  # Convert to JSON
        else:
            raise HTTPException(status_code=500, detail="No valid response from API.")

        # Extract ticker
        sample_ticker = stock_details.get("ticker")
        # print("Ticker being considered = "+sample_ticker)
        if not sample_ticker:
            raise HTTPException(status_code=400, detail="Failed to extract ticker from input.")

        # Fetch related stocks from MongoDB
        related_stocks = []
        result = collection_corelation_db.find_one({"ticker": sample_ticker})
        if result:
            related_stocks = result["correlations"]
        related_stocks.insert(0, sample_ticker)
        print("list of Ticker being considered = ",related_stocks)
        # Get predicted prices & sentiment analysis
        predicted_closing_rate = {}
        sentiment_analysis_results = {}
        recommendation = []
        predicted_data_all= predict_stock_close_price()
        for stock in related_stocks[:5]:
            predicted_closing_rate[stock] = predicted_data_all[stock]
            sentiment_analysis_results[stock] = get_sentiment_by_ticker(
                mongo_uri, db, collection_sentiment_db, stock
            )
            # Get stock recommendation using LLM
            recommendation.append(get_stock_recommendation(stock, predicted_closing_rate[stock], sentiment_analysis_results[stock]))

        return recommendation

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing stock recommendation: {e}")

def get_stock_recommendation(stock_name, predictions, sentiment_summary):
    """
    Uses Gemini AI to generate stock recommendations (buy/sell/hold) based on predictions & sentiment.
    """
    prompt = (
        f"You are a stock trading assistant helping investors make decisions.\n"
        f"The user wants to make an investment decision for the stock '{stock_name}'.\n"
        f"Here is are the price prediction for next 5 days for {stock_name}: {predictions}.\n"
        f"Here is a summary of recent sentiment analysis for {stock_name}:\n"
        f"'{sentiment_summary}'\n\n"
        f"Based on this prediction data and sentiment, provide a recommendation. I want you to build your response on the sentiment and sentiment_reasoning field to give a description which provides an answer based on historical data and why a certain descision is being made.\n"
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
                return {"error": "Gemini API did not return valid JSON."}
        else:
            return {"error": "No valid response from Gemini API."}

    except Exception as e:
        return {"error": f"Error calling Gemini API: {e}"}


def get_sentiment_by_ticker(mongo_uri, db_name, collection, ticker):
    """
    Fetch all sentiment data from MongoDB filtered by the given ticker.
    """
    try:
        # Query MongoDB for all records with the given ticker
        query = {"tikker": ticker}
        results = list(collection.find(query, {"_id": 0}))  # Exclude _id field from results

        return results

    except Exception as e:
        print(f"Error retrieving data: {e}")
        return []
    
def get_stock_data(tickers, days=60):
    """
    Fetches the last 'days' of stock closing price data from Yahoo Finance for multiple stocks.
    """
    stock_data = yf.download(tickers, period=f"{days}d", interval="1d")['Close']
    return stock_data

def predict_stock_close_price():
    # NASDAQ100
    tickers = ["AAPL", "ABNB", "ADBE", "ADI", "ADP", "ADSK", "AEP", "ALGN", "AMAT",
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
        "WBA", "WDAY", "XEL", "ZM"]  
    stock_df = get_stock_data(tickers)

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(stock_df)  # Scale entire dataset

    # Ensure we have at least 60 days of data
    if len(scaled_data) < 60:
        raise ValueError("Not enough data! Model expects at least 60 time steps.")

    # Extract the last 60 days for prediction
    last_60_days = scaled_data[-60:].tolist()  # Convert to list for manipulation
    predictions_scaled = []

    days_to_predict = 5

    for _ in range(days_to_predict):
        input_data = np.reshape(last_60_days, (1, 60, len(tickers)))  # Reshape for LSTM
        predicted_price = model.predict(input_data)  # Predict next day's prices

        predictions_scaled.append(predicted_price[0])  # Store scaled predictions
        last_60_days.pop(0)  # Remove oldest day
        last_60_days.append(predicted_price[0].tolist())  # Append predicted day

    predictions_actual = scaler.inverse_transform(predictions_scaled)

    # Print the predicted stock prices for the next 5 days
    predictions_by_ticker = {ticker: [] for ticker in tickers}

    # Organize predictions by ticker
    for day_prices in predictions_actual:
        for i, ticker in enumerate(tickers):
            predictions_by_ticker[ticker].append(float(day_prices[i]))
    return predictions_by_ticker