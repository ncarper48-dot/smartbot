"""
Advanced Backtesting & Auto-Optimization Module
Continuous strategy testing and optimization
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict

class StrategyBacktester:
    """
    Backtest trading strategies and optimize parameters
    """
    def __init__(self):
        self.results_file = "ml/backtest_results.json"
        self.results = self.load_results()
        
    def load_results(self):
        """Load previous backtest results"""
        if os.path.exists(self.results_file):
            try:
                with open(self.results_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_results(self):
        """Save backtest results"""
        try:
            with open(self.results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving results: {e}")
    
    def calculate_indicators(self, df):
        """Calculate all technical indicators"""
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['BB_Upper'] = df['SMA_20'] + 2 * df['Close'].rolling(window=20).std()
        df['BB_Lower'] = df['SMA_20'] - 2 * df['Close'].rolling(window=20).std()
        
        # Moving Averages
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # Volume
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        
        return df
    
    def generate_signals(self, df, params):
        """Generate trading signals based on parameters"""
        signals = []
        
        for i in range(len(df)):
            signal = 0
            confidence = 0.0
            
            # RSI Strategy
            if df['RSI'].iloc[i] < params['rsi_oversold']:
                signal += 1
                confidence += 0.3
            elif df['RSI'].iloc[i] > params['rsi_overbought']:
                signal -= 1
                confidence += 0.3
            
            # MACD Strategy
            if df['MACD'].iloc[i] > df['MACD_Signal'].iloc[i]:
                signal += 1
                confidence += 0.2
            elif df['MACD'].iloc[i] < df['MACD_Signal'].iloc[i]:
                signal -= 1
                confidence += 0.2
            
            # Bollinger Bands
            if df['Close'].iloc[i] < df['BB_Lower'].iloc[i]:
                signal += 1
                confidence += 0.25
            elif df['Close'].iloc[i] > df['BB_Upper'].iloc[i]:
                signal -= 1
                confidence += 0.25
            
            # Moving Average Crossover
            if df['SMA_50'].iloc[i] > df['SMA_200'].iloc[i]:
                signal += 1
                confidence += 0.25
            elif df['SMA_50'].iloc[i] < df['SMA_200'].iloc[i]:
                signal -= 1
                confidence += 0.25
            
            # Normalize signal
            if signal > 1:
                final_signal = 1
            elif signal < -1:
                final_signal = -1
            else:
                final_signal = 0
            
            signals.append({
                'signal': final_signal,
                'confidence': min(confidence, 1.0)
            })
        
        return signals
    
    def simulate_trades(self, df, signals, params):
        """Simulate trading based on signals"""
        initial_capital = 10000
        capital = initial_capital
        position = 0
        position_price = 0
        trades = []
        
        for i in range(len(df)):
            current_price = df['Close'].iloc[i]
            signal = signals[i]['signal']
            confidence = signals[i]['confidence']
            
            # Buy signal
            if signal == 1 and position == 0 and confidence > params['confidence_threshold']:
                shares = int((capital * params['position_size']) / current_price)
                if shares > 0:
                    position = shares
                    position_price = current_price
                    cost = shares * current_price
                    capital -= cost
                    
                    trades.append({
                        'type': 'buy',
                        'price': current_price,
                        'shares': shares,
                        'date': df.index[i],
                        'capital': capital
                    })
            
            # Sell signal or stop loss
            elif position > 0:
                should_sell = False
                
                # Sell signal
                if signal == -1 and confidence > params['confidence_threshold']:
                    should_sell = True
                    reason = 'signal'
                
                # Take profit
                elif current_price > position_price * (1 + params['take_profit']):
                    should_sell = True
                    reason = 'take_profit'
                
                # Stop loss
                elif current_price < position_price * (1 - params['stop_loss']):
                    should_sell = True
                    reason = 'stop_loss'
                
                if should_sell:
                    revenue = position * current_price
                    capital += revenue
                    profit = revenue - (position * position_price)
                    
                    trades.append({
                        'type': 'sell',
                        'price': current_price,
                        'shares': position,
                        'date': df.index[i],
                        'capital': capital,
                        'profit': profit,
                        'return': (profit / (position * position_price)) * 100,
                        'reason': reason
                    })
                    
                    position = 0
                    position_price = 0
        
        # Close any open position
        if position > 0:
            revenue = position * df['Close'].iloc[-1]
            capital += revenue
            profit = revenue - (position * position_price)
            trades.append({
                'type': 'sell',
                'price': df['Close'].iloc[-1],
                'shares': position,
                'date': df.index[-1],
                'capital': capital,
                'profit': profit,
                'return': (profit / (position * position_price)) * 100,
                'reason': 'final'
            })
        
        return trades, capital
    
    def calculate_metrics(self, trades, final_capital, initial_capital=10000):
        """Calculate performance metrics"""
        if not trades:
            return None
        
        total_trades = len([t for t in trades if t['type'] == 'sell'])
        if total_trades == 0:
            return None
        
        winning_trades = [t for t in trades if t['type'] == 'sell' and t.get('profit', 0) > 0]
        losing_trades = [t for t in trades if t['type'] == 'sell' and t.get('profit', 0) < 0]
        
        total_return = ((final_capital - initial_capital) / initial_capital) * 100
        win_rate = (len(winning_trades) / total_trades) * 100
        
        avg_win = np.mean([t['profit'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t['profit']) for t in losing_trades]) if losing_trades else 0
        
        profit_factor = (sum(t['profit'] for t in winning_trades) / 
                        sum(abs(t['profit']) for t in losing_trades)) if losing_trades else float('inf')
        
        returns = [t.get('return', 0) for t in trades if t['type'] == 'sell']
        sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if len(returns) > 1 else 0
        
        max_drawdown = 0
        peak = initial_capital
        for trade in trades:
            current_capital = trade.get('capital', initial_capital)
            if current_capital > peak:
                peak = current_capital
            drawdown = ((peak - current_capital) / peak) * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            'total_return': total_return,
            'final_capital': final_capital,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown
        }
    
    def backtest_symbol(self, symbol, period='1y', params=None):
        """Backtest strategy on a single symbol"""
        if params is None:
            params = {
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'confidence_threshold': 0.20,
                'position_size': 0.35,
                'take_profit': 0.015,
                'stop_loss': 0.008
            }
        
        try:
            # Download data
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            
            if len(df) < 100:
                return None
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            df = df.dropna()
            
            # Generate signals
            signals = self.generate_signals(df, params)
            
            # Simulate trades
            trades, final_capital = self.simulate_trades(df, signals, params)
            
            # Calculate metrics
            metrics = self.calculate_metrics(trades, final_capital)
            
            if metrics:
                metrics['symbol'] = symbol
                metrics['period'] = period
                metrics['params'] = params
                metrics['timestamp'] = datetime.now().isoformat()
            
            return metrics
            
        except Exception as e:
            print(f"⚠️ Error backtesting {symbol}: {e}")
            return None
    
    def optimize_parameters(self, symbol, period='1y'):
        """Optimize strategy parameters for best performance"""
        best_result = None
        best_score = -float('inf')
        
        # Parameter grid
        rsi_levels = [(25, 75), (30, 70), (35, 65)]
        confidence_levels = [0.15, 0.20, 0.25]
        position_sizes = [0.3, 0.35, 0.4]
        take_profits = [0.01, 0.015, 0.02]
        stop_losses = [0.006, 0.008, 0.01]
        
        print(f"🔍 Optimizing parameters for {symbol}...")
        
        for rsi in rsi_levels:
            for conf in confidence_levels:
                for pos_size in position_sizes:
                    for tp in take_profits:
                        for sl in stop_losses:
                            params = {
                                'rsi_oversold': rsi[0],
                                'rsi_overbought': rsi[1],
                                'confidence_threshold': conf,
                                'position_size': pos_size,
                                'take_profit': tp,
                                'stop_loss': sl
                            }
                            
                            result = self.backtest_symbol(symbol, period, params)
                            
                            if result and result['total_trades'] > 5:
                                # Score based on return, win rate, and Sharpe ratio
                                score = (result['total_return'] * 0.5 + 
                                        result['win_rate'] * 0.3 + 
                                        result['sharpe_ratio'] * 10 * 0.2)
                                
                                if score > best_score:
                                    best_score = score
                                    best_result = result
        
        return best_result
    
    def run_multi_symbol_backtest(self, symbols, period='1y'):
        """Run backtest on multiple symbols"""
        print("🚀 Running Multi-Symbol Backtest")
        print("=" * 60)
        
        results = []
        for symbol in symbols:
            print(f"\n📊 Backtesting {symbol}...")
            result = self.backtest_symbol(symbol, period)
            
            if result:
                results.append(result)
                print(f"  Return: {result['total_return']:.2f}%")
                print(f"  Win Rate: {result['win_rate']:.1f}%")
                print(f"  Sharpe: {result['sharpe_ratio']:.2f}")
                
                # Save result
                self.results[f"{symbol}_{period}"] = result
        
        self.save_results()
        
        # Summary
        if results:
            avg_return = np.mean([r['total_return'] for r in results])
            avg_winrate = np.mean([r['win_rate'] for r in results])
            print(f"\n{'=' * 60}")
            print(f"📈 Average Return: {avg_return:.2f}%")
            print(f"🎯 Average Win Rate: {avg_winrate:.1f}%")
        
        return results


# Quick backtest function
def quick_backtest(symbol, period='1y'):
    """Quick backtest for a symbol"""
    backtester = StrategyBacktester()
    return backtester.backtest_symbol(symbol, period)


if __name__ == "__main__":
    print("📊 SmartBot Backtesting System")
    print("=" * 60)
    
    backtester = StrategyBacktester()
    
    # Test symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    results = backtester.run_multi_symbol_backtest(test_symbols, period='6mo')
    
    print(f"\n✅ Backtest complete! Results saved to {backtester.results_file}")
