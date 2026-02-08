#!/usr/bin/env python3
"""
SmartBot System Upgrade & Verification
Tests all new AI/ML features and generates reports
"""

import os
import sys
import json
from datetime import datetime

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def test_deep_learning():
    """Test deep learning module"""
    print_header("🤖 Testing Deep Learning Module")
    
    try:
        from ml.deep_learning_model import DeepLearningPredictor, EnsemblePredictor, KERAS_AVAILABLE
        
        if not KERAS_AVAILABLE:
            print("⚠️  TensorFlow not installed")
            print("   Install with: pip install tensorflow-cpu")
            return False
        
        print("✅ TensorFlow available")
        
        # Test predictor
        predictor = DeepLearningPredictor()
        print(f"✅ Deep learning predictor initialized")
        
        # Test ensemble
        ensemble = EnsemblePredictor()
        print(f"✅ Ensemble predictor initialized")
        
        if predictor.load_model():
            print("✅ Pre-trained LSTM model loaded")
        else:
            print("⚠️  No trained model found - train with: python3 ml/train_deep_model.py")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_sentiment_analysis():
    """Test sentiment analysis"""
    print_header("📰 Testing Sentiment Analysis")
    
    try:
        from ml.sentiment_analysis import SentimentAnalyzer, MarketMoodAnalyzer, get_sentiment_boost
        
        print("✅ Sentiment modules imported")
        
        # Test sentiment analyzer
        analyzer = SentimentAnalyzer()
        print("✅ Sentiment analyzer initialized")
        
        # Test market mood
        mood_analyzer = MarketMoodAnalyzer()
        mood, description = mood_analyzer.get_market_mood()
        print(f"✅ Market mood: {description} (Score: {mood:.3f})")
        
        should_trade, reason = mood_analyzer.should_trade_today()
        print(f"{'✅' if should_trade else '⚠️ '} Trading recommendation: {reason}")
        
        # Test sentiment boost
        boost, conf = get_sentiment_boost("AAPL")
        print(f"✅ Sentiment boost for AAPL: {boost:.2f}x (confidence: {conf:.2f})")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Install with: pip install textblob")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_backtesting():
    """Test backtesting module"""
    print_header("📊 Testing Backtesting Module")
    
    try:
        from ml.backtesting import StrategyBacktester, quick_backtest
        
        print("✅ Backtesting modules imported")
        
        # Test backtester
        backtester = StrategyBacktester()
        print("✅ Backtester initialized")
        
        # Quick test
        print("📊 Running quick backtest on AAPL (6 months)...")
        result = quick_backtest("AAPL", period="6mo")
        
        if result:
            print(f"✅ Backtest complete:")
            print(f"   Total Return: {result['total_return']:.2f}%")
            print(f"   Win Rate: {result['win_rate']:.1f}%")
            print(f"   Sharpe Ratio: {result['sharpe_ratio']:.2f}")
            print(f"   Total Trades: {result['total_trades']}")
        else:
            print("⚠️  Backtest returned no results")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_live_trader_integration():
    """Test live trader AI integration"""
    print_header("🔗 Testing Live Trader AI Integration")
    
    try:
        # Check if enhanced AI is available in live_trader
        with open("live_trader.py", "r") as f:
            content = f.read()
        
        if "ENHANCED_AI_AVAILABLE" in content:
            print("✅ Enhanced AI integration found in live_trader.py")
        else:
            print("⚠️  Enhanced AI not integrated in live_trader.py")
            return False
        
        if "EnsemblePredictor" in content:
            print("✅ Ensemble predictor integration found")
        else:
            print("⚠️  Ensemble predictor not integrated")
        
        if "get_sentiment_boost" in content:
            print("✅ Sentiment analysis integration found")
        else:
            print("⚠️  Sentiment analysis not integrated")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def generate_system_report():
    """Generate comprehensive system report"""
    print_header("📋 Generating System Report")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "smartbot_version": "Pro v2.0 - Enhanced AI Edition",
        "features": {
            "deep_learning": False,
            "sentiment_analysis": False,
            "backtesting": True,
            "ensemble_ai": False,
            "live_integration": False
        },
        "status": "READY",
        "recommendations": []
    }
    
    # Test each feature
    report["features"]["deep_learning"] = test_deep_learning()
    report["features"]["sentiment_analysis"] = test_sentiment_analysis()
    report["features"]["backtesting"] = test_backtesting()
    report["features"]["live_integration"] = test_live_trader_integration()
    
    # Generate recommendations
    if not report["features"]["deep_learning"]:
        report["recommendations"].append("Install TensorFlow: pip install tensorflow-cpu")
        report["recommendations"].append("Train LSTM model: python3 ml/train_deep_model.py")
    
    if not report["features"]["sentiment_analysis"]:
        report["recommendations"].append("Install TextBlob: pip install textblob")
    
    # Calculate overall readiness
    total_features = len(report["features"])
    enabled_features = sum(report["features"].values())
    readiness = (enabled_features / total_features) * 100
    
    report["readiness"] = readiness
    
    if readiness >= 80:
        report["status"] = "🚀 READY FOR TRADING"
    elif readiness >= 50:
        report["status"] = "⚠️  PARTIAL - Some features missing"
    else:
        report["status"] = "❌ NOT READY - Install dependencies"
    
    # Save report
    report_file = f"ml/system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Report saved to: {report_file}")
    
    return report

def main():
    """Main system check"""
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "🚀 SmartBot Pro System Check" + " " * 18 + "║")
    print("║" + " " * 12 + "Enhanced AI/ML Edition" + " " * 23 + "║")
    print("╚" + "═" * 58 + "╝")
    
    report = generate_system_report()
    
    # Print summary
    print_header("📊 System Summary")
    print(f"Status: {report['status']}")
    print(f"Readiness: {report['readiness']:.0f}%")
    print(f"\nFeatures:")
    for feature, enabled in report['features'].items():
        status = "✅" if enabled else "❌"
        print(f"  {status} {feature.replace('_', ' ').title()}")
    
    if report['recommendations']:
        print(f"\n🔧 Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    print_header("🎯 Next Steps for Monday Trading")
    print("1. Run installation script: bash install_enhanced_ai.sh")
    print("2. Train models if needed: python3 ml/train_deep_model.py")
    print("3. Generate enhanced dashboard: python3 generate_enhanced_dashboard.py")
    print("4. Restart SmartBot: sudo systemctl restart smartbot_live_trader")
    print("5. Monitor dashboard: http://localhost:8000/status_dashboard_pro.html")
    
    print("\n" + "=" * 60)
    print("🚀 SmartBot is working hard to be THE BEST!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
