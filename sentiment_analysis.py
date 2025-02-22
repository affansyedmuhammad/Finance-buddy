from polygon import RESTClient
import pandas as pd
from datetime import datetime, timedelta
import time
import json

def fetch_sentiment_data(client, company_tickers, days=5):
    """
    Fetches news sentiment data for a list of stock tickers from Polygon.io.
    """
    # Initialize Polygon.io client
    sentiment_data = []

    # Define date range
    end_date = (datetime.today() - timedelta(days=2)).strftime('%Y-%m-%d')  # Yesterday
    start_date = (datetime.today() - timedelta(days=days)).strftime('%Y-%m-%d')  # Past 'days' days

    for ticker in company_tickers:
        for day in pd.date_range(start=start_date, end=end_date):
            try:
                # Fetch news articles for the given date
                daily_news = list(client.list_ticker_news(ticker=ticker, published_utc=day.strftime("%Y-%m-%d"), limit=100))
                
                # Extract sentiment insights from articles
                for article in daily_news:
                    if hasattr(article, 'insights') and article.insights:
                        for insight in article.insights:
                            sentiment_entry = {
                                "date": day.strftime("%Y-%m-%d"),
                                "sentiment": insight.sentiment,
                                "sentiment_reasoning": insight.sentiment_reasoning,
                                "ticker": ticker
                            }
                            sentiment_data.append(sentiment_entry)

                print(f"Processed sentiment data for {ticker} on {day.strftime('%Y-%m-%d')}")

            except Exception as e:
                print(f"Error processing {ticker} on {day.strftime('%Y-%m-%d')}: {e}")

    return sentiment_data

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

