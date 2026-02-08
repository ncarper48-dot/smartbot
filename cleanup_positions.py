#!/usr/bin/env python3
"""
Clean up phantom positions (0 quantity but marked OPEN)
Run automatically before each trading session
"""

import json
import os
from datetime import datetime

POSITIONS_FILE = '/home/tradebot/open_positions.json'

def cleanup_positions():
    """Remove positions with 0 quantity or invalid status"""
    if not os.path.exists(POSITIONS_FILE):
        print("No positions file found")
        return
    
    try:
        with open(POSITIONS_FILE, 'r') as f:
            positions = json.load(f)
        
        original_count = len(positions)
        cleaned = {}
        
        for ticker, pos in positions.items():
            quantity = pos.get('quantity', 0)
            status = pos.get('status', 'UNKNOWN')
            
            # Only keep positions with actual quantity
            if quantity > 0 and status == 'OPEN':
                cleaned[ticker] = pos
            else:
                print(f"🗑️  Removing phantom: {ticker} (qty={quantity}, status={status})")
        
        # Save cleaned positions
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(cleaned, f, indent=2)
        
        removed = original_count - len(cleaned)
        if removed > 0:
            print(f"✅ Cleaned {removed} phantom position(s)")
            print(f"📊 Active positions: {len(cleaned)}")
        else:
            print(f"✓ All positions valid ({len(cleaned)} active)")
        
        return cleaned
    
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return None

if __name__ == "__main__":
    print(f"🧹 Position cleanup at {datetime.now()}")
    cleanup_positions()
