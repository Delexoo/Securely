import tkinter as tk
from tkinter import messagebox

# Try to use CustomTkinter for modern UI, fallback to regular tkinter
try:
    import customtkinter as ctk
    USE_CTK = True
except ImportError:
    USE_CTK = False
    print("CustomTkinter not available, using standard tkinter")

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
WIN11TOAST_AVAILABLE = False

# Try to import win11toast
try:
    from win11toast import notify as win11_notify
    WIN11TOAST_AVAILABLE = True
except ImportError:
    WIN11TOAST_AVAILABLE = False

# Try to import win10toast
try:
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    WIN10TOAST_AVAILABLE = True
except ImportError:
    WIN10TOAST_AVAILABLE = False


def show_notification(title, message, duration=10):
    """
    Show a Windows notification with multiple fallback methods
    """
    notification_sent = False
    
    # Try win11toast first
    if not notification_sent:
        try:
            if WIN11TOAST_AVAILABLE:
                win11_notify(title, message, duration=duration)
                notification_sent = True
                print(f"Notification sent via win11toast: {title}")
        except Exception as e:
            print(f"win11toast failed: {e}")
    
    # Try win10toast
    if not notification_sent:
        try:
            if WIN10TOAST_AVAILABLE and toaster:
                toaster.show_toast(title, message, duration=duration, threaded=True)
                notification_sent = True
                print(f"Notification sent via win10toast: {title}")
        except Exception as e:
            print(f"win10toast failed or not available: {e}")
    
    # Try winrt (Windows Runtime)
    if not notification_sent and WINRT_AVAILABLE:
        try:
            toast_xml = f"""
            <toast>
                <visual>
                    <binding template="ToastText02">
                        <text id="1">{title}</text>
                        <text id="2">{message}</text>
                    </binding>
                </visual>
            </toast>
            """
            doc = XmlDocument()
            doc.load_xml(toast_xml)
            notifier = ToastNotificationManager.create_toast_notifier("Securely Test")
            t = ToastNotification(doc)
            notifier.show(t)
            notification_sent = True
            print(f"Notification sent via winrt: {title}")
        except Exception as e:
            print(f"winrt notification failed: {e}")
    
    # Final fallback: messagebox
    if not notification_sent:
        messagebox.showinfo(title, message)
        print(f"Notification sent via messagebox: {title}")


def on_test_button_click():
    """Handle the test button click event"""
    # Hardcoded notification based on phishing email detection
    show_notification(
        title="⚠️ Phishing Email Detected",
        message="Securely detected a phishing email!\n\nSuspicious email from 'Bank of America' detected:\n• Suspicious sender domain: ameribank7.com\n• Contains urgent login alert\n• Suspicious reset password link detected\n\nDo not click any links in this email!",
        duration=15
    )


def main():
    """Create and run the main window"""
    if USE_CTK:
        # Use CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        root = ctk.CTk()
        root.title("Securely Test Notification")
        root.geometry("400x200")
        
        # Create button
        button = ctk.CTkButton(
            root,
            text="Test Button",
            command=on_test_button_click,
            width=200,
            height=50,
            font=("Arial", 16)
        )
        button.pack(pady=50)
    else:
        # Use standard tkinter
        root = tk.Tk()
        root.title("Securely Test Notification")
        root.geometry("400x200")
        root.configure(bg="#2b2b2b")
        
        # Create button
        button = tk.Button(
            root,
            text="Test Button",
            command=on_test_button_click,
            width=20,
            height=3,
            font=("Arial", 14),
            bg="#1f538d",
            fg="white",
            activebackground="#2d6bb3",
            activeforeground="white"
        )
        button.pack(pady=50)
    
    root.mainloop()


if __name__ == "__main__":
    main()

