using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Globalization;
using System.Speech.Recognition;
using System.Text.Json;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

namespace SecurelyShell;

internal static class Program
{
    [STAThread]
    private static void Main(string[] args)
    {
        var url = args.Length > 0 ? args[0] : "https://securely.local/index.html";
        Environment.SetEnvironmentVariable("WEBVIEW2_DEFAULT_BACKGROUND_COLOR", "00000000");
        Application.SetHighDpiMode(HighDpiMode.PerMonitorV2);
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
        Application.ThreadException += (_, e) =>
        {
            MessageBox.Show(
                "Securely hit a problem and recovered.\n\n" + (e.Exception.Message.Length > 180 ? e.Exception.Message[..180] : e.Exception.Message),
                "Securely",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning);
        };
        AppDomain.CurrentDomain.UnhandledException += (_, e) =>
        {
            var ex = e.ExceptionObject as Exception;
            MessageBox.Show(
                "Securely needs to close.\n\n" + (ex?.Message is { Length: > 0 } m ? (m.Length > 180 ? m[..180] : m) : "Unexpected error."),
                "Securely",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error);
        };
        Application.Run(new ShellForm(url));
    }
}

internal sealed class ShellForm : Form
{
    private readonly WebView2 view = new() { Dock = DockStyle.Fill };
    private readonly System.Windows.Forms.Timer anim = new() { Interval = 12 };
    private readonly System.Windows.Forms.Timer reveal = new() { Interval = 8 };
    private readonly System.Windows.Forms.Timer pin = new() { Interval = 200 };
    private bool userMoved;
    private bool animating;
    private bool excludeCapture;
    private int shapeWidth;
    private int shapeHeight;
    private int shapeDiameter;
    private bool followArmed;
    private Point followGrab;
    private readonly System.Windows.Forms.Timer follow = new() { Interval = 16 };
    private NotifyIcon? tray;
    private readonly string pageUrl;
    private Form? dashboard;
    private WebView2? dashboardView;
    private bool dashboardLoading;
    private string pendingDashboardTab = "dashboard";
    private bool shellClosing;
    private long animStart;
    private Rectangle animFrom;
    private Rectangle animTo;
    private bool widgetShown = true;
    private bool revealAnimating;
    private bool revealHiding;
    private bool revealTiming;
    private long revealStart;
    private Rectangle revealFrom;
    private Rectangle revealTo;
    private Rectangle revealHome;
    private const int RevealMs = 280;
    private int lastCssWidth = 368;
    private int lastCssHeight = 52;

    public ShellForm(string url)
    {
        pageUrl = url;
        Text = "Securely";
        Icon = (Icon)AppIcon().Clone();
        FormBorderStyle = FormBorderStyle.None;
        TopMost = true;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.Manual;
        BackColor = Color.Black;
        PlaceAtTopCenter();
        Controls.Add(view);
        view.DefaultBackgroundColor = Color.Transparent;
        anim.Tick += (_, _) => StepAnim();
        reveal.Tick += (_, _) => StepReveal();
        pin.Tick += (_, _) => PinTopmost();
        follow.Tick += (_, _) => StepFollow();
        Shown += (_, _) =>
        {
            PinTopmost();
            pin.Start();
            Emit(new { ok = true, ready = true });
        };
        Load += async (_, _) =>
        {
            await OpenPage(url);
        };
        var reader = new Thread(ReadCommands) { IsBackground = true };
        reader.Start();
    }

    protected override CreateParams CreateParams
    {
        get
        {
            const int WS_EX_TOPMOST = 0x00000008;
            const int WS_EX_NOREDIRECTIONBITMAP = 0x00200000;
            var parameters = base.CreateParams;
            parameters.ExStyle |= WS_EX_TOPMOST | WS_EX_NOREDIRECTIONBITMAP;
            return parameters;
        }
    }

    protected override void OnHandleCreated(EventArgs e)
    {
        base.OnHandleCreated(e);
        ClearBackdrop();
        PlaceAtTopCenter();
        RegisterHotKey(Handle, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, 0x48);
        RegisterHotKey(Handle, 2, MOD_CONTROL | MOD_NOREPEAT, 0xDC);
        RegisterHotKey(Handle, 3, MOD_CONTROL | MOD_NOREPEAT, 0x0D);
        RegisterHotKey(Handle, 4, MOD_CONTROL | MOD_NOREPEAT, 0x52);
        RegisterHotKey(Handle, 5, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, 0xDC);
        InstallVisibilityHook();
    }

    protected override void OnDpiChanged(DpiChangedEventArgs e)
    {
        base.OnDpiChanged(e);
        anim.Stop();
        animating = false;
        StopReveal();
        if (!widgetShown)
        {
            Hide();
            if (IsHandleCreated) ShowWindow(Handle, SW_HIDE);
        }
        ApplyBounds(TargetBounds(lastCssWidth, lastCssHeight));
        if (dashboard != null && !dashboard.IsDisposed) PlaceDashboard(dashboard);
    }

    protected override void OnFormClosed(FormClosedEventArgs e)
    {
        for (var id = 1; id <= 9; id++) UnregisterHotKey(Handle, id);
        if (keyboardHook != IntPtr.Zero)
        {
            UnhookWindowsHookEx(keyboardHook);
            keyboardHook = IntPtr.Zero;
        }
        if (tray != null)
        {
            tray.Visible = false;
            tray.Dispose();
        }
        reveal.Stop();
        EndRevealTiming();
        shellClosing = true;
        StopVoice();
        audioIo.Dispose();
        if (dashboard != null && !dashboard.IsDisposed) dashboard.Close();
        base.OnFormClosed(e);
    }

    protected override void OnDeactivate(EventArgs e)
    {
        base.OnDeactivate(e);
        NotifyPage(false);
        PinTopmost();
    }

    protected override void OnActivated(EventArgs e)
    {
        base.OnActivated(e);
        BeginInvoke(() => NotifyPage(true));
    }

    private void YieldFocus()
    {
        var shell = GetShellWindow();
        if (shell == IntPtr.Zero || shell == Handle) return;
        SetForegroundWindow(shell);
    }

    private void NotifyPage(bool active)
    {
        if (active && GetForegroundWindow() != Handle) return;
        var core = view.CoreWebView2;
        if (core == null) return;
        var flag = active ? "true" : "false";
        core.ExecuteScriptAsync($"window.onWidgetActive&&window.onWidgetActive({flag})");
    }

    protected override void WndProc(ref Message m)
    {
        const int WM_HOTKEY = 0x0312;
        if (m.Msg == WM_HOTKEY)
        {
            DispatchHotkey(m.WParam.ToInt32());
            return;
        }
        const int WM_NCHITTEST = 0x0084;
        const int HTTRANSPARENT = -1;
        if (m.Msg == WM_NCHITTEST)
        {
            var packed = unchecked((int)(m.LParam.ToInt64() & 0xFFFFFFFF));
            var screenX = (short)(packed & 0xFFFF);
            var screenY = (short)((packed >> 16) & 0xFFFF);
            if (GetWindowRect(Handle, out var window))
            {
                var localX = screenX - window.Left;
                var localY = screenY - window.Top;
                var width = window.Right - window.Left;
                var height = window.Bottom - window.Top;
                if (!InsideRoundedRect(localX, localY, width, height, WindowRadius(width, height)))
                {
                    m.Result = (IntPtr)HTTRANSPARENT;
                    return;
                }
            }
        }
        const int WM_WINDOWPOSCHANGING = 0x0046;
        if (m.Msg == WM_WINDOWPOSCHANGING)
        {
            var pos = System.Runtime.InteropServices.Marshal.PtrToStructure<WindowPos>(m.LParam);
            var reorder = (pos.flags & SWP_NOZORDER) == 0 && pos.hwndInsertAfter != HWND_TOPMOST;
            if (reorder && !DashboardIsOpen())
            {
                pos.hwndInsertAfter = HWND_TOPMOST;
                System.Runtime.InteropServices.Marshal.StructureToPtr(pos, m.LParam, false);
            }
        }
        base.WndProc(ref m);
    }

    private void PinTopmost()
    {
        if (!IsHandleCreated || !Visible || DashboardIsOpen()) return;
        if (GetTopWindow(IntPtr.Zero) == Handle) return;
        TopMost = true;
        SetWindowPos(Handle, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
    }

    private void HideWidget()
    {
        if (IsDisposed) return;
        if (!widgetShown && (!revealAnimating || revealHiding))
        {
            EnsureTray();
            tray!.Visible = true;
            return;
        }
        widgetShown = false;
        EnsureTray();
        tray!.Visible = true;
        follow.Stop();
        if (!AnimationsEnabled())
        {
            revealHome = Bounds;
            ParkHidden();
            return;
        }
        if (!revealAnimating) revealHome = Bounds;
        BeginSlide(Offscreen(revealHome), hiding: true);
    }

    private void ShowWidget()
    {
        if (IsDisposed) return;
        if (widgetShown && !revealAnimating)
        {
            PresentInstant();
            return;
        }
        widgetShown = true;
        if (tray != null) tray.Visible = false;
        follow.Stop();
        if (!AnimationsEnabled())
        {
            StopReveal();
            PresentInstant();
            return;
        }
        if (!revealAnimating)
        {
            revealHome = Bounds;
            var off = Offscreen(revealHome);
            Location = new Point(off.X, off.Y);
            PresentWindow();
        }
        BeginSlide(revealHome, hiding: false);
    }

    private void PresentInstant()
    {
        StopReveal();
        widgetShown = true;
        SettlePage();
        PresentWindow();
        Activate();
        if (tray != null) tray.Visible = false;
    }

    private void PresentWindow()
    {
        if (WindowState == FormWindowState.Minimized) WindowState = FormWindowState.Normal;
        Show();
        if (IsHandleCreated)
        {
            // The process starts hidden, and Windows ignores the first ShowWindow.
            ShowWindow(Handle, SW_SHOWNORMAL);
            ShowWindow(Handle, SW_SHOWNORMAL);
            SetWindowPos(Handle, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW);
        }
        PinTopmost();
        if (excludeCapture) ApplyCaptureAffinity();
    }

    private void BeginSlide(Rectangle to, bool hiding)
    {
        if (animating)
        {
            anim.Stop();
            animating = false;
        }
        revealFrom = new Rectangle(Left, Top, Width, Height);
        revealTo = to;
        revealHiding = hiding;
        revealStart = Environment.TickCount64;
        FadePage(hiding ? 0 : 1, easeIn: hiding);
        if (!revealTiming)
        {
            timeBeginPeriod(1);
            revealTiming = true;
        }
        if (!revealAnimating)
        {
            revealAnimating = true;
            reveal.Start();
        }
    }

    private bool revealStepping;

    private void StepReveal()
    {
        if (revealStepping) return;
        revealStepping = true;
        try
        {
            var t = Math.Clamp((Environment.TickCount64 - revealStart) / (double)RevealMs, 0, 1);
            var eased = revealHiding ? t * t * t : 1 - Math.Pow(1 - t, 3);
            if (t >= 1)
            {
                reveal.Stop();
                BeginInvoke(new Action(() =>
                {
                    if (revealHiding) ParkHidden();
                    else FinishShown();
                }));
                return;
            }
            var x = Lerp(revealFrom.X, revealTo.X, eased);
            var y = Lerp(revealFrom.Y, revealTo.Y, eased);
            if (IsHandleCreated && (x != Left || y != Top))
                SetWindowPos(Handle, HWND_TOPMOST, x, y, 0, 0, SWP_NOSIZE | SWP_NOACTIVATE);
        }
        finally
        {
            revealStepping = false;
        }
    }

    private void FinishShown()
    {
        StopReveal();
        Bounds = revealTo;
        SettlePage();
        Activate();
        PinTopmost();
        if (excludeCapture) ApplyCaptureAffinity();
    }

    private void ParkHidden()
    {
        StopReveal();
        Hide();
        if (IsHandleCreated) ShowWindow(Handle, SW_HIDE);
        if (revealHome.Width > 0) Bounds = revealHome;
        if (IsHandleCreated) ShowWindow(Handle, SW_HIDE);
    }

    private void StopReveal()
    {
        reveal.Stop();
        revealAnimating = false;
        EndRevealTiming();
    }

    private void EndRevealTiming()
    {
        if (!revealTiming) return;
        timeEndPeriod(1);
        revealTiming = false;
    }

    private Rectangle Offscreen(Rectangle home)
    {
        var screen = Screen.FromRectangle(home).WorkingArea;
        var cx = home.X + home.Width / 2.0;
        var cy = home.Y + home.Height / 2.0;
        var distLeft = cx - screen.Left;
        var distRight = screen.Right - cx;
        var distTop = cy - screen.Top;
        var distBottom = screen.Bottom - cy;
        var min = Math.Min(Math.Min(distLeft, distRight), Math.Min(distTop, distBottom));
        var gap = Math.Max(8, ScaleDelta(12));
        var x = home.X;
        var y = home.Y;
        if (min == distLeft) x = screen.Left - home.Width - gap;
        else if (min == distRight) x = screen.Right + gap;
        else if (min == distTop) y = screen.Top - home.Height - gap;
        else y = screen.Bottom + gap;
        return new Rectangle(x, y, home.Width, home.Height);
    }

    private void FadePage(double target, bool easeIn)
    {
        var core = view.CoreWebView2;
        if (core == null) return;
        var curve = easeIn ? "cubic-bezier(0.32,0,0.67,0)" : "cubic-bezier(0.33,1,0.68,1)";
        var opacity = target.ToString("0.###", CultureInfo.InvariantCulture);
        core.ExecuteScriptAsync(
            "(()=>{const e=document.documentElement;const from=getComputedStyle(e).opacity;" +
            "e.style.transition='none';e.style.opacity=from;void e.offsetWidth;" +
            "e.style.transition='opacity " + RevealMs + "ms " + curve + "';e.style.opacity='" + opacity + "';})()");
    }

    private void SettlePage()
    {
        var core = view.CoreWebView2;
        if (core == null) return;
        core.ExecuteScriptAsync("document.documentElement.style.transition='none';document.documentElement.style.opacity='1';");
    }

    private static bool AnimationsEnabled()
    {
        var enabled = 1;
        return !SystemParametersInfo(0x1042, 0, ref enabled, 0) || enabled != 0;
    }

    private bool WidgetOnScreen()
    {
        return IsHandleCreated && IsWindowVisible(Handle);
    }

    private static Icon? appIcon;

    private static Icon AppIcon()
    {
        if (appIcon != null) return appIcon;
        foreach (var path in IconCandidates())
        {
            try
            {
                if (!File.Exists(path)) continue;
                appIcon = new Icon(path);
                return appIcon;
            }
            catch
            {
                /* try next */
            }
        }
        try
        {
            appIcon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
        }
        catch
        {
            appIcon = null;
        }
        appIcon ??= SystemIcons.Application;
        return appIcon;
    }

    private static IEnumerable<string> IconCandidates()
    {
        var baseDir = AppContext.BaseDirectory;
        yield return Path.Combine(baseDir, "securely.ico");
        yield return Path.GetFullPath(Path.Combine(baseDir, "..", "..", "..", "securely.ico"));
        yield return Path.GetFullPath(Path.Combine(baseDir, "..", "..", "..", "..", "ui", "public", "favicon.ico"));
    }

    private void EnsureTray()
    {
        if (tray != null) return;
        tray = new NotifyIcon
        {
            Icon = (Icon)AppIcon().Clone(),
            Text = "Securely — threat monitor",
            Visible = false,
        };
        tray.MouseClick += (_, _) => BeginInvoke(ShowWidget);
    }

    private bool SetUndetectable(bool enabled)
    {
        excludeCapture = enabled;
        var applied = ApplyCaptureAffinity();
        if (enabled && !applied) excludeCapture = false;
        return !enabled || applied;
    }

    private bool ApplyCaptureAffinity()
    {
        var affinity = excludeCapture ? WDA_EXCLUDEFROMCAPTURE : WDA_NONE;
        var applied = PaintAffinity(Handle, affinity);
        if (dashboard != null && !dashboard.IsDisposed && dashboard.IsHandleCreated)
            PaintAffinity(dashboard.Handle, affinity);
        return applied;
    }

    private static bool PaintAffinity(IntPtr handle, uint affinity)
    {
        if (handle == IntPtr.Zero) return false;
        var applied = SetWindowDisplayAffinity(handle, affinity);
        EnumChildWindows(handle, (child, _) =>
        {
            SetWindowDisplayAffinity(child, affinity);
            return true;
        }, IntPtr.Zero);
        return applied;
    }

    private void ResetPosition()
    {
        follow.Stop();
        userMoved = false;
        var target = TargetBounds(lastCssWidth, lastCssHeight);
        if (revealAnimating)
        {
            revealHome = target;
            revealTo = revealHiding ? Offscreen(target) : target;
            Emit(new { ok = true });
            return;
        }
        if (!widgetShown)
        {
            revealHome = target;
            Bounds = target;
            if (IsHandleCreated) ShowWindow(Handle, SW_HIDE);
            Emit(new { ok = true });
            return;
        }
        Fit(lastCssWidth, lastCssHeight);
    }

    private void StartFollow()
    {
        if (!GetCursorPos(out var cursor)) return;
        followGrab = new Point(cursor.X - Left, cursor.Y - Top);
        followArmed = false;
        userMoved = true;
        follow.Start();
    }

    private void StopFollow()
    {
        follow.Stop();
        followArmed = false;
    }

    private void StepFollow()
    {
        var down = (GetAsyncKeyState(0x01) & 0x8000) != 0;
        if (!followArmed)
        {
            if (!down) followArmed = true;
            MoveToCursor();
            return;
        }
        if (down)
        {
            follow.Stop();
            return;
        }
        MoveToCursor();
    }

    private void MoveToCursor()
    {
        if (revealAnimating || !GetCursorPos(out var cursor)) return;
        var area = Screen.FromPoint(new Point(cursor.X, cursor.Y)).WorkingArea;
        var x = ClampStart(cursor.X - followGrab.X, area.Left, area.Right, Width);
        var y = ClampStart(cursor.Y - followGrab.Y, area.Top, area.Bottom, Height);
        var shiftX = x - Left;
        var shiftY = y - Top;
        if (shiftX == 0 && shiftY == 0) return;
        if (animating)
        {
            animFrom.X += shiftX;
            animFrom.Y += shiftY;
            animTo.X += shiftX;
            animTo.Y += shiftY;
        }
        Location = new Point(x, y);
        SetWindowPos(Handle, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
    }

    private async Task OpenPage(string url)
    {
        var folder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Securely", "webview");
        Directory.CreateDirectory(folder);
        var environment = await CoreWebView2Environment.CreateAsync(null, folder, new CoreWebView2EnvironmentOptions("--autoplay-policy=no-user-gesture-required"));
        await view.EnsureCoreWebView2Async(environment);
        view.DefaultBackgroundColor = Color.Transparent;
        view.CoreWebView2.PermissionRequested += (_, args) =>
        {
            if (args.PermissionKind != CoreWebView2PermissionKind.Microphone) return;
            args.State = CoreWebView2PermissionState.Allow;
            args.Handled = true;
        };
        var settings = view.CoreWebView2.Settings;
        settings.AreDefaultContextMenusEnabled = false;
        settings.AreDevToolsEnabled = true;
        settings.IsStatusBarEnabled = false;
        settings.IsZoomControlEnabled = false;
        settings.IsPinchZoomEnabled = false;
        view.ZoomFactor = 1;
        if (view.CoreWebView2 != null)
        {
            MapUiFolder(view.CoreWebView2);
            KeepWidgetLinksHere(view.CoreWebView2);
            view.CoreWebView2.WebMessageReceived += (_, args) => HandleUiMessage(args.TryGetWebMessageAsString());
        }
        view.Source = new Uri(url);
        if (excludeCapture) ApplyCaptureAffinity();
    }

    private static string? ResolveUiPublic()
    {
        var baseDir = AppContext.BaseDirectory;
        string[] candidates =
        [
            Path.GetFullPath(Path.Combine(baseDir, "..", "..", "..", "..", "ui", "public")),
            Path.GetFullPath(Path.Combine(baseDir, "..", "..", "..", "ui", "public")),
            Path.GetFullPath(Path.Combine(baseDir, "ui", "public")),
            Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), "ui", "public")),
            Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), "..", "ui", "public")),
        ];
        foreach (var path in candidates)
        {
            if (File.Exists(Path.Combine(path, "index.html"))) return path;
        }
        return null;
    }

    private static void MapUiFolder(CoreWebView2 core)
    {
        var ui = ResolveUiPublic();
        if (ui == null) return;
        core.SetVirtualHostNameToFolderMapping(
            "securely.local",
            ui,
            CoreWebView2HostResourceAccessKind.Allow);
    }

    private void HandleUiMessage(string? raw)
    {
        if (string.IsNullOrWhiteSpace(raw)) return;
        try
        {
            using var doc = JsonDocument.Parse(raw);
            var root = doc.RootElement;
            var cmd = root.TryGetProperty("cmd", out var cmdEl) ? cmdEl.GetString() : null;
            // Copy values before JsonDocument disposes — BeginInvoke runs later.
            switch (cmd)
            {
                case "fit":
                {
                    var width = ReadInt(root, "cssWidth");
                    var height = ReadInt(root, "cssHeight");
                    var instant = root.TryGetProperty("instant", out var instantEl) && instantEl.ValueKind == JsonValueKind.True;
                    BeginInvoke(() => Fit(width, height, instant));
                    break;
                }
                case "move":
                {
                    // Screen/CSS deltas from the pill — always move the widget, never the dashboard.
                    var dx = ScaleDelta(ReadInt(root, "dx"));
                    var dy = ScaleDelta(ReadInt(root, "dy"));
                    BeginInvoke(() => Nudge(dx, dy));
                    break;
                }
                case "visible":
                {
                    var shown = root.TryGetProperty("shown", out var shownEl) && shownEl.ValueKind == JsonValueKind.True;
                    BeginInvoke(() => { if (shown) ShowWidget(); else HideWidget(); });
                    break;
                }
                case "follow":
                {
                    var followOn = !root.TryGetProperty("active", out var followEl) || followEl.ValueKind != JsonValueKind.False;
                    BeginInvoke(() =>
                    {
                        if (followOn) StartFollow();
                        else StopFollow();
                    });
                    break;
                }
                case "home":
                    BeginInvoke(ResetPosition);
                    break;
                case "dashboard":
                {
                    var openDash = !root.TryGetProperty("open", out var openEl) || openEl.ValueKind != JsonValueKind.False;
                    var tab = root.TryGetProperty("tab", out var tabEl) ? tabEl.GetString() ?? "dashboard" : "dashboard";
                    BeginInvoke(() =>
                    {
                        if (!openDash) HideDashboard();
                        else
                        {
                            pendingDashboardTab = tab;
                            ShowDashboard();
                        }
                    });
                    break;
                }
                case "quit":
                    BeginInvoke(() =>
                    {
                        shellClosing = true;
                        if (dashboard != null && !dashboard.IsDisposed) dashboard.Close();
                        Application.Exit();
                    });
                    break;
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine("HandleUiMessage: " + ex.Message);
        }
    }

    private static bool IsCursorSite(string? uri)
    {
        if (string.IsNullOrWhiteSpace(uri)) return false;
        if (!Uri.TryCreate(uri, UriKind.Absolute, out var parsed)) return false;
        if (parsed.Scheme != Uri.UriSchemeHttps) return false;
        return parsed.Host.Equals("cursor.com", StringComparison.OrdinalIgnoreCase)
            || parsed.Host.Equals("www.cursor.com", StringComparison.OrdinalIgnoreCase);
    }

    private static void OpenCursorSite(string uri)
    {
        System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(uri) { UseShellExecute = true });
    }

    private void OpenExternal(string uri)
    {
        if (IsDashboardUrl(uri)) return;
        if (!Uri.TryCreate(uri, UriKind.Absolute, out var parsed)) return;
        if (parsed.Scheme != Uri.UriSchemeHttps && parsed.Scheme != Uri.UriSchemeHttp && parsed.Scheme != Uri.UriSchemeMailto) return;
        System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(uri) { UseShellExecute = true });
    }

    private void KeepDashboardHere(CoreWebView2 core)
    {
        core.NewWindowRequested += (_, args) =>
        {
            args.Handled = true;
            if (IsDashboardUrl(args.Uri)) return;
            OpenExternal(args.Uri);
        };
        core.NavigationStarting += (_, args) =>
        {
            if (StayInDashboard(args.Uri)) return;
            args.Cancel = true;
            if (IsDashboardUrl(args.Uri)) return;
            OpenExternal(args.Uri);
        };
    }

    private void KeepWidgetLinksHere(CoreWebView2 core)
    {
        core.NewWindowRequested += (_, args) =>
        {
            if (IsDashboardUrl(args.Uri))
            {
                args.Handled = true;
                BeginInvoke(ShowDashboard);
                return;
            }
            if (!IsCursorSite(args.Uri)) return;
            args.Handled = true;
            OpenCursorSite(args.Uri);
        };
        core.NavigationStarting += (_, args) =>
        {
            if (IsDashboardUrl(args.Uri))
            {
                args.Cancel = true;
                BeginInvoke(ShowDashboard);
                return;
            }
            if (!IsCursorSite(args.Uri)) return;
            args.Cancel = true;
            OpenCursorSite(args.Uri);
        };
    }

    private static bool StayInDashboard(string uri)
    {
        if (string.IsNullOrWhiteSpace(uri)) return true;
        if (!Uri.TryCreate(uri, UriKind.Absolute, out var parsed)) return true;
        if (parsed.Scheme.Equals("about", StringComparison.OrdinalIgnoreCase)) return true;
        if (parsed.Host.Equals("securely.local", StringComparison.OrdinalIgnoreCase)) return true;
        return IsLoopback(parsed.Host) && DashboardPath(parsed);
    }

    private static bool IsDashboardUrl(string? uri)
    {
        if (string.IsNullOrWhiteSpace(uri)) return false;
        if (!Uri.TryCreate(uri, UriKind.Absolute, out var parsed)) return false;
        if (!DashboardPath(parsed)) return false;
        if (IsLoopback(parsed.Host)) return true;
        return parsed.Host.Equals("Securely.com", StringComparison.OrdinalIgnoreCase)
            || parsed.Host.Equals("www.Securely.com", StringComparison.OrdinalIgnoreCase);
    }

    private static bool DashboardPath(Uri uri)
    {
        var path = uri.AbsolutePath.TrimEnd('/');
        return path.Equals("/dashboard", StringComparison.OrdinalIgnoreCase)
            || path.Equals("/dashboard.html", StringComparison.OrdinalIgnoreCase);
    }

    private static bool IsLoopback(string host)
    {
        return host.Equals("127.0.0.1", StringComparison.OrdinalIgnoreCase)
            || host.Equals("localhost", StringComparison.OrdinalIgnoreCase)
            || host.Equals("[::1]", StringComparison.OrdinalIgnoreCase);
    }

    private static void MarkDesktop(CoreWebView2 core)
    {
        var agent = core.Settings.UserAgent ?? "";
        if (agent.Contains("SecurelyDesktop", StringComparison.Ordinal)) return;
        core.Settings.UserAgent = string.IsNullOrWhiteSpace(agent) ? "SecurelyDesktop" : agent + " SecurelyDesktop";
    }

    private void WarmDashboard()
    {
        EnsureDashboardWindow();
        _ = LoadDashboardPage();
    }

    private Form EnsureDashboardWindow()
    {
        if (dashboard != null && !dashboard.IsDisposed) return dashboard;
        var window = new Form
        {
            Text = "Securely",
            Icon = (Icon)AppIcon().Clone(),
            StartPosition = FormStartPosition.CenterScreen,
            ClientSize = new Size(1120, 760),
            BackColor = Color.FromArgb(0xEC, 0xEE, 0xF2),
            ShowInTaskbar = true,
            TopMost = false,
        };
        var page = new WebView2 { Dock = DockStyle.Fill };
        page.DefaultBackgroundColor = Color.FromArgb(0xEC, 0xEE, 0xF2);
        window.Controls.Add(page);
        dashboardView = page;
        dashboard = window;
        window.FormClosing += (_, args) =>
        {
            if (shellClosing) return;
            args.Cancel = true;
            HideDashboard();
        };
        window.FormClosed += (_, _) =>
        {
            if (!ReferenceEquals(dashboard, window)) return;
            dashboard = null;
            dashboardView = null;
            dashboardLoading = false;
            NotifyDashboard(false);
        };
        window.DpiChanged += (_, _) => PlaceDashboard(window);
        _ = window.Handle;
        PlaceDashboard(window);
        if (excludeCapture) ApplyCaptureAffinity();
        return window;
    }

    private bool DashboardIsOpen()
    {
        return dashboard != null && !dashboard.IsDisposed && dashboard.Visible && dashboard.WindowState != FormWindowState.Minimized;
    }

    private void ToggleDashboard()
    {
        if (DashboardIsOpen()) HideDashboard();
        else ShowDashboard();
    }

    private void ShowDashboard()
    {
        var window = EnsureDashboardWindow();
        if (window.WindowState == FormWindowState.Minimized) window.WindowState = FormWindowState.Normal;
        window.TopMost = true;
        PlaceDashboard(window);
        window.Show();
        if (window.IsHandleCreated)
        {
            // The shell is started with a hidden startup show command, and Windows
            // ignores the first ShowWindow. A second show is what actually appears.
            ShowWindow(window.Handle, SW_SHOWNORMAL);
            ShowWindow(window.Handle, SW_SHOWNORMAL);
            SetWindowPos(window.Handle, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW);
        }
        window.BringToFront();
        window.Activate();
        if (excludeCapture) ApplyCaptureAffinity();
        window.BeginInvoke(() => { _ = LoadDashboardPage(); });
        NotifyDashboard(true);
    }

    private void HideDashboard()
    {
        if (dashboard == null || dashboard.IsDisposed) return;
        dashboard.TopMost = false;
        dashboard.Hide();
        NotifyDashboard(false);
        PinTopmost();
    }

    private void NotifyDashboard(bool open)
    {
        var core = view.CoreWebView2;
        if (core == null) return;
        var flag = open ? "true" : "false";
        _ = core.ExecuteScriptAsync($"window.onDashboardOpen&&window.onDashboardOpen({flag})");
    }

    private async Task LoadDashboardPage()
    {
        var window = dashboard;
        var page = dashboardView;
        if (window == null || page == null || window.IsDisposed || dashboardLoading) return;
        if (page.CoreWebView2 == null && (!window.Visible || window.WindowState == FormWindowState.Minimized)) return;
        dashboardLoading = true;
        try
        {
            if (page.CoreWebView2 == null)
            {
                var folder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Securely", "webview-dashboard");
                Directory.CreateDirectory(folder);
                var environment = await CoreWebView2Environment.CreateAsync(null, folder);
                if (window.IsDisposed || page.IsDisposed) return;
                await page.EnsureCoreWebView2Async(environment);
                if (window.IsDisposed || page.CoreWebView2 == null) return;
                var settings = page.CoreWebView2.Settings;
                settings.AreDefaultContextMenusEnabled = false;
                settings.AreDevToolsEnabled = false;
                settings.IsStatusBarEnabled = false;
                settings.IsZoomControlEnabled = false;
                settings.IsPinchZoomEnabled = false;
                page.ZoomFactor = 1;
                MarkDesktop(page.CoreWebView2);
                MapUiFolder(page.CoreWebView2);
                KeepDashboardHere(page.CoreWebView2);
                page.CoreWebView2.WebMessageReceived += (_, args) => HandleUiMessage(args.TryGetWebMessageAsString());
            }
            if (page.CoreWebView2 == null) return;
            MarkDesktop(page.CoreWebView2);
            var tab = string.IsNullOrWhiteSpace(pendingDashboardTab) ? "dashboard" : pendingDashboardTab;
            var target = "https://securely.local/dashboard.html?tab=" + Uri.EscapeDataString(tab);
            var source = page.CoreWebView2.Source ?? "";
            if (!source.StartsWith("https://securely.local/dashboard.html", StringComparison.OrdinalIgnoreCase))
                page.CoreWebView2.Navigate(target);
            else
            {
                var section = tab switch
                {
                    "settings" => "settings",
                    "audit" => "audit",
                    "releases" => "releases",
                    "credits" => "credits",
                    _ => "monitor",
                };
                _ = page.CoreWebView2.ExecuteScriptAsync(
                    $"window.openSecurelySection&&window.openSecurelySection('{section}');history.replaceState(null,'','?tab={Uri.EscapeDataString(tab)}');");
            }
            if (excludeCapture) ApplyCaptureAffinity();
        }
        catch
        {
            /* The next open tries again. */
        }
        finally
        {
            dashboardLoading = false;
        }
    }

    private void ReadCommands()
    {
        string? line;
        while ((line = Console.ReadLine()) is not null)
        {
            if (string.IsNullOrWhiteSpace(line)) continue;
            try
            {
                using var doc = JsonDocument.Parse(line);
                var root = doc.RootElement;
                var cmd = root.GetProperty("cmd").GetString();
                switch (cmd)
                {
                    case "fit":
                        var width = ReadInt(root, "cssWidth");
                        var height = ReadInt(root, "cssHeight");
                        var instant = root.TryGetProperty("instant", out var instantEl) && instantEl.ValueKind == JsonValueKind.True;
                        BeginInvoke(() => Fit(width, height, instant));
                        break;
                    case "move":
                        var dx = ReadInt(root, "dx");
                        var dy = ReadInt(root, "dy");
                        BeginInvoke(() => Nudge(ScaleDelta(dx), ScaleDelta(dy)));
                        break;
                    case "browse":
                        var initial = root.TryGetProperty("initialPath", out var pathEl) ? pathEl.GetString() ?? "" : "";
                        string picked = "";
                        Invoke(() => picked = Browse(initial));
                        Emit(new { ok = true, path = picked });
                        break;
                    case "capture":
                        string captured = "";
                        Invoke(() => captured = CaptureScreen());
                        Emit(new { ok = true, image = captured, mimeType = "image/jpeg" });
                        break;
                    case "devices":
                        try
                        {
                            var listed = audioIo.List();
                            Emit(new
                            {
                                ok = true,
                                inputs = listed.Inputs.Select(item => new { id = item.Id, name = item.Name }).ToArray(),
                                outputs = listed.Outputs.Select(item => new { id = item.Id, name = item.Name }).ToArray(),
                            });
                        }
                        catch (Exception ex)
                        {
                            Emit(new { ok = false, error = ex.Message, inputs = Array.Empty<object>(), outputs = Array.Empty<object>() });
                        }
                        break;
                    case "audio":
                        var inputId = root.TryGetProperty("input", out var inputEl) ? inputEl.GetString() ?? "" : "";
                        var outputId = root.TryGetProperty("output", out var outputEl) ? outputEl.GetString() ?? "" : "";
                        var inputChanged = audioIo.SetDevices(inputId, outputId);
                        if (inputChanged && voiceEngine != null)
                        {
                            var restartWake = voicePhase == "wake";
                            if (restartWake) StartWake();
                            else StartVoice();
                        }
                        Emit(new { ok = true });
                        break;
                    case "play":
                        var soundPath = root.TryGetProperty("path", out var soundEl) ? soundEl.GetString() ?? "" : "";
                        try
                        {
                            audioIo.Play(soundPath);
                            Emit(new { ok = true });
                        }
                        catch (Exception ex)
                        {
                            Emit(new { ok = false, error = ex.Message });
                        }
                        break;
                    case "voice":
                        var action = root.TryGetProperty("action", out var actionEl) ? actionEl.GetString() ?? "" : "";
                        try
                        {
                            if (action == "start") StartVoice();
                            else if (action == "wake") StartWake();
                            else if (action == "stop") StopVoice();
                            else if (action != "poll") throw new InvalidOperationException("Unknown voice action.");
                            var state = VoiceState();
                            Emit(new { ok = true, listening = state.Listening, text = state.Text, error = state.Error, phase = state.Phase, silenceMs = state.SilenceMs, awake = state.Awake });
                        }
                        catch (Exception ex)
                        {
                            Emit(new { ok = false, listening = false, text = "", error = ex.Message, phase = "off", silenceMs = 0, awake = false });
                        }
                        break;
                    case "focus":
                        Emit(new { ok = true, active = GetForegroundWindow() == Handle });
                        break;
                    case "yield":
                        Invoke(YieldFocus);
                        Emit(new { ok = true, active = GetForegroundWindow() == Handle });
                        break;
                    case "visible":
                        var shown = root.TryGetProperty("shown", out var shownEl) && shownEl.ValueKind == JsonValueKind.True;
                        Invoke(() => { if (shown) ShowWidget(); else HideWidget(); });
                        Emit(new { ok = true, shown = widgetShown });
                        break;
                    case "follow":
                    {
                        var followOn = !root.TryGetProperty("active", out var followActiveEl) || followActiveEl.ValueKind != JsonValueKind.False;
                        BeginInvoke(() =>
                        {
                            if (followOn) StartFollow();
                            else StopFollow();
                        });
                        Emit(new { ok = true });
                        break;
                    }
                    case "home":
                        BeginInvoke(ResetPosition);
                        break;
                    case "arrows":
                        var arrowsOn = root.TryGetProperty("enabled", out var arrowsEl) && arrowsEl.ValueKind == JsonValueKind.True;
                        Invoke(() => SetMoveKeys(arrowsOn));
                        Emit(new { ok = true, enabled = moveKeys });
                        break;
                    case "undetectable":
                        var enabled = root.TryGetProperty("enabled", out var enabledEl) && enabledEl.ValueKind == JsonValueKind.True;
                        var applied = false;
                        Invoke(() => applied = SetUndetectable(enabled));
                        if (!applied && enabled) excludeCapture = false;
                        Emit(new { ok = applied || !enabled, enabled = excludeCapture, error = applied || !enabled ? "" : "This Windows session could not hide Securely from capture." });
                        break;
                    case "dashboard":
                        var dashOpen = false;
                        Invoke(() =>
                        {
                            ToggleDashboard();
                            dashOpen = DashboardIsOpen();
                        });
                        Emit(new { ok = true, open = dashOpen });
                        break;
                    case "quit":
                        Emit(new { ok = true });
                        BeginInvoke(() =>
                        {
                            shellClosing = true;
                            if (dashboard != null && !dashboard.IsDisposed) dashboard.Close();
                            Application.Exit();
                        });
                        return;
                    default:
                        Emit(new { ok = false, error = "unknown" });
                        break;
                }
            }
            catch (Exception ex)
            {
                Emit(new { ok = false, error = ex.Message });
            }
        }
    }

    private void PlaceAtTopCenter()
    {
        var bounds = TargetBounds(lastCssWidth, lastCssHeight);
        if (IsHandleCreated) ApplyBounds(bounds);
        else
        {
            ClientSize = new Size(bounds.Width, bounds.Height);
            Location = new Point(bounds.X, bounds.Y);
        }
    }

    private void Fit(int width, int height, bool instant = false)
    {
        var target = TargetBounds(width, height);
        if (revealAnimating)
        {
            revealHome = target;
            revealTo = revealHiding ? Offscreen(target) : target;
            Emit(new { ok = true });
            return;
        }
        var same = target.X == Left && target.Y == Top && target.Width == Width && target.Height == Height;
        if (same)
        {
            if (animating)
            {
                anim.Stop();
                animating = false;
            }
            Emit(new { ok = true });
            return;
        }
        var tiny = Math.Abs(target.Height - Height) < 6
            && Math.Abs(target.Width - Width) < 2
            && Math.Abs(target.Y - Top) < 6;
        if (instant || tiny)
        {
            if (animating)
            {
                anim.Stop();
                animating = false;
            }
            ApplyBounds(target);
            Emit(new { ok = true });
            return;
        }
        animFrom = new Rectangle(Left, Top, Width, Height);
        animTo = target;
        animStart = Environment.TickCount64;
        if (!animating)
        {
            animating = true;
            anim.Start();
        }
        Emit(new { ok = true });
    }

    private void StepAnim()
    {
        const int duration = 280;
        var t = Math.Clamp((Environment.TickCount64 - animStart) / (double)duration, 0, 1);
        var eased = 1 - Math.Pow(1 - t, 4);
        if (t >= 1)
        {
            anim.Stop();
            animating = false;
            ApplyBounds(animTo);
            return;
        }
        ApplyBounds(new Rectangle(
            Lerp(animFrom.X, animTo.X, eased),
            Lerp(animFrom.Y, animTo.Y, eased),
            Lerp(animFrom.Width, animTo.Width, eased),
            Lerp(animFrom.Height, animTo.Height, eased)));
    }

    private Rectangle TargetBounds(int cssWidth, int cssHeight)
    {
        lastCssWidth = Math.Clamp(cssWidth, 160, 2000);
        lastCssHeight = Math.Clamp(cssHeight, 48, 4000);
        var area = CurrentWorkArea();
        var margin = ScaleDelta(12);
        var topInset = ScaleDelta(20);
        var width = Math.Min(ScaleCss(lastCssWidth), Math.Max(ScaleDelta(200), area.Width - margin * 2));
        var height = Math.Min(ScaleCss(lastCssHeight), Math.Max(ScaleDelta(48), area.Height - margin * 2));
        var anchorX = revealAnimating ? revealHome.X : Left;
        var anchorY = revealAnimating ? revealHome.Y : Top;
        var anchorW = revealAnimating ? revealHome.Width : Width;
        var top = userMoved ? anchorY : area.Top + topInset;
        var center = anchorX + anchorW / 2.0;
        var left = userMoved
            ? (int)Math.Round(center - width / 2.0)
            : area.Left + Math.Max(0, (area.Width - width) / 2);
        left = ClampStart(left, area.Left, area.Right, width);
        top = ClampStart(top, area.Top, area.Bottom, height);
        return new Rectangle(left, top, width, height);
    }

    private Rectangle CurrentWorkArea()
    {
        Screen? screen = null;
        if (IsHandleCreated) screen = Screen.FromHandle(Handle);
        screen ??= Screen.PrimaryScreen;
        return screen?.WorkingArea ?? new Rectangle(0, 0, 1280, 800);
    }

    private double DpiScale => (DeviceDpi > 0 ? DeviceDpi : 96) / 96.0;

    private int ScaleCss(int css)
    {
        return Math.Max(1, (int)Math.Ceiling(css * DpiScale - 1e-6));
    }

    private int ScaleDelta(int css)
    {
        return (int)Math.Round(css * DpiScale, MidpointRounding.AwayFromZero);
    }

    private static int ClampStart(int value, int areaStart, int areaEnd, int size)
    {
        var max = areaEnd - size;
        if (max <= areaStart) return areaStart;
        return Math.Clamp(value, areaStart, max);
    }

    private void PlaceDashboard(Form window)
    {
        if (window.IsDisposed || !window.IsHandleCreated) return;
        var area = Screen.FromHandle(window.Handle).WorkingArea;
        var dpi = (window.DeviceDpi > 0 ? window.DeviceDpi : 96) / 96.0;
        int Scale(int css) => Math.Max(1, (int)Math.Ceiling(css * dpi - 1e-6));
        var chromeW = Math.Max(0, window.Width - window.ClientSize.Width);
        var chromeH = Math.Max(0, window.Height - window.ClientSize.Height);
        var margin = Scale(16);
        var width = Math.Min(Scale(1120), Math.Max(Scale(320), area.Width - margin * 2 - chromeW));
        var height = Math.Min(Scale(760), Math.Max(Scale(240), area.Height - margin * 2 - chromeH));
        window.MaximumSize = new Size(Math.Max(1, area.Width), Math.Max(1, area.Height));
        window.MinimumSize = new Size(
            Math.Max(1, Math.Min(area.Width, Math.Min(width, Scale(480)) + chromeW)),
            Math.Max(1, Math.Min(area.Height, Math.Min(height, Scale(320)) + chromeH)));
        window.ClientSize = new Size(width, height);
        window.Location = new Point(
            ClampStart(area.Left + Math.Max(0, (area.Width - window.Width) / 2), area.Left, area.Right, window.Width),
            ClampStart(area.Top + Math.Max(0, (area.Height - window.Height) / 2), area.Top, area.Bottom, window.Height));
    }

    private void ApplyBounds(Rectangle bounds)
    {
        if (bounds.X == Left && bounds.Y == Top && bounds.Width == Width && bounds.Height == Height) return;
        Bounds = bounds;
        if (IsHandleCreated) SetWindowPos(Handle, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
        ApplyWindowShape();
    }

    protected override void OnResize(EventArgs e)
    {
        base.OnResize(e);
        ApplyWindowShape();
    }

    private void ClearBackdrop()
    {
        if (!IsHandleCreated) return;
        var backdrop = 1;
        DwmSetWindowAttribute(Handle, 38, ref backdrop, sizeof(int));
        var border = unchecked((int)0xFFFFFFFE);
        DwmSetWindowAttribute(Handle, 34, ref border, sizeof(int));
        var accent = new AccentPolicy();
        var size = System.Runtime.InteropServices.Marshal.SizeOf<AccentPolicy>();
        var pointer = System.Runtime.InteropServices.Marshal.AllocHGlobal(size);
        try
        {
            System.Runtime.InteropServices.Marshal.StructureToPtr(accent, pointer, false);
            var data = new WindowCompositionAttributeData
            {
                Attribute = 19,
                Data = pointer,
                SizeOfData = size,
            };
            SetWindowCompositionAttribute(Handle, ref data);
        }
        finally
        {
            System.Runtime.InteropServices.Marshal.FreeHGlobal(pointer);
        }
    }

    private void ApplyWindowShape()
    {
        if (!IsHandleCreated) return;
        var width = Math.Max(1, ClientSize.Width);
        var height = Math.Max(1, ClientSize.Height);
        var diameter = Math.Max(2, WindowRadius(width, height) * 2);
        diameter = Math.Min(diameter, Math.Min(width, height) - 1);
        if (width == shapeWidth && height == shapeHeight && diameter == shapeDiameter && Region != null) return;
        using var path = new GraphicsPath();
        path.AddArc(0, 0, diameter, diameter, 180, 90);
        path.AddArc(width - diameter - 1, 0, diameter, diameter, 270, 90);
        path.AddArc(width - diameter - 1, height - diameter - 1, diameter, diameter, 0, 90);
        path.AddArc(0, height - diameter - 1, diameter, diameter, 90, 90);
        path.CloseFigure();
        var next = new Region(path);
        var old = Region;
        shapeWidth = width;
        shapeHeight = height;
        shapeDiameter = diameter;
        Region = next;
        old?.Dispose();
    }

    private int WindowRadius(int width, int height)
    {
        var dpi = (DeviceDpi > 0 ? DeviceDpi : 96) / 96f;
        var shortSide = Math.Min(width, height);
        var shortPill = height <= (int)Math.Round(64 * dpi);
        // Compact pill: fully rounded ends. Taller layouts keep a fixed corner so
        // a resize never stretches the radius into a giant capsule.
        var wanted = shortPill ? shortSide / 2 : (int)Math.Round(22 * dpi);
        var maxCorner = shortPill ? shortSide / 2 : (int)Math.Round(26 * dpi);
        return Math.Max(8, Math.Min(wanted, Math.Min(shortSide / 2, maxCorner)));
    }

    private void Nudge(int dx, int dy)
    {
        Shift(dx, dy);
        Emit(new { ok = true });
    }

    private void Shift(int dx, int dy)
    {
        if (revealAnimating) return;
        userMoved = true;
        follow.Stop();
        var proposedX = Left + dx;
        var proposedY = Top + dy;
        var area = Screen.FromPoint(new Point(proposedX + Width / 2, proposedY + Height / 2)).WorkingArea;
        var x = ClampStart(proposedX, area.Left, area.Right, Width);
        var y = ClampStart(proposedY, area.Top, area.Bottom, Height);
        var shiftX = x - Left;
        var shiftY = y - Top;
        if (shiftX == 0 && shiftY == 0) return;
        if (animating)
        {
            animFrom.X += shiftX;
            animFrom.Y += shiftY;
            animTo.X += shiftX;
            animTo.Y += shiftY;
        }
        Location = new Point(x, y);
        SetWindowPos(Handle, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
    }

    private bool moveKeys;

    private void SetMoveKeys(bool enabled)
    {
        if (moveKeys == enabled) return;
        if (enabled)
        {
            RegisterHotKey(Handle, 6, MOD_CONTROL, 0x26);
            RegisterHotKey(Handle, 7, MOD_CONTROL, 0x28);
            RegisterHotKey(Handle, 8, MOD_CONTROL, 0x25);
            RegisterHotKey(Handle, 9, MOD_CONTROL, 0x27);
        }
        else
        {
            for (var id = 6; id <= 9; id++) UnregisterHotKey(Handle, id);
        }
        moveKeys = enabled;
    }

    private void DispatchHotkey(int id)
    {
        if (id == 1 || id == 2)
        {
            ToggleVisibility();
            return;
        }
        if (id == 3)
        {
            if (!widgetShown) ShowWidget();
            NotifyHotkey("ask");
            return;
        }
        if (id == 4)
        {
            NotifyHotkey("clear");
            return;
        }
        if (id == 5)
        {
            if (!widgetShown) ShowWidget();
            NotifyHotkey("session");
            return;
        }
        var step = ScaleDelta(40);
        if (id == 6) Shift(0, -step);
        else if (id == 7) Shift(0, step);
        else if (id == 8) Shift(-step, 0);
        else if (id == 9) Shift(step, 0);
    }

    private IntPtr keyboardHook;
    private LowLevelKeyboardProc? keyboardProc;
    private bool backslashDown;
    private int backslashVk = 0xDC;

    private void InstallVisibilityHook()
    {
        var mapped = VkKeyScan('\\');
        if (mapped >= 0 && (mapped & 0x100) == 0) backslashVk = mapped & 0xFF;
        keyboardProc = VisibilityHook;
        keyboardHook = SetWindowsHookEx(WH_KEYBOARD_LL, keyboardProc, GetModuleHandle(null), 0);
        if (keyboardHook != IntPtr.Zero) UnregisterHotKey(Handle, 2);
    }

    private void ToggleVisibility()
    {
        if (IsDisposed) return;
        if (widgetShown) HideWidget();
        else ShowWidget();
    }

    private IntPtr VisibilityHook(int nCode, IntPtr wParam, IntPtr lParam)
    {
        if (nCode < 0 || keyboardHook == IntPtr.Zero) return CallNextHookEx(keyboardHook, nCode, wParam, lParam);
        var info = System.Runtime.InteropServices.Marshal.PtrToStructure<KbdLlHook>(lParam);
        var up = (info.flags & LLKHF_UP) != 0;
        if (IsBackslashKey(info.vkCode))
        {
            var ctrl = KeyHeld(0x11) || KeyHeld(0xA2) || KeyHeld(0xA3);
            var shift = KeyHeld(0x10) || KeyHeld(0xA0) || KeyHeld(0xA1);
            var alt = KeyHeld(0x12) || KeyHeld(0xA4) || KeyHeld(0xA5);
            if (up)
            {
                var eaten = backslashDown;
                backslashDown = false;
                if (eaten) return (IntPtr)1;
            }
            else if (ctrl && !shift && !alt && (info.flags & LLKHF_INJECTED) == 0)
            {
                if (!backslashDown)
                {
                    backslashDown = true;
                    BeginInvoke(ToggleVisibility);
                }
                return (IntPtr)1;
            }
        }
        return CallNextHookEx(keyboardHook, nCode, wParam, lParam);
    }

    private bool IsBackslashKey(uint vk)
    {
        return vk == 0xDC || vk == 0xE2 || (backslashVk > 0 && vk == (uint)backslashVk);
    }

    private static bool KeyHeld(int vk)
    {
        return (GetAsyncKeyState(vk) & 0x8000) != 0;
    }

    private void NotifyHotkey(string name)
    {
        var core = view.CoreWebView2;
        if (core == null) return;
        core.ExecuteScriptAsync($"window.onSecurelyHotkey&&window.onSecurelyHotkey({JsonSerializer.Serialize(name)})");
    }

    private string Browse(string initialPath)
    {
        using var dialog = new OpenFileDialog
        {
            Title = "Choose a file or folder",
            Filter = "All files|*.*",
            CheckFileExists = false,
            CheckPathExists = true,
            ValidateNames = false,
            DereferenceLinks = true,
            FileName = "Select this folder",
        };
        var start = initialPath.Trim();
        if (File.Exists(start)) start = Path.GetDirectoryName(start) ?? start;
        if (Directory.Exists(start)) dialog.InitialDirectory = start;
        if (dialog.ShowDialog(this) != DialogResult.OK) return "";
        var chosen = dialog.FileName;
        if (string.IsNullOrWhiteSpace(chosen)) return "";
        if (File.Exists(chosen)) return Path.GetFullPath(chosen);
        var folder = Path.GetDirectoryName(chosen);
        if (!string.IsNullOrEmpty(folder) && Directory.Exists(folder)) return Path.GetFullPath(folder);
        return "";
    }

    private static bool InsideRoundedRect(int x, int y, int width, int height, int radius)
    {
        if (x < 0 || y < 0 || x >= width || y >= height) return false;
        var r = Math.Min(radius + 1, Math.Min(width, height) / 2);
        var midX = x >= r && x < width - r;
        var midY = y >= r && y < height - r;
        if (midX || midY) return true;
        var cx = x < r ? r : width - r;
        var cy = y < r ? r : height - r;
        var dx = x - cx;
        var dy = y - cy;
        return dx * dx + dy * dy <= r * r;
    }

    private SpeechRecognitionEngine? voiceEngine;
    private SpeechAudioSource? voiceSource;
    private readonly AudioIO audioIo = new();
    private readonly object voiceGate = new();
    private string voiceCommitted = "";
    private string voiceLive = "";
    private string voiceError = "";
    private string voicePhase = "off";
    private int voiceGeneration;
    private long voiceActivityTick;
    private long voiceWakeTick;
    private bool voiceAwakeEdge;

    private void StartVoice() => StartEngine(false);

    private void StartWake() => StartEngine(true);

    private void StartEngine(bool wake)
    {
        var generation = ++voiceGeneration;
        DisposeVoiceEngine();
        lock (voiceGate)
        {
            voiceCommitted = "";
            voiceLive = "";
            voiceError = "";
            voicePhase = wake ? "wake" : "prompt";
            voiceAwakeEdge = false;
            voiceActivityTick = Environment.TickCount64;
        }
        var installed = SpeechRecognitionEngine.InstalledRecognizers();
        if (installed.Count == 0)
        {
            lock (voiceGate) voicePhase = "off";
            throw new InvalidOperationException("Windows speech recognition is not installed. Add a speech language in Windows settings.");
        }
        var language = CultureInfo.CurrentUICulture.TwoLetterISOLanguageName;
        var chosen = installed.FirstOrDefault(item => item.Culture.TwoLetterISOLanguageName.Equals(language, StringComparison.OrdinalIgnoreCase)) ?? installed[0];
        var engine = new SpeechRecognitionEngine(chosen);
        try
        {
            if (wake)
            {
                var choices = new Choices("say Securely", "hey Securely", "Securely");
                engine.LoadGrammar(new Grammar(new GrammarBuilder(choices)) { Name = "Securely-wake" });
            }
            else
            {
                engine.LoadGrammar(new DictationGrammar());
            }
            SpeechAudioSource? source = null;
            try
            {
                source = audioIo.OpenCapture();
                engine.SetInputToAudioStream(source, source.Format);
            }
            catch
            {
                source?.Dispose();
                source = null;
                engine.SetInputToDefaultAudioDevice();
            }
            voiceSource = source;
            engine.BabbleTimeout = TimeSpan.Zero;
            engine.InitialSilenceTimeout = TimeSpan.FromSeconds(30);
            engine.EndSilenceTimeout = TimeSpan.FromMilliseconds(500);
            engine.EndSilenceTimeoutAmbiguous = TimeSpan.FromMilliseconds(900);
            try { engine.UpdateRecognizerSetting("CFGConfidenceRejectionThreshold", 30); } catch { /* This recognizer has no rejection setting. */ }
            engine.SpeechDetected += (_, _) =>
            {
                if (generation != voiceGeneration) return;
                lock (voiceGate) voiceActivityTick = Environment.TickCount64;
            };
            engine.SpeechHypothesized += (_, args) =>
            {
                if (generation != voiceGeneration || wake) return;
                lock (voiceGate)
                {
                    voiceLive = args.Result?.Text ?? "";
                    voiceActivityTick = Environment.TickCount64;
                }
            };
            engine.SpeechRecognized += (_, args) =>
            {
                if (generation != voiceGeneration) return;
                var said = (args.Result?.Text ?? "").Trim();
                var confidence = args.Result?.Confidence ?? 0;
                if (said.Length == 0) return;
                if (!wake && confidence < 0.3f)
                {
                    lock (voiceGate) voiceLive = "";
                    return;
                }
                if (wake)
                {
                    var accept = false;
                    lock (voiceGate)
                    {
                        var now = Environment.TickCount64;
                        if (voicePhase == "wake" && now - voiceWakeTick >= 4000)
                        {
                            voiceWakeTick = now;
                            voicePhase = "prompt";
                            voiceAwakeEdge = true;
                            voiceCommitted = "";
                            voiceLive = "";
                            accept = true;
                        }
                    }
                    if (!accept) return;
                    BeginInvoke(() =>
                    {
                        try { HoldForCue(); }
                        catch (Exception ex)
                        {
                            lock (voiceGate) voiceError = ex.Message;
                        }
                    });
                    return;
                }
                said = WithoutWake(said);
                if (said.Length == 0) return;
                lock (voiceGate)
                {
                    voiceCommitted = string.IsNullOrEmpty(voiceCommitted) ? said : voiceCommitted + " " + said;
                    voiceLive = "";
                    voiceActivityTick = Environment.TickCount64;
                }
            };
            engine.RecognizeCompleted += (_, args) =>
            {
                if (generation != voiceGeneration) return;
                if (args.Cancelled) return;
                if (args.Error != null)
                {
                    lock (voiceGate) voiceError = args.Error.Message;
                    return;
                }
                try
                {
                    if (generation == voiceGeneration && voiceEngine == engine) engine.RecognizeAsync(RecognizeMode.Multiple);
                }
                catch (Exception ex)
                {
                    lock (voiceGate) voiceError = ex.Message;
                }
            };
            engine.RecognizeAsync(RecognizeMode.Multiple);
            voiceEngine = engine;
        }
        catch
        {
            try { engine.Dispose(); } catch { /* already disposed */ }
            voiceSource?.Dispose();
            voiceSource = null;
            lock (voiceGate) voicePhase = "off";
            throw;
        }
    }

    private void HoldForCue()
    {
        lock (voiceGate)
        {
            if (voicePhase != "prompt") return;
        }
        voiceGeneration++;
        DisposeVoiceEngine();
        lock (voiceGate)
        {
            if (voicePhase != "prompt") return;
            voiceCommitted = "";
            voiceLive = "";
            voiceActivityTick = Environment.TickCount64;
        }
    }

    private static string WithoutWake(string said)
    {
        var text = said.Trim();
        var lower = text.ToLowerInvariant();
        string[] phrases = ["say Securely", "hey Securely", "Securely"];
        foreach (var phrase in phrases)
        {
            if (lower == phrase) return "";
            if (lower.StartsWith(phrase + " ", StringComparison.Ordinal)) return text[(phrase.Length + 1)..].Trim();
        }
        return text;
    }

    private void StopVoice()
    {
        voiceGeneration++;
        DisposeVoiceEngine();
        lock (voiceGate)
        {
            voiceCommitted = "";
            voiceLive = "";
            voicePhase = "off";
            voiceAwakeEdge = false;
        }
    }

    private void DisposeVoiceEngine()
    {
        var engine = voiceEngine;
        voiceEngine = null;
        if (engine == null) return;
        try { engine.RecognizeAsyncCancel(); } catch { /* already stopped */ }
        try { engine.SetInputToNull(); } catch { /* already released */ }
        try { engine.Dispose(); } catch { /* already disposed */ }
        voiceSource?.Dispose();
        voiceSource = null;
    }

    private (bool Listening, string Text, string Error, string Phase, long SilenceMs, bool Awake) VoiceState()
    {
        lock (voiceGate)
        {
            var text = voicePhase == "wake"
                ? ""
                : string.Join(" ", new[] { voiceCommitted, voiceLive }.Where(part => !string.IsNullOrWhiteSpace(part))).Trim();
            var silence = voiceEngine == null ? 0 : Math.Max(0, Environment.TickCount64 - voiceActivityTick);
            var awake = voiceAwakeEdge;
            voiceAwakeEdge = false;
            return (voiceEngine != null, text, voiceError, voicePhase, silence, awake);
        }
    }

    private string CaptureScreen()
    {
        var screen = Screen.FromControl(this);
        var bounds = screen.Bounds;
        var wasVisible = Visible;
        try
        {
            if (wasVisible)
            {
                Visible = false;
                Application.DoEvents();
                Thread.Sleep(140);
            }
            using var full = new Bitmap(bounds.Width, bounds.Height, PixelFormat.Format24bppRgb);
            using (var graphics = Graphics.FromImage(full))
            {
                graphics.CopyFromScreen(bounds.Left, bounds.Top, 0, 0, bounds.Size, CopyPixelOperation.SourceCopy);
            }
            using var fitted = FitWidth(full, 1600);
            using var stream = new MemoryStream();
            SaveJpeg(fitted, stream, 62);
            return Convert.ToBase64String(stream.ToArray());
        }
        finally
        {
            if (wasVisible)
            {
                Visible = true;
                PinTopmost();
            }
        }
    }

    private static Bitmap FitWidth(Bitmap source, int maxWidth)
    {
        if (source.Width <= maxWidth) return (Bitmap)source.Clone();
        var height = Math.Max(1, (int)Math.Round(source.Height * (maxWidth / (double)source.Width)));
        return new Bitmap(source, new Size(maxWidth, height));
    }

    private static void SaveJpeg(Bitmap bitmap, Stream stream, long quality)
    {
        var encoder = ImageCodecInfo.GetImageEncoders().First(item => item.FormatID == ImageFormat.Jpeg.Guid);
        using var parameters = new EncoderParameters(1);
        parameters.Param[0] = new EncoderParameter(Encoder.Quality, quality);
        bitmap.Save(stream, encoder, parameters);
    }

    private static int Lerp(int from, int to, double t)
    {
        return (int)Math.Round(from + (to - from) * t);
    }

    private static int ReadInt(JsonElement root, string name)
    {
        return (int)Math.Round(root.GetProperty(name).GetDouble());
    }

    private static void Emit(object body)
    {
        Console.Out.WriteLine(JsonSerializer.Serialize(body));
        Console.Out.Flush();
    }

    private static readonly IntPtr HWND_TOPMOST = new(-1);
    private static readonly IntPtr HWND_NOTOPMOST = new(-2);
    private const uint SWP_NOSIZE = 0x0001;
    private const uint SWP_NOMOVE = 0x0002;
    private const uint SWP_NOZORDER = 0x0004;
    private const uint SWP_NOACTIVATE = 0x0010;
    private const uint SWP_SHOWWINDOW = 0x0040;
    private const int SW_HIDE = 0;
    private const int SW_SHOWNORMAL = 1;
    private const int WH_KEYBOARD_LL = 13;
    private const uint LLKHF_UP = 0x80;
    private const uint LLKHF_INJECTED = 0x10;
    private const uint SWP_NOCOPYBITS = 0x0100;
    private const uint MOD_ALT = 0x0001;
    private const uint MOD_CONTROL = 0x0002;
    private const uint MOD_SHIFT = 0x0004;
    private const uint MOD_NOREPEAT = 0x4000;
    private const uint WDA_NONE = 0x0;
    private const uint WDA_EXCLUDEFROMCAPTURE = 0x00000011;

    private delegate bool EnumChildProc(IntPtr hWnd, IntPtr lParam);

    [System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)]
    private struct CursorPoint
    {
        public int X;
        public int Y;
    }

    [System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)]
    private struct WindowPos
    {
        public IntPtr hwnd;
        public IntPtr hwndInsertAfter;
        public int x;
        public int y;
        public int cx;
        public int cy;
        public uint flags;
    }

    [System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)]
    private struct WindowRect
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern IntPtr GetTopWindow(IntPtr hWnd);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern IntPtr GetShellWindow();

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr hWnd);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool GetWindowRect(IntPtr hWnd, out WindowRect rect);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int x, int y, int cx, int cy, uint flags);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool SystemParametersInfo(uint action, uint param, ref int value, uint winIni);

    [System.Runtime.InteropServices.DllImport("winmm.dll")]
    private static extern uint timeBeginPeriod(uint period);

    [System.Runtime.InteropServices.DllImport("winmm.dll")]
    private static extern uint timeEndPeriod(uint period);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool IsWindowVisible(IntPtr hWnd);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern short VkKeyScan(char ch);

    private delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);

    [System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)]
    private struct KbdLlHook
    {
        public uint vkCode;
        public uint scanCode;
        public uint flags;
        public uint time;
        public IntPtr extra;
    }

    [System.Runtime.InteropServices.DllImport("user32.dll", SetLastError = true)]
    private static extern IntPtr SetWindowsHookEx(int idHook, LowLevelKeyboardProc lpfn, IntPtr hMod, uint dwThreadId);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool UnhookWindowsHookEx(IntPtr hhk);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

    [System.Runtime.InteropServices.DllImport("kernel32.dll", CharSet = System.Runtime.InteropServices.CharSet.Auto)]
    private static extern IntPtr GetModuleHandle(string? lpModuleName);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool SetWindowDisplayAffinity(IntPtr hWnd, uint affinity);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool EnumChildWindows(IntPtr hWnd, EnumChildProc lpEnumFunc, IntPtr lParam);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool GetCursorPos(out CursorPoint point);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern short GetAsyncKeyState(int virtualKey);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint modifiers, uint virtualKey);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool UnregisterHotKey(IntPtr hWnd, int id);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern int SetWindowCompositionAttribute(IntPtr hWnd, ref WindowCompositionAttributeData data);

    [System.Runtime.InteropServices.DllImport("dwmapi.dll")]
    private static extern int DwmSetWindowAttribute(IntPtr hWnd, int attribute, ref int value, int size);

    [System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)]
    private struct AccentPolicy
    {
        public int AccentState;
        public int AccentFlags;
        public int GradientColor;
        public int AnimationId;
    }

    [System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)]
    private struct WindowCompositionAttributeData
    {
        public int Attribute;
        public IntPtr Data;
        public int SizeOfData;
    }
}
