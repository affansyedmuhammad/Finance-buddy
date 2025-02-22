import numpy as np
import pandas as pd
import yfinance as yf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler


MODEL_PATH = "lstm_model.h5"  # Change this to your actual model path
model = load_model(MODEL_PATH)

def get_stock_data(ticker, days=60):
    """
    Fetches the last 'days' of stock data from Yahoo Finance.
    """
    stock_data = yf.download(ticker, period=f"{days}d", interval="1d")
    return stock_data[['Close']]

# Example: Fetch last 60 days of AAPL stock data
ticker = "AAPL"
stock_df = get_stock_data(ticker)

scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(stock_df)
last_60_days = scaled_data[-60:]  # Extract last 60 days
input_data = np.reshape(last_60_days, (1, last_60_days.shape[0], 1))  # Reshape for LSTM
predicted_price = model.predict(input_data)
predicted_price = scaler.inverse_transform(predicted_price)

print(f"Predicted Closing Price for {ticker}: ${predicted_price[0][0]:.2f}")