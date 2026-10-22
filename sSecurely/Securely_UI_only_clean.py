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
