#!/usr/bin/env python3
"""
SMS/Email notification system for SmartBot Trading
Sends alerts via email and SMS gateway
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json

# User contact info
PHONE_NUMBER = "07568785488"
EMAIL = "nottscarper@yahoo.co.uk"

# SMS Gateway for UK numbers (try multiple)
SMS_GATEWAYS = [
    f"{PHONE_NUMBER}@sms.o2.co.uk",  # O2
    f"{PHONE_NUMBER}@vodafone.sms.sms",  # Vodafone  
    f"{PHONE_NUMBER}@mmail.co.uk",  # Orange/EE
]

def send_notification(subject, message, priority="normal"):
    """Send notification via email (and attempt SMS)"""
    
    # For now, just log to file (requires Gmail app password to actually send)
    # User can set up later with: SMTP_USER and SMTP_PASSWORD in .env
    
    log_file = "/home/tradebot/notifications.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    notification = f"""
{'='*60}
[{timestamp}] {priority.upper()}
SUBJECT: {subject}
TO: {EMAIL}
MESSAGE:
{message}
{'='*60}
"""
    
    # Log notification
    with open(log_file, 'a') as f:
        f.write(notification)
    
    # Also save to JSON for dashboard
    notif_data = {
        "timestamp": timestamp,
        "subject": subject,
        "message": message,
        "priority": priority,
        "sent_to": EMAIL
    }
    
    try:
        with open("/home/tradebot/last_notification.json", 'w') as f:
            json.dump(notif_data, f, indent=2)
    except:
        pass
    
    print(f"📱 Notification logged: {subject}")

    
    
    # Email sending disabled - only logging to file

def send_email_smtp(subject, message, smtp_user, smtp_password):
    """Actually send email via SMTP (Gmail/Yahoo)"""
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = EMAIL
    msg['Subject'] = f"SmartBot: {subject}"
    
    msg.attach(MIMEText(message, 'plain'))
    
    # Try Gmail first, then Yahoo
    servers = [
        ('smtp.gmail.com', 587),
        ('smtp.mail.yahoo.com', 587)
    ]
    
    for server, port in servers:
        try:
            with smtplib.SMTP(server, port) as smtp:
                smtp.starttls()
                smtp.login(smtp_user, smtp_password)
                smtp.send_message(msg)
            return True
        except:
            continue
    
    raise Exception("All SMTP servers failed")

def notify_trade(ticker, action, quantity, price, reason, pnl=None):
    """Send trade alert only if profitable (pnl > 0)"""
    message = f"""
SmartBot executed a trade:

SYMBOL: {ticker}
ACTION: {action.upper()}
QUANTITY: {quantity}
PRICE: ${price:.2f}
REASON: {reason}
"""
    if pnl is not None and pnl > 0:
        message += f"\nPROFIT: ${pnl:.2f}\n"
        send_notification(f"Trade Profit: {action.upper()} {ticker}", message, priority="high")
    else:
        # Only log, do not email
        send_notification(f"Trade Alert (No Profit): {action.upper()} {ticker}", message, priority="normal")

def notify_daily_summary(balance, daily_pnl, positions, trades_today):
    """Send end-of-day summary"""
    message = f"""
SmartBot Daily Summary:

💰 Balance: ${balance:,.2f}
📊 Daily P&L: ${daily_pnl:+,.2f}
📦 Open Positions: {positions}
🔄 Trades Today: {trades_today}

Date: {datetime.now().strftime('%A, %B %d, %Y')}
"""
    send_notification("Daily Summary", message, priority="normal")

def notify_bot_status(status, details=""):
    """Send bot status alert"""
    message = f"""
SmartBot Status Change:

STATUS: {status}
{details}

Time: {datetime.now().strftime('%I:%M %p')}
"""
    # Only log, do not email any status
    send_notification(f"Bot Status: {status}", message, priority="normal")

if __name__ == "__main__":
    # Test notification
    notify_bot_status("OPERATIONAL", "System check - all systems running normally")
    print("\n✅ Test notification created")
    print(f"📱 Phone: {PHONE_NUMBER}")
    print(f"📧 Email: {EMAIL}")
    print("\nTo enable actual email sending:")
    print("1. Add to .env file:")
    print("   SMTP_USER=your_email@gmail.com")
    print("   SMTP_PASSWORD=your_app_password")
    print("2. For Gmail: Enable 2FA and create App Password")
    print("3. For Yahoo: Use account password or app password")
