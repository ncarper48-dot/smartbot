"""
News & Sentiment Analysis Module for SmartBot
Real-time market sentiment from news and social media
"""

import requests
import json
from datetime import datetime, timedelta
import os
from textblob import TextBlob  # For sentiment analysis
import yfinance as yf

class SentimentAnalyzer:
    """
    Analyze market sentiment from news and social sources
    """
    def __init__(self):
        self.cache_file = "ml/sentiment_cache.json"
        self.sentiment_data = self.load_cache()
        
    def load_cache(self):
        """Load cached sentiment data"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_cache(self):
        """Save sentiment data to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.sentiment_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving sentiment cache: {e}")
    
    def analyze_text(self, text):
        """Analyze sentiment of text using TextBlob"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Classify sentiment
            if polarity > 0.1:
                sentiment = "positive"
            elif polarity < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return {
                'sentiment': sentiment,
                'polarity': polarity,
                'subjectivity': subjectivity,
                'confidence': abs(polarity)
            }
        except:
            return None
    
    def get_stock_news(self, symbol):
        """Get recent news for a stock symbol"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return []
            
            analyzed_news = []
            for item in news[:10]:  # Analyze top 10 news items
                title = item.get('title', '')
                if title:
                    sentiment = self.analyze_text(title)
                    if sentiment:
                        analyzed_news.append({
                            'title': title,
                            'timestamp': item.get('providerPublishTime', 0),
                            'sentiment': sentiment['sentiment'],
                            'polarity': sentiment['polarity']
                        })
            
            return analyzed_news
            
        except Exception as e:
            print(f"⚠️ Error fetching news for {symbol}: {e}")
            return []
    
    def get_market_sentiment(self, symbol):
        """
        Get overall market sentiment for a symbol
        Returns: sentiment_score (-1 to 1), signal strength (0 to 1)
        """
        news = self.get_stock_news(symbol)
        
        if not news:
            return 0.0, 0.0  # Neutral, low confidence
        
        # Calculate average sentiment
        polarities = [item['polarity'] for item in news]
        avg_polarity = sum(polarities) / len(polarities)
        
        # Calculate signal strength based on consistency
        sentiment_consistency = 1 - (sum(abs(p - avg_polarity) for p in polarities) / len(polarities) / 2)
        
        # Cache the result
        self.sentiment_data[symbol] = {
            'timestamp': datetime.now().isoformat(),
            'sentiment_score': avg_polarity,
            'signal_strength': sentiment_consistency,
            'news_count': len(news),
            'latest_news': news[:3]  # Store top 3 for reference
        }
        self.save_cache()
        
        return avg_polarity, sentiment_consistency
    
    def get_sentiment_signal(self, symbol):
        """
        Generate trading signal based on sentiment
        Returns: (signal, confidence, details)
        """
        sentiment_score, strength = self.get_market_sentiment(symbol)
        
        # Generate signal
        if sentiment_score > 0.15 and strength > 0.5:
            signal = 1  # Buy - positive news
            confidence = min(sentiment_score * strength, 1.0)
        elif sentiment_score < -0.15 and strength > 0.5:
            signal = -1  # Sell - negative news
            confidence = min(abs(sentiment_score) * strength, 1.0)
        else:
            signal = 0  # Hold - neutral or weak signal
            confidence = 0.0
        
        details = {
            'sentiment_score': sentiment_score,
            'signal_strength': strength,
            'recent_news': self.sentiment_data.get(symbol, {}).get('latest_news', [])
        }
        
        return signal, confidence, details


class MarketMoodAnalyzer:
    """
    Analyze overall market mood from major indices
    """
    def __init__(self):
        self.indices = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^IXIC': 'NASDAQ',
            '^VIX': 'VIX (Fear Index)'
        }
    
    def get_market_mood(self):
        """
        Analyze overall market mood
        Returns: mood score (-1 to 1), description
        """
        try:
            moods = []
            
            for symbol, name in self.indices.items():
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='5d')
                
                if len(hist) > 1:
                    # Calculate momentum (use positional indexing)
                    close = hist['Close']
                    price_change = (close.iloc[-1] - close.iloc[0]) / close.iloc[0]
                    
                    # VIX is inverse (higher VIX = more fear)
                    if symbol == '^VIX':
                        price_change = -price_change
                    
                    moods.append(price_change)
            
            if not moods:
                return 0.0, "Unknown"
            
            avg_mood = sum(moods) / len(moods)
            
            # Classify mood
            if avg_mood > 0.02:
                description = "🚀 Bullish - Strong positive momentum"
            elif avg_mood > 0.01:
                description = "📈 Optimistic - Moderate gains"
            elif avg_mood > -0.01:
                description = "😐 Neutral - Sideways market"
            elif avg_mood > -0.02:
                description = "📉 Cautious - Slight decline"
            else:
                description = "🐻 Bearish - Strong negative momentum"
            
            return avg_mood, description
            
        except Exception as e:
            print(f"⚠️ Error analyzing market mood: {e}")
            return 0.0, "Error"
    
    def should_trade_today(self):
        """
        Determine if market conditions are favorable for trading
        Returns: (should_trade, reason)
        """
        mood, description = self.get_market_mood()
        
        # Don't trade in extreme fear
        if mood < -0.03:
            return False, f"Market too bearish: {description}"
        
        # Be cautious in high volatility
        try:
            vix = yf.Ticker('^VIX')
            vix_hist = vix.history(period='1d')
            if not vix_hist.empty:
                vix_value = vix_hist['Close'].iloc[-1]
            else:
                vix_value = None
            
            if vix_value is not None and vix_value > 30:
                return False, f"VIX too high ({vix_value:.1f}) - High volatility"
        except:
            pass
        
        return True, f"Market conditions favorable: {description}"


# Sentiment scoring function for easy integration
def get_sentiment_boost(symbol):
    """
    Quick function to get sentiment boost for trading decisions
    Returns: boost_factor (0.8 to 1.2), confidence
    """
    try:
        analyzer = SentimentAnalyzer()
        signal, confidence, details = analyzer.get_sentiment_signal(symbol)
        
        # Convert signal to boost factor
        boost = 1.0 + (signal * confidence * 0.2)  # Max ±20% boost
        
        return boost, confidence
        
    except Exception as e:
        print(f"⚠️ Sentiment analysis error: {e}")
        return 1.0, 0.0


# Test functionality
if __name__ == "__main__":
    print("📰 SmartBot Sentiment Analysis")
    print("=" * 60)
    
    # Test sentiment analysis
    analyzer = SentimentAnalyzer()
    
    test_symbols = ['AAPL', 'TSLA', 'NVDA']
    print("\n📊 Stock Sentiment Analysis:")
    for symbol in test_symbols:
        signal, conf, details = analyzer.get_sentiment_signal(symbol)
        print(f"\n  {symbol}:")
        print(f"    Signal: {signal} | Confidence: {conf:.2f}")
        print(f"    Sentiment Score: {details['sentiment_score']:.3f}")
        
    # Test market mood
    print("\n\n🌐 Overall Market Mood:")
    mood_analyzer = MarketMoodAnalyzer()
    mood, description = mood_analyzer.get_market_mood()
    print(f"  Mood Score: {mood:.3f}")
    print(f"  {description}")
    
    should_trade, reason = mood_analyzer.should_trade_today()
    print(f"\n  Should Trade: {'✅ Yes' if should_trade else '❌ No'}")
    print(f"  Reason: {reason}")
