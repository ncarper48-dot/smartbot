#!/usr/bin/env python3
"""DEPLOYMENT & MONITORING DASHBOARD for Autonomous Trading Bot"""
import os
import time
import subprocess
from datetime import datetime

class DeploymentManager:
    def __init__(self):
        self.bot_dir = "/home/tradebot"
        self.pid_file = f"{self.bot_dir}/.auto_trader.pid"
        
    def verify_config(self):
        """Verify all configuration is correct."""
        print("\n" + "="*70)
        print("🔍 VERIFYING CONFIGURATION")
        print("="*70)
        
        env_file = f"{self.bot_dir}/.env"
        required_vars = [
            "T212_API_KEY",
            "T212_API_SECRET", 
            "T212_API_BASE_URL",
            "TRADING212_AUTO_CONFIRM",
            "TRADING212_MODE",
            "TRADING212_DAILY_TICKERS"
        ]
        
        if not os.path.exists(env_file):
            print("❌ .env file not found")
            return False
        
        with open(env_file) as f:
            config = f.read()
        
        all_present = True
        for var in required_vars:
            if var in config:
                value = [l.split("=")[1] for l in config.split("\n") if l.startswith(var)]
                print(f"✅ {var}: {'*' * 20}")
            else:
                print(f"❌ {var}: MISSING")
                all_present = False
        
        # Verify directories
        for dir_name in ["reports", "support"]:
            dir_path = f"{self.bot_dir}/{dir_name}"
            if os.path.exists(dir_path):
                print(f"✅ {dir_name}/ directory exists")
            else:
                print(f"❌ {dir_name}/ directory missing")
                all_present = False
        
        return all_present
    
    def is_auto_trader_running(self):
        """Check if auto_trader is already running."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "auto_trader.py"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def start_auto_trader(self):
        """Start the autonomous trader."""
        print("\n" + "="*70)
        print("🚀 STARTING AUTONOMOUS TRADER")
        print("="*70)
        
        if self.is_auto_trader_running():
            print("⚠️  Auto-trader already running!")
            return True
        
        try:
            subprocess.Popen(
                ["nohup", "python3", f"{self.bot_dir}/auto_trader.py"],
                stdout=open(f"{self.bot_dir}/auto_trader_output.log", "w"),
                stderr=subprocess.STDOUT,
                cwd=self.bot_dir
            )
            time.sleep(2)  # Wait for process to start
            
            if self.is_auto_trader_running():
                print("✅ Auto-trader started successfully")
                return True
            else:
                print("❌ Failed to start auto-trader")
                return False
        except Exception as e:
            print(f"❌ Error starting auto-trader: {e}")
            return False
    
    def test_run(self):
        """Run a test strategy execution."""
        print("\n" + "="*70)
        print("🧪 RUNNING TEST EXECUTION")
        print("="*70)
        
        try:
            result = subprocess.run(
                ["python3", f"{self.bot_dir}/daily_runner.py"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.bot_dir
            )
            
            if result.returncode == 0:
                print("✅ Test execution successful!")
                # Print last 20 lines of output
                output_lines = result.stdout.strip().split("\n")
                for line in output_lines[-15:]:
                    print(f"  {line}")
                return True
            else:
                print("❌ Test execution failed!")
                print(result.stderr)
                return False
        except subprocess.TimeoutExpired:
            print("❌ Test execution timeout")
            return False
        except Exception as e:
            print(f"❌ Error running test: {e}")
            return False
    
    def show_status(self):
        """Show current bot status."""
        print("\n" + "="*70)
        print("📊 BOT STATUS")
        print("="*70)
        
        # Auto-trader process
        if self.is_auto_trader_running():
            print("✅ Auto-trader: RUNNING")
            try:
                result = subprocess.run(
                    ["pgrep", "-f", "auto_trader.py"],
                    capture_output=True,
                    text=True
                )
                pid = result.stdout.strip()
                print(f"   PID: {pid}")
            except:
                pass
        else:
            print("❌ Auto-trader: STOPPED")
        
        # Latest reports
        reports_dir = f"{self.bot_dir}/reports"
        if os.path.exists(reports_dir):
            files = sorted(os.listdir(reports_dir), reverse=True)
            if files:
                latest = files[0]
                print(f"\n✅ Latest report: {latest}")
                
                # Parse latest summary CSV if available
                summary_files = [f for f in files if f.startswith("summary_")]
                if summary_files:
                    latest_summary = f"{reports_dir}/{summary_files[0]}"
                    try:
                        with open(latest_summary) as f:
                            lines = f.readlines()
                            if len(lines) > 1:
                                print("\n   Latest Results:")
                                for line in lines[1:]:
                                    print(f"   {line.strip()}")
                    except:
                        pass
        
        # Log file
        log_file = f"{self.bot_dir}/auto_trader.log"
        if os.path.exists(log_file):
            with open(log_file) as f:
                lines = f.readlines()
                if lines:
                    print(f"\n✅ Latest log entries:")
                    for line in lines[-5:]:
                        print(f"   {line.strip()}")
    
    def deploy(self):
        """Full deployment process."""
        print("\n" + "█"*70)
        print("█" + " "*68 + "█")
        print("█" + " AUTONOMOUS TRADING BOT - PRODUCTION DEPLOYMENT".center(68) + "█")
        print("█" + " "*68 + "█")
        print("█"*70 + "\n")
        
        # Step 1: Verify config
        if not self.verify_config():
            print("\n❌ Configuration verification failed!")
            return False
        
        # Step 2: Test run
        if not self.test_run():
            print("\n❌ Test run failed!")
            return False
        
        # Step 3: Start auto-trader
        if not self.start_auto_trader():
            print("\n❌ Failed to start auto-trader!")
            return False
        
        # Step 4: Show status
        self.show_status()
        
        # Success banner
        print("\n" + "="*70)
        print("🎯 DEPLOYMENT COMPLETE - BOT IS LIVE!")
        print("="*70)
        print("\n📋 QUICK COMMANDS:")
        print("   Monitor:  tail -f /home/tradebot/auto_trader.log")
        print("   Stop:     pkill -f auto_trader.py")
        print("   Status:   ps aux | grep auto_trader")
        print("   Reports:  ls -la /home/tradebot/reports/")
        print("\n✅ Bot is now autonomously trading 24/7!")
        print("="*70 + "\n")
        
        return True


if __name__ == "__main__":
    manager = DeploymentManager()
    manager.deploy()
