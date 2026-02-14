#!/usr/bin/env python3
"""Auto-trader: runs the bot continuously with smart scheduling.

Runs daily_runner.py:
- At market open (9:30 AM ET)
- Every 4 hours during market hours
- Logs all activity to auto_trader.log
"""
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, time as dt_time
import subprocess
import sys
import json

# Setup logging with automatic rotation (max 5MB, keep 2 backups)
_fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
_file_handler = RotatingFileHandler(
    '/home/tradebot/auto_trader.log',
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=2,             # keeps auto_trader.log.1, .2
)
_file_handler.setFormatter(_fmt)
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setFormatter(_fmt)

logging.basicConfig(level=logging.INFO, handlers=[_file_handler])
logger = logging.getLogger(__name__)

MARKET_OPEN = dt_time(9, 30)  # 9:30 AM ET
MARKET_CLOSE = dt_time(16, 0)  # 4:00 PM ET
RUN_INTERVAL = 120  # 2 minutes - BEAST MODE for maximum opportunities
OVERNIGHT_INTERVAL = 1800  # 30 minutes between overnight scans


def is_market_hours() -> bool:
    """Check if US market is currently open (weekdays 9:30-16:00 ET)."""
    import pytz
    et = pytz.timezone('America/New_York')
    now_et = datetime.now(et)
    time_et = now_et.time()
    weekday = now_et.weekday()
    is_weekday = weekday < 5  # 0-4 = Mon-Fri
    is_open = MARKET_OPEN <= time_et <= MARKET_CLOSE
    return is_weekday and is_open


def run_overnight_analysis():
    """Run overnight intelligence engine (news, global markets, technicals)."""
    logger.info("🌙🔬 OVERNIGHT INTELLIGENCE ENGINE RUNNING...")
    try:
        env = os.environ.copy()
        env.setdefault("SMARTBOT_DISABLE_TF", "1")
        env["VIRTUAL_ENV"] = "/home/tradebot/.venv"
        env["PATH"] = f"/home/tradebot/.venv/bin:{env.get('PATH', '')}"
        venv_site = "/home/tradebot/.venv/lib/python3.11/site-packages"
        env["PYTHONPATH"] = f"{venv_site}:{env.get('PYTHONPATH', '')}".rstrip(":")
        result = subprocess.run(
            [sys.executable, '/home/tradebot/overnight_analysis.py'],
            capture_output=True,
            text=True,
            timeout=600,  # 10 min — lots of data to fetch
            env=env
        )
        if result.returncode == 0:
            logger.info("✅ Overnight analysis complete — watchlist saved")
            # Log top picks
            try:
                with open('/home/tradebot/overnight_watchlist.json') as f:
                    wl = json.load(f)
                for entry in wl.get("watchlist", [])[:5]:
                    logger.info(f"   #{entry['rank']} {entry['symbol']} "
                                f"Edge:{entry['edge_score']:+.1f} {entry['recommendation']}")
            except Exception:
                pass
        else:
            logger.error(f"❌ Overnight analysis failed: {result.stderr[:300]}")
    except subprocess.TimeoutExpired:
        logger.error("❌ Overnight analysis timed out (>10 min)")
    except Exception as e:
        logger.error(f"❌ Overnight analysis error: {e}")


def run_eod_close():
    """End-of-day profit taking — lock in gains before market close."""
    logger.info("🔔 END-OF-DAY PROFIT TAKING — Locking in gains before close")
    try:
        env = os.environ.copy()
        env.setdefault("SMARTBOT_DISABLE_TF", "1")
        env["VIRTUAL_ENV"] = "/home/tradebot/.venv"
        env["PATH"] = f"/home/tradebot/.venv/bin:{env.get('PATH', '')}"
        venv_site = "/home/tradebot/.venv/lib/python3.11/site-packages"
        env["PYTHONPATH"] = f"{venv_site}:{env.get('PYTHONPATH', '')}"  
        result = subprocess.run(
            [sys.executable, '-c',
             'from live_trader import end_of_day_close; end_of_day_close(dry_run=False)'],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
            cwd='/home/tradebot'
        )
        if result.returncode == 0:
            logger.info("✅ EOD profit taking complete")
            if result.stdout:
                logger.info(result.stdout)
        else:
            logger.error(f"❌ EOD close failed: {result.stderr[:300]}")
    except subprocess.TimeoutExpired:
        logger.error("❌ EOD close timed out")
    except Exception as e:
        logger.error(f"❌ EOD close error: {e}")


def run_strategy():
    """Execute the daily trading strategy."""
    logger.info("🤖 AUTONOMOUS TRADER EXECUTING...")
    
    # Clean up phantom positions before trading
    try:
        subprocess.run([sys.executable, '/home/tradebot/cleanup_positions.py'], 
                      capture_output=True, timeout=10)
    except Exception:
        pass  # Continue even if cleanup fails
    
    try:
        # Use live trader for real-time trading
        env = os.environ.copy()
        env.setdefault("SMARTBOT_DISABLE_TF", "1")
        env["VIRTUAL_ENV"] = "/home/tradebot/.venv"
        env["PATH"] = f"/home/tradebot/.venv/bin:{env.get('PATH', '')}"
        venv_site = "/home/tradebot/.venv/lib/python3.11/site-packages"
        env["PYTHONPATH"] = f"{venv_site}:{env.get('PYTHONPATH', '')}".rstrip(":")
        result = subprocess.run(
            [sys.executable, '/home/tradebot/live_trader.py'],
            capture_output=True,
            text=True,
            timeout=600,
            env=env
        )
        
        if result.returncode == 0:
            logger.info("✅ Live trading executed successfully")
            if result.stdout:
                logger.info(result.stdout)
        else:
            logger.error(f"❌ Live trading failed: {result.stderr}")
            # Don't crash - just log and continue
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Strategy timeout (>5 min) - continuing...")
    except Exception as e:
        logger.error(f"❌ Error running strategy: {e} - continuing...")
        # Bot continues running even if one cycle fails


def main():
    """Main loop: run 24/7 for continuous learning and trading."""
    logger.info("="*70)
    logger.info("🚀 AUTONOMOUS TRADING BOT STARTED - 24/7 MODE")
    logger.info("="*70)
    logger.info(f"Market hours: {MARKET_OPEN} - {MARKET_CLOSE} ET (2:30 PM - 9:00 PM UK)")
    logger.info(f"Run interval: Every {RUN_INTERVAL // 60} minutes")
    logger.info("📈 Live trades during US market hours")
    logger.info("🌙 Overnight intelligence engine (news, global, technicals)")
    logger.info("☀️ Pre-open watchlist refresh at 9:00 AM ET (2:00 PM UK)")
    logger.info("="*70)
    
    last_run = 0
    last_overnight_run = 0
    last_report_open = None
    last_report_close = None
    last_overnight_close = None  # Track post-close analysis
    last_overnight_preopen = None  # Track pre-open analysis
    last_eod_close = None  # Track EOD profit taking
    
    try:
        while True:
            now = time.time()
            market_open = is_market_hours()
            
            # Show UK time in logs for convenience
            import pytz as _pz
            _uk_now = datetime.now(_pz.timezone('Europe/London')).strftime('%H:%M UK')
            et_tz = _pz.timezone('America/New_York')
            now_et = datetime.now(et_tz)
            time_et = now_et.time()
            today = now_et.strftime('%Y-%m-%d')
            
            # === END-OF-DAY PROFIT TAKING: 3:45 PM ET (8:45 PM UK) ===
            if time_et.hour == 15 and 45 <= time_et.minute <= 55:
                if last_eod_close != today:
                    logger.info(f"🔔 EOD PROFIT TAKING ({_uk_now}) — Locking in gains before close")
                    run_eod_close()
                    last_eod_close = today
            
            if market_open:
                # === MARKET HOURS: Trade every 2 min ===
                if (now - last_run) >= RUN_INTERVAL:
                    logger.info(f"📈 US MARKET OPEN ({_uk_now}) - Executing live trades")
                    run_strategy()
                    last_run = now
            else:
                # === OFF-HOURS: Overnight intelligence ===
                
                # Key analysis window 1: Right after close (4:15 PM ET)
                if time_et.hour == 16 and 15 <= time_et.minute <= 20:
                    if last_overnight_close != today:
                        logger.info(f"🌙 POST-CLOSE SCAN ({_uk_now}) — Running full overnight analysis")
                        run_overnight_analysis()
                        last_overnight_close = today
                        last_overnight_run = now
                
                # Key analysis window 2: Pre-open (9:00 AM ET)
                elif time_et.hour == 9 and 0 <= time_et.minute <= 5:
                    if last_overnight_preopen != today:
                        logger.info(f"☀️ PRE-OPEN SCAN ({_uk_now}) — Refreshing watchlist for today")
                        run_overnight_analysis()
                        last_overnight_preopen = today
                        last_overnight_run = now
                
                # Periodic off-hours scan every 30 min
                elif (now - last_overnight_run) >= OVERNIGHT_INTERVAL:
                    logger.info(f"🌙 Off-hours ({_uk_now}) — Periodic intelligence scan")
                    run_overnight_analysis()
                    last_overnight_run = now
            
            # Daily report scheduler (market open + close ET)
            try:

                # 09:35 ET report (after open)
                if time_et.hour == 9 and time_et.minute >= 35:
                    if last_report_open != today:
                        subprocess.run([sys.executable, '/home/tradebot/daily_report.py'],
                                      capture_output=True, timeout=30)
                        last_report_open = today

                # 16:10 ET report (after close)
                if time_et.hour == 16 and time_et.minute >= 10:
                    if last_report_close != today:
                        subprocess.run([sys.executable, '/home/tradebot/daily_report.py'],
                                      capture_output=True, timeout=30)
                        last_report_close = today
            except Exception:
                pass

            time.sleep(30)  # Check every 30 seconds
                
    except KeyboardInterrupt:
        logger.info("🛑 AUTONOMOUS TRADER STOPPED")
        sys.exit(0)


if __name__ == "__main__":
    main()
