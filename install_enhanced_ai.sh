#!/bin/bash
# Install Enhanced AI/ML dependencies for SmartBot

echo "🚀 Installing SmartBot Enhanced AI/ML Dependencies"
echo "=================================================="

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install Python 3 first."
    exit 1
fi

echo ""
echo "📦 Installing core ML dependencies..."
pip3 install --upgrade pandas numpy scikit-learn joblib

echo ""
echo "📦 Installing deep learning (TensorFlow)..."
echo "   Note: Installing CPU version. For GPU, install tensorflow-gpu separately."
pip3 install tensorflow-cpu || pip3 install tensorflow

echo ""
echo "📦 Installing NLP for sentiment analysis..."
pip3 install textblob
python3 -m textblob.download_corpora

echo ""
echo "📦 Installing additional dependencies..."
pip3 install yfinance requests pytz

echo ""
echo "=================================================="
echo "✅ Installation complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Train deep learning model:"
echo "      python3 ml/train_deep_model.py"
echo ""
echo "   2. Test sentiment analysis:"
echo "      python3 ml/sentiment_analysis.py"
echo ""
echo "   3. Run backtests:"
echo "      python3 ml/backtesting.py"
echo ""
echo "   4. Generate enhanced dashboard:"
echo "      python3 generate_enhanced_dashboard.py"
echo ""
echo "🚀 SmartBot is ready for ultra-aggressive Monday trading!"
