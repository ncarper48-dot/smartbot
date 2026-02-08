import os
from dotenv import load_dotenv
import requests
import base64
import json
import argparse
import logging
import sys
from typing import Optional

# Configure basic logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Load .env (optional) so env vars can be set in a .env file
# For tests, you can set TRADING212_SKIP_DOTENV=1 to avoid reading the local .env file
if os.getenv("TRADING212_SKIP_DOTENV", "").lower() not in ("1", "true", "yes"):
    load_dotenv()

# Read credentials from environment variables (preferred) or fall back to placeholders
API_KEY = os.getenv("TRADING212_API_KEY", "your_api_key")
API_SECRET = os.getenv("TRADING212_API_SECRET", "your_api_secret")
BASE_URL = os.getenv("TRADING212_BASE_URL", "https://live.trading212.com/api/v0") # Use 'demo' instead of 'live' for testing

# Safety: maximum allowed order quantity per order (can be overridden via env)
MAX_ORDER_QUANTITY = float(os.getenv("TRADING212_MAX_ORDER_QUANTITY", "100.0"))

# Use dry-run unless explicitly confirmed for live orders


def _ensure_credentials():
    """Raise a clear error if credentials are not set."""
    api_key = os.getenv("TRADING212_API_KEY")
    api_secret = os.getenv("TRADING212_API_SECRET")
    if not api_key or not api_secret:
        raise RuntimeError(
            "Trading 212 API credentials are not set.\n"
            "Set TRADING212_API_KEY and TRADING212_API_SECRET in the environment or in a .env file (see .env.example)."
        )

def get_headers():
    # Read credentials at call-time so runtime env changes and tests work reliably
    api_key = os.getenv("TRADING212_API_KEY")
    api_secret = os.getenv("TRADING212_API_SECRET")
    if not api_key or not api_secret:
        raise RuntimeError(
            "Trading 212 API credentials are not set. Set TRADING212_API_KEY and TRADING212_API_SECRET."
        )

    # Trading 212 uses Basic Auth: base64(API_KEY:API_SECRET)
    auth_str = f"{api_key}:{api_secret}"
    encoded_auth = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
    return {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/json"
    }

def get_account_cash():
    # If mock mode is enabled, return synthetic data for safe testing
    if os.getenv("TRADING212_USE_MOCK", "").lower() in ("1", "true", "yes"):
        return {"cash": {"available": 10000.0, "currency": "USD"}}

    url = f"{BASE_URL}/equity/account/cash"
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code} - {response.text}"

import time
import uuid
import hashlib
import json as _json

IDEMPOTENCY_STORE = os.path.join(os.path.dirname(__file__), ".idempotency.json")


def _load_idempotency_store():
    try:
        with open(IDEMPOTENCY_STORE, "r") as f:
            return _json.load(f)
    except Exception:
        return {}


def _save_idempotency_store(store):
    try:
        with open(IDEMPOTENCY_STORE, "w") as f:
            _json.dump(store, f)
    except Exception as e:
        logger.warning("Failed to save idempotency store: %s", e)


def _fingerprint(ticker: str, quantity: float):
    return hashlib.sha256(f"{ticker}:{quantity}".encode()).hexdigest()


def _ensure_client_order_id(ticker: str, quantity: float, persist: bool = False):
    # Use fingerprint to check if we already generated an idempotency key for this order
    fp = _fingerprint(ticker, quantity)
    store = _load_idempotency_store()
    if fp in store:
        return store[fp]["idempotency_key"]
    key = str(uuid.uuid4())
    store[fp] = {"idempotency_key": key, "ticker": ticker, "quantity": quantity, "created": time.time()}
    if persist:
        _save_idempotency_store(store)
    return key


def get_order(order_id: str):
    """Retrieve a single order by ID. In mock mode returns a synthetic order."""
    if os.getenv("TRADING212_USE_MOCK", "").lower() in ("1", "true", "yes"):
        # Simulated order structure
        return {"id": order_id, "status": "filled", "ticker": "MOCK_TICKER", "quantity": 1.0}

    url = f"{BASE_URL}/equity/orders/{order_id}"
    # Simple retry on transient network errors
    for attempt in range(3):
        try:
            response = requests.get(url, headers=get_headers(), timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code in (502, 503, 504):
                logger.warning("Transient response %s from get_order, retrying...", response.status_code)
                time.sleep(0.5 * (attempt + 1))
                continue
            else:
                raise RuntimeError(f"Error fetching order {order_id}: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            logger.warning("Network error fetching order %s: %s", order_id, e)
            time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch order {order_id} after retries")


def list_orders():
    """List recent orders. In mock mode returns synthetic list."""
    if os.getenv("TRADING212_USE_MOCK", "").lower() in ("1", "true", "yes"):
        return [{"id": "MOCK-1", "status": "filled", "ticker": "MOCK_TICKER", "quantity": 1.0}]

    url = f"{BASE_URL}/equity/orders"
    for attempt in range(3):
        try:
            response = requests.get(url, headers=get_headers(), timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code in (502, 503, 504):
                logger.warning("Transient response %s from list_orders, retrying...", response.status_code)
                time.sleep(0.5 * (attempt + 1))
                continue
            else:
                raise RuntimeError(f"Error listing orders: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            logger.warning("Network error listing orders: %s", e)
            time.sleep(0.5 * (attempt + 1))
    raise RuntimeError("Failed to list orders after retries")


def wait_for_order_status(order_id: str, *, target_statuses=("filled",), timeout: int = 30, poll_interval: float = 2.0, max_backoff: float = 8.0):
    """Poll order status until one of `target_statuses` is reached or timeout.

    Uses exponential backoff between polls to reduce load. Returns final order on success or raises TimeoutError.
    """
    import time
    start = time.time()
    attempt = 0
    while True:
        try:
            order = get_order(order_id)
        except Exception as e:
            logger.warning("Error polling order %s: %s", order_id, e)
            order = {"status": "unknown"}

        status = str(order.get("status", "")).lower()
        logger.debug("Polled order %s status=%s", order_id, status)
        if status in target_statuses:
            return order
        if time.time() - start > timeout:
            raise TimeoutError(f"Timeout waiting for order {order_id} to reach {target_statuses}; last status={status}")
        # Exponential backoff
        sleep_for = min(poll_interval * (2 ** attempt), max_backoff)
        time.sleep(sleep_for)
        attempt += 1


from risk import compute_position_size_by_risk, check_daily_loss_allowed, get_price as get_market_price


def place_market_order(ticker: str, quantity: Optional[float], mode: Optional[str] = None, confirm: bool = False, client_order_id: Optional[str] = None, wait_for_fill: bool = False, wait_timeout: int = 30, auto_size: bool = False, stop_loss_pct: float = 0.02):
    """Place a market order. For safety:
    - If `auto_size` is True and `quantity` is falsy, compute quantity by risk rules.
    - stop_loss_pct is used for auto sizing calculation.
    """
    """
    Place a market order. For safety:
    - If `mode` is set to 'mock' or TRADING212_USE_MOCK=1, the call is mocked.
    - If `mode` is 'live', `confirm` must be True to actually place the order.
    - Enforces a maximum order quantity limit.
    - Optionally `wait_for_fill` will poll order status until `filled` or timeout.
    """
    # Validate quantity against safety limit
    if abs(quantity) > MAX_ORDER_QUANTITY:
        raise ValueError(f"Requested quantity {quantity} exceeds the maximum allowed {MAX_ORDER_QUANTITY}")

    # Daily loss guard
    max_daily_loss = os.getenv("TRADING212_MAX_DAILY_LOSS")
    if not check_daily_loss_allowed(max_daily_loss):
        raise RuntimeError("Daily loss limit exceeded; new orders are blocked")

    # Auto-size if requested (and quantity not provided)
    if auto_size and not quantity:
        price_for_size = get_market_price(ticker)
        risk_pct = float(os.getenv("TRADING212_RISK_PER_TRADE", "0.01"))
        qty = compute_position_size_by_risk(price_for_size, None, risk_pct, stop_loss_pct)
        if qty <= 0:
            raise RuntimeError("Computed auto size is zero; increase cash or risk parameters")
        quantity = qty

    # Resolve mode: function arg -> env var -> default to live
    resolved_mode = (mode or os.getenv("TRADING212_MODE") or "live").lower()

    # Mock mode shortcut
    if resolved_mode == "mock" or os.getenv("TRADING212_USE_MOCK", "").lower() in ("1", "true", "yes"):
        logger.info("MOCK order: ticker=%s quantity=%s", ticker, quantity)
        mock_order = {"status": "ok", "order": {"ticker": ticker, "quantity": quantity, "id": "MOCK-1234"}}
        if wait_for_fill:
            # In mock, simulate immediate fill
            mock_order["order"]["status"] = "filled"
        return mock_order

    # Demo mode: pass through without placing live trades but return an order id for polling
    if resolved_mode == "demo":
        logger.info("DEMO order (simulated): ticker=%s quantity=%s", ticker, quantity)
        demo_order = {"status": "demo", "order": {"ticker": ticker, "quantity": quantity, "id": "DEMO-123"}}
        if wait_for_fill:
            # Attempt to poll until filled; in many demo APIs this may not be supported, but we attempt
            try:
                return wait_for_order_status(demo_order["order"]["id"], timeout=wait_timeout)
            except Exception:
                return demo_order
        return demo_order

    # Live mode requires explicit confirmation
    if resolved_mode == "live" and not confirm and os.getenv("TRADING212_AUTO_CONFIRM", "").lower() not in ("1", "true", "yes"):
        raise RuntimeError("Live orders require explicit confirmation. Call with confirm=True or set TRADING212_AUTO_CONFIRM=1 in env for automation.")

    url = f"{BASE_URL}/equity/orders/market"
    data = {
        "ticker": ticker,
        "quantity": quantity
    }
    if client_order_id:
        data["client_order_id"] = client_order_id

    # Ensure idempotency header is set (generate if not provided)
    idempotency_key = client_order_id or _ensure_client_order_id(ticker, quantity)
    headers = get_headers()
    headers["Idempotency-Key"] = idempotency_key

    logger.info("Placing LIVE order: ticker=%s quantity=%s idempotency=%s", ticker, quantity, idempotency_key)
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Order timeout for {ticker}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Order network error for {ticker}: {e}")
    
    # Check response status
    if response.status_code == 429:
        raise RuntimeError(f"Rate limit hit - wait before placing more orders")
    elif response.status_code != 200:
        raise RuntimeError(f"Order failed ({response.status_code}): {response.text}")
    
    # Parse response
    try:
        order_resp = response.json()
    except Exception as e:
        raise RuntimeError(f"Failed to parse order response: {e}")
    
    # Verify order was created (must have an ID)
    if not isinstance(order_resp, dict) or not order_resp.get("id"):
        raise RuntimeError(f"Order response missing ID: {order_resp}")
    
    logger.info("✅ Order placed successfully: ID=%s status=%s", order_resp.get("id"), order_resp.get("status"))
    
    # Wait for fill if requested
    if wait_for_fill:
        try:
            return wait_for_order_status(order_resp["id"], timeout=wait_timeout)
        except Exception as e:
            logger.warning("Wait for fill failed: %s", e)
            return order_resp

    return order_resp


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Trading212 bot runner")
    parser.add_argument("--mode", choices=["mock", "demo", "live"], default=os.getenv("TRADING212_CLI_MODE", "demo"), help="Mode to run: mock/demo/live (default: demo)")
    parser.add_argument("--confirm", action="store_true", help="Confirm live trades (required to place live orders)")
    parser.add_argument("--cash", action="store_true", help="Print account cash and exit")
    parser.add_argument("--order", nargs=2, metavar=("TICKER","QTY"), help="Place a market order: --order TICKER QTY")
    parser.add_argument("--auto-size", action="store_true", help="Automatically compute quantity by risk sizing when placing an order")
    parser.add_argument("--stop-loss-pct", type=float, default=0.02, help="Stop loss percent used when auto-sizing (default 0.02)")
    parser.add_argument("--orders", action="store_true", help="List recent orders")
    parser.add_argument("--order-status", dest="order_status", help="Get status for a single order ID")
    parser.add_argument("--wait-for-fill", action="store_true", help="Wait for order to be filled when placing orders")
    parser.add_argument("--wait-timeout", type=int, default=30, help="Timeout seconds to wait for order fill when using --wait-for-fill")
    parser.add_argument("--idempotency-persist", action="store_true", help="Persist generated idempotency keys to .idempotency.json")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()

    try:
        print("requests version:", requests.__version__)
    except Exception as e:
        print("requests import check failed:", e)

    # Respect CLI mode first; set env for downstream calls
    if args.mode:
        os.environ["TRADING212_MODE"] = args.mode

    if args.mode == "demo":
        print("Running in DEMO mode (simulated orders).")

    if args.cash:
        try:
            print(get_account_cash())
        except Exception as e:
            print("Error during account check:", e)
        sys.exit(0)

    if args.order:
        ticker, qty = args.order
        try:
            qty_val = float(qty) if qty not in ("auto", "Auto", "AUTO") else None
        except Exception:
            print("Invalid quantity", qty); sys.exit(2)

        try:
            res = place_market_order(ticker, qty_val, mode=args.mode, confirm=args.confirm, wait_for_fill=args.wait_for_fill, wait_timeout=args.wait_timeout, auto_size=args.auto_size, stop_loss_pct=args.stop_loss_pct)
            print(res)
        except Exception as e:
            print("Order failed:", e)
            sys.exit(1)

    # New CLI helpers
    if getattr(args, "orders", None):
        try:
            orders = list_orders()
            print(orders)
        except Exception as e:
            print("Failed to list orders:", e)
            sys.exit(1)
        sys.exit(0)

    if getattr(args, "order_status", None):
        order_id = args.order_status
        try:
            print(get_order(order_id))
        except Exception as e:
            print("Failed to fetch order:", e)
            sys.exit(1)
