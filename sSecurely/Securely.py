import sys
import time
import threading
import queue
import os
import shutil
from datetime import datetime
import webbrowser
import warnings
import pytesseract
import tkinter as tk
from tkinter import messagebox
import base64
import re

# ANSI Color Codes for Windows terminal (defined early for use in _early_audit_log)
class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Standard colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'

# Enable ANSI colors on Windows
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)  # Enable ANSI escape sequences
    except Exception:
        pass  # If it fails, colors might not work but program continues

# Early audit log wrapper (before full definition)
def _early_audit_log(message, level='INFO'):
    """Early audit log wrapper - converts to print until full audit_log is available"""
    time_str = datetime.now().strftime("%H:%M")
    timestamp = f"[{time_str}]"
    # Remove markdown formatting
    clean_message = message.replace('**', '').replace('__', '').replace('*', '').replace('_', '')
    
    # Color mapping for early logs
    color_map = {
        'INFO': Colors.CYAN,
        'SUCCESS': Colors.BRIGHT_GREEN,
        'WARNING': Colors.BRIGHT_YELLOW,
        'ERROR': Colors.BRIGHT_RED,
        'INIT': Colors.BRIGHT_GREEN + Colors.BOLD,
    }
    
    selected_color = color_map.get(level, Colors.WHITE)
    print(f"{selected_color}{timestamp} {level} {clean_message}{Colors.RESET}")

# HTTP client optional
try:
    import requests
except Exception:
    requests = None
    _early_audit_log("Warning: requests library not installed. Install with: pip install requests", 'WARNING')

# Groq API
try:
    from groq import Groq
    groq_available = True
except Exception:
    Groq = None
    groq_available = False
    _early_audit_log("Warning: groq library not installed. Install with: pip install groq", 'WARNING')

# Modern UI library
try:
    import customtkinter as ctk
except Exception:
    # Fallback to tkinter
    ctk = tk
    _early_audit_log("Warning: customtkinter not installed - falling back to tkinter. Install with: pip install customtkinter", 'WARNING')

    # Provide a minimal CustomTkinter compatibility layer so the app can run on
    # plain tkinter when customtkinter isn't installed.
    try:
        from tkinter import ttk as _ttk
    except Exception:
        _ttk = None

    # No-op appearance APIs used by CustomTkinter
    def _ctk_noop(*_args, **_kwargs):
        return None

    ctk.set_appearance_mode = _ctk_noop
    ctk.set_default_color_theme = _ctk_noop

    # Vars are available on tkinter module, but keep the ctk.* names working
    ctk.BooleanVar = tk.BooleanVar
    ctk.StringVar = tk.StringVar
    ctk.IntVar = tk.IntVar
    ctk.DoubleVar = tk.DoubleVar

    # CustomTkinter uses CTkFont and CTkImage; make them safe to call.
    class _CTkFontFallback:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def __repr__(self) -> str:
            return f"_CTkFontFallback({self.args!r}, {self.kwargs!r})"

    ctk.CTkFont = _CTkFontFallback

    class _CTkImageFallback:
        def __init__(self, *args, **kwargs):
            # In tkinter mode, images should be PhotoImage/ImageTk.PhotoImage.
            # We just store inputs so code that constructs CTkImage won't crash.
            self.args = args
            self.kwargs = kwargs

    ctk.CTkImage = _CTkImageFallback

    def _ctk_font_to_tk(font_obj):
        if isinstance(font_obj, _CTkFontFallback):
            size = font_obj.kwargs.get("size")
            weight = font_obj.kwargs.get("weight")
            family = font_obj.kwargs.get("family")
            tk_family = family or "Segoe UI"
            parts = [tk_family]
            if size is not None:
                try:
                    parts.append(int(size))
                except Exception:
                    pass
            if weight:
                parts.append(weight)
            return tuple(parts) if len(parts) > 1 else (tk_family, 10)
        return font_obj

    def _ctk_translate_kwargs(widget_kind: str, kwargs: dict) -> dict:
        """Translate common CustomTkinter kwargs into tkinter equivalents."""
        out = dict(kwargs)

        # Colors
        fg_color = out.pop("fg_color", None)
        text_color = out.pop("text_color", None)

        # Drop any other CustomTkinter color-style kwargs (segmented buttons, etc.)
        for _k in list(out.keys()):
            if _k.endswith("_color") and _k not in {"bg", "fg", "background", "foreground"}:
                out.pop(_k, None)

        # CustomTkinter-only styling (ignored in tkinter fallback)
        out.pop("corner_radius", None)
        out.pop("hover_color", None)
        out.pop("border_color", None)
        out.pop("border_width", None)
        out.pop("bg_color", None)

        # Translate fonts
        if "font" in out:
            out["font"] = _ctk_font_to_tk(out["font"])
            if out["font"] is None:
                out.pop("font", None)

        # Apply colors to supported widgets
        if fg_color is not None and str(fg_color).lower() != "transparent":
            # tkinter uses bg/background for most widgets
            out.setdefault("bg", fg_color)
            if widget_kind in {"Text"}:
                out.setdefault("background", fg_color)

        if text_color is not None and widget_kind in {"Label", "Button", "Checkbutton", "Text"}:
            # tkinter uses fg/foreground
            out.setdefault("fg", text_color)
            if widget_kind in {"Text"}:
                out.setdefault("foreground", text_color)

        # CustomTkinter sometimes passes width/height for frames; tkinter Frame
        # accepts them, so keep as-is.
        return out

    class _CTkConfigureMixin:
        _ctk_widget_kind = "Widget"

        def configure(self, cnf=None, **kw):
            if cnf:
                try:
                    kw = {**dict(cnf), **kw}
                except Exception:
                    pass
            kw = _ctk_translate_kwargs(self._ctk_widget_kind, kw)
            return super().configure(**kw)

        config = configure

    class CTk(_CTkConfigureMixin, tk.Tk):
        _ctk_widget_kind = "Tk"

        def __init__(self, *args, **kwargs):
            translated = _ctk_translate_kwargs(self._ctk_widget_kind, kwargs)
            super().__init__(*args)
            if translated:
                try:
                    super().configure(**translated)
                except Exception:
                    pass

    class CTkToplevel(_CTkConfigureMixin, tk.Toplevel):
        _ctk_widget_kind = "Toplevel"

        def __init__(self, *args, **kwargs):
            translated = _ctk_translate_kwargs(self._ctk_widget_kind, kwargs)
            super().__init__(*args)
            if translated:
                try:
                    super().configure(**translated)
                except Exception:
                    pass

    class CTkFrame(_CTkConfigureMixin, tk.Frame):
        _ctk_widget_kind = "Frame"

        def __init__(self, master=None, **kwargs):
            super().__init__(master, **_ctk_translate_kwargs(self._ctk_widget_kind, kwargs))

    class CTkLabel(_CTkConfigureMixin, tk.Label):
        _ctk_widget_kind = "Label"

        def __init__(self, master=None, **kwargs):
            super().__init__(master, **_ctk_translate_kwargs(self._ctk_widget_kind, kwargs))

    class CTkButton(_CTkConfigureMixin, tk.Button):
        _ctk_widget_kind = "Button"

        def __init__(self, master=None, **kwargs):
            super().__init__(master, **_ctk_translate_kwargs(self._ctk_widget_kind, kwargs))

    class CTkTextbox(_CTkConfigureMixin, tk.Text):
        _ctk_widget_kind = "Text"

        def __init__(self, master=None, **kwargs):
            super().__init__(master, **_ctk_translate_kwargs(self._ctk_widget_kind, kwargs))

    class CTkCheckBox(_CTkConfigureMixin, tk.Checkbutton):
        _ctk_widget_kind = "Checkbutton"

        def __init__(self, master=None, **kwargs):
            super().__init__(master, **_ctk_translate_kwargs(self._ctk_widget_kind, kwargs))

    # ScrollableFrame fallback: non-scrollable Frame (functional but no scroll).
    class CTkScrollableFrame(CTkFrame):
        pass

    # Complex widgets: provide usable fallbacks.
    if _ttk is not None:
        class CTkComboBox(_ttk.Combobox):
            def __init__(self, master=None, **kwargs):
                cmd = kwargs.pop("command", None)
                # Translate CustomTkinter-ish options to ttk options
                if "variable" in kwargs and "textvariable" not in kwargs:
                    kwargs["textvariable"] = kwargs.pop("variable")
                for _k in list(kwargs.keys()):
                    if _k.endswith("_color") or _k in {"corner_radius", "border_width", "border_color", "hover_color"}:
                        kwargs.pop(_k, None)
                font = _ctk_font_to_tk(kwargs.get("font"))
                if font is None:
                    kwargs.pop("font", None)
                else:
                    kwargs["font"] = font
                super().__init__(master, **kwargs)
                if callable(cmd):
                    self.bind("<<ComboboxSelected>>", lambda _e: cmd(self.get()))

        class CTkTabview(tk.Frame):
            def __init__(self, master=None, **kwargs):
                super().__init__(master, **_ctk_translate_kwargs("Frame", kwargs))
                self._nb = _ttk.Notebook(self)
                self._tabs = {}
                self._nb.pack(fill="both", expand=True)

            def add(self, name: str):
                frame = tk.Frame(self._nb)
                self._tabs[name] = frame
                self._nb.add(frame, text=name)
                return frame

            def tab(self, name: str):
                return self._tabs[name]

            def get(self):
                current_id = self._nb.select()
                for name, frame in self._tabs.items():
                    if str(frame) == str(current_id):
                        return name
                # fallback
                return self._nb.tab(current_id, "text")

            def set(self, name: str):
                frame = self._tabs.get(name)
                if frame is not None:
                    self._nb.select(frame)
    else:
        CTkComboBox = tk.OptionMenu
        CTkTabview = CTkFrame

    # Export into ctk namespace
    ctk.CTk = CTk
    ctk.CTkToplevel = CTkToplevel
    ctk.CTkFrame = CTkFrame
    ctk.CTkLabel = CTkLabel
    ctk.CTkButton = CTkButton
    ctk.CTkTextbox = CTkTextbox
    ctk.CTkCheckBox = CTkCheckBox
    ctk.CTkScrollableFrame = CTkScrollableFrame
    ctk.CTkComboBox = CTkComboBox
    ctk.CTkTabview = CTkTabview

# Image handling library
try:
    from PIL import Image, ImageDraw, ImageTk
except Exception:
    Image = None
    ImageDraw = None
    ImageTk = None
    _early_audit_log("Warning: Pillow (PIL) not installed. Install with: pip install pillow", 'WARNING')

# Screen capture
try:
    import mss
except Exception:
    mss = None
    _early_audit_log("Warning: mss library not installed. Install with: pip install mss", 'WARNING')

# Windows sound alerts
try:
    import winsound
except Exception:
    winsound = None

# Windows toast notifications
WINRT_AVAILABLE = False
try:
    from winrt.windows.ui.notifications import ToastNotificationManager, ToastNotification
    from winrt.windows.data.xml.dom import XmlDocument
    WINRT_AVAILABLE = True
except Exception:
    WINRT_AVAILABLE = False

# Notification defaults
toaster = None
WIN10TOAST_AVAILABLE = False

# Auto-detect Tesseract OCR
import shutil

# OCR availability flag
TESSERACT_AVAILABLE = False
TESS_WARNED = False
# Auto-pause on sensitive pages
PAUSED_FOR_SENSITIVE_PAGE = False
# Last AI analysis text
LAST_AI_ANALYSIS = None
# AI analysis cache
AI_ANALYSIS_CACHE = {}
# Training screenshot toggle
TRAINING_CAPTURE_ENABLED = False
# App version string
APP_VERSION = "v2.1"

# Detect Tesseract location
_tess_path = None
_checked_paths = []

try:
    # Check PATH first
    _tess_path = shutil.which('tesseract')
    if _tess_path:
        _checked_paths.append(f"PATH: {_tess_path}")
        _early_audit_log(f"Found Tesseract in PATH: {_tess_path}", 'INIT')
    else:
        _checked_paths.append("PATH: Not found")
    
    # Check common paths
    if not _tess_path:
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        
        for path in common_paths:
            _checked_paths.append(f"Checked: {path}")
            if os.path.exists(path):
                _tess_path = path
                _early_audit_log(f"Found Tesseract at: {path}", 'INIT')
                break
    
    # Configure and test
    if _tess_path:
        pytesseract.pytesseract.tesseract_cmd = _tess_path
        # Test Tesseract works
        try:
            # Verify Tesseract
            test_result = pytesseract.get_tesseract_version()
            TESSERACT_AVAILABLE = True
            _early_audit_log(f"Tesseract OCR initialized successfully (version: {test_result})", 'INIT')
        except Exception as test_err:
            _early_audit_log(f"Tesseract found but test failed: {test_err} Path: {_tess_path}", 'WARNING')
            TESSERACT_AVAILABLE = False
    else:
        _early_audit_log("Tesseract OCR not found. Checked paths: " + ", ".join(_checked_paths), 'ERROR')
        _early_audit_log("To install Tesseract: Download from https://github.com/UB-Mannheim/tesseract/wiki, Install to C:\\Program Files\\Tesseract-OCR\\, or add to PATH, then restart Securely", 'INFO')
        
except Exception as _err:
    _early_audit_log(f"Error detecting Tesseract: {_err}", 'ERROR')
    TESSERACT_AVAILABLE = False


# API Usage Statistics Tracking (will be initialized after GROQ_API_KEYS is defined)
_api_usage_stats = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'rate_limited_requests': 0,
    'key_usage': {},  # Track usage per key: {key_index: {'requests': count, 'successes': count, 'failures': count, 'rate_limits': count}}
    'key_switches': 0,
    'start_time': time.time()
}

# Console logger class with color support
class ConsoleLogger:
    """Enhanced console logger with color coding and comprehensive auditing"""
    def __init__(self):
        self.terminal = sys.stdout
        self.log = []
        self.max_lines = 5000  # Keep last 5000 lines for comprehensive audit
        
    def _colorize(self, message, color_code):
        """Add color to message"""
        return f"{color_code}{message}{Colors.RESET}"
    
    def write(self, message):
        if self.terminal is not None:
            try:
                self.terminal.write(message)
            except Exception:
                pass
        if message.strip():
            # Use MM/DD/YYYY - HH:MM:SS format
            date_str = datetime.now().strftime("%m/%d/%Y")
            time_str = datetime.now().strftime("%H:%M:%S")
            timestamp = f"{date_str} - {time_str}"
            # Remove markdown formatting
            clean_message = message.strip().replace('**', '').replace('__', '').replace('*', '').replace('_', '')
            self.log.append(f"[{timestamp}] {clean_message}")
            if len(self.log) > self.max_lines:
                self.log = self.log[-self.max_lines:]
    
    def flush(self):
        if self.terminal is not None:
            try:
                self.terminal.flush()
            except Exception:
                pass
    
    def get_log(self):
        return "\n".join(self.log)

# Create logger instance
console_logger = ConsoleLogger()
sys.stdout = console_logger

# Typewriter queue system (non-blocking)
_typewriter_queue = queue.Queue()
_typewriter_thread = None
_typewriter_running = False

def _typewriter_worker():
    """Background thread that processes typewriter messages from the queue"""
    global _typewriter_running
    _typewriter_running = True
    
    while _typewriter_running:
        try:
            # Get message from queue (with timeout to allow checking _typewriter_running)
            try:
                item = _typewriter_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            
            text, delay, color = item
            
            # Display text character by character (no ANSI codes)
            for char in text:
                try:
                    print(char, end='', flush=True)
                    time.sleep(delay)
                except Exception:
                    # If printing fails, just continue silently
                    pass
            
            print()  # New line after typewriter effect
            _typewriter_queue.task_done()
            
        except Exception:
            # Silently handle errors - don't let the thread crash
            continue

def _start_typewriter_thread():
    """Start the background typewriter thread if not already running"""
    global _typewriter_thread, _typewriter_running
    
    if _typewriter_thread is None or not _typewriter_thread.is_alive():
        _typewriter_running = True
        _typewriter_thread = threading.Thread(target=_typewriter_worker, daemon=True)
        _typewriter_thread.start()

def fast_typewriter_effect(text, delay=0.005, color=None):
    """
    Queue text for typewriter effect display (non-blocking)
    
    Args:
        text: Text to display
        delay: Delay between characters (seconds) - default 0.005 for fast effect
        color: Color code to use
    """
    # Start the worker thread if needed
    _start_typewriter_thread()
    
    # Add message to queue (non-blocking)
    try:
        _typewriter_queue.put((text, delay, color), block=False)
    except queue.Full:
        # If queue is full, just print directly (fallback, preserve colors)
        print(text)

def typewriter_effect(text, delay=0.03, color=None):
    """
    Queue text for typewriter effect display (non-blocking) - uses fast by default
    """
    fast_typewriter_effect(text, delay=0.005, color=color)

# Comprehensive Audit Logger (Compact Mode with Fast Typewriter)
_COMPACT_MODE = True  # Enable compact logging
_LAST_LOG_TIME = {}  # Track last log time per level to reduce spam
_TYPEWRITER_ENABLED = True  # Enable fast typewriter effect
_TYPEWRITER_DELAY = 0.003  # Very fast typewriter (3ms per character)

def audit_log(message, level='INFO', color=None, show_stats=False, compact=True, use_typewriter=True):
    """
    Comprehensive audit logging with color coding and fast typewriter effect
    
    Levels:
    - INFO: General information (CYAN)
    - SUCCESS: Successful operations (BRIGHT_GREEN)
    - WARNING: Warnings (YELLOW)
    - ERROR: Errors (BRIGHT_RED)
    - API: API calls (MAGENTA)
    - SCREENSHOT: Screenshot operations (BLUE)
    - OCR: OCR operations (BRIGHT_CYAN)
    - THREAT: Threat detections (BRIGHT_RED + BG_RED)
    - STATS: Statistics (BRIGHT_YELLOW)
    - SWITCH: Key switching (BRIGHT_MAGENTA)
    - INIT: Initialization (BRIGHT_GREEN)
    - NETWORK: Network operations (BRIGHT_BLUE)
    - FILE: File operations (BRIGHT_WHITE)
    - SECURITY: Security events (BRIGHT_RED)
    """
    # Remove markdown formatting (**bold**, etc.)
    message = message.replace('**', '').replace('__', '').replace('*', '').replace('_', '')
    
    # Use HH:MM format only
    time_str = datetime.now().strftime("%H:%M")
    timestamp = f"[{time_str}]"
    
    # Throttle frequent logs in compact mode
    if compact and _COMPACT_MODE:
        current_time = time.time()
        last_time = _LAST_LOG_TIME.get(level, 0)
        # Throttle INFO/API logs to max once per 2 seconds
        if level in ['INFO', 'API', 'SCREENSHOT', 'OCR']:
            if current_time - last_time < 2.0:
                return  # Skip this log to reduce spam
        _LAST_LOG_TIME[level] = current_time
    
    # Enhanced color mapping with more options
    color_map = {
        'INFO': Colors.CYAN,
        'SUCCESS': Colors.BRIGHT_GREEN,
        'WARNING': Colors.BRIGHT_YELLOW,
        'ERROR': Colors.BRIGHT_RED,
        'API': Colors.MAGENTA,
        'SCREENSHOT': Colors.BRIGHT_BLUE,
        'OCR': Colors.BRIGHT_CYAN,
        'THREAT': Colors.BRIGHT_RED + Colors.BG_RED + Colors.BOLD,  # Red background for threats
        'STATS': Colors.BRIGHT_YELLOW,
        'SWITCH': Colors.BRIGHT_MAGENTA,
        'INIT': Colors.BRIGHT_GREEN + Colors.BOLD,
        'NETWORK': Colors.BRIGHT_BLUE,
        'FILE': Colors.BRIGHT_WHITE,
        'SECURITY': Colors.BRIGHT_RED + Colors.BOLD
    }
    
    # Compact format: shorter level names without emojis
    level_short = {
        'INFO': 'I',
        'SUCCESS': 'SUCCESS',
        'WARNING': 'WARNING',
        'ERROR': 'ERROR',
        'API': 'API',
        'SCREENSHOT': 'SCREENSHOT',
        'OCR': 'OCR',
        'THREAT': 'THREAT',
        'STATS': 'STATS',
        'SWITCH': 'SWITCH',
        'INIT': 'INIT',
        'NETWORK': 'NETWORK',
        'FILE': 'FILE',
        'SECURITY': 'SECURITY'
    }.get(level, level)
    
    # Color mapping for output
    color_map = {
        'INFO': Colors.CYAN,
        'SUCCESS': Colors.BRIGHT_GREEN,
        'WARNING': Colors.BRIGHT_YELLOW,
        'ERROR': Colors.BRIGHT_RED,
        'API': Colors.MAGENTA,
        'SCREENSHOT': Colors.BRIGHT_BLUE,
        'OCR': Colors.BRIGHT_CYAN,
        'THREAT': Colors.BRIGHT_RED + Colors.BG_RED + Colors.BOLD,
        'STATS': Colors.BRIGHT_YELLOW,
        'SWITCH': Colors.BRIGHT_MAGENTA,
        'INIT': Colors.BRIGHT_GREEN + Colors.BOLD,
        'NETWORK': Colors.BRIGHT_BLUE,
        'FILE': Colors.BRIGHT_WHITE,
        'SECURITY': Colors.BRIGHT_RED + Colors.BOLD
    }
    
    selected_color = color if color else color_map.get(level, Colors.WHITE)
    
    if compact and _COMPACT_MODE:
        # Compact single-line format with colors
        formatted_message = f"{selected_color}{timestamp} {level_short} {message}{Colors.RESET}"
    else:
        formatted_message = f"{selected_color}{timestamp} [{level}] {message}{Colors.RESET}"
    
    # Use fast typewriter effect if enabled
    if use_typewriter and _TYPEWRITER_ENABLED:
        try:
            fast_typewriter_effect(formatted_message, delay=_TYPEWRITER_DELAY, color=None)
        except Exception:
            # Fallback to regular print if typewriter fails
            print(formatted_message)
    else:
        print(formatted_message)
    
    # Show API stats if requested
    if show_stats:
        display_api_stats()

def display_api_stats():
    """Display comprehensive API usage statistics (compact format)"""
    global _api_usage_stats
    
    uptime = time.time() - _api_usage_stats['start_time']
    uptime_str = f"{int(uptime // 3600)}h{int((uptime % 3600) // 60)}m{int(uptime % 60)}s"
    
    # Compact single-line header without ANSI codes
    print(f"📊 API Stats | Uptime: {uptime_str} | Total: {_api_usage_stats['total_requests']} | ✓: {_api_usage_stats['successful_requests']} | ✗: {_api_usage_stats['failed_requests']} | ⏳: {_api_usage_stats['rate_limited_requests']} | 🔄: {_api_usage_stats['key_switches']}")
    
    # Compact per-key stats (single line per key) without ANSI codes
    for idx in sorted(_api_usage_stats['key_usage'].keys()):
        stats = _api_usage_stats['key_usage'][idx]
        key_num = idx + 1
        if stats['requests'] > 0:
            success_rate = (stats['successes'] / stats['requests']) * 100
            print(f"  Key{key_num}: Req:{stats['requests']} ✓:{stats['successes']} ✗:{stats['failures']} ⏳:{stats['rate_limits']} Rate:{success_rate:.0f}%")

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="win10toast")

# Windows notifications import
try:
    from win11toast import notify as win11_notify
    WIN11TOAST_AVAILABLE = True
except:
    WIN11TOAST_AVAILABLE = False
    try:
        # Use ctypes fallback
        import ctypes
        from ctypes import wintypes
        CTYPES_AVAILABLE = True
    except:
        CTYPES_AVAILABLE = False

# Universal notification function
# Cursor AI assisted with this complex implementation
def show_notification(title, message, duration=10):
    """
    Notification with multiple fallbacks
    """
    notification_sent = False

    # Try win11toast first
    try:
        if 'WIN11TOAST_AVAILABLE' in globals() and WIN11TOAST_AVAILABLE:
            try:
                win11_notify(title, message, app_id='Securely - Alert!', duration='short')
                notification_sent = True
                audit_log(f"Notification sent via win11toast: {title}", 'INFO', use_typewriter=False)
            except Exception as e:
                audit_log(f"win11toast failed: {e}", 'WARNING', use_typewriter=False)
    except Exception:
        # Ignore errors
        pass

    # Try win10toast
    if not notification_sent:
        try:
            from win10toast import ToastNotifier
            global toaster, WIN10TOAST_AVAILABLE
            if toaster is None:
                toaster = ToastNotifier()
                WIN10TOAST_AVAILABLE = True
            # Non-blocking call
            toaster.show_toast(title, message, duration=duration, threaded=True)
            notification_sent = True
            audit_log(f"Notification sent via win10toast: {title}", 'INFO', use_typewriter=False)
        except Exception as e:
            audit_log(f"win10toast failed or not available: {e}", 'WARNING', use_typewriter=False)

    # Try WinRT
    if not notification_sent and 'WINRT_AVAILABLE' in globals() and WINRT_AVAILABLE:
        try:
            # Build XML
            try:
                xml = f"""<toast>
  <visual>
    <binding template=\"ToastGeneric\">
      <text>{title}</text>
      <text>{message}</text>
    </binding>
  </visual>
</toast>"""
                doc = XmlDocument()
                doc.load_xml(xml)
                notifier = ToastNotificationManager.create_toast_notifier("Securely")
                t = ToastNotification(doc)
                notifier.show(t)
                notification_sent = True
                audit_log(f"Notification sent via WinRT: {title}", 'INFO', use_typewriter=False)
            except Exception as _e:
                audit_log(f"WinRT toast failed: {_e}", 'WARNING', use_typewriter=False)
        except Exception as e:
            audit_log(f"WinRT path not available: {e}", 'WARNING', use_typewriter=False)

    # Return if failed
    if not notification_sent:
        audit_log(f"No native notification available for: {title}", 'WARNING', use_typewriter=False)

    return notification_sent

# --- Groq API settings ---

# Multiple API keys for fallback support - if one gets rate limited, it will switch to the next
# Do not embed provider keys. Use SECURELY_API_URL (OpenRouter via server proxy).
GROQ_API_KEYS = []

# Legacy single key support (uses first key from list)
GROQ_API_KEY = GROQ_API_KEYS[0] if GROQ_API_KEYS else None

# Groq model to use
# Note: Groq currently doesn't have active vision models, so we use text-only models with OCR text
# Current available models (as of 2025):
# - "llama-3.3-70b-versatile" (recommended - versatile, high quality)
# - "llama-3.1-70b-versatile" (versatile, multilingual)
# - "llama-3.1-8b-instant" (fast, lightweight)
# - "mixtral-8x7b-32768" (large context window)
# - "gemma2-9b-it" (efficient, fast)
GROQ_MODEL = "llama-3.1-8b-instant"  # Default model (text-only, will analyze OCR text) - using instant for better compatibility
GROQ_VISION_MODEL = None  # No vision models available currently

# Current API tracker - tracks which API key index we're using
_current_api_key_index = 0
_current_api = f"groq_{_current_api_key_index}"

# API tracking init - track each key separately
_api_failure_counts = {}
_api_cooldowns = {}
_groq_clients = {}  # Dictionary to store clients for each API key

# Initialize API usage stats for each key
for idx in range(len(GROQ_API_KEYS)):
    _api_usage_stats['key_usage'][idx] = {
        'requests': 0,
        'successes': 0,
        'failures': 0,
        'rate_limits': 0
    }

# Initialize all Groq clients
audit_log(f"🔧 Initializing {len(GROQ_API_KEYS)} Groq API clients...", 'INFO')
if groq_available and GROQ_API_KEYS:
    for idx, api_key in enumerate(GROQ_API_KEYS):
        if api_key and isinstance(api_key, str) and api_key.strip():
            try:
                audit_log(f"  → Initializing API client {idx + 1}/{len(GROQ_API_KEYS)}...", 'API')
                _groq_clients[idx] = Groq(api_key=api_key)
                _api_failure_counts[idx] = 0
                _api_cooldowns[idx] = 0
                audit_log(f"Groq API client {idx + 1}/{len(GROQ_API_KEYS)} initialized successfully", 'SUCCESS')
            except Exception as e:
                audit_log(f"Failed to initialize Groq client {idx + 1}: {e}", 'ERROR')
                _groq_clients[idx] = None
                _api_failure_counts[idx] = 0
                _api_cooldowns[idx] = 0
        else:
            audit_log(f"API key {idx + 1} is empty or invalid", 'WARNING')
            _groq_clients[idx] = None
            _api_failure_counts[idx] = 0
            _api_cooldowns[idx] = 0
else:
    audit_log("Groq library not available or no API keys configured", 'WARNING')

def reset_api_state():
    """Reset all API state (cooldowns, failure counts) - useful after updating API keys"""
    global _current_api_key_index, _current_api, _api_failure_counts, _api_cooldowns, _ai_rate_limit_until, _ai_in_rate_limit, _groq_clients
    audit_log("Resetting API state...", 'INFO')
    _current_api_key_index = 0
    _current_api = f"groq_{_current_api_key_index}"
    _api_failure_counts = {}
    _api_cooldowns = {}
    _ai_rate_limit_until = 0
    _ai_in_rate_limit = False
    # Reinit all clients
    _groq_clients = {}
    if groq_available and GROQ_API_KEYS:
        for idx, api_key in enumerate(GROQ_API_KEYS):
            if api_key and isinstance(api_key, str) and api_key.strip():
                try:
                    audit_log(f"  → Reinitializing API client {idx + 1}...", 'API')
                    _groq_clients[idx] = Groq(api_key=api_key)
                    _api_failure_counts[idx] = 0
                    _api_cooldowns[idx] = 0
                except Exception as e:
                    audit_log(f"  Failed to reinitialize client {idx + 1}: {e}", 'ERROR')
                    _groq_clients[idx] = None
                    _api_failure_counts[idx] = 0
                    _api_cooldowns[idx] = 0
    audit_log("API state reset - all cooldowns and failure counts cleared", 'SUCCESS')

def get_api_status():
    """Get current status of API (cooldowns, failures) for all keys"""
    current_time = time.time()
    status = []
    
    for idx in range(len(GROQ_API_KEYS)):
        api_key = GROQ_API_KEYS[idx] if idx < len(GROQ_API_KEYS) else None
        cooldown_until = _api_cooldowns.get(idx, 0)
        failures = _api_failure_counts.get(idx, 0)
        is_valid = api_key and isinstance(api_key, str) and api_key.strip()
        is_current = idx == _current_api_key_index
        
        key_status = f"Key {idx + 1}"
        if is_current:
            key_status += " (Active)"
        
        if cooldown_until > current_time:
            remaining = int(cooldown_until - current_time)
            if remaining > 3600:
                status.append(f"{key_status}: Cooldown ({remaining//60}min remaining)")
            else:
                status.append(f"{key_status}: Cooldown ({remaining}s remaining)")
        elif not is_valid:
            status.append(f"{key_status}: Invalid/Empty")
        elif idx not in _groq_clients or not _groq_clients[idx]:
            status.append(f"{key_status}: Not initialized")
        elif failures > 0:
            status.append(f"{key_status}: {failures} failures")
        else:
            status.append(f"{key_status}: Ready")
    
    return status

# --- settings ---
SCREENSHOT_INTERVAL = 0.05  # Ultra-fast 50ms interval for maximum responsiveness
KEYWORDS = [
    # Malware types
    "virus", "malware", "worm", "trojan", "spyware", "adware", "ransomware", "rootkit", "botnet",
    
    # Phishing & Scams
    "phish", "phishing", "scam", "fraud", "fake", "suspicious", "verify account", "confirm identity",
    "urgent action", "suspended account", "click here", "act now", "limited time", 
    
    # Security threats
    "keylogger", "password", "login", "credential", "steal", "hack", "breach", "exploit",
    "vulnerability", "backdoor", "injection", "bypass", "crack",
    
    # Social engineering
    "winner", "congratulations", "prize", "lottery", "inheritance", "tax refund",
    "bitcoin", "cryptocurrency", "investment", "profit", "guaranteed", "risk-free",
    
    # Tech support scams
    "microsoft support", "apple support", "google support", "tech support", "computer infected",
    "error detected", "system compromised", "immediate action", "call now",
    
    # Suspicious URLs/Downloads
    "download now", "install", "update required", "flash player", "codec", "driver update",
    "free download", "crack", "keygen", "serial", "patch", "portable",
    
    # Test keywords for easy testing
    "test threat", "security test", "demo threat", "malicious test", "threat test"
]

# --- AI-powered analysis with rate limit tracking ---
_ai_rate_limit_until = 0  # Track when rate limit expires
_ai_in_rate_limit = False  # Track if we're currently rate limited

def get_next_available_api_key():
    """Get the next available API key index that's not in cooldown"""
    global _current_api_key_index, _api_cooldowns, _api_usage_stats
    current_time = time.time()
    
    # Try current key first
    if _current_api_key_index < len(GROQ_API_KEYS):
        cooldown_until = _api_cooldowns.get(_current_api_key_index, 0)
        if cooldown_until <= current_time:
            if _current_api_key_index in _groq_clients and _groq_clients[_current_api_key_index]:
                audit_log(f"Using current API key {_current_api_key_index + 1}", 'API')
                return _current_api_key_index
            else:
                audit_log(f"Current API key {_current_api_key_index + 1} client not available, searching for alternative...", 'WARNING')
        else:
            remaining = int(cooldown_until - current_time)
            audit_log(f"⏳ Current API key {_current_api_key_index + 1} in cooldown ({remaining}s remaining), searching for alternative...", 'WARNING')
    
    # Try all keys in order
    for idx in range(len(GROQ_API_KEYS)):
        cooldown_until = _api_cooldowns.get(idx, 0)
        if cooldown_until <= current_time:
            if idx in _groq_clients and _groq_clients[idx]:
                old_index = _current_api_key_index
                _current_api_key_index = idx
                _current_api = f"groq_{idx}"
                if idx != old_index:
                    _api_usage_stats['key_switches'] += 1
                    audit_log(f"Key{old_index + 1}->{idx + 1}", 'SWITCH')
                return idx
            else:
                audit_log(f"  → API key {idx + 1} client not initialized", 'WARNING')
        else:
            remaining = int(cooldown_until - current_time)
            audit_log(f"  → API key {idx + 1} in cooldown ({remaining}s remaining)", 'WARNING')
    
    audit_log("No available API keys found - all keys are in cooldown or unavailable", 'ERROR')
    return None

def analyze_screen_with_ai(image_base64, detected_text=None, monitor=None):
    """Use AI to analyze screen content with automatic API fallback
    
    Args:
        image_base64: Base64 encoded image
        detected_text: OCR detected text
        monitor: Optional ScreenMonitor instance to check scan type
    """
    global _ai_rate_limit_until, _ai_in_rate_limit, _current_api_key_index, _current_api, _api_failure_counts, _api_cooldowns, _groq_clients
    
    # Compact: Only log occasionally
    if not hasattr(analyze_screen_with_ai, '_call_count'):
        analyze_screen_with_ai._call_count = 0
    analyze_screen_with_ai._call_count += 1
    if analyze_screen_with_ai._call_count % 50 == 0:
        audit_log("🔍 AI analysis active...", 'INFO')
    
    # Check if we're still in rate limit cooldown
    current_time = time.time()
    if _ai_rate_limit_until > current_time:
        remaining = int(_ai_rate_limit_until - current_time)
        _ai_in_rate_limit = True
        if remaining % 10 == 0:  # Only print every 10 seconds to avoid spam
            audit_log(f"⏳ AI rate limit cooldown: {remaining}s remaining (scanning every 5 seconds)", 'WARNING')
        return []
    else:
        # Cooldown expired
        if _ai_in_rate_limit:
            _ai_in_rate_limit = False
            audit_log("✅ AI rate limit cooldown expired - resuming normal scanning", 'SUCCESS')
    
    # Check if Groq API is configured and available
    if not GROQ_API_KEYS or len(GROQ_API_KEYS) == 0:
        audit_log("⚠️ No valid Groq API keys found. Please check your GROQ_API_KEYS configuration.", 'ERROR')
        return []
    
    # Get next available API key
    api_key_index = get_next_available_api_key()
    if api_key_index is None:
        # All keys are in cooldown - find the shortest cooldown
        min_cooldown = float('inf')
        min_idx = None
        for idx in range(len(GROQ_API_KEYS)):
            cooldown_until = _api_cooldowns.get(idx, 0)
            if cooldown_until > current_time:
                remaining = cooldown_until - current_time
                if remaining < min_cooldown:
                    min_cooldown = remaining
                    min_idx = idx
        
        if min_idx is not None:
            remaining = int(min_cooldown)
            if remaining % 10 == 0:
                msg = f"⏳ All Groq API keys in cooldown. Shortest: {int(remaining)}s remaining"
                audit_log(msg, 'WARNING')
                try:
                    show_notification("Securely: API Cooldown",
                                      f"Securely is on cooldown — AI requests are rate limited.\n{msg}",
                                      duration=8)
                except Exception:
                    pass
        else:
            audit_log("⚠️ No available Groq API clients. Please check your API keys.", 'ERROR')
        return []
    
    _groq_client = _groq_clients[api_key_index]
    api_name = f"groq_{api_key_index}"
    
    # Track API request
    _api_usage_stats['total_requests'] += 1
    _api_usage_stats['key_usage'][api_key_index]['requests'] += 1
    # Only log every 10th API request in compact mode
    if _api_usage_stats['total_requests'] % 10 == 0:
        audit_log(f"📡 API Key{api_key_index + 1} (Total: {_api_usage_stats['total_requests']})", 'API')
    
    prompt = """
You are a cybersecurity expert analyzing screen content for threats. Your job is to PROTECT users from malicious content. Be VIGILANT and PROACTIVE in detecting threats.

CRITICAL SECURITY PRIORITY: When analyzing emails, messages, or web content, err on the side of CAUTION. If you detect ANY suspicious indicators (suspicious sender, urgency tactics, suspicious links, typosquatting, etc.), flag it as SUSPICIOUS. It's better to flag a potentially malicious email than to miss a real threat.

ANALYZE THE FOLLOWING CONTENT TYPES:
• Essays and articles - check for misinformation, scams, or malicious content
• Headlines and news - identify fake news, clickbait scams, or phishing
• Captions and social media posts - detect social engineering, scams
• Messages and emails - identify phishing, impersonation, or fraud attempts (ONLY if clearly malicious)
• Webpages and websites - detect fake login pages, malicious sites, phishing
• Download prompts - identify potentially harmful downloads
• Forms requesting personal information - assess legitimacy
• Payment pages - verify authenticity
• URLs and links - check for suspicious domains

SPECIAL DETECTION - LEGITIMATE LOGIN AND PAYMENT PAGES:
IMPORTANT: Distinguish between LOGIN PAGES and PAYMENT PAGES:

LOGIN PAGES ask for credentials:
• Username / Email address (for authentication)
• Password
• Two-factor authentication codes
• Security questions

PAYMENT PAGES ask for payment information:
• Credit/Debit card number
• Expiration date / CVV / CVC / Security code
• Billing address / Postal code / ZIP code
• Payment method selection
• Order total / Subtotal / Checkout

If you see a LEGITIMATE login form (asking for username/password for authentication), respond with "LEGITIMATE_LOGIN".
If you see a LEGITIMATE payment form (asking for card details for checkout), respond with "LEGITIMATE_PAYMENT".

Both login and payment pages are sensitive and should pause monitoring, but they are DIFFERENT:
- Login pages = authentication/credentials
- Payment pages = checkout/payment processing

CRITICAL: FAKE/PHISHING LOGIN PAGE DETECTION:
Before responding with "LEGITIMATE_LOGIN", you MUST verify the domain is legitimate:
• Check the URL/domain carefully - look for typosquatting (g00gle.com, goog1e.com, etc.)
• Verify the domain matches the legitimate service (google.com for Google, not google-login.com or similar)
• Look for suspicious domains that mimic legitimate services
• If you see a login page but the domain is suspicious/fake, DO NOT respond with "LEGITIMATE_LOGIN" - instead flag it as a threat with "SUSPICIOUS: Fake login page detected - suspicious domain [domain name]"
• Common fake login indicators:
  - Domain contains service name but isn't the official domain (e.g., google-login.com, microsoft-account.net)
  - Typosquatting domains (g00gle.com, micr0soft.com, faceb00k.com)
  - Suspicious TLDs (.tk, .ml, .ga, .cf) with service names
  - Numbers replacing letters in domain names
  - Domains that look like legitimate services but have extra words (google-verify.com, microsoft-update.net)

This helps users know when to pause the security monitor to avoid false alarms on real banking/shopping sites, while catching fake/phishing pages.

IGNORE THE FOLLOWING (Do not flag these - these are ALWAYS safe):
• Windows system notifications in the bottom-right corner
• "Securely" security alerts or notifications
• Legitimate security software messages
• Standard Windows UI elements
• Code editors and development tools (VS Code, Visual Studio, PyCharm, IntelliJ, Eclipse, etc.)
• Programming code or syntax (Python, JavaScript, Java, C++, etc.)
• File explorers showing filenames
• The Securely application itself and its detection messages
• Development environments showing code, debug consoles, terminals, or IDE interfaces
• Code files (.py, .js, .java, .cpp, etc.) being edited in IDEs
• Legitimate educational emails (edX, Coursera, Udemy, etc.) - these are ALWAYS safe, do not flag
• Legitimate course/learning platform emails with course updates, welcome messages, "Welcome to week X", etc. - these are safe
• Legitimate marketing emails from known brands (Nike, Google, Microsoft, Amazon, etc.) - these are safe unless clearly fake
• Legitimate promotional emails from financial services (Cash App, PayPal, Venmo, etc.) - these are safe if from official domains
• Cash App promotional emails from @cash.app, @updates.cash.app, @square.com, or @squareup.com - these are legitimate
• Newsletters and subscription emails from legitimate sources
• Emails from @edx.org, @coursera.org, @udemy.com, @news.edx.org - these are legitimate educational platforms
• Course-related emails mentioning "week", "course", "learning", "class", "lesson" from educational platforms

LOOK FOR THESE THREATS (FLAG AS SUSPICIOUS IF ANY INDICATORS ARE PRESENT):
1. HTTP (insecure) websites - ANY website using http:// instead of https:// is a security risk (except localhost/127.0.0.1 for development)
2. Phishing emails - ANY email with suspicious sender addresses, typosquatting domains, mismatched sender/domain, or fraud indicators
3. Fake sender addresses - ANY typosquatting (g00gle.com, micr0soft.com), numbers replacing letters, suspicious TLDs (.tk, .ml, .ga, .cf)
4. Urgency tactics - "act now", "urgent", "account will be closed", "immediate action required" combined with suspicious elements
5. Prize/lottery scams - "you've won", "congratulations", "claim your prize" with suspicious links
6. Tech support scams - Virus warnings, "your computer is infected", phone numbers, obvious impersonation
7. Credential harvesting - Login pages with suspicious domains, fake login forms
8. Impersonation - Fake Microsoft/Apple/Google pages, wrong domains, suspicious branding
9. Cryptocurrency/investment scams - "guaranteed returns", "risk-free", "limited time" with suspicious links
10. Malicious attachments or downloads - Suspicious file types, untrusted sources, unexpected downloads
11. Fake invoices or payment requests - Unknown senders, suspicious payment requests, fake invoices

EMAIL-SPECIFIC THREAT INDICATORS (Flag if ANY are present):
• Suspicious sender email address (typosquatting, numbers replacing letters, suspicious domains)
• Mismatched sender name and email address
• Urgency language ("act now", "urgent", "immediate action", "account suspended")
• Suspicious links or URLs (hover to check, but if visible and suspicious, flag it)
• Requests for personal information, passwords, or credentials
• Threats or warnings ("your account will be closed", "legal action", "immediate payment")
• Prize/lottery claims ("you've won", "congratulations", "claim now")
• Unusual sender domains or TLDs
• Generic greetings ("Dear Customer" instead of your name)
• Poor grammar or spelling errors (common in phishing)

CRITICAL: HTTP (INSECURE) WEBSITE DETECTION:
• HTTP websites (http://) are INSECURE and should ALWAYS be flagged as threats
• Data sent over HTTP is unencrypted and can be intercepted by attackers
• Flag ANY website using http:// (including localhost and local IPs) as "SUSPICIOUS: Insecure HTTP connection detected - [URL]"
• This includes http://127.0.0.1, http://localhost, http://172.x.x.x, and any other HTTP URLs
• HTTPS (https://) is secure, but HTTP (http://) is always a security risk

IMPORTANT: For emails and messages, if you detect ANY suspicious indicators, flag it as SUSPICIOUS. It's better to be cautious than to miss a real threat.

RESPOND FORMAT:
- "SAFE" ONLY if content appears completely legitimate with NO suspicious indicators whatsoever
- "SUSPICIOUS: [detailed description of the threat]" if you detect ANY suspicious indicators (suspicious sender, urgency tactics, suspicious links, typosquatting, etc.)
- "UNSURE: [brief description]" only for edge cases where content appears mostly legitimate but has minor concerns

SECURITY PRIORITY: When analyzing emails, if you see ANY red flags (suspicious sender, urgency language, suspicious links, typosquatting), flag it as SUSPICIOUS. Do not default to "SAFE" when suspicious indicators are present.
"""
    
    # Try Groq API with fallback logic
    # Note: Groq doesn't currently have active vision models, so we use text-only models with OCR text
    # Current available models (2025) - try most compatible first
    models_to_try = [
        ("llama-3.1-8b-instant", False),  # Fast, lightweight, most compatible
        ("llama-3.1-70b-versatile", False),  # Versatile, multilingual (fallback)
        ("llama-3.3-70b-versatile", False),  # Recommended - versatile, high quality (fallback)
        ("mixtral-8x7b-32768", False),  # Large context window (fallback)
        ("gemma2-9b-it", False),  # Efficient, fast (fallback)
    ]
    
    # If no models specified, use default
    if not models_to_try:
        models_to_try = [(GROQ_MODEL, False)]
    
    for model_name, _ in models_to_try:
        try:
            # Compact: Only log model attempts occasionally
            if not hasattr(analyze_screen_with_ai, '_model_log_count'):
                analyze_screen_with_ai._model_log_count = 0
            analyze_screen_with_ai._model_log_count += 1
            if analyze_screen_with_ai._model_log_count % 20 == 0:
                audit_log(f"🤖 Model: {model_name.split('/')[-1]} Key{api_key_index + 1}", 'API')
            
            # Text-only model - use OCR text (Groq doesn't have active vision models)
            if detected_text and detected_text.strip():
                text_prompt = prompt + f"""

DETECTED TEXT FROM SCREEN (OCR):
{detected_text}

Analyze the above text for security threats. Look for suspicious indicators like phishing emails, suspicious sender addresses, urgency tactics, suspicious links, typosquatting, etc."""
            else:
                # No text detected - warn user but still try to analyze
                text_prompt = prompt + """

WARNING: No text was detected from the screen (OCR may not be working or screen may contain only images).

Since no text was extracted, I cannot fully analyze the content. However, if this is an email or message window, you should manually check for:
- Suspicious sender email addresses
- Urgency language (act now, urgent, account suspended)
- Suspicious links or URLs
- Typosquatting or fake domains
- Requests for personal information

RESPOND WITH: UNSURE: No text detected - manual review recommended. Please check sender address, links, and content manually for suspicious indicators."""
            
            messages = [
                {
                    "role": "user",
                    "content": text_prompt
                }
            ]
            
            # Make API call to Groq
            api_start_time = time.time()
            chat_completion = _groq_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            )
            api_duration = time.time() - api_start_time
            
            # Extract response
            text_response = chat_completion.choices[0].message.content.strip()
            response_length = len(text_response)
            
            try:
                globals()['LAST_AI_ANALYSIS'] = text_response
            except Exception:
                pass
            
            _current_api = api_name
            _api_failure_counts[api_key_index] = 0
            
            # Track successful request
            _api_usage_stats['successful_requests'] += 1
            _api_usage_stats['key_usage'][api_key_index]['successes'] += 1
            
            # Compact: Only log success details occasionally
            if _api_usage_stats['successful_requests'] % 10 == 0:
                audit_log(f"✅ API Key{api_key_index + 1} ✓ ({api_duration:.1f}s, {response_length} chars)", 'SUCCESS')
            
            # Get window title for domain validation
            window_title = ""
            if monitor and hasattr(monitor, 'main_window'):
                try:
                    import win32gui
                    active_window = win32gui.GetForegroundWindow()
                    window_title = win32gui.GetWindowText(active_window)
                except Exception:
                    window_title = ""
            
            return process_ai_response(text_response, detected_text, monitor=monitor, window_title=window_title)
            
        except Exception as e:
            error_str = str(e)
            # If model not found or access denied, try next model
            if ("model_not_found" in error_str.lower() or "404" in error_str.lower() or 
                "does not exist" in error_str.lower() or "403" in error_str.lower() or 
                "access denied" in error_str.lower()):
                audit_log(f"⚠️ Model {model_name} not available/accessible with Key {api_key_index + 1}, trying next model...", 'WARNING')
                continue  # Try next model
            
            # For other errors (like 401 invalid key), break and handle below
            audit_log(f"❌ API error with Key {api_key_index + 1} and model {model_name}: {error_str}", 'ERROR')
            break
    
    # All models failed - handle errors and switch API keys if rate limited
    error_str = str(e) if 'e' in locals() else "Unknown error"
    _api_failure_counts[api_key_index] = _api_failure_counts.get(api_key_index, 0) + 1
    
    # Track failed request
    _api_usage_stats['failed_requests'] += 1
    _api_usage_stats['key_usage'][api_key_index]['failures'] += 1
    
    audit_log(f"❌ API call failed for Key {api_key_index + 1}. Error: {error_str}", 'ERROR')
    
    # Handle rate limits and errors - switch to next key on rate limit
    if "rate limit" in error_str.lower() or "429" in error_str.lower():
        _api_cooldowns[api_key_index] = current_time + 65
        _api_usage_stats['rate_limited_requests'] += 1
        _api_usage_stats['key_usage'][api_key_index]['rate_limits'] += 1
        audit_log(f"⏳ Key{api_key_index + 1} rate limit (65s cooldown)", 'WARNING')
        # Switch to next available API key
        next_key = get_next_available_api_key()
        if next_key is not None and next_key != api_key_index:
            audit_log(f"🔄 Retry Key{next_key + 1}", 'SWITCH')
            # Retry with new key (recursive call, but limit depth)
            return analyze_screen_with_ai(image_base64, detected_text, monitor)
    elif "401" in error_str.lower() or "403" in error_str.lower() or "invalid" in error_str.lower() or "access denied" in error_str.lower():
        _api_cooldowns[api_key_index] = current_time + 3600  # 1 hour for invalid keys
        audit_log(f"❌ Key{api_key_index + 1} authentication failed (403/401) - Key may be invalid, expired, or model not accessible", 'ERROR')
        audit_log(f"   Error details: {error_str[:200]}", 'ERROR')
        # Switch to next available API key
        next_key = get_next_available_api_key()
        if next_key is not None and next_key != api_key_index:
            audit_log(f"🔄 Retry Key{next_key + 1} (invalid Key{api_key_index + 1})", 'SWITCH')
            return analyze_screen_with_ai(image_base64, detected_text, monitor)
        else:
            audit_log(f"⚠️ All API keys failed authentication. Please verify your API keys are valid and have access to Groq models.", 'ERROR')
    elif "timeout" in error_str.lower() or "timed out" in error_str.lower():
        _api_cooldowns[api_key_index] = current_time + 30
        audit_log(f"⏳ Key{api_key_index + 1} timeout (30s)", 'WARNING')
    else:
        _api_cooldowns[api_key_index] = current_time + 30  # Default cooldown
        audit_log(f"⚠️ Key{api_key_index + 1} error (30s)", 'WARNING')
    
    # Groq API failed or in cooldown
    try:
        globals()['LAST_AI_ANALYSIS'] = None
    except Exception:
        pass
    
    # Show detailed status
    current_time = time.time()
    cooldown_until = _api_cooldowns.get(api_key_index, 0)
    if cooldown_until > current_time:
        remaining = int(cooldown_until - current_time)
        if remaining > 3600:
            status_msg = f"❌ Groq API Key {api_key_index + 1}: Invalid/Expired (cooldown: {remaining//60}min)"
        else:
            status_msg = f"❌ Groq API Key {api_key_index + 1}: Cooldown ({remaining}s remaining)"
    else:
        status_msg = f"❌ Groq API Key {api_key_index + 1}: Failed"
    audit_log(status_msg, 'ERROR')
    
    try:
        # Inform the user that AI API is unavailable / in cooldown
        show_notification("Securely: AI Unavailable",
                          "Groq API failed or is in cooldown. Securely will continue keyword-based monitoring.",
                          duration=10)
    except Exception:
        pass
    return []

def _extract_urls_from_text(text: str) -> list:
    """Extract all URLs (both HTTP and HTTPS) from text, including IP addresses"""
    import re
    urls = []
    # Match full URLs including http://, https://, and IP addresses
    # Pattern matches: http://..., https://..., http://IP:PORT, https://IP:PORT
    # Also try to catch OCR errors where "https" might be misread
    url_pattern = re.compile(r'(https?://[^\s<>"\'\)]+|https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?)', re.IGNORECASE)
    matches = url_pattern.findall(text)
    for match in matches:
        if match:
            # Check for common OCR errors where "https" might be misread as "http"
            # Look for patterns like "http" followed by a domain that typically uses HTTPS
            url_lower = match.lower()
            if url_lower.startswith('http://'):
                # Check if there might be a missing 's' - look for common HTTPS domains
                # or check if the context suggests it should be HTTPS
                domain_part = url_lower.replace('http://', '').split('/')[0]
                # Common domains that almost always use HTTPS
                common_https_domains = [
                    'google.com', 'facebook.com', 'amazon.com', 'microsoft.com',
                    'apple.com', 'twitter.com', 'x.com', 'youtube.com', 'github.com',
                    'paypal.com', 'ebay.com', 'netflix.com', 'linkedin.com',
                    'politics1.com', 'reddit.com', 'wikipedia.org', 'stackoverflow.com'
                ]
                # If domain matches a common HTTPS site, assume OCR error and treat as HTTPS
                if any(domain in domain_part for domain in common_https_domains):
                    # Don't add this as HTTP - it's likely HTTPS misread by OCR
                    continue
            urls.append(match)
    return urls


def _extract_domains_from_text(text: str) -> list:
    """Extract all domains/URLs from text"""
    import re
    domains = []
    # Match URLs and domains
    url_pattern = re.compile(r'(https?://)?([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}', re.IGNORECASE)
    matches = url_pattern.findall(text)
    for match in matches:
        full_url = ''.join(match) if match[0] else match[1]
        # Extract just the domain part
        domain_match = re.search(r'([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}', full_url, re.IGNORECASE)
        if domain_match:
            domain = domain_match.group(0).lower()
            # Remove www. prefix for comparison
            if domain.startswith('www.'):
                domain = domain[4:]
            domains.append(domain)
    return domains


def _is_http_url(url: str) -> bool:
    """Check if a URL uses HTTP (insecure) instead of HTTPS"""
    if not url:
        return False
    url_lower = url.lower().strip()
    # Check if it starts with http:// (not https://)
    if url_lower.startswith('http://'):
        return True
    return False


def _is_suspicious_domain(domain: str, window_title: str = "") -> bool:
    """Check if a domain is suspicious (fake/phishing)
    
    Args:
        domain: The domain to check (e.g., 'google.com', 'g00gle.com')
        window_title: Optional window title that might contain additional context
    """
    if not domain:
        return False
    
    domain_lower = domain.lower()
    
    # List of legitimate domains for common services
    legitimate_domains = {
        'google.com', 'accounts.google.com', 'myaccount.google.com',
        'microsoft.com', 'login.microsoftonline.com', 'account.microsoft.com',
        'apple.com', 'appleid.apple.com', 'id.apple.com',
        'facebook.com', 'www.facebook.com', 'm.facebook.com',
        'amazon.com', 'pay.amazon.com',
        'paypal.com', 'www.paypal.com',
        'ebay.com', 'www.ebay.com',
        'netflix.com', 'www.netflix.com',
        'twitter.com', 'x.com',
        'linkedin.com', 'www.linkedin.com',
        'github.com', 'github.io',
        'dropbox.com', 'www.dropbox.com',
        'adobe.com', 'accounts.adobe.com',
        'yahoo.com', 'login.yahoo.com',
        'outlook.com', 'hotmail.com', 'live.com',
        'bankofamerica.com', 'chase.com', 'wellsfargo.com',
        'getpostman.com',  # Legitimate Postman domain
        'tebex.io', 'pay.tebex.io'  # Legitimate Tebex payment platform
    }
    
    # Check if it's a known legitimate domain
    if domain_lower in legitimate_domains:
        return False
    
    # Check for typosquatting - domains that look similar to legitimate ones
    suspicious_patterns = [
        # Common typosquatting patterns
        r'g[o0]{2}gle',  # g00gle, go0gle, etc.
        r'goog[e1]e',    # googe, goog1e
        r'micr[o0]soft', # micr0soft
        r'faceb[o0]ok',  # faceb00k
        r'amaz[o0]n',    # amaz0n
        r'payp[a4]l',    # payp4l
        r'[a4]pple',     # 4pple
        r'yah[o0]o',     # yah00
        r'[e3]bay',      # 3bay
    ]
    
    import re
    for pattern in suspicious_patterns:
        if re.search(pattern, domain_lower):
            return True
    
    # Check if domain contains legitimate service name but isn't the actual domain
    service_names = ['google', 'microsoft', 'apple', 'facebook', 'amazon', 'paypal', 
                     'ebay', 'netflix', 'twitter', 'linkedin', 'github', 'adobe',
                     'yahoo', 'outlook', 'hotmail', 'bank', 'chase', 'wells', 'postman']
    
    for service in service_names:
        if service in domain_lower:
            # If it contains a service name but isn't a known legitimate domain, it's suspicious
            # Check if it's a subdomain of a legitimate domain
            is_legitimate_subdomain = any(
                domain_lower.endswith('.' + legit) or domain_lower == legit
                for legit in legitimate_domains
            )
            if not is_legitimate_subdomain:
                # Additional check: if window title mentions the service but domain doesn't match
                if window_title:
                    title_lower = window_title.lower()
                    if service in title_lower and service in domain_lower:
                        # This could be a fake page - domain contains service name but isn't legitimate
                        return True
    
    # Check for suspicious TLDs or unusual domain structures
    suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq']  # Known for abuse
    if any(domain_lower.endswith(tld) for tld in suspicious_tlds):
        return True
    
    # Check for domains with numbers in suspicious places (like g00gle.com)
    if re.search(r'[a-z][0-9]{2,}[a-z]', domain_lower):
        return True
    
    return False


def _is_development_environment(detected_text: str, window_title: str = "") -> bool:
    """Check if this is a development environment (IDE, code editor, etc.) to avoid false positives"""
    if not detected_text and not window_title:
        return False
    
    text = (detected_text or "").upper()
    title = (window_title or "").upper()
    
    # Development environment indicators
    dev_indicators = [
        "VISUAL STUDIO", "VS CODE", "VSCODE", "CODE -", "PYCHARM", "INTELLIJ",
        "ECLIPSE", "SUBLIME", "ATOM", "VIM", "EMACS", "NOTEPAD++",
        "JETBRAINS", "ANDROID STUDIO", "XCODE", "DEVELOPER",
        "DEBUG", "BREAKPOINT", "CALL STACK", "TERMINAL", "CONSOLE",
        "GIT", "GITHUB", "BITBUCKET", "GITLAB",
        "PYTHON", "JAVASCRIPT", "TYPESCRIPT", "JAVA", "C++", "C#",
        "FUNCTION", "DEF ", "CLASS ", "IMPORT ", "FROM ", "RETURN ",
        "IF __NAME__", "MAIN()", "SYNTAX", "INDENT", "TAB",
        "SECURELY_CTK.PY", ".PY", ".JS", ".TS", ".JAVA", ".CPP"
    ]
    
    # Check window title first (most reliable indicator)
    for indicator in dev_indicators:
        if indicator in title:
            return True
    
    # Check detected text for code patterns
    code_patterns = [
        "DEF ", "CLASS ", "IMPORT ", "FROM ", "RETURN ", "IF ", "ELSE ",
        "FUNCTION", "VAR ", "LET ", "CONST ", "PUBLIC ", "PRIVATE ",
        "BREAKPOINT", "CALL STACK", "DEBUG CONSOLE", "TERMINAL",
        "SECURELY_CTK", ".PY", "PYTHON", "JAVASCRIPT"
    ]
    
    for pattern in code_patterns:
        if pattern in text:
            return True
    
    return False


def _is_payment_page(detected_text: str) -> bool:
    """Check if this is specifically a payment page (not a login page)"""
    if not detected_text:
        return False
    
    text = detected_text.upper()
    
    # Payment-specific keywords (must have these, not just generic form fields)
    payment_keywords = [
        "CARD NUMBER", "CREDIT CARD", "DEBIT CARD", "CVV", "CVC",
        "EXPIRY DATE", "EXPIRATION", "EXP DATE", "MM/YY", "MM/YYYY",
        "BILLING ADDRESS", "BILLING", "ZIP CODE", "POSTAL CODE",
        "PAYMENT METHOD", "PAY NOW", "CHECKOUT", "PROCEED TO PAYMENT",
        "TOTAL PRICE", "SUBTOTAL", "ORDER TOTAL", "PAYMENT INFORMATION"
    ]
    
    # Login-specific keywords (if these are present without payment keywords, it's likely a login)
    login_keywords = [
        "PASSWORD", "USERNAME", "SIGN IN", "LOG IN", "LOGIN",
        "FORGOT PASSWORD", "RESET PASSWORD", "ACCOUNT LOGIN"
    ]
    
    payment_count = sum(1 for kw in payment_keywords if kw in text)
    login_count = sum(1 for kw in login_keywords if kw in text)
    
    # If payment keywords are present and outnumber login keywords, it's a payment page
    if payment_count > 0 and payment_count >= login_count:
        return True
    
    return False


def _looks_like_login_or_payment_page(detected_text: str, window_title: str = "") -> bool:
    """Heuristic check: determine whether OCR-detected text resembles a login/payment web page.
    
    Also checks for suspicious/fake domains that might be phishing attempts.
    Distinguishes between login pages (credentials) and payment pages (card info).

    Look for both a URL/domain indicator and form-related labels close together.
    """
    if not detected_text:
        return False
    
    # Exclude development environments to avoid false positives
    if _is_development_environment(detected_text, window_title):
        return False
    
    text = detected_text.upper()

    # Extract domains from text
    domains = _extract_domains_from_text(detected_text)
    
    # Check for suspicious domains - if found, this is likely a fake/phishing page
    for domain in domains:
        if _is_suspicious_domain(domain, window_title):
            print(f"⚠️ Suspicious domain detected: {domain} - Possible phishing/fake page")
            return True  # Treat suspicious domains as sensitive pages (but will be flagged as threats, not legitimate)

    # URL/domain patterns
    import re
    url_pattern = re.compile(r'https?://\S+|www\.\S+|[A-Z0-9.-]+\.(COM|NET|ORG|BANK|IO|CO|EDU|GOV)')
    has_url = bool(url_pattern.search(text))

    # Separate login and payment indicators
    login_keywords = [
        "LOGIN", "SIGN IN", "SIGN-IN", "USERNAME", "PASSWORD", "PASSWORD:",
        "FORGOT PASSWORD", "RESET PASSWORD", "ACCOUNT LOGIN", "ENTER PASSWORD"
    ]
    
    payment_keywords = [
        "CARD NUMBER", "CREDIT CARD", "DEBIT CARD", "CVV", "CVC", "EXPIR", "EXPIRATION",
        "BILLING", "PAYMENT", "PAY NOW", "CHECKOUT", "ENTER CARD", "EXPIRY DATE"
    ]
    
    # Generic form indicators (could be either)
    generic_keywords = ["EMAIL", "EMAIL ADDRESS", "FULL NAME", "NAME"]
    
    found_login_keywords = [k for k in login_keywords if k in text]
    found_payment_keywords = [k for k in payment_keywords if k in text]
    found_generic_keywords = [k for k in generic_keywords if k in text]

    # If it's clearly a payment page, treat it as such (but still sensitive)
    if _is_payment_page(detected_text):
        # Payment pages are sensitive and should trigger pause, but are not "login" pages
        if has_url or len(found_payment_keywords) >= 2:
            return True
    
    # Login page detection: requires login-specific keywords
    if len(found_login_keywords) >= 1 and has_url:
        return True

    # If we have both login and payment keywords, prioritize based on count
    if len(found_login_keywords) > 0 and len(found_payment_keywords) > 0:
        # If payment keywords outnumber login, it's a payment page
        if len(found_payment_keywords) >= len(found_login_keywords):
            return True  # Payment page
        else:
            return True  # Login page
    
    # Generic form with URL: require multiple indicators
    if len(found_generic_keywords) >= 2 and has_url and (len(found_login_keywords) > 0 or len(found_payment_keywords) > 0):
        return True

    # If there are many form-like keywords but no explicit URL, check for browser UI markers
    total_keywords = len(found_login_keywords) + len(found_payment_keywords) + len(found_generic_keywords)
    if total_keywords >= 3 and ("HTTPS" in text or "HTTP" in text or "SECURE" in text):
        return True

    return False


def process_ai_response(text_response, detected_text=None, monitor=None, window_title=None):
    """Process AI response regardless of which API it came from.

    Uses OCR `detected_text` to avoid pausing on emails that merely mention login fields.
    
    Args:
        text_response: AI response text
        detected_text: OCR detected text
        monitor: Optional ScreenMonitor instance to check if this is a quick scan
        window_title: Optional window title for domain validation
    """
    # Check for legitimate login/payment detection, but only pause for explicit pages/forms
    resp_upper = text_response.upper()
    
    # Handle payment pages separately from login pages
    is_payment_page = "LEGITIMATE_PAYMENT" in resp_upper or _is_payment_page(detected_text or "")
    is_login_page = "LEGITIMATE_LOGIN" in resp_upper
    
    if is_payment_page or is_login_page:
        # Defer to OCR-aware heuristic to decide whether this is an actual page/form
        # Get window title for domain validation
        window_title = ""
        if monitor and hasattr(monitor, 'main_window'):
            try:
                import win32gui
                active_window = win32gui.GetForegroundWindow()
                window_title = win32gui.GetWindowText(active_window)
            except Exception:
                window_title = ""
        
        try:
            is_page = _looks_like_login_or_payment_page(detected_text or "", window_title)
        except Exception as _e:
            audit_log(f"Login/page heuristic error: {_e}", 'ERROR')
            is_page = False

        if is_page:
            # Determine if this is a payment page or login page
            page_type = "payment" if is_payment_page else "login"
            # Check if this is a quick scan - if so, don't pause
            is_quick_scan = False
            if monitor is not None:
                try:
                    is_quick_scan = getattr(monitor, '_one_shot', False)
                except Exception:
                    pass

            if is_quick_scan:
                page_type_label = "payment" if page_type == "payment" else "login"
                audit_log(f"Legitimate {page_type_label} page detected during Quick Scan - Not pausing (pause only works during 24/7 monitoring or Scan for 15m)", 'INFO')
                # Still notify the user that it was detected, but don't pause
                try:
                    show_notification(
                            title=f"{page_type_label.capitalize()} Page Detected",
                            message=f"Securely detected a {page_type_label} page during Quick Scan. Auto-pause only works during 24/7 monitoring or Scan for 15m.",
                            duration=8
                    )
                except Exception:
                    pass
                return []  # Don't treat as threat, but don't pause either
            
            # Not a quick scan - check if it's a temporary scan and stop it first
            page_type_label = "payment" if page_type == "payment" else "login"
            
            # Check if this is a temporary scan (15-minute scan) - if so, stop it
            is_temporary_scan = False
            if monitor is not None:
                try:
                    is_temporary_scan = hasattr(monitor, '_multi_scan_until') and getattr(monitor, '_multi_scan_until', 0) > time.time()
                except Exception:
                    pass
            
            if is_temporary_scan:
                audit_log(f"Legitimate {page_type_label} page detected during temporary scan - Stopping temporary scan and pausing", 'INFO')
                # Stop the temporary scan by clearing the timer
                try:
                    if hasattr(monitor, '_multi_scan_until'):
                        delattr(monitor, '_multi_scan_until')
                except Exception as e:
                    audit_log(f"Error stopping temporary scan: {e}", 'ERROR')
                
                # Update UI to stop the temporary scan countdown and reset button
                # The pause UI will be updated by _ui_pause_update() below
                if monitor and hasattr(monitor, 'main_window') and monitor.main_window:
                    try:
                        def _stop_temporary_scan_ui():
                            try:
                                main_win = monitor.main_window
                                # Cancel temporary scan countdown
                                if hasattr(main_win, '_scan_countdown_after_id') and main_win._scan_countdown_after_id:
                                    try:
                                        main_win.after_cancel(main_win._scan_countdown_after_id)
                                    except Exception:
                                        pass
                                    main_win._scan_countdown_after_id = None
                                
                                # Reset countdown state
                                if hasattr(main_win, 'short_scan_seconds'):
                                    main_win.short_scan_seconds = 0
                                
                                # Update button to show it can be started again
                                if hasattr(main_win, 'short_scan_btn'):
                                    try:
                                        button_text = main_win.get_scan_button_text() if hasattr(main_win, 'get_scan_button_text') else "Scan for 15m"
                                        main_win.short_scan_btn.configure(text=button_text, fg_color="#0969da", hover_color="#0860ca")
                                    except Exception:
                                        pass
                            except Exception as e:
                                audit_log(f"Error updating UI after stopping temporary scan: {e}", 'ERROR')
                        
                        try:
                            monitor.main_window.after(50, _stop_temporary_scan_ui)
                        except Exception:
                            _stop_temporary_scan_ui()
                    except Exception as e:
                        audit_log(f"Error scheduling UI update: {e}", 'ERROR')
            
            # Proceed with auto-pause (for both temporary scan and 24/7 monitoring)
            audit_log(f"Legitimate {page_type_label} page detected - Auto-pausing Securely", 'INFO')
            # Set global pause flag so monitor/thread can react
            # Also store if this was a temporary scan so the notification can mention it
            try:
                globals()['PAUSED_FOR_SENSITIVE_PAGE'] = True
                if is_temporary_scan:
                    globals()['PAUSED_DURING_TEMPORARY_SCAN'] = True
            except Exception:
                pass

            # Don't send notification here - let the UI update function handle it to avoid duplicates
            # The notification will be sent in _ui_pause_update with the correct message about auto-resume

            return []  # Don't treat as threat
        else:
            # Do not auto-pause for ambiguous cases (e.g. an email that mentions login fields)
            audit_log("AI flagged LEGITIMATE_LOGIN but OCR/URL heuristic did not confirm a login/payment page — not pausing", 'INFO')
            return []

    elif text_response.startswith("SUSPICIOUS:") or "SUSPICIOUS" in text_response:
        threat_desc = text_response.replace("SUSPICIOUS:", "").strip()
        audit_log(f"AI DETECTED THREAT: {threat_desc}", 'THREAT')
        return [threat_desc]
    elif text_response.startswith("UNSURE:") or "UNSURE" in text_response.upper():
        # Handle uncertain content - notify user but don't treat as high-priority threat
        unsure_desc = text_response.replace("UNSURE:", "").replace("unsure:", "").strip()
        if not unsure_desc:
            unsure_desc = "Content appears uncertain - manual review recommended"
        audit_log(f"AI UNCERTAIN: {unsure_desc}", 'WARNING')
        # Return as "Unsure" threat so user is notified but it's categorized differently
        return [f"Unsure: {unsure_desc}"]
    else:
        audit_log("AI says: Content appears safe", 'SUCCESS')
        return []  # Safe content

def analyze_screenshot_for_training(screenshot_path, detected_text):
    """Provide detailed training analysis of a screenshot"""
    global _groq_clients, _current_api_key_index
    
    # Check if Groq API is available
    if not GROQ_API_KEYS or len(GROQ_API_KEYS) == 0:
        return "AI analysis unavailable - no valid Groq API keys configured."
    
    # Get available API key
    api_key_index = get_next_available_api_key()
    if api_key_index is None:
        return "AI analysis unavailable - all API keys are in cooldown or unavailable."
    
    _groq_client = _groq_clients[api_key_index]
    
    # Convert image to base64 for API
    try:
        with open(screenshot_path, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        return f"Error reading screenshot: {e}"
    
    prompt = f"""CYBERSECURITY TRAINING ANALYSIS:
    
    You are a cybersecurity expert providing detailed training explanations.
    Analyze the detected text from a screenshot for security threats.
    
    Detected text from screen (OCR): "{detected_text}"
    
    Provide a comprehensive analysis covering:
    1. THREAT LEVEL: (Safe/Suspicious/Malicious)
    2. WHAT THIS TEXT INDICATES: Describe what this text likely represents
    3. WHY IT'S CONCERNING/SAFE: Detailed explanation
    4. RED FLAGS: Specific warning signs (if any)
    5. PREVENTION TIPS: How to avoid this threat
    6. WHAT TO DO: Immediate actions to take
    
    Be educational and detailed - this is for training purposes.
    If no text was detected, explain that the screen appears empty or contains only images.
    """
    
    # Prepare messages for Groq (text-only, no vision models available)
    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    try:
        chat_completion = _groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )
        
        analysis = chat_completion.choices[0].message.content.strip()
        return analysis
        
    except Exception as e:
        error_str = str(e)
        current_time = time.time()
        
        # Handle rate limits - switch to next key
        if "rate limit" in error_str.lower() or "429" in error_str.lower():
            _api_cooldowns[api_key_index] = current_time + 65
            audit_log(f"Groq API Key {api_key_index + 1} rate limit - switching to next key", 'WARNING')
            # Try next available key
            next_key = get_next_available_api_key()
            if next_key is not None and next_key != api_key_index:
                audit_log(f"Retrying with API key {next_key + 1}", 'SWITCH')
                _groq_client = _groq_clients[next_key]
                try:
                    chat_completion = _groq_client.chat.completions.create(
                        model=GROQ_MODEL,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=2048,
                    )
                    analysis = chat_completion.choices[0].message.content.strip()
                    return analysis
                except Exception:
                    pass  # Fall through to error handling below
            
            # API rate limited - provide a safe explanation using local keyword detection
            try:
                keywords_found = analyze_text(detected_text or "", strict_mode=False)
            except Exception:
                keywords_found = []

            if keywords_found:
                found_list = ', '.join(keywords_found[:6])
                return (f"⚠️ API RATE LIMIT — analysis unavailable (429).\n\n"
                        f"Local keyword scan found potential indicators: {found_list}.\n\n"
                        "Explanation: The AI service is rate-limited, so a full model analysis could not be performed. "
                        "However, a local keyword scan detected the terms above which may warrant manual review. "
                        "Open the Audit Log to review the captured text and consider taking a screenshot for later analysis.")
            else:
                return (f"⚠️ API RATE LIMIT — analysis unavailable (429).\n\n"
                        "Explanation: The AI service is rate-limited, so a full model analysis could not be performed. "
                        "A local keyword scan of the detected text found no obvious phishing, credential, or urgency keywords. "
                        "This suggests the content is likely safe, but continue to exercise caution and review the Audit Log if unsure.")
        else:
            error_msg = f"""⚠️ AI SERVICE ERROR

❌ Unable to connect to AI analysis service: {str(e)}

💡 Possible causes:
• Network connectivity issues
• API service temporarily unavailable
• Invalid API credentials

✅ Keyword-based detection is still active and protecting you."""
            return error_msg

# Comprehensive threat education database
THREAT_EDUCATION = {
    "virus": {
        "name": "Computer Virus",
        "description": "A computer virus is malicious software that infects files and spreads to other programs or computers. It can corrupt data, steal information, or damage your system.",
        "risks": ["Data corruption", "System crashes", "Identity theft", "Performance degradation"],
        "prevention": ["Keep antivirus updated", "Don't open suspicious attachments", "Avoid pirated software", "Regular system scans"]
    },
    "malware": {
        "name": "Malicious Software (Malware)",
        "description": "Malware is any software designed to harm your computer, steal data, or gain unauthorized access. It includes viruses, trojans, spyware, and ransomware.",
        "risks": ["Data theft", "Financial loss", "System compromise", "Privacy invasion"],
        "prevention": ["Use reputable antivirus", "Keep software updated", "Avoid suspicious downloads", "Enable firewall"]
    },
    "phishing": {
        "name": "Phishing Attack",
        "description": "Phishing is a cybercrime where attackers impersonate legitimate organizations to steal sensitive information like passwords, credit card numbers, or personal data.",
        "risks": ["Identity theft", "Financial fraud", "Account takeover", "Data breach"],
        "prevention": ["Verify sender authenticity", "Check URLs carefully", "Never share passwords via email", "Use two-factor authentication"]
    },
    "ransomware": {
        "name": "Ransomware",
        "description": "Ransomware encrypts your files and demands payment for the decryption key. It can lock you out of your own data and systems.",
        "risks": ["Data loss", "Financial extortion", "Business disruption", "Permanent file damage"],
        "prevention": ["Regular backups", "Keep systems updated", "Employee training", "Network segmentation"]
    },
    "trojan": {
        "name": "Trojan Horse",
        "description": "A trojan appears as legitimate software but contains malicious code. It can create backdoors, steal data, or download additional malware.",
        "risks": ["Remote access", "Data theft", "System compromise", "Additional malware installation"],
        "prevention": ["Download from trusted sources", "Read software reviews", "Use antivirus protection", "Check digital signatures"]
    },
    "spyware": {
        "name": "Spyware",
        "description": "Spyware secretly monitors your activities, collects personal information, and sends it to third parties without your knowledge or consent.",
        "risks": ["Privacy invasion", "Identity theft", "Financial fraud", "Personal data exposure"],
        "prevention": ["Use anti-spyware tools", "Avoid free suspicious software", "Read privacy policies", "Regular system scans"]
    },
    "adware": {
        "name": "Advertising Software (Adware)",
        "description": "Adware displays unwanted advertisements and may track your browsing habits. While not always malicious, it can slow your system and compromise privacy.",
        "risks": ["Privacy concerns", "System slowdown", "Unwanted ads", "Browser hijacking"],
        "prevention": ["Use ad blockers", "Avoid bundled software", "Read installation prompts carefully", "Use reputable software sources"]
    },
    "keylogger": {
        "name": "Keylogger",
        "description": "A keylogger records every keystroke you make, potentially capturing passwords, credit card numbers, and other sensitive information.",
        "risks": ["Password theft", "Financial fraud", "Identity theft", "Account compromise"],
        "prevention": ["Use virtual keyboards for sensitive input", "Enable keystroke encryption", "Regular malware scans", "Monitor account activity"]
    },
    "rootkit": {
        "name": "Rootkit",
        "description": "A rootkit hides deep in your system to maintain persistent access while concealing its presence from security software and users.",
        "risks": ["Complete system compromise", "Persistent backdoor access", "Data theft", "Difficult detection"],
        "prevention": ["Use rootkit scanners", "Keep OS updated", "Avoid suspicious downloads", "Regular security audits"]
    },
    "botnet": {
        "name": "Botnet",
        "description": "A botnet is a network of infected computers controlled remotely by cybercriminals to perform coordinated attacks or illegal activities.",
        "risks": ["Becoming part of cybercrime", "Legal liability", "System performance issues", "Data theft"],
        "prevention": ["Keep systems patched", "Use reputable antivirus", "Monitor network traffic", "Regular security updates"]
    }
}

def analyze_text(text, strict_mode=False):
    """Keyword analysis - now more effective by default, extra sensitive in strict mode"""
    found = []
    text_lower = text.lower()  # Convert once for faster multiple comparisons
    
    # In normal mode: Match full keywords only (more targeted)
    # In strict mode: Also match partial words for extra sensitivity
    for word in KEYWORDS:
        word_lower = word.lower()
        
        # Always check for full word matches
        if word_lower in text_lower:
            # For multi-word keywords, do substring match
            if ' ' in word_lower:
                if word_lower in text_lower:
                    found.append(word)
            else:
                # For single words, check word boundaries to avoid false positives
                # But in strict mode, allow partial matches too
                if strict_mode:
                    # Strict mode: any occurrence (substring match)
                    if word_lower in text_lower:
                        found.append(word)
                else:
                    # Normal mode: word boundary match (more accurate)
                    import re
                    pattern = r'\b' + re.escape(word_lower) + r'\b'
                    if re.search(pattern, text_lower):
                        found.append(word)
    
    return found

def get_primary_monitor(sct):
    """Get the primary monitor using Windows API - ensures we only capture from primary screen"""
    try:
        import ctypes
        from ctypes import wintypes
        
        # Get primary monitor dimensions using Windows API
        user32 = ctypes.windll.user32
        prim_width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
        prim_height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
        
        # Primary monitor should start at (0,0) or be the one with SM_CXSCREEN/SM_CYSCREEN dimensions
        primary_monitor = None
        
        # First, try to find monitor that matches primary screen dimensions and is at (0,0)
        for i, monitor in enumerate(sct.monitors):
            if i == 0:  # CRITICAL: Skip monitor[0] which is ALL monitors combined - never use this!
                continue
            # Check if this monitor matches primary screen dimensions and position
            if (monitor['width'] == prim_width and monitor['height'] == prim_height and
                monitor['left'] == 0 and monitor['top'] == 0):
                primary_monitor = monitor
                audit_log(f"Found primary monitor (exact match): {monitor['width']}x{monitor['height']} at ({monitor['left']},{monitor['top']})", 'INIT')
                break
        
        # If not found by exact match, find monitor containing (0,0)
        if not primary_monitor:
            for i, monitor in enumerate(sct.monitors):
                if i == 0:  # CRITICAL: Skip monitor[0] - never use this!
                    continue
                left, top, right, bottom = monitor['left'], monitor['top'], monitor['left'] + monitor['width'], monitor['top'] + monitor['height']
                if left <= 0 <= right and top <= 0 <= bottom:
                    primary_monitor = monitor
                    audit_log(f"Found primary monitor (contains 0,0): {monitor['width']}x{monitor['height']} at ({monitor['left']},{monitor['top']})", 'INIT')
                    break
        
        # Final fallback: use monitor[1] (but warn if it doesn't match expected primary)
        if not primary_monitor:
            primary_monitor = sct.monitors[1]
            audit_log(f"Using fallback monitor[1]: {primary_monitor['width']}x{primary_monitor['height']} at ({primary_monitor['left']},{primary_monitor['top']})", 'WARNING')
            audit_log(f"   Expected primary: {prim_width}x{prim_height} at (0,0)", 'WARNING')
        
        # CRITICAL SAFETY CHECK: Never use monitor[0] (all monitors combined)
        if primary_monitor == sct.monitors[0]:
            audit_log(f"ERROR: Attempted to use monitor[0] (all monitors) - using monitor[1] instead", 'ERROR')
            primary_monitor = sct.monitors[1]
        
        # Debug: List all monitors to help diagnose issues
        audit_log("All detected monitors:", 'INIT')
        for i, monitor in enumerate(sct.monitors):
            if i == 0:
                audit_log(f"Monitor[{i}]: ALL MONITORS COMBINED (width={monitor['width']}, height={monitor['height']}, left={monitor['left']}, top={monitor['top']}) - NOT USED", 'WARNING')
            else:
                is_primary = (monitor == primary_monitor)
                marker = "SELECTED" if is_primary else ""
                audit_log(f"Monitor[{i}]: {marker} width={monitor['width']}, height={monitor['height']}, left={monitor['left']}, top={monitor['top']}", 'INIT')
        
        return primary_monitor
    except Exception as e:
        audit_log(f"Error getting primary monitor: {e}", 'ERROR')
        # Fallback: use monitor[1] (never monitor[0])
        if len(sct.monitors) > 1:
            return sct.monitors[1]
        else:
            # This shouldn't happen, but if it does, return monitor[0] as last resort
            return sct.monitors[0]

def capture_training_screenshot(threat_type, description, text_content=""):
    """Capture screenshot for training analysis"""
    try:
        audit_log(f"Starting training screenshot capture for threat type: {threat_type}", 'FILE')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_dir = "training_screenshots"
        
        # Create directory if it doesn't exist
        if not os.path.exists(screenshot_dir):
            audit_log(f"Creating directory: {screenshot_dir}", 'FILE')
            os.makedirs(screenshot_dir)
        
        # Capture screenshot - PRIMARY MONITOR ONLY
        audit_log("Capturing screenshot from primary monitor", 'SCREENSHOT')
        with mss.mss() as sct:
            primary_monitor = get_primary_monitor(sct)
            screenshot = sct.grab(primary_monitor)  # Primary monitor only
            screenshot_path = os.path.join(screenshot_dir, f"threat_{timestamp}.png")
            audit_log(f"Saving screenshot to: {screenshot_path}", 'FILE')
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=screenshot_path)
        
        # Create training data entry
        training_id = f"{threat_type}_{timestamp}"
        training_data = {
            'screenshot_path': screenshot_path,
            'threat_type': threat_type,
            'description': description,
            'text_content': text_content,
            'timestamp': timestamp,
            'analyzed': False
        }
        
        audit_log(f"Training screenshot captured successfully: {training_id}", 'SUCCESS')
        return training_id, training_data
        
    except Exception as e:
        audit_log(f"Failed to capture training screenshot: {e}", 'ERROR')
        audit_log(f"Training screenshot error: {e}", 'ERROR')
        return None, None

def log_event(msg, threat_type=None, description=None, text_content=""):
    """Enhanced logging with training screenshot capture"""
    audit_log(f"Logging event: {msg[:100]}", 'FILE')
    
    # Use MM/DD/YYYY and 12-hour time without seconds
    date_part = datetime.now().strftime('%m/%d/%Y')
    time_part = datetime.now().strftime('%I:%M %p').lstrip('0')
    # Format: [MM/DD/YYYY] [H:MM AM/PM] Problem
    log_msg = f"[{date_part}] [{time_part}] {msg}"
    
    # Optionally capture training screenshot if this is a threat detection and training capture is enabled
    training_id = None
    if TRAINING_CAPTURE_ENABLED and threat_type and description:
        audit_log(f"Training capture enabled for threat: {threat_type}", 'SECURITY')
        training_id, training_data = capture_training_screenshot(threat_type, description, text_content)
        if training_id:
            log_msg += f" | Training ID: {training_id}"
            # Store training data globally (will be accessed by UI)
            if not hasattr(log_event, 'training_storage'):
                log_event.training_storage = {}
            log_event.training_storage[training_id] = training_data
    
    # Always write a textual audit entry to the log file. Include raw OCR/text content
    # on the following indented line (if provided). This keeps the Audit Log privacy-friendly
    # by storing only text and timestamps.
    try:
        audit_log(f"Writing to log file: securely_log.txt", 'FILE')
        with open("securely_log.txt", "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
            audit_log(f"Log entry written successfully", 'SUCCESS')
            # Do NOT write raw OCR/AI text to the audit log to preserve privacy.
            # Previously we wrote a Details/Raw Text block; per request we remove it entirely.
            # After writing the audit entry, trigger a UI refresh of the Audit Log
            try:
                if 'APP_MAIN_WINDOW' in globals() and getattr(globals()['APP_MAIN_WINDOW'], 'after', None):
                    # Schedule the load to run on the main thread (safe from background threads)
                    globals()['APP_MAIN_WINDOW'].after(200, globals()['APP_MAIN_WINDOW'].load_audit_log)
                    audit_log("UI audit log refresh scheduled", 'INFO')
            except Exception:
                # If UI refresh fails (no UI present), ignore silently
                pass
    except Exception as _e:
        audit_log(f"Failed to write secure log: {_e}", 'ERROR')

def get_threat_education(threat_keyword):
    """Get educational information about a specific threat"""
    threat_lower = threat_keyword.lower()
    
    # Find matching threat in education database
    for key, info in THREAT_EDUCATION.items():
        if key in threat_lower or threat_lower in key:
            return info
    
    # Generic fallback for unknown threats
    return {
        "name": "Security Threat",
        "description": "This appears to be a security-related term that requires attention. It may indicate potential malicious activity or suspicious content.",
        "risks": ["Potential system compromise", "Data security concerns", "Privacy risks", "Unknown threats"],
        "prevention": ["Exercise caution", "Verify legitimacy", "Keep security software updated", "Report suspicious activity"]
    }

def show_threat_education(threat_keyword):
    """Display educational popup about a specific threat"""
    try:
        import customtkinter as ctk
        threat_info = get_threat_education(threat_keyword)
        
        # Create education window
        education_window = tk.CTkToplevel()
        education_window.title(f"Security Education: {threat_info['name']}")
        education_window.geometry("600x500")
        education_window.configure(fg_color="#0d1117")
        
        # Make window stay on top
        education_window.attributes("-topmost", True)
        education_window.focus_force()
        
        # Header
        header_frame = ctk.CTkFrame(education_window, fg_color="#21262d", corner_radius=8)
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        title_label = ctk.CTkLabel(header_frame, text=f"🛡️ {threat_info['name']}",
                                  font=ctk.CTkFont(size=18, weight="bold"),
                                  text_color="#f85149")
        title_label.pack(pady=10)
        
        # Main content frame with scrollbar
        main_frame = ctk.CTkScrollableFrame(education_window, fg_color="#161b22")
        main_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Description
        desc_label = ctk.CTkLabel(main_frame, text="📖 What is this threat?",
                                 font=ctk.CTkFont(size=14, weight="bold"),
                                 text_color="#58a6ff", anchor="w")
        desc_label.pack(fill="x", pady=(10, 5))
        
        desc_text = ctk.CTkTextbox(main_frame, height=80, wrap="word",
                                  font=ctk.CTkFont(size=11))
        desc_text.pack(fill="x", pady=(0, 15))
        desc_text.insert("1.0", threat_info['description'])
        desc_text.configure(state="disabled")
        
        # Risks section
        risks_label = ctk.CTkLabel(main_frame, text="⚠️ Potential Risks",
                                  font=ctk.CTkFont(size=14, weight="bold"),
                                  text_color="#f85149", anchor="w")
        risks_label.pack(fill="x", pady=(0, 5))
        
        risks_text = "\\n".join([f"• {risk}" for risk in threat_info['risks']])
        risks_textbox = ctk.CTkTextbox(main_frame, height=100, wrap="word",
                                      font=ctk.CTkFont(size=11))
        risks_textbox.pack(fill="x", pady=(0, 15))
        risks_textbox.insert("1.0", risks_text)
        risks_textbox.configure(state="disabled")
        
        # Prevention section
        prevention_label = ctk.CTkLabel(main_frame, text="🛡️ Prevention Tips",
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       text_color="#28a745", anchor="w")
        prevention_label.pack(fill="x", pady=(0, 5))
        
        prevention_text = "\\n".join([f"• {tip}" for tip in threat_info['prevention']])
        prevention_textbox = ctk.CTkTextbox(main_frame, height=100, wrap="word",
                                           font=ctk.CTkFont(size=11))
        prevention_textbox.pack(fill="x", pady=(0, 15))
        prevention_textbox.insert("1.0", prevention_text)
        prevention_textbox.configure(state="disabled")
        
        # Close button
        close_btn = ctk.CTkButton(main_frame, text="✅ Got It!",
                                 font=ctk.CTkFont(size=12, weight="bold"),
                                 fg_color="#28a745", hover_color="#218838",
                                 command=education_window.destroy)
        close_btn.pack(pady=(10, 20))
        
        # Center the window
        education_window.update_idletasks()
        width = education_window.winfo_width()
        height = education_window.winfo_height()
        x = (education_window.winfo_screenwidth() // 2) - (width // 2)
        y = (education_window.winfo_screenheight() // 2) - (height // 2)
        education_window.geometry(f"{width}x{height}+{x}+{y}")
        
    except Exception as e:
        audit_log(f"Error showing threat education: {e}", 'ERROR')

# --- AI monitor thread ---
class ScreenMonitor(threading.Thread):
    def __init__(self, interval=SCREENSHOT_INTERVAL):
        super().__init__(daemon=True)
        self.interval = interval
        self.running = threading.Event()
        self.recent_alerts = []
        # notification controls (can be changed from UI)
        self.notifications_enabled = True
        self.sound_enabled = False
        self.strict_mode = False
        self.hitboxes_enabled = False
        self.test_mode = False
        self.main_window = None
        self.overlay_window = None
        self.active_threats = {}  # Track multiple active threats
        self.threat_history = {}  # Track threat positions over time
        self.false_positive_tracker = {}  # Track potential false positives
        self.threat_positions = {}  # Track current positions for smooth movement
        self.ai_status = "Initializing..."  # Track AI detection status
        self.ai_active = False  # Whether AI is currently processing
        
        # Duplicate notification prevention
        self.recent_notifications = {}  # Track {threat_description: timestamp} to prevent spam
        self.notification_cooldown = 60  # 1 minute cooldown for same threat (reduced from 5 minutes to show more notifications)
        self.window_threat_cache = {}  # Track {window_title: {threat: timestamp}} for per-window filtering
        self.window_threat_cache = {}  # Track {window_title: {threat: timestamp}} for per-window filtering
        
        # Training feature
        self.training_data = {}  # Store training screenshots and data

    def start_monitor(self):
        try:
            # Prevent multiple instances
            if hasattr(self, '_monitor_started') and self._monitor_started:
                self.running.set()
                return
                
            self.running.set()
            if not self.is_alive():
                self.start()
                self._monitor_started = True
        except Exception as e:
            audit_log(f"Monitor start error: {e}", 'ERROR')

    def request_scan_once(self):
        """Request the monitor to perform a single immediate scan."""
        try:
            # Mark one-shot request and ensure monitor is running
            self._one_shot = True
            self.start_monitor()
        except Exception as e:
            audit_log(f"request_scan_once error: {e}", 'ERROR')

    def request_scan_for(self, seconds=3):
        """Request the monitor to run for a short duration (seconds)."""
        try:
            self._multi_scan_until = time.time() + float(seconds)
            self.start_monitor()
        except Exception as e:
            audit_log(f"request_scan_for error: {e}", 'ERROR')

    def should_notify(self, threat_description, window_title=""):
        """Check if we should send a notification for this threat (prevents spam)"""
        current_time = time.time()
        
        # Clean up old notifications from history (older than cooldown period)
        expired_threats = [threat for threat, timestamp in self.recent_notifications.items() 
                          if current_time - timestamp > self.notification_cooldown]
        for threat in expired_threats:
            del self.recent_notifications[threat]
        
        # If we have window context, check per-window cache (shorter cooldown)
        if window_title:
            if window_title not in self.window_threat_cache:
                self.window_threat_cache[window_title] = {}
            
            window_cache = self.window_threat_cache[window_title]
            if threat_description in window_cache:
                last_time = window_cache[threat_description]
                # Reduced cooldown to 30 seconds per window to show more notifications
                if current_time - last_time < 30:  # 30 second cooldown per window (reduced from 60)
                    print(f"Suppressing duplicate alert from same window '{window_title[:30]}...'")
                    return False
        
        # Check if this threat was recently notified globally
        if threat_description in self.recent_notifications:
            last_notification_time = self.recent_notifications[threat_description]
            time_since_last = current_time - last_notification_time
            
            if time_since_last < self.notification_cooldown:
                # Too soon - don't notify again
                remaining_time = int(self.notification_cooldown - time_since_last)
                print(f"Suppressing duplicate notification for '{threat_description}' (cooldown: {remaining_time}s remaining)")
                return False
        
        # This is a new threat or cooldown has expired - allow notification
        return True
    
    def mark_notified(self, threat_description, window_title=""):
        """Mark a threat as notified (call this AFTER successfully sending notification)"""
        current_time = time.time()
        self.recent_notifications[threat_description] = current_time
        
        # Also mark in window-specific cache
        if window_title:
            if window_title not in self.window_threat_cache:
                self.window_threat_cache[window_title] = {}
            self.window_threat_cache[window_title][threat_description] = current_time
    
    def categorize_threat(self, threat_description):
        """Categorize threat based on description to determine notification title
        
        Returns appropriate category: "Threat Detected", "Suspicious Activity", "Unsure", etc.
        """
        if not threat_description:
            return "Unsure"
        
        desc_lower = threat_description.lower()
        
        # Check if AI explicitly marked it as "Unsure"
        if desc_lower.startswith("unsure:"):
            return "Unsure"
        
        # High-confidence threat indicators - clear malicious content
        high_threat_keywords = [
            "virus", "malware", "ransomware", "trojan", "spyware", "rootkit",
            "keylogger", "botnet", "backdoor", "exploit", "vulnerability",
            "infected", "compromised", "hacked", "breach", "attack",
            "malicious software", "malicious code", "harmful", "dangerous",
            "stealing", "steal", "theft", "fraud", "scam", "phishing",
            "credential harvesting", "password theft", "identity theft"
        ]
        
        # Suspicious activity indicators - potentially harmful but less certain
        suspicious_keywords = [
            "suspicious", "unusual", "unexpected", "strange", "odd",
            "questionable", "concerning", "warning", "alert", "caution",
            "potential threat", "possible", "might be", "could be",
            "unverified", "untrusted", "unknown source", "unfamiliar",
            "unusual activity", "suspicious email", "suspicious link",
            "suspicious website", "suspicious message", "suspicious attachment"
        ]
        
        # Uncertain/ambiguous indicators - needs review
        unsure_keywords = [
            "unclear", "ambiguous", "uncertain", "unidentified",
            "unknown", "unrecognized", "may be", "appears to be",
            "looks like", "seems", "possibly", "perhaps", "might",
            "could potentially", "needs review", "requires investigation",
            "manual review", "uncertain content"
        ]
        
        # Check for high-confidence threats first
        for keyword in high_threat_keywords:
            if keyword in desc_lower:
                return "Threat Detected"
        
        # Check for uncertain indicators (before suspicious, to prioritize "Unsure" category)
        for keyword in unsure_keywords:
            if keyword in desc_lower:
                return "Unsure"
        
        # Check for suspicious activity
        for keyword in suspicious_keywords:
            if keyword in desc_lower:
                return "Suspicious Activity"
        
        # Default based on AI response format
        if desc_lower.startswith("suspicious:"):
            return "Suspicious Activity"
        elif "threat" in desc_lower or "malicious" in desc_lower:
            return "Threat Detected"
        elif "suspicious" in desc_lower:
            return "Suspicious Activity"
        else:
            # Default to "Unsure" if we can't determine (more conservative)
            return "Unsure"
    
    def stop_monitor(self):
        try:
            self.running.clear()
            # Clear hitboxes when stopping
            if getattr(self, "hitboxes_enabled", False):
                self.close_overlay()
            # Clear tracking data
            self.threat_history = {}
            self.false_positive_tracker = {}
            self.active_threats = {}
            self.recent_notifications = {}  # Clear notification history
            # Reset monitor started flag
            if hasattr(self, '_monitor_started'):
                self._monitor_started = False
        except Exception as e:
            audit_log(f"Monitor stop error: {e}", 'ERROR')

    def run(self):
        with mss.mss() as sct:
            # Get PRIMARY monitor using Windows API - ensures we only capture from primary screen
            primary_monitor = get_primary_monitor(sct)
            prim_left = primary_monitor['left']
            prim_top = primary_monitor['top']
            prim_right = prim_left + primary_monitor['width']
            prim_bottom = prim_top + primary_monitor['height']
            
            audit_log(f"✅ PRIMARY MONITOR ONLY: left={prim_left}, top={prim_top}, width={primary_monitor['width']}, height={primary_monitor['height']}", 'SUCCESS')
            audit_log("   All other monitors will be IGNORED", 'INFO')
            audit_log("🚀 Screen monitoring started", 'SUCCESS')
            
            scan_count = 0
            while True:
                if not self.running.is_set():
                    time.sleep(0.01)  # Ultra-fast check - 10ms
                    continue
                    
                try:
                    scan_count += 1
                    scan_start_time = time.time()
                    
                    # Initialize findings list at the start of each scan iteration
                    findings = []
                    
                    # Update AI status
                    self.ai_status = "🔍 Scanning screen..."
                    self.ai_active = True
                    if self.main_window:
                        self.main_window.update_ai_status(self.ai_status)
                    
                    # Only log screenshot capture occasionally (every 20th scan)
                    if scan_count % 20 == 0:
                        audit_log(f"📸 Scan #{scan_count}: Capturing...", 'SCREENSHOT')
                    
                    # Capture screen or selected window target - PRIMARY MONITOR ONLY
                    img = None
                    im = None
                    try:
                        sel = None
                        if hasattr(self, 'main_window') and getattr(self.main_window, 'selected_target', None):
                            sel = getattr(self.main_window, 'selected_target')
                        # sel is ('window', hwnd, title) or ('screen', None, 'Entire Screen')
                        if sel and sel[0] == 'window' and sel[1]:
                            try:
                                import ctypes
                                rect = ctypes.wintypes.RECT()
                                user32 = ctypes.windll.user32
                                hwnd = int(sel[1])
                                if user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd):
                                    res = user32.GetWindowRect(hwnd, ctypes.byref(rect))
                                    if res:
                                        left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
                                        width = max(1, right - left)
                                        height = max(1, bottom - top)
                                        
                                        # Check if window is ENTIRELY on primary monitor - only capture if it is
                                        prim_left = primary_monitor['left']
                                        prim_top = primary_monitor['top']
                                        prim_right = prim_left + primary_monitor['width']
                                        prim_bottom = prim_top + primary_monitor['height']
                                        
                                        # STRICT: Only capture if window is ENTIRELY within primary monitor boundaries
                                        # This prevents capturing windows that span multiple monitors
                                        if (left >= prim_left and right <= prim_right and 
                                            top >= prim_top and bottom <= prim_bottom):
                                            # Window is entirely on primary monitor - safe to capture
                                            bbox = {
                                                'left': left,
                                                'top': top,
                                                'width': width,
                                                'height': height
                                            }
                                            img = sct.grab(bbox)
                                        else:
                                            # Window spans multiple monitors or is on secondary monitor - SKIP IT
                                            print(f"⚠️ Window spans monitors or is on secondary - skipping capture (window: {left},{top} to {right},{bottom}, primary: {prim_left},{prim_top} to {prim_right},{prim_bottom})")
                                            img = None
                            except Exception:
                                img = None

                        # Fallback to full primary screen if no valid window capture
                        # PRIMARY MONITOR ONLY
                        if img is None:
                            img = sct.grab(primary_monitor)  # Use explicitly found primary monitor

                        im = Image.frombytes("RGB", img.size, img.rgb)
                        audit_log(f"✅ Screenshot captured: {img.size[0]}x{img.size[1]} pixels", 'SCREENSHOT')
                    except Exception as _cap_e:
                        audit_log(f"❌ Capture error: {_cap_e}", 'ERROR')
                        # As a final fallback, try primary screen only
                        try:
                            audit_log("🔄 Attempting fallback capture...", 'WARNING')
                            img = sct.grab(primary_monitor)  # Use explicitly found primary monitor
                            im = Image.frombytes("RGB", img.size, img.rgb)
                            audit_log("✅ Fallback capture successful", 'SUCCESS')
                        except Exception as _final_e:
                            audit_log(f"❌ Final capture fallback failed: {_final_e}", 'ERROR')
                            time.sleep(0.5)
                            continue
                    
                    # Exclude notification area (bottom-right corner) from analysis
                    # This prevents Securely's own notifications from triggering false positives
                    width, height = im.size
                    notification_area_height = int(height * 0.15)  # Bottom 15% of screen
                    notification_area_width = int(width * 0.25)    # Right 25% of screen
                    
                    # Create a mask to exclude notification area (draw black box over it)
                    im_masked = im.copy()
                    draw = ImageDraw.Draw(im_masked)
                    # Black out bottom-right notification area
                    draw.rectangle(
                        [(width - notification_area_width, height - notification_area_height), (width, height)],
                        fill='black'
                    )
                    
                    # Convert masked image to base64 for AI analysis (without notification area)
                    import io
                    img_buffer = io.BytesIO()
                    im_masked.save(img_buffer, format='PNG')
                    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                    
                    # Extract text from FULL screen (for keyword detection, we want everything)
                    ocr_start_time = time.time()
                    if TESSERACT_AVAILABLE:
                        try:
                            screen_text = pytesseract.image_to_string(im, config=r'--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?@#$%^&*()_+-={}[]|\:\"<>?/')
                            # Only log OCR occasionally (every 30th scan)
                            if scan_count % 30 == 0:
                                ocr_duration = time.time() - ocr_start_time
                                text_length = len(screen_text)
                                audit_log(f"🔤 OCR: {text_length} chars ({ocr_duration:.1f}s)", 'OCR')
                        except Exception as _ocr_e:
                            audit_log(f"❌ OCR error: {_ocr_e}", 'ERROR')
                            screen_text = ""
                    else:
                        # Print a helpful one-time message and avoid spamming the console
                        if not TESS_WARNED:
                            error_msg = (
                                "⚠️ CRITICAL: Tesseract OCR is not installed!\n"
                                "Without OCR, Securely cannot read text from your screen to detect threats.\n\n"
                                "To fix this:\n"
                                "1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki\n"
                                "2. Install it to: C:\\Program Files\\Tesseract-OCR\\\n"
                                "3. Restart Securely\n\n"
                                "Until Tesseract is installed, threat detection will be limited."
                            )
                            audit_log(error_msg, 'ERROR')
                            # Try to show a notification about this critical issue
                            try:
                                show_notification(
                                    "⚠️ Tesseract OCR Not Installed",
                                    "Securely cannot read screen text. Install Tesseract OCR to enable threat detection. See console for details.",
                                    duration=15
                                )
                            except Exception:
                                pass
                            globals()['TESS_WARNED'] = True
                        screen_text = ""
                    
                    # Filter out Securely's own notifications and code from text analysis
                    filtered_lines = []
                    for line in screen_text.split('\n'):
                        line_lower = line.lower()
                        # Skip lines from Securely program itself
                        if 'securely' in line_lower and ('threat' in line_lower or 'alert' in line_lower):
                            continue
                        if 'view security audit' in line_lower:
                            continue
                        # Skip code editor content (file names, code syntax)
                        if 'securely_ctk.py' in line_lower or 'securely.py' in line_lower:
                            continue
                        # Skip Python code and dictionaries containing keywords
                        if 'keywords' in line_lower and ('=' in line or '[' in line):
                            continue  # Skip keyword definitions
                        if '"virus"' in line or "'virus'" in line or '"malware"' in line:
                            continue  # Skip quoted keyword strings in code
                        if 'THREAT_EDUCATION' in line or 'threat_education' in line_lower:
                            continue  # Skip threat education dictionary
                        if line.strip().startswith('#') or line.strip().startswith('//'):
                            continue
                        # Skip common IDE elements
                        if 'file' in line_lower and 'edit' in line_lower and 'view' in line_lower:
                            continue  # Menu bar
                        if 'explorer' in line_lower and '@' in line:
                            continue  # VS Code explorer
                        # Skip lines with lots of special characters (likely code)
                        if line.count('(') + line.count('{') + line.count('[') > 3:
                            continue
                        filtered_lines.append(line)
                    screen_text = '\n'.join(filtered_lines)
                    
                    # Add test content if in test mode for easier testing
                    if getattr(self, "test_mode", False):
                        screen_text += " test threat malicious test security test"
                        print("Test mode: Added test keywords to screen text")
                    
                    # Use AI to analyze the screen (if API key is valid)
                    self.ai_status = "🤖 AI analyzing..."
                    if self.main_window:
                        self.main_window.update_ai_status(self.ai_status)
                    
                    # Get window title for domain validation
                    window_title = ""
                    try:
                        import win32gui
                        active_window = win32gui.GetForegroundWindow()
                        window_title = win32gui.GetWindowText(active_window)
                        if window_title:
                            audit_log(f"🪟 Active window: {window_title[:50]}...", 'INFO')
                    except Exception:
                        window_title = ""
                    
                    # Run AI visual analysis on screen (use full unmasked image for position tracking)
                    ai_findings = analyze_screen_with_ai(img_base64, screen_text, monitor=self)  # Store AI findings separately (pass OCR text for heuristics, and monitor instance to check scan type)
                    
                    # Only log AI analysis results if threats found (threats are always logged)
                    if not ai_findings and scan_count % 15 == 0:
                        audit_log("🤖 AI: No threats", 'API')
                    
                    # Check for HTTP (insecure) URLs - ALWAYS flag HTTP sites as threats (regardless of environment)
                    # HTTP is unencrypted and insecure, so it should always be detected
                    # Also check window title for actual URL to avoid OCR misreads
                    if screen_text:
                        # First, try to get the actual URL from the window title (more accurate than OCR)
                        actual_url = ""
                        try:
                            import re
                            # Use the window_title already captured above
                            if window_title:
                                url_in_title = re.search(r'(https?://[^\s]+)', window_title, re.IGNORECASE)
                                if url_in_title:
                                    actual_url = url_in_title.group(1).lower()
                        except Exception:
                            pass
                        
                        urls = _extract_urls_from_text(screen_text)
                        for url in urls:
                            if _is_http_url(url):
                                # Double-check: if window title shows HTTPS, ignore OCR misread
                                if actual_url and actual_url.startswith('https://'):
                                    print(f"⚠️ OCR misread HTTPS as HTTP - ignoring false positive: {url}")
                                    continue
                                
                                # Flag ALL HTTP sites as threats (including localhost/local IPs)
                                # HTTP is unencrypted and insecure regardless of the domain
                                threat_msg = f"Insecure HTTP connection detected - {url}"
                                if threat_msg not in ai_findings:
                                    audit_log(f"🚨 HTTP threat detection: {threat_msg}", 'THREAT')
                                    ai_findings.append(threat_msg)
                    
                    # Also check detected text for suspicious domains even if AI didn't flag it
                    # But first check if this is a development environment to avoid false positives
                    if screen_text and not _is_development_environment(screen_text, window_title):
                        # Check for suspicious domains
                        domains = _extract_domains_from_text(screen_text)
                        for domain in domains:
                            if _is_suspicious_domain(domain, window_title):
                                # Determine if it's a payment or login page
                                is_payment = _is_payment_page(screen_text)
                                page_type = "payment" if is_payment else "login"
                                threat_msg = f"Fake {page_type} page detected - Suspicious domain: {domain}"
                                if threat_msg not in ai_findings:
                                    print(f"🚨 Domain-based threat detection: {threat_msg}")
                                    ai_findings.append(threat_msg)
                    
                    # If AI signaled a pause-for-sensitive-page, pause monitoring and update UI
                    try:
                        if globals().get('PAUSED_FOR_SENSITIVE_PAGE', False):
                            print("Auto-pause engaged due to sensitive page detection - pausing monitor")
                            # Don't stop the monitor - just pause it by clearing running flag
                            # This allows the pause countdown to work and auto-resume to function
                            try:
                                # Clear running flag to pause the monitor loop
                                self.running.clear()
                            except Exception:
                                pass

                            # Update main window UI on main thread
                            if self.main_window:
                                try:
                                    # Capture screen_text for use in the closure
                                    captured_screen_text = screen_text
                                    
                                    def _ui_pause_update():
                                        try:
                                            self.main_window.program_enabled = False
                                            # Update toggle button and status label to paused state
                                            if hasattr(self.main_window, 'program_toggle_btn'):
                                                self.main_window.program_toggle_btn.configure(text="Toggle 24/7 Monitoring", fg_color="#28a745", hover_color="#218838")
                                            if hasattr(self.main_window, 'status_label'):
                                                self.main_window.status_label.configure(text="● Paused (3:00)", text_color="#f85149")
                                            if hasattr(self.main_window, 'monitoring_var'):
                                                try:
                                                    self.main_window.monitoring_var.set(False)
                                                except Exception:
                                                    pass
                                            
                                            # Start countdown timer for status label
                                            pause_seconds = [180]  # 3 minutes - use list for mutable reference
                                            countdown_id = [None]
                                            
                                            def update_countdown():
                                                if pause_seconds[0] > 0 and globals().get('PAUSED_FOR_SENSITIVE_PAGE', False):
                                                    minutes = pause_seconds[0] // 60
                                                    seconds = pause_seconds[0] % 60
                                                    if hasattr(self.main_window, 'status_label'):
                                                        self.main_window.status_label.configure(text=f"● Paused ({minutes}:{seconds:02d})", text_color="#f85149")
                                                    pause_seconds[0] -= 1
                                                    countdown_id[0] = self.main_window.after(1000, update_countdown)
                                                else:
                                                    countdown_id[0] = None
                                            
                                            # Store countdown ID so it can be cancelled if needed
                                            if not hasattr(self.main_window, '_pause_countdown_id'):
                                                self.main_window._pause_countdown_id = None
                                            
                                            # Cancel any existing countdown
                                            if self.main_window._pause_countdown_id:
                                                try:
                                                    self.main_window.after_cancel(self.main_window._pause_countdown_id)
                                                except Exception:
                                                    pass
                                            
                                            # Start countdown
                                            countdown_id[0] = self.main_window.after(1000, update_countdown)
                                            self.main_window._pause_countdown_id = countdown_id[0]
                                            
                                            # Determine page type for notification (use captured screen_text)
                                            page_type = "payment" if _is_payment_page(captured_screen_text or "") else "login"
                                            page_type_label = "Payment" if page_type == "payment" else "Login"
                                            
                                            # Send a single notification explaining the pause and auto-resume
                                            try:
                                                # Check if this was during a temporary scan
                                                was_temporary_scan = globals().get('PAUSED_DURING_TEMPORARY_SCAN', False)
                                                if was_temporary_scan:
                                                    message = f"Securely detected a {page_type} page during temporary scan. Temporary scan stopped and monitoring paused. Will auto-resume in 3 minutes."
                                                    # Clear the flag after using it
                                                    try:
                                                        globals()['PAUSED_DURING_TEMPORARY_SCAN'] = False
                                                    except Exception:
                                                        pass
                                                else:
                                                    message = f"Securely detected a {page_type} page and has paused monitoring. It will automatically reactivate after 3 minutes."
                                                
                                                sent = show_notification(
                                                    f"{page_type_label} Page Detected - Monitoring Paused",
                                                    message,
                                                    duration=10
                                                )
                                                if not sent:
                                                    print("Native notification not available. Install 'win11toast' or 'win10toast' or 'winrt' for native toasts.")
                                            except Exception:
                                                pass

                                            # Schedule auto-resume in 3 minutes unless the user changes state
                                            try:
                                                # Cancel any previous pending auto-resume
                                                if hasattr(self.main_window, '_auto_resume_after_id') and self.main_window._auto_resume_after_id:
                                                    try:
                                                        self.main_window.after_cancel(self.main_window._auto_resume_after_id)
                                                    except Exception:
                                                        pass

                                                def _auto_resume():
                                                    try:
                                                        # Cancel countdown timer if still running
                                                        if hasattr(self.main_window, '_pause_countdown_id') and self.main_window._pause_countdown_id:
                                                            try:
                                                                self.main_window.after_cancel(self.main_window._pause_countdown_id)
                                                                self.main_window._pause_countdown_id = None
                                                            except Exception:
                                                                pass
                                                        
                                                        # Only resume if still paused/disabled and auto-pause flag was the cause
                                                        if not getattr(self.main_window, 'program_enabled', False):
                                                            # Clear pause flag
                                                            try:
                                                                globals()['PAUSED_FOR_SENSITIVE_PAGE'] = False
                                                            except Exception:
                                                                pass
                                                            # Update UI to Active
                                                            try:
                                                                self.main_window.program_enabled = True
                                                                if hasattr(self.main_window, 'program_toggle_btn'):
                                                                    self.main_window.program_toggle_btn.configure(text="Turn Off", fg_color="#dc3545", hover_color="#c82333")
                                                                if hasattr(self.main_window, 'status_label'):
                                                                    self.main_window.status_label.configure(text="● Active", text_color="#28a745")
                                                                if hasattr(self.main_window, 'monitoring_var'):
                                                                    self.main_window.monitoring_var.set(True)
                                                            except Exception:
                                                                pass
                                                            # Restart monitor if needed
                                                            try:
                                                                if not self.running.is_set():
                                                                    self.start_monitor()
                                                            except Exception:
                                                                pass
                                                            # Notify resumed
                                                            try:
                                                                show_notification("Monitoring Resumed", "Securely automatically resumed after 3 minutes.", duration=6)
                                                            except Exception:
                                                                pass
                                                    finally:
                                                        try:
                                                            self.main_window._auto_resume_after_id = None
                                                        except Exception:
                                                            pass

                                                self.main_window._auto_resume_after_id = self.main_window.after(180000, _auto_resume)  # 3 minutes = 180000ms
                                            except Exception as e:
                                                audit_log(f"Auto-resume schedule error: {e}", 'ERROR')
                                        except Exception as e:
                                            audit_log(f"UI pause update error: {e}", 'ERROR')

                                    self.main_window.after(50, _ui_pause_update)
                                except Exception:
                                    pass

                            # Continue to next loop without processing findings
                            continue
                    except Exception:
                        pass
                    if ai_findings:
                        print(f"AI detected: {ai_findings}")
                        # Store the image for hitbox position detection
                        self._last_analyzed_image = im
                    
                    # In test mode, simulate a threat detection
                    if getattr(self, "test_mode", False):
                        if not ai_findings:
                            ai_findings = []
                        ai_findings.append("Test threat detected - this is a simulation")
                    
                    # Start with AI findings
                    findings = ai_findings.copy() if ai_findings else []
                    
                    # Only run keyword detection if "More Strict" mode is enabled
                    keyword_findings = []
                    strict_mode_enabled = getattr(self, "strict_mode", False)
                    
                    if strict_mode_enabled and len(screen_text.strip()) > 0:
                        print(f"Strict mode enabled - Running keyword detection on text: {screen_text[:100]}...")
                        keyword_findings = analyze_text(screen_text, strict_mode=True)
                        if keyword_findings:
                            print(f"Keyword detection found: {keyword_findings}")
                        # Add keyword findings to all findings (remove duplicates)
                        for kf in keyword_findings:
                            if kf not in findings:
                                findings.append(kf)
                    elif not strict_mode_enabled:
                        print("Keyword detection disabled - Enable 'More Strict' mode to activate")
                    else:
                        print("No text detected on screen for analysis")
                    
                    # In strict mode, show enhanced status
                    if strict_mode_enabled:
                        print("✓ Strict mode: AI + Keyword detection active")
                    
                    if findings:
                        # Update AI status with threat count
                        threat_count = len(findings)
                        self.ai_status = f"⚠️ {threat_count} threat{'s' if threat_count != 1 else ''} detected"
                        self.ai_active = True
                        if self.main_window:
                            self.main_window.update_ai_status(self.ai_status)
                        
                        audit_log(f"🚨 {threat_count} threat(s): {', '.join([t[:60] + '...' if len(t) > 60 else t for t in findings[:3]])}", 'THREAT')
                        
                        # Get OCR data for logging (needed for all paths, not just hitboxes)
                        text = screen_text  # Use the already extracted screen_text
                    else:
                        # Update AI status - no threats found
                        self.ai_status = "✅ Screen secure"
                        self.ai_active = False
                        if self.main_window:
                            self.main_window.update_ai_status(self.ai_status)
                        
                        # Only log scan completion occasionally in compact mode (every 10th scan)
                        if scan_count % 10 == 0:
                            scan_duration = time.time() - scan_start_time
                            audit_log(f"Scan #{scan_count} ✓ No threats ({scan_duration:.1f}s)", 'SUCCESS')
                        
                        text = screen_text  # Still need text for hitbox tracking
                    
                    # Check if this is a quick scan (one-shot)
                    is_quick_scan = getattr(self, '_one_shot', False)
                    
                    # Record a scan audit entry
                    # For quick scans with threats: skip summary entry (individual threat entries will be logged below)
                    # For quick scans without threats: log "No threats detected"
                    # For continuous monitoring: log summary for both cases
                    try:
                        # Compose combined text: OCR text + AI analysis (if any)
                        ai_text = globals().get('LAST_AI_ANALYSIS', None)
                        combined_text = (text or "")
                        if ai_text:
                            combined_text = combined_text + "\n\nAI Analysis: " + ai_text

                        if findings:
                            # For quick scans, skip the summary entry - individual threat entries will be logged below
                            if not is_quick_scan:
                                # For continuous monitoring, add a summary entry
                                log_event("Scan Result: Threats detected", threat_type="SCAN_SUMMARY", description=", ".join([str(x) for x in findings]), text_content=combined_text)
                            # Individual threat entries will be logged in the loop below
                        else:
                            # If AI is currently in rate-limit cooldown, skip logging the generic 'No threats detected' entry
                            now_time = time.time()
                            if globals().get('_ai_in_rate_limit', False) or globals().get('_ai_rate_limit_until', 0) > now_time:
                                # Skip creating a 'No threats detected' audit log while AI is unavailable
                                print("Skipping 'No threats detected' audit entry due to AI cooldown")
                            else:
                                # Safe scan: log as informational scan entry (for both quick scan and continuous monitoring)
                                log_event("Scan Result: No threats detected", threat_type="SCAN", description="No threats detected", text_content=combined_text)
                    except Exception as _log_e:
                        audit_log(f"Audit log write failed: {_log_e}", 'ERROR')
                    
                    # Update continuous hitboxes if enabled - Run IMMEDIATELY when toggled
                    if getattr(self, "hitboxes_enabled", False):
                        # Initialize active_threats if it doesn't exist (persistent storage)
                        if not hasattr(self, 'active_threats'):
                            self.active_threats = {}
                        
                        # Run OCR EVERY scan for real-time hitbox updates (removed "every other scan" limitation)
                        should_run_ocr = True  # Always run OCR for hitboxes when enabled
                        
                        # Detect screen changes (scrolling) by comparing text content
                        current_text_hash = hash(screen_text[:500])  # Hash first 500 chars
                        last_text_hash = getattr(self, '_last_text_hash', None)
                        screen_changed = (last_text_hash is not None and current_text_hash != last_text_hash)
                        self._last_text_hash = current_text_hash
                        
                        # Process findings if we have any OR if we have active threats to track
                        if findings or self.active_threats:
                            if findings:
                                audit_log(f"Hitboxes enabled - processing {len(findings)} threat(s)", 'INFO')
                            
                            # Get OCR data for position tracking
                            try:
                                ocr_data = pytesseract.image_to_data(im, config='--psm 6 -c tessedit_do_invert=0', output_type=pytesseract.Output.DICT)
                            except Exception as ocr_error:
                                audit_log(f"OCR error (skipping this scan): {ocr_error}", 'ERROR')
                                ocr_data = None
                            
                            # For test mode, always show hitbox
                            if getattr(self, "test_mode", False):
                                self.active_threats["Test threat detected - this is a simulation"] = (200, 200, 300, 60)
                                print("Test mode: Added test hitbox")
                            
                            # Only process positions if OCR succeeded
                            if ocr_data:
                                # For AI-detected threats, try to find their locations on screen using OCR
                                for f in ai_findings:
                                    if f != "Test threat detected - this is a simulation":
                                        # Try to find where this threat appears on screen
                                        ai_threat_locations = self.find_all_threat_locations(f, text, ocr_data)
                                        if ai_threat_locations:
                                            # Store only the FIRST location (one box per unique threat)
                                            self.active_threats[f] = ai_threat_locations[0]  # Single location, not list
                                            print(f"AI detection - found location for: {f}")
                                        else:
                                            # Fallback: create warning banner if location not found
                                            banner_width = int(im.size[0] * 0.6)  # 60% of screen width
                                            banner_height = 80
                                            banner_x = int(im.size[0] * 0.2)  # Center horizontally
                                            banner_y = 50  # Near top
                                            # Store as single tuple (one box per threat)
                                            self.active_threats[f] = (banner_x, banner_y, banner_width, banner_height)
                                            audit_log(f"AI detection - creating warning banner for: {f}", 'THREAT')
                                
                                # For keyword-only threats, find the FIRST/BEST location (one box per threat)
                                for f in findings:
                                    if f not in ai_findings and f != "Test threat detected - this is a simulation":
                                        # Get locations where this threat appears, but only use the first/best one
                                        threat_locations = self.find_all_threat_locations(f, text, ocr_data)
                                        if threat_locations:
                                            # Store only the FIRST location (one box per unique threat)
                                            self.active_threats[f] = threat_locations[0]  # Single location, not list
                                            print(f"Keyword detection - found location for '{f}' at {threat_locations[0]}")
                                        else:
                                            print(f"Could not locate keyword '{f}' on screen")
                        
                        # Always update overlay if we have active threats (real-time updates)
                        # Clear old threats that are no longer detected to prevent accumulation
                        if findings:
                            # Only keep threats that are currently detected
                            current_threat_keys = set(findings + ai_findings)
                            if hasattr(self, 'active_threats'):
                                # Remove threats that are no longer present
                                keys_to_remove = [k for k in self.active_threats.keys() if k not in current_threat_keys and k != "Test threat detected - this is a simulation"]
                                for key in keys_to_remove:
                                    del self.active_threats[key]
                                    print(f"Removed stale threat from hitboxes: {key}")
                        
                        # Update overlay with current threats (one box per threat)
                        if self.active_threats:
                            self._hitbox_timeout = time.time()  # Reset timeout when updating
                            self.update_continuous_overlay(self.active_threats, im.size)
                        else:
                            # No threats - clear overlay
                            self.close_overlay()
                    else:
                        # Hitboxes disabled - clear any existing overlays
                        if hasattr(self, 'active_threats') and self.active_threats:
                            print("Hitboxes disabled - clearing overlay")
                            self.close_overlay()
                            self.active_threats = {}
                            if hasattr(self, '_hitbox_timeout'):
                                delattr(self, '_hitbox_timeout')
                    
                    # Send notifications and log events for each finding (only when we have findings)
                    if findings:
                        # Get active window title for context-aware duplicate detection
                        try:
                            import win32gui
                            active_window = win32gui.GetForegroundWindow()
                            window_title = win32gui.GetWindowText(active_window)
                        except:
                            window_title = ""
                        
                        # Send notifications and log events for each finding
                        for f in findings:
                            msg = f
                            
                            # Check if we should notify about this threat (prevents duplicate spam)
                            should_send_notification = self.should_notify(f, window_title)
                            
                            # Immediately mark as "in process" to prevent race conditions from rapid scans
                            if should_send_notification:
                                self.mark_notified(f, window_title)
                            
                            # only show desktop notifications when enabled AND not a duplicate
                            if getattr(self, "notifications_enabled", True) and should_send_notification:
                                # Create notification message in user's desired format
                                threat_name = f if len(f) < 50 else f[:50] + "..."
                                
                                # Categorize threat to determine notification title
                                threat_category = self.categorize_threat(f)
                                
                                # Adjust notification message based on category
                                if threat_category == "Unsure":
                                    # Remove "Unsure:" prefix from threat_name if it already has it to avoid duplication
                                    if threat_name.lower().startswith("unsure:"):
                                        threat_name_clean = threat_name[7:].strip()  # Remove "Unsure:" prefix
                                    else:
                                        threat_name_clean = threat_name
                                    notification_title = f"Unsure: {threat_name_clean}"
                                    notification_msg = f"Content appears uncertain - manual review recommended: {threat_name_clean}"
                                else:
                                    notification_title = f"{threat_category}: {threat_name}"
                                    notification_msg = f"Personalized threat detected: {threat_name}"
                                
                                # Use universal notification function (works in .exe)
                                notification_sent = show_notification(notification_title, notification_msg, duration=10)
                                # Only log notification failures
                                if not notification_sent:
                                    audit_log(f"❌ Notification failed: {threat_name[:50]}", 'ERROR')
                                
                                # No need to mark_notified here anymore - already done at the start
                            # play a short beep when sound alerts enabled (only for new notifications)
                            if should_send_notification and getattr(self, "sound_enabled", False) and winsound is not None:
                                try:
                                    winsound.Beep(1000, 300)  # Higher pitch for AI alerts
                                except Exception:
                                    pass
                            
                            # Log with training data capture (only for AI detections with screenshots)
                            if should_send_notification:
                                # Only create screenshot/audit log entry if AI detected this threat
                                if f in ai_findings:
                                    print(f"AI detection - creating audit entry for: {f}")
                                    # Include OCR text plus the raw AI analysis text (if available) in the audit log
                                    ai_text = globals().get('LAST_AI_ANALYSIS', None)
                                    combined_text = text or ""
                                    if ai_text:
                                        combined_text = combined_text + "\n\nAI Analysis: " + ai_text
                                    # Log as textual entry only (no screenshots saved to audit log view)
                                    log_event(msg, threat_type="AI_THREAT", description=f, text_content=combined_text)
                                else:
                                    print(f"Keyword detection only - no screenshot/audit entry for: {f}")
                                    # Just log to text file without screenshot for keyword-only detections
                                    with open("securely_log.txt", "a", encoding="utf-8") as log_file:
                                        timestamp = time.strftime('%H:%M:%S')
                                        log_file.write(f"[{timestamp}] {msg} (keyword detection)\n")
                                self.recent_alerts.append(msg)
                                if len(self.recent_alerts) > 10:  # Keep more AI alerts
                                    self.recent_alerts.pop(0)
                            else:
                                # Still update recent alerts but don't create new log entry
                                if msg not in self.recent_alerts:
                                    print(f"Duplicate threat detected (not logging): {f}")
                                
                except Exception as e:
                    audit_log(f"Screen monitoring error: {e}", 'ERROR')
                    
                # Dynamic scan interval based on AI rate limit status and API errors
                global _ai_in_rate_limit, _api_failure_counts, _api_cooldowns
                
                # Check if APIs are having issues (timeouts, errors)
                current_time_check = time.time()
                api_issues = False
                for api_name, cooldown_time in _api_cooldowns.items():
                    if cooldown_time > current_time_check:
                        api_issues = True
                        break
                
                # Check if failure counts are high (indicating persistent issues)
                total_failures = sum(_api_failure_counts.values())
                if total_failures > 3:
                    api_issues = True
                
                if getattr(self, "hitboxes_enabled", False):
                    # Hitboxes enabled - use fast scanning for real-time updates
                    time.sleep(0.3)  # 300ms interval for responsive hitbox updates
                elif _ai_in_rate_limit or api_issues:
                    # AI rate limited or API issues - scan every 5 seconds to reduce load
                    time.sleep(5.0)  # 5 second interval during rate limit/API issues
                else:
                    # Normal scanning - reasonable interval to avoid overwhelming the API
                    time.sleep(1.0)  # 1 second interval (increased from 50ms to reduce API load)
                # If this was a one-shot scan request, stop after one iteration
                try:
                    now = time.time()
                    if hasattr(self, '_one_shot') and getattr(self, '_one_shot'):
                        # Before clearing the one-shot flag, send a summary notification
                        try:
                            now_time = time.time()
                            # If AI is currently rate-limited, avoid showing a normal scan result
                            # and instead explicitly notify the user that Securely is on cooldown.
                            if globals().get('_ai_in_rate_limit', False) or globals().get('_ai_rate_limit_until', 0) > now_time:
                                try:
                                    cooldown_msg = (
                                        "Securely is currently on cooldown due to AI rate limits.\n\n"
                                        "A keyword-only scan was performed. Results are recorded in the Audit Log.\n\n"
                                        "Tip: Wait a moment or try again later for full AI analysis."
                                    )
                                    sent = show_notification("Securely: AI Cooldown", cooldown_msg, duration=8)
                                    if not sent:
                                        audit_log("Cooldown notification (native) failed; showing console message instead.", 'WARNING')
                                    else:
                                        print("Cooldown notification shown to user.")

                                    # Also show a brief UI status update so repeated Quick Scan clicks are visible
                                    try:
                                        if self.main_window and hasattr(self.main_window, 'status_label'):
                                            prev_text = None
                                            prev_color = None
                                            try:
                                                prev_text = self.main_window.status_label.cget('text')
                                                prev_color = self.main_window.status_label.cget('text_color')
                                            except Exception:
                                                prev_text = None
                                                prev_color = None

                                            try:
                                                self.main_window.status_label.configure(text='● Cooldown (AI rate limit)', text_color='#f59e0b')
                                            except Exception:
                                                pass

                                            def _restore_status():
                                                try:
                                                    if prev_text is not None:
                                                        self.main_window.status_label.configure(text=prev_text)
                                                    if prev_color is not None:
                                                        try:
                                                            self.main_window.status_label.configure(text_color=prev_color)
                                                        except Exception:
                                                            pass
                                                except Exception:
                                                    pass

                                            try:
                                                # Revert after 6 seconds so user notices the message
                                                self.main_window.after(6000, _restore_status)
                                            except Exception:
                                                # If after is not available, just ignore
                                                pass
                                    except Exception as _e:
                                        audit_log(f"Cooldown UI update error: {_e}", 'ERROR')
                                except Exception as _e:
                                    audit_log(f"Cooldown notification error: {_e}", 'ERROR')
                            else:
                                # Summarize findings from this iteration
                                # Only show summary notification if NO threats were found (to avoid duplicate notifications)
                                # If threats were found, they were already notified individually above
                                sent = False  # Initialize sent variable
                                
                                # Check if API keys are available - don't send completion notification if all keys failed
                                api_keys_available = False
                                try:
                                    if GROQ_API_KEYS and len(GROQ_API_KEYS) > 0:
                                        # Check if any key is available (not in cooldown or failed)
                                        next_key = get_next_available_api_key()
                                        if next_key is not None:
                                            api_keys_available = True
                                        # Also check if we have any initialized clients that aren't in long cooldown (1 hour = invalid)
                                        if not api_keys_available:
                                            current_time_check = time.time()
                                            for idx in range(len(GROQ_API_KEYS)):
                                                cooldown_until = _api_cooldowns.get(idx, 0)
                                                # If cooldown is less than 1 hour, it's just a temporary issue, not invalid keys
                                                if idx in _groq_clients and _groq_clients[idx] is not None:
                                                    if cooldown_until <= current_time_check or (cooldown_until - current_time_check) < 3600:
                                                        api_keys_available = True
                                                        break
                                except Exception:
                                    api_keys_available = False
                                
                                if not findings and api_keys_available:
                                    summary_title = "Securely - Scan Result"
                                    msg = "✅ Scan complete - No threats detected."
                                    sent = show_notification(summary_title, msg, duration=8)
                                    if not sent:
                                        audit_log("Native notification failed: ensure 'win11toast', 'win10toast', or 'winrt' is installed.", 'WARNING')
                                elif not findings and not api_keys_available:
                                    # Skip notification if API keys are missing/invalid - user already got "AI Unavailable" notification
                                    pass  # Don't send completion notification when API keys are unavailable
                                # If threats were found, skip the summary notification to avoid duplicates
                        except Exception as _e:
                            audit_log(f"One-shot notification error: {_e}", 'ERROR')

                        try:
                            delattr(self, '_one_shot')
                        except Exception:
                            pass
                        self.running.clear()
                        # Update main window UI to show paused after one-shot
                        try:
                            if self.main_window:
                                def _set_paused_ui():
                                    try:
                                        self.main_window.program_enabled = False
                                        try:
                                            self.main_window.program_toggle_btn.configure(text="Toggle 24/7 Monitoring", fg_color="#28a745", hover_color="#218838")
                                        except Exception:
                                            pass
                                        try:
                                            self.main_window.status_label.configure(text="● Disabled", text_color="#f85149")
                                        except Exception:
                                            pass
                                        try:
                                            if hasattr(self.main_window, 'monitoring_var'):
                                                self.main_window.monitoring_var.set(False)
                                        except Exception:
                                            pass
                                    except Exception:
                                        pass
                                try:
                                    self.main_window.after(50, _set_paused_ui)
                                except Exception:
                                    _set_paused_ui()
                        except Exception:
                            pass
                    elif hasattr(self, '_multi_scan_until'):
                        if now >= self._multi_scan_until:
                            try:
                                delattr(self, '_multi_scan_until')
                            except Exception:
                                pass
                            self.running.clear()
                except Exception:
                    pass
    
    def find_specific_threat_location(self, threat_text, full_text, ocr_data):
        """Find exact location of specific threat/keyword on screen with position memory (returns best match)"""
        all_locations = self.find_all_threat_locations(threat_text, full_text, ocr_data)
        if all_locations:
            return all_locations[0]  # Return first (best) match for backward compatibility
        return None
    
    def find_all_threat_locations(self, threat_text, full_text, ocr_data):
        """Find ALL locations where a threat/keyword appears on screen"""
        try:
            threat_lower = threat_text.lower()
            
            # Look for the threat keyword in the OCR results
            all_matches = []
            
            for i, text in enumerate(ocr_data['text']):
                if text.strip():
                    text_lower = text.lower().strip()
                    
                    # Check if this text contains our threat
                    contains_threat = False
                    
                    # Direct keyword match
                    if threat_lower in text_lower:
                        contains_threat = True
                    
                    # Check against our keywords list
                    for keyword in KEYWORDS:
                        if keyword.lower() == threat_lower and keyword.lower() in text_lower:
                            contains_threat = True
                            break
                    
                    if contains_threat:
                        confidence = ocr_data['conf'][i]
                        if confidence > 10:  # Even lower threshold for instant tracking
                            x = ocr_data['left'][i]
                            y = ocr_data['top'][i]
                            w = ocr_data['width'][i]
                            h = ocr_data['height'][i]
                            
                            # Make sure the dimensions are reasonable
                            if w > 1 and h > 1:  # Maximum leniency for instant response
                                all_matches.append({
                                    'position': (x, y, w, h),
                                    'confidence': confidence,
                                    'distance': 0  # Will calculate if we have previous position
                                })
            
            if not all_matches:
                return []
            
            # Sort by confidence (highest first)
            all_matches.sort(key=lambda x: -x['confidence'])
            
            # Return ALL matches with padding
            result_locations = []
            padding = 4
            for match in all_matches:
                x, y, w, h = match['position']
                # Add padding around each detected text
                box_x = max(0, x - padding)
                box_y = max(0, y - padding)
                box_w = w + (padding * 2)
                box_h = h + (padding * 2)
                result_locations.append((box_x, box_y, box_w, box_h))
            
            return result_locations
            
        except Exception as e:
            audit_log(f"Threat location error: {e}", 'ERROR')
            return []
    
    def update_continuous_overlay(self, current_threats, screen_size):
        """Update continuous overlay with all active threats
        
        Hitboxes will persist on screen while the feature is enabled.
        Threats are added to active_threats and remain visible until hitboxes are disabled.
        """
        try:
            print(f"update_continuous_overlay called with {len(current_threats)} threats")
            
            # If hitboxes disabled, clear overlay
            if not getattr(self, "hitboxes_enabled", False):
                print("Hitboxes disabled - clearing overlay")
                self.close_overlay()
                if hasattr(self, 'active_threats'):
                    self.active_threats = {}
                return
            
            # current_threats should already be self.active_threats (passed from run method)
            # This contains all persistent threats that should remain visible
            if not current_threats:
                # No threats to display - if overlay exists, keep it visible (persistent hitboxes)
                if hasattr(self, 'overlay_window') and self.overlay_window:
                    print("No threats to display - keeping existing overlay visible")
                    return
                else:
                    print("No threats and no overlay - nothing to display")
                return
            
            print(f"Creating overlay for threats: {list(current_threats.keys())}")
            
            # Close existing overlay
            self.close_overlay()
            
            # Create new overlay window with optimizations to prevent white flash
            print(f"Creating overlay window at {screen_size[0]}x{screen_size[1]}")
            self.overlay_window = tk.Toplevel()
            
            # Set all attributes BEFORE showing window to prevent white flash
            self.overlay_window.withdraw()  # Hide immediately
            self.overlay_window.overrideredirect(True)  # Remove window decorations
            self.overlay_window.configure(bg='black')  # Black background
            self.overlay_window.attributes('-transparentcolor', 'black')  # Make black transparent
            self.overlay_window.attributes('-topmost', True)  # Always on top
            self.overlay_window.attributes('-alpha', 1.0)  # Fully opaque for colored rectangles
            self.overlay_window.wm_attributes('-disabled', True)  # Make click-through
            
            # Set geometry while hidden
            self.overlay_window.geometry(f"{screen_size[0]}x{screen_size[1]}+0+0")
            
            # Update to ensure all settings applied
            self.overlay_window.update_idletasks()
            
            # Create canvas for multiple rectangles with optimizations
            canvas = tk.Canvas(self.overlay_window, bg='black', highlightthickness=0,
                             bd=0, relief='flat')  # Remove borders for performance
            canvas.pack(fill='both', expand=True)
            
            # Draw ONE rectangle per threat (no text labels, just boxes)
            colors = ['red', 'orange', 'yellow', 'magenta', 'cyan', 'lime', 'pink']  # More colors for multiple threats
            color_index = 0
            
            for threat_text, threat_location in current_threats.items():
                color = colors[color_index % len(colors)]
                
                # Handle both list (legacy) and tuple (current) formats
                if isinstance(threat_location, list) and threat_location:
                    # If it's a list, use the first location only (one box per threat)
                    location = threat_location[0]
                elif isinstance(threat_location, tuple) and len(threat_location) == 4:
                    # Single location tuple
                    location = threat_location
                else:
                    # No valid location - skip this threat
                    print(f"Skipping '{threat_text}' - no valid location")
                    color_index += 1
                    continue
                
                if isinstance(location, tuple) and len(location) == 4:
                    x, y, w, h = location
                    # Add minimal padding around the detected text
                    padding = 5
                    box_x = max(0, x - padding)
                    box_y = max(0, y - padding)
                    box_width = min(w + (padding * 2), screen_size[0] - box_x)
                    box_height = min(h + (padding * 2), screen_size[1] - box_y)
                    
                    # Draw rectangle border ONLY (no text labels)
                    canvas.create_rectangle(box_x, box_y, box_x+box_width, box_y+box_height, 
                                          outline=color, width=2, fill='')
                    
                    print(f"Drawing hitbox for '{threat_text}' at ({box_x}, {box_y}) size {box_width}x{box_height}")
                
                color_index += 1
            
            # Show window only after everything is drawn (prevents white flash)
            self.overlay_window.deiconify()
            
            audit_log(f"Overlay created successfully with {len(current_threats)} hitbox(es) (one per threat)", 'SUCCESS')
            
        except Exception as e:
            audit_log(f"Continuous overlay error: {e}", 'ERROR')
    
    def close_overlay(self):
        """Close the detection overlay safely"""
        try:
            if hasattr(self, 'overlay_window') and self.overlay_window:
                try:
                    self.overlay_window.withdraw()  # Hide first
                    self.overlay_window.destroy()   # Then destroy
                except:
                    pass
                self.overlay_window = None
        except Exception as e:
            audit_log(f"Overlay close error (safe to ignore): {e}", 'WARNING')
        finally:
            self.overlay_window = None

# --- GUI ---
class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure CustomTkinter appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Window setup
        self.title("Securely")
        self.geometry("220x200")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color="#0d1117")  # GitHub dark theme
        
        # Set custom icon for window and taskbar
        try:
            icon_path = r"C:\Program Files\Securely-Assets\02.ico"
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
                print(f"Icon loaded: {icon_path}")
            else:
                print(f"Icon not found at: {icon_path}")
        except Exception as e:
            print(f"Could not load icon: {e}")
        
        # Remove title bar but keep in taskbar
        self.overrideredirect(True)
        
        # Force window to appear in taskbar (Windows-specific)
        try:
            # Wait a bit for window to be fully created before setting up taskbar icon
            self.after(100, lambda: self._setup_taskbar_icon())
        except Exception as e:
            print(f"Taskbar icon setup: {e}")
        
        # Handle window closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create main frame with scrollable content
        self.main_frame = ctk.CTkFrame(self, fg_color="#0d1117", corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Custom title bar with exit button
        self.title_bar = ctk.CTkFrame(self.main_frame, fg_color="#161b22", height=20)
        self.title_bar.pack(fill="x", padx=0, pady=(0, 2))
        self.title_bar.pack_propagate(False)
        
        # Add icon to title bar (left side) - circular
        try:
            icon_path = r"C:\Program Files\Securely-Assets\2.ico"
            if os.path.exists(icon_path):
                icon_img = Image.open(icon_path).convert("RGBA")
                icon_img = icon_img.resize((14, 14), Image.Resampling.LANCZOS)
                
                # Create circular mask
                mask = Image.new('L', (14, 14), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, 14, 14), fill=255)
                
                # Apply circular mask to icon
                circular_icon = Image.new('RGBA', (14, 14), (0, 0, 0, 0))
                circular_icon.paste(icon_img, (0, 0))
                circular_icon.putalpha(mask)
                
                # Keep original circular icon image for dynamic resizing
                try:
                    self._original_icon_img = circular_icon.copy()
                except Exception:
                    self._original_icon_img = circular_icon
                self.icon_photo = ImageTk.PhotoImage(circular_icon)
                self.icon_label = tk.Label(self.title_bar, image=self.icon_photo, bg="#161b22")
                self.icon_label.pack(side="left", padx=(4, 2), pady=2)
                # Allow dragging from icon
                self.icon_label.bind("<Button-1>", self.start_drag)
                self.icon_label.bind("<B1-Motion>", self.on_drag)
        except Exception as e:
            print(f"Could not load icon in title bar: {e}")
        
        # Title label
        self.title_label = ctk.CTkLabel(self.title_bar, text="Securely", 
                                       font=ctk.CTkFont(size=10, weight="bold"),
                                       text_color="#f0f6fc")
        self.title_label.pack(side="left", padx=(2, 6), pady=2)

        # Small AI status in title bar (text-only) placed to the right of the title
        try:
            # Keep only the original icon on the very left; do not duplicate it here.
            self.title_ai_icon = None

            # Start with a minimal, helpful status: prefer 'Screen secure'
            # Slightly smaller compact status for the title bar
            # Start blank until the user interacts with controls
            self.title_ai_label = ctk.CTkLabel(self.title_bar, text="",
                                               font=ctk.CTkFont(size=8),
                                               text_color="#8b949e",
                                               fg_color="transparent")
            self.title_ai_label.pack(side="left", padx=(1, 4), pady=1)
        except Exception as e:
            print(f"Could not create title-bar AI status: {e}")
        
        # Custom exit button
        self.exit_btn = ctk.CTkButton(self.title_bar, text="✕", width=18, height=16,
                                     font=ctk.CTkFont(size=11, weight="bold"),
                                     fg_color="transparent",
                                     hover_color="#d73a49",
                                     text_color="#8b949e",
                                     command=self.on_closing)
        self.exit_btn.pack(side="right", padx=2, pady=2)
        
        # Custom resizer button
        self.is_enlarged = False  # Track window size state
        self.original_size = (220, 200)  # Store original dimensions
        self.resizer_btn = ctk.CTkButton(self.title_bar, text="⛶", width=18, height=16,
                                        font=ctk.CTkFont(size=11, weight="bold"),
                                        fg_color="transparent",
                                        hover_color="#58a6ff",
                                        text_color="#8b949e",
                                        command=self.toggle_window_size)
        self.resizer_btn.pack(side="right", padx=(2, 0), pady=2)
        
        # Custom minimize button
        self.minimize_btn = ctk.CTkButton(self.title_bar, text="−", width=18, height=16,
                                         font=ctk.CTkFont(size=11, weight="bold"),
                                         fg_color="transparent",
                                         hover_color="#30363d",
                                         text_color="#8b949e",
                                         command=self.minimize_window)
        self.minimize_btn.pack(side="right", padx=(2, 0), pady=2)
        
        # Bind title bar for dragging
        self.title_bar.bind("<Button-1>", self.start_drag)
        self.title_bar.bind("<B1-Motion>", self.on_drag)
        self.title_label.bind("<Button-1>", self.start_drag)
        self.title_label.bind("<B1-Motion>", self.on_drag)
        
        # Create tab view for compact navigation
        self.tab_view = ctk.CTkTabview(self.main_frame, height=170, 
                                       fg_color="#161b22", 
                                       segmented_button_fg_color="#21262d",
                                       segmented_button_selected_color="#30363d",
                                       text_color="#f0f6fc")
        self.tab_view.pack(fill="both", expand=True)
        
        # Add tabs with compact emoji icons
        self.tab_view.add("📊")  # Dashboard
        self.tab_view.add("⚙️")  # Settings  
        self.tab_view.add("📋")  # Audit Log
        self.tab_view.add("ℹ️")  # Credits
        
        # Initialize scan duration (default: 5 minutes)
        self.scan_duration_seconds = 5 * 60
        
        self.create_dashboard_tab()
        self.create_settings_tab()
        self.create_audit_log_tab()
        self.create_credits_tab()
        
        # Add tooltips to tabs
        self.after(200, self.add_simple_tooltips)
        
        # Bind tab change event for lazy loading of audit log
        try:
            # Monitor tab changes to load audit log only when needed
            def on_tab_change(event=None):
                try:
                    current_tab = self.tab_view.get()
                    # Lazy load audit log only when tab is first accessed
                    if current_tab == "📋" and not getattr(self, '_audit_log_loaded', False):
                        # Load audit log in background to prevent UI blocking
                        self.after(50, self.load_audit_log)
                except Exception:
                    pass
            
            # Bind to tab view changes (check periodically since CTkTabview doesn't have direct event)
            def check_tab_change():
                try:
                    current_tab = self.tab_view.get()
                    if current_tab == "📋" and not getattr(self, '_audit_log_loaded', False):
                        self.after(50, self.load_audit_log)
                except Exception:
                    pass
                # Check every 100ms for tab changes
                self.after(100, check_tab_change)
            
            # Start checking for tab changes
            self.after(100, check_tab_change)
        except Exception:
            pass
        
        # Monitor setup - DON'T start monitoring until user clicks "On"
        self.monitor = ScreenMonitor(interval=1)  # 1-second scan interval
        self.monitor.notifications_enabled = True
        self.monitor.sound_enabled = False
        self.monitor.strict_mode = False
        self.monitor.hitboxes_enabled = False
        self.monitor.test_mode = False
        self.monitor.main_window = self
        # Expose the main window globally so background threads can schedule UI updates
        try:
            globals()['APP_MAIN_WINDOW'] = self
        except Exception:
            pass
        # DO NOT start monitor here - wait for user to click "On" button
        
        # Load saved API key
        # self.load_api_key()  # Removed API key loading
        
        # Position window at left center of screen (small left margin)
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # Use a small margin from the left edge so the window isn't flush against the border
        left_margin = 20
        x = left_margin
        y = (screen_height - 220) // 2
        self.geometry(f"220x200+{x}+{y}")
        
        # Store the actual window size after positioning
        self.update_idletasks()
        self.original_size = (220, 200)
    
    def _setup_taskbar_icon(self):
        """Setup window to appear in taskbar"""
        try:
            import ctypes
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if hwnd:
                # Get current style
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                # Remove TOOLWINDOW flag (which hides from taskbar) and ensure APPWINDOW flag is set
                style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
                # Force window refresh
                ctypes.windll.user32.ShowWindow(hwnd, 4)  # SW_SHOWNOACTIVATE
        except Exception as e:
            audit_log(f"Taskbar icon setup error: {e}", 'ERROR')
        
    def update_ai_status(self, status):
        """Update AI status display on dashboard"""
        try:
            if hasattr(self, 'ai_status_label'):
                self.ai_status_label.configure(text=status)
            # Also update compact title-bar AI status if present, but simplify the wording
            if hasattr(self, 'title_ai_label'):
                try:
                    lower = (status or "").lower()
                    title_text = ""
                    title_color = "#8b949e"

                    # Prefer short, clear labels for the title bar
                    if 'screen secure' in lower or status.startswith('✅'):
                        title_text = "Screen secure"
                        title_color = "#28a745"
                    elif 'analys' in lower or 'analysis' in lower or 'progress' in lower or 'ai' in lower:
                        title_text = "AI analysing..."
                        # Make analysing appear green per user request
                        title_color = "#28a745"
                    elif 'threat' in lower or '⚠' in status or 'detected' in lower:
                        title_text = "Threat detected"
                        title_color = "#d73a49"
                    else:
                        # Hide trivial/verbose messages like 'monitoring paused' from the compact area
                        title_text = ""
                        title_color = "#8b949e"

                    # Update compact title-bar label
                    try:
                        self.title_ai_label.configure(text=title_text, text_color=title_color)
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass
        
    def create_dashboard_tab(self):
        dashboard = self.tab_view.tab("📊")
        
        # Status label with darker background - Start in disabled state
        self.status_label = ctk.CTkLabel(dashboard, text="● Disabled", 
                                        fg_color="#21262d", corner_radius=6,
                                        text_color="#8b949e",
                                        font=ctk.CTkFont(size=11, weight="bold"))
        self.status_label.pack(pady=(4, 4), padx=6, fill="x")
        
        # AI Status label removed from dashboard (compact title-bar status is used instead)
        # self.ai_status_label = ctk.CTkLabel(dashboard, text="⏸️ Monitoring paused",
        #                                    fg_color="#161b22", corner_radius=4,
        #                                    text_color="#8b949e",
        #                                    font=ctk.CTkFont(size=9))
        # self.ai_status_label.pack(pady=(0, 4), padx=6, fill="x")
        
        # Control buttons frame - centered
        buttons_frame = ctk.CTkFrame(dashboard, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=4, padx=6)
        
        # Set default target to Entire Screen
        self.selected_target = ('screen', None, 'Entire Screen')

        # First row: Quick Scan and Scan for 15m buttons
        top_row_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        top_row_frame.pack(anchor="center", pady=(0, 2))
        
        # Scan once button
        self.temp_disable_btn = ctk.CTkButton(top_row_frame, text="Quick Scan", width=60, height=24,
                    font=ctk.CTkFont(size=10),
                    fg_color="#d73a49",
                    hover_color="#cb2431",
                    text_color="#ffffff",
                command=self._quick_scan_click)
        self.temp_disable_btn.pack(side="left", padx=(0, 4), pady=4, anchor="center")
        # store base metrics for reliable scaling
        try:
            self.temp_disable_btn._base_width = 60
            self.temp_disable_btn._base_height = 24
            self.temp_disable_btn._base_font = 10
        except Exception:
            pass

        # Short-duration scan button (runs scanning for a few seconds)
        # Get initial button text based on scan duration
        duration_seconds = getattr(self, 'scan_duration_seconds', 5 * 60)
        if duration_seconds == 1 * 60:
            initial_text = "Scan for 1m"
        elif duration_seconds == 5 * 60:
            initial_text = "Scan for 5m"
        elif duration_seconds == 10 * 60:
            initial_text = "Scan for 10m"
        elif duration_seconds == 15 * 60:
            initial_text = "Scan for 15m"
        elif duration_seconds == 30 * 60:
            initial_text = "Scan for 30m"
        elif duration_seconds == 60 * 60:
            initial_text = "Scan for 1h"
        else:
            minutes = duration_seconds // 60
            initial_text = f"Scan for {minutes}m"
        self.short_scan_btn = ctk.CTkButton(top_row_frame, text=initial_text, width=80, height=24,
                            font=ctk.CTkFont(size=10),
                            fg_color="#0969da",
                            hover_color="#0860ca",
                            text_color="#ffffff",
                    command=self._short_scan_click)
        self.short_scan_btn.pack(side="left", padx=(4, 0), pady=4, anchor="center")
        try:
            self.short_scan_btn._base_width = 80
            self.short_scan_btn._base_height = 24
            self.short_scan_btn._base_font = 10
        except Exception:
            pass
        
        # Second row: Toggle 24/7 Monitoring button
        bottom_row_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        bottom_row_frame.pack(anchor="center")
        
        # Program toggle button (Off/On) - Start in OFF state
        self.program_enabled = False
        self.program_toggle_btn = ctk.CTkButton(bottom_row_frame, text="Toggle 24/7 Monitoring", width=140, height=24,
                              font=ctk.CTkFont(size=10),
                              fg_color="#28a745",  # Green for ON
                              hover_color="#218838",
                              text_color="#ffffff",
                      command=self._program_toggle_click)
        self.program_toggle_btn.pack(pady=4, anchor="center")
        try:
            self.program_toggle_btn._base_width = 140
            self.program_toggle_btn._base_height = 24
            self.program_toggle_btn._base_font = 10
        except Exception:
            pass
        # Create (hidden) in-app confirmation page for enabling continuous monitoring
        self.monitor_confirm_frame = ctk.CTkFrame(self.main_frame, fg_color="#0d1117")
        
        # Confirmation header as a label with proper wrapping
        confirm_header = ctk.CTkLabel(self.monitor_confirm_frame, text="Enable Continuous Monitoring?",
                           font=ctk.CTkFont(size=11, weight="bold"), text_color="#f0f6fc",
                           wraplength=380, justify="center")
        confirm_header.pack(pady=(10, 6), padx=12)

        # Update wraplength dynamically based on window width
        def _update_header_wrap(event=None):
            try:
                win_w = self.winfo_width() if hasattr(self, 'winfo_width') else 380
                width = max(160, win_w - 48)
                confirm_header.configure(wraplength=width)
            except Exception:
                pass

        try:
            self.monitor_confirm_frame.bind('<Configure>', _update_header_wrap)
            self.bind('<Configure>', _update_header_wrap)
            self.after(100, _update_header_wrap)
        except Exception:
            pass

        confirm_text = (
            "Be aware, enabling continuous monitoring means Securely will actively monitor "
            "and analyze absolutely everything displayed on your screen 24/7. The AI will continuously "
            "capture and process your screen content in real-time to detect security threats, phishing attempts, "
            "malicious content, and other potential dangers. This includes all applications, websites, emails, "
            "messages, and any other content visible on your display. Make sure you are completely comfortable "
            "with this level of monitoring and understand that Securely will have full visibility into your "
            "screen activity before enabling this feature."
        )

        # Use textbox instead of label for better text wrapping
        confirm_textbox = ctk.CTkTextbox(self.monitor_confirm_frame, height=65, wrap="word",
                                        fg_color="#161b22",
                                        text_color="#8b949e",
                                        font=ctk.CTkFont(size=11),
                                        border_width=1,
                                        border_color="#30363d")
        confirm_textbox.pack(fill="x", padx=12, pady=(6, 6))
        confirm_textbox.insert("1.0", confirm_text)
        confirm_textbox.configure(state="disabled")

        # Footer area: place buttons directly under the confirmation text (centered)
        footer_frame = ctk.CTkFrame(self.monitor_confirm_frame, fg_color="transparent")
        footer_frame.pack(fill="x", padx=12, pady=(6, 8))

        # Buttons frame inside footer: use a full-width container and center an inner frame
        confirm_btn_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        confirm_btn_frame.pack(fill="x", pady=4)

        # Inner centering frame so buttons are centered horizontally
        btn_center = ctk.CTkFrame(confirm_btn_frame, fg_color="transparent")
        btn_center.pack(anchor="center")

        # Enable button (slightly narrower so it fits compact windows)
        self._enable_monitor_btn = ctk.CTkButton(btn_center, text="Enable",
                              fg_color="#28a745", hover_color="#218838", width=100,
                              command=self._confirm_enable_monitor)
        self._enable_monitor_btn.pack(side="left", padx=8)

        # Cancel button (go back)
        cancel_btn = ctk.CTkButton(btn_center, text="Cancel",
                       fg_color="#6e40aa", hover_color="#8b5cf6", width=90,
                       command=self.hide_monitor_confirm_page)
        cancel_btn.pack(side="left", padx=8)
        
    # --- Target selection helpers ---
    def open_target_selector(self):
        """Open a small dialog allowing the user to pick an application window or the entire screen."""
        # Enumerate top-level visible windows (Windows-only). Fall back to screen-only option if unavailable.
        windows = []
        try:
            import ctypes
            user32 = ctypes.windll.user32
            EnumWindows = user32.EnumWindows
            GetWindowTextW = user32.GetWindowTextW
            GetWindowTextLengthW = user32.GetWindowTextLengthW
            IsWindowVisible = user32.IsWindowVisible

            titles = []
            EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

            @EnumProc
            def _enum(hwnd, lParam):
                try:
                    if IsWindowVisible(hwnd):
                        length = GetWindowTextLengthW(hwnd)
                        if length > 0:
                            buf = ctypes.create_unicode_buffer(length + 1)
                            GetWindowTextW(hwnd, buf, length + 1)
                            title = buf.value
                            if title and title.strip():
                                titles.append((int(hwnd), title))
                except Exception:
                    pass
                return True

            EnumWindows(_enum, 0)
            windows = titles
        except Exception:
            windows = []

        # Always allow Entire Screen as first option
        options = [(None, "Entire Screen")] + windows
        self._show_target_dialog(options)

    def _show_target_dialog(self, options):
        dlg = ctk.CTkToplevel()
        dlg.title("Select Target")
        dlg.geometry("520x320")
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text="Choose a window to target or select Entire Screen:", bg="#0d1117", fg="#c9d1d9").pack(anchor='w', padx=12, pady=(8,4))

        list_frame = tk.Frame(dlg, bg="#0d1117")
        list_frame.pack(fill='both', expand=True, padx=12, pady=(0,8))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        lb = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, bg='#0d1117', fg='#c9d1d9', selectbackground='#30363d')
        for idx, (hwnd, title) in enumerate(options):
            display = title if hwnd is None else f"{title}"
            lb.insert('end', display)
        lb.pack(fill='both', expand=True)
        scrollbar.config(command=lb.yview)

        def on_ok():
            sel = lb.curselection()
            if not sel:
                messagebox.showwarning('Select Target', 'Please select a target or Cancel.')
                return
            index = sel[0]
            hwnd, title = options[index]
            self._set_selected_target(hwnd, title)
            dlg.destroy()

        btns = tk.Frame(dlg, bg="#0d1117")
        btns.pack(pady=(0,8))
        ok = ctk.CTkButton(btns, text="OK", width=80, command=on_ok)
        ok.pack(side='left', padx=8)
        cancel = ctk.CTkButton(btns, text="Cancel", width=80, command=dlg.destroy)
        cancel.pack(side='left', padx=8)

    def _set_selected_target(self, hwnd, title):
        """Store the selected target and update UI; enable scan controls."""
        if hwnd is None:
            self.selected_target = ('screen', None, 'Entire Screen')
            label = 'Entire Screen'
        else:
            self.selected_target = ('window', hwnd, title)

    def _quick_scan_click(self):
        # call existing handler
        try:
            self.on_temp_disable()
        except Exception:
            pass

    def _short_scan_click(self):
        try:
            self.on_scan_short()
        except Exception:
            pass
    
    def get_scan_button_text(self):
        """Get the button text based on current scan duration"""
        duration_seconds = getattr(self, 'scan_duration_seconds', 5 * 60)
        if duration_seconds == 1 * 60:
            return "Scan for 1m"
        elif duration_seconds == 5 * 60:
            return "Scan for 5m"
        elif duration_seconds == 10 * 60:
            return "Scan for 10m"
        elif duration_seconds == 15 * 60:
            return "Scan for 15m"
        elif duration_seconds == 30 * 60:
            return "Scan for 30m"
        elif duration_seconds == 60 * 60:
            return "Scan for 1h"
        else:
            # Fallback: calculate minutes
            minutes = duration_seconds // 60
            return f"Scan for {minutes}m"
    
    def on_scan_duration_changed(self, choice):
        """Callback when scan duration dropdown changes"""
        try:
            # Update the duration in seconds
            if choice in self.scan_duration_map:
                self.scan_duration_seconds = self.scan_duration_map[choice]
                
                # Update button text if scan is not currently active
                if hasattr(self, 'short_scan_btn'):
                    current_text = self.short_scan_btn.cget('text')
                    # Only update if button is not in "Stop Scan" state
                    if current_text != "Stop Scan":
                        new_text = self.get_scan_button_text()
                        self.short_scan_btn.configure(text=new_text)
                        print(f"Scan duration changed to {choice} ({self.scan_duration_seconds}s)")
        except Exception as e:
            audit_log(f"Error updating scan duration: {e}", 'ERROR')

    def _program_toggle_click(self):
        try:
            self.on_program_toggle()
        except Exception:
            pass

    def create_settings_tab(self):
        settings = self.tab_view.tab("⚙️")
        
        # Create scrollable frame for settings with dark styling
        settings_scroll = ctk.CTkScrollableFrame(settings, fg_color="#0d1117",
                                               scrollbar_button_color="#30363d")
        settings_scroll.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Hitboxes toggle (larger label, tighter spacing)
        self.hitboxes_var = ctk.BooleanVar(value=False)
        self.hitboxes_toggle = ctk.CTkCheckBox(settings_scroll, text="Hitboxes",
                             variable=self.hitboxes_var,
                             command=self.on_hitboxes_toggled,
                             font=ctk.CTkFont(size=12),
                             text_color="#f0f6fc",
                             fg_color="#1f6feb",
                             hover_color="#58a6ff")
        self.hitboxes_toggle.pack(anchor="w", pady=2)
        
        # Monitoring toggle is intentionally hidden from Settings UI.
        # Keep the variable for programmatic control and backward compatibility.
        self.monitoring_var = ctk.BooleanVar(value=True)
        
        # More Strict toggle
        self.strict_mode_var = ctk.BooleanVar(value=False)
        self.strict_mode_toggle = ctk.CTkCheckBox(settings_scroll, text="More Strict",
                            variable=self.strict_mode_var,
                            command=self.on_strict_mode_toggled,
                            font=ctk.CTkFont(size=12),
                            text_color="#f0f6fc",
                            fg_color="#1f6feb",
                            hover_color="#58a6ff")
        self.strict_mode_toggle.pack(anchor="w", pady=2)
        
        # Notifications toggle  
        self.notifications_var = ctk.BooleanVar(value=True)
        self.notifications_toggle = ctk.CTkCheckBox(settings_scroll, text="Notifications",
                              variable=self.notifications_var,
                              command=self.on_notifications_toggled,
                              font=ctk.CTkFont(size=12),
                              text_color="#f0f6fc",
                              fg_color="#1f6feb",
                              hover_color="#58a6ff")
        self.notifications_toggle.pack(anchor="w", pady=2)
        
        # Sound toggle
        self.sound_var = ctk.BooleanVar(value=False)
        self.sound_toggle = ctk.CTkCheckBox(settings_scroll, text="Sound",
                          variable=self.sound_var,
                          command=self.on_sound_toggled,
                          font=ctk.CTkFont(size=12),
                          text_color="#f0f6fc",
                          fg_color="#1f6feb",
                          hover_color="#58a6ff")
        self.sound_toggle.pack(anchor="w", pady=2)
        
        # Test notification button
        test_notification_btn = ctk.CTkButton(settings_scroll, text="🚨 Test Notification",
                                            height=20, width=130,
                                            font=ctk.CTkFont(size=11),
                                            fg_color="#238636",
                                            hover_color="#2ea043",
                                            command=self.test_notification)
        test_notification_btn.pack(anchor="w", pady=(5, 3))
        try:
            test_notification_btn._base_width = 130
            test_notification_btn._base_height = 20
            test_notification_btn._base_font = 11
            self.test_notification_btn = test_notification_btn
        except Exception:
            pass
        
        # Divider before Advanced Section
        divider_advanced = ctk.CTkFrame(settings_scroll, height=1, fg_color="#30363d")
        divider_advanced.pack(fill="x", pady=(10, 5))
        
        # Advanced Section label
        advanced_label = ctk.CTkLabel(settings_scroll, text="⚙️ Advanced",
                                     font=ctk.CTkFont(size=11, weight="bold"),
                                     text_color="#8b949e")
        advanced_label.pack(anchor="w", pady=(5, 8))
        
        # Scan Duration dropdown
        scan_duration_frame = ctk.CTkFrame(settings_scroll, fg_color="transparent")
        scan_duration_frame.pack(anchor="w", pady=(0, 8), fill="x")
        
        scan_duration_label = ctk.CTkLabel(scan_duration_frame, text="Temporary Scan Duration:",
                                          font=ctk.CTkFont(size=11),
                                          text_color="#f0f6fc")
        scan_duration_label.pack(side="left", padx=(0, 8))
        
        # Duration options: (display_text, seconds)
        duration_options = [
            ("1 Minute", 1 * 60),
            ("5 Minutes", 5 * 60),
            ("10 Minutes", 10 * 60),
            ("15 Minutes", 15 * 60),
            ("30 Minutes", 30 * 60),
            ("1 Hour", 60 * 60)
        ]
        
        # Find current selection index
        current_index = 1  # Default to 5 minutes
        for i, (_, seconds) in enumerate(duration_options):
            if seconds == self.scan_duration_seconds:
                current_index = i
                break
        
        self.scan_duration_var = ctk.StringVar(value=duration_options[current_index][0])
        self.scan_duration_dropdown = ctk.CTkComboBox(scan_duration_frame,
                                                      values=[opt[0] for opt in duration_options],
                                                      variable=self.scan_duration_var,
                                                      command=self.on_scan_duration_changed,
                                                      width=120,
                                                      height=24,
                                                      font=ctk.CTkFont(size=11),
                                                      fg_color="#21262d",
                                                      button_color="#30363d",
                                                      button_hover_color="#424549",
                                                      text_color="#f0f6fc",
                                                      dropdown_fg_color="#161b22",
                                                      dropdown_text_color="#f0f6fc",
                                                      dropdown_hover_color="#30363d")
        self.scan_duration_dropdown.pack(side="left")
        
        # Store duration mapping for easy lookup
        self.scan_duration_map = {opt[0]: opt[1] for opt in duration_options}
        
        # Test Mode toggle for debugging
        self.test_mode_var = ctk.BooleanVar(value=False)
        self.test_mode_toggle = ctk.CTkCheckBox(settings_scroll, text="Test Mode",
                              variable=self.test_mode_var,
                              command=self.on_test_mode_toggled,
                              font=ctk.CTkFont(size=12),
                              text_color="#f0f6fc",
                              fg_color="#1f6feb",
                              hover_color="#58a6ff")
        self.test_mode_toggle.pack(anchor="w", pady=2)
        
        # Console viewer button
        console_viewer_btn = ctk.CTkButton(settings_scroll, text="🖥️ View Console Log",
                                          height=20, width=130,
                                          font=ctk.CTkFont(size=11),
                                          fg_color="#6e40aa",
                                          hover_color="#8b5cf6",
                                          command=self.open_console_viewer)
        console_viewer_btn.pack(anchor="w", pady=(5, 3))
        try:
            console_viewer_btn._base_width = 130
            console_viewer_btn._base_height = 20
            console_viewer_btn._base_font = 11
            self.console_viewer_btn = console_viewer_btn
        except Exception:
            pass
        
    def create_audit_log_tab(self):
        audit_log = self.tab_view.tab("📋")
        
        # Header with buttons
        header_frame = ctk.CTkFrame(audit_log, fg_color="transparent")
        header_frame.pack(fill="x", pady=(4, 4), padx=4)
        
        # Quick Scan button on the left: perform a single immediate scan (same as Dashboard 'Scan Once')
        # Make these accessible for dynamic scaling
        self.quick_scan_btn = ctk.CTkButton(header_frame, text="Quick Scan",
                height=20, width=100,
                font=ctk.CTkFont(size=9, weight="bold"),
                    fg_color="#d73a49",
                    hover_color="#cb2431",
                    text_color="#ffffff",
                    command=self.on_temp_disable)
        self.quick_scan_btn.pack(side="left", padx=5)
        try:
            self.quick_scan_btn._base_width = 100
            self.quick_scan_btn._base_height = 20
            self.quick_scan_btn._base_font = 9
        except Exception:
            pass
        
        # Clear Log button on the right
        self.clear_btn = ctk.CTkButton(header_frame, text="Clear Log", height=20, width=80,
                     font=ctk.CTkFont(size=8, weight="bold"),
                                 fg_color="#d73a49",
                                 hover_color="#cb2431",
                                 text_color="#ffffff",
                                 command=self.clear_audit_log)
        self.clear_btn.pack(side="right", padx=5)
        try:
            self.clear_btn._base_width = 80
            self.clear_btn._base_height = 20
            self.clear_btn._base_font = 8
        except Exception:
            pass
        
        # Scrollable audit log frame for threat cards
        self.audit_frame = ctk.CTkScrollableFrame(audit_log, fg_color="#0d1117",
                                                 scrollbar_button_color="#30363d",
                                                 scrollbar_button_hover_color="#424549")
        self.audit_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        
        # Store threat cards for dynamic updates
        self.threat_cards = []
        self._audit_log_loaded = False  # Track if audit log has been loaded
        
        # Don't load immediately - use lazy loading when tab is first accessed
        # This prevents heavy operations during initialization
        # Note: audit log will only auto-refresh while monitoring is active. See `on_program_toggle`.
        
    def refresh_audit_log(self):
        # Only refresh if audit tab is currently visible AND monitor is running
        try:
            monitor_running = False
            if hasattr(self, 'monitor') and self.monitor:
                monitor_running = bool(getattr(self.monitor, 'running', threading.Event()).is_set())

            if monitor_running and self.tab_view.get() == "📋":
                self.load_audit_log()
                # Schedule next refresh only while monitor is running
                self.after(3000, self.refresh_audit_log)
        except Exception:
            # Fail silently - do not keep scheduling refreshes when monitor is off or on error
            pass
    
    def show_training_analysis(self, training_id):
        """Show detailed training analysis window"""
        try:
            # Get training data from the global storage
            if not hasattr(log_event, 'training_storage') or training_id not in log_event.training_storage:
                messagebox.showwarning("Training", "Training data not found for this entry.")
                return
            
            training_data = log_event.training_storage[training_id]
            
            # Create professional training analysis window
            training_window = ctk.CTkToplevel(self)
            training_window.title("Securely - AI Cybersecurity Analysis")
            training_window.geometry("800x600")
            training_window.configure(fg_color="#0d1117")
            training_window.attributes("-topmost", True)
            training_window.resizable(True, True)
            
            # Professional header frame
            header_frame = ctk.CTkFrame(training_window, fg_color="#161b22", height=60)
            header_frame.pack(fill="x", padx=0, pady=0)
            header_frame.pack_propagate(False)
            
            # Professional title with icon
            title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
            title_container.pack(expand=True, fill="both", padx=20, pady=15)
            
            title_label = ctk.CTkLabel(title_container, 
                                     text="🛡️ AI Cybersecurity Analysis",
                                     font=ctk.CTkFont(size=18, weight="bold"),
                                     text_color="#58a6ff")
            title_label.pack(side="left")
            
            # Threat type badge
            threat_badge = ctk.CTkLabel(title_container,
                                      text=f"⚠️ {training_data['threat_type']}",
                                      font=ctk.CTkFont(size=12, weight="bold"),
                                      text_color="#ffffff",
                                      fg_color="#d73a49",
                                      corner_radius=15)
            threat_badge.pack(side="right", padx=(10, 0))
            
            # Main content frame with scrolling
            main_frame = ctk.CTkScrollableFrame(training_window, fg_color="#0d1117",
                                              scrollbar_button_color="#30363d",
                                              scrollbar_button_hover_color="#484f58")
            main_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
            
            # Professional screenshot section
            screenshot_section = ctk.CTkFrame(main_frame, fg_color="#161b22", corner_radius=10)
            screenshot_section.pack(fill="x", pady=(10, 15), padx=10)
            
            screenshot_header = ctk.CTkLabel(screenshot_section, 
                                           text="📸 Captured Screen Content",
                                           font=ctk.CTkFont(size=13, weight="bold"),
                                           text_color="#f0f6fc")
            screenshot_header.pack(pady=(15, 10))
            
            # Screenshot display with border
            try:
                if os.path.exists(training_data['screenshot_path']):
                    screenshot = Image.open(training_data['screenshot_path'])
                    # Enhanced resize with better quality
                    screenshot.thumbnail((700, 350), Image.Resampling.LANCZOS)
                    
                    # Add subtle border to screenshot
                    bordered_screenshot = Image.new('RGB', 
                                                   (screenshot.width + 4, screenshot.height + 4), 
                                                   '#30363d')
                    bordered_screenshot.paste(screenshot, (2, 2))
                    
                    screenshot_photo = ctk.CTkImage(light_image=bordered_screenshot, 
                                                   size=(bordered_screenshot.width, bordered_screenshot.height))
                    
                    screenshot_label = ctk.CTkLabel(screenshot_section, image=screenshot_photo, text="")
                    screenshot_label.pack(pady=(0, 15))
                else:
                    error_label = ctk.CTkLabel(screenshot_section, 
                                             text="⚠️ Screenshot not available",
                                             font=ctk.CTkFont(size=12),
                                             text_color="#d73a49")
                    error_label.pack(pady=15)
            except Exception as e:
                error_label = ctk.CTkLabel(screenshot_section, 
                                         text=f"⚠️ Screenshot error: {e}",
                                         font=ctk.CTkFont(size=12),
                                         text_color="#d73a49")
                error_label.pack(pady=15)
            
            # Professional AI analysis section
            analysis_section = ctk.CTkFrame(main_frame, fg_color="#161b22", corner_radius=10)
            analysis_section.pack(fill="both", expand=True, pady=(0, 10), padx=10)
            
            # Analysis header with professional styling
            analysis_header_frame = ctk.CTkFrame(analysis_section, fg_color="#21262d", height=50)
            analysis_header_frame.pack(fill="x", padx=15, pady=(15, 0))
            analysis_header_frame.pack_propagate(False)
            
            analysis_icon = ctk.CTkLabel(analysis_header_frame, text="🤖",
                                       font=ctk.CTkFont(size=20))
            analysis_icon.pack(side="left", padx=(15, 10), pady=12)
            
            analysis_title = ctk.CTkLabel(analysis_header_frame, 
                                        text="AI Security Analysis",
                                        font=ctk.CTkFont(size=14, weight="bold"),
                                        text_color="#58a6ff")
            analysis_title.pack(side="left", pady=12)
            
            # Professional loading indicator
            loading_frame = ctk.CTkFrame(analysis_section, fg_color="transparent")
            loading_frame.pack(fill="x", padx=15, pady=10)
            
            loading_label = ctk.CTkLabel(loading_frame, 
                                       text="⏳ Analyzing threat data with advanced AI...",
                                       font=ctk.CTkFont(size=12),
                                       text_color="#8b949e")
            loading_label.pack()
            
            # Enhanced analysis text area - larger for more detailed output
            self.analysis_text = ctk.CTkTextbox(analysis_section, height=400,
                                              fg_color="#0d1117",
                                              text_color="#f0f6fc",
                                              font=ctk.CTkFont(size=10, family="Consolas"),
                                              border_width=2,
                                              border_color="#30363d",
                                              corner_radius=8,
                                              wrap="word")
            self.analysis_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
            
            # Professional loading message
            loading_message = """🔍 INITIATING CYBERSECURITY ANALYSIS...

⚡ Scanning screenshot for security threats
🧠 Processing with advanced AI algorithms  
🛡️ Generating comprehensive threat assessment
📋 Preparing detailed security recommendations

Please wait while our AI analyzes the captured content..."""
            
            self.analysis_text.insert("1.0", loading_message)
            
            # Optimized analysis execution
            def run_analysis():
                try:
                    # Update status
                    training_window.after(0, lambda: loading_label.configure(
                        text="🔍 AI analysis in progress..."
                    ))
                    
                    # Run AI analysis
                    analysis = analyze_screenshot_for_training(
                        training_data['screenshot_path'],
                        training_data['text_content']
                    )
                    
                    # Update UI with results
                    training_window.after(0, lambda: self.update_analysis_text(analysis))
                    training_window.after(0, lambda: loading_label.configure(
                        text="✅ Analysis complete"
                    ))
                    
                except Exception as e:
                    error_msg = f"❌ ANALYSIS ERROR\n\nFailed to analyze screenshot: {str(e)}\n\nThis could be due to:\n• No API key configured\n• Network connectivity issues\n• Invalid screenshot file\n• AI service unavailable"
                    training_window.after(0, lambda: self.update_analysis_text(error_msg))
                    training_window.after(0, lambda: loading_label.configure(
                        text="❌ Analysis failed"
                    ))
            
            # Start high-priority analysis thread
            analysis_thread = threading.Thread(target=run_analysis, daemon=True, name="AI_Analysis")
            analysis_thread.start()
            
        except Exception as e:
            messagebox.showerror("Training Error", f"Failed to show training analysis: {e}")
    
    def switch_to_audit_with_analysis(self, threat_description, detected_text):
        """Switch to Security Audit tab and show analysis window"""
        try:
            # Switch to Security Audit tab
            self.tab_view.set("📋")
            
            # Show analysis window
            self.handle_notification_click(threat_description, detected_text)
            
        except Exception as e:
            audit_log(f"Switch to audit error: {e}", 'ERROR')
    
    def switch_to_audit_with_analysis(self, threat_description, detected_text):
        """Switch to Security Audit tab and show analysis window"""
        try:
            # Switch to Security Audit tab
            self.tab_view.set("📋")
            
            # Show analysis window
            self.handle_notification_click(threat_description, detected_text)
            
        except Exception as e:
            audit_log(f"Switch to audit error: {e}", 'ERROR')
    
    def handle_notification_click(self, threat_description, detected_text):
        """Handle notification click with immediate screenshot and AI analysis"""
        try:
            # Capture screenshot immediately
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = "instant_analysis"
            
            # Create directory if it doesn't exist
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            
            # Capture current screen - PRIMARY MONITOR ONLY
            with mss.mss() as sct:
                primary_monitor = get_primary_monitor(sct)
                screenshot = sct.grab(primary_monitor)  # Primary monitor only
                screenshot_path = os.path.join(screenshot_dir, f"instant_{timestamp}.png")
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=screenshot_path)
            
            # Show instant analysis window
            self.show_instant_analysis(screenshot_path, threat_description, detected_text)
            
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Failed to capture screenshot: {e}")
    
    def show_instant_analysis(self, screenshot_path, threat_description, detected_text):
        """Show immediate AI analysis window with screenshot and detailed explanation"""
        try:
            # Create instant analysis window
            analysis_window = ctk.CTkToplevel(self)
            analysis_window.title("🛡️ Securely - Security Audit Analysis")
            analysis_window.geometry("800x600")
            analysis_window.configure(fg_color="#0d1117")
            analysis_window.attributes("-topmost", True)
            analysis_window.resizable(True, True)
            
            # Professional header
            header_frame = ctk.CTkFrame(analysis_window, fg_color="#161b22", height=55)
            header_frame.pack(fill="x", padx=0, pady=0)
            header_frame.pack_propagate(False)
            
            header_container = ctk.CTkFrame(header_frame, fg_color="transparent")
            header_container.pack(expand=True, fill="both", padx=15, pady=8)
            
            title_label = ctk.CTkLabel(header_container, 
                                     text="🛡️ SECURITY AUDIT ANALYSIS",
                                     font=ctk.CTkFont(size=16, weight="bold"),
                                     text_color="#58a6ff")
            title_label.pack(side="left")
            
            status_badge = ctk.CTkLabel(header_container,
                                      text="🔍 ANALYZING THREAT...",
                                      font=ctk.CTkFont(size=11, weight="bold"),
                                      text_color="#ffffff",
                                      fg_color="#d73a49",
                                      corner_radius=12)
            status_badge.pack(side="right", padx=(10, 0))
            
            # Content frame with scrolling
            content_frame = ctk.CTkScrollableFrame(analysis_window, fg_color="#0d1117")
            content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
            
            # Threat Detection Summary
            summary_frame = ctk.CTkFrame(content_frame, fg_color="#21262d", corner_radius=10)
            summary_frame.pack(fill="x", pady=(10, 10), padx=10)
            
            summary_header = ctk.CTkLabel(summary_frame, 
                                         text="⚠️ Threat Detection Summary",
                                         font=ctk.CTkFont(size=13, weight="bold"),
                                         text_color="#ff6b35")
            summary_header.pack(pady=(15, 10), padx=15, anchor="w")
            
            threat_label = ctk.CTkLabel(summary_frame,
                                       text=f"Detected Issue: {threat_description.upper()}",
                                       font=ctk.CTkFont(size=13, weight="bold"),
                                       text_color="#f0f6fc",
                                       anchor="w")
            threat_label.pack(pady=(0, 5), padx=15, anchor="w")
            
            detected_label = ctk.CTkLabel(summary_frame,
                                         text=f"Detected Text: {detected_text[:150]}...",
                                         font=ctk.CTkFont(size=11),
                                         text_color="#8b949e",
                                         anchor="w",
                                         wraplength=1100)
            detected_label.pack(pady=(0, 15), padx=15, anchor="w")
            
            # Screenshot section
            screenshot_frame = ctk.CTkFrame(content_frame, fg_color="#161b22", corner_radius=10)
            screenshot_frame.pack(fill="both", expand=True, pady=(10, 10), padx=10)
            
            screenshot_header = ctk.CTkLabel(screenshot_frame, 
                                           text="📸 Screen Capture at Detection Time",
                                           font=ctk.CTkFont(size=12, weight="bold"),
                                           text_color="#f0f6fc")
            screenshot_header.pack(pady=(15, 10))
            
            # Display screenshot
            try:
                if os.path.exists(screenshot_path):
                    screenshot = Image.open(screenshot_path)
                    screenshot.thumbnail((700, 300), Image.Resampling.LANCZOS)
                    
                    # Add border
                    bordered_screenshot = Image.new('RGB', 
                                                   (screenshot.width + 4, screenshot.height + 4), 
                                                   '#30363d')
                    bordered_screenshot.paste(screenshot, (2, 2))
                    
                    screenshot_photo = ctk.CTkImage(light_image=bordered_screenshot, 
                                                   size=(bordered_screenshot.width, bordered_screenshot.height))
                    
                    screenshot_label = ctk.CTkLabel(screenshot_frame, image=screenshot_photo, text="")
                    screenshot_label.pack(pady=(0, 10))
            except Exception as e:
                error_label = ctk.CTkLabel(screenshot_frame, 
                                         text=f"Screenshot error: {e}",
                                         text_color="#d73a49")
                error_label.pack(pady=10)
            
            # Analysis section
            analysis_frame = ctk.CTkFrame(content_frame, fg_color="#161b22", corner_radius=10)
            analysis_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
            
            analysis_header = ctk.CTkLabel(analysis_frame, 
                                         text="🤖 AI Security Assessment",
                                         font=ctk.CTkFont(size=13, weight="bold"),
                                         text_color="#58a6ff")
            analysis_header.pack(pady=(15, 10))
            
            # Analysis text area - larger for more detailed output
            self.instant_analysis_text = ctk.CTkTextbox(analysis_frame, height=350,
                                                       fg_color="#0d1117",
                                                       text_color="#f0f6fc",
                                                       font=ctk.CTkFont(size=10, family="Consolas"),
                                                       border_width=2,
                                                       border_color="#30363d",
                                                       wrap="word")
            self.instant_analysis_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
            
            # Loading message
            loading_msg = """🚀 INSTANT ANALYSIS IN PROGRESS...

🔍 Analyzing current screen content
🧠 Processing with advanced AI
⚡ Generating real-time assessment
🛡️ Evaluating security implications

Analyzing what you're currently seeing..."""
            
            self.instant_analysis_text.insert("1.0", loading_msg)
            
            # Start immediate analysis
            def run_instant_analysis():
                try:
                    # Update status
                    analysis_window.after(0, lambda: status_badge.configure(text="🔥 ANALYZING"))
                    
                    # Run enhanced AI analysis
                    analysis = self.analyze_current_screen(screenshot_path, detected_text)
                    
                    # Update results
                    analysis_window.after(0, lambda: self.update_instant_analysis(analysis))
                    analysis_window.after(0, lambda: status_badge.configure(
                        text="✅ COMPLETE", fg_color="#28a745"
                    ))
                    
                except Exception as e:
                    error_msg = f"❌ ANALYSIS FAILED\n\nError: {str(e)}"
                    analysis_window.after(0, lambda: self.update_instant_analysis(error_msg))
                    analysis_window.after(0, lambda: status_badge.configure(
                        text="❌ ERROR", fg_color="#d73a49"
                    ))
            
            # Start analysis thread
            analysis_thread = threading.Thread(target=run_instant_analysis, daemon=True)
            analysis_thread.start()
            
        except Exception as e:
            messagebox.showerror("Analysis Window Error", f"Failed to create analysis window: {e}")
    
    def analyze_current_screen(self, screenshot_path, detected_text):
        """Analyze current screen with enhanced AI prompt"""
        global _groq_clients, _current_api_key_index
        
        # Check if Groq API is available
        if not GROQ_API_KEYS or len(GROQ_API_KEYS) == 0:
            return "⚠️ AI analysis unavailable - no valid Groq API keys configured."
        
        # Get available API key
        api_key_index = get_next_available_api_key()
        if api_key_index is None:
            return "⚠️ AI analysis unavailable - all API keys are in cooldown or unavailable."
        
        _groq_client = _groq_clients[api_key_index]
        
        try:
            with open(screenshot_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            return f"Error reading screenshot: {e}"
        
        prompt = f"""INSTANT CYBERSECURITY ANALYSIS:
        
        You are an expert cybersecurity analyst. Analyze the detected text from a screenshot immediately and provide a clear assessment.
        
        Detected text from screen (OCR): "{detected_text}"
        
        Provide analysis in this format:
        
        🚨 THREAT LEVEL: [SAFE/SUSPICIOUS/MALICIOUS]
        
        📋 WHAT THIS TEXT INDICATES:
        [Describe what this text likely represents]
        
        🔍 SECURITY ASSESSMENT:
        [Explain if this is concerning and why]
        
        ⚡ IMMEDIATE ACTION:
        [What the user should do right now]
        
        🛡️ PREVENTION TIPS:
        [How to avoid this in the future]
        
        Be direct and actionable. If no text was detected, state that the screen appears empty or contains only images.
        If nothing suspicious is found, clearly state the content appears safe.
        """
        
        # Prepare messages for Groq (text-only, no vision models available)
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            chat_completion = _groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.2,
                max_tokens=1024,
            )
            
            return chat_completion.choices[0].message.content.strip()
            
        except Exception as e:
            error_str = str(e)
            if "rate limit" in error_str.lower() or "429" in error_str.lower():
                # AI rate-limited for instant analysis - provide local keyword-based explanation
                try:
                    keywords_found = analyze_text(detected_text or "", strict_mode=False)
                except Exception:
                    keywords_found = []

                if keywords_found:
                    found_list = ', '.join(keywords_found[:6])
                    return (f"⚠️ API RATE LIMIT — analysis unavailable (429).\n\n"
                            f"Local keyword scan found potential indicators: {found_list}.\n\n"
                            "Explanation: The AI service is currently rate-limited, so a full model analysis could not be performed. "
                            "The keyword indicators above suggest manual review is recommended. See the Audit Log for captured text.")
                else:
                    return (f"⚠️ API RATE LIMIT — analysis unavailable (429).\n\n"
                            "Explanation: The AI service is currently rate-limited, so a full model analysis could not be performed. "
                            "A local keyword scan found no obvious phishing, credential, or urgency keywords; this suggests the content is likely safe, but please review the Audit Log if uncertain.")
            
            return f"Analysis error: {str(e)}"
    
    def update_instant_analysis(self, analysis):
        """Update instant analysis text with detailed, informative formatting"""
        try:
            if hasattr(self, 'instant_analysis_text'):
                self.instant_analysis_text.delete("1.0", "end")
                
                if analysis.startswith("❌") or analysis.startswith("⚠️"):
                    # Enhanced error/warning formatting
                    formatted_error = f"""{'='*70}
⚠️ INSTANT ANALYSIS STATUS
{'='*70}

{analysis}

{'-'*70}
📊 ANALYSIS CONTEXT:
{'-'*70}
  • Analysis Type: Real-Time Threat Detection
  • Detection Method: Instant AI Analysis
  • Timestamp: {datetime.now().strftime('%m/%d/%Y - %I:%M:%S %p')}
  • Status: Analysis Completed (with limitations)

{'-'*70}
💡 WHAT THIS MEANS:
{'-'*70}
  This analysis was generated immediately after a threat was detected.
  The system captured a screenshot and analyzed it using advanced AI
  algorithms to provide you with actionable security information.

  If the analysis indicates a rate limit or service error, the system
  has fallen back to local keyword-based detection, which is still
  effective but may be less comprehensive than full AI analysis.

{'-'*70}
🔍 NEXT STEPS:
{'-'*70}
  • Review the screenshot above to see what was detected
  • Check the detected text summary for specific indicators
  • Visit the Audit Log tab for complete threat history
  • Consider taking manual action if threats are confirmed

{'='*70}
🔒 SECURELY - REAL-TIME THREAT PROTECTION
{'='*70}"""
                    self.instant_analysis_text.insert("1.0", formatted_error)
                else:
                    # Enhanced detailed formatting for successful analysis
                    try:
                        clean = analysis.replace('**', '').replace('`', '').replace('__', '')
                        clean = re.sub(r'^[ \t]*[-*+]\s+', '  • ', clean, flags=re.M)
                        clean = re.sub(r'^[-=]{3,}\s*$', '', clean, flags=re.M)
                        clean = re.sub(r'\n{3,}', '\n\n', clean)
                        clean = clean.strip()
                    except Exception:
                        clean = analysis
                    
                    formatted_analysis = f"""{'='*70}
⚡ INSTANT CYBERSECURITY ANALYSIS COMPLETE
{'='*70}

📋 DETAILED ASSESSMENT:
{'-'*70}
{clean}

{'-'*70}
📊 ANALYSIS METADATA:
{'-'*70}
  • Analysis Type: Real-Time Instant Analysis
  • Detection Method: AI-Powered Threat Detection
  • Analysis Engine: Advanced Cybersecurity AI Model
  • Response Time: Immediate (captured at threat detection)
  • Timestamp: {datetime.now().strftime('%m/%d/%Y - %I:%M:%S %p')}
  • Status: Analysis Complete and Ready for Review

{'-'*70}
💡 UNDERSTANDING THIS ANALYSIS:
{'-'*70}
  This instant analysis was generated immediately after Securely detected
  a potential security threat on your screen. The AI examined the captured
  screenshot and extracted text to provide you with actionable security
  information.

  Key sections in this analysis:
  • THREAT LEVEL: Overall risk assessment (Safe/Suspicious/Malicious)
  • WHAT THIS TEXT INDICATES: What the detected content likely represents
  • SECURITY ASSESSMENT: Detailed explanation of why this is concerning or safe
  • IMMEDIATE ACTION: What you should do right now
  • PREVENTION TIPS: How to avoid similar threats in the future

{'-'*70}
🔍 ADDITIONAL INFORMATION:
{'-'*70}
  • Review the screenshot above to see the exact content that triggered
    this analysis
  • Check the Threat Detection Summary section for the specific threat
    type and detected text
  • Visit the Audit Log tab to see all historical threat detections
  • Enable continuous monitoring for 24/7 protection

{'-'*70}
🛡️ SECURELY PROTECTION STATUS:
{'-'*70}
  Your system is actively protected by Securely's real-time threat
  detection system. This analysis is part of our comprehensive security
  monitoring that helps keep you safe from phishing, malware, and
  other cyber threats.

{'='*70}
🔒 SECURELY - REAL-TIME THREAT PROTECTION
{'='*70}"""
                    self.instant_analysis_text.insert("1.0", formatted_analysis)
        except Exception as e:
            audit_log(f"Instant analysis update error: {e}", 'ERROR')

    def analyze_text_with_ai(self, text):
        """Run a text-only AI prompt to produce a clear educational analysis and prevention tips."""
        global _groq_clients, _current_api_key_index
        
        # Check if Groq API is available
        if not GROQ_API_KEYS or len(GROQ_API_KEYS) == 0:
            return "⚠️ AI analysis unavailable - no valid Groq API keys configured."
        
        # Get available API key
        api_key_index = get_next_available_api_key()
        if api_key_index is None:
            return "⚠️ AI analysis unavailable - all API keys are in cooldown or unavailable."
        
        _groq_client = _groq_clients[api_key_index]

        # Build a concise educational prompt
        prompt = f"""You are an expert cybersecurity educator. A user saw this short issue: \"{text}\". Provide a clear, concise analysis in this format:

🚨 THREAT LEVEL: [SAFE / SUSPICIOUS / MALICIOUS]

📋 WHAT THIS MEANS:
[Brief plain-English explanation of what this issue likely indicates]

⚡ IMMEDIATE ACTION:
[What the user should do right now, 2-3 bullet points]

🛡️ PREVENTION TIPS:
[3-5 practical prevention steps the user can take]

Keep the response short, direct, and actionable.
"""

        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            chat_completion = _groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.2,
                max_tokens=512,
            )
            
            return chat_completion.choices[0].message.content.strip()
            
        except Exception as e:
            error_str = str(e)
            if "rate limit" in error_str.lower() or "429" in error_str.lower():
                # API rate limited - provide helpful message
                return (f"⚠️ API RATE LIMIT — analysis unavailable (429).\n\n"
                        "The AI service is currently rate-limited. Please try again in a few minutes.\n\n"
                        "In the meantime, you can:\n"
                        "• Review the Audit Log for captured text\n"
                        "• Check the sender's domain and email address\n"
                        "• Look for suspicious links or urgent language\n"
                        "• When in doubt, contact the company directly through their official website")
            
            return f"Analysis error: {str(e)}"

    def show_help_analysis(self, headline_text):
        """Open a compact educational analysis window for the given audit headline."""
        try:
            # Create a borderless toplevel and build a custom title bar like the main window
            win = ctk.CTkToplevel(self)
            win.overrideredirect(True)
            # Set accessibility/title for the window (still useful for task switchers)
            try:
                win.title("Securely - Quick Analysis & Training")
            except Exception:
                pass
            win.geometry("600x420")
            win.configure(fg_color="#0d1117")
            win.attributes("-topmost", True)

            # Title bar
            title_bar = ctk.CTkFrame(win, fg_color="#161b22", height=28)
            title_bar.pack(fill="x")
            title_bar.pack_propagate(False)

            # Icon (reuse main window's original icon if available)
            try:
                if hasattr(self, '_original_icon_img') and Image is not None:
                    small = self._original_icon_img.resize((18, 18), Image.Resampling.LANCZOS)
                    icon_photo = ImageTk.PhotoImage(small)
                    icon_lbl = tk.Label(title_bar, image=icon_photo, bg="#161b22")
                    icon_lbl.image = icon_photo
                    icon_lbl.pack(side="left", padx=(6, 6), pady=4)
            except Exception:
                pass

            # Title text
            title_lbl = ctk.CTkLabel(title_bar, text="Securely — Quick Analysis & Training", font=ctk.CTkFont(size=11, weight="bold"), text_color="#58a6ff")
            title_lbl.pack(side="left", padx=(2, 4))

            # Spacer frame
            spacer = ctk.CTkFrame(title_bar, fg_color="transparent")
            spacer.pack(side="left", expand=True, fill="x")

            # Custom control buttons
            def _minimize():
                try:
                    win.iconify()
                except Exception:
                    pass

            def _toggle_maximize():
                try:
                    if getattr(win, '_is_max', False):
                        # restore
                        prev = getattr(win, '_prev_geom', None)
                        if prev:
                            win.geometry(prev)
                        win._is_max = False
                    else:
                        win._prev_geom = win.geometry()
                        screen_w = win.winfo_screenwidth()
                        screen_h = win.winfo_screenheight()
                        win.geometry(f"{screen_w}x{screen_h}+0+0")
                        win._is_max = True
                except Exception:
                    pass

            def _close():
                try:
                    win.destroy()
                except Exception:
                    pass

            close_btn = ctk.CTkButton(title_bar, text="✕", width=26, height=20, fg_color="transparent", hover_color="#d73a49", text_color="#8b949e", command=_close)
            close_btn.pack(side="right", padx=(4, 6), pady=3)

            resize_btn = ctk.CTkButton(title_bar, text="⛶", width=26, height=20, fg_color="transparent", hover_color="#58a6ff", text_color="#8b949e", command=_toggle_maximize)
            resize_btn.pack(side="right", padx=2, pady=3)

            min_btn = ctk.CTkButton(title_bar, text="−", width=26, height=20, fg_color="transparent", hover_color="#30363d", text_color="#8b949e", command=_minimize)
            min_btn.pack(side="right", padx=2, pady=3)

            # Enable dragging of the window from the title bar
            def start_move(evt):
                win._drag_x = evt.x
                win._drag_y = evt.y

            def on_move(evt):
                try:
                    x = win.winfo_x() + evt.x - win._drag_x
                    y = win.winfo_y() + evt.y - win._drag_y
                    win.geometry(f"+{x}+{y}")
                except Exception:
                    pass

            title_bar.bind("<Button-1>", start_move)
            title_bar.bind("<B1-Motion>", on_move)
            title_lbl.bind("<Button-1>", start_move)
            title_lbl.bind("<B1-Motion>", on_move)

            # Content area
            content = ctk.CTkFrame(win, fg_color="#0d1117")
            content.pack(fill="both", expand=True)

            # Use Textbox instead of Label for better text wrapping
            sub_textbox = ctk.CTkTextbox(content, height=60, wrap="word",
                                        fg_color="#161b22",
                                        text_color="#f0f6fc",
                                        font=ctk.CTkFont(size=10),
                                        border_width=1,
                                        border_color="#30363d")
            sub_textbox.pack(fill="x", padx=12, pady=(12, 6))
            sub_textbox.insert("1.0", headline_text)
            sub_textbox.configure(state="disabled")

            # Scrollable area for analysis results (use textbox for better wrapping)
            scroll_container = ctk.CTkScrollableFrame(content, fg_color="#0d1117")
            scroll_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

            analysis_textbox = ctk.CTkTextbox(scroll_container,
                                            wrap="word",
                                            fg_color="#161b22",
                                        text_color="#f0f6fc",
                                            font=ctk.CTkFont(size=11),
                                            border_width=1,
                                            border_color="#30363d")
            analysis_textbox.pack(fill="both", expand=True, padx=6, pady=6)
            analysis_textbox.insert("1.0", "🔍 Generating educational analysis...\n\nPlease wait.")
            analysis_textbox.configure(state="disabled")

            # Adjust textbox width dynamically so text fits the window
            def adjust_wrap(evt=None):
                try:
                    # Get the available width from scroll container
                    w = scroll_container.winfo_width()
                    if w > 1:  # Only adjust if width is valid
                        # Account for padding/margins (12px padx on each side + 6px internal padx)
                        avail = max(200, w - 36)
                        # Textboxes automatically wrap, but we can ensure they use full width
                        analysis_textbox.configure(width=avail)
                except Exception:
                    pass

            # Bind resizing events and run an initial adjust after the window shows
            try:
                win.bind("<Configure>", adjust_wrap)
                scroll_container.bind("<Configure>", adjust_wrap)
                win.after(120, adjust_wrap)
                win.after(300, adjust_wrap)  # Second adjustment after window fully renders
            except Exception:
                pass

            def sanitize_markdown(text):
                try:
                    s = text
                    # Convert markdown links [text](url) to just text
                    s = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', s)
                    # Remove bold/italic markers like **text** or _text_
                    s = re.sub(r'(\*{1,2}|_{1,2})(.*?)\1', r'\2', s, flags=re.S)
                    # Remove inline code ticks
                    s = s.replace('`', '')
                    # Convert list markers to bullets
                    s = re.sub(r'^[ \t]*[-*+]\s+', '• ', s, flags=re.M)
                    # Remove heading hashes
                    s = re.sub(r'^#{1,6}\s+', '', s, flags=re.M)
                    # Remove thematic breaks
                    s = re.sub(r'^[-=]{3,}\s*$', '', s, flags=re.M)
                    # Collapse excessive blank lines
                    s = re.sub(r'\n{3,}', '\n\n', s)
                    # Remove leading boilerplate lines like "Okay, here's... formatted as requested" or "as requested"
                    try:
                        lines = s.strip().splitlines()
                        # Strip up to the first 3 lines if they look like polite boilerplate
                        for _ in range(3):
                            if not lines:
                                break
                            first = lines[0].strip()
                            if re.search(r"(?i)formatted as requested|as requested", first):
                                lines.pop(0)
                                continue
                            if re.search(r"(?i)^okay[,\.!\s]|^here('?s)?\s+(a\s+)?(cybersecurity|security|analysis)", first):
                                lines.pop(0)
                                continue
                            # If the line is a short boilerplate like 'Analysis:' remove it
                            if re.search(r"(?i)^(analysis|cybersecurity analysis|threat level)[:\-]?$", first):
                                lines.pop(0)
                                continue
                            break
                        s = '\n'.join(lines).lstrip()
                    except Exception:
                        pass

                    return s.strip()
                except Exception:
                    return text

            # Per-entry cache key (use the original headline/log line)
            cache_key = (headline_text or '').strip()
            cache = globals().get('AI_ANALYSIS_CACHE', {})
            if cache_key and cache_key in cache:
                try:
                    analysis_textbox.configure(state="normal")
                    analysis_textbox.delete("1.0", "end")
                    analysis_textbox.insert("1.0", cache[cache_key])
                    analysis_textbox.configure(state="disabled")
                except Exception:
                    try:
                        analysis_textbox.configure(state="normal")
                        analysis_textbox.delete("1.0", "end")
                        analysis_textbox.insert("1.0", cache.get(cache_key, "(cached analysis)"))
                        analysis_textbox.configure(state="disabled")
                    except Exception:
                        pass
            else:
                def run_analysis():
                    try:
                        analysis = self.analyze_text_with_ai(headline_text)
                        clean = sanitize_markdown(analysis)

                        # Store cleaned analysis in the in-memory cache
                        try:
                            globals().setdefault('AI_ANALYSIS_CACHE', {})[cache_key] = clean
                        except Exception:
                            pass

                        def _insert_clean():
                            try:
                                analysis_textbox.configure(state="normal")
                                analysis_textbox.delete("1.0", "end")
                                analysis_textbox.insert("1.0", clean)
                                analysis_textbox.configure(state="disabled")
                            except Exception:
                                try:
                                    analysis_textbox.configure(state="normal")
                                    analysis_textbox.delete("1.0", "end")
                                    analysis_textbox.insert("1.0", analysis)
                                    analysis_textbox.configure(state="disabled")
                                except Exception:
                                    pass

                        win.after(0, _insert_clean)
                    except Exception as e:
                        def _show_error():
                            try:
                                analysis_textbox.configure(state="normal")
                                analysis_textbox.delete("1.0", "end")
                                analysis_textbox.insert("1.0", f"Analysis error: {e}")
                                analysis_textbox.configure(state="disabled")
                            except Exception:
                                pass
                        win.after(0, _show_error)

                threading.Thread(target=run_analysis, daemon=True).start()

            # Ensure close works when user presses Escape
            win.bind('<Escape>', lambda e: _close())

        except Exception as e:
            try:
                messagebox.showerror("Analysis Error", f"Failed to open analysis window: {e}")
            except Exception:
                audit_log(f"Failed to open analysis window: {e}", 'ERROR')
    
    def update_analysis_text(self, analysis):
        """Update analysis text in training window with detailed, informative formatting"""
        try:
            if hasattr(self, 'analysis_text'):
                self.analysis_text.delete("1.0", "end")
                
                # Professional formatting for analysis results
                if analysis.startswith("❌") or analysis.startswith("⚠️"):
                    # Error or warning formatting - keep as is but enhance structure
                    formatted_error = f"""{'='*70}
⚠️ ANALYSIS STATUS
{'='*70}

{analysis}

{'='*70}
📊 DETAILED BREAKDOWN
{'='*70}

This analysis was generated using advanced AI threat detection algorithms.
The system analyzed the captured screenshot and extracted text to provide
this comprehensive security assessment.

💡 TIP: Review the screenshot above to see the exact content that was analyzed.
   Check the Audit Log tab for additional context and historical threats.

{'='*70}
🔒 SECURELY - PROTECTING YOUR DIGITAL ENVIRONMENT
{'='*70}"""
                    self.analysis_text.insert("1.0", formatted_error)
                else:
                    # Enhanced detailed formatting for successful analysis
                    try:
                        clean = analysis.replace('**', '').replace('`', '').replace('__', '')
                        clean = re.sub(r'^[ \t]*[-*+]\s+', '  • ', clean, flags=re.M)
                        clean = re.sub(r'^[-=]{3,}\s*$', '', clean, flags=re.M)
                        clean = re.sub(r'\n{3,}', '\n\n', clean)
                        
                        # Remove polite boilerplate lines at the start
                        try:
                            lines = clean.strip().splitlines()
                            for _ in range(3):
                                if not lines:
                                    break
                                first = lines[0].strip()
                                if re.search(r"(?i)formatted as requested|as requested", first):
                                    lines.pop(0)
                                    continue
                                if re.search(r"(?i)^okay[,\.!\s]|^here('?s)?\s+(a\s+)?(cybersecurity|security|analysis)", first):
                                    lines.pop(0)
                                    continue
                                if re.search(r"(?i)^(analysis|cybersecurity analysis|threat level)[:\-]?$", first):
                                    lines.pop(0)
                                    continue
                                break
                            clean = '\n'.join(lines).lstrip()
                        except Exception:
                            pass
                        clean = clean.strip()
                    except Exception:
                        clean = analysis

                    # Enhanced informative formatting
                    formatted_analysis = f"""{'='*70}
🛡️ COMPREHENSIVE CYBERSECURITY ANALYSIS
{'='*70}

📋 ANALYSIS DETAILS:
{'-'*70}
{clean}

{'-'*70}
📊 ANALYSIS METADATA:
{'-'*70}
  • Analysis Type: Training/Educational Analysis
  • Detection Method: AI-Powered Threat Analysis
  • Analysis Engine: Advanced Cybersecurity AI Model
  • Timestamp: {datetime.now().strftime('%m/%d/%Y - %I:%M:%S %p')}
  • Status: Analysis Complete

{'-'*70}
💡 UNDERSTANDING THIS ANALYSIS:
{'-'*70}
  This detailed analysis was generated by Securely's AI threat detection
  system. The AI examined the captured screenshot and extracted text to
  provide a comprehensive security assessment.

  Key sections explained:
  • THREAT LEVEL: Overall risk assessment (Safe/Suspicious/Malicious)
  • WHAT THIS INDICATES: What the detected content likely represents
  • WHY IT'S CONCERNING/SAFE: Detailed explanation of the assessment
  • RED FLAGS: Specific warning signs detected (if any)
  • PREVENTION TIPS: How to avoid similar threats in the future
  • WHAT TO DO: Immediate actions you should take

{'-'*70}
🔍 ADDITIONAL RESOURCES:
{'-'*70}
  • Review the screenshot above to see the exact content analyzed
  • Check the Audit Log tab for historical threat detections
  • Visit the Settings tab to adjust detection sensitivity
  • Enable notifications to stay informed about future threats

{'='*70}
🔒 SECURELY - REAL-TIME THREAT PROTECTION
{'='*70}"""

                    self.analysis_text.insert("1.0", formatted_analysis)
        except Exception as e:
            print(f"Analysis text update error: {e}")
        
    def create_credits_tab(self):
        credits = self.tab_view.tab("ℹ️")
        
        # Use scrollable frame to ensure everything fits
        scroll = ctk.CTkScrollableFrame(credits, fg_color="#0d1117", 
                                       scrollbar_button_color="#30363d",
                                       scrollbar_button_hover_color="#424549")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Need Help? label
        need_help_label = ctk.CTkLabel(scroll,
                                      text="Need Help?",
                                      font=ctk.CTkFont(size=11, weight="bold"),
                                      text_color="#8b949e")
        need_help_label.pack(pady=(8, 4))
        
        # Guide Button
        guide_btn = ctk.CTkButton(scroll,
                                 text="Quick Guide",
                                 width=120,
                                 height=28,
                                 font=ctk.CTkFont(size=11),
                                 fg_color="#28a745",
                                 hover_color="#22863a",
                                 text_color="#ffffff",
                                 corner_radius=6,
                                 command=self.open_guide)
        guide_btn.pack(pady=(0, 12))
        
        # Development Team
        dev_label = ctk.CTkLabel(scroll,
                                 text="Developed by:",
                                 font=ctk.CTkFont(size=11, weight="bold"),
                                 text_color="#8b949e")
        dev_label.pack(pady=(0, 4))
        
        delexo_label = ctk.CTkLabel(scroll,
                                    text="@Diego - Lead Developer",
                                    font=ctk.CTkFont(size=11),
                                    text_color="#f0f6fc")
        delexo_label.pack(pady=2)
        
        mai_label = ctk.CTkLabel(scroll,
                                 text="@Mai - Business & Marketing",
                                 font=ctk.CTkFont(size=11),
                                 text_color="#f0f6fc")
        mai_label.pack(pady=2)
        
        # Special Thanks
        thanks_label = ctk.CTkLabel(scroll,
                                    text="Special Thanks:",
                                    font=ctk.CTkFont(size=11, weight="bold"),
                                    text_color="#8b949e")
        thanks_label.pack(pady=(12, 4))
        
        thanks_names = ["Priscilla", "Derek", "CSUSM Community"]
        for name in thanks_names:
            thanks_item = ctk.CTkLabel(scroll,
                                      text=f"• {name}",
                                      font=ctk.CTkFont(size=10),
                                      text_color="#8b949e")
            thanks_item.pack(pady=1)
        
        # Built With
        tech_label = ctk.CTkLabel(scroll,
                                  text="Built With:",
                                  font=ctk.CTkFont(size=11, weight="bold"),
                                  text_color="#8b949e")
        tech_label.pack(pady=(12, 4))
        
        tech_items = ["🐍 Python", "🤖 Google Gemini API", "👁️ Tesseract OCR", "☕ A lot of Starbucks"]
        for tech in tech_items:
            tech_item = ctk.CTkLabel(scroll,
                                    text=f"• {tech}",
                                    font=ctk.CTkFont(size=10),
                                    text_color="#8b949e")
            tech_item.pack(pady=1)
        
        # Learn More Button
        learn_btn = ctk.CTkButton(scroll,
                                 text="Visit Website",
                                 width=120,
                                 height=28,
                                 font=ctk.CTkFont(size=11),
                                 fg_color="#0969da",
                                 hover_color="#0860ca",
                                 text_color="#ffffff",
                                 corner_radius=6,
                                 command=self.open_learn_more)
        learn_btn.pack(pady=(12, 8))
        
        # Copyright
        copyright_label = ctk.CTkLabel(scroll,
                                      text=f"© 2025 Securely {APP_VERSION}",
                                      font=ctk.CTkFont(size=9),
                                      text_color="#6e7681")
        copyright_label.pack(pady=(4, 8))
    
    def open_guide(self):
        """Open guide page for Securely"""
        import webbrowser
        try:
            webbrowser.open("https://delexoo.github.io/Securely/guide.html")
        except Exception as e:
            print(f"Error opening guide: {e}")
    
    def open_learn_more(self):
        """Open learn more link or show additional information"""
        import webbrowser
        try:
            # Open official Securely page
            webbrowser.open("https://delexoo.github.io/Securely/")
        except Exception:
            # Fallback - show info dialog
            info_window = ctk.CTkToplevel(self)
            info_window.title("Learn More - Securely")
            info_window.geometry("500x400")
            info_window.configure(fg_color="#0d1117")
            
            info_text = """🛡️ Securely - Advanced Security Monitoring
            
Securely is a comprehensive security monitoring solution that provides:

🔍 Real-time Threat Detection
• Advanced OCR-based screen analysis
• AI-powered threat identification
• Comprehensive keyword matching

🎯 Visual Feedback System
• Real-time hitbox overlays
• Smooth threat tracking
• Ultra-fast response times

🎓 Educational Security
• Interactive threat learning
• Detailed prevention guides
• Professional security training

📊 Comprehensive Monitoring
• Detailed audit logging
• Customizable alert systems
• Advanced filtering options

Developed by @Delexo and @Mai
© 2025 Securely - Advanced Security Solutions"""
            
            info_label = ctk.CTkTextbox(info_window, wrap="word")
            info_label.pack(fill="both", expand=True, padx=20, pady=20)
            info_label.insert("1.0", info_text)
            info_label.configure(state="disabled")
            
            close_btn = ctk.CTkButton(info_window, text="Close",
                                     command=info_window.destroy)
            close_btn.pack(pady=(0, 20))
    
    def open_store(self):
        """Open store link in the default browser"""
        import webbrowser
        try:
            webbrowser.open("https://beacons.ai/delexo")
        except Exception as _e:
            try:
                messagebox.showinfo("Store", "Store link unavailable right now.")
            except Exception:
                print(f"Store link error: {_e}")
        
    def show_audit_log(self):
        # Switch to audit log tab
        self.tab_view.set("📋")
        self.load_audit_log()
        
    def load_audit_log(self):
        """Load and display audit log with visual threat cards, screenshots, and AI analysis"""
        try:
            # Mark as loaded
            self._audit_log_loaded = True
            
            # Clear existing threat cards
            for widget in self.audit_frame.winfo_children():
                widget.destroy()
            self.threat_cards = []

            # Always display the textual audit log (no screenshots stored/displayed)
            try:
                with open("securely_log.txt", "r", encoding="utf-8") as f:
                    log_content = f.read().strip()

                    if log_content:
                        # Show the last ~100 lines for context (reduced from 200 to improve performance)
                        lines = log_content.split('\n')[-100:]
                        # Reverse the order so most recent entries appear at the top
                        lines.reverse()

                        # Calculate wrap length based on audit_frame width so text wraps with the window
                        try:
                            self.audit_frame.update_idletasks()
                            frame_width = max(200, self.audit_frame.winfo_width() - 24)
                        except Exception:
                            frame_width = 600

                        # Only display header lines (the simplified [date] [time] Problem)
                        for line in lines:
                            stripped = line.rstrip()
                            if not stripped:
                                continue
                            if stripped.startswith('[') and ']' in stripped:
                                # Create a horizontal frame with the headline and a small help button
                                row = ctk.CTkFrame(self.audit_frame, fg_color="transparent")
                                row.pack(fill="x", padx=6, pady=1)

                                # Parse the timestamp and message. Log format: [MM/DD/YYYY] [H:MM AM/PM] Message
                                try:
                                    m = re.match(r'^\[([^\]]+)\]\s*\[([^\]]+)\]\s*(.*)$', stripped)
                                    if m:
                                        date_part = m.group(1).strip()
                                        time_part = m.group(2).strip()
                                        msg_only = m.group(3).strip()
                                    else:
                                        # Fallback if format unexpected
                                        date_part = ""
                                        time_part = ""
                                        msg_only = re.sub(r'^\[[^\]]+\]\s*', '', stripped)
                                except Exception:
                                    date_part = ""
                                    time_part = ""
                                    msg_only = stripped

                                # Create a single-line entry: Date & Time (primary) and a help button
                                primary_text = f"{date_part} {time_part}".strip()
                                if not primary_text:
                                    primary_text = date_part or time_part or "Unknown Time"

                                # Help button to open deep educational analysis for this audit line
                                help_btn = None
                                try:
                                    # Use a clearer action label for the audit entry
                                    help_btn = ctk.CTkButton(row, text="Inspect",
                                                             width=72, height=22,
                                                             font=ctk.CTkFont(size=10, weight="bold"),
                                                             fg_color="#0969da",
                                                             hover_color="#085fc7",
                                                             text_color="#ffffff",
                                                             command=(lambda t=stripped: self.show_help_analysis(t)))
                                    help_btn.pack(side="right", padx=(6, 0))
                                    # Accessibility: tooltip-like binding (shows full label when hovered)
                                    # No-op tooltip binding here; main app already provides tab tooltips.
                                    pass
                                except Exception:
                                    help_btn = None

                                # Primary label: Date & Time (bolder)
                                primary_label = ctk.CTkLabel(row,
                                                             text=primary_text,
                                                             font=ctk.CTkFont(size=9, weight="bold"),
                                                             text_color="#f0f6fc",
                                                             anchor="w")
                                primary_label.pack(side="left", fill="x", expand=True)

                                # If the help button couldn't be created, make the date label clickable as a fallback
                                if not help_btn:
                                    try:
                                        primary_label.bind("<Button-1>", lambda e, t=stripped: self.show_help_analysis(t))
                                    except Exception:
                                        pass
                    else:
                        no_log_label = ctk.CTkLabel(self.audit_frame,
                                                   text="📋 No security events logged",
                                                   font=ctk.CTkFont(size=12),
                                                   text_color="#8b949e")
                        no_log_label.pack(pady=20)
            except FileNotFoundError:
                no_file_label = ctk.CTkLabel(self.audit_frame,
                                            text="📋 No security events logged",
                                            font=ctk.CTkFont(size=12),
                                            text_color="#8b949e")
                no_file_label.pack(pady=20)

        except Exception as e:
            print(f"Load audit log error: {e}")
            error_label = ctk.CTkLabel(self.audit_frame,
                                      text=f"⚠️ Error loading audit log: {e}",
                                      font=ctk.CTkFont(size=11),
                                      text_color="#d73a49")
            error_label.pack(pady=20)
            
    def create_threat_card(self, training_id, training_data):
        """Create a visual threat card with screenshot and AI analysis"""
        try:
            # Main threat card frame
            card = ctk.CTkFrame(self.audit_frame, fg_color="#161b22", corner_radius=10,
                              border_width=2, border_color="#30363d")
            card.pack(fill="x", padx=10, pady=8)
            
            # Header with threat type and timestamp
            header_frame = ctk.CTkFrame(card, fg_color="#21262d", corner_radius=8)
            header_frame.pack(fill="x", padx=8, pady=8)
            
            threat_label = ctk.CTkLabel(header_frame,
                                       text=f"⚠️ {training_data['threat_type']}",
                                       font=ctk.CTkFont(size=13, weight="bold"),
                                       text_color="#ff6b35")
            threat_label.pack(side="left", padx=10, pady=8)
            
            time_label = ctk.CTkLabel(header_frame,
                                    text=training_data['timestamp'],
                                    font=ctk.CTkFont(size=10),
                                    text_color="#8b949e")
            time_label.pack(side="right", padx=10, pady=8)
            
            # Screenshot section - only show in enlarged mode to save space
            if os.path.exists(training_data['screenshot_path']):
                if not self.is_enlarged:
                    # In mini mode, show compact info only
                    compact_info = ctk.CTkLabel(card, 
                                               text="📸 Screenshot captured\n(Expand window to view)",
                                               font=ctk.CTkFont(size=9),
                                               text_color="#8b949e")
                    compact_info.pack(padx=8, pady=(0, 8))
                else:
                    try:
                        screenshot = Image.open(training_data['screenshot_path'])
                        # Thumbnail for audit log
                        screenshot.thumbnail((600, 250), Image.Resampling.LANCZOS)
                        
                        # Add border
                        bordered = Image.new('RGB', (screenshot.width + 4, screenshot.height + 4), '#30363d')
                        bordered.paste(screenshot, (2, 2))
                        
                        screenshot_photo = ctk.CTkImage(light_image=bordered,
                                                       size=(bordered.width, bordered.height))
                        
                        screenshot_label = ctk.CTkLabel(card, image=screenshot_photo, text="")
                        screenshot_label.image = screenshot_photo  # Keep reference
                        screenshot_label.pack(padx=8, pady=(0, 8))
                    except Exception as e:
                        print(f"Screenshot display error: {e}")
            
            # AI Analysis section - compact in mini mode
            if not self.is_enlarged:
                # Mini mode - show compact summary only
                mini_summary = ctk.CTkLabel(card,
                                           text="🤖 AI Analysis Available",
                                           font=ctk.CTkFont(size=10),
                                           text_color="#58a6ff")
                mini_summary.pack(padx=8, pady=(0, 8))
                analysis_text = None  # Skip full analysis in mini mode
            else:
                # Full mode - show complete analysis
                analysis_frame = ctk.CTkFrame(card, fg_color="#0d1117", corner_radius=8)
                analysis_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
                
                analysis_header = ctk.CTkLabel(analysis_frame,
                                             text="🤖 AI Security Analysis",
                                             font=ctk.CTkFont(size=12, weight="bold"),
                                             text_color="#58a6ff")
                analysis_header.pack(anchor="w", padx=10, pady=(8, 5))
                
                # Analysis text
                analysis_text = ctk.CTkTextbox(analysis_frame, height=100,
                                              fg_color="#161b22",
                                              text_color="#f0f6fc",
                                              font=ctk.CTkFont(size=9),
                                              border_width=1,
                                              border_color="#30363d",
                                              wrap="word")
                analysis_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
            # Check if already analyzed (only in full mode)
            if analysis_text is not None:  # Only process if not in mini mode
                if training_data.get('analyzed', False) and training_data.get('ai_analysis'):
                    # Display cached analysis
                    analysis_text.insert("1.0", training_data['ai_analysis'])
                    analysis_text.configure(state="disabled")
                else:
                    # Show loading and start analysis
                    analysis_text.insert("1.0", "⏳ Running AI analysis...\n\nAnalyzing screenshot for security threats...")
                    analysis_text.configure(state="disabled")
                    
                    # Run AI analysis in background
                    def analyze_threat():
                        try:
                            analysis = analyze_screenshot_for_training(
                                training_data['screenshot_path'],
                                training_data['text_content']
                            )
                            
                            # Store analysis in training data
                            training_data['ai_analysis'] = analysis
                            training_data['analyzed'] = True
                            
                            # Update UI
                            self.after(0, lambda: self.update_threat_card_analysis(analysis_text, analysis))
                        except Exception as e:
                            error_msg = f"❌ Analysis failed: {str(e)}"
                            self.after(0, lambda: self.update_threat_card_analysis(analysis_text, error_msg))
                    
                    # Start analysis thread
                    threading.Thread(target=analyze_threat, daemon=True).start()
            
            # View details button
            details_btn = ctk.CTkButton(card, text="🔍 View Full Analysis",
                                       height=30,
                                       font=ctk.CTkFont(size=11),
                                       fg_color="#0969da",
                                       hover_color="#0860ca",
                                       command=lambda tid=training_id: self.show_training_analysis(tid))
            details_btn.pack(pady=(0, 8))
            
            self.threat_cards.append(card)
            
        except Exception as e:
            print(f"Create threat card error: {e}")
    
    def update_threat_card_analysis(self, textbox, analysis):
        """Update the analysis textbox with AI results"""
        try:
            textbox.configure(state="normal")
            textbox.delete("1.0", "end")
            textbox.insert("1.0", analysis)
            textbox.configure(state="disabled")
        except Exception as e:
            print(f"Update analysis error: {e}")
    
    def clear_audit_log(self):
        # Clear the audit log file and display
        try:
            with open("securely_log.txt", "w", encoding="utf-8") as f:
                f.write("")
            
            # Clear training storage
            if hasattr(log_event, 'training_storage'):
                log_event.training_storage = {}
            
            # Clear visual display
            for widget in self.audit_frame.winfo_children():
                widget.destroy()
            self.threat_cards = []
            
            # Show cleared message
            cleared_label = ctk.CTkLabel(self.audit_frame,
                                        text="✅ Audit log cleared",
                                        font=ctk.CTkFont(size=12),
                                        text_color="#238636")
            cleared_label.pack(pady=20)
            
        except Exception as e:
            print(f"Clear log error: {e}")
        
    def on_program_toggle(self):
        # If currently OFF and user clicked to enable, show confirmation page instead of toggling immediately
        if not getattr(self, 'program_enabled', False):
            try:
                self.show_monitor_confirm_page()
                return
            except Exception:
                # If confirmation page cannot be shown for any reason, fall back to enabling directly
                pass

        # Toggle program on/off (used for turning OFF or fallback enabling)
        self.program_enabled = not getattr(self, 'program_enabled', False)

        if self.program_enabled:
            # Automatically stop 15-minute scan if it's active
            import time
            scan_active = False
            if hasattr(self, 'monitor') and self.monitor:
                if hasattr(self.monitor, '_multi_scan_until'):
                    scan_until = getattr(self.monitor, '_multi_scan_until', 0)
                    if scan_until > time.time():
                        scan_active = True
            
            if scan_active:
                print("Stopping temporary scan to enable 24/7 monitoring")
                # Stop the 15-minute scan
                if hasattr(self, 'monitor') and self.monitor:
                    # Clear the scan timer
                    if hasattr(self.monitor, '_multi_scan_until'):
                        delattr(self.monitor, '_multi_scan_until')
                
                # Cancel countdown
                if hasattr(self, '_scan_countdown_after_id') and self._scan_countdown_after_id:
                    try:
                        self.after_cancel(self._scan_countdown_after_id)
                    except Exception:
                        pass
                    self._scan_countdown_after_id = None
                
                # Reset countdown state
                if hasattr(self, 'short_scan_seconds'):
                    self.short_scan_seconds = 0
                
                # Update button to show it can be started again
                try:
                    current_text = self.short_scan_btn.cget('text')
                    if current_text == "Stop Scan":
                        button_text = self.get_scan_button_text()
                        self.short_scan_btn.configure(text=button_text, fg_color="#0969da", hover_color="#0860ca")
                except Exception:
                    pass
            
            # Program is now ON
            self.program_toggle_btn.configure(text="Turn Off", 
                                            fg_color="#dc3545",  # Red for Turn Off
                                            hover_color="#c82333")
            # Show green active indicator when program is enabled
            self.status_label.configure(text="● Active", text_color="#28a745")
            # Cancel any pending auto-resume (user took manual action)
            try:
                if hasattr(self, '_auto_resume_after_id') and self._auto_resume_after_id:
                    self.after_cancel(self._auto_resume_after_id)
                    self._auto_resume_after_id = None
            except Exception:
                pass
            
            # Cancel countdown timer if running
            try:
                if hasattr(self, '_pause_countdown_id') and self._pause_countdown_id:
                    self.after_cancel(self._pause_countdown_id)
                    self._pause_countdown_id = None
            except Exception:
                pass
            
            # Only start if not already running
            if not self.monitor.running.is_set():
                self.monitor.start_monitor()
            self.monitoring_var.set(True)
            # Clear any auto-pause flag when user manually re-enables
            try:
                globals()['PAUSED_FOR_SENSITIVE_PAGE'] = False
            except Exception:
                pass
            # User interacted: show compact title status as Screen Secured
            try:
                self.update_ai_status("Screen Secured")
            except Exception:
                pass
            # Start audit log auto-refresh loop while monitoring is active
            try:
                # Kick off refresh loop (it will only actually refresh while the monitor is running)
                self.refresh_audit_log()
            except Exception:
                pass
        else:
            # Program is now OFF
            self.program_toggle_btn.configure(text="Toggle 24/7 Monitoring", 
                                            fg_color="#28a745",  # Green for ON
                                            hover_color="#218838")
            self.status_label.configure(text="● Disabled", text_color="#8b949e")
            # Cancel any pending auto-resume (user took manual action)
            try:
                if hasattr(self, '_auto_resume_after_id') and self._auto_resume_after_id:
                    self.after_cancel(self._auto_resume_after_id)
                    self._auto_resume_after_id = None
            except Exception:
                pass
            
            # Cancel countdown timer if running
            try:
                if hasattr(self, '_pause_countdown_id') and self._pause_countdown_id:
                    self.after_cancel(self._pause_countdown_id)
                    self._pause_countdown_id = None
            except Exception:
                pass
            
            # Pause everything safely
            try:
                self.pause_all()
            except Exception:
                try:
                    self.monitor.stop_monitor()
                except Exception:
                    pass
            self.monitoring_var.set(False)
        
    def on_monitoring_toggled(self):
        # Sync with program toggle button
        if self.monitoring_var.get():
            self.program_enabled = True
            self.program_toggle_btn.configure(text="Turn Off", 
                                            fg_color="#dc3545",  # Red for Turn Off
                                            hover_color="#c82333")
            self.status_label.configure(text="● Active", text_color="#58a6ff")
            # Only start if not already running
            if not self.monitor.running.is_set():
                self.monitor.start_monitor()
            # Clear any auto-pause flag when user manually re-enables
            try:
                globals()['PAUSED_FOR_SENSITIVE_PAGE'] = False
            except Exception:
                pass
        else:
            self.program_enabled = False
            self.program_toggle_btn.configure(text="Toggle 24/7 Monitoring", 
                                            fg_color="#28a745",  # Green for Turn On
                                            hover_color="#218838")
            self.status_label.configure(text="● Disabled", text_color="#f85149") 
            # Pause everything safely
            try:
                self.pause_all()
            except Exception:
                try:
                    self.monitor.stop_monitor()
                except Exception:
                    pass
    
    def show_monitor_confirm_page(self):
        """Show the in-app confirmation page (hides the main tab view)."""
        try:
            # Hide the tab view and pack confirmation frame in its place
            try:
                self.tab_view.pack_forget()
            except Exception:
                pass
            try:
                self.monitor_confirm_frame.pack(fill="both", expand=True, padx=4, pady=4)
            except Exception:
                pass
        except Exception as e:
            print(f"Failed to show confirmation page: {e}")

    def hide_monitor_confirm_page(self):
        """Hide confirmation page and restore main tab view."""
        try:
            try:
                self.monitor_confirm_frame.pack_forget()
            except Exception:
                pass
            try:
                self.tab_view.pack(fill="both", expand=True)
            except Exception:
                pass
        except Exception as e:
            print(f"Failed to hide confirmation page: {e}")

    def _confirm_enable_monitor(self):
        """Called when user confirms enabling continuous monitoring."""
        try:
            # Hide confirmation UI first
            try:
                self.hide_monitor_confirm_page()
            except Exception:
                pass

            # Automatically stop 15-minute scan if it's active
            import time
            scan_active = False
            if hasattr(self, 'monitor') and self.monitor:
                if hasattr(self.monitor, '_multi_scan_until'):
                    scan_until = getattr(self.monitor, '_multi_scan_until', 0)
                    if scan_until > time.time():
                        scan_active = True
            
            if scan_active:
                print("Stopping temporary scan to enable 24/7 monitoring")
                # Stop the 15-minute scan
                if hasattr(self, 'monitor') and self.monitor:
                    # Clear the scan timer
                    if hasattr(self.monitor, '_multi_scan_until'):
                        delattr(self.monitor, '_multi_scan_until')
                
                # Cancel countdown
                if hasattr(self, '_scan_countdown_after_id') and self._scan_countdown_after_id:
                    try:
                        self.after_cancel(self._scan_countdown_after_id)
                    except Exception:
                        pass
                    self._scan_countdown_after_id = None
                
                # Reset countdown state
                if hasattr(self, 'short_scan_seconds'):
                    self.short_scan_seconds = 0
                
                # Update button to show it can be started again
                try:
                    current_text = self.short_scan_btn.cget('text')
                    if current_text == "Stop Scan":
                        button_text = self.get_scan_button_text()
                        self.short_scan_btn.configure(text=button_text, fg_color="#0969da", hover_color="#0860ca")
                except Exception:
                    pass

            # Set enabled state and perform same enabling logic as on_program_toggle would do
            self.program_enabled = True
            try:
                self.program_toggle_btn.configure(text="Turn Off", 
                                                fg_color="#dc3545",  # Red for Turn Off
                                                hover_color="#c82333")
            except Exception:
                pass
            try:
                self.status_label.configure(text="● Active", text_color="#28a745")
            except Exception:
                pass

            # Cancel any pending auto-resume (user took manual action)
            try:
                if hasattr(self, '_auto_resume_after_id') and self._auto_resume_after_id:
                    self.after_cancel(self._auto_resume_after_id)
                    self._auto_resume_after_id = None
            except Exception:
                pass
            
            # Cancel countdown timer if running
            try:
                if hasattr(self, '_pause_countdown_id') and self._pause_countdown_id:
                    self.after_cancel(self._pause_countdown_id)
                    self._pause_countdown_id = None
            except Exception:
                pass

            # Start monitor
            if not self.monitor.running.is_set():
                try:
                    self.monitor.start_monitor()
                except Exception as e:
                    print(f"Failed to start monitor: {e}")

            try:
                self.monitoring_var.set(True)
            except Exception:
                pass
            try:
                globals()['PAUSED_FOR_SENSITIVE_PAGE'] = False
            except Exception:
                pass
            try:
                self.update_ai_status("Screen Secured")
            except Exception:
                pass
            try:
                self.refresh_audit_log()
            except Exception:
                pass
        except Exception as e:
            print(f"Error confirming and enabling monitor: {e}")
            
    def on_notifications_toggled(self):
        enabled = self.notifications_var.get()
        self.monitor.notifications_enabled = enabled
        
    def on_sound_toggled(self):
        enabled = self.sound_var.get()
        self.monitor.sound_enabled = enabled
        
    def on_strict_mode_toggled(self):
        enabled = self.strict_mode_var.get()
        self.monitor.strict_mode = enabled
        
    def on_hitboxes_toggled(self):
        enabled = self.hitboxes_var.get()
        self.monitor.hitboxes_enabled = enabled
        print(f"Hitboxes toggled: {enabled}")
        
        # If disabling, immediately close any existing overlay
        if not enabled:
            self.monitor.close_overlay()
            self.monitor.active_threats = {}
            print("Hitboxes disabled - overlay closed")
        else:
            print("Hitboxes enabled - waiting for threat detection...")
            print("TIP: Enable 'Test Mode' to see a demo hitbox immediately!")
            
            # When enabling, force an immediate update if threats exist
            if hasattr(self.monitor, 'active_threats') and self.monitor.active_threats:
                # Redraw hitboxes for existing threats
                try:
                    import mss
                    # Capture PRIMARY MONITOR ONLY for overlay sizing
                    with mss.mss() as sct:
                        # Use PRIMARY MONITOR ONLY
                        primary_monitor = get_primary_monitor(sct)
                        img = sct.grab(primary_monitor)  # Primary monitor only
                        screen_size = img.size
                        self.monitor.update_continuous_overlay(self.monitor.active_threats, screen_size)
                        print(f"Redrew {len(self.monitor.active_threats)} hitbox(es)")
                except Exception as e:
                    print(f"Immediate hitbox update error: {e}")
            else:
                print("No active threats to display - hitboxes will appear when threats detected")
        
    def test_notification(self):
        """Trigger a test notification to verify the system is working"""
        print("Testing notification system...")
        
        try:
            # Send a clear test notification with success message
            notification_title = "✅ Securely - Test Successful"
            notification_msg = "Notification system is working correctly! This is a test notification from Securely."

            # Use universal notification function (works in .exe)
            notification_sent = show_notification(notification_title, notification_msg, duration=10)

            if notification_sent:
                print("✅ Test notification sent successfully.")
                # Show a second confirmation notification to make it clear it worked
                try:
                    show_notification(
                        "✅ Test Complete",
                        "If you see this notification, the test was successful!",
                        duration=5
                    )
                except Exception:
                    pass
            else:
                print("⚠️ Test notification could not be delivered natively.")
                print("Install 'win11toast' or 'win10toast' or 'winrt' in this Python environment to enable OS toasts.")
                # Try to show a fallback message
                try:
                    from tkinter import messagebox
                    messagebox.showinfo(
                        "Test Notification",
                        "Notification system test completed.\n\n"
                        "If you did not see a desktop notification, please install:\n"
                        "• win11toast (for Windows 11)\n"
                        "• win10toast (for Windows 10)\n"
                        "• python-winrt (alternative)\n\n"
                        "Run: pip install win11toast"
                    )
                except Exception as msg_e:
                    print(f"Fallback messagebox error: {msg_e}")
            
        except Exception as e:
            print(f"Test notification error: {e}")
            # Show error notification if possible
            try:
                show_notification(
                    "❌ Test Failed",
                    f"Notification test encountered an error: {str(e)}",
                    duration=8
                )
            except Exception:
                pass

    # `show_in_app_toast` removed per user request — native-only notifications enforced.
    # Any prior fallback to in-app toasts was intentionally removed. Keep no-op placeholder for compatibility.
    def show_in_app_toast(self, title, message, duration=5):
        return False
    
    def instant_analysis_test(self):
        """Provide an educational deep analysis for the most recent detected threat.

        Behavior:
        - If the monitor has a recent analyzed screenshot, save it and open the full AI analysis window
          (calls `show_instant_analysis`) with the last threat description and AI text.
        - If no recent screenshot is available, fall back to the Threat Education Library.
        """
        try:
            print("Educate Me: preparing deep analysis...")

            # Prefer to use the monitor's last analyzed image if available
            screenshot_path = None
            threat_description = "Detected Threat"
            detected_text = globals().get('LAST_AI_ANALYSIS', '') or ''

            if hasattr(self, 'monitor') and self.monitor:
                # Use the most recent alert description when available
                try:
                    if hasattr(self.monitor, 'recent_alerts') and self.monitor.recent_alerts:
                        threat_description = self.monitor.recent_alerts[-1]
                except Exception:
                    pass

                # If monitor captured a last analyzed PIL image, save it to an instant_analysis file
                try:
                    last_img = getattr(self.monitor, '_last_analyzed_image', None)
                    if last_img is not None and Image is not None:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_dir = "instant_analysis"
                        if not os.path.exists(screenshot_dir):
                            os.makedirs(screenshot_dir)
                        screenshot_path = os.path.join(screenshot_dir, f"educate_{timestamp}.png")
                        try:
                            last_img.save(screenshot_path)
                        except Exception:
                            # last_img may already be a PIL Image; try converting
                            try:
                                pil_img = Image.fromarray(last_img) if hasattr(last_img, 'shape') else last_img
                                pil_img.save(screenshot_path)
                            except Exception:
                                screenshot_path = None
                except Exception:
                    screenshot_path = None

            # If we have a screenshot, open the instant analysis (deep, educational AI analysis)
            if screenshot_path and os.path.exists(screenshot_path):
                try:
                    self.show_instant_analysis(screenshot_path, threat_description, detected_text)
                    return
                except Exception as e:
                    print(f"Educate: failed to show instant analysis: {e}")

            # Fallback: no recent screenshot — open the Threat Education Library
            try:
                messagebox.showinfo("No Recent Detection", "No recent threat screenshot is available. Opening the Threat Education Library for guidance.")
            except Exception:
                pass
            try:
                self.show_threat_library()
            except Exception as e:
                print(f"Educate fallback error: {e}")

        except Exception as e:
            print(f"Educate button error: {e}")
    
    def on_test_mode_toggled(self):
        enabled = self.test_mode_var.get()
        self.monitor.test_mode = enabled
        print(f"Test mode {'enabled' if enabled else 'disabled'}")
        
    def show_threat_library(self):
        """Show comprehensive threat education library"""
        try:
            library_window = ctk.CTkToplevel(self)
            library_window.title("🎓 Securely Threat Education Library")
            library_window.geometry("700x600")
            library_window.configure(fg_color="#0d1117")
            
            # Make window stay on top
            library_window.attributes("-topmost", True)
            library_window.focus_force()
            
            # Header
            header_frame = ctk.CTkFrame(library_window, fg_color="#21262d", corner_radius=8)
            header_frame.pack(fill="x", padx=15, pady=(15, 10))
            
            title_label = ctk.CTkLabel(header_frame, text="🎓 Security Threat Education Library",
                                      font=ctk.CTkFont(size=18, weight="bold"),
                                      text_color="#58a6ff")
            title_label.pack(pady=10)
            
            subtitle_label = ctk.CTkLabel(header_frame, text="Click on any threat below to learn more",
                                         font=ctk.CTkFont(size=12),
                                         text_color="#8b949e")
            subtitle_label.pack(pady=(0, 10))
            
            # Scrollable frame for threat list
            threats_frame = ctk.CTkScrollableFrame(library_window, fg_color="#161b22")
            threats_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
            
            # Create threat buttons
            for threat_key, threat_info in THREAT_EDUCATION.items():
                threat_btn_frame = ctk.CTkFrame(threats_frame, fg_color="#21262d")
                threat_btn_frame.pack(fill="x", pady=5, padx=5)
                
                threat_btn = ctk.CTkButton(threat_btn_frame, 
                                          text=f"🛡️ {threat_info['name']}",
                                          font=ctk.CTkFont(size=13, weight="bold"),
                                          fg_color="transparent",
                                          text_color="#f0f6fc",
                                          hover_color="#30363d",
                                          anchor="w",
                                          command=lambda tk=threat_key: show_threat_education(tk))
                threat_btn.pack(fill="x", pady=5, padx=5)
                
                # Show brief description
                desc_label = ctk.CTkLabel(threat_btn_frame, 
                                         text=threat_info['description'][:100] + "...",
                                         font=ctk.CTkFont(size=10),
                                         text_color="#8b949e",
                                         anchor="w", justify="left", wraplength=600)
                desc_label.pack(fill="x", pady=(0, 5), padx=15)
            
            # Close button
            close_btn = ctk.CTkButton(library_window, text="✅ Close Library",
                                     font=ctk.CTkFont(size=12, weight="bold"),
                                     fg_color="#28a745", hover_color="#218838",
                                     command=library_window.destroy)
            close_btn.pack(pady=10)
            
            # Center the window
            library_window.update_idletasks()
            width = library_window.winfo_width()
            height = library_window.winfo_height()
            x = (library_window.winfo_screenwidth() // 2) - (width // 2)
            y = (library_window.winfo_screenheight() // 2) - (height // 2)
            library_window.geometry(f"{width}x{height}+{x}+{y}")
            
        except Exception as e:
            print(f"Error showing threat library: {e}")
    
    def on_temp_disable(self):
        # Trigger a single immediate scan (one-shot)
        try:
            # Check if program is paused - if so, resume from pause first
            if globals().get('PAUSED_FOR_SENSITIVE_PAGE', False):
                print("Resuming from pause to perform Quick Scan")
                # Clear pause flag
                try:
                    globals()['PAUSED_FOR_SENSITIVE_PAGE'] = False
                except Exception:
                    pass
                # Cancel pause countdown if active
                if hasattr(self, '_pause_countdown_id') and self._pause_countdown_id:
                    try:
                        self.after_cancel(self._pause_countdown_id)
                        self._pause_countdown_id = None
                    except Exception:
                        pass
                # Resume monitor
                if hasattr(self, 'monitor') and self.monitor:
                    try:
                        self.monitor.running.set()
                        self.monitor.start_monitor()
                    except Exception:
                        pass
            
            print("Requested single scan via UI")
            
            # Automatically turn off 24/7 monitoring if it's enabled
            if getattr(self, 'program_enabled', False):
                print("Turning off 24/7 monitoring to start Quick Scan")
                self.program_enabled = False
                try:
                    self.program_toggle_btn.configure(text="Toggle 24/7 Monitoring", 
                                                    fg_color="#28a745",  # Green for Turn On
                                                    hover_color="#218838")
                except Exception:
                    pass
                try:
                    self.status_label.configure(text="● Disabled", text_color="#8b949e")
                except Exception:
                    pass
                # Stop the continuous monitoring
                try:
                    self.pause_all()
                except Exception:
                    try:
                        if hasattr(self, 'monitor') and self.monitor:
                            self.monitor.stop_monitor()
                    except Exception:
                        pass
                try:
                    self.monitoring_var.set(False)
                except Exception:
                    pass
            
            # Automatically stop 15-minute scan if it's active
            import time
            scan_active = False
            if hasattr(self, 'monitor') and self.monitor:
                if hasattr(self.monitor, '_multi_scan_until'):
                    scan_until = getattr(self.monitor, '_multi_scan_until', 0)
                    if scan_until > time.time():
                        scan_active = True
            
            if scan_active:
                print("Stopping temporary scan to start Quick Scan")
                # Stop the 15-minute scan
                if hasattr(self, 'monitor') and self.monitor:
                    # Clear the scan timer
                    if hasattr(self.monitor, '_multi_scan_until'):
                        delattr(self.monitor, '_multi_scan_until')
                
                # Cancel countdown
                if hasattr(self, '_scan_countdown_after_id') and self._scan_countdown_after_id:
                    try:
                        self.after_cancel(self._scan_countdown_after_id)
                    except Exception:
                        pass
                    self._scan_countdown_after_id = None
                
                # Reset countdown state
                if hasattr(self, 'short_scan_seconds'):
                    self.short_scan_seconds = 0
                
                # Update button to show it can be started again
                try:
                    current_text = self.short_scan_btn.cget('text')
                    if current_text == "Stop Scan":
                        button_text = self.get_scan_button_text()
                        self.short_scan_btn.configure(text=button_text, fg_color="#0969da", hover_color="#0860ca")
                except Exception:
                    pass
            
            # Show green indicator when a one-shot scan is requested
            self.status_label.configure(text="● Scanning...", text_color="#28a745")
            # User initiated action — show compact title status as AI analysing
            try:
                self.update_ai_status("AI analysing...")
            except Exception:
                pass
            # Request monitor to perform a one-shot scan
            if hasattr(self, 'monitor') and self.monitor:
                self.monitor.request_scan_once()
        except Exception as e:
            print(f"Error requesting single scan: {e}")
        
    def update_countdown(self):
        if hasattr(self, 'temp_disable_seconds') and self.temp_disable_seconds > 0:
            minutes = self.temp_disable_seconds // 60
            seconds = self.temp_disable_seconds % 60
            self.status_label.configure(text=f"● Paused ({minutes}:{seconds:02d})", text_color="#f85149")
            self.temp_disable_seconds -= 1
            self._countdown_timer = threading.Timer(1.0, self.update_countdown)
            self._countdown_timer.daemon = True
            self._countdown_timer.start()
        else:
            # Countdown finished - re-enable everything
            self.program_enabled = True
            self.program_toggle_btn.configure(text="Turn Off", 
                                            fg_color="#dc3545",  # Red for Turn Off
                                            hover_color="#c82333")

    # --- Short-scan (15m) countdown helpers using tkinter's after() to safely update UI ---
    def start_scan_countdown(self):
        try:
            # Cancel any existing scan countdown
            if hasattr(self, '_scan_countdown_after_id') and self._scan_countdown_after_id:
                try:
                    self.after_cancel(self._scan_countdown_after_id)
                except Exception:
                    pass
            # Kick off the tick loop
            self._scan_countdown_tick()
        except Exception as e:
            print(f"Error starting scan countdown: {e}")

    def _scan_countdown_tick(self):
        try:
            secs = getattr(self, 'short_scan_seconds', 0)
            if secs > 0:
                minutes = secs // 60
                seconds = secs % 60
                # Keep indicator green while counting down
                self.status_label.configure(text=f"● Scanning ({minutes}:{seconds:02d})", text_color="#28a745")
                self.short_scan_seconds = secs - 1
                # Schedule next tick
                self._scan_countdown_after_id = self.after(1000, self._scan_countdown_tick)
            else:
                # Countdown finished — show disabled indicator (red) by default
                try:
                    self.status_label.configure(text="● Disabled", text_color="#f85149")
                except Exception:
                    pass
                self._scan_countdown_after_id = None
                
                # Get scan duration for notification
                duration_seconds = getattr(self, 'scan_duration_seconds', 5 * 60)
                minutes = duration_seconds // 60
                
                # Send notification that scan is complete
                try:
                    show_notification(
                        "Securely - Scan Complete",
                        f"Temporary scan finished ({minutes} minute{'s' if minutes != 1 else ''} completed). Monitoring stopped.",
                        duration=8
                    )
                except Exception as notif_e:
                    print(f"Notification error on scan completion: {notif_e}")
                
                # Reset button text back to original when countdown finishes
                try:
                    current_text = self.short_scan_btn.cget('text')
                    # Restore to original format based on current duration setting
                    if current_text == "Stop Scan":
                        button_text = self.get_scan_button_text()
                        self.short_scan_btn.configure(text=button_text, fg_color="#0969da", hover_color="#0860ca")
                except Exception:
                    pass
        except Exception as e:
            print(f"Scan countdown tick error: {e}")

    def on_scan_short(self):
        """Toggle temporary scan on/off (duration set in Advanced settings)"""
        try:
            import time
            
            # Check if program is paused - if so, resume from pause first
            if globals().get('PAUSED_FOR_SENSITIVE_PAGE', False):
                print("Resuming from pause to perform temporary scan")
                # Clear pause flag
                try:
                    globals()['PAUSED_FOR_SENSITIVE_PAGE'] = False
                except Exception:
                    pass
                # Cancel pause countdown if active
                if hasattr(self, '_pause_countdown_id') and self._pause_countdown_id:
                    try:
                        self.after_cancel(self._pause_countdown_id)
                        self._pause_countdown_id = None
                    except Exception:
                        pass
                # Resume monitor
                if hasattr(self, 'monitor') and self.monitor:
                    try:
                        self.monitor.running.set()
                        self.monitor.start_monitor()
                    except Exception:
                        pass
            
            # Check if a temporary scan is currently running
            scan_active = False
            if hasattr(self, 'monitor') and self.monitor:
                if hasattr(self.monitor, '_multi_scan_until'):
                    scan_until = getattr(self.monitor, '_multi_scan_until', 0)
                    if scan_until > time.time():
                        scan_active = True
            
            if scan_active:
                # Stop the scan
                duration_seconds = getattr(self, 'scan_duration_seconds', 5 * 60)
                minutes = duration_seconds // 60
                print(f"Stopping temporary scan ({minutes} minutes) via UI")
                
                # Stop the monitor
                if hasattr(self, 'monitor') and self.monitor:
                    self.monitor.stop_monitor()
                    # Clear the scan timer
                    if hasattr(self.monitor, '_multi_scan_until'):
                        delattr(self.monitor, '_multi_scan_until')
                
                # Cancel countdown
                if hasattr(self, '_scan_countdown_after_id') and self._scan_countdown_after_id:
                    try:
                        self.after_cancel(self._scan_countdown_after_id)
                    except Exception:
                        pass
                    self._scan_countdown_after_id = None
                
                # Reset countdown state
                if hasattr(self, 'short_scan_seconds'):
                    self.short_scan_seconds = 0
                
                # Update UI to show stopped state
                try:
                    self.status_label.configure(text="● Disabled", text_color="#8b949e")
                except Exception:
                    pass
                
                # Update button to show it can be started again
                try:
                    current_text = self.short_scan_btn.cget('text')
                    # Update to match the current duration setting
                    if current_text == "Stop Scan":
                        button_text = self.get_scan_button_text()
                        self.short_scan_btn.configure(text=button_text, fg_color="#0969da", hover_color="#0860ca")
                except Exception:
                    pass
            else:
                # Start the scan
                seconds = getattr(self, 'scan_duration_seconds', 5 * 60)
                minutes = seconds // 60
                print(f"Requested temporary scan for {seconds}s ({minutes} minutes) via UI")
                
                # Automatically turn off 24/7 monitoring if it's enabled
                if getattr(self, 'program_enabled', False):
                    print("Turning off 24/7 monitoring to start temporary scan")
                    self.program_enabled = False
                    try:
                        self.program_toggle_btn.configure(text="Toggle 24/7 Monitoring", 
                                                        fg_color="#28a745",  # Green for Turn On
                                                        hover_color="#218838")
                    except Exception:
                        pass
                    try:
                        self.status_label.configure(text="● Disabled", text_color="#8b949e")
                    except Exception:
                        pass
                    # Stop the continuous monitoring
                    try:
                        self.pause_all()
                    except Exception:
                        try:
                            if hasattr(self, 'monitor') and self.monitor:
                                self.monitor.stop_monitor()
                        except Exception:
                            pass
                    try:
                        self.monitoring_var.set(False)
                    except Exception:
                        pass
                
            # Set up countdown state and start the UI countdown (green indicator)
            self.short_scan_seconds = seconds
            try:
                self.start_scan_countdown()
                # User initiated action — show compact title status as AI analysing
                try:
                    self.update_ai_status("AI analysing...")
                except Exception:
                    pass
            except Exception:
                # Fallback initial text if countdown cannot start
                minutes = seconds // 60
                self.status_label.configure(text=f"● Scanning ({minutes}:00)", text_color="#28a745")
                
            # Request monitor to run for the duration
            if hasattr(self, 'monitor') and self.monitor:
                self.monitor.request_scan_for(seconds)
                
                # Update button to show it can be stopped
                try:
                    self.short_scan_btn.configure(text="Stop Scan", fg_color="#d73a49", hover_color="#cb2431")
                except Exception:
                    pass
                
        except Exception as e:
            print(f"Error toggling short scan: {e}")
    
    def open_console_viewer(self):
        """Open a window showing all console/terminal output"""
        try:
            # Create console viewer window
            console_window = ctk.CTkToplevel(self)
            console_window.title("Securely - Console Log Viewer")
            console_window.geometry("900x600")
            console_window.configure(fg_color="#0d1117")
            
            # Make window stay on top
            console_window.attributes("-topmost", True)
            console_window.focus_force()
            
            # Header
            header_frame = ctk.CTkFrame(console_window, fg_color="#21262d", corner_radius=8)
            header_frame.pack(fill="x", padx=15, pady=(15, 10))
            
            title_label = ctk.CTkLabel(header_frame, text="🖥️ Console Log Viewer",
                                      font=ctk.CTkFont(size=18, weight="bold"),
                                      text_color="#58a6ff")
            title_label.pack(side="left", pady=10, padx=10)
            
            # Status indicator
            status_label = ctk.CTkLabel(header_frame, text="● LIVE",
                                       font=ctk.CTkFont(size=11, weight="bold"),
                                       text_color="#28a745")
            status_label.pack(side="right", pady=10, padx=10)
            
            # Button frame
            button_frame = ctk.CTkFrame(console_window, fg_color="transparent")
            button_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            # Console text area with dark terminal theme
            console_text = ctk.CTkTextbox(console_window, 
                                         fg_color="#161b22",
                                         text_color="#c9d1d9",
                                         font=ctk.CTkFont(family="Consolas", size=10),
                                         wrap="word")
            console_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))
            
            # Insert current console log
            global console_logger
            log_content = console_logger.get_log()
            console_text.insert("1.0", log_content if log_content else "[No console output yet]")
            console_text.configure(state="disabled")  # Make read-only
            
            # Auto-scroll to bottom
            console_text.see("end")
            
            # Refresh button
            def refresh_log():
                console_text.configure(state="normal")
                console_text.delete("1.0", "end")
                log_content = console_logger.get_log()
                console_text.insert("1.0", log_content if log_content else "[No console output yet]")
                console_text.configure(state="disabled")
                console_text.see("end")
                status_label.configure(text="● REFRESHED", text_color="#58a6ff")
                console_window.after(1000, lambda: status_label.configure(text="● LIVE", text_color="#28a745"))
            
            refresh_btn = ctk.CTkButton(button_frame, text="🔄 Refresh",
                                       font=ctk.CTkFont(size=11, weight="bold"),
                                       fg_color="#238636", hover_color="#2ea043",
                                       command=refresh_log)
            refresh_btn.pack(side="left", padx=5)
            
            # Clear log button
            def clear_log():
                global console_logger
                console_logger.log = []
                refresh_log()
                status_label.configure(text="● CLEARED", text_color="#d73a49")
                console_window.after(1000, lambda: status_label.configure(text="● LIVE", text_color="#28a745"))
            
            clear_btn = ctk.CTkButton(button_frame, text="🗑️ Clear Log",
                                     font=ctk.CTkFont(size=11, weight="bold"),
                                     fg_color="#d73a49", hover_color="#cb2431",
                                     command=clear_log)
            clear_btn.pack(side="left", padx=5)
            
            # Copy to clipboard button
            def copy_to_clipboard():
                log_content = console_logger.get_log()
                console_window.clipboard_clear()
                console_window.clipboard_append(log_content)
                status_label.configure(text="● COPIED", text_color="#58a6ff")
                console_window.after(1000, lambda: status_label.configure(text="● LIVE", text_color="#28a745"))
            
            copy_btn = ctk.CTkButton(button_frame, text="📋 Copy to Clipboard",
                                    font=ctk.CTkFont(size=11, weight="bold"),
                                    fg_color="#0969da", hover_color="#0860ca",
                                    command=copy_to_clipboard)
            copy_btn.pack(side="left", padx=5)
            
            # Auto-refresh toggle
            auto_refresh_enabled = [True]  # Use list to allow modification in nested function
            
            def toggle_auto_refresh():
                auto_refresh_enabled[0] = not auto_refresh_enabled[0]
                if auto_refresh_enabled[0]:
                    auto_refresh_btn.configure(text="⏸️ Pause Auto-Refresh")
                    status_label.configure(text="● LIVE", text_color="#28a745")
                else:
                    auto_refresh_btn.configure(text="▶️ Resume Auto-Refresh")
                    status_label.configure(text="● PAUSED", text_color="#f85149")
            
            auto_refresh_btn = ctk.CTkButton(button_frame, text="⏸️ Pause Auto-Refresh",
                                            font=ctk.CTkFont(size=11, weight="bold"),
                                            fg_color="#6e40aa", hover_color="#8b5cf6",
                                            command=toggle_auto_refresh)
            auto_refresh_btn.pack(side="right", padx=5)
            
            # Auto-refresh every 2 seconds
            def auto_refresh():
                if auto_refresh_enabled[0]:
                    refresh_log()
                console_window.after(2000, auto_refresh)  # Refresh every 2 seconds
            
            # Start auto-refresh
            console_window.after(2000, auto_refresh)
            
            # Center the window
            console_window.update_idletasks()
            width = console_window.winfo_width()
            height = console_window.winfo_height()
            x = (console_window.winfo_screenwidth() // 2) - (width // 2)
            y = (console_window.winfo_screenheight() // 2) - (height // 2)
            console_window.geometry(f"{width}x{height}+{x}+{y}")
            
        except Exception as e:
            messagebox.showerror("Console Viewer Error", f"Failed to open console viewer: {e}")
            self.monitoring_var.set(True)
            self.status_label.configure(text="● Active", text_color="#58a6ff")
            
            # Re-enable the temp disable button
            self.temp_disable_btn.configure(text="2m", state="normal")
            
            # Restart monitoring only if not already running
            if not self.monitor.running.is_set():
                self.monitor.start_monitor()
            
            # Clear countdown variables
            if hasattr(self, 'temp_disable_seconds'):
                delattr(self, 'temp_disable_seconds')
        
    def on_closing(self):
        # Properly stop the monitor thread and exit
        if hasattr(self, 'monitor'):
            self.monitor.close_overlay()  # Close any open overlay
            self.monitor.stop_monitor()
        if hasattr(self, '_temp_timer'):
            try:
                self._temp_timer.cancel()
            except Exception:
                pass
        if hasattr(self, '_countdown_timer'):
            try:
                self._countdown_timer.cancel()
            except Exception:
                pass
        self.destroy()

    def pause_all(self):
        """Stop monitoring, cancel timers, and clear overlays safely."""
        try:
            # Stop monitor thread and close overlays
            if hasattr(self, 'monitor') and self.monitor:
                try:
                    self.monitor.close_overlay()
                except Exception:
                    pass
                try:
                    self.monitor.stop_monitor()
                except Exception:
                    pass

                # Remove any pending one-shot or multi-scan requests
                try:
                    if hasattr(self.monitor, '_one_shot'):
                        delattr(self.monitor, '_one_shot')
                except Exception:
                    pass
                try:
                    if hasattr(self.monitor, '_multi_scan_until'):
                        delattr(self.monitor, '_multi_scan_until')
                except Exception:
                    pass
            # Cancel any UI scan countdown
            try:
                if hasattr(self, '_scan_countdown_after_id') and self._scan_countdown_after_id:
                    try:
                        self.after_cancel(self._scan_countdown_after_id)
                    except Exception:
                        pass
                    self._scan_countdown_after_id = None
                if hasattr(self, 'short_scan_seconds'):
                    self.short_scan_seconds = 0
            except Exception:
                pass

            # Cancel UI timers if present
            try:
                if hasattr(self, '_temp_timer') and self._temp_timer is not None:
                    self._temp_timer.cancel()
                    delattr(self, '_temp_timer')
            except Exception:
                pass
            try:
                if hasattr(self, '_countdown_timer') and self._countdown_timer is not None:
                    self._countdown_timer.cancel()
                    delattr(self, '_countdown_timer')
            except Exception:
                pass

            # Clear any state that may trigger background work
            try:
                globals()['PAUSED_FOR_SENSITIVE_PAGE'] = False
            except Exception:
                pass

            # Update UI state to paused
            try:
                self.program_enabled = False
                try:
                    self.program_toggle_btn.configure(text="Toggle 24/7 Monitoring", fg_color="#28a745", hover_color="#218838")
                except Exception:
                    pass
                try:
                    self.status_label.configure(text="● Disabled", text_color="#f85149")
                except Exception:
                    pass
                try:
                    if hasattr(self, 'monitoring_var'):
                        self.monitoring_var.set(False)
                except Exception:
                    pass
            except Exception:
                pass
            except Exception:
                pass
        except Exception as e:
            print(f"Error pausing operations: {e}")
    
    def minimize_window(self):
        """Minimize the window to taskbar"""
        try:
            # When overrideredirect is set, we need to use Windows API directly to minimize
            import ctypes
            
            # Get the window handle
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if hwnd:
                # Ensure window appears in taskbar
                GWL_EXSTYLE = -20
                WS_EX_APPWINDOW = 0x00040000
                WS_EX_TOOLWINDOW = 0x00000080
                
                # Get current style
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                # Remove TOOLWINDOW flag and ensure APPWINDOW flag is set
                style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
                
                # Minimize using Windows API (works even with overrideredirect)
                SW_MINIMIZE = 6
                ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)
            else:
                # Fallback: temporarily remove overrideredirect, minimize, then restore
                try:
                    self.overrideredirect(False)
                    self.iconify()
                    # Restore overrideredirect after a brief delay
                    self.after(100, lambda: self.overrideredirect(True))
                except Exception:
                    # If all else fails, just hide it
                    self.withdraw()
                    
        except Exception as e:
            print(f"Minimize error: {e}")
            # Fallback: just hide the window
            try:
                self.withdraw()
            except Exception:
                pass
    
    def toggle_window_size(self):
        """Toggle between normal and 2x enlarged window size"""
        try:
            if not self.is_enlarged:
                # Enlarge to 2x size — compute new size and center on previous center to avoid jumpiness
                try:
                    scale = 2.0
                    new_width = max(300, int(self.original_size[0] * scale))
                    new_height = max(260, int(self.original_size[1] * scale))

                    # Save current position (but always use original_size for dimensions when restoring)
                    # We don't need to save dimensions since we always restore to original_size
                    try:
                        self._prev_position = (self.winfo_x(), self.winfo_y())
                    except Exception:
                        self._prev_position = None

                    # Compute current center
                    current_x = self.winfo_x()
                    current_y = self.winfo_y()
                    current_w = self.winfo_width() or self.original_size[0]
                    current_h = self.winfo_height() or self.original_size[1]
                    center_x = current_x + current_w // 2
                    center_y = current_y + current_h // 2

                    # New top-left to keep centered
                    new_x = max(0, center_x - new_width // 2)
                    new_y = max(0, center_y - new_height // 2)

                    # Safely apply geometry with brief withdraw/deiconify to avoid white flash on borderless window
                    try:
                        self.withdraw()
                        self.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")
                        self.update_idletasks()
                        self.deiconify()
                    except Exception:
                        # Fallback: set geometry directly
                        self.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")

                    # Scale UI elements using computed factor
                    try:
                        self._scale_ui_elements(scale)
                    except Exception:
                        pass

                    # Update resizer appearance
                    try:
                        self.resizer_btn.configure(text="⛶", hover_color="#f85149")
                    except Exception:
                        pass

                    self.is_enlarged = True
                except Exception as e:
                    print(f"Resize enlarge error: {e}")
            else:
                # Return to original size - always use the fixed original_size, not saved geometry
                try:
                    # Always restore to the exact original size (220x200)
                    new_width = self.original_size[0]
                    new_height = self.original_size[1]

                    # Compute current center to keep window centered when shrinking
                    current_x = self.winfo_x()
                    current_y = self.winfo_y()
                    current_w = self.winfo_width() or new_width
                    current_h = self.winfo_height() or new_height
                    center_x = current_x + current_w // 2
                    center_y = current_y + current_h // 2

                    # New position to keep centered
                    new_x = max(0, center_x - new_width // 2)
                    new_y = max(0, center_y - new_height // 2)

                    try:
                        self.withdraw()
                        self.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")
                        self.update_idletasks()
                        self.deiconify()
                    except Exception:
                        self.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")

                    # Reset UI elements to normal scale
                    try:
                        self._scale_ui_elements(1.0)
                    except Exception:
                        pass

                    try:
                        self.resizer_btn.configure(text="⛶", hover_color="#58a6ff")
                    except Exception:
                        pass

                    # Clear saved position after restore
                    try:
                        if hasattr(self, '_prev_position'):
                            self._prev_position = None
                    except Exception:
                        pass

                    self.is_enlarged = False
                except Exception as e:
                    print(f"Resize shrink error: {e}")
        except Exception as e:
            print(f"Resize error: {e}")
    
    def _scale_ui_elements(self, scale_factor):
        """Scale UI elements proportionally"""
        try:
            # Scale fonts
            base_sizes = {
                'title': 10,
                'normal': 11,
                'small': 9,
                'button': 10
            }
            
            # Update title bar font
            if hasattr(self, 'title_label'):
                new_size = int(base_sizes['title'] * scale_factor)
                self.title_label.configure(font=ctk.CTkFont(size=new_size, weight="bold"))
            
            # Scale title AI status label (Screen secure/AI analysing)
            if hasattr(self, 'title_ai_label'):
                # Base size is 8, scale it proportionally
                base_ai_size = 8
                new_ai_size = int(base_ai_size * scale_factor)
                try:
                    current_text = self.title_ai_label.cget('text')
                    current_color = self.title_ai_label.cget('text_color')
                    self.title_ai_label.configure(font=ctk.CTkFont(size=new_ai_size))
                    # Preserve text and color
                    self.title_ai_label.configure(text=current_text, text_color=current_color)
                except Exception:
                    pass
            
            # Scale button fonts in title bar
            button_size = int(base_sizes['button'] * scale_factor)
            if hasattr(self, 'exit_btn'):
                self.exit_btn.configure(font=ctk.CTkFont(size=button_size, weight="bold"))
            if hasattr(self, 'minimize_btn'):
                self.minimize_btn.configure(font=ctk.CTkFont(size=button_size, weight="bold"))
            if hasattr(self, 'resizer_btn'):
                self.resizer_btn.configure(font=ctk.CTkFont(size=button_size, weight="bold"))
            
            # Scale tab view and content fonts
            if hasattr(self, 'tab_view'):
                # Update tab font size
                tab_font_size = int(base_sizes['small'] * scale_factor)
                try:
                    # Attempt to update the segmented control font (internal attribute)
                    seg = getattr(self.tab_view, '_segmented_button', None)
                    if seg is not None:
                        try:
                            seg.configure(font=ctk.CTkFont(size=tab_font_size))
                        except Exception:
                            pass
                except Exception:
                    pass

                # Scale dashboard elements
                if hasattr(self, 'status_label'):
                    status_size = int(base_sizes['normal'] * scale_factor)
                    self.status_label.configure(font=ctk.CTkFont(size=status_size, weight="bold"))
                
                if hasattr(self, 'ai_status_label'):
                    ai_size = int(base_sizes['small'] * scale_factor)
                    self.ai_status_label.configure(font=ctk.CTkFont(size=ai_size))
                
                # Scale buttons using stored base metrics where available; restore exact base when scale==1.0
                try:
                    btns = [
                        ('temp_disable_btn', 'temp_disable_btn'),
                        ('short_scan_btn', 'short_scan_btn'),
                        ('program_toggle_btn', 'program_toggle_btn'),
                        ('test_notification_btn', 'test_notification_btn'),
                        ('console_viewer_btn', 'console_viewer_btn')
                    ]
                    for attr_name, _ in btns:
                        try:
                            btn = getattr(self, attr_name, None)
                            if btn is None:
                                continue
                            base_f = getattr(btn, '_base_font', base_sizes['button'])
                            base_w = getattr(btn, '_base_width', None)
                            if scale_factor == 1.0:
                                # Restore original exact metrics
                                try:
                                    btn.configure(font=ctk.CTkFont(size=int(base_f)))
                                except Exception:
                                    pass
                                if base_w is not None:
                                    try:
                                        btn.configure(width=int(base_w))
                                    except Exception:
                                        pass
                            else:
                                new_font = int(max(8, base_f * scale_factor))
                                try:
                                    btn.configure(font=ctk.CTkFont(size=new_font))
                                except Exception:
                                    pass
                                if base_w is not None:
                                    try:
                                        btn.configure(width=max(40, int(base_w * scale_factor)))
                                    except Exception:
                                        pass
                        except Exception:
                            continue
                except Exception:
                    pass

            # Resize title icon if we saved an original image
            try:
                if hasattr(self, '_original_icon_img') and Image is not None:
                    # Base icon was 14x14 — scale accordingly
                    base_icon_size = 14
                    new_size = max(10, int(base_icon_size * scale_factor))
                    try:
                        resized = self._original_icon_img.resize((new_size, new_size), Image.Resampling.LANCZOS)
                    except Exception:
                        try:
                            resized = self._original_icon_img.resize((new_size, new_size))
                        except Exception:
                            resized = None
                    if resized is not None:
                        try:
                            self.icon_photo = ImageTk.PhotoImage(resized)
                            try:
                                self.icon_label.configure(image=self.icon_photo)
                            except Exception:
                                pass
                        except Exception:
                            pass
            except Exception:
                pass

            # Scale audit header buttons if present
            try:
                if hasattr(self, 'quick_scan_btn'):
                    try:
                        base_f = getattr(self.quick_scan_btn, '_base_font', base_sizes['button'])
                        base_w = getattr(self.quick_scan_btn, '_base_width', 100)
                        q_font = int(max(8, base_f * scale_factor))
                        self.quick_scan_btn.configure(font=ctk.CTkFont(size=q_font))
                        try:
                            self.quick_scan_btn.configure(width=max(60, int(base_w * scale_factor)))
                        except Exception:
                            pass
                    except Exception:
                        pass
                if hasattr(self, 'clear_btn'):
                    try:
                        base_f = getattr(self.clear_btn, '_base_font', base_sizes['button'] - 1)
                        base_w = getattr(self.clear_btn, '_base_width', 80)
                        c_font = int(max(8, base_f * scale_factor))
                        self.clear_btn.configure(font=ctk.CTkFont(size=c_font))
                        try:
                            self.clear_btn.configure(width=max(48, int(base_w * scale_factor)))
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass
            
            # Force UI update
            self.update_idletasks()

            # Rebuild audit log to apply new sizes to dynamic elements
            try:
                if hasattr(self, 'tab_view') and self.tab_view.get() == "📋":
                    # reload audit content so buttons/cards use updated fonts
                    self.load_audit_log()
            except Exception:
                pass
            
        except Exception as e:
            print(f"UI scaling error: {e}")
    
    def add_simple_tooltips(self):
        """Add working tooltips to tabs"""
        try:
            print("Setting up tooltips...")
            self.tooltip_window = None
            # Ensure we have lifecycle IDs initialized
            self._tooltip_check_id = None
            self._tooltip_life_id = None
            tooltips = {
                "📊": "Dashboard",
                "⚙️": "Settings", 
                "📋": "Audit Log",
                "ℹ️": "Credits"
            }
            
            def create_tooltip(widget, text):
                """Create a minimal in-window tooltip label on hover."""
                def show_tooltip(event):
                    try:
                        # Remove existing in-window tooltip if any
                        try:
                            if hasattr(self, '_tooltip_label') and self._tooltip_label:
                                self._tooltip_label.destroy()
                        except Exception:
                            pass

                        # Compute position relative to main window
                        try:
                            rx = widget.winfo_rootx() - self.winfo_rootx()
                            ry = widget.winfo_rooty() - self.winfo_rooty()
                        except Exception:
                            rx = widget.winfo_x()
                            ry = widget.winfo_y()

                        x = rx + max(0, widget.winfo_width() // 2 - 40)
                        y = ry - 24

                        # Create a slightly larger, padded label inside the main window
                        lbl = ctk.CTkLabel(self, text=text,
                                          font=ctk.CTkFont(size=10),
                                          text_color="#f0f6fc",
                                          fg_color="#21262d",
                                          corner_radius=5,
                                          padx=8, pady=4,
                                          wraplength=240)
                        # Slightly adjust position to account for larger size
                        lbl.place(x=x - 8, y=y - 4)
                        self._tooltip_label = lbl
                    except Exception as e:
                        print(f"Show tooltip error: {e}")

                def hide_tooltip(event):
                    try:
                        if hasattr(self, '_tooltip_label') and self._tooltip_label:
                            try:
                                self._tooltip_label.destroy()
                            except Exception:
                                pass
                            self._tooltip_label = None
                    except Exception as e:
                        print(f"Hide tooltip error: {e}")

                widget.bind("<Enter>", show_tooltip)
                widget.bind("<Leave>", hide_tooltip)
            
            # Wait a moment for UI to be ready, then find and bind to tab buttons
            def setup_after_delay():
                try:
                    # Access the segmented button that contains the tab buttons and bind per-button tooltips
                    segmented_button = getattr(self.tab_view, '_segmented_button', None)
                    tooltip_texts = ["Dashboard", "Settings", "Audit Log", "Credits"]
                    if segmented_button:
                        try:
                            children = segmented_button.winfo_children()
                            for i, button in enumerate(children):
                                if i < len(tooltip_texts):
                                    create_tooltip(button, tooltip_texts[i])
                        except Exception as e:
                            print(f"Tooltip binding error: {e}")
                    else:
                        # Fallback: try to find tab header buttons directly in the tab view
                        try:
                            children = self.tab_view.winfo_children()
                            idx = 0
                            for child in children:
                                if idx >= len(tooltip_texts):
                                    break
                                try:
                                    create_tooltip(child, tooltip_texts[idx])
                                    idx += 1
                                except Exception:
                                    continue
                        except Exception as e:
                            print(f"Tooltip fallback error: {e}")
                        
                except Exception as e:
                    print(f"Delayed setup error: {e}")
            
            # Schedule the setup after UI is ready
            self.after(500, setup_after_delay)
            
        except Exception as e:
            print(f"Tooltip setup error: {e}")
        
    def start_drag(self, event):
        self.x = event.x
        self.y = event.y
        # Ensure tooltips are removed when starting a drag to avoid leaving copies/trails
        try:
            try:
                if hasattr(self, '_tooltip_check_id') and self._tooltip_check_id:
                    self.after_cancel(self._tooltip_check_id)
            except Exception:
                pass
            try:
                if hasattr(self, '_tooltip_anim_id') and self._tooltip_anim_id:
                    self.after_cancel(self._tooltip_anim_id)
            except Exception:
                pass
            try:
                if hasattr(self, '_tooltip_life_id') and self._tooltip_life_id:
                    self.after_cancel(self._tooltip_life_id)
                    self._tooltip_life_id = None
            except Exception:
                pass
            try:
                if hasattr(self, '_tooltip_hide_anim_id') and self._tooltip_hide_anim_id:
                    self.after_cancel(self._tooltip_hide_anim_id)
            except Exception:
                pass
            if hasattr(self, 'tooltip_window') and self.tooltip_window:
                try:
                    self.tooltip_window.destroy()
                except Exception:
                    pass
                self.tooltip_window = None
        except Exception:
            pass
        
    def on_drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        
        # Use the correct window size based on current state
        if hasattr(self, 'is_enlarged') and self.is_enlarged:
            # Use enlarged size
            width = self.original_size[0] * 2
            height = self.original_size[1] * 2
        else:
            # Use original size
            width = self.original_size[0]
            height = self.original_size[1]
        
        self.geometry(f"{width}x{height}+{x}+{y}")
        # Remove any tooltip immediately after moving the window to prevent trails
        try:
            try:
                if hasattr(self, '_tooltip_check_id') and self._tooltip_check_id:
                    self.after_cancel(self._tooltip_check_id)
                    self._tooltip_check_id = None
            except Exception:
                pass
            try:
                if hasattr(self, '_tooltip_anim_id') and self._tooltip_anim_id:
                    self.after_cancel(self._tooltip_anim_id)
                    self._tooltip_anim_id = None
            except Exception:
                pass
            try:
                if hasattr(self, '_tooltip_life_id') and self._tooltip_life_id:
                    self.after_cancel(self._tooltip_life_id)
                    self._tooltip_life_id = None
            except Exception:
                pass
            try:
                if hasattr(self, '_tooltip_hide_anim_id') and self._tooltip_hide_anim_id:
                    self.after_cancel(self._tooltip_hide_anim_id)
                    self._tooltip_hide_anim_id = None
            except Exception:
                pass
            if hasattr(self, 'tooltip_window') and self.tooltip_window:
                try:
                    self.tooltip_window.destroy()
                except Exception:
                    pass
                self.tooltip_window = None
        except Exception:
            pass

# --- entry point ---
if __name__ == "__main__":
    # Display startup banner with system information
    audit_log("="*80, 'INIT', use_typewriter=False)
    audit_log("SECURELY - Real-Time Cybersecurity Monitoring", 'INIT', use_typewriter=False)
    audit_log("="*80, 'INIT', use_typewriter=False)
    audit_log(f"System Status:", 'INIT', use_typewriter=False)
    audit_log(f"  Tesseract OCR: {'Available' if TESSERACT_AVAILABLE else 'Not Available'}", 'INIT', use_typewriter=False)
    audit_log(f"  Groq API: {'Available' if groq_available else 'Not Available'}", 'INIT', use_typewriter=False)
    audit_log(f"  API Keys Configured: {len(GROQ_API_KEYS)}", 'INIT', use_typewriter=False)
    audit_log(f"  Active API Clients: {sum(1 for k, v in _groq_clients.items() if v is not None)}/{len(GROQ_API_KEYS)}", 'INIT', use_typewriter=False)
    audit_log("="*80, 'INIT', use_typewriter=False)
    
    audit_log("Securely application starting", 'SUCCESS')
    audit_log(f"Configuration: {len(GROQ_API_KEYS)} API keys, {sum(1 for k, v in _groq_clients.items() if v is not None)} active clients", 'INFO')
    
    # Start ASCII art display thread (non-blocking, runs in background)
    app = MainWindow()
    
    # Display API stats after a short delay (once UI is initialized)
    def show_startup_stats():
        time.sleep(1)  # Wait for UI to initialize
        display_api_stats()
    
    threading.Thread(target=show_startup_stats, daemon=True).start()
    
    app.mainloop()