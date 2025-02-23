import numpy as np
import yfinance as yf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

MODEL_PATH = "./data/lstm_model.h5"  # Change this to your actual model path
model = load_model(MODEL_PATH)

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