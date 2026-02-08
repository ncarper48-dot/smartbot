"""
Advanced Risk Management System
Features:
- Dynamic risk adjustment based on performance
- Position limits and concentration management
- Market regime detection (VIX, volatility)
- Trailing stops and profit targets
- Circuit breakers for max drawdown
"""

import os
import json
import yfinance as yf
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class AdvancedRiskManager:
    def __init__(self):
        self.base_risk = float(os.getenv('TRADING212_RISK_PER_TRADE', 0.12))
        self.max_positions = int(os.getenv('TRADING212_MAX_POSITIONS', 7))
        self.max_daily_loss_pct = float(os.getenv('TRADING212_MAX_DAILY_LOSS_PCT', 0.05))
        self.risk_state_file = 'risk_state.json'
        self.positions_file = 'open_positions.json'
        
        # Sector mappings for diversification
        self.sectors = {
            'TECH': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'NFLX'],
            'AUTO': ['TSLA', 'RIVN', 'LCID'],
            'ECOMMERCE': ['AMZN', 'SHOP', 'BABA'],
            'FINTECH': ['COIN', 'SQ', 'SOFI', 'HOOD'],
            'CRYPTO': ['MARA', 'RIOT', 'MSTR'],
            'GAMING': ['RBLX', 'DKNG'],
            'SERVICES': ['PLTR', 'ZM', 'SNAP', 'UPST', 'ROKU', 'DASH', 'CLOV', 'WISH']
        }
        
    def load_risk_state(self):
        """Load current risk state (consecutive wins/losses)"""
        if os.path.exists(self.risk_state_file):
            with open(self.risk_state_file, 'r') as f:
                return json.load(f)
        return {
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'daily_pnl': 0.0,
            'last_update': datetime.now().strftime('%Y-%m-%d')
        }
    
    def save_risk_state(self, state):
        """Save risk state"""
        with open(self.risk_state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_positions(self):
        """Load open positions"""
        if os.path.exists(self.positions_file):
            with open(self.positions_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_positions(self, positions):
        """Save open positions"""
        with open(self.positions_file, 'w') as f:
            json.dump(positions, f, indent=2)
    
    def get_dynamic_risk(self):
        """Adjust risk based on recent performance - CASH POT: REINVEST WINS IMMEDIATELY"""
        state = self.load_risk_state()
        
        # Check if new day
        today = datetime.now().strftime('%Y-%m-%d')
        if state['last_update'] != today:
            state['daily_pnl'] = 0.0
            state['last_update'] = today
            self.save_risk_state(state)
        
        # Check circuit breaker
        if state['daily_pnl'] <= -self.max_daily_loss_pct:
            print(f"⚠️ CIRCUIT BREAKER: Daily loss {state['daily_pnl']*100:.1f}% exceeds limit")
            return 0.0  # No new trades
        
        risk = self.base_risk
        
        # Scale down after consecutive losses
        if state['consecutive_losses'] >= 3:
            risk *= 0.6  # 60% of normal risk
            print(f"📉 Risk reduced to {risk*100:.1f}% after {state['consecutive_losses']} losses")
        elif state['consecutive_losses'] >= 2:
            risk *= 0.75  # 75% of normal risk
        
        # Scale up after consecutive wins - COMPOUND GAINS INTO BIGGER POSITIONS
        if state['consecutive_wins'] >= 3:
            risk *= 1.3  # 130% of normal risk - MORE AGGRESSIVE
            risk = min(risk, 0.28)  # Cap at 28% (was 15%) - BIGGER SWINGS!
            print(f"💰 CASH POT BOOST: Risk at {risk*100:.1f}% after {state['consecutive_wins']} wins! Compounding gains!")
        elif state['consecutive_wins'] >= 2:
            risk *= 1.15  # 115% after 2 wins
            print(f"📈 Risk boosted to {risk*100:.1f}% after {state['consecutive_wins']} wins")
        
        # REINVESTMENT: If daily profits are positive, add 5% of profits to position size
        if state['daily_pnl'] > 0:
            profit_boost = 1 + (state['daily_pnl'] * 0.05)  # 5% of profits
            risk *= profit_boost
            risk = min(risk, 0.30)  # Cap at 30% total
            print(f"💎 PROFIT REINVESTMENT: +{state['daily_pnl']*100:.1f}% gains → {risk*100:.1f}% position size!")
        
        return risk
    
    def check_position_limits(self, ticker):
        """Check if we can open a new position"""
        positions = self.load_positions()
        
        # Check total position count
        open_count = len([p for p in positions.values() if p.get('status') == 'OPEN'])
        if open_count >= self.max_positions:
            print(f"⚠️ Position limit reached: {open_count}/{self.max_positions}")
            return False
        
        # Check sector concentration
        ticker_sector = None
        for sector, tickers in self.sectors.items():
            if ticker in tickers:
                ticker_sector = sector
                break
        
        if ticker_sector:
            sector_count = sum(1 for p in positions.values() 
                             if p.get('status') == 'OPEN' and p.get('ticker') in self.sectors.get(ticker_sector, []))
            if sector_count >= 2:
                print(f"⚠️ Sector limit reached for {ticker_sector}: {sector_count}/2")
                return False
        
        return True
    
    def get_market_regime(self):
        """Detect market regime (trending, choppy, volatile)"""
        try:
            # Fetch VIX for volatility
            vix = yf.Ticker("^VIX")
            vix_data = vix.history(period='5d', interval='1d')
            
            if vix_data.empty:
                return 'NORMAL', 1.0
            
            current_vix = vix_data['Close'].iloc[-1]
            
            # Fetch SPY for market trend
            spy = yf.Ticker("SPY")
            spy_data = spy.history(period='30d', interval='1d')
            
            if len(spy_data) < 20:
                return 'NORMAL', 1.0
            
            # Calculate ADX-like trend strength
            spy_data['SMA_10'] = spy_data['Close'].rolling(10).mean()
            spy_data['SMA_20'] = spy_data['Close'].rolling(20).mean()
            
            trend_strength = abs(spy_data['SMA_10'].iloc[-1] - spy_data['SMA_20'].iloc[-1]) / spy_data['Close'].iloc[-1]
            
            # Determine regime
            if current_vix > 30:
                print(f"⚠️ HIGH VOLATILITY: VIX={current_vix:.1f}")
                return 'VOLATILE', 0.5  # Reduce aggression by 50%
            elif current_vix > 20:
                print(f"📊 ELEVATED VOLATILITY: VIX={current_vix:.1f}")
                return 'CHOPPY', 0.75  # Reduce aggression by 25%
            elif trend_strength > 0.03:
                print(f"📈 STRONG TREND: Trend strength={trend_strength:.3f}")
                return 'TRENDING', 1.2  # Increase aggression by 20%
            else:
                return 'NORMAL', 1.0
                
        except Exception as e:
            print(f"Market regime detection failed: {e}")
            return 'NORMAL', 1.0
    
    def calculate_trailing_stop(self, entry_price, current_price, atr):
        """Calculate trailing stop loss"""
        gain_pct = (current_price - entry_price) / entry_price
        
        # Move to breakeven after 1% gain
        if gain_pct >= 0.01:
            return max(entry_price, entry_price + (atr * 0.5))
        
        # Standard stop at 2*ATR
        return entry_price - (atr * 2)
    
    def calculate_profit_target(self, entry_price, atr, risk_reward_ratio=1.0):
        """Calculate profit target based on risk:reward - ULTRA AGGRESSIVE 1.0:1 for FAST CASH"""
        risk = atr * 2  # Stop loss distance
        target_price = entry_price + (risk * risk_reward_ratio)
        return target_price
    
    def should_take_partial_profit(self, entry_price, current_price, atr):
        """Check if we should take partial profits (70% at 0.5:1) - ULTRA AGGRESSIVE FOR CASH POT"""
        risk = atr * 2
        target_half = entry_price + (risk * 0.5)  # Take profits at 50% of risk distance (1-1.5% gains)
        
        if current_price >= target_half:
            return True, 0.7  # Take 70% profit at just 1-1.5% gain - LOCK IT IN!
        
        return False, 0
    
    def update_trade_result(self, ticker, pnl):
        """Update risk state after trade closes"""
        state = self.load_risk_state()
        
        # Update daily P&L
        state['daily_pnl'] += pnl
        
        # Update win/loss streak
        if pnl > 0:
            state['consecutive_wins'] += 1
            state['consecutive_losses'] = 0
            print(f"✅ Win! Streak: {state['consecutive_wins']}")
        else:
            state['consecutive_losses'] += 1
            state['consecutive_wins'] = 0
            print(f"❌ Loss! Streak: {state['consecutive_losses']}")
        
        self.save_risk_state(state)
    
    def add_position(self, ticker, quantity, entry_price, atr, strategy, stop_loss=None, profit_target=None):
        """Track new position"""
        positions = self.load_positions()
        
        stop_loss_value = stop_loss if stop_loss is not None else entry_price - (atr * 2)
        profit_target_value = profit_target if profit_target is not None else entry_price + (atr * 2)

        positions[ticker] = {
            'ticker': ticker,
            'quantity': quantity,
            'entry_price': entry_price,
            'current_price': entry_price,
            'atr': atr,
            'strategy': strategy,
            'entry_time': datetime.now().isoformat(),
            'stop_loss': stop_loss_value,
            'profit_target': profit_target_value,  # Dynamic risk:reward from live_trader
            'status': 'OPEN',
            'partial_taken': False
        }
        
        self.save_positions(positions)
        print(f"📝 Position opened: {ticker} @ ${entry_price:.2f}")
    
    def update_position(self, ticker, current_price):
        """Update position with current price and trailing stop"""
        positions = self.load_positions()
        
        if ticker not in positions or positions[ticker]['status'] != 'OPEN':
            return
        
        pos = positions[ticker]
        pos['current_price'] = current_price
        
        # Update trailing stop
        pos['stop_loss'] = self.calculate_trailing_stop(
            pos['entry_price'], 
            current_price, 
            pos['atr']
        )
        
        self.save_positions(positions)
    
    def close_position(self, ticker, close_price, reason):
        """Close a position"""
        positions = self.load_positions()
        
        if ticker not in positions:
            return
        
        pos = positions[ticker]
        pos['status'] = 'CLOSED'
        pos['close_price'] = close_price
        pos['close_time'] = datetime.now().isoformat()
        pos['close_reason'] = reason
        
        # Calculate P&L
        pnl = (close_price - pos['entry_price']) / pos['entry_price']
        pos['pnl_pct'] = pnl
        
        self.save_positions(positions)
        self.update_trade_result(ticker, pnl)
        
        print(f"🔒 Position closed: {ticker} @ ${close_price:.2f} | P&L: {pnl*100:.2f}% | {reason}")
    
    def get_open_positions(self):
        """Get all open positions"""
        positions = self.load_positions()
        return {k: v for k, v in positions.items() if v.get('status') == 'OPEN'}
    
    def check_exit_signals(self):
        """Check all positions for exit signals"""
        positions = self.get_open_positions()
        exit_signals = []
        
        for ticker, pos in positions.items():
            try:
                # Fetch current price
                stock = yf.Ticker(ticker)
                data = stock.history(period='1d', interval='1m')
                
                if data.empty:
                    continue
                
                current_price = data['Close'].iloc[-1]
                self.update_position(ticker, current_price)
                
                # Check stop loss
                if current_price <= pos['stop_loss']:
                    exit_signals.append({
                        'ticker': ticker,
                        'action': 'SELL',
                        'reason': 'STOP_LOSS',
                        'price': current_price
                    })
                
                # Check profit target (partial)
                should_take, portion = self.should_take_partial_profit(
                    pos['entry_price'], 
                    current_price, 
                    pos['atr']
                )
                
                if should_take and not pos.get('partial_taken'):
                    exit_signals.append({
                        'ticker': ticker,
                        'action': 'SELL_PARTIAL',
                        'portion': portion,
                        'reason': 'PROFIT_TARGET_1X',  # Updated to reflect 1:1 take
                        'price': current_price
                    })
                    
                    # Mark partial taken
                    positions[ticker]['partial_taken'] = True
                    self.save_positions(positions)
                
                # Check full profit target
                if current_price >= pos['profit_target']:
                    exit_signals.append({
                        'ticker': ticker,
                        'action': 'SELL',
                        'reason': 'PROFIT_TARGET_FULL',
                        'price': current_price
                    })
                    
            except Exception as e:
                print(f"Error checking exit for {ticker}: {e}")
        
        return exit_signals


def test_risk_manager():
    """Test the advanced risk manager"""
    rm = AdvancedRiskManager()
    
    print("=" * 60)
    print("ADVANCED RISK MANAGER TEST")
    print("=" * 60)
    
    # Test dynamic risk
    risk = rm.get_dynamic_risk()
    print(f"\n💰 Current risk per trade: {risk*100:.1f}%")
    
    # Test market regime
    regime, multiplier = rm.get_market_regime()
    print(f"📊 Market regime: {regime} (multiplier: {multiplier:.2f})")
    
    # Test position limits
    can_trade = rm.check_position_limits('AAPL')
    print(f"✅ Can trade AAPL: {can_trade}")
    
    # Test open positions
    positions = rm.get_open_positions()
    print(f"📈 Open positions: {len(positions)}")
    
    print("=" * 60)


if __name__ == '__main__':
    test_risk_manager()
