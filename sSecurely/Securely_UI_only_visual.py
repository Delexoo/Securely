"""
UI-only visual mockup for Securely.
- Uses customtkinter when available, falls back to tkinter/ttk.
- Provides titlebar with logo, minimize/resize/exit buttons.
- Tabs: Dashboard, Settings, Audit Log, Credits.
- Dashboard contains program indicator, window selector dropdown, Quick Scan, Scan 15m, Toggle button.
- No functional monitoring/AI — buttons show a simple message.
"""

import sys
import webbrowser
try:
    import customtkinter as ctk
    from tkinter import messagebox
    USE_CTK = True
except Exception:
    import tkinter as ctk
    from tkinter import messagebox
    USE_CTK = False

import tkinter as tk
from tkinter import ttk

APP_TITLE = "Securely (UI Only)"

class VisualApp(ctk.CTk if USE_CTK else tk.Tk):
    def __init__(self):
        super().__init__()
        if USE_CTK:
            try:
                ctk.set_appearance_mode("dark")
                ctk.set_default_color_theme("blue")
            except Exception:
                pass

        # Window setup
        self.title(APP_TITLE)
        self.geometry("720x520")
        self.minsize(520, 360)
        # Custom title bar area (we keep normal window decorations for simplicity)

        # Top frame for logo and controls
        top = ctk.CTkFrame(self, fg_color="#0d1117") if USE_CTK else tk.Frame(self, bg="#0d1117")
        top.pack(fill="x", side="top")

        # Logo (drawn canvas) + title
        logo_canvas = tk.Canvas(top, width=44, height=44, bg="#0d1117", highlightthickness=0)
        logo_canvas.pack(side="left", padx=10, pady=8)
        # Draw simple circular logo with 'S'
        logo_canvas.create_oval(4,4,40,40, fill="#238636", outline="")
        logo_canvas.create_text(22,22, text="S", fill="white", font=("Segoe UI", 16, "bold"))

        title_lbl = ctk.CTkLabel(top, text=APP_TITLE, text_color="#f0f6fc", font=ctk.CTkFont(size=14, weight="bold")) if USE_CTK else tk.Label(top, text=APP_TITLE, fg="#f0f6fc", bg="#0d1117", font=("Segoe UI", 14, "bold"))
        title_lbl.pack(side="left", padx=(6,0))

        # Spacer
        spacer = tk.Frame(top, bg="#0d1117")
        spacer.pack(side="left", expand=True, fill="x")

        # Window control buttons
        btn_frame = tk.Frame(top, bg="#0d1117")
        btn_frame.pack(side="right", padx=8, pady=6)

        def on_minimize():
            try:
                self.iconify()
            except Exception:
                pass
        def on_toggle_size():
            if self.winfo_width() < 800:
                self.geometry("1000x700")
            else:
                self.geometry("720x520")
        def on_close():
            self.destroy()

        min_btn = tk.Button(btn_frame, text="_", width=3, command=on_minimize)
        min_btn.pack(side="left", padx=4)
        res_btn = tk.Button(btn_frame, text="⛶", width=3, command=on_toggle_size)
        res_btn.pack(side="left", padx=4)
        close_btn = tk.Button(btn_frame, text="✕", width=3, command=on_close)
        close_btn.pack(side="left", padx=4)

        # Main content area with tabs
        if USE_CTK:
            tabview = ctk.CTkTabview(self, width=800)
            tabview.add("📊 Dashboard")
            tabview.add("⚙️ Settings")
            tabview.add("📋 Audit Log")
            tabview.add("ℹ️ Credits")
            tabview.pack(fill="both", expand=True, padx=12, pady=12)
        else:
            tab_control = ttk.Notebook(self)
            tab_control.pack(fill="both", expand=True, padx=12, pady=12)
            dashboard_tab = tk.Frame(tab_control, bg="#0d1117")
            settings_tab = tk.Frame(tab_control, bg="#0d1117")
            audit_tab = tk.Frame(tab_control, bg="#0d1117")
            credits_tab = tk.Frame(tab_control, bg="#0d1117")
            tab_control.add(dashboard_tab, text="📊 Dashboard")
            tab_control.add(settings_tab, text="⚙️ Settings")
            tab_control.add(audit_tab, text="📋 Audit Log")
            tab_control.add(credits_tab, text="ℹ️ Credits")

        # Use unified references for tab frames
        if USE_CTK:
            dashboard = tabview.tab("📊 Dashboard")
            settings = tabview.tab("⚙️ Settings")
            audit_log = tabview.tab("📋 Audit Log")
            credits = tabview.tab("ℹ️ Credits")
        else:
            dashboard = dashboard_tab
            settings = settings_tab
            audit_log = audit_tab
            credits = credits_tab

        # --- Dashboard content ---
        dash_top = ctk.CTkFrame(dashboard, fg_color="#0d1117") if USE_CTK else tk.Frame(dashboard, bg="#0d1117")
        dash_top.pack(fill="x", padx=12, pady=(8,6))

        # Program indicator
        self.program_status = ctk.CTkLabel(dash_top, text="● Disabled", text_color="#8b949e", font=ctk.CTkFont(size=11, weight="bold")) if USE_CTK else tk.Label(dash_top, text="● Disabled", fg="#8b949e", bg="#0d1117", font=("Segoe UI", 11, "bold"))
        self.program_status.pack(fill="x")

        # Controls area
        controls = ctk.CTkFrame(dashboard, fg_color="transparent") if USE_CTK else tk.Frame(dashboard, bg="#0d1117")
        controls.pack(pady=12)

        # Target selector
        tk.Label(controls, text="Target:", fg="#c9d1d9", bg="#0d1117").grid(row=0, column=0, padx=6, pady=4, sticky="w")
        self.target_var = tk.StringVar(value="Entire Screen")
        self.target_menu = ttk.Combobox(controls, textvariable=self.target_var, values=["Entire Screen", "Browser - Example Page", "Chat App - Conversation"], state="readonly", width=28)
        self.target_menu.grid(row=0, column=1, padx=6, pady=4)
        refresh_btn = tk.Button(controls, text="↻", command=lambda: messagebox.showinfo("UI Only", "Refresh targets (visual only)"))
        refresh_btn.grid(row=0, column=2, padx=(4,0))

        # Buttons: Quick Scan, Scan 15m, Toggle
        btn_frame = tk.Frame(controls, bg="#0d1117")
        btn_frame.grid(row=1, column=0, columnspan=3, pady=(12,0))

        quick_btn = tk.Button(btn_frame, text="Quick Scan", bg="#d73a49", fg="white", width=12, command=lambda: messagebox.showinfo("UI Only", "Quick Scan (visual only)"))
        quick_btn.pack(side="left", padx=6)
        scan15_btn = tk.Button(btn_frame, text="Scan 15m", bg="#0969da", fg="white", width=12, command=lambda: messagebox.showinfo("UI Only", "Scan 15m (visual only)"))
        scan15_btn.pack(side="left", padx=6)

        # Toggle button appearance
        self.toggle_state = tk.BooleanVar(value=False)
        def toggle():
            self.toggle_state.set(not self.toggle_state.get())
            state = self.toggle_state.get()
            self.program_status.config(text=("● Active" if state else "● Disabled"), fg=("#28a745" if state else "#8b949e"))
        toggle_btn = tk.Button(btn_frame, text="Turn On", bg="#28a745", fg="white", width=12, command=toggle)
        toggle_btn.pack(side="left", padx=6)

        # --- Settings tab ---
        sframe = ctk.CTkFrame(settings, fg_color="#0d1117") if USE_CTK else tk.Frame(settings, bg="#0d1117")
        sframe.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(sframe, text="Settings (visual only)", fg="#f0f6fc", bg="#0d1117", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        chk1 = tk.Checkbutton(sframe, text="Notifications", fg="#c9d1d9", bg="#0d1117")
        chk1.pack(anchor="w", pady=6)
        chk2 = tk.Checkbutton(sframe, text="Enable Hitboxes", fg="#c9d1d9", bg="#0d1117")
        chk2.pack(anchor="w", pady=6)
        chk3 = tk.Checkbutton(sframe, text="Strict Mode", fg="#c9d1d9", bg="#0d1117")
        chk3.pack(anchor="w", pady=6)

        # --- Audit Log tab ---
        a_top = ctk.CTkFrame(audit_log, fg_color="#0d1117") if USE_CTK else tk.Frame(audit_log, bg="#0d1117")
        a_top.pack(fill="x", padx=12, pady=(8,6))
        quick_header_btn = tk.Button(a_top, text="Quick Scan", bg="#d73a49", fg="white", command=lambda: messagebox.showinfo("UI Only", "Quick Scan (visual only)"))
        quick_header_btn.pack(side="left", padx=6)
        clear_btn = tk.Button(a_top, text="Clear Log", bg="#d73a49", fg="white", command=lambda: messagebox.showinfo("UI Only", "Clear Log (visual only)"))
        clear_btn.pack(side="right", padx=6)

        # Log area
        log_area = tk.Text(audit_log, height=20, bg="#0d1117", fg="#c9d1d9")
        log_area.pack(fill="both", expand=True, padx=12, pady=(8,12))
        log_area.insert("1.0", "📋 Audit Log (visual only)\n\nNo events (UI-only mode).")
        log_area.config(state="disabled")

        # --- Credits tab ---
        cred_frame = ctk.CTkFrame(credits, fg_color="#0d1117") if USE_CTK else tk.Frame(credits, bg="#0d1117")
        cred_frame.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(cred_frame, text="Securely", fg="#f0f6fc", bg="#0d1117", font=("Segoe UI", 14, "bold")).pack()
        tk.Label(cred_frame, text="A simple UI-only mockup for testing visuals.", fg="#8b949e", bg="#0d1117").pack(pady=(6,12))
        learn_btn = tk.Button(cred_frame, text="Learn More", bg="#0969da", fg="white", command=lambda: webbrowser.open("https://delexoo.github.io/Securely/"))
        learn_btn.pack(pady=8)

        # Center window on screen
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

if __name__ == "__main__":
    app = VisualApp()
    app.mainloop()
