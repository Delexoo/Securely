import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import os
from datetime import datetime

APP_VERSION = "v2.1"
LOG_FILE = "securely_log.txt"


class SecurelyUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Securely")
        self.geometry("640x420")
        self.configure(bg="#0d1117")

        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=12, pady=12)

        self._build_dashboard()
        self._build_audit()
        self._build_credits()

        footer = tk.Label(self, text=f"© Securely — {APP_VERSION}", bg='#0d1117', fg='#6e7681')
        footer.pack(side='bottom', pady=(0,8))

    def _build_dashboard(self):
        frame = tk.Frame(self.notebook, bg='#0d1117')
        self.notebook.add(frame, text='Dashboard')

        tk.Label(frame, text='Securely — UI Only', bg='#0d1117', fg='#58a6ff', font=('Segoe UI', 16, 'bold')).pack(anchor='w', pady=(6,8), padx=6)
        tk.Label(frame, text='A lightweight UI for testing. AI and monitoring are removed in this build.',
                 bg='#0d1117', fg='#8b949e', font=('Segoe UI', 11), wraplength=580, justify='left').pack(anchor='w', padx=6)

        btn_row = tk.Frame(frame, bg='#0d1117')
        btn_row.pack(pady=18)

        tk.Button(btn_row, text='Quick Scan', width=14, command=self._quick_scan).grid(row=0, column=0, padx=6)
        tk.Button(btn_row, text='Timed Scan (3s)', width=14, command=self._timed_scan).grid(row=0, column=1, padx=6)
        tk.Button(btn_row, text='View Audit Log', width=14, command=lambda: self.notebook.select(self.audit_frame)).grid(row=0, column=2, padx=6)

    def _build_audit(self):
        self.audit_frame = tk.Frame(self.notebook, bg='#0d1117')
        self.notebook.add(self.audit_frame, text='Audit Log')

        tk.Label(self.audit_frame, text='Audit Log (latest 200 lines)', bg='#0d1117', fg='#58a6ff', font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(8,4), padx=8)

        btns = tk.Frame(self.audit_frame, bg='#0d1117')
        btns.pack(fill='x', padx=8)
        tk.Button(btns, text='Refresh', width=10, command=self.load_audit_log).pack(side='left')
        tk.Button(btns, text='Clear Log', width=10, command=self.clear_audit_log).pack(side='left', padx=(6,0))

        self.log_text = tk.Text(self.audit_frame, height=18, wrap='word', bg='#0d1117', fg='#c9d1d9')
        self.log_text.pack(fill='both', expand=True, padx=8, pady=(8,12))
        self.log_text.configure(state='disabled')

        self.load_audit_log()

    def _build_credits(self):
        frame = tk.Frame(self.notebook, bg='#0d1117')
        self.notebook.add(frame, text='Credits')

        pad = {'padx':10, 'pady':4}
        tk.Label(frame, text='Development Team', bg='#0d1117', fg='#f0f6fc', font=('Segoe UI', 14, 'bold')).pack(anchor='w', **pad)
        tk.Label(frame, text='• @Delexo — Lead Development', bg='#0d1117', fg='#8b949e', font=('Segoe UI', 11)).pack(anchor='w', **pad)
        tk.Label(frame, text='• @Mai — Product Strategy', bg='#0d1117', fg='#8b949e', font=('Segoe UI', 11)).pack(anchor='w', **pad)

        tk.Label(frame, text='Special Thanks', bg='#0d1117', fg='#f0f6fc', font=('Segoe UI', 14, 'bold')).pack(anchor='w', pady=(10,4), padx=10)
        tk.Label(frame, text='• @Priscilla — Guidance & Support', bg='#0d1117', fg='#8b949e', font=('Segoe UI', 11)).pack(anchor='w', padx=10)
        tk.Label(frame, text='• @Derek — Quality Feedback', bg='#0d1117', fg='#8b949e', font=('Segoe UI', 11)).pack(anchor='w', padx=10)
        tk.Label(frame, text='• @CSUSM Community — Collaboration', bg='#0d1117', fg='#8b949e', font=('Segoe UI', 11)).pack(anchor='w', padx=10)

        tk.Label(frame, text='Program Features', bg='#0d1117', fg='#f0f6fc', font=('Segoe UI', 14, 'bold')).pack(anchor='w', pady=(10,4), padx=10)
        tk.Label(frame, text='• Real‑time monitoring (UI only)', bg='#0d1117', fg='#8b949e', font=('Segoe UI', 11)).pack(anchor='w', padx=10)
        tk.Label(frame, text='• On‑demand deep analysis (stubbed)', bg='#0d1117', fg='#8b949e', font=('Segoe UI', 11)).pack(anchor='w', padx=10)

        tk.Label(frame, text='Built With', bg='#0d1117', fg='#f0f6fc', font=('Segoe UI', 14, 'bold')).pack(anchor='w', pady=(10,4), padx=10)
        tk.Label(frame, text='• Python', bg='#0d1117', fg='#8b949e', font=('Segoe UI', 11)).pack(anchor='w', padx=10)
        tk.Label(frame, text='• Google Gemini API (removed)', bg='#0d1117', fg='#8b949e', font=('Segoe UI', 11)).pack(anchor='w', padx=10)
        tk.Label(frame, text='• Tesseract OCR (removed)', bg='#0d1117', fg='#8b949e', font=('Segoe UI', 11)).pack(anchor='w', padx=10)

        btn_frame = tk.Frame(frame, bg='#0d1117')
        btn_frame.pack(pady=12)
        tk.Button(btn_frame, text='Learn More', width=14, command=self.open_learn_more).pack()

    def _quick_scan(self):
        ts = datetime.now().strftime('%m/%d/%Y %I:%M %p').lstrip('0')
        line = f"[{ts}] Quick scan requested (UI-only)."
        self._append_log(line)
        messagebox.showinfo('Quick Scan', 'Quick scan requested (UI-only).')

    def _timed_scan(self):
        ts = datetime.now().strftime('%m/%d/%Y %I:%M %p').lstrip('0')
        line = f"[{ts}] Timed scan (3s) requested (UI-only)."
        self._append_log(line)
        messagebox.showinfo('Timed Scan', 'Timed scan requested (UI-only).')

    def load_audit_log(self):
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    lines = f.read().splitlines()[-200:]
                content = '\n'.join(lines)
            else:
                content = 'No security events logged.'
            self.log_text.configure(state='normal')
            self.log_text.delete('1.0', 'end')
            self.log_text.insert('1.0', content)
            self.log_text.configure(state='disabled')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to read log: {e}')

    def _append_log(self, line):
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
            self.load_audit_log()
        except Exception as e:
            print('Log append failed:', e)

    def clear_audit_log(self):
        try:
            if os.path.exists(LOG_FILE):
                os.remove(LOG_FILE)
            self.load_audit_log()
            messagebox.showinfo('Audit Log', 'Audit log cleared.')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to clear log: {e}')

    def open_learn_more(self):
        webbrowser.open('https://delexoo.github.io/Securely/')


if __name__ == '__main__':
    app = SecurelyUI()
    app.mainloop()


💡 What you can do:
• Wait about 1 minute for the quota to reset
• Continue using keyword-based detection (still active)
• Upgrade your API plan at: https://ai.google.dev/pricing

✅ Your security monitoring is still running with keyword detection."""
        else:
            error_msg = f"""⚠️ AI SERVICE ERROR ({response.status_code})

❌ Unable to connect to AI analysis service.

💡 Possible causes:
• Network connectivity issues
• API service temporarily unavailable
• Invalid API credentials

✅ Keyword-based detection is still active and protecting you."""
            return error_msg
            
    except Exception as e:
        return f"""⚠️ ANALYSIS ERROR

❌ {str(e)}

✅ Keyword-based detection is still active and protecting you."""

    return "Analysis unavailable."

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

def capture_training_screenshot(threat_type, description, text_content=""):
    """Capture screenshot for training analysis"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_dir = "training_screenshots"
        
        # Create directory if it doesn't exist
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
        
        # Capture screenshot
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[1])  # Primary monitor
            screenshot_path = os.path.join(screenshot_dir, f"threat_{timestamp}.png")
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
        
        return training_id, training_data
        
    except Exception as e:
        print(f"Training screenshot error: {e}")
        return None, None

def log_event(msg, threat_type=None, description=None, text_content=""):
    """Enhanced logging with training screenshot capture"""
    # Use MM/DD/YYYY and 12-hour time without seconds
    date_part = datetime.now().strftime('%m/%d/%Y')
    time_part = datetime.now().strftime('%I:%M %p').lstrip('0')
    # Format: [MM/DD/YYYY] [H:MM AM/PM] Problem
    log_msg = f"[{date_part}] [{time_part}] {msg}"
    
    # Optionally capture training screenshot if this is a threat detection and training capture is enabled
    training_id = None
    if TRAINING_CAPTURE_ENABLED and threat_type and description:
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
        with open("securely_log.txt", "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
            # Do NOT write raw OCR/AI text to the audit log to preserve privacy.
            # Previously we wrote a Details/Raw Text block; per request we remove it entirely.
            # After writing the audit entry, trigger a UI refresh of the Audit Log
            try:
                if 'APP_MAIN_WINDOW' in globals() and getattr(globals()['APP_MAIN_WINDOW'], 'after', None):
                    # Schedule the load to run on the main thread (safe from background threads)
                    globals()['APP_MAIN_WINDOW'].after(200, globals()['APP_MAIN_WINDOW'].load_audit_log)
            except Exception:
                # If UI refresh fails (no UI present), ignore silently
                pass
    except Exception as _e:
        print(f"Failed to write secure log: {_e}")

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
        education_window = ctk.CTkToplevel()
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
        print(f"Error showing threat education: {e}")

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
        self.notification_cooldown = 300  # 5 minutes cooldown for same threat (300 seconds)
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
            print(f"Monitor start error: {e}")

    def request_scan_once(self):
        """Request the monitor to perform a single immediate scan."""
        try:
            # Mark one-shot request and ensure monitor is running
            self._one_shot = True
            self.start_monitor()
        except Exception as e:
            print(f"request_scan_once error: {e}")

    def request_scan_for(self, seconds=3):
        """Request the monitor to run for a short duration (seconds)."""
        try:
            self._multi_scan_until = time.time() + float(seconds)
            self.start_monitor()
        except Exception as e:
            print(f"request_scan_for error: {e}")

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
                if current_time - last_time < 60:  # 1 minute cooldown per window
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
            print(f"Monitor stop error: {e}")

    def run(self):
        with mss.mss() as sct:
            while True:
                if not self.running.is_set():
                    time.sleep(0.01)  # Ultra-fast check - 10ms
                    continue
                    
                try:
                    # Update AI status
                    self.ai_status = "🔍 Scanning screen..."
                    self.ai_active = True
                    if self.main_window:
                        self.main_window.update_ai_status(self.ai_status)
                    
                    # Capture screen
                    img = sct.grab(sct.monitors[1])
                    im = Image.frombytes("RGB", img.size, img.rgb)
                    
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
                    if TESSERACT_AVAILABLE:
                        try:
                            screen_text = pytesseract.image_to_string(im, config=r'--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?@#$%^&*()_+-={}[]|\:\"<>?/')
                        except Exception as _ocr_e:
                            print(f"OCR error: {_ocr_e}")
                            screen_text = ""
                    else:
                        # Print a helpful one-time message and avoid spamming the console
                        if not TESS_WARNED:
                            print("Screen monitoring error: tesseract is not installed or it's not in your PATH. See README file for more information.")
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
                    
                    # Run AI visual analysis on screen (use full unmasked image for position tracking)
                    print("Running AI visual analysis...")
                    ai_findings = analyze_screen_with_ai(img_base64, screen_text)  # Store AI findings separately (pass OCR text for heuristics)
                    # If AI signaled a pause-for-sensitive-page, stop monitoring and update UI
                    try:
                        if globals().get('PAUSED_FOR_SENSITIVE_PAGE', False):
                            print("Auto-pause engaged due to sensitive page detection - stopping monitor")
                            try:
                                # Stop the monitor loop
                                self.stop_monitor()
                            except Exception:
                                pass

                            # Update main window UI on main thread
                            if self.main_window:
                                try:
                                    def _ui_pause_update():
                                        try:
                                            self.main_window.program_enabled = False
                                            # Update toggle button and status label to paused state
                                            if hasattr(self.main_window, 'program_toggle_btn'):
                                                self.main_window.program_toggle_btn.configure(text="Turn On", fg_color="#28a745", hover_color="#218838")
                                            if hasattr(self.main_window, 'status_label'):
                                                self.main_window.status_label.configure(text="● Paused (Sensitive Page)", text_color="#f85149")
                                            if hasattr(self.main_window, 'monitoring_var'):
                                                try:
                                                    self.main_window.monitoring_var.set(False)
                                                except Exception:
                                                    pass
                                            # Attempt to send a native notification explaining the pause
                                            try:
                                                sent = show_notification(
                                                    "Paused: Sensitive Page Detected",
                                                    "Securely paused for 2 minutes to protect credentials. It will auto-resume.",
                                                    duration=8
                                                )
                                                if not sent:
                                                    print("Native notification not available. Install 'win11toast' or 'win10toast' or 'winrt' for native toasts.")
                                            except Exception:
                                                pass

                                            # Schedule auto-resume in 2 minutes unless the user changes state
                                            try:
                                                # Cancel any previous pending auto-resume
                                                if hasattr(self.main_window, '_auto_resume_after_id') and self.main_window._auto_resume_after_id:
                                                    try:
                                                        self.main_window.after_cancel(self.main_window._auto_resume_after_id)
                                                    except Exception:
                                                        pass

                                                def _auto_resume():
                                                    try:
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
                                                                show_notification("Monitoring Resumed", "Securely resumed after sensitive page pause.", duration=6)
                                                            except Exception:
                                                                pass
                                                    finally:
                                                        try:
                                                            self.main_window._auto_resume_after_id = None
                                                        except Exception:
                                                            pass

                                                self.main_window._auto_resume_after_id = self.main_window.after(120000, _auto_resume)
                                            except Exception as e:
                                                print(f"Auto-resume schedule error: {e}")
                                        except Exception as e:
                                            print(f"UI pause update error: {e}")

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
                        
                        print(f"THREAT DETECTED: {findings}")
                        
                        # Get OCR data for logging (needed for all paths, not just hitboxes)
                        text = screen_text  # Use the already extracted screen_text
                    else:
                        # Update AI status - no threats found
                        self.ai_status = "✅ Screen secure"
                        self.ai_active = False
                        if self.main_window:
                            self.main_window.update_ai_status(self.ai_status)
                        
                        # Debug: Show what text was analyzed
                        if len(screen_text.strip()) > 0:
                            print(f"No threats found in text: {screen_text[:50]}...")
                        else:
                            print("No text detected on screen")
                        
                        text = screen_text  # Still need text for hitbox tracking
                    
                    # Update continuous hitboxes if enabled - Run IMMEDIATELY when toggled
                    if getattr(self, "hitboxes_enabled", False):
                        current_threats = {}
                        
                        # Run OCR more frequently for better tracking (every 2nd scan instead of 5th)
                        scan_counter = getattr(self, '_hitbox_scan_counter', 0)
                        self._hitbox_scan_counter = (scan_counter + 1) % 2  # Every other scan
                        should_run_ocr = (self._hitbox_scan_counter == 0)
                        
                        # Detect screen changes (scrolling) by comparing text content
                        current_text_hash = hash(screen_text[:500])  # Hash first 500 chars
                        last_text_hash = getattr(self, '_last_text_hash', None)
                        screen_changed = (last_text_hash is not None and current_text_hash != last_text_hash)
                        self._last_text_hash = current_text_hash
                        
                        # On scroll, try to re-detect threats immediately (don't just clear)
                        if screen_changed and findings:
                            print("Screen scrolled - re-detecting threat positions...")
                            should_run_ocr = True  # Force immediate OCR on scroll
                        
                        # Process findings if we have any OR if we have active threats to track
                        if (findings or self.active_threats) and should_run_ocr:
                            if findings:
                                print(f"Hitboxes enabled - processing {len(findings)} threat(s)")
                            
                            # Get OCR data for position tracking
                            try:
                                ocr_data = pytesseract.image_to_data(im, config='--psm 6 -c tessedit_do_invert=0', output_type=pytesseract.Output.DICT)
                            except Exception as ocr_error:
                                print(f"OCR error (skipping this scan): {ocr_error}")
                                ocr_data = None
                            
                            # For test mode, always show hitbox
                            if getattr(self, "test_mode", False):
                                current_threats["Test threat detected - this is a simulation"] = (200, 200, 300, 60)
                                print("Test mode: Added test hitbox")
                            
                            # Only process positions if OCR succeeded
                            if ocr_data:
                                # For AI-detected threats, create larger region hitboxes (AI sees visually)
                                for f in ai_findings:
                                    if f != "Test threat detected - this is a simulation":
                                        # AI detections get prominent full-area hitboxes since AI analyzes whole screen
                                        # Place at center-top of screen as a warning banner
                                        banner_width = int(im.size[0] * 0.6)  # 60% of screen width
                                        banner_height = 80
                                        banner_x = int(im.size[0] * 0.2)  # Center horizontally
                                        banner_y = 50  # Near top
                                        current_threats[f] = (banner_x, banner_y, banner_width, banner_height)
                                        print(f"AI detection - creating warning banner for: {f}")
                                
                                # For keyword-only threats, find their specific text locations
                                for f in findings:
                                    if f not in ai_findings and f != "Test threat detected - this is a simulation":
                                        threat_location = self.find_specific_threat_location(f, text, ocr_data)
                                        if threat_location:
                                            current_threats[f] = threat_location
                                            print(f"Keyword detection - found location for '{f}': {threat_location}")
                                        else:
                                            print(f"Could not locate keyword '{f}' on screen")
                        
                        # Clear hitboxes when no findings detected (threat disappeared)
                        elif not findings:
                            if hasattr(self, 'active_threats') and self.active_threats:
                                print("No threats detected - clearing hitboxes")
                                self.close_overlay()
                                self.active_threats = {}
                                if hasattr(self, '_hitbox_timeout'):
                                    delattr(self, '_hitbox_timeout')
                        
                        # Always update overlay to maintain continuous tracking
                        if current_threats:
                            self._hitbox_timeout = time.time()  # Reset timeout when updating
                            self.update_continuous_overlay(current_threats, im.size)
                        elif findings and not should_run_ocr:
                            # We have threats but waiting for next OCR cycle - maintain display
                            if hasattr(self, 'active_threats') and self.active_threats:
                                print(f"Maintaining {len(self.active_threats)} hitboxes (waiting for OCR)")
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
                                # Create professional notification message
                                threat_name = f.upper() if len(f) < 20 else f[:20].upper() + "..."
                                notification_title = "⚠️ THREAT DETECTED:"
                                notification_msg = f"{threat_name}\n\n📋 View Security Audit for detailed analysis"
                                
                                # Use universal notification function (works in .exe)
                                notification_sent = show_notification(notification_title, notification_msg, duration=10)
                                
                                if notification_sent:
                                    print(f"Professional notification sent: {threat_name}")
                                else:
                                    print(f"Failed to send notification for: {threat_name}")
                                
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
                    print(f"Screen monitoring error: {e}")
                    
                # Dynamic scan interval based on AI rate limit status
                global _ai_in_rate_limit
                
                if getattr(self, "hitboxes_enabled", False):
                    # Hitboxes enabled - always use fast scanning for smooth tracking
                    time.sleep(0.01)  # 10ms for ultra-smooth hitboxes
                elif _ai_in_rate_limit:
                    # AI rate limited - scan every 5 seconds to conserve API quota
                    time.sleep(5.0)  # 5 second interval during rate limit
                else:
                    # Normal scanning - fast but not excessive
                    time.sleep(0.05)  # 50ms interval
                # If this was a one-shot scan request, stop after one iteration
                try:
                    now = time.time()
                    if hasattr(self, '_one_shot') and getattr(self, '_one_shot'):
                        # Before clearing the one-shot flag, send a summary notification
                        try:
                            # Summarize findings from this iteration
                            summary_title = "Securely - Scan Result"
                            if findings:
                                # Build concise message
                                if isinstance(findings, list):
                                    short = ", ".join([str(x) for x in findings[:3]])
                                    more = len(findings) - 3
                                    msg = f"⚠️ Threats detected: {short}{'...' if more>0 else ''}\n\nOpen Securely to view details."
                                else:
                                    msg = f"⚠️ Threats detected: {str(findings)}\n\nOpen Securely to view details."
                            else:
                                msg = "✅ Scan complete - No threats detected."

                            sent = show_notification(summary_title, msg, duration=8)
                            if not sent:
                                print("Native notification failed: ensure 'win11toast', 'win10toast', or 'winrt' is installed.")
                        except Exception as _e:
                            print(f"One-shot notification error: {_e}")

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
                                            self.main_window.program_toggle_btn.configure(text="Turn On", fg_color="#28a745", hover_color="#218838")
                                        except Exception:
                                            pass
                                        try:
                                            self.main_window.status_label.configure(text="● Paused", text_color="#f85149")
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
        """Find exact location of specific threat/keyword on screen with position memory"""
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
                return None
            
            # If we have previous position for this threat, prefer closest match
            threat_key = f"{threat_lower}_pos"
            if hasattr(self, 'threat_positions') and threat_key in self.threat_positions:
                prev_x, prev_y = self.threat_positions[threat_key][:2]
                for match in all_matches:
                    x, y, w, h = match['position']
                    distance = ((x - prev_x) ** 2 + (y - prev_y) ** 2) ** 0.5
                    match['distance'] = distance
                
                # Prioritize distance heavily for instant movement tracking
                all_matches.sort(key=lambda x: (x['distance'] * 0.5, -x['confidence']))
            else:
                # Sort by confidence only
                all_matches.sort(key=lambda x: -x['confidence'])
            
            best_match = all_matches[0]
            x, y, w, h = best_match['position']
            
            # Add minimal padding for faster movement response
            padding = 4
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = w + (padding * 2)
            h = h + (padding * 2)
            
            # Remember this position for next time
            if not hasattr(self, 'threat_positions'):
                self.threat_positions = {}
            self.threat_positions[threat_key] = (x, y, w, h)
            
            return (x, y, w, h)
            
        except Exception as e:
            print(f"Threat location error: {e}")
            return None
    
    def update_continuous_overlay(self, current_threats, screen_size):
        """Update continuous overlay with all active threats"""
        try:
            print(f"update_continuous_overlay called with {len(current_threats)} threats")
            
            # If hitboxes disabled, clear overlay
            if not getattr(self, "hitboxes_enabled", False):
                print("Hitboxes disabled - clearing overlay")
                self.close_overlay()
                self.active_threats = {}
                return
            
            # If no threats detected, clear overlay
            if not current_threats:
                print("No threats to display - clearing overlay")
                self.close_overlay()
                self.active_threats = {}
                return
            
            # Update active threats
            self.active_threats = current_threats
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
            
            # Draw rectangle for each threat at its specific location
            colors = ['red', 'orange', 'yellow', 'magenta', 'cyan', 'lime', 'pink']  # More colors for multiple threats
            color_index = 0
            fallback_offset = 0
            
            for threat_text, threat_location in current_threats.items():
                color = colors[color_index % len(colors)]
                
                if threat_location:
                    # Use detected threat location - position box directly over the detected text
                    x, y, w, h = threat_location
                    # Add minimal padding around the detected text
                    padding = 5
                    box_x = max(0, x - padding)
                    box_y = max(0, y - padding)
                    box_width = min(w + (padding * 2), screen_size[0] - box_x)
                    box_height = min(h + (padding * 2), screen_size[1] - box_y)
                    print(f"Drawing hitbox for '{threat_text}' at ({box_x}, {box_y}) size {box_width}x{box_height}")
                else:
                    # Fallback: stack boxes if location not detected
                    box_width = 200
                    box_height = 30
                    box_x = 50 + fallback_offset
                    box_y = 50 + fallback_offset
                    fallback_offset += 40  # Stack vertically
                    print(f"Drawing fallback hitbox for '{threat_text}' at ({box_x}, {box_y})")
                
                # Draw rectangle border for this specific threat
                canvas.create_rectangle(box_x, box_y, box_x+box_width, box_y+box_height, 
                                      outline=color, width=2, fill='')                
                # Add text label for the threat
                label_text = threat_text[:20] + "..." if len(threat_text) > 20 else threat_text
                canvas.create_text(box_x + 5, box_y - 15, text=label_text, 
                                 fill=color, font=('Arial', 8), anchor='w')
                
                color_index += 1
            
            # Show window only after everything is drawn (prevents white flash)
            self.overlay_window.deiconify()
            
            print(f"Overlay created successfully with {len(current_threats)} hitbox(es)")
            
        except Exception as e:
            print(f"Continuous overlay error: {e}")
    
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
            print(f"Overlay close error (safe to ignore): {e}")
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
            icon_path = r"C:\Program Files\Securely-Assets\2.ico"
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
            # Use Windows API to keep window in taskbar
            import ctypes
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_APPWINDOW)
            # Force redraw
            self.withdraw()
            self.after(10, self.deiconify)
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
        
        self.create_dashboard_tab()
        self.create_settings_tab()
        self.create_audit_log_tab()
        self.create_credits_tab()
        
        # Add tooltips to tabs
        self.after(200, self.add_simple_tooltips)
        
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
        
        # Create inner frame to center buttons
        center_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        center_frame.pack(anchor="center")
        
        # Scan once button
        self.temp_disable_btn = ctk.CTkButton(center_frame, text="Quick Scan", width=60, height=24,
                    font=ctk.CTkFont(size=10),
                    fg_color="#d73a49",
                    hover_color="#cb2431",
                    text_color="#ffffff",
                    command=self.on_temp_disable)
        self.temp_disable_btn.pack(side="left", padx=(0, 4), pady=4, anchor="center")
        # store base metrics for reliable scaling
        try:
            self.temp_disable_btn._base_width = 60
            self.temp_disable_btn._base_height = 24
            self.temp_disable_btn._base_font = 10
        except Exception:
            pass

        # Short-duration scan button (runs scanning for a few seconds)
        self.short_scan_btn = ctk.CTkButton(center_frame, text="Scan 15m", width=60, height=24,
                            font=ctk.CTkFont(size=10),
                            fg_color="#0969da",
                            hover_color="#0860ca",
                            text_color="#ffffff",
                            command=self.on_scan_short)
        self.short_scan_btn.pack(side="left", padx=(4, 4), pady=4, anchor="center")
        try:
            self.short_scan_btn._base_width = 60
            self.short_scan_btn._base_height = 24
            self.short_scan_btn._base_font = 10
        except Exception:
            pass
        
        # Program toggle button (Off/On) - Start in OFF state
        self.program_enabled = False
        # Use a shorter label and normal font weight so it fits the button
        self.program_toggle_btn = ctk.CTkButton(center_frame, text="Turn On", width=72, height=24,
                              font=ctk.CTkFont(size=10),
                              fg_color="#28a745",  # Green for Turn On
                              hover_color="#218838",
                              text_color="#ffffff",
                              command=self.on_program_toggle)
        self.program_toggle_btn.pack(side="left", padx=(4, 0), pady=4, anchor="center")
        try:
            self.program_toggle_btn._base_width = 72
            self.program_toggle_btn._base_height = 24
            self.program_toggle_btn._base_font = 10
        except Exception:
            pass
        # Create (hidden) in-app confirmation page for enabling continuous monitoring
        self.monitor_confirm_frame = ctk.CTkFrame(self.main_frame, fg_color="#0d1117")
        # Confirmation header (wraps to fit window)
        confirm_header = ctk.CTkLabel(self.monitor_confirm_frame, text="Enable Continuous Monitoring?",
                           font=ctk.CTkFont(size=11, weight="bold"), text_color="#f0f6fc",
                           wraplength=380, justify="center")
        confirm_header.pack(pady=(10, 6), padx=12)

        confirm_text = (
            "Enabling continuous monitoring will keep Securely running in the background. "
            "AI may analyze portions of your screen to detect threats."
        )

        # Use a scrollable frame so the confirmation content adapts to window size and scrolls if needed
        # Use a simple, fixed confirmation label (no scrolling) so buttons appear directly under it
        try:
            # Slightly smaller font and dynamic wrap so text fits narrow windows
            confirm_label = ctk.CTkLabel(self.monitor_confirm_frame, text=confirm_text,
                                         font=ctk.CTkFont(size=9), text_color="#8b949e", justify="left",
                                         wraplength=380)
            confirm_label.pack(fill="x", padx=12, pady=(12, 6))

            # Update wraplength dynamically based on the MAIN window width so it always fits
            def _update_confirm_wrap(event=None):
                try:
                    # Use the current window width as the basis (subtract margins)
                    win_w = getattr(self, 'winfo_width', lambda: 380)()
                    # Fall back to a sensible minimum
                    width = max(160, win_w - 48)
                    # Update both the main confirmation label and the header so they both wrap nicely
                    try:
                        confirm_label.configure(wraplength=width)
                    except Exception:
                        pass
                    try:
                        confirm_header.configure(wraplength=width)
                    except Exception:
                        pass
                except Exception:
                    pass

            try:
                # Bind both the confirmation frame and the main window to handle different resize paths
                self.monitor_confirm_frame.bind('<Configure>', _update_confirm_wrap)
                try:
                    self.bind('<Configure>', _update_confirm_wrap)
                except Exception:
                    pass
                # Initial call to set proper wraplength immediately
                _update_confirm_wrap()
            except Exception:
                pass
        except Exception:
            confirm_label = ctk.CTkLabel(self.monitor_confirm_frame, text=confirm_text,
                                         font=ctk.CTkFont(size=9), text_color="#8b949e", justify="left",
                                         wraplength=420)
            confirm_label.pack(fill="x", padx=12, pady=(12, 6))

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
        
        # Load existing log entries
        self.load_audit_log()
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
            
            # Enhanced analysis text area
            self.analysis_text = ctk.CTkTextbox(analysis_section, height=200,
                                              fg_color="#0d1117",
                                              text_color="#f0f6fc",
                                              font=ctk.CTkFont(size=11, family="Consolas"),
                                              border_width=2,
                                              border_color="#30363d",
                                              corner_radius=8)
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
            print(f"Switch to audit error: {e}")
    
    def switch_to_audit_with_analysis(self, threat_description, detected_text):
        """Switch to Security Audit tab and show analysis window"""
        try:
            # Switch to Security Audit tab
            self.tab_view.set("📋")
            
            # Show analysis window
            self.handle_notification_click(threat_description, detected_text)
            
        except Exception as e:
            print(f"Switch to audit error: {e}")
    
    def handle_notification_click(self, threat_description, detected_text):
        """Handle notification click with immediate screenshot and AI analysis"""
        try:
            # Capture screenshot immediately
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = "instant_analysis"
            
            # Create directory if it doesn't exist
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            
            # Capture current screen
            with mss.mss() as sct:
                screenshot = sct.grab(sct.monitors[1])
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
            
            # Analysis text area
            self.instant_analysis_text = ctk.CTkTextbox(analysis_frame, height=180,
                                                       fg_color="#0d1117",
                                                       text_color="#f0f6fc",
                                                       font=ctk.CTkFont(size=10, family="Consolas"),
                                                       border_width=2,
                                                       border_color="#30363d")
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
        if not any(GOOGLE_API_KEYS):
            return "⚠️ AI analysis unavailable - no API key configured."
        
        # Use first available Gemini key
        api_key = next((key for key in GOOGLE_API_KEYS if key), None)
        if not api_key:
            return "⚠️ AI analysis unavailable - no valid API key."
        
        try:
            with open(screenshot_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            return f"Error reading screenshot: {e}"
        
        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": f"""INSTANT CYBERSECURITY ANALYSIS:
                        
                        You are an expert cybersecurity analyst. Analyze this screenshot immediately and provide a clear assessment.
                        
                        Detected text: "{detected_text}"
                        
                        Provide analysis in this format:
                        
                        🚨 THREAT LEVEL: [SAFE/SUSPICIOUS/MALICIOUS]
                        
                        📋 WHAT I'M SEEING:
                        [Describe the visual content clearly]
                        
                        🔍 SECURITY ASSESSMENT:
                        [Explain if this is concerning and why]
                        
                        ⚡ IMMEDIATE ACTION:
                        [What the user should do right now]
                        
                        🛡️ PREVENTION TIPS:
                        [How to avoid this in the future]
                        
                        Be direct and actionable. If nothing suspicious is found, clearly state the content appears safe.
                        """
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": img_data
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 800,
            }
        }
        
        try:
            response = requests.post(
                f"{GEMINI_API_URL}?key={api_key}",
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text'].strip()
            
            return f"AI service error: {response.status_code}"
            
        except Exception as e:
            return f"Analysis error: {str(e)}"
    
    def update_instant_analysis(self, analysis):
        """Update instant analysis text"""
        try:
            if hasattr(self, 'instant_analysis_text'):
                self.instant_analysis_text.delete("1.0", "end")
                
                if analysis.startswith("❌") or analysis.startswith("⚠️"):
                    self.instant_analysis_text.insert("1.0", analysis)
                else:
                    formatted_analysis = f"""⚡ INSTANT ANALYSIS COMPLETE
{'='*50}

{analysis}

{'='*50}
🔒 SECURELY - REAL-TIME THREAT PROTECTION"""
                    self.instant_analysis_text.insert("1.0", formatted_analysis)
        except Exception as e:
            print(f"Instant analysis update error: {e}")

    def analyze_text_with_ai(self, text):
        """Run a text-only AI prompt to produce a clear educational analysis and prevention tips."""
        if not any(GOOGLE_API_KEYS):
            return "⚠️ AI analysis unavailable - no API key configured."

        api_key = next((key for key in GOOGLE_API_KEYS if key), None)
        if not api_key:
            return "⚠️ AI analysis unavailable - no valid API key."

        # Build a concise educational prompt
        prompt = f"""You are an expert cybersecurity educator. A user saw this short issue: \"{text}\". Provide a clear, concise analysis in this format:

🚨 THREAT LEVEL: [SAFE / SUSPICIOUS / MALICIOUS]

📋 WHAT THIS MEANS:
[Brief plain-English explanation of what this issue likely indicates]

⚡ IMMEDIATE ACTION:
[What the user should do right now, 2-3 bullet points]

🛡️ PREVENTION TIPS:
[3-5 practical prevention steps the user can take]

Keep the response short, direct, and actionable."
"""

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 400
            }
        }

        try:
            if requests is None:
                return "⚠️ 'requests' library not installed; cannot call AI API. Install with: pip install requests"

            response = requests.post(
                f"{GEMINI_API_URL}?key={api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=20
            )
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text'].strip()
            return f"AI service error: {response.status_code}"
        except Exception as e:
            return f"Analysis error: {e}"

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

            sub = ctk.CTkLabel(content, text=headline_text, font=ctk.CTkFont(size=10), text_color="#f0f6fc", wraplength=560, justify="left")
            sub.pack(padx=12, pady=(12, 6), anchor="w")

            # Scrollable area for analysis results (use label inside a scrollable frame)
            scroll_container = ctk.CTkScrollableFrame(content, fg_color="#0d1117")
            scroll_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

            analysis_lbl = ctk.CTkLabel(scroll_container,
                                        text="🔍 Generating educational analysis...\n\nPlease wait.",
                                        font=ctk.CTkFont(size=11),
                                        text_color="#f0f6fc",
                                        wraplength=560,
                                        justify="left",
                                        anchor="nw")
            analysis_lbl.pack(fill="both", expand=True, padx=6, pady=6)

            # Adjust wraplength dynamically so text fits the window and doesn't get cut off
            def adjust_wrap(evt=None):
                try:
                    # Prefer the scroll container width; fall back to content
                    w = scroll_container.winfo_width() or content.winfo_width()
                    # Account for padding/margins
                    avail = max(200, w - 36)
                    sub.configure(wraplength=avail)
                    analysis_lbl.configure(wraplength=avail)
                except Exception:
                    pass

            # Bind resizing events and run an initial adjust after the window shows
            try:
                win.bind("<Configure>", adjust_wrap)
                scroll_container.bind("<Configure>", adjust_wrap)
                win.after(120, adjust_wrap)
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
                    analysis_lbl.configure(text=cache[cache_key])
                except Exception:
                    analysis_lbl.configure(text=cache.get(cache_key, "(cached analysis)"))
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
                                analysis_lbl.configure(text=clean)
                            except Exception:
                                try:
                                    analysis_lbl.configure(text=analysis)
                                except Exception:
                                    pass

                        win.after(0, _insert_clean)
                    except Exception as e:
                        win.after(0, lambda: analysis_lbl.configure(text=f"Analysis error: {e}"))

                threading.Thread(target=run_analysis, daemon=True).start()

            # Ensure close works when user presses Escape
            win.bind('<Escape>', lambda e: _close())

        except Exception as e:
            try:
                messagebox.showerror("Analysis Error", f"Failed to open analysis window: {e}")
            except Exception:
                print(f"Failed to open analysis window: {e}")
    
    def update_analysis_text(self, analysis):
        """Update analysis text in training window with professional formatting"""
        try:
            if hasattr(self, 'analysis_text'):
                self.analysis_text.delete("1.0", "end")
                
                # Professional formatting for analysis results
                if analysis.startswith("❌"):
                    # Error formatting
                    self.analysis_text.insert("1.0", analysis)
                else:
                    # Simpler success formatting for readability
                    # Sanitize analysis similar to the quick view
                    try:
                        clean = analysis.replace('**', '').replace('`', '')
                        clean = re.sub(r'^[ \t]*[-*+]\s+', '• ', clean, flags=re.M)
                        clean = re.sub(r'^[-=]{3,}\s*$', '', clean, flags=re.M)
                        clean = re.sub(r'\n{3,}', '\n\n', clean)
                        # Remove polite boilerplate lines at the start (e.g., 'Okay, here's... formatted as requested')
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

                    formatted_analysis = f"""🛡️ CYBERSECURITY ANALYSIS COMPLETE

{clean}

🔒 SECURELY - PROTECTING YOUR DIGITAL ENVIRONMENT"""

                    self.analysis_text.insert("1.0", formatted_analysis)
        except Exception as e:
            print(f"Analysis text update error: {e}")
        
    def create_credits_tab(self):
        credits = self.tab_view.tab("ℹ️")
        # Simple, scrollable credits with just labels
        scroll = ctk.CTkScrollableFrame(credits, fg_color="#0d1117")
        scroll.pack(fill="both", expand=True, padx=12, pady=10)

        # Development Team
        ctk.CTkLabel(scroll, text="Development Team", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f0f6fc").pack(anchor="w", pady=(2, 2))
        ctk.CTkLabel(scroll, text="• @Delexo — Lead Development", font=ctk.CTkFont(size=12), text_color="#8b949e").pack(anchor="w")
        ctk.CTkLabel(scroll, text="• @Mai — Product Strategy", font=ctk.CTkFont(size=12), text_color="#8b949e").pack(anchor="w", pady=(0, 6))

        # Special Thanks
        ctk.CTkLabel(scroll, text="Special Thanks", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f0f6fc").pack(anchor="w", pady=(6, 2))
        ctk.CTkLabel(scroll, text="• Priscilla", font=ctk.CTkFont(size=12), text_color="#8b949e").pack(anchor="w")
        ctk.CTkLabel(scroll, text="• Derek", font=ctk.CTkFont(size=12), text_color="#8b949e").pack(anchor="w")
        ctk.CTkLabel(scroll, text="• CSUSM Community", font=ctk.CTkFont(size=12), text_color="#8b949e").pack(anchor="w", pady=(0, 6))

        # Built With
        ctk.CTkLabel(scroll, text="Built With", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f0f6fc").pack(anchor="w", pady=(6, 2))
        ctk.CTkLabel(scroll, text="• Python", font=ctk.CTkFont(size=12), text_color="#8b949e").pack(anchor="w")
        ctk.CTkLabel(scroll, text="• Google Gemini API", font=ctk.CTkFont(size=12), text_color="#8b949e").pack(anchor="w")
        ctk.CTkLabel(scroll, text="• Tesseract OCR", font=ctk.CTkFont(size=12), text_color="#8b949e").pack(anchor="w")
        ctk.CTkLabel(scroll, text="• And coffee", font=ctk.CTkFont(size=12), text_color="#8b949e").pack(anchor="w", pady=(0, 8))

        # Buttons row
        # Button row (centered, small)
        btn_row = ctk.CTkFrame(scroll, fg_color="#0d1117")
        btn_row.pack(fill="x", pady=(6, 10))
        try:
            # Center single button with spacer columns
            btn_row.grid_columnconfigure(0, weight=1)
            btn_row.grid_columnconfigure(2, weight=1)
            learn_btn = ctk.CTkButton(btn_row, text="Visit My Website", width=110, height=28,
                                      font=ctk.CTkFont(size=11, weight="bold"),
                                      command=self.open_learn_more)
            learn_btn.grid(row=0, column=1, pady=0)
        except Exception:
            # Fallback centers by default when using pack from the top
            learn_btn.pack(pady=0)

        # Footer
        ctk.CTkLabel(scroll, text=f"© Securely — {APP_VERSION}", font=ctk.CTkFont(size=11), text_color="#6e7681").pack(pady=(8, 6))
    
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
            # Replace with your actual store URL
            webbrowser.open("https://store.example.com/securely")
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
            # Clear existing threat cards
            for widget in self.audit_frame.winfo_children():
                widget.destroy()
            self.threat_cards = []

            # Always display the textual audit log (no screenshots stored/displayed)
            try:
                with open("securely_log.txt", "r", encoding="utf-8") as f:
                    log_content = f.read().strip()

                    if log_content:
                        # Show the last ~200 lines for context
                        lines = log_content.split('\n')[-200:]

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
            self.program_toggle_btn.configure(text="Turn On", 
                                            fg_color="#28a745",  # Green for Turn On
                                            hover_color="#218838")
            self.status_label.configure(text="● Disabled", text_color="#8b949e")
            # Cancel any pending auto-resume (user took manual action)
            try:
                if hasattr(self, '_auto_resume_after_id') and self._auto_resume_after_id:
                    self.after_cancel(self._auto_resume_after_id)
                    self._auto_resume_after_id = None
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
            self.program_toggle_btn.configure(text="Turn On", 
                                            fg_color="#28a745",
                                            hover_color="#218838")
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
            self.program_toggle_btn.configure(text="Turn Off", 
                                            fg_color="#dc3545",
                                            hover_color="#c82333")
            self.status_label.configure(text="● Paused", text_color="#f85149") 
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
                    with mss.mss() as sct:
                        img = sct.grab(sct.monitors[1])
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
            # Send a user-friendly test notification only (do NOT write to audit log)
            notification_title = "🔔 Test Notification"
            notification_msg = "This is a test from Securely — no action required."

            # Use universal notification function (works in .exe)
            notification_sent = show_notification(notification_title, notification_msg, duration=8)

            if notification_sent:
                print("✅ Test notification sent successfully.")
            else:
                print("⚠️ Test notification could not be delivered natively.")
                print("Install 'win11toast' or 'win10toast' or 'winrt' in this Python environment to enable OS toasts.")
            
            print("Check the Security Audit tab (📋) to see the threat card with screenshot!")
            
            # Switch to audit tab to show the result
            self.after(1000, lambda: self.tab_view.set("📋"))
            
        except Exception as e:
            print(f"Test notification error: {e}")
            # Direct fallback - show analysis window immediately
            try:
                print("Showing analysis window directly due to notification failure")
                self.switch_to_audit_with_analysis(
                    "Notification Test Failed", 
                    "Testing analysis window directly since notification system failed"
                )
            except Exception as e2:
                print(f"Direct analysis error: {e2}")

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
            print("Requested single scan via UI")
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
            self.program_toggle_btn.configure(text="On", 
                                            fg_color="#28a745",
                                            hover_color="#218838")

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
                # Countdown finished — show paused indicator (red) by default
                try:
                    self.status_label.configure(text="● Paused", text_color="#f85149")
                except Exception:
                    pass
                self._scan_countdown_after_id = None
        except Exception as e:
            print(f"Scan countdown tick error: {e}")

    def on_scan_short(self):
        """Start a short multi-second scan (runs monitor for a few seconds)."""
        try:
            # Change short scan to a 15-minute scan (900 seconds)
            seconds = 15 * 60
            print(f"Requested short scan for {seconds}s (15 minutes) via UI")
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
                self.status_label.configure(text=f"● Scanning (15:00)", text_color="#28a745")
            # Request monitor to run for the duration
            if hasattr(self, 'monitor') and self.monitor:
                self.monitor.request_scan_for(seconds)
        except Exception as e:
            print(f"Error requesting short scan: {e}")
    
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
                    self.program_toggle_btn.configure(text="Turn On", fg_color="#28a745", hover_color="#218838")
                except Exception:
                    pass
                try:
                    self.status_label.configure(text="● Paused", text_color="#f85149")
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
        """Hide the window without showing white box"""
        try:
            # Simply withdraw (hide) the window instead of iconifying
            # This avoids the white window box issue with borderless windows
            self.withdraw()
            
            # Create a system tray-like behavior by showing a notification
            if hasattr(self, 'monitor') and getattr(self.monitor, 'notifications_enabled', True):
                try:
                    from win10toast import ToastNotifier
                    # Use universal notification function (works in .exe)
                    def restore_window():
                        self.deiconify()
                        self.lift()
                        self.focus_force()
                    
                    # Note: Cannot use callbacks in .exe, so just show notification
                    notification_sent = show_notification(
                        "Securely Minimized", 
                        "Use taskbar to restore Securely window",
                        duration=5
                    )
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"Minimize error: {e}")
    
    def toggle_window_size(self):
        """Toggle between normal and 2x enlarged window size"""
        try:
            if not self.is_enlarged:
                # Enlarge to 2x size — compute new size and center on previous center to avoid jumpiness
                try:
                    scale = 2.0
                    new_width = max(300, int(self.original_size[0] * scale))
                    new_height = max(260, int(self.original_size[1] * scale))

                    # Save current geometry so we can restore exactly later
                    try:
                        self._prev_geometry = (self.winfo_width(), self.winfo_height(), self.winfo_x(), self.winfo_y())
                    except Exception:
                        self._prev_geometry = (self.original_size[0], self.original_size[1], self.winfo_x(), self.winfo_y())

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
                # Return to original size and recenter near previous geometry if available
                try:
                    # Prefer restoring exact previous geometry if we saved it
                    if hasattr(self, '_prev_geometry') and self._prev_geometry:
                        prev_w, prev_h, prev_x, prev_y = self._prev_geometry
                        new_width = prev_w or self.original_size[0]
                        new_height = prev_h or self.original_size[1]
                        new_x = prev_x
                        new_y = prev_y
                    else:
                        new_width = self.original_size[0]
                        new_height = self.original_size[1]

                        current_x = self.winfo_x()
                        current_y = self.winfo_y()
                        current_w = self.winfo_width() or new_width
                        current_h = self.winfo_height() or new_height
                        center_x = current_x + current_w // 2
                        center_y = current_y + current_h // 2

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

                    # Clear saved geometry after restore
                    try:
                        self._prev_geometry = None
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
    app = MainWindow()
    app.mainloop()