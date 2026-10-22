import sys 
import time
import threading
import warnings
import pytesseract
from PIL import Image
from mss import mss
import requests
try:
    import winsound
except Exception:
    winsound = None
import customtkinter as ctk
from win10toast import ToastNotifier

# --- ignore warnings ---
warnings.filterwarnings("ignore", category=UserWarning, module="win10toast")

# --- notifier ---
toaster = ToastNotifier()

# --- settings ---
SCREENSHOT_INTERVAL = 8  # seconds
KEYWORDS = ["virus", "malware", "worm", "spyware", "spy", "http", "phish", "keylogger"]

# --- keyword & domain analysis ---
def analyze_text(text):
    found = []
    for word in KEYWORDS:
        if word.lower() in text.lower():
            found.append(word)
    return found

def log_event(msg):
    with open("securely_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

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

    def start_monitor(self):
        self.running.set()
        if not self.is_alive():
            self.start()

    def stop_monitor(self):
        self.running.clear()

    def run(self):
        with mss() as sct:
            while True:
                if not self.running.is_set():
                    time.sleep(0.2)
                    continue
                img = sct.grab(sct.monitors[1])
                im = Image.frombytes("RGB", img.size, img.rgb)
                text = pytesseract.image_to_string(im)
                findings = analyze_text(text)
                if findings:
                    for f in findings:
                        msg = f"Suspicious keyword detected: {f}"
                        # only show desktop notifications when enabled
                        if getattr(self, "notifications_enabled", True):
                            toaster.show_toast("Securely — Alert", msg, duration=6, threaded=True)
                        # play a short beep when sound alerts enabled
                        if getattr(self, "sound_enabled", False) and winsound is not None:
                            try:
                                winsound.Beep(800, 220)
                            except Exception:
                                pass
                        log_event(msg)
                        self.recent_alerts.append(msg)
                        if len(self.recent_alerts) > 5:
                            self.recent_alerts.pop(0)
                time.sleep(self.interval)

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
        self.overrideredirect(True)  # Remove default window controls
        self.configure(fg_color="#0d1117")  # GitHub dark theme
        
        # Handle window closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create main frame with scrollable content
        self.main_frame = ctk.CTkFrame(self, fg_color="#0d1117", corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Custom title bar with exit button
        self.title_bar = ctk.CTkFrame(self.main_frame, fg_color="#161b22", height=20)
        self.title_bar.pack(fill="x", padx=0, pady=(0, 2))
        self.title_bar.pack_propagate(False)
        
        # Title label
        self.title_label = ctk.CTkLabel(self.title_bar, text="Securely", 
                                       font=ctk.CTkFont(size=10, weight="bold"),
                                       text_color="#f0f6fc")
        self.title_label.pack(side="left", padx=6, pady=2)
        
        # Custom exit button
        self.exit_btn = ctk.CTkButton(self.title_bar, text="✕", width=18, height=16,
                                     font=ctk.CTkFont(size=11, weight="bold"),
                                     fg_color="transparent",
                                     hover_color="#d73a49",
                                     text_color="#8b949e",
                                     command=self.on_closing)
        self.exit_btn.pack(side="right", padx=2, pady=2)
        
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
        
        # Monitor setup
        self.monitor = ScreenMonitor()
        self.monitor.notifications_enabled = True
        self.monitor.sound_enabled = False
        self.monitor.start_monitor()
        
        # Position window at right center of screen
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - 240
        y = (screen_height - 220) // 2
        self.geometry(f"220x200+{x}+{y}")
        
    def create_dashboard_tab(self):
        dashboard = self.tab_view.tab("📊")
        
        # Status label with darker background
        self.status_label = ctk.CTkLabel(dashboard, text="● Active", 
                                        fg_color="#21262d", corner_radius=6,
                                        text_color="#58a6ff",
                                        font=ctk.CTkFont(size=11, weight="bold"))
        self.status_label.pack(pady=(4, 4), padx=6, fill="x")
        
        # Control buttons frame
        buttons_frame = ctk.CTkFrame(dashboard, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=4, padx=6)
        
        # Temporary disable button (5 minutes)
        self.temp_disable_btn = ctk.CTkButton(buttons_frame, text="5m", width=60, height=24,
                                            font=ctk.CTkFont(size=10),
                                            fg_color="#d73a49",
                                            hover_color="#cb2431",
                                            text_color="#ffffff",
                                            command=self.on_temp_disable)
        self.temp_disable_btn.pack(side="left", padx=(0, 4))
        
        # Program toggle button (Off/On)
        self.program_enabled = True
        self.program_toggle_btn = ctk.CTkButton(buttons_frame, text="On", width=60, height=24,
                                              font=ctk.CTkFont(size=10, weight="bold"),
                                              fg_color="#28a745",  # Green for On
                                              hover_color="#218838",
                                              text_color="#ffffff",
                                              command=self.on_program_toggle)
        self.program_toggle_btn.pack(side="left")
        
    def create_settings_tab(self):
        settings = self.tab_view.tab("⚙️")
        
        # Create scrollable frame for settings with dark styling
        settings_scroll = ctk.CTkScrollableFrame(settings, fg_color="#0d1117",
                                               scrollbar_button_color="#30363d")
        settings_scroll.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Monitoring toggle
        self.monitoring_var = ctk.BooleanVar(value=True)
        self.monitoring_toggle = ctk.CTkCheckBox(settings_scroll, text="Monitor", 
                                               variable=self.monitoring_var,
                                               command=self.on_monitoring_toggled,
                                               font=ctk.CTkFont(size=10),
                                               text_color="#f0f6fc",
                                               fg_color="#1f6feb",
                                               hover_color="#58a6ff")
        self.monitoring_toggle.pack(anchor="w", pady=3)
        
        # Notifications toggle  
        self.notifications_var = ctk.BooleanVar(value=True)
        self.notifications_toggle = ctk.CTkCheckBox(settings_scroll, text="Notifications",
                                                  variable=self.notifications_var,
                                                  command=self.on_notifications_toggled,
                                                  font=ctk.CTkFont(size=10),
                                                  text_color="#f0f6fc",
                                                  fg_color="#1f6feb",
                                                  hover_color="#58a6ff")
        self.notifications_toggle.pack(anchor="w", pady=3)
        
        # Sound toggle
        self.sound_var = ctk.BooleanVar(value=False)
        self.sound_toggle = ctk.CTkCheckBox(settings_scroll, text="Sound",
                                          variable=self.sound_var,
                                          command=self.on_sound_toggled,
                                          font=ctk.CTkFont(size=10),
                                          text_color="#f0f6fc",
                                          fg_color="#1f6feb",
                                          hover_color="#58a6ff")
        self.sound_toggle.pack(anchor="w", pady=3)
        
    def create_audit_log_tab(self):
        audit_log = self.tab_view.tab("📋")
        
        # Header label
        header_label = ctk.CTkLabel(audit_log, text="Security Audit Log",
                                   font=ctk.CTkFont(size=12, weight="bold"),
                                   text_color="#58a6ff")
        header_label.pack(pady=(4, 6))
        
        # Clear log button
        clear_btn = ctk.CTkButton(audit_log, text="Clear Log", height=24,
                                 font=ctk.CTkFont(size=9),
                                 fg_color="#d73a49",
                                 hover_color="#cb2431",
                                 text_color="#ffffff",
                                 command=self.clear_audit_log)
        clear_btn.pack(pady=(0, 4))
        
        # Scrollable audit log frame
        self.audit_frame = ctk.CTkScrollableFrame(audit_log, fg_color="#0d1117",
                                                 scrollbar_button_color="#30363d",
                                                 scrollbar_button_hover_color="#424549")
        self.audit_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        
        # Audit log text
        self.audit_text = ctk.CTkLabel(self.audit_frame, text="No security events logged.",
                                      font=ctk.CTkFont(size=9),
                                      text_color="#8b949e",
                                      justify="left", anchor="nw")
        self.audit_text.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Load existing log entries
        self.load_audit_log()
        
        # Auto-refresh audit log every 3 seconds
        self.refresh_audit_log()
        
    def refresh_audit_log(self):
        # Only refresh if audit tab is currently visible
        if self.tab_view.get() == "📋":
            self.load_audit_log()
        self.after(3000, self.refresh_audit_log)
        
    def create_credits_tab(self):
        credits = self.tab_view.tab("ℹ️")
        
        credits_label = ctk.CTkLabel(credits, text="@Delexo & @Mai",
                                   font=ctk.CTkFont(size=11, weight="bold"),
                                   text_color="#58a6ff")
        credits_label.pack(expand=True)
        
    def show_audit_log(self):
        # Switch to audit log tab
        self.tab_view.set("📋")
        self.load_audit_log()
        
    def load_audit_log(self):
        # Load and display audit log from file
        try:
            with open("securely_log.txt", "r", encoding="utf-8") as f:
                log_content = f.read().strip()
                if log_content:
                    # Show last 20 entries to keep it manageable
                    lines = log_content.split('\n')[-20:]
                    formatted_log = "\n".join(lines)
                    self.audit_text.configure(text=formatted_log, text_color="#f85149")
                else:
                    self.audit_text.configure(text="No security events logged.", text_color="#8b949e")
        except FileNotFoundError:
            self.audit_text.configure(text="No security events logged.", text_color="#8b949e")
            
    def clear_audit_log(self):
        # Clear the audit log file and display
        try:
            with open("securely_log.txt", "w", encoding="utf-8") as f:
                f.write("")
            self.audit_text.configure(text="Audit log cleared.", text_color="#8b949e")
        except Exception:
            pass
        
    def on_program_toggle(self):
        # Toggle program on/off
        self.program_enabled = not self.program_enabled
        
        if self.program_enabled:
            # Program is now ON
            self.program_toggle_btn.configure(text="On", 
                                            fg_color="#28a745",  # Green
                                            hover_color="#218838")
            self.status_label.configure(text="● Active", text_color="#58a6ff")
            self.monitor.start_monitor()
            self.monitoring_var.set(True)
        else:
            # Program is now OFF
            self.program_toggle_btn.configure(text="Off", 
                                            fg_color="#dc3545",  # Red
                                            hover_color="#c82333")
            self.status_label.configure(text="● Disabled", text_color="#8b949e")
            self.monitor.stop_monitor()
            self.monitoring_var.set(False)
        
    def on_monitoring_toggled(self):
        # Sync with program toggle button
        if self.monitoring_var.get():
            self.program_enabled = True
            self.program_toggle_btn.configure(text="On", 
                                            fg_color="#28a745",
                                            hover_color="#218838")
            self.status_label.configure(text="● Active", text_color="#58a6ff")
            self.monitor.start_monitor()
        else:
            self.program_enabled = False
            self.program_toggle_btn.configure(text="Off", 
                                            fg_color="#dc3545",
                                            hover_color="#c82333")
            self.status_label.configure(text="● Paused", text_color="#f85149") 
            self.monitor.stop_monitor()
            
    def on_notifications_toggled(self):
        enabled = self.notifications_var.get()
        self.monitor.notifications_enabled = enabled
        
    def on_sound_toggled(self):
        enabled = self.sound_var.get()
        self.monitor.sound_enabled = enabled
        
    def on_temp_disable(self):
        # Temporary disable for 5 minutes
        self.program_enabled = False
        self.program_toggle_btn.configure(text="Off", 
                                        fg_color="#dc3545",
                                        hover_color="#c82333")
        self.monitoring_var.set(False)
        self.status_label.configure(text="● Paused (5m)", text_color="#f85149")
        self.monitor.stop_monitor()
        
        # Cancel existing timer if any
        if hasattr(self, '_temp_timer'):
            try:
                self._temp_timer.cancel()
            except Exception:
                pass
                
        # Schedule re-enable after 5 minutes
        def reenable():
            self.program_enabled = True
            self.program_toggle_btn.configure(text="On", 
                                            fg_color="#28a745",
                                            hover_color="#218838")
            self.monitoring_var.set(True)
            self.status_label.configure(text="● Active", text_color="#58a6ff")
            self.monitor.start_monitor()
            
        self._temp_timer = threading.Timer(300, reenable)
        self._temp_timer.daemon = True
        self._temp_timer.start()
        
    def on_closing(self):
        # Properly stop the monitor thread and exit
        if hasattr(self, 'monitor'):
            self.monitor.stop_monitor()
        if hasattr(self, '_temp_timer'):
            try:
                self._temp_timer.cancel()
            except Exception:
                pass
        self.destroy()
        
    def start_drag(self, event):
        self.x = event.x
        self.y = event.y
        
    def on_drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"220x200+{x}+{y}")

# --- entry point ---
if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()