# Securely
#### Video Demo: <URL HERE>
#### Description:

Securely is a real-time cybersecurity monitoring application that uses artificial intelligence and optical character recognition (OCR) to detect security threats on your computer screen. The application continuously monitors your screen content, analyzes it for potential threats like phishing attempts, malware warnings, suspicious websites, and social engineering attacks, then alerts you immediately via desktop notifications.

## Features

**Real-Time Threat Detection**: Securely takes screenshots of your screen every second, extracts text using OCR technology, and analyzes the content using your API (Groq key on Supabase) or Groq to identify security threats.

**AI-Powered Analysis**: The application uses Groq (or your own API) to intelligently detect various types of cyber threats including phishing emails, suspicious websites, malware warnings, and social engineering attempts.

**Desktop Notifications**: When a threat is detected, Securely immediately sends a desktop notification alerting you to the potential security risk.

**Comprehensive Audit Log**: All detected threats are logged in a detailed audit log, allowing you to review past threats and understand patterns in security risks.

**Customizable Settings**: Users can customize notification preferences, enable or disable sound alerts, adjust monitoring sensitivity, and configure auto-pause features for login pages to protect credentials.

**Quick Scan Mode**: In addition to continuous monitoring, users can run quick scans on-demand to check their current screen for threats.

**Educational Features**: The application includes educational components to help users learn about different types of security threats and how to protect themselves.

## Technical Implementation

Securely is built using Python and implements several key technologies:

**CustomTkinter**: The graphical user interface is built using CustomTkinter, providing a modern, dark-themed interface that's both functional and visually appealing.

**pytesseract**: Optical Character Recognition (OCR) is performed using pytesseract, which extracts text from screenshots for analysis. The application automatically detects Tesseract OCR installation on Windows systems.

**mss**: Screen capture functionality is implemented using the mss library, which efficiently captures screenshots at regular intervals without significant performance impact.

**Groq API / your server**: Threat analysis is performed by your Vercel API (key stored on Supabase), or optionally by Groq directly for local dev. The app sends OCR text to your API when `SECURELY_API_URL` is set so the key never lives in the distributed app.

**Multi-threading**: The application uses Python's threading module to run monitoring in the background, ensuring the GUI remains responsive while continuous monitoring occurs.

**Windows Notifications**: Desktop notifications are implemented using multiple fallback methods including win11toast, win10toast, and native Windows APIs to ensure compatibility across different Windows versions.

## File Structure

**Securely_CTK.py**: This is the main application file containing the complete implementation of Securely. It includes the GUI class (`MainWindow`), monitoring thread logic, AI analysis functions, notification handlers, and all core functionality. The file is approximately 5,000+ lines and represents the full-featured version of the application.

**requirements.txt**: Lists all Python dependencies required to run the application, including customtkinter, Pillow, mss, pytesseract, requests, win10toast, and win11toast.

**Securely_CTK.spec**: PyInstaller specification file used to build the Windows executable (.exe) version of the application.

**create_icon.py**: Utility script for creating application icons.

**assets/**: Directory containing application assets such as logos and images.

**instant_analysis/**: Directory where instant analysis screenshots are stored.

**training_screenshots/**: Directory containing training data screenshots used for threat detection.

**dist/**: Directory containing the built executable and distribution files.

**build/**: Directory containing build artifacts from PyInstaller.

## Key Design Decisions

**Multi-threaded Architecture**: The decision to use multi-threading was crucial for maintaining a responsive GUI while performing continuous screen monitoring. The monitoring runs in a separate thread, preventing the application from freezing during screenshot capture and AI analysis operations.

**Multiple Notification Methods**: To ensure compatibility across different Windows versions, the application implements multiple notification methods with fallback mechanisms. This design decision ensures users receive alerts regardless of their Windows version.

**Auto-pause on Sensitive Pages**: The application automatically pauses monitoring when it detects login or payment pages. This feature protects user credentials from being captured and analyzed, addressing privacy concerns while maintaining security monitoring.

**Caching AI Analysis**: To reduce API costs and improve performance, the application implements an in-memory cache for AI analysis results. This prevents redundant API calls for similar content.

**OCR Text Extraction**: The choice to use OCR rather than direct text extraction was necessary because many threats appear as images or in non-selectable text formats. OCR ensures the application can detect threats regardless of how they're displayed on screen.

## Installation and Usage

To run Securely:

1. Install Python 3.8 or higher
2. Install Tesseract OCR from the official website
3. Install required Python packages: `pip install -r requirements.txt`
4. **For distribution (selling the app):** Do **not** put your Groq API key in the app. Store it in **Supabase Vault** and deploy the API to Vercel (see `api/README.md`). Then set **`SECURELY_API_URL`** (e.g. `https://your-project.vercel.app/api/analyze`) so the desktop app calls your API; optionally set **`SECURELY_API_JWT`** (Supabase JWT) if your API requires auth.
5. Run the application: `python Securely_CTK.py`

Alternatively, use the pre-built executable in the `dist` folder. When distributing, never ship an API key — use `SECURELY_API_URL` so the key stays on Supabase/Vercel.

## Challenges and Solutions

One significant challenge was ensuring the application could reliably capture and analyze screen content without impacting system performance. This was solved through efficient screenshot capture using mss, optimized OCR processing, and asynchronous AI API calls.

Another challenge was ensuring cross-platform notification compatibility. This was addressed by implementing multiple notification methods with automatic fallback, ensuring alerts work on Windows 10, Windows 11, and other Windows versions.

Privacy concerns were addressed through the auto-pause feature on sensitive pages and by making training screenshot capture optional and disabled by default.

## Future Enhancements

Potential future enhancements include:
- Support for macOS and Linux platforms
- Machine learning model training on user-specific threat patterns
- Integration with antivirus software for enhanced threat detection
- Cloud-based threat intelligence sharing
- Mobile app companion for remote monitoring

## Conclusion

Securely represents a comprehensive solution to real-time cybersecurity threat detection, combining modern AI technology with practical user interface design. The application demonstrates proficiency in Python programming, GUI development, API integration, multi-threading, and system-level programming concepts learned throughout CS50x.

