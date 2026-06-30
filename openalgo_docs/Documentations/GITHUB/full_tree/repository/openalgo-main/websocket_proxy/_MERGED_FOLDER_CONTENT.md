# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\websocket_proxy



---

# FILE: websocket_proxy\__init__.py

```py
# websocket_proxy/__init__.py

import logging

from .base_adapter import (
    BaseBrokerWebSocketAdapter,
    ENABLE_CONNECTION_POOLING,
    MAX_SYMBOLS_PER_WEBSOCKET,
    MAX_WEBSOCKET_CONNECTIONS,
)
from .broker_factory import (
    cleanup_all_pools,
    create_broker_adapter,
    get_pool_stats,
    get_resource_health,
    register_adapter,
)
from .connection_manager import (
    ConnectionPool,
    SharedZmqPublisher,
    get_max_symbols_per_websocket,
    get_max_websocket_connections,
)
from .server import WebSocketProxy
from .server import main as websocket_main

# Set up logger
logger = logging.getLogger(__name__)

# Import the angel_adapter directly from the broker directory
from broker.angel.streaming.angel_adapter import AngelWebSocketAdapter

# Import the compositedge_adapter
from broker.compositedge.streaming.compositedge_adapter import CompositedgeWebSocketAdapter

# Import the definedge_adapter
from broker.definedge.streaming.definedge_adapter import DefinedgeWebSocketAdapter

# Import the dhan_adapter
from broker.dhan.streaming.dhan_adapter import DhanWebSocketAdapter

# Import the fivepaisa_adapter
from broker.fivepaisa.streaming.fivepaisa_adapter import FivepaisaWebSocketAdapter

# Import the fivepaisaxts_adapter
from broker.fivepaisaxts.streaming.fivepaisaxts_adapter import FivepaisaXTSWebSocketAdapter

# Import the flattrade_adapter
from broker.flattrade.streaming.flattrade_adapter import FlattradeWebSocketAdapter

# Import the fyers_adapter
from broker.fyers.streaming.fyers_websocket_adapter import FyersWebSocketAdapter

# Import the ibulls_adapter
from broker.ibulls.streaming.ibulls_adapter import IbullsWebSocketAdapter

# Import the iifl_adapter
from broker.iifl.streaming.iifl_adapter import IiflWebSocketAdapter

# Import the iiflcapital_adapter
from broker.iiflcapital.streaming.iiflcapital_adapter import IiflcapitalWebSocketAdapter

# Import the indmoney_adapter
from broker.indmoney.streaming.indmoney_adapter import IndmoneyWebSocketAdapter

# Import the fivepaisaxts_adapter
from broker.jainamxts.streaming.jainamxts_adapter import JainamXTSWebSocketAdapter

# Import the kotak_adapter
from broker.kotak.streaming.kotak_adapter import KotakWebSocketAdapter

# Import the motilal_adapter
from broker.motilal.streaming.motilal_adapter import MotilalWebSocketAdapter

# Import the mstock_adapter
from broker.mstock.streaming.mstock_adapter import MstockWebSocketAdapter

# Import the nubra_adapter
from broker.nubra.streaming.nubra_adapter import NubraWebSocketAdapter

# Import the paytm_adapter
from broker.paytm.streaming.paytm_adapter import PaytmWebSocketAdapter

# Import the pocketful_adapter
from broker.pocketful.streaming.pocketful_adapter import PocketfulWebSocketAdapter

# Import the rmoney_adapter
from broker.rmoney.streaming.rmoney_adapter import RMoneyWebSocketAdapter

# Import the samco_adapter
from broker.samco.streaming.samco_adapter import SamcoWebSocketAdapter

# Import the shoonya_adapter
from broker.shoonya.streaming.shoonya_adapter import ShoonyaWebSocketAdapter

# Import the upstox_adapter
from broker.upstox.streaming.upstox_adapter import UpstoxWebSocketAdapter

# Import the wisdom_adapter
from broker.wisdom.streaming.wisdom_adapter import WisdomWebSocketAdapter

# Import the zerodha_adapter
from broker.zerodha.streaming.zerodha_adapter import ZerodhaWebSocketAdapter

# AliceBlue adapter will be loaded dynamically

# Register adapters
register_adapter("angel", AngelWebSocketAdapter)
register_adapter("zerodha", ZerodhaWebSocketAdapter)
register_adapter("dhan", DhanWebSocketAdapter)
register_adapter("flattrade", FlattradeWebSocketAdapter)
register_adapter("shoonya", ShoonyaWebSocketAdapter)
register_adapter("ibulls", IbullsWebSocketAdapter)
register_adapter("compositedge", CompositedgeWebSocketAdapter)
register_adapter("fivepaisa", FivepaisaWebSocketAdapter)
register_adapter("fivepaisaxts", FivepaisaXTSWebSocketAdapter)
register_adapter("iifl", IiflWebSocketAdapter)
register_adapter("iiflcapital", IiflcapitalWebSocketAdapter)
register_adapter("wisdom", WisdomWebSocketAdapter)
register_adapter("upstox", UpstoxWebSocketAdapter)
register_adapter("kotak", KotakWebSocketAdapter)
register_adapter("fyers", FyersWebSocketAdapter)
register_adapter("definedge", DefinedgeWebSocketAdapter)
register_adapter("paytm", PaytmWebSocketAdapter)
register_adapter("indmoney", IndmoneyWebSocketAdapter)
register_adapter("mstock", MstockWebSocketAdapter)
register_adapter("motilal", MotilalWebSocketAdapter)
register_adapter("jainamxts", JainamXTSWebSocketAdapter)
register_adapter("samco", SamcoWebSocketAdapter)
register_adapter("pocketful", PocketfulWebSocketAdapter)
register_adapter("nubra", NubraWebSocketAdapter)
register_adapter("rmoney", RMoneyWebSocketAdapter)

# AliceBlue adapter will be registered dynamically when first used

__all__ = [
    # Core classes
    "WebSocketProxy",
    "websocket_main",
    "register_adapter",
    "create_broker_adapter",
    # Base adapter (for cleanup utilities)
    "BaseBrokerWebSocketAdapter",
    # Connection pooling (multi-websocket support)
    "ConnectionPool",
    "SharedZmqPublisher",
    "get_pool_stats",
    "get_resource_health",
    "cleanup_all_pools",
    "get_max_symbols_per_websocket",
    "get_max_websocket_connections",
    # Configuration constants
    "MAX_SYMBOLS_PER_WEBSOCKET",
    "MAX_WEBSOCKET_CONNECTIONS",
    "ENABLE_CONNECTION_POOLING",
    # Broker adapters
    "AngelWebSocketAdapter",
    "ZerodhaWebSocketAdapter",
    "DhanWebSocketAdapter",
    "FlattradeWebSocketAdapter",
    "ShoonyaWebSocketAdapter",
    "IbullsWebSocketAdapter",
    "CompositedgeWebSocketAdapter",
    "FivepaisaWebSocketAdapter",
    "FivepaisaXTSWebSocketAdapter",
    "IiflWebSocketAdapter",
    "IiflcapitalWebSocketAdapter",
    "JainamWebSocketAdapter",
    "TrustlineWebSocketAdapter",
    "WisdomWebSocketAdapter",
    "UpstoxWebSocketAdapter",
    "KotakWebSocketAdapter",
    "FyersWebSocketAdapter",
    "DefinedgeWebSocketAdapter",
    "PaytmWebSocketAdapter",
    "IndmoneyWebSocketAdapter",
    "MstockWebSocketAdapter",
    "MotilalWebSocketAdapter",
    "JainamXTSWebSocketAdapter",
    "SamcoWebSocketAdapter",
    "PocketfulWebSocketAdapter",
    "NubraWebSocketAdapter",
    "RMoneyWebSocketAdapter",
]

```


---

# FILE: websocket_proxy\app_integration.py

```py
import asyncio
import atexit
import os
import platform
import signal
import subprocess
import sys
import threading

from utils.logging import get_logger, highlight_url

from .server import main as websocket_main

# Import the original threading module to run the asyncio event loop in a real
# OS thread, bypassing eventlet's monkey-patching which turns threading.Thread
# into green threads where asyncio.new_event_loop() cannot work.
if "eventlet" in sys.modules:
    import eventlet

    _original_threading = eventlet.patcher.original("threading")
else:
    _original_threading = threading


def _eventlet_active() -> bool:
    """True when eventlet has monkey-patched the stdlib (gunicorn worker)."""
    try:
        from eventlet.patcher import is_monkey_patched
        return bool(is_monkey_patched("socket"))
    except Exception:
        return False


# Set the correct event loop policy for Windows to avoid ZeroMQ warnings
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Global flag to track if the WebSocket server has been started
# Used to prevent multiple instances in Flask debug mode
_websocket_server_started = False
_websocket_proxy_instance = None
_websocket_thread = None
_websocket_subprocess = None  # set when running under eventlet (gunicorn)

logger = get_logger(__name__)


# Check if we're in the Flask child process that should start the WebSocket server
def should_start_websocket():
    """
    Determine if the current process should start the WebSocket server

    In Flask debug mode with reloader enabled, we only want to start the
    WebSocket server in the child process, not the parent process that
    monitors for file changes.

    Returns:
        bool: True if we should start the WebSocket server, False otherwise
    """
    # In debug mode, only start in the Flask child process
    if os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true"):
        # WERKZEUG_RUN_MAIN is set to 'true' by Flask in the child process
        # that actually runs the application
        return os.environ.get("WERKZEUG_RUN_MAIN") == "true"

    # In non-debug mode, always start
    return True


def cleanup_websocket_server():
    """Clean up WebSocket server resources - cross-platform compatible"""
    global _websocket_proxy_instance, _websocket_thread

    # If we spawned the WS as a subprocess (gunicorn+eventlet path), there is
    # no in-process thread or proxy instance to clean up — just kill the child.
    if _websocket_subprocess is not None:
        _terminate_websocket_subprocess()
        return

    try:
        logger.info("Cleaning up WebSocket server...")

        if _websocket_proxy_instance:
            # For Windows compatibility, set a shutdown flag instead of trying to
            # manipulate the event loop from a different thread
            _websocket_proxy_instance.running = False

            # Try to close the server gracefully
            try:
                if (
                    hasattr(_websocket_proxy_instance, "server")
                    and _websocket_proxy_instance.server
                ):
                    try:
                        _websocket_proxy_instance.server.close()
                    except Exception as e:
                        logger.warning(f"Error closing server handle: {e}")

                # Close ZMQ resources immediately
                if (
                    hasattr(_websocket_proxy_instance, "socket")
                    and _websocket_proxy_instance.socket
                ):
                    try:
                        import zmq

                        _websocket_proxy_instance.socket.setsockopt(zmq.LINGER, 0)
                        _websocket_proxy_instance.socket.close()
                    except Exception as e:
                        logger.warning(f"Error closing ZMQ socket: {e}")

                if (
                    hasattr(_websocket_proxy_instance, "context")
                    and _websocket_proxy_instance.context
                ):
                    try:
                        _websocket_proxy_instance.context.term()
                    except Exception as e:
                        logger.warning(f"Error terminating ZMQ context: {e}")

            except Exception as e:
                logger.exception(f"Error during WebSocket cleanup: {e}")
            finally:
                _websocket_proxy_instance = None

        if _websocket_thread and _websocket_thread.is_alive():
            logger.info("Waiting for WebSocket thread to finish...")
            _websocket_thread.join(timeout=5.0)  # Increased timeout for slow broker disconnects
            if _websocket_thread.is_alive():
                logger.warning("WebSocket thread did not finish gracefully")
            _websocket_thread = None

        # Clean up shared ZMQ context (handles app restart without process exit)
        try:
            from .base_adapter import BaseBrokerWebSocketAdapter
            BaseBrokerWebSocketAdapter.cleanup_shared_context()
            logger.info("Shared ZMQ context cleaned up")
        except Exception as e:
            logger.warning(f"Error cleaning up shared ZMQ context: {e}")

        logger.info("WebSocket server cleanup completed")

    except Exception as e:
        logger.exception(f"Error during WebSocket cleanup: {e}")
        # Last resort: force cleanup
        _websocket_proxy_instance = None
        _websocket_thread = None


def signal_handler(signum, frame):
    """Handle SIGINT (Ctrl+C) and SIGTERM signals"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    cleanup_websocket_server()
    # Use os._exit() for immediate termination across all platforms
    os._exit(0)


def _spawn_websocket_subprocess():
    """
    Spawn the WebSocket proxy as a child *process* (not a thread).

    Required under gunicorn+eventlet: an in-process asyncio thread shares the
    process with the eventlet hub, and any eventlet-monkey-patched semaphore
    (stdlib logging RLock, socketio lock, broker adapter `threading.Lock`)
    touched from both threads triggers `greenlet.error: Cannot switch to a
    different thread` and silently corrupts WS state (GitHub issue #1421).

    The child runs `python -m websocket_proxy.server` in a fresh interpreter
    with no eventlet monkey-patching, so all the offending primitives are
    real OS locks. Systemd's cgroup-based KillMode (default: control-group)
    cleans up the child when the unit stops; our atexit handler covers
    graceful gunicorn shutdown.
    """
    global _websocket_subprocess

    if _websocket_subprocess is not None and _websocket_subprocess.poll() is None:
        logger.debug("WebSocket subprocess already running, skipping spawn")
        return

    # Find the openalgo project root (parent of websocket_proxy/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    cmd = [sys.executable, "-u", "-m", "websocket_proxy.server"]
    logger.debug(f"Spawning WebSocket subprocess: {' '.join(cmd)} (cwd={project_root})")

    try:
        # Inherit stdout/stderr so the child's logging lands in the same
        # systemd journal as gunicorn. The WS server already uses Python
        # logging via utils.logging, so file/json log handlers fire too.
        _websocket_subprocess = subprocess.Popen(
            cmd,
            cwd=project_root,
            stdout=None,
            stderr=None,
            # Do NOT set start_new_session=True — staying in the gunicorn
            # cgroup means systemd reaps the child if gunicorn dies hard.
        )
        logger.info(f"WebSocket subprocess started with PID {_websocket_subprocess.pid}")
    except Exception as e:
        logger.exception(f"Failed to spawn WebSocket subprocess: {e}")
        _websocket_subprocess = None
        return

    # Graceful shutdown on clean gunicorn exit
    atexit.register(_terminate_websocket_subprocess)


def _terminate_websocket_subprocess():
    """SIGTERM the WS child on shutdown; SIGKILL if it ignores TERM."""
    global _websocket_subprocess
    if _websocket_subprocess is None:
        return
    if _websocket_subprocess.poll() is not None:
        _websocket_subprocess = None
        return
    try:
        logger.info(f"Terminating WebSocket subprocess PID {_websocket_subprocess.pid}")
        _websocket_subprocess.terminate()
        try:
            _websocket_subprocess.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logger.warning("WebSocket subprocess did not exit on SIGTERM, sending SIGKILL")
            _websocket_subprocess.kill()
            _websocket_subprocess.wait(timeout=5)
    except Exception as e:
        logger.warning(f"Error terminating WebSocket subprocess: {e}")
    finally:
        _websocket_subprocess = None


def start_websocket_server():
    """
    Start the WebSocket proxy server.

    Under gunicorn+eventlet: spawned as a child process (avoids the
    eventlet/asyncio cross-OS-thread greenlet crash class).

    Under the dev server (no eventlet): run as a real OS thread inside the
    Flask process, preserving the long-standing dev workflow.
    """
    global _websocket_proxy_instance, _websocket_thread

    if _eventlet_active():
        _spawn_websocket_subprocess()
        # Register signal handlers so Ctrl+C in dev forwards cleanly. Under
        # systemd these are typically replaced by the unit's signal handling.
        try:
            signal.signal(signal.SIGINT, signal_handler)
            if hasattr(signal, "SIGTERM"):
                signal.signal(signal.SIGTERM, signal_handler)
        except Exception as e:
            logger.warning(f"Could not register signal handlers: {e}")
        return None

    logger.debug("Starting WebSocket proxy server in a separate thread")

    def run_websocket_server():
        """Run the WebSocket server in an event loop"""
        global _websocket_proxy_instance
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Import here to avoid circular imports
            import os

            from dotenv import load_dotenv

            from .server import WebSocketProxy

            load_dotenv()
            ws_host = os.getenv("WEBSOCKET_HOST", "127.0.0.1")
            ws_port = int(os.getenv("WEBSOCKET_PORT", "8765"))

            # Create and store the proxy instance
            _websocket_proxy_instance = WebSocketProxy(host=ws_host, port=ws_port)

            # Start the proxy
            loop.run_until_complete(_websocket_proxy_instance.start())

        except Exception as e:
            logger.exception(f"Error in WebSocket server thread: {e}")
            _websocket_proxy_instance = None
        finally:
            # Always close the event loop to prevent FD leak
            if loop is not None:
                try:
                    # Cancel all pending tasks
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    # Run until all tasks are cancelled
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    loop.close()
                    logger.debug("Event loop closed successfully")
                except Exception as loop_err:
                    logger.warning(f"Error closing event loop: {loop_err}")

    # Start the WebSocket server in a daemon thread
    _websocket_thread = _original_threading.Thread(
        target=run_websocket_server,
        daemon=False,  # Changed to False so we can properly clean up
    )
    _websocket_thread.start()

    # Register cleanup handlers
    atexit.register(cleanup_websocket_server)

    # Register signal handlers for graceful shutdown
    try:
        # SIGINT (Ctrl+C) - Available on all platforms
        signal.signal(signal.SIGINT, signal_handler)
        signals_registered = ["SIGINT"]

        # SIGTERM - Available on Unix-like systems (Mac, Linux)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, signal_handler)
            signals_registered.append("SIGTERM")

        logger.debug(f"Signal handlers registered: {', '.join(signals_registered)}")
    except Exception as e:
        logger.warning(f"Could not register signal handlers: {e}")

    logger.debug("WebSocket proxy server thread started")
    return _websocket_thread


def start_websocket_proxy(app):
    """
    Integrate the WebSocket proxy server with a Flask application.
    This should be called during app initialization.

    Args:
        app: Flask application instance
    """
    global _websocket_server_started

    # Check if this process should start the WebSocket server
    if should_start_websocket():
        # Our flag will prevent multiple starts if called multiple times
        if not _websocket_server_started:
            _websocket_server_started = True
            logger.debug("Starting WebSocket server in Flask application process")
            start_websocket_server()
            logger.debug("WebSocket server integration with Flask complete")
        else:
            logger.debug("WebSocket server already running, skipping initialization")
    else:
        logger.debug("Skipping WebSocket server in parent/monitor process")

```


---

# FILE: websocket_proxy\base_adapter.py

```py
import json
import os
import random
import socket
import threading
from abc import ABC, abstractmethod

import zmq

from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# =============================================================================
# Connection Pool Configuration
# =============================================================================
# These settings control how the websocket_proxy handles broker symbol limits.
# Most brokers limit symbols per WebSocket connection (e.g., Angel: 1000, Zerodha: 3000).
# The connection pool automatically creates additional connections when limits are reached.

# Maximum symbols per single WebSocket connection
# Set lower than broker limits to be safe (Angel=1000, Zerodha=3000)
MAX_SYMBOLS_PER_WEBSOCKET = int(os.getenv("MAX_SYMBOLS_PER_WEBSOCKET", "1000"))

# Maximum WebSocket connections per user/broker
# Total capacity = MAX_SYMBOLS_PER_WEBSOCKET × MAX_WEBSOCKET_CONNECTIONS
MAX_WEBSOCKET_CONNECTIONS = int(os.getenv("MAX_WEBSOCKET_CONNECTIONS", "3"))

# Enable/disable connection pooling globally
# When disabled, falls back to single connection per broker
ENABLE_CONNECTION_POOLING = os.getenv("ENABLE_CONNECTION_POOLING", "true").lower() == "true"


def is_port_available(port):
    """
    Check if a port is available for use
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.settimeout(1.0)
            s.bind(("127.0.0.1", port))
            return True
    except OSError:
        return False


def find_free_zmq_port(start_port=5556, max_attempts=50):
    """
    Find an available port starting from start_port that's not already bound

    Args:
        start_port (int): Port number to start the search from
        max_attempts (int): Maximum number of attempts to find a free port

    Returns:
        int: Available port number, or None if no port is available
    """
    # Create logger here instead of using self.logger because this is a standalone function
    logger = get_logger("zmq_port_finder")

    # First check if any ports in the bound_ports set are actually free now
    # This handles cases where the process that had the port died without cleanup
    with BaseBrokerWebSocketAdapter._port_lock:
        ports_to_remove = [
            port for port in BaseBrokerWebSocketAdapter._bound_ports if is_port_available(port)
        ]

        # Remove ports that are actually available now
        for port in ports_to_remove:
            BaseBrokerWebSocketAdapter._bound_ports.remove(port)
            logger.info(f"Port {port} removed from bound ports registry")

    # Now find a new free port
    for _ in range(max_attempts):
        # Try a sequential port first, then random if that fails
        if start_port not in BaseBrokerWebSocketAdapter._bound_ports and is_port_available(
            start_port
        ):
            return start_port

        # Try a random port between start_port and 65535
        random_port = random.randint(start_port, 65535)
        if random_port not in BaseBrokerWebSocketAdapter._bound_ports and is_port_available(
            random_port
        ):
            return random_port

        start_port = min(start_port + 1, 65000)

    # If we get here, we couldn't find an available port
    logger.error("Failed to find an available port after maximum attempts")
    return None


class BaseBrokerWebSocketAdapter(ABC):
    """
    Base class for all broker-specific WebSocket adapters that implements
    common functionality and defines the interface for broker-specific implementations.
    """

    # Class variable to track bound ports across instances
    _bound_ports = set()
    _port_lock = threading.Lock()
    _shared_context = None
    _context_lock = threading.Lock()
    _instance_count = 0  # Track active adapter instances for cleanup decisions

    def __init__(self, use_shared_zmq: bool = False, shared_publisher=None):
        """
        Initialize the base broker adapter.

        Args:
            use_shared_zmq: If True, use a shared ZeroMQ publisher instead of creating one.
                           This is used by ConnectionPool for multi-connection support.
            shared_publisher: The shared publisher instance to use when use_shared_zmq=True
        """
        self.logger = get_logger("broker_adapter")
        self.logger.info("BaseBrokerWebSocketAdapter initializing")

        # Track instance count for shared context cleanup decisions
        with self._context_lock:
            BaseBrokerWebSocketAdapter._instance_count += 1
            self.logger.debug(f"Adapter instance count: {BaseBrokerWebSocketAdapter._instance_count}")

        # Check if being created within a ConnectionPool context
        # This handles the case where broker adapters don't forward kwargs to super().__init__()
        try:
            from .connection_manager import (
                get_shared_publisher_for_pooled_creation,
                is_pooled_creation,
            )

            if is_pooled_creation():
                use_shared_zmq = True
                shared_publisher = get_shared_publisher_for_pooled_creation()
                self.logger.info("Detected pooled creation context - using shared ZMQ")
        except ImportError:
            pass  # connection_manager not available, use provided params

        # Track if using shared ZMQ (for connection pooling)
        self._uses_shared_zmq = use_shared_zmq
        self._shared_publisher = shared_publisher

        try:
            if use_shared_zmq and shared_publisher:
                # Use shared publisher's socket instead of creating own
                self.socket = shared_publisher.socket
                self.zmq_port = shared_publisher.zmq_port
                self.context = shared_publisher.context
                self.logger.info(f"Using shared ZMQ publisher on port {self.zmq_port}")
            else:
                # Initialize own ZeroMQ context and socket
                self._initialize_shared_context()

                # Create socket and bind to port
                self.socket = self._create_socket()
                self.zmq_port = self._bind_to_available_port()
                os.environ["ZMQ_PORT"] = str(self.zmq_port)
                self.logger.info(f"BaseBrokerWebSocketAdapter initialized on port {self.zmq_port}")

            # Initialize instance variables
            self.subscriptions = {}
            self.connected = False

        except Exception as e:
            self.logger.exception(f"Error in BaseBrokerWebSocketAdapter init: {e}")
            raise

    def _initialize_shared_context(self):
        """
        Initialize shared ZeroMQ context if not already created
        """
        with self._context_lock:
            if not BaseBrokerWebSocketAdapter._shared_context:
                self.logger.info("Creating shared ZMQ context")
                BaseBrokerWebSocketAdapter._shared_context = zmq.Context()

        self.context = BaseBrokerWebSocketAdapter._shared_context

    def _create_socket(self):
        """
        Create and configure ZeroMQ socket
        """
        with self._context_lock:
            socket = self.context.socket(zmq.PUB)
            socket.setsockopt(zmq.LINGER, 1000)  # 1 second linger
            socket.setsockopt(zmq.SNDHWM, 1000)  # High water mark
            return socket

    def _bind_to_available_port(self):
        """
        Find an available port and bind the socket to it.
        If binding fails, closes the socket to prevent FD leak.
        """
        # Internal message bus — bind only to the configured ZMQ_HOST (loopback by default).
        # Publishing on `tcp://*` would expose raw tick data to anyone who can reach the port.
        bind_host = os.getenv("ZMQ_HOST", "127.0.0.1")
        with self._port_lock:
            # Try default port from environment first
            default_port = int(os.getenv("ZMQ_PORT", "5555"))

            if default_port not in self._bound_ports and is_port_available(default_port):
                try:
                    self.socket.bind(f"tcp://{bind_host}:{default_port}")
                    self._bound_ports.add(default_port)
                    self.logger.info(f"Bound to default port {default_port} on {bind_host}")
                    return default_port
                except zmq.ZMQError as e:
                    self.logger.warning(f"Failed to bind to default port {default_port}: {e}")

            # Find random available port
            for attempt in range(5):
                port = find_free_zmq_port(start_port=5556 + random.randint(0, 1000))

                if not port:
                    self.logger.warning(f"Failed to find free port on attempt {attempt + 1}")
                    continue

                try:
                    self.socket.bind(f"tcp://{bind_host}:{port}")
                    self._bound_ports.add(port)
                    self.logger.info(f"Successfully bound to port {port} on {bind_host}")
                    return port
                except zmq.ZMQError as e:
                    self.logger.warning(f"Failed to bind to port {port}: {e}")
                    continue

            # All binding attempts failed - clean up socket to prevent FD leak
            try:
                if hasattr(self, "socket") and self.socket:
                    self.socket.close(linger=0)
                    self.socket = None
                    self.logger.warning("Closed socket after failed binding attempts")
            except Exception as cleanup_err:
                self.logger.warning(f"Error closing socket after bind failure: {cleanup_err}")

            raise RuntimeError("Could not bind to any available ZMQ port after multiple attempts")

    @abstractmethod
    def initialize(self, broker_name, user_id, auth_data=None):
        """
        Initialize connection with broker WebSocket API

        Args:
            broker_name: The name of the broker (e.g., 'angel', 'zerodha')
            user_id: The user's ID or client code
            auth_data: Dict containing authentication data, if not provided will fetch from DB
        """
        pass

    @abstractmethod
    def subscribe(self, symbol, exchange, mode=2, depth_level=5):
        """
        Subscribe to market data with the specified mode and depth level

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            exchange: Exchange code (e.g., 'NSE', 'BSE')
            mode: Subscription mode - 1:LTP, 2:Quote, 4:Depth
            depth_level: Market depth level (5, 20, or 30 depending on broker support)

        Returns:
            dict: Response with status and capability information
        """
        pass

    @abstractmethod
    def unsubscribe(self, symbol, exchange, mode=2):
        """
        Unsubscribe from market data

        Args:
            symbol: Trading symbol
            exchange: Exchange code
            mode: Subscription mode

        Returns:
            dict: Response with status
        """
        pass

    @abstractmethod
    def connect(self):
        """
        Establish connection to the broker's WebSocket
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        Disconnect from the broker's WebSocket
        """
        pass

    def cleanup_zmq(self):
        """
        Properly clean up ZeroMQ resources and release bound ports.
        Skips cleanup if using shared ZeroMQ publisher (connection pooling mode).
        Also manages shared context lifecycle based on instance count.

        This method is idempotent - calling it multiple times is safe.
        """
        # Prevent double cleanup (e.g., explicit cleanup followed by __del__)
        if hasattr(self, "_zmq_cleaned_up") and self._zmq_cleaned_up:
            return
        self._zmq_cleaned_up = True

        # Skip cleanup if using shared ZMQ (managed by ConnectionPool)
        if hasattr(self, "_uses_shared_zmq") and self._uses_shared_zmq:
            self.logger.debug("Skipping ZMQ cleanup - using shared publisher")
            # Still decrement instance count (only once due to _zmq_cleaned_up flag)
            with self._context_lock:
                BaseBrokerWebSocketAdapter._instance_count = max(0, BaseBrokerWebSocketAdapter._instance_count - 1)
            return

        try:
            # Release the port from the bound ports set
            if hasattr(self, "zmq_port") and self.zmq_port:
                with self._port_lock:
                    self._bound_ports.discard(self.zmq_port)
                    self.logger.info(f"Released port {self.zmq_port}")

            # Close the socket
            if hasattr(self, "socket") and self.socket:
                self.socket.close(linger=0)  # Don't linger on close
                self.socket = None
                self.logger.info("ZeroMQ socket closed")

            # Decrement instance count and cleanup shared context if last instance
            with self._context_lock:
                BaseBrokerWebSocketAdapter._instance_count = max(0, BaseBrokerWebSocketAdapter._instance_count - 1)
                self.logger.debug(f"Adapter instance count after cleanup: {BaseBrokerWebSocketAdapter._instance_count}")

                # If this was the last instance, clean up shared context
                if BaseBrokerWebSocketAdapter._instance_count == 0 and BaseBrokerWebSocketAdapter._shared_context:
                    self.logger.info("Last adapter instance - cleaning up shared ZMQ context")
                    try:
                        BaseBrokerWebSocketAdapter._shared_context.term()
                    except Exception as ctx_err:
                        self.logger.warning(f"Error terminating shared context: {ctx_err}")
                    finally:
                        BaseBrokerWebSocketAdapter._shared_context = None

        except Exception as e:
            self.logger.exception(f"Error cleaning up ZeroMQ resources: {e}")

    def __del__(self):
        """
        Destructor to ensure ZeroMQ resources are properly cleaned up
        """
        try:
            self.cleanup_zmq()
        except Exception as e:
            # Can't use self.logger here as it might be gone during destruction
            logger.exception(f"Error in __del__ cleaning up ZMQ resources: {e}")
            pass

    @classmethod
    def cleanup_shared_context(cls):
        """
        Force cleanup of shared ZeroMQ context.

        Call this during app shutdown or restart to ensure all ZMQ resources
        are released, even if individual adapters weren't properly cleaned up.
        This is useful for scenarios where the app restarts without a full
        process exit.
        """
        with cls._context_lock:
            if cls._shared_context:
                try:
                    logger.info("Force cleaning up shared ZMQ context")
                    cls._shared_context.term()
                except Exception as e:
                    logger.warning(f"Error during forced context cleanup: {e}")
                finally:
                    cls._shared_context = None
                    cls._instance_count = 0

            # Also clear bound ports registry
            with cls._port_lock:
                if cls._bound_ports:
                    logger.info(f"Clearing {len(cls._bound_ports)} bound ports from registry")
                    cls._bound_ports.clear()

    @classmethod
    def get_resource_stats(cls) -> dict:
        """
        Get statistics about ZMQ resources for health monitoring.

        Returns:
            dict: Resource statistics including instance count and bound ports
        """
        with cls._context_lock:
            with cls._port_lock:
                return {
                    "active_adapter_instances": cls._instance_count,
                    "bound_ports_count": len(cls._bound_ports),
                    "bound_ports": list(cls._bound_ports),
                    "shared_context_active": cls._shared_context is not None,
                }

    def publish_market_data(self, topic, data):
        """
        Publish market data to ZeroMQ subscribers

        Args:
            topic: Topic string for subscriber filtering (e.g., 'NSE_RELIANCE_LTP')
            data: Market data dictionary
        """
        try:
            if self._uses_shared_zmq and self._shared_publisher:
                # Use shared publisher (connection pooling mode)
                self._shared_publisher.publish(topic, data)
            elif self.socket:
                # Use own socket
                self.socket.send_multipart(
                    [topic.encode("utf-8"), json.dumps(data).encode("utf-8")]
                )
            else:
                self.logger.warning("No ZMQ socket available for publishing")
        except Exception as e:
            self.logger.exception(f"Error publishing market data: {e}")

    def _create_success_response(self, message, **kwargs):
        """
        Create a standard success response
        """
        response = {"status": "success", "message": message}
        response.update(kwargs)
        return response

    def _create_error_response(self, code, message):
        """
        Create a standard error response
        """
        return {"status": "error", "code": code, "message": message}

    # =========================================================================
    # Authentication Helper Methods (Issue #765 - Stale Token Handling)
    # =========================================================================
    # These methods provide a standardized way for broker adapters to handle
    # authentication, including automatic retry with fresh tokens on 403 errors.

    def get_auth_token_for_user(self, user_id: str, bypass_cache: bool = False):
        """
        Get authentication token for a user with optional cache bypass.

        This is the recommended method for broker adapters to retrieve auth tokens.
        Use bypass_cache=True after receiving a 403 error to get fresh credentials.

        Args:
            user_id: The user's ID
            bypass_cache: If True, skip cache and query database directly

        Returns:
            The decrypted auth token, or None if not found/revoked
        """
        try:
            from database.auth_db import get_auth_token
            return get_auth_token(user_id, bypass_cache=bypass_cache)
        except Exception as e:
            self.logger.exception(f"Error getting auth token for user {user_id}: {e}")
            return None

    def get_fresh_auth_token(self, user_id: str):
        """
        Get fresh authentication token directly from database, bypassing cache.

        Use this method after receiving a 403/401 error to get the latest token.
        This clears the local cache entry and fetches fresh data from database.

        See GitHub issue #765 for details on the stale token problem this solves.

        Args:
            user_id: The user's ID

        Returns:
            The decrypted auth token, or None if not found/revoked
        """
        self.logger.info(f"Fetching fresh auth token for user {user_id} (bypassing cache)")
        return self.get_auth_token_for_user(user_id, bypass_cache=True)

    def clear_auth_cache_for_user(self, user_id: str):
        """
        Clear all cached authentication data for a user.

        Call this when you detect stale credentials (e.g., 403 error from broker).
        The next call to get_auth_token will fetch fresh data from database.

        Args:
            user_id: The user's ID
        """
        try:
            from database.auth_db import (
                auth_cache,
                feed_token_cache,
            )

            cache_key_auth = f"auth-{user_id}"
            cache_key_feed = f"feed-{user_id}"

            caches_cleared = []
            if cache_key_auth in auth_cache:
                del auth_cache[cache_key_auth]
                caches_cleared.append("auth_cache")
            if cache_key_feed in feed_token_cache:
                del feed_token_cache[cache_key_feed]
                caches_cleared.append("feed_token_cache")
            # Note: broker_cache is keyed by API key, not user_id, so we skip it here
            # It only caches broker names which don't affect auth token validation

            if caches_cleared:
                self.logger.info(f"Cleared auth caches for user {user_id}: {', '.join(caches_cleared)}")
            else:
                self.logger.debug(f"No cached auth data found for user {user_id}")

        except Exception as e:
            self.logger.exception(f"Error clearing auth cache for user {user_id}: {e}")

    def is_auth_error(self, error_message: str) -> bool:
        """
        Check if an error message indicates an authentication failure.

        Use this to detect when to retry with fresh credentials.

        Args:
            error_message: The error message string

        Returns:
            True if the error indicates authentication failure (401/403)
        """
        if not error_message:
            return False

        error_lower = str(error_message).lower()
        auth_error_indicators = [
            "401",
            "403",
            "unauthorized",
            "forbidden",
            "authentication failed",
            "auth failed",
            "invalid token",
            "token expired",
            "access denied",
            "invalid credentials",
            "session expired",
        ]
        return any(indicator in error_lower for indicator in auth_error_indicators)

    def handle_auth_error_and_retry(self, user_id: str, retry_func, *args, **kwargs):
        """
        Handle authentication errors with automatic retry using fresh credentials.

        This method implements the database fallback pattern from issue #765:
        1. If an operation fails with 403/401, clear the cached token
        2. Fetch fresh token from database
        3. Retry the operation once with the new token

        Args:
            user_id: The user's ID for token refresh
            retry_func: The function to retry (should accept auth_token as first arg)
            *args: Additional positional arguments for retry_func
            **kwargs: Additional keyword arguments for retry_func

        Returns:
            The result of retry_func, or None if retry also fails
        """
        try:
            self.logger.info(f"Handling auth error for user {user_id} - fetching fresh token")

            # Clear stale cache
            self.clear_auth_cache_for_user(user_id)

            # Get fresh token from database
            fresh_token = self.get_fresh_auth_token(user_id)
            if not fresh_token:
                self.logger.error(f"No valid token found in database for user {user_id}")
                return None

            self.logger.info(f"Retrying operation with fresh token for user {user_id}")

            # Retry with fresh token
            return retry_func(fresh_token, *args, **kwargs)

        except Exception as e:
            self.logger.exception(f"Retry with fresh token failed for user {user_id}: {e}")
            return None

```


---

# FILE: websocket_proxy\broker_factory.py

```py
import importlib
from typing import Dict, Optional, Type

from utils.logging import get_logger

from .base_adapter import (
    ENABLE_CONNECTION_POOLING,
    MAX_SYMBOLS_PER_WEBSOCKET,
    MAX_WEBSOCKET_CONNECTIONS,
    BaseBrokerWebSocketAdapter,
)
from .connection_manager import ConnectionPool

logger = get_logger(__name__)

# Registry of all supported broker adapters
BROKER_ADAPTERS: dict[str, type[BaseBrokerWebSocketAdapter]] = {}

# Registry of pooled adapters (one pool per user_id + broker combination)
_POOLED_ADAPTERS: dict[str, ConnectionPool] = {}


def register_adapter(broker_name: str, adapter_class: type[BaseBrokerWebSocketAdapter]) -> None:
    """
    Register a broker adapter class for a specific broker

    Args:
        broker_name: Name of the broker
        adapter_class: Class that implements the BaseBrokerWebSocketAdapter interface
    """
    BROKER_ADAPTERS[broker_name.lower()] = adapter_class


def _get_adapter_class(broker_name: str) -> type[BaseBrokerWebSocketAdapter]:
    """
    Get the adapter class for a broker (without instantiating).

    Args:
        broker_name: Name of the broker

    Returns:
        The adapter class

    Raises:
        ValueError: If broker is not supported
    """
    broker_name = broker_name.lower()

    # Check if adapter is registered
    if broker_name in BROKER_ADAPTERS:
        return BROKER_ADAPTERS[broker_name]

    # Try dynamic import if not registered
    try:
        # Try to import from broker-specific directory first
        module_name = f"broker.{broker_name}.streaming.{broker_name}_adapter"
        class_name = f"{broker_name.capitalize()}WebSocketAdapter"

        try:
            module = importlib.import_module(module_name)
            adapter_class = getattr(module, class_name)
            register_adapter(broker_name, adapter_class)
            return adapter_class
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not import from broker-specific path: {e}")

            # Try websocket_proxy directory as fallback
            module_name = f"websocket_proxy.{broker_name}_adapter"
            module = importlib.import_module(module_name)
            adapter_class = getattr(module, class_name)
            register_adapter(broker_name, adapter_class)
            return adapter_class

    except (ImportError, AttributeError) as e:
        logger.exception(f"Failed to load adapter for broker {broker_name}: {e}")
        raise ValueError(f"Unsupported broker: {broker_name}. No adapter available.")


def create_broker_adapter(
    broker_name: str, use_pooling: bool | None = None
) -> BaseBrokerWebSocketAdapter | None:
    """
    Create an instance of the appropriate broker adapter.

    When connection pooling is enabled, returns a ConnectionPool that automatically
    manages multiple WebSocket connections to handle symbol limits.

    Args:
        broker_name: Name of the broker (e.g., 'angel', 'zerodha')
        use_pooling: Override for connection pooling. If None, uses global setting.

    Returns:
        BaseBrokerWebSocketAdapter or ConnectionPool: An adapter instance

    Raises:
        ValueError: If the broker is not supported
    """
    broker_name = broker_name.lower()

    # Determine if pooling should be used
    pooling_enabled = use_pooling if use_pooling is not None else ENABLE_CONNECTION_POOLING

    # Get the adapter class
    adapter_class = _get_adapter_class(broker_name)

    if pooling_enabled:
        logger.info(
            f"Creating pooled adapter for broker: {broker_name} "
            f"(max {MAX_SYMBOLS_PER_WEBSOCKET} symbols × {MAX_WEBSOCKET_CONNECTIONS} connections)"
        )
        # Return a ConnectionPool wrapper
        # Note: The pool is initialized later with user_id via initialize() method
        return _PooledAdapterWrapper(adapter_class, broker_name)
    else:
        logger.info(f"Creating single adapter for broker: {broker_name} (pooling disabled)")
        return adapter_class()


class _PooledAdapterWrapper:
    """
    Wrapper that creates a ConnectionPool when initialized with user_id.
    Provides the same interface as BaseBrokerWebSocketAdapter.
    """

    def __init__(self, adapter_class: type, broker_name: str):
        self._adapter_class = adapter_class
        self._broker_name = broker_name
        self._pool: ConnectionPool | None = None
        self._user_id: str | None = None
        self.logger = get_logger(f"pooled_adapter_{broker_name}")

    def _ensure_pool(self, user_id: str) -> ConnectionPool:
        """Create or get existing pool for this user"""
        if self._pool is None:
            pool_key = f"{self._broker_name}_{user_id}"

            # Check if pool already exists for this user
            if pool_key in _POOLED_ADAPTERS:
                self._pool = _POOLED_ADAPTERS[pool_key]
                self.logger.info(f"Reusing existing pool for {pool_key}")
            else:
                self._pool = ConnectionPool(
                    adapter_class=self._adapter_class,
                    broker_name=self._broker_name,
                    user_id=user_id,
                    max_symbols_per_connection=MAX_SYMBOLS_PER_WEBSOCKET,
                    max_connections=MAX_WEBSOCKET_CONNECTIONS,
                )
                _POOLED_ADAPTERS[pool_key] = self._pool
                self.logger.info(
                    f"Created new connection pool for {pool_key}: "
                    f"max {MAX_SYMBOLS_PER_WEBSOCKET} symbols × {MAX_WEBSOCKET_CONNECTIONS} connections"
                )

            self._user_id = user_id

        return self._pool

    def initialize(self, broker_name: str, user_id: str, auth_data: dict = None, force: bool = False):
        """Initialize the pool with user credentials

        Args:
            broker_name: The broker name
            user_id: The user ID
            auth_data: Optional authentication data
            force: If True, force re-initialization with fresh credentials (issue #765)
        """
        pool = self._ensure_pool(user_id)
        return pool.initialize(broker_name, user_id, auth_data, force=force)

    def connect(self):
        """Connect the pool"""
        if self._pool:
            return self._pool.connect()
        return {"success": False, "error": "Not initialized"}

    def disconnect(self):
        """Disconnect and cleanup the pool"""
        if self._pool:
            self._pool.disconnect()
            # Remove from global registry
            pool_key = f"{self._broker_name}_{self._user_id}"
            _POOLED_ADAPTERS.pop(pool_key, None)

    def subscribe(self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5):
        """Subscribe to market data"""
        if self._pool:
            return self._pool.subscribe(symbol, exchange, mode, depth_level)
        return {"status": "error", "message": "Not initialized"}

    def unsubscribe(self, symbol: str, exchange: str, mode: int = 2):
        """Unsubscribe from market data"""
        if self._pool:
            return self._pool.unsubscribe(symbol, exchange, mode)
        return {"status": "error", "message": "Not initialized"}

    def unsubscribe_all(self):
        """Unsubscribe from all symbols"""
        if self._pool:
            self._pool.unsubscribe_all()

    def get_stats(self) -> dict:
        """Get pool statistics"""
        if self._pool:
            return self._pool.get_stats()
        return {}

    @property
    def subscriptions(self) -> dict:
        """Get current subscriptions"""
        if self._pool:
            return self._pool.subscriptions
        return {}

    @property
    def connected(self) -> bool:
        """Check if pool is connected"""
        if self._pool:
            return self._pool.connected
        return False

    def publish_market_data(self, topic: str, data: dict):
        """Publish market data through the pool"""
        if self._pool:
            self._pool.publish_market_data(topic, data)

    # =========================================================================
    # Authentication Helper Methods (Issue #765 - Stale Token Handling)
    # =========================================================================
    # These methods delegate to the underlying adapter or implement the logic
    # directly for handling stale auth tokens in multi-process deployments.

    def is_auth_error(self, error_message: str) -> bool:
        """
        Check if an error message indicates an authentication failure.

        Args:
            error_message: The error message string

        Returns:
            True if the error indicates authentication failure (401/403)
        """
        if not error_message:
            return False

        error_lower = str(error_message).lower()
        auth_error_indicators = [
            "401",
            "403",
            "unauthorized",
            "forbidden",
            "authentication failed",
            "auth failed",
            "invalid token",
            "token expired",
            "access denied",
            "invalid credentials",
            "session expired",
        ]
        return any(indicator in error_lower for indicator in auth_error_indicators)

    def clear_auth_cache_for_user(self, user_id: str):
        """
        Clear all cached authentication data for a user.

        Call this when you detect stale credentials (e.g., 403 error from broker).

        Args:
            user_id: The user's ID
        """
        try:
            from database.auth_db import (
                auth_cache,
                feed_token_cache,
            )

            cache_key_auth = f"auth-{user_id}"
            cache_key_feed = f"feed-{user_id}"

            caches_cleared = []
            if cache_key_auth in auth_cache:
                del auth_cache[cache_key_auth]
                caches_cleared.append("auth_cache")
            if cache_key_feed in feed_token_cache:
                del feed_token_cache[cache_key_feed]
                caches_cleared.append("feed_token_cache")
            # Note: broker_cache is keyed by API key, not user_id, so we skip it here
            # It only caches broker names which don't affect auth token validation

            if caches_cleared:
                self.logger.info(f"Cleared auth caches for user {user_id}: {', '.join(caches_cleared)}")
            else:
                self.logger.debug(f"No cached auth data found for user {user_id}")

        except Exception as e:
            self.logger.exception(f"Error clearing auth cache for user {user_id}: {e}")


def get_pool_stats(broker_name: str = None) -> dict:
    """
    Get statistics for all connection pools or a specific broker.

    Args:
        broker_name: Optional broker name to filter stats

    Returns:
        Dictionary with pool statistics
    """
    stats = {}
    for pool_key, pool in _POOLED_ADAPTERS.items():
        if broker_name is None or pool_key.startswith(broker_name):
            stats[pool_key] = pool.get_stats()
    return stats


def cleanup_all_pools():
    """Disconnect and cleanup all connection pools"""
    for pool_key, pool in list(_POOLED_ADAPTERS.items()):
        try:
            pool.disconnect()
        except Exception as e:
            logger.exception(f"Error cleaning up pool {pool_key}: {e}")
    _POOLED_ADAPTERS.clear()


def cleanup_pools_for_user(user_id: str, broker_name: str | None = None) -> int:
    """Tear down cached connection pools tied to ``user_id``.

    Called by ``database.auth_db.upsert_auth`` whenever fresh broker
    credentials are persisted (login, re-login, token refresh). Without this
    targeted invalidation, the next websocket connect re-uses the cached
    pool from before the auth refresh — which still holds the stale token
    that initialised it — and the user sees ``Adapter initialization
    failed: No authentication token found`` until they restart the whole
    process. See marketcalls/openalgo#1394 for the user-visible symptom.

    Args:
        user_id: OpenAlgo username whose pools should be discarded.
        broker_name: Optional. When set, only that broker's pool is
            discarded; otherwise every pool keyed by this user is purged.

    Returns:
        Count of pools removed.
    """
    if not user_id:
        return 0

    targets: list[str] = []
    suffix = f"_{user_id}"
    for pool_key in list(_POOLED_ADAPTERS.keys()):
        if not pool_key.endswith(suffix):
            continue
        if broker_name is not None and not pool_key.startswith(f"{broker_name}_"):
            continue
        targets.append(pool_key)

    for pool_key in targets:
        pool = _POOLED_ADAPTERS.pop(pool_key, None)
        if pool is None:
            continue
        try:
            pool.disconnect()
        except Exception as e:
            # Best-effort: even if disconnect raises, the pool is already
            # detached from the registry so the next connect rebuilds.
            logger.warning(f"Error disconnecting pool {pool_key} during invalidation: {e}")

    if targets:
        logger.info(
            f"Invalidated {len(targets)} cached pool(s) for user={user_id}"
            + (f" broker={broker_name}" if broker_name else "")
        )
    return len(targets)


def get_resource_health() -> dict:
    """
    Get comprehensive health statistics for all WebSocket proxy resources.

    This is useful for monitoring file descriptors, memory usage, and
    connection health across all broker adapters and pools.

    Returns:
        dict: Health statistics including:
            - adapter_resources: ZMQ socket and context stats
            - registered_adapters: Count of registered broker adapters
            - active_pools: Stats for each active connection pool
    """
    try:
        adapter_stats = BaseBrokerWebSocketAdapter.get_resource_stats()
    except Exception as e:
        logger.warning(f"Error getting adapter stats: {e}")
        adapter_stats = {"error": str(e)}

    pool_stats = {}
    for pool_key, pool in _POOLED_ADAPTERS.items():
        try:
            pool_stats[pool_key] = pool.get_stats()
        except Exception as e:
            pool_stats[pool_key] = {"error": str(e)}

    return {
        "adapter_resources": adapter_stats,
        "registered_adapters": {
            "count": len(BROKER_ADAPTERS),
            "brokers": list(BROKER_ADAPTERS.keys()),
        },
        "active_pools": {
            "count": len(_POOLED_ADAPTERS),
            "pools": pool_stats,
        },
    }

```


---

# FILE: websocket_proxy\connection_manager.py

```py
"""
Connection Manager for WebSocket Proxy

Handles multiple WebSocket connections per broker to overcome symbol limits.
Each broker typically limits symbols per WebSocket session (e.g., Angel: 1000, Zerodha: 3000).
This module manages connection pooling transparently without modifying broker adapters.

Configuration:
    MAX_SYMBOLS_PER_WEBSOCKET: Maximum symbols per single WebSocket connection (default: 1000)
    MAX_WEBSOCKET_CONNECTIONS: Maximum WebSocket connections per user/broker (default: 3)
"""

import json
import os
import threading
from collections import defaultdict
from collections.abc import Callable
from typing import Any, Dict, List, Optional, Tuple

import zmq

from utils.logging import get_logger

logger = get_logger(__name__)

# Thread-local storage for pooled adapter creation context
# This allows BaseBrokerWebSocketAdapter to detect when it's being created
# within a ConnectionPool and skip its own ZMQ socket creation
_pooled_creation_context = threading.local()


def is_pooled_creation() -> bool:
    """Check if we're currently creating an adapter within a ConnectionPool"""
    return getattr(_pooled_creation_context, "active", False)


def get_shared_publisher_for_pooled_creation():
    """Get the shared publisher during pooled adapter creation"""
    return getattr(_pooled_creation_context, "shared_publisher", None)


# Default configuration - can be overridden via environment variables
DEFAULT_MAX_SYMBOLS_PER_WEBSOCKET = 1000
DEFAULT_MAX_WEBSOCKET_CONNECTIONS = 3


def get_max_symbols_per_websocket() -> int:
    """Get maximum symbols per WebSocket connection from config"""
    return int(os.getenv("MAX_SYMBOLS_PER_WEBSOCKET", DEFAULT_MAX_SYMBOLS_PER_WEBSOCKET))


def get_max_websocket_connections() -> int:
    """Get maximum WebSocket connections from config"""
    return int(os.getenv("MAX_WEBSOCKET_CONNECTIONS", DEFAULT_MAX_WEBSOCKET_CONNECTIONS))


# Keywords used to recognize auth-related failures returned by broker adapters.
# Matches 401/403 plus the common token-expiry phrasings emitted by broker REST
# APIs and WS clients. Used by ConnectionPool to decide whether a connect or
# subscribe failure is recoverable via a forced re-init that reads a fresh
# token from auth_db. See issue #1419.
_AUTH_ERROR_INDICATORS = (
    "401",
    "403",
    "unauthorized",
    "forbidden",
    "authentication failed",
    "auth failed",
    "invalid token",
    "token expired",
    "access token has expired",
    "access denied",
    "invalid credentials",
    "session expired",
)


def _is_auth_error(error_message: str) -> bool:
    """True if ``error_message`` looks like an auth failure (401/403/expired)."""
    if not error_message:
        return False
    msg = str(error_message).lower()
    return any(indicator in msg for indicator in _AUTH_ERROR_INDICATORS)


class SharedZmqPublisher:
    """
    Shared ZeroMQ publisher that can be used by multiple adapter instances.
    Ensures all connections publish to the same ZeroMQ socket, so the WebSocketProxy
    receives data from all connections on a single port.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern to ensure only one shared publisher exists"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.logger = get_logger("shared_zmq_publisher")
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.setsockopt(zmq.LINGER, 1000)
        self.socket.setsockopt(zmq.SNDHWM, 1000)
        self.zmq_port = None
        self._bound = False
        self._publish_lock = threading.Lock()

    def bind(self, port: int | None = None) -> int:
        """
        Bind to a ZeroMQ port. If already bound, returns existing port.

        Args:
            port: Optional specific port to bind to

        Returns:
            The port number that was bound
        """
        if self._bound:
            return self.zmq_port

        with self._lock:
            if self._bound:
                return self.zmq_port

            # Internal message bus — bind only to the configured ZMQ_HOST
            # (loopback by default). Publishing on `tcp://*` would expose raw
            # tick data to anyone who can reach the port. Mirrors the bind
            # behavior in websocket_proxy/base_adapter.py so both publisher
            # paths are reachable from the proxy at the same address.
            # Operators who genuinely need multi-host setups can set
            # ZMQ_HOST=0.0.0.0 explicitly.
            bind_host = os.getenv("ZMQ_HOST", "127.0.0.1")

            # Try specified port or find available one
            if port:
                try:
                    self.socket.bind(f"tcp://{bind_host}:{port}")
                    self.zmq_port = port
                    self._bound = True
                    os.environ["ZMQ_PORT"] = str(port)
                    self.logger.info(
                        f"Shared ZMQ publisher bound to {bind_host}:{port}"
                    )
                    return port
                except zmq.ZMQError as e:
                    self.logger.warning(f"Failed to bind to port {port}: {e}")

            # Find available port
            default_port = int(os.getenv("ZMQ_PORT", "5555"))
            for attempt_port in range(default_port, default_port + 100):
                try:
                    self.socket.bind(f"tcp://{bind_host}:{attempt_port}")
                    self.zmq_port = attempt_port
                    self._bound = True
                    os.environ["ZMQ_PORT"] = str(attempt_port)
                    self.logger.info(
                        f"Shared ZMQ publisher bound to {bind_host}:{attempt_port}"
                    )
                    return attempt_port
                except zmq.ZMQError:
                    continue

            raise RuntimeError("Could not bind shared ZMQ publisher to any port")

    def publish(self, topic: str, data: dict):
        """
        Publish market data to ZeroMQ subscribers.
        Thread-safe publishing.

        Args:
            topic: Topic string for subscriber filtering
            data: Market data dictionary
        """
        if not self._bound:
            self.logger.error("Cannot publish: ZMQ socket not bound")
            return

        with self._publish_lock:
            try:
                self.socket.send_multipart(
                    [topic.encode("utf-8"), json.dumps(data).encode("utf-8")]
                )
            except Exception as e:
                self.logger.exception(f"Error publishing to ZMQ: {e}")

    def cleanup(self):
        """Clean up ZeroMQ resources with separate error handling for each step"""
        # Close socket first (separate try/except to ensure context.term() is attempted)
        try:
            if self.socket:
                self.socket.close(linger=0)
        except Exception as e:
            self.logger.warning(f"Error closing shared ZMQ socket: {e}")
        finally:
            self.socket = None

        # Terminate context (always attempt even if socket.close() failed)
        try:
            if self.context:
                self.context.term()
        except Exception as e:
            self.logger.warning(f"Error terminating shared ZMQ context: {e}")
        finally:
            self.context = None

        # Reset state
        self._bound = False
        self._initialized = False
        SharedZmqPublisher._instance = None
        self.logger.info("Shared ZMQ publisher cleaned up")


class ConnectionPool:
    """
    Manages multiple WebSocket connections for a single broker/user.

    Automatically creates new connections when symbol limits are reached,
    up to the configured maximum. Distributes subscriptions across connections
    and aggregates data from all connections through a shared ZeroMQ publisher.

    Usage:
        pool = ConnectionPool(
            adapter_class=AngelWebSocketAdapter,
            broker_name='angel',
            user_id='user123'
        )
        pool.initialize()
        pool.connect()
        pool.subscribe('RELIANCE', 'NSE', mode=2)
    """

    def __init__(
        self,
        adapter_class: type,
        broker_name: str,
        user_id: str,
        max_symbols_per_connection: int | None = None,
        max_connections: int | None = None,
    ):
        """
        Initialize the connection pool.

        Args:
            adapter_class: The broker adapter class to instantiate
            broker_name: Name of the broker (e.g., 'angel', 'zerodha')
            user_id: User ID for authentication
            max_symbols_per_connection: Max symbols per WebSocket (default from config)
            max_connections: Max WebSocket connections (default from config)
        """
        self.adapter_class = adapter_class
        self.broker_name = broker_name
        self.user_id = user_id
        self.max_symbols = max_symbols_per_connection or get_max_symbols_per_websocket()
        self.max_connections = max_connections or get_max_websocket_connections()

        self.logger = get_logger(f"connection_pool_{broker_name}")
        self.lock = threading.RLock()

        # Connection tracking
        self.adapters: list[Any] = []  # List of adapter instances
        self.adapter_symbol_counts: list[int] = []  # Symbols per adapter

        # Subscription tracking: (symbol, exchange, mode) -> adapter_index
        self.subscription_map: dict[tuple[str, str, int], int] = {}
        # Per-subscription depth_level so auth-recovery restore can re-issue
        # mode=3 (Depth) at its originally requested depth, not the default.
        self.subscription_depths: dict[tuple[str, str, int], int] = {}

        # Shared ZeroMQ publisher
        self.shared_publisher = SharedZmqPublisher()

        # State
        self.initialized = False
        self.connected = False

        # Peak usage tracking (for logging purposes)
        self.peak_total_symbols = 0
        self.peak_connections_used = 0
        self.peak_symbol_counts = []  # Snapshot of counts at peak

        self.logger.info("[POOL] ========== CONNECTION POOL INITIALIZED ==========")
        self.logger.info(f"[POOL] Broker: {broker_name} | User: {user_id}")
        self.logger.info(
            f"[POOL] Config: {self.max_symbols} symbols/connection x {self.max_connections} max connections = {self.max_symbols * self.max_connections} total capacity"
        )
        self.logger.info("[POOL] ==================================================")

    def _create_adapter(self) -> Any:
        """
        Create a new adapter instance configured to use the shared ZeroMQ publisher.

        Returns:
            New adapter instance
        """
        # Ensure shared publisher is bound
        self.shared_publisher.bind()

        # Set context flag so BaseBrokerWebSocketAdapter knows to skip ZMQ creation
        _pooled_creation_context.active = True
        _pooled_creation_context.shared_publisher = self.shared_publisher

        try:
            # Create adapter instance
            # BaseBrokerWebSocketAdapter will detect the context and skip ZMQ socket creation
            adapter = self.adapter_class()

            # Override the adapter's publish method to use shared publisher
            def shared_publish(topic: str, data: dict):
                self.shared_publisher.publish(topic, data)

            adapter.publish_market_data = shared_publish

            # Mark that this adapter uses shared ZMQ (to skip individual cleanup)
            adapter._uses_shared_zmq = True
            adapter._shared_publisher = self.shared_publisher

            return adapter

        finally:
            # Clear context flag
            _pooled_creation_context.active = False
            _pooled_creation_context.shared_publisher = None

    def _get_adapter_with_capacity(self) -> tuple[int, Any]:
        """
        Get an adapter with available capacity, or create a new one.

        Returns:
            Tuple of (adapter_index, adapter_instance)

        Raises:
            RuntimeError: If max connections reached and all are full
        """
        with self.lock:
            # Find adapter with capacity
            for idx, count in enumerate(self.adapter_symbol_counts):
                if count < self.max_symbols:
                    return idx, self.adapters[idx]

            # Need new adapter
            if len(self.adapters) >= self.max_connections:
                total_symbols = sum(self.adapter_symbol_counts)
                raise RuntimeError(
                    f"Maximum capacity reached: {self.max_connections} connections × "
                    f"{self.max_symbols} symbols = {self.max_connections * self.max_symbols} symbols. "
                    f"Currently subscribed to {total_symbols} symbols."
                )

            # Create new adapter
            prev_conn_symbols = self.adapter_symbol_counts[-1] if self.adapter_symbol_counts else 0
            total_symbols = sum(self.adapter_symbol_counts)
            self.logger.info(
                f"[POOL] Creating NEW connection {len(self.adapters) + 1}/{self.max_connections} "
                f"for {self.broker_name} (previous connection full: {prev_conn_symbols}/{self.max_symbols} symbols, "
                f"total subscribed: {total_symbols})"
            )

            adapter = self._create_adapter()

            # Initialize and connect the new adapter
            adapter.initialize(self.broker_name, self.user_id)
            adapter.connect()

            self.adapters.append(adapter)
            self.adapter_symbol_counts.append(0)

            return len(self.adapters) - 1, adapter

    def _get_existing_modes(self, symbol: str, exchange: str) -> dict[int, int]:
        """
        Return {mode: adapter_idx} for all tracked subscriptions of this symbol/exchange.
        Must be called while holding self.lock.
        """
        return {
            m: idx
            for (s, e, m), idx in self.subscription_map.items()
            if s == symbol and e == exchange
        }

    def initialize(
        self, broker_name: str = None, user_id: str = None, auth_data: dict = None, force: bool = False
    ) -> dict:
        """
        Initialize the connection pool with the first adapter.

        Args:
            broker_name: Optional broker name override
            user_id: Optional user ID override
            auth_data: Optional authentication data
            force: If True, force re-initialization even if already initialized.
                   Used for retrying with fresh credentials after auth errors (issue #765).

        Returns:
            Initialization result dict
        """
        if self.initialized and not force:
            return {"success": True, "message": "Already initialized"}

        with self.lock:
            # If forcing re-initialization, clean up existing adapters first (inside lock to prevent race conditions)
            if force and self.initialized:
                self.logger.info(f"Force re-initializing pool for {self.broker_name} with fresh credentials")
                # Disconnect existing adapters
                for adapter in self.adapters:
                    try:
                        adapter.disconnect()
                    except Exception as e:
                        self.logger.warning(f"Error disconnecting adapter during re-init: {e}")
                self.adapters.clear()
                self.adapter_symbol_counts.clear()
                self.subscription_map.clear()
                self.subscription_depths.clear()
                self.connected = False
                self.initialized = False
            try:
                # Use provided values or defaults
                self.broker_name = broker_name or self.broker_name
                self.user_id = user_id or self.user_id

                # Ensure shared publisher is ready
                self.shared_publisher.bind()

                # Create first adapter
                adapter = self._create_adapter()
                result = adapter.initialize(self.broker_name, self.user_id, auth_data)

                # Handle both response formats from adapters:
                # - {"success": False, "error": "..."} (ConnectionPool format)
                # - {"status": "error", "code": "...", "message": "..."} (Adapter format)
                is_error = (
                    (result and result.get("success") == False) or
                    (result and result.get("status") == "error")
                )
                if is_error:
                    error_msg = result.get("message", result.get("error", "Initialization failed"))
                    self.logger.error(f"Adapter initialization failed: {error_msg}")
                    return {"success": False, "error": error_msg}

                self.adapters.append(adapter)
                self.adapter_symbol_counts.append(0)
                self.initialized = True

                self.logger.info(f"ConnectionPool initialized for {self.broker_name}")
                return {"success": True, "message": "Connection pool initialized"}

            except Exception as e:
                self.logger.exception(f"Failed to initialize connection pool: {e}")
                return {"success": False, "error": str(e)}

    def _clear_auth_cache_for_user(self) -> None:
        """Drop cached auth tokens for this pool's user.

        The next ``initialize(force=True)`` then re-reads from ``auth_db`` and
        constructs adapters with the fresh token. Called when an auth error is
        detected on connect/subscribe (issue #1419).
        """
        try:
            from database.auth_db import auth_cache, feed_token_cache

            cleared = []
            if f"auth-{self.user_id}" in auth_cache:
                del auth_cache[f"auth-{self.user_id}"]
                cleared.append("auth_cache")
            if f"feed-{self.user_id}" in feed_token_cache:
                del feed_token_cache[f"feed-{self.user_id}"]
                cleared.append("feed_token_cache")
            if cleared:
                self.logger.info(
                    f"Cleared auth caches for user {self.user_id}: {', '.join(cleared)}"
                )
        except Exception as e:
            self.logger.warning(f"Error clearing auth cache for user {self.user_id}: {e}")

    def _attempt_auth_recovery(self, error_msg: str) -> bool:
        """Rebuild the pool with a fresh token after an auth failure.

        Tears down the existing adapter (which was constructed with a stale
        token), clears cached auth state, re-initializes the pool — which
        re-reads the token from ``auth_db`` — and reconnects. Existing
        subscriptions are snapshotted before the rebuild and re-issued on the
        new adapter so callers don't silently lose their feeds.

        Does not recurse into ``self.connect()``; it calls the adapter's
        ``connect()`` directly on the freshly rebuilt adapter. Returns ``True``
        when the post-refresh reconnect succeeds.
        """
        self.logger.warning(
            f"Auth error on {self.broker_name} (user={self.user_id}): {error_msg}. "
            f"Refreshing token and rebuilding pool."
        )

        # Snapshot (symbol, exchange, mode, depth_level) before
        # initialize(force=True) clears subscription_map / subscription_depths.
        with self.lock:
            prior_subs = [
                (s, e, m, self.subscription_depths.get((s, e, m), 5))
                for (s, e, m) in self.subscription_map
            ]

        self._clear_auth_cache_for_user()
        reinit = self.initialize(force=True)
        if not reinit.get("success"):
            self.logger.error(
                f"Pool re-initialization after auth error failed: {reinit.get('error')}"
            )
            return False
        if not self.adapters:
            return False
        result = self.adapters[0].connect()
        is_error = (result and result.get("success") is False) or (
            result and result.get("status") == "error"
        )
        if is_error:
            err = result.get("message", result.get("error", "Connection failed"))
            self.logger.error(f"Reconnect after auth refresh failed: {err}")
            return False
        self.connected = True

        if prior_subs:
            self.logger.info(
                f"Restoring {len(prior_subs)} subscription(s) after auth refresh"
            )
            restored = 0
            for symbol, exchange, mode, depth in prior_subs:
                try:
                    sub_result = self._subscribe_inner(symbol, exchange, mode, depth)
                    if sub_result.get("status") == "success":
                        restored += 1
                    else:
                        self.logger.warning(
                            f"Failed to restore {symbol}.{exchange} mode={mode}: "
                            f"{sub_result.get('message')}"
                        )
                except Exception as e:
                    self.logger.warning(
                        f"Error restoring {symbol}.{exchange} mode={mode}: {e}"
                    )
            self.logger.info(
                f"Restored {restored}/{len(prior_subs)} subscriptions after auth refresh"
            )

        self.logger.info(
            f"Auth recovery succeeded for {self.broker_name} (user={self.user_id})"
        )
        return True

    def connect(self) -> dict:
        """
        Connect the first adapter in the pool.
        Additional connections are created on-demand when capacity is needed.

        Returns:
            Connection result dict
        """
        if not self.initialized:
            return {"success": False, "error": "Not initialized"}

        if self.connected:
            return {"success": True, "message": "Already connected"}

        with self.lock:
            try:
                if self.adapters:
                    result = self.adapters[0].connect()
                    # Handle both response formats from adapters:
                    # - {"success": False, "error": "..."} (ConnectionPool format)
                    # - {"status": "error", "code": "...", "message": "..."} (Adapter format)
                    is_error = (
                        (result and result.get("success") == False) or
                        (result and result.get("status") == "error")
                    )
                    if is_error:
                        error_msg = result.get("message", result.get("error", "Connection failed"))
                        # Issue #1419: try recovery once if this looks like a stale
                        # auth token (new trading day, etc.) before surfacing the
                        # error. _attempt_auth_recovery() does not call back into
                        # self.connect(), so no recursion; _recovering guards against
                        # repeat attempts on the same call.
                        if _is_auth_error(error_msg) and not getattr(self, "_recovering", False):
                            self._recovering = True
                            try:
                                if self._attempt_auth_recovery(error_msg):
                                    return {"success": True, "message": "Connected after auth refresh"}
                            finally:
                                self._recovering = False
                        self.logger.error(f"Adapter connection failed: {error_msg}")
                        return {"success": False, "error": error_msg}
                    self.connected = True
                    return {"success": True, "message": "Connected"}
                else:
                    return {"success": False, "error": "No adapters available"}

            except Exception as e:
                err_str = str(e)
                # Some adapters raise instead of returning an error dict; apply the
                # same recovery path if the exception message looks auth-related.
                if _is_auth_error(err_str) and not getattr(self, "_recovering", False):
                    self._recovering = True
                    try:
                        if self._attempt_auth_recovery(err_str):
                            return {"success": True, "message": "Connected after auth refresh"}
                    finally:
                        self._recovering = False
                self.logger.exception(f"Failed to connect: {e}")
                return {"success": False, "error": err_str}

    def subscribe(self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5) -> dict:
        """
        Subscribe to market data, automatically using connection with capacity.

        Implements mode hierarchy: Depth (3) > Quote (2) > LTP (1).
        Higher modes include all data from lower modes, so only the highest
        requested mode is sent to the broker. All requested modes are tracked
        in subscription_map so unsubscribe can downgrade correctly.

        Issue #1419: if the underlying subscribe fails with what looks like a
        stale auth token, the pool tears itself down, re-reads the token from
        ``auth_db``, and retries once.

        Args:
            symbol: Trading symbol
            exchange: Exchange code
            mode: Subscription mode (1=LTP, 2=Quote, 3=Depth)
            depth_level: Market depth level

        Returns:
            Subscription result dict
        """
        result = self._subscribe_inner(symbol, exchange, mode, depth_level)

        if (
            isinstance(result, dict)
            and result.get("status") == "error"
            and _is_auth_error(result.get("message", ""))
            and not getattr(self, "_recovering", False)
        ):
            self._recovering = True
            try:
                if self._attempt_auth_recovery(result.get("message", "")):
                    result = self._subscribe_inner(symbol, exchange, mode, depth_level)
            finally:
                self._recovering = False

        return result

    def _subscribe_inner(
        self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5
    ) -> dict:
        """Core subscribe logic without the auth-recovery wrapper.

        ``subscribe()`` wraps this so it can retry once after a forced pool
        refresh when an auth error is detected.
        """
        sub_key = (symbol, exchange, mode)

        with self.lock:
            # Already subscribed in this exact mode
            if sub_key in self.subscription_map:
                return {
                    "status": "success",
                    "message": f"Already subscribed to {symbol}.{exchange}",
                    "connection": self.subscription_map[sub_key] + 1,
                }

            existing_modes = self._get_existing_modes(symbol, exchange)
            highest_existing = max(existing_modes.keys()) if existing_modes else 0

            try:
                if existing_modes:
                    # Reuse the same adapter as existing subscriptions
                    adapter_idx = existing_modes[highest_existing]
                    adapter = self.adapters[adapter_idx]

                    if mode > highest_existing:
                        # UPGRADE: new mode is higher — tell broker to switch up
                        result = adapter.subscribe(symbol, exchange, mode, depth_level)
                        if result.get("status") == "success":
                            self.subscription_map[sub_key] = adapter_idx
                            self.subscription_depths[sub_key] = depth_level
                            # Don't increment adapter_symbol_counts — same symbol, already counted
                            result["connection"] = adapter_idx + 1
                            self.logger.info(
                                f"[POOL] Upgraded {symbol}.{exchange} from mode {highest_existing} "
                                f"to mode {mode} on connection {adapter_idx + 1}"
                            )
                        return result
                    else:
                        # COVERED: higher mode already active — just track, skip broker call
                        self.subscription_map[sub_key] = adapter_idx
                        self.subscription_depths[sub_key] = depth_level
                        # Don't increment adapter_symbol_counts — same symbol, already counted
                        self.logger.debug(
                            f"Tracked {symbol}.{exchange} mode {mode} "
                            f"(covered by active mode {highest_existing})"
                        )
                        return {
                            "status": "success",
                            "message": f"Subscribed to {symbol}.{exchange} (covered by mode {highest_existing})",
                            "connection": adapter_idx + 1,
                        }
                else:
                    # NEW SYMBOL: normal path
                    adapter_idx, adapter = self._get_adapter_with_capacity()
                    result = adapter.subscribe(symbol, exchange, mode, depth_level)

                    if result.get("status") == "success":
                        self.subscription_map[sub_key] = adapter_idx
                        self.subscription_depths[sub_key] = depth_level
                        self.adapter_symbol_counts[adapter_idx] += 1
                        symbols_on_conn = self.adapter_symbol_counts[adapter_idx]
                        total_symbols = sum(self.adapter_symbol_counts)

                        # Update peak usage tracking
                        if total_symbols > self.peak_total_symbols:
                            self.peak_total_symbols = total_symbols
                            self.peak_connections_used = len(self.adapters)
                            self.peak_symbol_counts = list(self.adapter_symbol_counts)

                        # Add connection info to result
                        result["connection"] = adapter_idx + 1
                        result["total_connections"] = len(self.adapters)
                        result["symbols_on_connection"] = symbols_on_conn

                        # Log at key milestones
                        if symbols_on_conn == 1:
                            self.logger.info(
                                f"[POOL] Connection {adapter_idx + 1} started - "
                                f"first symbol: {symbol}.{exchange}"
                            )
                        elif symbols_on_conn % 100 == 0 or symbols_on_conn == self.max_symbols:
                            capacity_pct = (symbols_on_conn / self.max_symbols) * 100
                            self.logger.info(
                                f"[POOL] Connection {adapter_idx + 1}: "
                                f"{symbols_on_conn}/{self.max_symbols} symbols "
                                f"({capacity_pct:.0f}% full) | Total: {total_symbols} "
                                f"symbols across {len(self.adapters)} connection(s)"
                            )

                        self.logger.debug(
                            f"Subscribed {symbol}.{exchange} on connection {adapter_idx + 1}, "
                            f"symbols: {symbols_on_conn}/{self.max_symbols}"
                        )

                    return result

            except RuntimeError as e:
                # Max capacity reached
                return {"status": "error", "code": "MAX_CAPACITY_REACHED", "message": str(e)}
            except Exception as e:
                self.logger.exception(f"Error subscribing to {symbol}.{exchange}: {e}")
                return {"status": "error", "code": "SUBSCRIPTION_ERROR", "message": str(e)}

    def unsubscribe(self, symbol: str, exchange: str, mode: int = 2) -> dict:
        """
        Unsubscribe from market data.

        Implements mode hierarchy awareness: when the highest mode is removed but
        lower modes remain, the broker subscription is downgraded rather than
        fully removed. When a lower mode is removed while a higher mode is still
        active, only the tracking entry is removed (no broker call needed).

        Args:
            symbol: Trading symbol
            exchange: Exchange code
            mode: Subscription mode

        Returns:
            Unsubscription result dict
        """
        sub_key = (symbol, exchange, mode)

        with self.lock:
            if sub_key not in self.subscription_map:
                return {
                    "status": "error",
                    "code": "NOT_SUBSCRIBED",
                    "message": f"Not subscribed to {symbol}.{exchange}",
                }

            try:
                adapter_idx = self.subscription_map[sub_key]
                adapter = self.adapters[adapter_idx]

                # Remove tracking entry. Stash the prior depth so rollback paths
                # below can restore both maps atomically if the broker call fails.
                old_depth = self.subscription_depths.get(sub_key, 5)
                del self.subscription_map[sub_key]
                self.subscription_depths.pop(sub_key, None)

                # Check what modes remain for this symbol
                remaining_modes = self._get_existing_modes(symbol, exchange)

                if not remaining_modes:
                    # LAST mode removed — fully unsubscribe from broker
                    result = adapter.unsubscribe(symbol, exchange, mode)
                    if result.get("status") == "success":
                        self.adapter_symbol_counts[adapter_idx] -= 1
                        self.logger.debug(
                            f"Fully unsubscribed {symbol}.{exchange} from connection "
                            f"{adapter_idx + 1}, remaining: {self.adapter_symbol_counts[adapter_idx]}"
                        )
                    else:
                        # Rollback tracking on failure
                        self.subscription_map[sub_key] = adapter_idx
                        self.subscription_depths[sub_key] = old_depth
                    return result

                else:
                    new_highest = max(remaining_modes.keys())

                    if mode > new_highest:
                        # DOWNGRADE: removed the highest mode, broker needs to switch down
                        adapter.unsubscribe(symbol, exchange, mode)
                        result = adapter.subscribe(symbol, exchange, new_highest, 5)
                        if result.get("status") == "success":
                            self.logger.info(
                                f"[POOL] Downgraded {symbol}.{exchange} from mode {mode} "
                                f"to mode {new_highest} on connection {adapter_idx + 1}"
                            )
                            return {
                                "status": "success",
                                "message": f"Unsubscribed mode {mode}, downgraded to mode {new_highest}",
                            }
                        else:
                            # Re-subscribe failed — rollback: restore tracking and try to
                            # re-subscribe at the old mode so the symbol isn't left dangling
                            self.logger.error(
                                f"[POOL] Failed to downgrade {symbol}.{exchange} to mode "
                                f"{new_highest}, rolling back: {result}"
                            )
                            self.subscription_map[sub_key] = adapter_idx
                            self.subscription_depths[sub_key] = old_depth
                            adapter.subscribe(symbol, exchange, mode, old_depth)
                            return {
                                "status": "error",
                                "code": "DOWNGRADE_FAILED",
                                "message": f"Failed to downgrade {symbol}.{exchange} to mode {new_highest}",
                            }
                    else:
                        # Removed a lower mode — broker still has the higher mode active
                        # No broker call needed
                        self.logger.debug(
                            f"Removed {symbol}.{exchange} mode {mode} tracking "
                            f"(broker still at mode {new_highest})"
                        )
                        return {
                            "status": "success",
                            "message": f"Unsubscribed from {symbol}.{exchange} mode {mode}",
                        }

            except Exception as e:
                # Rollback tracking on exception
                if sub_key not in self.subscription_map:
                    self.subscription_map[sub_key] = adapter_idx
                    self.subscription_depths[sub_key] = old_depth
                self.logger.exception(f"Error unsubscribing from {symbol}.{exchange}: {e}")
                return {"status": "error", "code": "UNSUBSCRIPTION_ERROR", "message": str(e)}

    def unsubscribe_all(self):
        """Unsubscribe from all symbols across all connections"""
        with self.lock:
            # Log stats before clearing
            total_symbols = sum(self.adapter_symbol_counts) if self.adapter_symbol_counts else 0
            num_connections = len(self.adapters)

            if total_symbols > 0:
                self.logger.info("[POOL] ========== UNSUBSCRIBING ALL ==========")
                self.logger.info(f"[POOL] Connections used: {num_connections}")
                self.logger.info(f"[POOL] Total symbols subscribed: {total_symbols}")
                for idx, count in enumerate(self.adapter_symbol_counts):
                    if count > 0:
                        self.logger.info(
                            f"[POOL]   Connection {idx + 1}: {count}/{self.max_symbols} symbols ({(count / self.max_symbols) * 100:.0f}%)"
                        )
                self.logger.info("[POOL] ==========================================")

            for adapter in self.adapters:
                if hasattr(adapter, "unsubscribe_all"):
                    adapter.unsubscribe_all()

            self.subscription_map.clear()
            self.subscription_depths.clear()
            self.adapter_symbol_counts = [0] * len(self.adapters)

            self.logger.info("[POOL] Unsubscribed from all symbols")

    def disconnect(self):
        """Disconnect all adapters and clean up"""
        with self.lock:
            # Log PEAK usage (not current, since unsubscribes may have already happened)
            self.logger.info("[POOL] ========== DISCONNECTING POOL ==========")
            self.logger.info(f"[POOL] Peak connections used: {self.peak_connections_used}")
            self.logger.info(f"[POOL] Peak symbols subscribed: {self.peak_total_symbols}")
            for idx, count in enumerate(self.peak_symbol_counts):
                self.logger.info(
                    f"[POOL]   Connection {idx + 1}: {count}/{self.max_symbols} symbols ({(count / self.max_symbols) * 100:.0f}%)"
                )
            self.logger.info("[POOL] ==========================================")

            for idx, adapter in enumerate(self.adapters):
                original_cleanup = None
                try:
                    # Skip ZMQ cleanup for adapters using shared publisher
                    if hasattr(adapter, "_uses_shared_zmq") and adapter._uses_shared_zmq:
                        # Temporarily disable ZMQ cleanup
                        original_cleanup = getattr(adapter, "cleanup_zmq", None)
                        adapter.cleanup_zmq = lambda: None

                    adapter.disconnect()

                    self.logger.debug(f"Disconnected connection {idx + 1}")
                except Exception as e:
                    self.logger.exception(f"Error disconnecting adapter {idx + 1}: {e}")
                finally:
                    # Always restore original cleanup method to prevent resource leaks
                    if original_cleanup is not None:
                        try:
                            adapter.cleanup_zmq = original_cleanup
                        except Exception:
                            pass  # Adapter may already be in bad state

            self.adapters.clear()
            self.adapter_symbol_counts.clear()
            self.subscription_map.clear()
            self.connected = False
            self.initialized = False

            # Reset peak counters for next session
            self.peak_total_symbols = 0
            self.peak_connections_used = 0
            self.peak_symbol_counts = []

            self.logger.info("[POOL] ConnectionPool disconnected successfully")

    def get_stats(self) -> dict:
        """
        Get pool statistics.

        Returns:
            Dict with pool statistics
        """
        with self.lock:
            total_symbols = sum(self.adapter_symbol_counts)
            max_capacity = self.max_connections * self.max_symbols

            return {
                "broker": self.broker_name,
                "user_id": self.user_id,
                "active_connections": len(self.adapters),
                "max_connections": self.max_connections,
                "max_symbols_per_connection": self.max_symbols,
                "total_subscriptions": total_symbols,
                "max_capacity": max_capacity,
                "capacity_used_percent": (total_symbols / max_capacity * 100)
                if max_capacity > 0
                else 0,
                "connections": [
                    {
                        "index": idx + 1,
                        "symbols": count,
                        "capacity_percent": (count / self.max_symbols * 100),
                    }
                    for idx, count in enumerate(self.adapter_symbol_counts)
                ],
            }

    # Compatibility methods to match BaseBrokerWebSocketAdapter interface

    @property
    def subscriptions(self) -> dict:
        """Get subscriptions dict for compatibility"""
        return {
            f"{k[0]}_{k[1]}_{k[2]}": {"symbol": k[0], "exchange": k[1], "mode": k[2]}
            for k in self.subscription_map.keys()
        }

    def publish_market_data(self, topic: str, data: dict):
        """Publish market data through shared publisher"""
        self.shared_publisher.publish(topic, data)


def create_pooled_adapter(
    adapter_class: type,
    broker_name: str,
    max_symbols_per_connection: int | None = None,
    max_connections: int | None = None,
) -> Callable:
    """
    Factory function to create a pooled adapter factory.

    This returns a function that can be used in place of direct adapter instantiation,
    providing transparent connection pooling.

    Args:
        adapter_class: The broker adapter class
        broker_name: Name of the broker
        max_symbols_per_connection: Optional override for max symbols
        max_connections: Optional override for max connections

    Returns:
        A factory function that creates ConnectionPool instances
    """

    def factory():
        # The pool will be initialized with user_id later
        # Return a wrapper that creates the pool on first use
        class PooledAdapterWrapper:
            def __init__(self):
                self._pool = None
                self._adapter_class = adapter_class
                self._broker_name = broker_name
                self._max_symbols = max_symbols_per_connection
                self._max_connections = max_connections

            def _ensure_pool(self, user_id: str) -> ConnectionPool:
                if self._pool is None:
                    self._pool = ConnectionPool(
                        adapter_class=self._adapter_class,
                        broker_name=self._broker_name,
                        user_id=user_id,
                        max_symbols_per_connection=self._max_symbols,
                        max_connections=self._max_connections,
                    )
                return self._pool

            def initialize(self, broker_name: str, user_id: str, auth_data: dict = None):
                pool = self._ensure_pool(user_id)
                return pool.initialize(broker_name, user_id, auth_data)

            def connect(self):
                if self._pool:
                    return self._pool.connect()
                return {"success": False, "error": "Not initialized"}

            def disconnect(self):
                if self._pool:
                    self._pool.disconnect()

            def subscribe(self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5):
                if self._pool:
                    return self._pool.subscribe(symbol, exchange, mode, depth_level)
                return {"status": "error", "message": "Not initialized"}

            def unsubscribe(self, symbol: str, exchange: str, mode: int = 2):
                if self._pool:
                    return self._pool.unsubscribe(symbol, exchange, mode)
                return {"status": "error", "message": "Not initialized"}

            def unsubscribe_all(self):
                if self._pool:
                    self._pool.unsubscribe_all()

            def get_stats(self):
                if self._pool:
                    return self._pool.get_stats()
                return {}

            @property
            def subscriptions(self):
                if self._pool:
                    return self._pool.subscriptions
                return {}

            def publish_market_data(self, topic: str, data: dict):
                if self._pool:
                    self._pool.publish_market_data(topic, data)

        return PooledAdapterWrapper()

    return factory

```


---

# FILE: websocket_proxy\mapping.py

```py
from database.symbol import SymToken
from database.token_db import get_brexchange, get_token
from utils.logging import get_logger


class ExchangeMapper:
    """Base class for mapping OpenAlgo exchange codes to broker-specific exchange types"""

    @staticmethod
    def get_exchange_type(exchange, broker):
        """
        Convert exchange code to broker-specific exchange type

        This is a base implementation that should be overridden by broker-specific mappers.

        Args:
            exchange (str): Exchange code (e.g., 'NSE', 'BSE')
            broker (str): Broker name

        Returns:
            int: Broker-specific exchange type
        """
        # This method should be implemented by broker-specific exchange mappers
        # Default to a common value (1 typically represents NSE in most brokers)
        return 1


class SymbolMapper:
    """Maps OpenAlgo symbols to broker-specific tokens"""

    logger = get_logger("symbol_mapper")

    @staticmethod
    def get_token_from_symbol(symbol, exchange):
        """
        Convert user-friendly symbol to broker-specific token

        Args:
            symbol (str): Trading symbol (e.g., 'RELIANCE')
            exchange (str): Exchange code (e.g., 'NSE', 'BSE')

        Returns:
            dict: Token data with 'token' and 'brexchange' or None if not found
        """
        try:
            # Get token from database
            token = get_token(symbol, exchange)
            brexchange = get_brexchange(symbol, exchange)

            if not token or not brexchange:
                SymbolMapper.logger.error(f"Symbol not found: {symbol}-{exchange}")
                return None

            return {"token": token, "brexchange": brexchange}
        except Exception as e:
            SymbolMapper.logger.exception(f"Error retrieving symbol: {e}")
            return None


class BrokerCapabilityRegistry:
    """
    Base class for broker capability registries

    This class defines the interface for broker-specific capability registries.
    Each broker should implement its own capability registry that can be queried
    for supported features.
    """

    @classmethod
    def get_supported_depth_levels(cls, broker, exchange):
        """
        Get supported depth levels for a broker and exchange

        Args:
            broker (str): Broker name
            exchange (str): Exchange code

        Returns:
            list: List of supported depth levels
        """
        # This method should be implemented by broker-specific capability registries
        # By default, assume support for the standard 5-level depth
        return [5]

    @classmethod
    def is_depth_level_supported(cls, broker, exchange, depth_level):
        """
        Check if a depth level is supported for the given broker and exchange

        Args:
            broker (str): Broker name
            exchange (str): Exchange code
            depth_level (int): Requested depth level

        Returns:
            bool: True if supported, False otherwise
        """
        supported_depths = cls.get_supported_depth_levels(broker, exchange)
        return depth_level in supported_depths

    @classmethod
    def get_fallback_depth_level(cls, broker, exchange, requested_depth):
        """
        Get the best available depth level as a fallback

        Args:
            broker (str): Broker name
            exchange (str): Exchange code
            requested_depth (int): Requested depth level

        Returns:
            int: Highest supported depth level that is ≤ requested depth
        """
        supported_depths = cls.get_supported_depth_levels(broker, exchange)
        # Find the highest supported depth that's less than or equal to requested depth
        fallbacks = [d for d in supported_depths if d <= requested_depth]
        if fallbacks:
            return max(fallbacks)
        return 5  # Default to basic depth

```


---

# FILE: websocket_proxy\mode_utils.py

```py
"""Mode normalization helpers for the WebSocket proxy.

Single source of truth for converting client- or topic-supplied "mode" values
into the canonical (numeric, label) pair used internally and on the wire.

Accepts:
    - int: 1, 2, 3
    - str: "LTP" / "Quote" / "Depth" — case-insensitive ("ltp", "QUOTE",
      "DePtH" all valid; whitespace is stripped).

Returns: (numeric_mode, canonical_label) where labels are always
"LTP" / "Quote" / "Depth" so API responses stay consistent regardless of
input casing.

Raises ValueError for invalid values (out-of-range int, unknown string,
empty string, wrong type — except non-int / non-str which raise TypeError).
Use normalize_mode_or_none() for hot paths that prefer to log+skip instead
of raising (e.g. the ZMQ topic parser in WebSocketProxy.zmq_listener).

This replaces the two prior in-class mappings (MODE_MAP uppercase-only and
mode_mapping CapCase-only) which silently disagreed and let documented
requests like {"mode": "QUOTE"} pass through to broker adapters as the raw
string. See issue #1375.
"""

_MODE_CANONICAL: dict[int, str] = {1: "LTP", 2: "Quote", 3: "Depth"}
_MODE_BY_UPPER_LABEL: dict[str, int] = {"LTP": 1, "QUOTE": 2, "DEPTH": 3}


def normalize_mode(value) -> tuple[int, str]:
    """Return (numeric_mode, canonical_label) for any accepted mode input.

    Raises:
        ValueError: int out of range, unknown string, or empty string.
        TypeError:  value is neither int nor str (or is a bool, which is
                    a subclass of int but disallowed here for safety).
    """
    if isinstance(value, bool):  # bool is a subclass of int — exclude explicitly
        raise TypeError(f"Mode must be int or str, got bool ({value!r})")
    if isinstance(value, int):
        if value not in _MODE_CANONICAL:
            raise ValueError(
                f"Invalid mode {value}; expected 1 (LTP), 2 (Quote), or 3 (Depth)"
            )
        return value, _MODE_CANONICAL[value]
    if isinstance(value, str):
        upper = value.strip().upper()
        if upper not in _MODE_BY_UPPER_LABEL:
            raise ValueError(
                f"Invalid mode {value!r}; expected 'LTP', 'Quote', or 'Depth' (case-insensitive)"
            )
        numeric = _MODE_BY_UPPER_LABEL[upper]
        return numeric, _MODE_CANONICAL[numeric]
    raise TypeError(f"Mode must be int or str, got {type(value).__name__}")


def normalize_mode_or_none(value) -> tuple[int, str] | None:
    """Non-raising variant for hot paths (e.g. ZMQ topic parser).

    Returns None if value is invalid; caller is expected to log and skip.
    """
    try:
        return normalize_mode(value)
    except (ValueError, TypeError):
        return None


# Convenience re-exports for callers that still want the raw mappings.
# Kept private-by-convention (single underscore) so new code is steered to
# the functions above instead.
MODE_BY_UPPER_LABEL = dict(_MODE_BY_UPPER_LABEL)  # {"LTP": 1, "QUOTE": 2, "DEPTH": 3}
MODE_CANONICAL = dict(_MODE_CANONICAL)            # {1: "LTP", 2: "Quote", 3: "Depth"}

```


---

# FILE: websocket_proxy\port_check.py

```py
import socket
import time

from utils.logging import get_logger

logger = get_logger("websocket_proxy")


def is_port_in_use(host, port, wait_time=0):
    """
    Check if a port is already in use on a specific host

    Args:
        host (str): Hostname to check
        port (int): Port number to check
        wait_time (float): Time to wait for port to be released (for cleanup scenarios)

    Returns:
        bool: True if the port is in use, False otherwise
    """
    # If wait_time is specified, check multiple times
    if wait_time > 0:
        attempts = int(wait_time * 10)  # Check every 0.1 seconds
        for attempt in range(attempts):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind((host, port))
                    # Port is not in use
                    return False
                except OSError:
                    if attempt == attempts - 1:  # Last attempt
                        logger.info(
                            f"Port {port} is still in use on {host} after {wait_time}s wait"
                        )
                        return True
                    time.sleep(0.1)  # Wait 0.1 second before next attempt
    else:
        # Single check
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((host, port))
                # Port is not in use
                return False
            except OSError:
                # Port is in use
                logger.info(f"Port {port} is already in use on {host}")
                return True


def find_available_port(start_port=8899, max_attempts=10):
    """
    Find an available port starting from the given port

    Args:
        start_port (int): Port to start searching from
        max_attempts (int): Maximum number of ports to try

    Returns:
        int: Available port number, or None if no port is available
    """
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use("127.0.0.1", port):
            return port

    logger.error(
        f"Could not find an available port after {max_attempts} attempts starting from {start_port}"
    )
    return None

```


---

# FILE: websocket_proxy\server.py

```py
import asyncio as aio
import json
import os
import signal
import socket
import threading
import time
from collections import defaultdict
from typing import Any, Dict, Optional, Set, Tuple

import websockets
import zmq
import zmq.asyncio
from dotenv import load_dotenv
from sqlalchemy import text

from database.auth_db import get_broker_name, verify_api_key
from services.market_data_service import get_market_data_service
from utils.logging import get_logger, highlight_url

from .base_adapter import BaseBrokerWebSocketAdapter
from .broker_factory import create_broker_adapter
from .mode_utils import (
    MODE_BY_UPPER_LABEL as _MODE_BY_UPPER_LABEL,
    normalize_mode,
    normalize_mode_or_none,
)
from .port_check import find_available_port, is_port_in_use

# Initialize logger
logger = get_logger("websocket_proxy")


class WebSocketProxy:
    """
    WebSocket Proxy Server that handles client connections and authentication,
    manages subscriptions, and routes market data from broker adapters to clients.
    Supports dynamic broker selection based on user configuration.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        """
        Initialize the WebSocket Proxy

        Args:
            host: Hostname to bind the WebSocket server to
            port: Port number to bind the WebSocket server to
        """
        self.host = host
        self.port = port

        # Check if the required port is already in use - wait briefly for cleanup to complete
        if is_port_in_use(host, port, wait_time=2.0):  # Wait up to 2 seconds for port release
            error_msg = (
                f"WebSocket port {port} is already in use on {host}.\n"
                f"This port is required for SDK compatibility (see strategies/ltp_example.py).\n"
                f"Please:\n"
                f"1. Stop any other OpenAlgo instances running on port {port}\n"
                f"2. Kill any processes using port {port}: lsof -ti:{port} | xargs kill -9\n"
                f"3. Or wait for the port to be released\n"
                f"Cannot start WebSocket server with port switching as it would break SDK clients."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        self.clients = {}  # Maps client_id to websocket connection
        self.subscriptions = {}  # Maps client_id to set of subscriptions
        self.broker_adapters = {}  # Maps user_id to broker adapter
        self.user_mapping = {}  # Maps client_id to user_id
        self.user_broker_mapping = {}  # Maps user_id to broker_name
        self.running = False

        # PERFORMANCE OPTIMIZATION: Subscription index for O(1) lookup
        # Maps (symbol, exchange, mode) -> set of client_ids
        # This eliminates the need for nested loops in zmq_listener
        self.subscription_index: dict[tuple[str, str, int], set[int]] = defaultdict(set)

        # PERFORMANCE OPTIMIZATION 2: Message throttling to avoid excessive updates
        # Maps (symbol, exchange, mode) -> last message timestamp
        # Prevents sending duplicate LTP updates faster than 50ms
        self.last_message_time: dict[tuple[str, str, int], float] = {}
        self.message_throttle_interval = 0.05  # 50ms minimum between messages

        # MODE_MAP retained for any external consumers that imported it from
        # this class. New code should call normalize_mode() / normalize_mode_or_none()
        # at module level — those accept case-insensitive strings AND ints.
        self.MODE_MAP = dict(_MODE_BY_UPPER_LABEL)

        # RESOURCE MONITORING: Track metrics for health checks
        self._stats_lock = aio.Lock() if hasattr(aio, 'Lock') else None
        self._messages_processed = 0
        self._last_cleanup_time = time.time()
        self._cleanup_interval = 300  # Clean stale entries every 5 minutes
        self._throttle_entry_max_age = 60  # Remove throttle entries older than 60 seconds

        # ZeroMQ context for subscribing to broker adapters
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)
        # Connecting to ZMQ
        ZMQ_HOST = os.getenv("ZMQ_HOST", "127.0.0.1")
        ZMQ_PORT = os.getenv("ZMQ_PORT")
        self.socket.connect(f"tcp://{ZMQ_HOST}:{ZMQ_PORT}")  # Connect to broker adapter publisher

        # Set up ZeroMQ subscriber to receive all messages
        self.socket.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all topics

    async def start(self):
        """Start the WebSocket server and ZeroMQ listener"""
        self.running = True

        try:
            # Start ZeroMQ listener
            logger.debug("Initializing ZeroMQ listener task")

            # Get the current event loop
            loop = aio.get_running_loop()

            # Create the ZMQ listener task
            zmq_task = loop.create_task(self.zmq_listener())

            # Start WebSocket server
            stop = aio.Future()  # Used to stop the server

            # Create a task to monitor the running flag
            async def monitor_shutdown():
                while self.running:
                    await aio.sleep(0.5)
                stop.set_result(None)

            monitor_task = aio.create_task(monitor_shutdown())

            # Handle graceful shutdown
            # Windows doesn't support add_signal_handler, so we'll use a simpler approach
            # Also, when running in a thread on Unix systems, signal handlers can't be set
            try:
                loop = aio.get_running_loop()

                # Check if we're in the main thread
                if threading.current_thread() is threading.main_thread():
                    try:
                        for sig in (signal.SIGINT, signal.SIGTERM):
                            loop.add_signal_handler(sig, stop.set_result, None)
                        logger.debug("Signal handlers registered successfully")
                    except (NotImplementedError, RuntimeError) as e:
                        # On Windows or when in a non-main thread
                        logger.debug(
                            f"Signal handlers not registered: {e}. Using fallback mechanism."
                        )
                else:
                    logger.debug("Running in a non-main thread. Signal handlers will not be used.")
            except RuntimeError:
                logger.debug("No running event loop found for signal handlers")

            highlighted_address = highlight_url(f"{self.host}:{self.port}")
            logger.debug(f"Starting WebSocket server on {highlighted_address}")

            # Try to start the WebSocket server with proper socket options for immediate port reuse
            try:
                # max_queue caps per-client send buffer to absorb tick bursts
                # without prematurely killing slow clients (default 32 was
                # surfacing as "random disconnects" during NIFTY expiry-day
                # storms). ping_interval/ping_timeout are set explicitly so
                # the keepalive contract is locked into the codebase rather
                # than relying on the websockets library defaults.
                ws_max_queue = int(os.getenv("WS_MAX_QUEUE", "1024"))
                ws_ping_interval = int(os.getenv("WS_PING_INTERVAL", "20"))
                ws_ping_timeout = int(os.getenv("WS_PING_TIMEOUT", "20"))

                # Start WebSocket server with socket reuse options
                self.server = await websockets.serve(
                    self.handle_client,
                    self.host,
                    self.port,
                    # Enable socket reuse for immediate port availability after close
                    reuse_port=True if hasattr(socket, "SO_REUSEPORT") else False,
                    max_queue=ws_max_queue,
                    ping_interval=ws_ping_interval,
                    ping_timeout=ws_ping_timeout,
                )

                highlighted_success_address = highlight_url(f"{self.host}:{self.port}")
                logger.debug(
                    f"WebSocket server successfully started on {highlighted_success_address}"
                )

                await stop  # Wait until stopped

                # Cancel the monitor task
                monitor_task.cancel()
                try:
                    await monitor_task
                except aio.CancelledError:
                    pass

                # Properly stop the server and release the port.
                # This calls server.wait_closed() which ensures the socket
                # is fully released before the event loop shuts down.
                await self.stop()

            except Exception as e:
                logger.exception(f"Failed to start WebSocket server: {e}")
                raise

        except Exception as e:
            logger.exception(f"Error in start method: {e}")
            raise

    async def stop(self):
        """Stop the WebSocket server and clean up all resources"""
        logger.info("Stopping WebSocket server...")
        self.running = False

        try:
            # Close the WebSocket server first (this releases the port)
            if hasattr(self, "server") and self.server:
                try:
                    logger.info("Closing WebSocket server...")
                    # On Windows, we need to handle the case where we're in a different event loop
                    try:
                        self.server.close()
                        await self.server.wait_closed()
                        logger.info("WebSocket server closed and port released")
                    except RuntimeError as e:
                        if "attached to a different loop" in str(e):
                            logger.warning(
                                f"WebSocket server cleanup skipped due to event loop mismatch: {e}"
                            )
                            # Force close the server without waiting
                            try:
                                self.server.close()
                            except Exception:
                                pass
                        else:
                            raise
                except Exception as e:
                    logger.exception(f"Error closing WebSocket server: {e}")

            # Close all client connections
            close_tasks = []
            for client_id, websocket in self.clients.items():
                try:
                    if hasattr(websocket, "open") and websocket.open:
                        close_tasks.append(websocket.close())
                except Exception as e:
                    logger.exception(f"Error preparing to close client {client_id}: {e}")

            # Wait for all connections to close with timeout
            if close_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*close_tasks, return_exceptions=True),
                        timeout=2.0,  # 2 second timeout
                    )
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for client connections to close")

            # Disconnect all broker adapters
            for user_id, adapter in self.broker_adapters.items():
                try:
                    adapter.disconnect()
                except Exception as e:
                    logger.exception(f"Error disconnecting adapter for user {user_id}: {e}")

            # Close ZeroMQ socket with linger=0 for immediate close
            if hasattr(self, "socket") and self.socket and not self.socket.closed:
                try:
                    self.socket.setsockopt(zmq.LINGER, 0)  # Don't wait for pending messages
                    self.socket.close()
                except Exception as e:
                    logger.exception(f"Error closing ZMQ socket: {e}")

            # Close ZeroMQ context with timeout
            if hasattr(self, "context") and self.context and not self.context.closed:
                try:
                    self.context.term()
                except Exception as e:
                    logger.exception(f"Error terminating ZMQ context: {e}")

            logger.info("WebSocket server stopped and resources cleaned up")

        except Exception as e:
            logger.exception(f"Error during WebSocket server stop: {e}")

    def _cleanup_zmq_sync(self):
        """
        Synchronous cleanup of ZeroMQ resources.
        Called from __del__ to ensure resources are freed even if stop() is never called.
        """
        try:
            if hasattr(self, "socket") and self.socket:
                try:
                    self.socket.setsockopt(zmq.LINGER, 0)
                    self.socket.close()
                except Exception:
                    pass  # Ignore errors during cleanup
                finally:
                    self.socket = None

            if hasattr(self, "context") and self.context:
                try:
                    self.context.term()
                except Exception:
                    pass  # Ignore errors during cleanup
                finally:
                    self.context = None
        except Exception:
            pass  # Suppress all errors in cleanup

    def __del__(self):
        """
        Destructor to ensure ZeroMQ resources are cleaned up.
        This is a safety net for cases where stop() is never called
        (e.g., exception during start() or unexpected termination).
        """
        try:
            self.running = False
            self._cleanup_zmq_sync()
        except Exception:
            pass  # Cannot raise in __del__

    def get_health_stats(self) -> dict:
        """
        Get health statistics for monitoring file descriptors and resources.

        Returns:
            dict: Health statistics including connection counts, subscription metrics,
                  and resource usage information.
        """
        try:
            # Get base adapter stats if available
            from .base_adapter import BaseBrokerWebSocketAdapter
            adapter_stats = BaseBrokerWebSocketAdapter.get_resource_stats()
        except Exception:
            adapter_stats = {}

        # Calculate subscription index stats
        total_subscriptions = len(self.subscription_index)
        total_client_subscriptions = sum(len(clients) for clients in self.subscription_index.values())
        throttle_entries = len(self.last_message_time)

        return {
            "server": {
                "running": self.running,
                "host": self.host,
                "port": self.port,
            },
            "clients": {
                "connected_count": len(self.clients),
                "user_mappings": len(self.user_mapping),
            },
            "subscriptions": {
                "unique_symbols": total_subscriptions,
                "total_client_subscriptions": total_client_subscriptions,
                "per_client_counts": {
                    str(client_id): len(subs)
                    for client_id, subs in self.subscriptions.items()
                },
            },
            "broker_adapters": {
                "active_count": len(self.broker_adapters),
                "brokers": list(self.user_broker_mapping.values()),
            },
            "performance": {
                "throttle_entries": throttle_entries,
                "messages_processed": self._messages_processed,
                "last_cleanup_time": self._last_cleanup_time,
            },
            "zmq_resources": adapter_stats,
        }

    def _cleanup_stale_throttle_entries(self):
        """
        Remove stale entries from last_message_time dict.

        This prevents unbounded memory growth from symbols that were
        subscribed to but are no longer active.
        """
        current_time = time.time()

        # Only run cleanup periodically
        if current_time - self._last_cleanup_time < self._cleanup_interval:
            return

        self._last_cleanup_time = current_time
        initial_count = len(self.last_message_time)

        # Find and remove stale entries
        stale_keys = [
            key for key, timestamp in self.last_message_time.items()
            if current_time - timestamp > self._throttle_entry_max_age
        ]

        for key in stale_keys:
            del self.last_message_time[key]

        if stale_keys:
            logger.info(
                f"Cleaned up {len(stale_keys)} stale throttle entries "
                f"(was {initial_count}, now {len(self.last_message_time)})"
            )

        # Log subscription index stats periodically
        total_subs = len(self.subscription_index)
        total_clients = len(self.clients)
        if total_subs > 0 or total_clients > 0:
            logger.debug(
                f"Resource stats: {total_clients} clients, "
                f"{total_subs} unique subscriptions, "
                f"{len(self.last_message_time)} throttle entries"
            )

    async def handle_client(self, websocket):
        """
        Handle a client connection

        Args:
            websocket: The WebSocket connection
        """
        client_id = id(websocket)
        self.clients[client_id] = websocket
        self.subscriptions[client_id] = set()

        # Get path info from websocket if available
        path = getattr(websocket, "path", "/unknown")
        logger.info(f"Client connected: {client_id} from path: {path}")

        # Unauthenticated grace window: drop connections that don't complete auth
        # within WS_AUTH_GRACE_SECONDS to prevent idle/holding-pattern resource
        # exhaustion from unauthenticated clients on a public-facing port.
        auth_grace_seconds = int(os.getenv("WS_AUTH_GRACE_SECONDS", "15"))

        async def _enforce_auth_deadline():
            try:
                await aio.sleep(auth_grace_seconds)
                if client_id not in self.user_mapping:
                    logger.warning(
                        f"Client {client_id} failed to authenticate within "
                        f"{auth_grace_seconds}s — closing connection"
                    )
                    try:
                        await websocket.close(code=4401, reason="auth timeout")
                    except Exception:
                        pass
            except aio.CancelledError:
                pass

        auth_deadline_task = aio.ensure_future(_enforce_auth_deadline())

        try:
            # Process messages from the client
            async for message in websocket:
                try:
                    # OPTIMIZATION: Remove debug logging from hot path
                    # logger.debug(f"Received message from client {client_id}: {message}")
                    await self.process_client_message(client_id, message)
                except Exception as e:
                    logger.exception(f"Error processing message from client {client_id}: {e}")
                    # Send error to client but don't disconnect
                    try:
                        await self.send_error(client_id, "PROCESSING_ERROR", str(e))
                    except Exception:
                        pass
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Client disconnected: {client_id}, code: {e.code}, reason: {e.reason}")
        except Exception as e:
            logger.exception(f"Unexpected error handling client {client_id}: {e}")
        finally:
            auth_deadline_task.cancel()
            # Clean up when the client disconnects
            await self.cleanup_client(client_id)

    async def cleanup_client(self, client_id):
        """
        Clean up client resources when they disconnect

        Args:
            client_id: Client ID to clean up
        """
        # Remove client from tracking
        if client_id in self.clients:
            del self.clients[client_id]

        # Clean up subscriptions
        if client_id in self.subscriptions:
            subscriptions = self.subscriptions[client_id]
            # Unsubscribe from all subscriptions
            for sub_json in subscriptions:
                try:
                    # Parse the JSON string to get the subscription info
                    sub_info = json.loads(sub_json)
                    symbol = sub_info.get("symbol")
                    exchange = sub_info.get("exchange")
                    mode = sub_info.get("mode")

                    # OPTIMIZATION: Remove from subscription index
                    sub_key = (symbol, exchange, mode)
                    should_unsubscribe_from_adapter = False
                    if sub_key in self.subscription_index:
                        self.subscription_index[sub_key].discard(client_id)
                        # Clean up empty entries and mark for adapter unsubscription
                        if not self.subscription_index[sub_key]:
                            del self.subscription_index[sub_key]
                            # Only unsubscribe from adapter when last client unsubscribes
                            should_unsubscribe_from_adapter = True

                    # Get the user's broker adapter
                    # Only unsubscribe from adapter if this was the last client for this symbol
                    user_id = self.user_mapping.get(client_id)
                    if (
                        should_unsubscribe_from_adapter
                        and user_id
                        and user_id in self.broker_adapters
                    ):
                        adapter = self.broker_adapters[user_id]
                        adapter.unsubscribe(symbol, exchange, mode)
                        logger.debug(
                            f"Last client unsubscribed from {symbol}:{exchange}, unsubscribing from adapter"
                        )
                except json.JSONDecodeError as e:
                    logger.exception(f"Error parsing subscription: {sub_json}, Error: {e}")
                except Exception as e:
                    logger.exception(f"Error processing subscription: {e}")
                    continue

            del self.subscriptions[client_id]

        # Remove from user mapping
        if client_id in self.user_mapping:
            user_id = self.user_mapping[client_id]

            # Check if this was the last client for this user
            is_last_client = True
            for other_client_id, other_user_id in self.user_mapping.items():
                if other_client_id != client_id and other_user_id == user_id:
                    is_last_client = False
                    break

            # If this was the last client for this user, handle the adapter state
            if is_last_client and user_id in self.broker_adapters:
                adapter = self.broker_adapters[user_id]
                broker_name = self.user_broker_mapping.get(user_id)

                # For Flattrade and Shoonya, keep the connection alive and just unsubscribe from data
                if broker_name in ["flattrade", "shoonya"] and hasattr(adapter, "unsubscribe_all"):
                    logger.info(
                        f"{broker_name.title()} adapter for user {user_id}: last client disconnected. Unsubscribing all symbols instead of disconnecting."
                    )
                    adapter.unsubscribe_all()
                else:
                    # For all other brokers, disconnect the adapter completely
                    logger.info(
                        f"Last client for user {user_id} disconnected. Disconnecting {broker_name or 'unknown broker'} adapter."
                    )
                    adapter.disconnect()
                    del self.broker_adapters[user_id]
                    if user_id in self.user_broker_mapping:
                        del self.user_broker_mapping[user_id]

            del self.user_mapping[client_id]

    async def process_client_message(self, client_id, message):
        """
        Process messages from a client

        Args:
            client_id: ID of the client
            message: The message from the client
        """
        try:
            data = json.loads(message)
            # OPTIMIZATION: Remove debug logging from hot path
            # logger.debug(f"Parsed message from client {client_id}: {data}")

            # Accept both 'action' and 'type' fields for better compatibility with different clients
            action = data.get("action") or data.get("type")
            # OPTIMIZATION: Only log important actions, not every subscribe/unsubscribe
            if action not in ["subscribe", "unsubscribe"]:
                logger.info(f"Client {client_id} requested action: {action}")

            if action in ["authenticate", "auth"]:
                await self.authenticate_client(client_id, data)
            elif action == "subscribe":
                await self.subscribe_client(client_id, data)
            elif action in ["unsubscribe", "unsubscribe_all"]:
                await self.unsubscribe_client(client_id, data)
            elif action == "get_broker_info":
                await self.get_broker_info(client_id)
            elif action == "get_supported_brokers":
                await self.get_supported_brokers(client_id)
            elif action == "ping":
                await self.handle_ping(client_id, data)
            else:
                logger.warning(f"Client {client_id} requested invalid action: {action}")
                await self.send_error(client_id, "INVALID_ACTION", f"Invalid action: {action}")
        except json.JSONDecodeError:
            logger.exception(f"Invalid JSON from client {client_id}: {message}")
            await self.send_error(client_id, "INVALID_JSON", "Invalid JSON message")
        except Exception as e:
            logger.exception(f"Error processing client message: {e}")
            await self.send_error(client_id, "SERVER_ERROR", str(e))

    async def get_user_broker_configuration(self, user_id):
        """
        Get the broker configuration for a specific user from database

        Args:
            user_id: User ID to get broker configuration for

        Returns:
            dict: Broker configuration containing broker_name and credentials
        """
        try:
            from sqlalchemy import text

            from database.auth_db import get_broker_name

            # Get user's connected broker from database
            # This queries the auth_token table to find the user's active broker
            query = text("""
                SELECT broker FROM auth_token 
                WHERE user_id = :user_id 
                ORDER BY id DESC 
                LIMIT 1
            """)

            result = db.session.execute(query, {"user_id": user_id}).fetchone()

            if result and result.broker:
                broker_name = result.broker
                logger.info(f"Found broker '{broker_name}' for user {user_id} from database")
            else:
                # Fallback to environment variable
                valid_brokers = os.getenv("VALID_BROKERS", "angel").split(",")
                broker_name = valid_brokers[0].strip() if valid_brokers else "angel"
                logger.warning(
                    f"No broker found in database for user {user_id}, using fallback: {broker_name}"
                )

            # Get broker credentials from environment variables
            # In a production system, these would be stored encrypted in the database per user
            broker_config = {
                "broker_name": broker_name,
                "api_key": os.getenv("BROKER_API_KEY"),
                "api_secret": os.getenv("BROKER_API_SECRET"),
                "api_key_market": os.getenv("BROKER_API_KEY_MARKET"),
                "api_secret_market": os.getenv("BROKER_API_SECRET_MARKET"),
                "broker_user_id": os.getenv("BROKER_USER_ID"),
                "password": os.getenv("BROKER_PASSWORD"),
                "totp_secret": os.getenv("BROKER_TOTP_SECRET"),
            }

            # Validate broker is supported
            valid_brokers_list = os.getenv("VALID_BROKERS", "").split(",")
            valid_brokers_list = [b.strip() for b in valid_brokers_list if b.strip()]

            if broker_name not in valid_brokers_list:
                logger.error(
                    f"Broker '{broker_name}' is not in VALID_BROKERS list: {valid_brokers_list}"
                )
                return None

            if not broker_config.get("broker_name"):
                logger.error(f"No broker configuration found for user {user_id}")
                return None

            logger.info(
                f"Retrieved broker configuration for user {user_id}: {broker_config['broker_name']}"
            )
            return broker_config

        except Exception as e:
            logger.exception(f"Error getting broker configuration for user {user_id}: {e}")
            return None

    async def authenticate_client(self, client_id, data):
        """
        Authenticate a client using their API key and determine their broker

        Args:
            client_id: ID of the client
            data: Authentication data containing API key
        """
        # Accept both 'api_key' and 'apikey' formats for compatibility
        api_key = data.get("api_key") or data.get("apikey")

        if not api_key:
            await self.send_error(client_id, "AUTHENTICATION_ERROR", "API key is required")
            return

        # Verify the API key and get the user ID
        user_id = verify_api_key(api_key)

        if not user_id:
            await self.send_error(client_id, "AUTHENTICATION_ERROR", "Invalid API key")
            return

        # Store the user mapping
        self.user_mapping[client_id] = user_id

        # Get broker name
        broker_name = get_broker_name(api_key)

        if not broker_name:
            await self.send_error(
                client_id, "BROKER_ERROR", "No broker configuration found for user"
            )
            return

        # Store the broker mapping for this user
        self.user_broker_mapping[user_id] = broker_name

        # Create or reuse broker adapter
        if user_id not in self.broker_adapters:
            try:
                # Create broker adapter with dynamic broker selection
                adapter = create_broker_adapter(broker_name)
                if not adapter:
                    await self.send_error(
                        client_id,
                        "BROKER_ERROR",
                        f"Failed to create adapter for broker: {broker_name}",
                    )
                    return

                # Initialize adapter with broker configuration
                # The adapter's initialize method should handle broker-specific setup
                initialization_result = adapter.initialize(broker_name, user_id)
                if initialization_result and initialization_result.get("status") == "error":
                    error_msg = initialization_result.get(
                        "message", initialization_result.get("error", "Failed to initialize broker adapter")
                    )

                    # Check if this is an auth error (403/401) - retry with fresh token
                    # This handles the stale cache issue described in GitHub issue #765
                    if adapter.is_auth_error(error_msg):
                        logger.warning(f"Auth error during initialization for user {user_id}, retrying with fresh token")
                        adapter.clear_auth_cache_for_user(user_id)

                        # Retry initialization with fresh credentials
                        initialization_result = adapter.initialize(broker_name, user_id)
                        if initialization_result and initialization_result.get("status") == "error":
                            error_msg = initialization_result.get("message", "Failed to initialize after retry")
                            await self.send_error(client_id, "BROKER_INIT_ERROR", error_msg)
                            return
                    else:
                        await self.send_error(client_id, "BROKER_INIT_ERROR", error_msg)
                        return

                # Connect to the broker
                connect_result = adapter.connect()
                # Handle both response formats:
                # - Adapter format: {"status": "error", "code": "...", "message": "..."}
                # - ConnectionPool format: {"success": False, "error": "..."}
                is_error = (
                    (connect_result and connect_result.get("status") == "error") or
                    (connect_result and connect_result.get("success") == False)
                )
                if is_error:
                    error_msg = connect_result.get("message", connect_result.get("error", "Failed to connect to broker"))
                    error_code = connect_result.get("code", "")

                    # Always retry connection failures with fresh token (issue #765)
                    # Connection failures after re-login are almost always due to stale cached tokens
                    # The upstox_client logs "401 Unauthorized" but returns generic "CONNECTION_FAILED"
                    should_retry = (
                        adapter.is_auth_error(error_msg) or
                        error_code in ("CONNECTION_FAILED", "CONNECTION_ERROR") or
                        "failed to connect" in error_msg.lower()
                    )

                    if should_retry:
                        logger.warning(f"Connection failed for user {user_id}, retrying with fresh token (error: {error_msg}, code: {error_code})")

                        # Clear stale cache in WebSocket process (issue #765)
                        self._clear_auth_cache_for_user(user_id)
                        adapter.clear_auth_cache_for_user(user_id)

                        # Re-initialize with fresh credentials from database
                        # Use force=True for pooled adapters to override existing initialization
                        logger.info(f"Re-initializing adapter for user {user_id} with fresh token")
                        try:
                            # Try with force parameter (supported by _PooledAdapterWrapper)
                            init_retry_result = adapter.initialize(broker_name, user_id, force=True)
                        except TypeError:
                            # Fallback for raw adapters that don't support force parameter
                            init_retry_result = adapter.initialize(broker_name, user_id)
                        # Handle both response formats
                        init_is_error = (
                            (init_retry_result and init_retry_result.get("status") == "error") or
                            (init_retry_result and init_retry_result.get("success") == False)
                        )
                        if init_is_error:
                            error_msg = init_retry_result.get("message", init_retry_result.get("error", "Failed to re-initialize"))
                            logger.error(f"Re-initialization failed for user {user_id}: {error_msg}")
                            await self.send_error(client_id, "BROKER_INIT_ERROR", error_msg)
                            return

                        # Retry connection
                        logger.info(f"Retrying connection for user {user_id}")
                        connect_result = adapter.connect()
                        # Handle both response formats
                        connect_is_error = (
                            (connect_result and connect_result.get("status") == "error") or
                            (connect_result and connect_result.get("success") == False)
                        )
                        if connect_is_error:
                            error_msg = connect_result.get("message", connect_result.get("error", "Failed to connect after retry"))
                            logger.error(f"Retry connection also failed for user {user_id}: {error_msg}")
                            await self.send_error(client_id, "BROKER_CONNECTION_ERROR", error_msg)
                            return

                        logger.info(f"Retry successful for user {user_id}")
                    else:
                        await self.send_error(client_id, "BROKER_CONNECTION_ERROR", error_msg)
                        return

                # Store the adapter
                self.broker_adapters[user_id] = adapter

                logger.info(
                    f"Successfully created and connected {broker_name} adapter for user {user_id}"
                )

            except Exception as e:
                error_str = str(e)
                logger.exception(f"Failed to create broker adapter for {broker_name}: {e}")

                # Check if exception is an auth error - retry with fresh token
                # This handles the stale cache issue described in GitHub issue #765
                if self._is_auth_error_exception(error_str):
                    logger.warning(f"Auth exception for user {user_id}, retrying with fresh token")
                    try:
                        self._clear_auth_cache_for_user(user_id)

                        # Retry adapter creation
                        adapter = create_broker_adapter(broker_name)
                        if adapter:
                            # Clear cache on the new adapter as well
                            if hasattr(adapter, 'clear_auth_cache_for_user'):
                                adapter.clear_auth_cache_for_user(user_id)

                            initialization_result = adapter.initialize(broker_name, user_id)
                            # Handle both response formats
                            init_is_error = (
                                (initialization_result and initialization_result.get("status") == "error") or
                                (initialization_result and initialization_result.get("success") == False)
                            )
                            if not init_is_error:
                                connect_result = adapter.connect()
                                # Handle both response formats
                                connect_is_error = (
                                    (connect_result and connect_result.get("status") == "error") or
                                    (connect_result and connect_result.get("success") == False)
                                )
                                if not connect_is_error:
                                    self.broker_adapters[user_id] = adapter
                                    logger.info(f"Successfully connected {broker_name} adapter for user {user_id} after retry")
                                    # Fall through to success response
                                else:
                                    error_msg = connect_result.get("message", connect_result.get("error", "Failed to connect after retry"))
                                    await self.send_error(client_id, "BROKER_CONNECTION_ERROR", error_msg)
                                    return
                            else:
                                error_msg = initialization_result.get("message", initialization_result.get("error", "Failed to initialize after retry"))
                                await self.send_error(client_id, "BROKER_INIT_ERROR", error_msg)
                                return
                        else:
                            await self.send_error(client_id, "BROKER_ERROR", f"Failed to create adapter for {broker_name}")
                            return
                    except Exception as retry_error:
                        logger.exception(f"Retry also failed for {broker_name}: {retry_error}")
                        await self.send_error(client_id, "BROKER_ERROR", str(retry_error))
                        return
                else:
                    logger.exception(f"Broker error for {broker_name}: {error_str}")
                    await self.send_error(client_id, "BROKER_ERROR", error_str)
                    return

        # Send success response with broker information
        await self.send_message(
            client_id,
            {
                "type": "auth",
                "status": "success",
                "message": "Authentication successful",
                "broker": broker_name,
                "user_id": user_id,
                "supported_features": {"ltp": True, "quote": True, "depth": True},
            },
        )

    async def get_supported_brokers(self, client_id):
        """
        Get list of supported brokers from environment configuration

        Args:
            client_id: ID of the client
        """
        try:
            valid_brokers = os.getenv("VALID_BROKERS", "").split(",")
            supported_brokers = [broker.strip() for broker in valid_brokers if broker.strip()]

            await self.send_message(
                client_id,
                {
                    "type": "supported_brokers",
                    "status": "success",
                    "brokers": supported_brokers,
                    "count": len(supported_brokers),
                },
            )
        except Exception as e:
            logger.exception(f"Error getting supported brokers: {e}")
            await self.send_error(client_id, "BROKER_LIST_ERROR", str(e))

    async def get_broker_info(self, client_id):
        """
        Get broker information for an authenticated client

        Args:
            client_id: ID of the client
        """
        # Check if the client is authenticated
        if client_id not in self.user_mapping:
            await self.send_error(client_id, "NOT_AUTHENTICATED", "You must authenticate first")
            return

        user_id = self.user_mapping[client_id]
        broker_name = self.user_broker_mapping.get(user_id)

        if not broker_name:
            await self.send_error(client_id, "BROKER_ERROR", "Broker information not available")
            return

        # Get adapter status
        adapter_status = "disconnected"
        if user_id in self.broker_adapters:
            adapter = self.broker_adapters[user_id]
            # Assuming the adapter has a status method or property
            adapter_status = getattr(adapter, "status", "connected")

        await self.send_message(
            client_id,
            {
                "type": "broker_info",
                "status": "success",
                "broker": broker_name,
                "adapter_status": adapter_status,
                "user_id": user_id,
            },
        )

    async def handle_ping(self, client_id, data):
        """
        Handle ping request from client

        Args:
            client_id: ID of the client
            data: Ping data containing optional timestamp
        """
        logger.debug(f"Handling ping from client {client_id}: {data}")
        client_timestamp = data.get("timestamp")
        ping_id = data.get("_pingId")
        server_timestamp = int(time.time() * 1000)  # Current time in milliseconds

        response = {"type": "pong", "status": "success", "server_timestamp": server_timestamp}

        # Include client timestamp in response if provided (for latency calculation)
        if client_timestamp is not None:
            response["client_timestamp"] = client_timestamp

        # Echo back _pingId for frontend latency calculation
        if ping_id is not None:
            response["_pingId"] = ping_id

        logger.debug(f"Sending pong to client {client_id}: {response}")
        await self.send_message(client_id, response)

    async def subscribe_client(self, client_id, data):
        """
        Subscribe a client to market data using their configured broker

        Args:
            client_id: ID of the client
            data: Subscription data
        """
        # Check if the client is authenticated
        if client_id not in self.user_mapping:
            await self.send_error(client_id, "NOT_AUTHENTICATED", "You must authenticate first")
            return

        # Get subscription parameters
        symbols = data.get("symbols") or []  # Handle array of symbols
        raw_mode = data.get("mode", "Quote")  # Accepts 1/2/3 or LTP/Quote/Depth (any case)
        depth_level = data.get("depth", 5)  # Default to 5 levels
        # Optional request_id (issue #1376): when the client supplies one, we
        # echo it back in the response so the client can correlate this ack
        # with the originating request and learn per-symbol success/failure
        # rather than guessing from tick activity.
        request_id = data.get("request_id")

        # Normalize mode through the single source of truth. Previously the
        # in-handler mapping was Title-Case-only and silently passed through
        # unknown strings (e.g. documented "QUOTE") — broker adapters then
        # received the raw string instead of a numeric mode. See issue #1375.
        try:
            mode, mode_label = normalize_mode(raw_mode)
        except (ValueError, TypeError) as e:
            await self.send_error(client_id, "INVALID_MODE", str(e))
            return
        mode_str = mode_label  # Canonical label echoed back in subscribe response

        # Handle case where a single symbol is passed directly instead of as an array
        if not symbols and (data.get("symbol") and data.get("exchange")):
            symbols = [{"symbol": data.get("symbol"), "exchange": data.get("exchange")}]

        if not symbols:
            await self.send_error(
                client_id, "INVALID_PARAMETERS", "At least one symbol must be specified"
            )
            return

        # Get the user's broker adapter
        user_id = self.user_mapping[client_id]
        if user_id not in self.broker_adapters:
            await self.send_error(client_id, "BROKER_ERROR", "Broker adapter not found")
            return

        adapter = self.broker_adapters[user_id]
        broker_name = self.user_broker_mapping.get(user_id, "unknown")

        # Process each symbol in the subscription request
        subscription_responses = []
        subscription_success = True

        for symbol_info in symbols:
            symbol = symbol_info.get("symbol")
            exchange = symbol_info.get("exchange")

            if not symbol or not exchange:
                continue  # Skip invalid symbols

            # Subscribe to market data
            response = adapter.subscribe(symbol, exchange, mode, depth_level)

            if response.get("status") == "success":
                # Store the subscription
                subscription_info = {
                    "symbol": symbol,
                    "exchange": exchange,
                    "mode": mode,
                    "depth_level": depth_level,
                    "broker": broker_name,
                }

                if client_id in self.subscriptions:
                    self.subscriptions[client_id].add(json.dumps(subscription_info))
                else:
                    self.subscriptions[client_id] = {json.dumps(subscription_info)}

                # OPTIMIZATION: Update subscription index for O(1) lookup
                sub_key = (symbol, exchange, mode)
                self.subscription_index[sub_key].add(client_id)

                # Add to successful subscriptions
                subscription_responses.append(
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "status": "success",
                        "mode": mode_str,
                        "depth": response.get("actual_depth", depth_level),
                        "broker": broker_name,
                    }
                )
            else:
                subscription_success = False
                # Add to failed subscriptions
                subscription_responses.append(
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "status": "error",
                        "message": response.get("message", "Subscription failed"),
                        "broker": broker_name,
                    }
                )

        # Send combined response
        response = {
            "type": "subscribe",
            "status": "success" if subscription_success else "partial",
            "subscriptions": subscription_responses,
            "message": "Subscription processing complete",
            "broker": broker_name,
        }
        if request_id is not None:
            response["request_id"] = request_id
        await self.send_message(client_id, response)

    async def unsubscribe_client(self, client_id, data):
        """
        Unsubscribe a client from market data

        Args:
            client_id: ID of the client
            data: Unsubscription data
        """
        # Check if the client is authenticated
        if client_id not in self.user_mapping:
            await self.send_error(client_id, "NOT_AUTHENTICATED", "You must authenticate first")
            return

        # Check if this is an unsubscribe_all request
        is_unsubscribe_all = (
            data.get("type") == "unsubscribe_all" or data.get("action") == "unsubscribe_all"
        )

        # Get unsubscription parameters for specific symbols
        symbols = data.get("symbols") or []
        # Optional request_id (issue #1376) — echoed in the response so callers
        # can correlate this ack with the originating unsubscribe request.
        request_id = data.get("request_id")

        # Handle single symbol format
        if not symbols and not is_unsubscribe_all and (data.get("symbol") and data.get("exchange")):
            try:
                _mode_int, _ = normalize_mode(data.get("mode", 2))
            except (ValueError, TypeError) as e:
                await self.send_error(client_id, "INVALID_MODE", str(e))
                return
            symbols = [
                {
                    "symbol": data.get("symbol"),
                    "exchange": data.get("exchange"),
                    "mode": _mode_int,
                }
            ]

        # If no symbols provided and not unsubscribe_all, return error
        if not symbols and not is_unsubscribe_all:
            await self.send_error(
                client_id, "INVALID_PARAMETERS", "Either symbols or unsubscribe_all is required"
            )
            return

        # Get the user's broker adapter
        user_id = self.user_mapping[client_id]
        if user_id not in self.broker_adapters:
            await self.send_error(client_id, "BROKER_ERROR", "Broker adapter not found")
            return

        adapter = self.broker_adapters[user_id]
        broker_name = self.user_broker_mapping.get(user_id, "unknown")

        # Process unsubscribe request
        successful_unsubscriptions = []
        failed_unsubscriptions = []

        # Handle unsubscribe_all case
        if is_unsubscribe_all:
            # Get all current subscriptions
            if client_id in self.subscriptions:
                # Convert all stored subscription strings back to dictionaries
                all_subscriptions = []
                for sub_json in self.subscriptions[client_id]:
                    try:
                        sub_dict = json.loads(sub_json)
                        all_subscriptions.append(sub_dict)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse subscription: {sub_json}")

                # Unsubscribe from each subscription
                for sub in all_subscriptions:
                    symbol = sub.get("symbol")
                    exchange = sub.get("exchange")
                    mode = sub.get("mode")

                    if symbol and exchange:
                        # Remove from subscription index and check if we should unsubscribe from adapter
                        sub_key = (symbol, exchange, mode)
                        should_unsubscribe_from_adapter = False
                        if sub_key in self.subscription_index:
                            self.subscription_index[sub_key].discard(client_id)
                            # Only unsubscribe from adapter when last client unsubscribes
                            if not self.subscription_index[sub_key]:
                                del self.subscription_index[sub_key]
                                should_unsubscribe_from_adapter = True

                        # Only call adapter.unsubscribe if this was the last client for this symbol
                        if should_unsubscribe_from_adapter:
                            response = adapter.unsubscribe(symbol, exchange, mode)
                            logger.debug(
                                f"Last client unsubscribed from {symbol}:{exchange}, unsubscribing from adapter"
                            )

                            if response.get("status") != "success":
                                failed_unsubscriptions.append(
                                    {
                                        "symbol": symbol,
                                        "exchange": exchange,
                                        "status": "error",
                                        "message": response.get("message", "Unsubscription failed"),
                                        "broker": broker_name,
                                    }
                                )
                                continue

                        successful_unsubscriptions.append(
                            {
                                "symbol": symbol,
                                "exchange": exchange,
                                "status": "success",
                                "broker": broker_name,
                            }
                        )

                # Clear all subscriptions for this client
                self.subscriptions[client_id].clear()
        else:
            # Process specific symbols
            for symbol_info in symbols:
                symbol = symbol_info.get("symbol")
                exchange = symbol_info.get("exchange")
                # Normalize mode (accepts 1/2/3 or LTP/Quote/Depth case-insensitive).
                # Default to Quote mode (2) if absent.
                try:
                    mode, _ = normalize_mode(symbol_info.get("mode", 2))
                except (ValueError, TypeError) as e:
                    failed_unsubscriptions.append(
                        {
                            "symbol": symbol,
                            "exchange": exchange,
                            "status": "error",
                            "message": str(e),
                            "broker": broker_name,
                        }
                    )
                    continue

                if not symbol or not exchange:
                    continue  # Skip invalid symbols

                # Remove from subscription index and check if we should unsubscribe from adapter
                sub_key = (symbol, exchange, mode)
                should_unsubscribe_from_adapter = False
                if sub_key in self.subscription_index:
                    self.subscription_index[sub_key].discard(client_id)
                    # Only unsubscribe from adapter when last client unsubscribes
                    if not self.subscription_index[sub_key]:
                        del self.subscription_index[sub_key]
                        should_unsubscribe_from_adapter = True

                # Remove from client's subscription list
                if client_id in self.subscriptions:
                    # Remove any matching subscription (with or without broker info)
                    subscriptions_to_remove = []
                    for sub_json in self.subscriptions[client_id]:
                        try:
                            sub_data = json.loads(sub_json)
                            if (
                                sub_data.get("symbol") == symbol
                                and sub_data.get("exchange") == exchange
                                and sub_data.get("mode") == mode
                            ):
                                subscriptions_to_remove.append(sub_json)
                        except json.JSONDecodeError:
                            continue

                    for sub_json in subscriptions_to_remove:
                        self.subscriptions[client_id].discard(sub_json)

                # Only call adapter.unsubscribe if this was the last client for this symbol
                if should_unsubscribe_from_adapter:
                    response = adapter.unsubscribe(symbol, exchange, mode)
                    logger.debug(
                        f"Last client unsubscribed from {symbol}:{exchange}, unsubscribing from adapter"
                    )

                    if response.get("status") != "success":
                        failed_unsubscriptions.append(
                            {
                                "symbol": symbol,
                                "exchange": exchange,
                                "status": "error",
                                "message": response.get("message", "Unsubscription failed"),
                                "broker": broker_name,
                            }
                        )
                        continue

                successful_unsubscriptions.append(
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "status": "success",
                        "broker": broker_name,
                    }
                )

        # Send combined response
        status = "success"
        if len(failed_unsubscriptions) > 0 and len(successful_unsubscriptions) > 0:
            status = "partial"
        elif len(failed_unsubscriptions) > 0 and len(successful_unsubscriptions) == 0:
            status = "error"

        unsub_response = {
            "type": "unsubscribe",
            "status": status,
            "message": "Unsubscription processing complete",
            "successful": successful_unsubscriptions,
            "failed": failed_unsubscriptions,
            "broker": broker_name,
        }
        if request_id is not None:
            unsub_response["request_id"] = request_id
        await self.send_message(client_id, unsub_response)

    async def send_message(self, client_id, message):
        """
        Send a message to a client

        Args:
            client_id: ID of the client
            message: The message to send
        """
        if client_id in self.clients:
            websocket = self.clients[client_id]
            try:
                await websocket.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"Connection closed while sending message to client {client_id}")

    async def send_error(self, client_id, code, message):
        """
        Send an error message to a client

        Args:
            client_id: ID of the client
            code: Error code
            message: Error message
        """
        await self.send_message(client_id, {"status": "error", "code": code, "message": message})

    def _handle_cache_invalidation(self, topic_str: str, data_str: str):
        """
        Handle cache invalidation messages from Flask process.

        When a user re-authenticates or logs out, Flask publishes a cache invalidation
        message via ZeroMQ. This method clears the local auth caches so that the next
        request fetches fresh data from the database.

        This solves the stale token issue described in GitHub issue #765.

        Args:
            topic_str: The ZMQ topic (format: CACHE_INVALIDATE_{TYPE}_{USER_ID})
            data_str: JSON string with invalidation details
        """
        try:
            # Import caches locally to avoid circular imports
            from database.auth_db import (
                auth_cache,
                broker_cache,
                feed_token_cache,
                invalid_api_key_cache,
                verified_api_key_cache,
            )

            # Parse the invalidation message
            message = json.loads(data_str)
            user_id = message.get("user_id")
            cache_type = message.get("cache_type", "ALL")

            if not user_id:
                logger.warning("Cache invalidation message missing user_id")
                return

            logger.info(f"Received cache invalidation for user: {user_id}, type: {cache_type}")

            # CRITICAL: Clear ALL cache entries to prevent stale token issues
            # This is necessary because get_auth_token_broker() uses a different cache key format
            # (sha256(api_key)_include_feed_token) than the user-id based keys.
            # Without clearing all entries, old cached tokens would persist and cause
            # 401 Unauthorized errors after re-login.
            # See GitHub issue #851 for details on this cache key mismatch bug.
            caches_cleared = []

            if cache_type in ("AUTH", "ALL"):
                auth_cache.clear()
                caches_cleared.append("auth_cache")

            if cache_type in ("FEED", "ALL"):
                feed_token_cache.clear()
                caches_cleared.append("feed_token_cache")

            if cache_type == "ALL":
                broker_cache.clear()
                caches_cleared.append("broker_cache")

                verified_api_key_cache.clear()
                invalid_api_key_cache.clear()
                caches_cleared.append("verified_api_key_cache")
                caches_cleared.append("invalid_api_key_cache")

            if caches_cleared:
                logger.info(f"Cleared caches for user {user_id}: {', '.join(caches_cleared)}")
            else:
                logger.debug(f"No cached data found for user {user_id}")

            # Also disconnect and clean up any existing broker adapters for this user
            # This forces re-initialization with fresh credentials on next connection
            if user_id in self.broker_adapters:
                try:
                    adapter = self.broker_adapters[user_id]
                    adapter.disconnect()
                    del self.broker_adapters[user_id]
                    logger.info(f"Disconnected stale broker adapter for user {user_id}")
                except Exception as adapter_error:
                    logger.warning(f"Error disconnecting adapter for user {user_id}: {adapter_error}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse cache invalidation message: {e}")
        except Exception as e:
            logger.exception(f"Error processing cache invalidation: {e}")

    def _is_auth_error_exception(self, error_message: str) -> bool:
        """
        Check if an error message indicates an authentication failure.

        Used to detect when to retry with fresh credentials (issue #765).

        Args:
            error_message: The error message string

        Returns:
            True if the error indicates authentication failure (401/403)
        """
        if not error_message:
            return False

        error_lower = str(error_message).lower()
        auth_error_indicators = [
            "401",
            "403",
            "unauthorized",
            "forbidden",
            "authentication failed",
            "auth failed",
            "invalid token",
            "token expired",
            "access denied",
            "invalid credentials",
            "session expired",
        ]
        return any(indicator in error_lower for indicator in auth_error_indicators)

    def _clear_auth_cache_for_user(self, user_id: str):
        """
        Clear all cached authentication data for a user.

        Called when detecting stale credentials (e.g., 403 error from broker).
        See GitHub issue #765 for details.

        Args:
            user_id: The user's ID
        """
        try:
            from database.auth_db import (
                auth_cache,
                broker_cache,
                feed_token_cache,
            )

            cache_key_auth = f"auth-{user_id}"
            cache_key_feed = f"feed-{user_id}"

            caches_cleared = []
            if cache_key_auth in auth_cache:
                del auth_cache[cache_key_auth]
                caches_cleared.append("auth_cache")
            if cache_key_feed in feed_token_cache:
                del feed_token_cache[cache_key_feed]
                caches_cleared.append("feed_token_cache")
            if cache_key_auth in broker_cache:
                del broker_cache[cache_key_auth]
                caches_cleared.append("broker_cache")

            if caches_cleared:
                logger.info(f"Cleared auth caches for user {user_id}: {', '.join(caches_cleared)}")
            else:
                logger.debug(f"No cached auth data found for user {user_id}")

        except Exception as e:
            logger.exception(f"Error clearing auth cache for user {user_id}: {e}")

    async def zmq_listener(self):
        """
        OPTIMIZED: Listen for messages from broker adapters via ZeroMQ and forward to clients

        Key Performance Improvements:
        1. Increased timeout from 0.1s to 0.3s (reduces busy-waiting by 66%)
        2. Use subscription_index for O(1) lookup instead of O(n²) iteration
        3. Batch message sending with asyncio.gather

        Also handles cache invalidation messages from Flask process for cross-process
        cache synchronization (see GitHub issue #765).
        """
        logger.debug("Starting OPTIMIZED ZeroMQ listener with subscription indexing and cache invalidation support")

        while self.running:
            try:
                # Check if we should stop
                if not self.running:
                    break

                # RESOURCE CLEANUP: Periodically clean stale throttle entries
                self._cleanup_stale_throttle_entries()

                # OPTIMIZATION 1: Increased timeout to reduce busy-waiting
                try:
                    [topic, data] = await aio.wait_for(
                        self.socket.recv_multipart(),
                        timeout=0.3,  # Increased from 0.1s (66% less CPU usage)
                    )
                except TimeoutError:
                    # No message received within timeout, continue the loop
                    continue

                # Parse the message
                topic_str = topic.decode("utf-8")
                data_str = data.decode("utf-8")

                # Handle cache invalidation messages (from Flask process)
                # These messages clear stale auth tokens after re-login
                # See GitHub issue #765 for details
                if topic_str.startswith("CACHE_INVALIDATE"):
                    try:
                        self._handle_cache_invalidation(topic_str, data_str)
                    except Exception as e:
                        logger.exception(f"Error handling cache invalidation: {e}")
                    continue  # Skip market data processing for cache messages

                # Skip private account-level event topics (orders, positions, margins).
                # These are published by broker adapters on the shared ZMQ socket but
                # do not follow the BROKER_EXCHANGE_SYMBOL_MODE market-data format.
                if topic_str.endswith(("_orders", "_positions", "_margins")):
                    logger.debug(f"Skipping private event topic: {topic_str}")
                    continue

                market_data = json.loads(data_str)

                # Extract topic components from ZMQ topic string.
                # All adapters publish: EXCHANGE_SYMBOL_MODE
                # Mode (LTP/QUOTE/DEPTH) is always the LAST segment.
                # Exchange is the first segment (NSE, BSE, NFO, MCX, CRYPTO, …)
                #   except NSE_INDEX / BSE_INDEX which span two segments.
                # Symbol is everything between exchange and mode — may contain
                # underscores for crypto spot pairs (e.g. CRYPTO_SOL_INR_LTP).
                parts = topic_str.split("_")

                if len(parts) < 3:
                    logger.warning(f"Invalid topic format: {topic_str}")
                    continue

                broker_name = "unknown"

                # Mode is always the last segment
                mode_str = parts[-1]
                remaining = parts[:-1]  # everything except mode

                # Detect two-segment exchange prefixes (NSE_INDEX, BSE_INDEX,
                # MCX_INDEX, GLOBAL_INDEX, NSEIX_INDEX). Add new index/multi-segment
                # exchanges here when introducing them.
                _MULTI_SEGMENT_EXCHANGE_PREFIXES = (
                    ("NSE", "INDEX"),
                    ("BSE", "INDEX"),
                    ("MCX", "INDEX"),
                    ("GLOBAL", "INDEX"),
                )
                if len(remaining) >= 2 and (remaining[0], remaining[1]) in _MULTI_SEGMENT_EXCHANGE_PREFIXES:
                    exchange = f"{remaining[0]}_{remaining[1]}"
                    symbol = "_".join(remaining[2:])
                else:
                    exchange = remaining[0]
                    symbol = "_".join(remaining[1:])

                if not symbol:
                    logger.warning(f"Invalid topic format (no symbol): {topic_str}")
                    continue

                # Route through the single normalizer so topic parsing stays
                # consistent with client-side mode handling.
                normalized = normalize_mode_or_none(mode_str)
                if normalized is None:
                    logger.warning(f"Invalid mode in topic: {mode_str}")
                    continue
                mode, _ = normalized

                # No server-side LTP throttling: the previous time-based
                # throttle dropped intra-window ticks instead of coalescing
                # them, so clients could miss the latest price during bursts
                # (e.g. NIFTY expiry, circuit triggers). With the O(1)
                # subscription_index, fan-out is cheap enough to forward every
                # tick. If CPU pressure ever returns, replace this with a
                # trailing-edge coalescer that emits the latest pending tick.
                sub_key = (symbol, exchange, mode)
                current_time = time.time()
                self.last_message_time[sub_key] = current_time

                # Feed market data to MarketDataService for backend consumers
                # (sandbox execution engine, position MTM, RMS, etc.)
                # This runs regardless of whether WebSocket clients are subscribed
                try:
                    mds_data = {
                        "symbol": symbol,
                        "exchange": exchange,
                        "mode": mode,
                        "data": market_data,
                    }
                    market_data_service = get_market_data_service()
                    market_data_service.process_market_data(mds_data)
                except Exception as mds_error:
                    # Don't block WebSocket delivery if MarketDataService has issues
                    logger.debug(f"MarketDataService processing error: {mds_error}")

                # OPTIMIZATION 2: O(1) lookup using subscription index
                # Higher modes include all lower-mode data (Depth > Quote > LTP),
                # so also deliver to subscribers at lower modes.
                # Maps client_id -> the mode they subscribed to (for correct message tagging)
                all_client_modes = {}
                for m in range(1, mode + 1):
                    for cid in self.subscription_index.get((symbol, exchange, m), set()):
                        all_client_modes[cid] = m

                if not all_client_modes:
                    continue  # No WebSocket clients subscribed, skip delivery

                # OPTIMIZATION 3: Batch message sends for parallel delivery
                send_tasks = []

                # OPTIMIZATION 4: Pre-create base message (reused for all clients)
                # This avoids creating the same dict 1000 times
                base_message = {
                    "type": "market_data",
                    "symbol": symbol,
                    "exchange": exchange,
                    "mode": mode,
                    "data": market_data,
                }

                for client_id, client_mode in all_client_modes.items():
                    # Verify client still exists
                    if client_id not in self.clients:
                        continue

                    # Verify user mapping exists
                    user_id = self.user_mapping.get(client_id)
                    if not user_id:
                        continue

                    # Check broker match (important for multi-broker setups)
                    client_broker = self.user_broker_mapping.get(user_id)
                    if broker_name != "unknown" and client_broker and client_broker != broker_name:
                        continue

                    # Tag message with client's subscribed mode so frontend renders correctly
                    message = base_message.copy()
                    message["mode"] = client_mode
                    message["broker"] = broker_name if broker_name != "unknown" else client_broker

                    # Add to batch
                    send_tasks.append(self.send_message(client_id, message))

                # Send all messages in parallel (non-blocking)
                if send_tasks:
                    await aio.gather(*send_tasks, return_exceptions=True)

                # METRICS: Track message count for health monitoring
                self._messages_processed += 1

            except Exception as e:
                logger.exception(f"Error in ZeroMQ listener: {e}")
                # Continue running despite errors
                await aio.sleep(1)


# Entry point for running the server standalone
async def main():
    """Main entry point for running the WebSocket proxy server"""
    proxy = None

    try:
        # Load environment variables
        load_dotenv()

        # Get WebSocket configuration from environment variables
        ws_host = os.getenv("WEBSOCKET_HOST", "127.0.0.1")
        ws_port = int(os.getenv("WEBSOCKET_PORT", "8765"))

        # Create and start the WebSocket proxy
        proxy = WebSocketProxy(host=ws_host, port=ws_port)

        await proxy.start()

    except KeyboardInterrupt:
        logger.info("Server stopped by user (KeyboardInterrupt)")
    except RuntimeError as e:
        if "set_wakeup_fd only works in main thread" in str(e):
            logger.error(f"Error in start method: {e}")
            logger.info("Starting ZeroMQ listener without signal handlers")
            # Continue with ZeroMQ listener even if signal handlers fail
            if proxy:
                await proxy.zmq_listener()
        else:
            logger.error(f"Runtime error: {e}")
            raise
    except Exception as e:
        logger.exception(f"Server error: {e}")
        raise
    finally:
        # Always clean up resources
        if proxy:
            try:
                await proxy.stop()
            except Exception as cleanup_error:
                logger.exception(f"Error during cleanup: {cleanup_error}")


if __name__ == "__main__":
    aio.run(main())

```
