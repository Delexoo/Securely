"""
Securely_Updated.py

Compact UI-only visual mockup for Securely.
Uses customtkinter when available, falls back to tkinter/ttk.
This is a visual mock — no AI/monitoring code.
"""

import os
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

try:
	import customtkinter as ctk
	CTK_AVAILABLE = True
except Exception:
	CTK_AVAILABLE = False

APP_TITLE = "Securely — UI Mock"
ICON_PATH = r"C:\Program Files\Securely-Assets\SecurelyLogo.ico"

# Simple color constants
BKG = "#0b0f13"
PANEL = "#010409"
TITLE_BAR = "#0b1117"
TEXT_MAIN = "#c9d1d9"
TEXT_MUTED = "#8b949e"
BTN_RED = "#d73a49"
BTN_BLUE = "#238636"
BTN_GREEN = "#2ea043"


class VisualMain(ctk.CTk if CTK_AVAILABLE else tk.Tk):
	def __init__(self):
		super().__init__()
		self.title(APP_TITLE)
		self.geometry("260x200")
		self.minsize(260, 200)

		# Try to set taskbar icon
		try:
			if os.path.exists(ICON_PATH):
				self.iconbitmap(ICON_PATH)
		except Exception:
			pass

		# Build UI
		self._tooltip_label = None
		self._build_ui()
		self.add_simple_tooltips()

	def _build_ui(self):
		if CTK_AVAILABLE:
			self._build_ctk()
		else:
			self._build_tk()

	def _build_ctk(self):
		self.configure(fg_color=BKG)
		# Frameless titlebar
		self.overrideredirect(True)
		top = ctk.CTkFrame(self, fg_color=TITLE_BAR, height=28)
		top.pack(fill="x", side="top")

		title_lbl = ctk.CTkLabel(top, text="Securely", text_color=TEXT_MAIN, fg_color=TITLE_BAR, font=ctk.CTkFont(size=10, weight="bold"))
		title_lbl.pack(side="left", padx=(8, 6))

		ctrl = ctk.CTkFrame(top, fg_color=TITLE_BAR)
		ctrl.pack(side="right", padx=4)
		b_min = ctk.CTkButton(ctrl, text="−", width=20, height=18, fg_color="transparent", hover_color="#30363d", text_color=TEXT_MUTED, command=self._minimize)
		b_min.pack(side="right", padx=2, pady=3)
		b_res = ctk.CTkButton(ctrl, text="⛶", width=20, height=18, fg_color="transparent", hover_color="#58a6ff", text_color=TEXT_MUTED, command=self._toggle_size)
		b_res.pack(side="right", padx=2, pady=3)
		b_close = ctk.CTkButton(ctrl, text="✕", width=20, height=18, fg_color="transparent", hover_color="#d73a49", text_color=TEXT_MUTED, command=self.destroy)
		b_close.pack(side="right", padx=2, pady=3)

		top.bind("<Button-1>", self._start_move)
		top.bind("<B1-Motion>", self._on_move)

		# Tab view
		self.tab_view = ctk.CTkTabview(self, width=240, height=140)
		self.tab_view.pack(padx=8, pady=(6,8), fill="both", expand=True)
		self.tab_view.add("📊")
		self.tab_view.add("⚙️")
		self.tab_view.add("📋")
		self.tab_view.add("ℹ️")

		# Dashboard
		dash = ctk.CTkFrame(self.tab_view.tab("📊"), fg_color=BKG)
		dash.pack(fill="both", expand=True, padx=6, pady=6)
		self.status_label = ctk.CTkLabel(dash, text="● Disabled", text_color=TEXT_MUTED, fg_color=BKG, font=ctk.CTkFont(size=10, weight="bold"))
		self.status_label.pack(fill="x")

		controls = ctk.CTkFrame(dash, fg_color=BKG)
		controls.pack(pady=6)
		self.target_var = tk.StringVar(value="Entire Screen")
		self.target_menu = ctk.CTkOptionMenu(controls, values=["Entire Screen", "Browser — Example", "Chat — Conversation"], variable=self.target_var, width=120)
		self.target_menu.grid(row=0, column=0, padx=(0,6))
		self.refresh = ctk.CTkButton(controls, text="↻", width=26, height=20, command=lambda: messagebox.showinfo("UI Only","Refresh targets (visual only)"))
		self.refresh.grid(row=0, column=1)

		btn_row = ctk.CTkFrame(controls, fg_color=BKG)
		btn_row.grid(row=1, column=0, columnspan=2, pady=(6,0))
		ctk.CTkButton(btn_row, text="Quick Scan", fg_color=BTN_RED, width=70, height=20, command=lambda: messagebox.showinfo("UI Only","Quick Scan (visual only)")).pack(side="left", padx=4)
		ctk.CTkButton(btn_row, text="Scan 15m", fg_color=BTN_BLUE, width=70, height=20, command=lambda: messagebox.showinfo("UI Only","Scan 15m (visual only)")).pack(side="left", padx=4)
		ctk.CTkButton(btn_row, text="Turn On", fg_color=BTN_GREEN, width=70, height=20, command=self._toggle_monitor).pack(side="left", padx=4)

		# Minimal content for other tabs
		ctk.CTkLabel(self.tab_view.tab("⚙️"), text="Settings (visual only)", text_color=TEXT_MAIN, fg_color=BKG).pack(padx=8, pady=8)
		ctk.CTkLabel(self.tab_view.tab("📋"), text="Audit Log (visual only)", text_color=TEXT_MAIN, fg_color=BKG).pack(padx=8, pady=8)
		cred = ctk.CTkFrame(self.tab_view.tab("ℹ️"), fg_color=BKG)
		cred.pack(fill="both", expand=True)
		ctk.CTkLabel(cred, text="Securely", text_color=TEXT_MAIN, fg_color=BKG, font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(8,2))
		ctk.CTkButton(cred, text="Learn More", fg_color=BTN_BLUE, width=120, height=28, command=lambda: webbrowser.open("https://delexoo.github.io/Securely/")).pack()

	def _build_tk(self):
		self.configure(bg=BKG)
		top = tk.Frame(self, bg=TITLE_BAR, height=28)
		top.pack(fill="x", side="top")
		title = tk.Label(top, text="Securely", fg=TEXT_MAIN, bg=TITLE_BAR)
		title.pack(side="left", padx=8)
		btn_frame = tk.Frame(top, bg=TITLE_BAR)
		btn_frame.pack(side="right")
		minb = tk.Button(btn_frame, text="−", command=self._minimize)
		minb.pack(side="left")
		clb = tk.Button(btn_frame, text="✕", command=self.destroy)
		clb.pack(side="left")

		nb = ttk.Notebook(self)
		nb.pack(fill="both", expand=True, padx=8, pady=8)
		p1 = tk.Frame(nb, bg=BKG)
		p2 = tk.Frame(nb, bg=BKG)
		p3 = tk.Frame(nb, bg=BKG)
		p4 = tk.Frame(nb, bg=BKG)
		nb.add(p1, text="📊")
		nb.add(p2, text="⚙️")
		nb.add(p3, text="📋")
		nb.add(p4, text="ℹ️")

		st = tk.Label(p1, text="● Disabled", fg=TEXT_MUTED, bg=BKG)
		st.pack(fill="x", padx=6, pady=4)
		controls = tk.Frame(p1, bg=BKG)
		controls.pack(pady=6)
		self.target_var = tk.StringVar(value="Entire Screen")
		cb = ttk.Combobox(controls, textvariable=self.target_var, values=["Entire Screen","Browser — Example"], width=18, state='readonly')
		cb.grid(row=0, column=0, padx=(0,6))
		rb = tk.Button(controls, text="↻", command=lambda: messagebox.showinfo("UI Only","Refresh targets (visual only)"))
		rb.grid(row=0, column=1)

	def _start_move(self, evt):
		self._drag_x = evt.x
		self._drag_y = evt.y

	def _on_move(self, evt):
		x = self.winfo_x() + (evt.x - getattr(self, '_drag_x', 0))
		y = self.winfo_y() + (evt.y - getattr(self, '_drag_y', 0))
		self.geometry(f"+{x}+{y}")

	def _minimize(self):
		try:
			self.iconify()
		except Exception:
			try:
				self.withdraw()
			except Exception:
				pass

	def _toggle_size(self):
		if self.winfo_width() < 500:
			self.geometry("820x560")
		else:
			self.geometry("260x200")

	def _toggle_monitor(self):
		if hasattr(self, 'status_label'):
			text = self.status_label.cget('text')
			if 'Disabled' in text:
				self.status_label.configure(text='● Active', text_color=BTN_GREEN)
			else:
				self.status_label.configure(text='● Disabled', text_color=TEXT_MUTED)

	def add_simple_tooltips(self):
		"""Add simple in-window tooltips for widgets: show small label above widget on hover."""
		def create_tooltip(widget, text):
			def show_tooltip(event=None):
				try:
					if getattr(self, '_tooltip_label', None):
						self._tooltip_label.destroy()
					rx = widget.winfo_rootx() - self.winfo_rootx()
					y = widget.winfo_rooty() - self.winfo_rooty()
					xpos = rx + max(0, widget.winfo_width() // 2 - 40)
					ypos = y - 24
					if CTK_AVAILABLE:
						lbl = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=10), text_color=TEXT_MAIN, fg_color=PANEL, corner_radius=5, padx=8, pady=4, wraplength=180)
						lbl.place(x=xpos - 8, y=ypos - 4)
					else:
						lbl = tk.Label(self, text=text, bg=PANEL, fg=TEXT_MAIN)
						lbl.place(x=xpos - 8, y=ypos - 4)
					self._tooltip_label = lbl
				except Exception:
					pass

			def hide_tooltip(event=None):
				try:
					if getattr(self, '_tooltip_label', None):
						self._tooltip_label.destroy()
						self._tooltip_label = None
				except Exception:
					pass

			widget.bind("<Enter>", show_tooltip)
			widget.bind("<Leave>", hide_tooltip)

		try:
			if hasattr(self, 'target_menu'):
				create_tooltip(self.target_menu, "Select a target window or the entire screen")
		except Exception:
			pass
		try:
			if hasattr(self, 'refresh'):
				create_tooltip(self.refresh, "Refresh available targets (visual only)")
		except Exception:
			pass

		def setup_tabs():
			try:
				seg = getattr(self.tab_view, '_segmented_button', None)
				texts = ["Dashboard", "Settings", "Audit Log", "Credits"]
				if seg:
					for i, b in enumerate(seg.winfo_children()):
						if i < len(texts):
							create_tooltip(b, texts[i])
			except Exception:
				pass

		try:
			self.after(400, setup_tabs)
		except Exception:
			pass


def make_app():
	if CTK_AVAILABLE:
		ctk.set_appearance_mode('dark')
		ctk.set_default_color_theme('dark-blue')
	return VisualMain()


if __name__ == '__main__':
	app = make_app()
	app.mainloop()
		ctk.CTkCheckBox(sett, text="More Strict").pack(anchor="w", padx=12, pady=4)

		# Audit tab
		audit = ctk.CTkFrame(self.tab_view.tab("📋"), fg_color=BKG)
		audit.pack(fill="both", expand=True)
		header = ctk.CTkFrame(audit, fg_color=BKG)
		header.pack(fill="x", padx=6, pady=(4,4))
		ctk.CTkButton(header, text="Quick Scan", fg_color=BTN_RED, width=80, height=20, command=lambda: messagebox.showinfo("UI Only","Quick Scan (visual only)")) .pack(side="left", padx=4)
		ctk.CTkButton(header, text="Clear Log", fg_color=BTN_RED, width=80, height=20, command=lambda: messagebox.showinfo("UI Only","Clear Log (visual only)")) .pack(side="right", padx=4)

		# Reduce audit textbox size slightly so it fits inside compact window
		self.log_text = ctk.CTkTextbox(audit, width=190, height=50)
		self.log_text.pack(fill="both", expand=True, padx=6, pady=(4,6))
		self.log_text.insert("0.0", "📋 Audit Log (visual only)\n\nNo recorded events — UI-only mode.")
		self.log_text.configure(state="disabled")

		# Credits tab
		cred = ctk.CTkFrame(self.tab_view.tab("ℹ️"), fg_color=BKG)
		cred.pack(fill="both", expand=True)
		ctk.CTkLabel(cred, text="Securely", text_color=TEXT_MAIN, fg_color=BKG, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12,6))
		ctk.CTkLabel(cred, text="Visual mockup for testing UI layout.", text_color=TEXT_MUTED, fg_color=BKG).pack(pady=(0,8))
		ctk.CTkButton(cred, text="Learn More", fg_color=BTN_BLUE, width=120, height=28, command=lambda: webbrowser.open("https://delexoo.github.io/Securely/")).pack()

	def _toggle_size(self):
		if self.winfo_width() < 500:
			self.geometry("820x560")
		else:
			# Return to compact size (updated narrower width)
			self.geometry("260x200")

	def _minimize(self):
		"""Minimize the window (works for both CTk and tkinter fallback)."""
		try:
			self.iconify()
		except Exception:
			try:
				# Fallback for some environments
				self.withdraw()
			except Exception:
				pass

	def _toggle_monitor(self):
		# simple visual toggle
		text = self.status_label.cget('text')
		if 'Disabled' in text:
			self.status_label.configure(text='● Active', text_color=BTN_GREEN)
		else:
			self.status_label.configure(text='● Disabled', text_color=TEXT_MUTED)

	def add_simple_tooltips(self):
		"""Add simple in-window tooltips for tabs and controls."""
		try:
			self._tooltip_label = None
			def create_tooltip(widget, text):
				def show_tooltip(event):
					try:
						# Remove existing tooltip if present
						if getattr(self, '_tooltip_label', None):
							try:
								self._tooltip_label.destroy()
							except Exception:
								pass

						# Compute position relative to main window
						try:
							rx = widget.winfo_rootx() - self.winfo_rootx()
							ry:
							ry:
							pass
							except Exception:
							pass
						except Exception:
							rx = widget.winfo_x()
							ry:
							ry:
							pass
							except Exception:
							pass
						try:
							ry:
							pass
							except Exception:
							pass
						ry:
							ry:
							pass
							except Exception:
							pass
						ry:
							ry:
							pass
							except Exception:
							pass
						ry:
						ry:
						pass
						except Exception:
						pass
					# Fallback coords
					rx = widget.winfo_rootx() - self.winfo_rootx() if hasattr(widget, 'winfo_rootx') else widget.winfo_x()
					ry:
						ry:
						y = widget.winfo_rooty() - self.winfo_rooty()
						except Exception:
						y = widget.winfo_y()

					xpos = rx + max(0, widget.winfo_width() // 2 - 40)
					ypos = y - 24

					lbl = ctk.CTkLabel(self, text=text,
						font=ctk.CTkFont(size=10),
						text_color=TEXT_MAIN,
						fg_color=PANEL,
						corner_radius=5,
						padx=8, pady=4,
						wraplength=200)
					lbl.place(x=xpos - 8, y=ypos - 4)
					self._tooltip_label = lbl
				except Exception as e:
					print(f"Show tooltip error: {e}")

				def hide_tooltip(event):
					try:
						if getattr(self, '_tooltip_label', None):
							self._tooltip_label.destroy()
							self._tooltip_label = None
					except Exception as e:
						print(f"Hide tooltip error: {e}")

				widget.bind("<Enter>", show_tooltip)
				widget.bind("<Leave>", hide_tooltip)

			# Bind to target menu and refresh button
			try:
				create_tooltip(self.target_menu, "Select a target window or the entire screen")
			except Exception:
				pass
			try:
				create_tooltip(self.refresh, "Refresh available targets (visual only)")
			except Exception:
				pass

			# Add tooltips to the tab buttons after UI is ready
			def setup_after_delay():
				try:
					segmented_button = getattr(self.tab_view, '_segmented_button', None)
					tooltip_texts = ["Dashboard", "Settings", "Audit Log", "Credits"]
					if segmented_button:
						children = segmented_button.winfo_children()
						for i, button in enumerate(children):
							if i < len(tooltip_texts):
								create_tooltip(button, tooltip_texts[i])
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
					print(f"Tooltip setup error: {e}")

			self.after(500, setup_after_delay)
		except Exception as e:
			print(f"add_simple_tooltips error: {e}")


class VisualMainTK(tk.Tk):
	"""Fallback simple UI built with tkinter when CTk not available."""
	def __init__(self):
		super().__init__()
		self.title(APP_TITLE)
		self.geometry("420x320")
		self.minsize(420, 320)

		# Try to set the app icon for the taskbar
		icon_path = r"C:\Program Files\Securely-Assets\SecurelyLogo.ico"
		try:
			if os.path.exists(icon_path):
				self.iconbitmap(icon_path)
		except Exception:
			pass

		top = tk.Frame(self, bg=TITLE_BAR)
		top.pack(fill="x", side="top")
		logo = tk.Canvas(top, width=36, height=24, bg=TITLE_BAR, highlightthickness=0)
		logo.pack(side="left", padx=8, pady=6)
		logo.create_oval(2, 2, 30, 22, fill="#238636", outline="")
		logo.create_text(16, 12, text="S", fill="white", font=("Segoe UI", 10, "bold"))

		title_lbl = tk.Label(top, text="Securely", fg=TEXT_MAIN, bg=TITLE_BAR, font=("Segoe UI", 12, "bold"))
		title_lbl.pack(side="left", padx=(6, 0))

		# Use ttk Notebook for tabs
		tabs = ttk.Notebook(self)
		tabs.pack(fill="both", expand=True, padx=8, pady=8)

		tab_dash = tk.Frame(tabs, bg=BKG)
		tab_sett = tk.Frame(tabs, bg=BKG)
		tab_audit = tk.Frame(tabs, bg=BKG)
		tab_cred = tk.Frame(tabs, bg=BKG)

		tabs.add(tab_dash, text="📊 Dashboard")
		tabs.add(tab_sett, text="⚙️ Settings")
		tabs.add(tab_audit, text="📋 Audit Log")
		tabs.add(tab_cred, text="ℹ️ Credits")

		# Dashboard content
		self.status_label = tk.Label(tab_dash, text="● Disabled", fg=TEXT_MUTED, bg=PANEL, font=("Segoe UI", 10, "bold"))
		self.status_label.pack(fill="x", padx=6, pady=(6,6))

		inner = tk.Frame(tab_dash, bg=BKG)
		inner.pack(pady=6)
		tk.Label(inner, text="Target:", fg="#c9d1d9", bg=BKG).grid(row=0, column=0, padx=6)
		self.target_var = tk.StringVar(value="Entire Screen")
		ttk.Combobox(inner, textvariable=self.target_var, values=["Entire Screen", "Browser — Example"]).grid(row=0, column=1)
		tk.Button(inner, text="Quick Scan", bg=BTN_RED, fg="white", command=lambda: messagebox.showinfo("UI Only","Quick Scan (visual only)")).grid(row=1, column=0, columnspan=2, pady=8)


if __name__ == "__main__":
	app = make_app()
	app.mainloop()