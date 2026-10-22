using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace SecurelyCore;

public sealed class ScreenMonitor : IDisposable
{
    private readonly IScreenCaptureService _captureService;
    private readonly IOcrService _ocrService;
    private readonly GroqThreatAnalyzer _analyzer;
    private readonly AuditLogger _logger;

    private readonly object _loopLock = new();
    private CancellationTokenSource? _cts;
    private Task? _loopTask;

    private readonly ManualResetEventSlim _runningEvent = new(initialState: false);

    // Notification throttling
    private readonly object _notifyLock = new();
    private readonly Dictionary<string, DateTime> _recentNotifications = new();
    private readonly Dictionary<string, Dictionary<string, DateTime>> _windowThreatCache = new();
    public TimeSpan NotificationCooldown { get; set; } = TimeSpan.FromSeconds(60);

    // Monitor controls (UI can toggle these)
    public bool NotificationsEnabled { get; set; } = true;
    public bool SoundEnabled { get; set; } = false;
    public bool StrictMode { get; set; } = false;
    public bool HitboxesEnabled { get; set; } = false;
    public bool TestMode { get; set; } = false;

    public string AiStatus { get; private set; } = "Initializing...";

    public ISecurelyUiBridge? UiBridge { get; set; }

    private bool _oneShotRequested;
    private DateTime? _multiScanUntilUtc;

    // Auto pause
    private bool _pausedForSensitivePage;
    private SensitivePageType? _pausedPageType;
    private CancellationTokenSource? _pauseCountdownCts;

    public ScreenMonitor(
        IScreenCaptureService captureService,
        IOcrService ocrService,
        GroqThreatAnalyzer analyzer,
        AuditLogger logger)
    {
        _captureService = captureService;
        _ocrService = ocrService;
        _analyzer = analyzer;
        _logger = logger;
    }

    public void StartMonitor()
    {
        lock (_loopLock)
        {
            if (_cts != null)
                return;

            _cts = new CancellationTokenSource();
            _runningEvent.Set();
            _pausedForSensitivePage = false;
            _pauseCountdownCts?.Cancel();
            _pauseCountdownCts = null;
            _loopTask = Task.Run(() => LoopAsync(_cts.Token));
        }
    }

    public void StopMonitor()
    {
        lock (_loopLock)
        {
            _runningEvent.Reset();
            _pauseCountdownCts?.Cancel();
            _pauseCountdownCts = null;
            _pausedForSensitivePage = false;
            _pausedPageType = null;

            _cts?.Cancel();
            _cts = null;
            _loopTask = null;
        }
    }

    public void RequestScanOnce()
    {
        _oneShotRequested = true;
        StartMonitor();
    }

    public void RequestScanFor(TimeSpan duration)
    {
        _multiScanUntilUtc = DateTime.UtcNow.Add(duration);
        StartMonitor();
    }

    public void Dispose()
    {
        try { StopMonitor(); } catch { }
        _runningEvent.Dispose();
    }

    private async Task LoopAsync(CancellationToken token)
    {
        var lastOcrTextHash = 0;
        var scanCount = 0;

        while (!token.IsCancellationRequested)
        {
            // Wait until monitoring is enabled.
            _runningEvent.Wait(token);

            scanCount++;
            var status = "🔍 Scanning screen...";
            SetAiStatus(status);

            try
            {
                using var capture = await _captureService.CapturePrimaryMonitorAsync(token).ConfigureAwait(false);

                var ocrResult = await _ocrService.AnalyzeAsync(capture.Bitmap, token).ConfigureAwait(false);
                var fullText = ocrResult.FullText ?? string.Empty;

                // Strict mode: local keyword scan.
                var isQuickScan = _oneShotRequested;

                AiAnalysisOutcome aiOutcome;
                if (TestMode)
                {
                    // Test mode: simulate downstream behavior without requiring AI connectivity.
                    aiOutcome = new AiAnalysisOutcome { Threats = [], AutoPausePageType = null };
                }
                else
                {
                    // Only run AI when we have OCR text? python calls AI even if empty.
                    aiOutcome = await _analyzer.AnalyzeScreenWithAiAsync(
                        imageBase64: capture.Base64,
                        detectedText: fullText,
                        isQuickScan: isQuickScan,
                        windowTitle: string.Empty,
                        notificationsEnabled: NotificationsEnabled,
                        requestNotification: req => UiBridge?.RequestNotification(req),
                        cancellationToken: token).ConfigureAwait(false);
                }

                if (aiOutcome.AutoPausePageType is not null)
                {
                    await EnterAutoPauseAsync(aiOutcome.AutoPausePageType.Value, token).ConfigureAwait(false);
                    // If we just paused, wait until resume before continuing.
                    continue;
                }

                var findings = aiOutcome.Threats.Distinct(StringComparer.OrdinalIgnoreCase).ToList();

                // Add strict keyword findings when enabled.
                if (StrictMode && fullText.Length > 0)
                {
                    var keywordFindings = LocalKeywordDetector.AnalyzeText(fullText, strictMode: true);
                    foreach (var kf in keywordFindings)
                    {
                        if (!findings.Any(f => f.Equals(kf, StringComparison.OrdinalIgnoreCase)))
                            findings.Add(kf);
                    }
                }

                if (TestMode && findings.Count == 0)
                    findings.Add("Test threat detected - this is a simulation");

                if (findings.Count > 0)
                {
                    SetAiStatus($"⚠️ {findings.Count} threat{(findings.Count == 1 ? "" : "s")} detected");

                    var threatFindings = findings.Select(f => new ThreatFinding(f, ThreatCategorizer.CategorizeThreat(f))).ToList();
                    UiBridge?.NotifyThreats(threatFindings);

                    var didLogThisScan = false;
                    for (var i = 0; i < findings.Count; i++)
                    {
                        var f = findings[i];
                        if (ShouldNotify(f, windowTitle: string.Empty))
                        {
                            MarkNotified(f, windowTitle: string.Empty);

                            var cat = ThreatCategorizer.CategorizeThreat(f);
                            var notif = BuildThreatNotification(cat, f);
                            if (NotificationsEnabled)
                                UiBridge?.RequestNotification(notif);

                            _logger.LogEvent($"Threat: {f}", threatType: cat.ToString(), description: f);
                            didLogThisScan = true;
                        }
                    }

                    if (didLogThisScan)
                        UiBridge?.RefreshAuditLog();
                }
                else
                {
                    SetAiStatus("✅ Screen secure");
                }

                // Hitboxes overlay support (WPF overlay window draws these rectangles).
                if (HitboxesEnabled)
                {
                    var hitboxes = new Dictionary<string, HitboxRect>(StringComparer.OrdinalIgnoreCase);

                    // Test mode: always display a banner-like hitbox like Securely.py.
                    if (TestMode)
                    {
                        hitboxes["Test threat detected - this is a simulation"] = new HitboxRect(200, 200, 300, 60);
                    }

                    foreach (var threat in findings)
                    {
                        if (TestMode && threat.Equals("Test threat detected - this is a simulation", StringComparison.OrdinalIgnoreCase))
                            continue;

                        var rect = FindBestThreatRect(threat, fullText, ocrResult.Words);
                        if (rect is not null)
                            hitboxes[threat] = rect.Value;
                    }

                    UiBridge?.UpdateHitboxes(hitboxes);
                }
                else
                {
                    UiBridge?.UpdateHitboxes(new Dictionary<string, HitboxRect>(StringComparer.OrdinalIgnoreCase));
                }

                // One-shot: stop after one scan.
                if (_oneShotRequested)
                {
                    _oneShotRequested = false;
                    _runningEvent.Reset();
                    UiBridge?.UpdateMonitorPaused(null, null);
                }

                // Multi-scan: stop after requested duration.
                if (_multiScanUntilUtc is DateTime until && DateTime.UtcNow >= until)
                {
                    _multiScanUntilUtc = null;
                    _runningEvent.Reset();
                    UiBridge?.UpdateMonitorPaused(null, null);
                }
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch (Exception ex)
            {
                _logger.LogError($"ScreenMonitor scan error: {ex.Message}");
                // Avoid tight loop on recurring errors.
                await Task.Delay(1000, token).ConfigureAwait(false);
            }

            // Base delay (python dynamically changes based on API/rate limit; start simple).
            await Task.Delay(TimeSpan.FromSeconds(1), token).ConfigureAwait(false);
        }
    }

    private static HitboxRect? FindBestThreatRect(string threatDescription, string fullText, IReadOnlyList<OcrWordBox> words)
    {
        if (string.IsNullOrWhiteSpace(threatDescription) || words.Count == 0)
            return null;

        // Normalize AI output prefixes.
        var threat = threatDescription.Trim();
        threat = threat.StartsWith("SUSPICIOUS:", StringComparison.OrdinalIgnoreCase)
            ? threat[11..].Trim()
            : threat;
        threat = threat.StartsWith("UNSURE:", StringComparison.OrdinalIgnoreCase)
            ? threat[7..].Trim()
            : threat;

        if (string.IsNullOrWhiteSpace(threat))
            return null;

        var threatLower = threat.ToLowerInvariant();

        // Tokenize threat to find likely matching words.
        var tokens = threatLower
            .Split([' ', '\t', '\r', '\n', '-', '_', '.', ',', ':', ';', '!', '?', '(', ')', '[', ']'], StringSplitOptions.RemoveEmptyEntries)
            .Select(t => t.Trim())
            .Where(t => t.Length >= 3)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();

        if (tokens.Count == 0)
            return null;

        var matching = words
            .Where(w =>
            {
                var wText = (w.Text ?? string.Empty).ToLowerInvariant();
                if (string.IsNullOrWhiteSpace(wText))
                    return false;
                return tokens.Any(tok => wText.Contains(tok, StringComparison.OrdinalIgnoreCase));
            })
            .ToList();

        if (matching.Count == 0)
            return null;

        var minX = matching.Min(w => w.Left);
        var minY = matching.Min(w => w.Top);
        var maxX = matching.Max(w => w.Left + w.Width);
        var maxY = matching.Max(w => w.Top + w.Height);

        return new HitboxRect(minX, minY, Math.Max(1, maxX - minX), Math.Max(1, maxY - minY));
    }

    private async Task EnterAutoPauseAsync(SensitivePageType pageType, CancellationToken token)
    {
        _pausedForSensitivePage = true;
        _pausedPageType = pageType;

        // Pause loop capturing.
        _runningEvent.Reset();
        UiBridge?.UpdateMonitorPaused(pageType, TimeSpan.FromSeconds(180));

        _pauseCountdownCts?.Cancel();
        _pauseCountdownCts = CancellationTokenSource.CreateLinkedTokenSource(token);
        var pauseToken = _pauseCountdownCts.Token;

        var remaining = TimeSpan.FromSeconds(180);
        var startedAt = DateTime.UtcNow;

        while (remaining.TotalSeconds > 0 && !pauseToken.IsCancellationRequested)
        {
            var elapsed = DateTime.UtcNow - startedAt;
            remaining = TimeSpan.FromSeconds(180) - elapsed;
            if (remaining < TimeSpan.Zero) remaining = TimeSpan.Zero;
            UiBridge?.UpdateMonitorPaused(pageType, remaining);
            try
            {
                await Task.Delay(1000, pauseToken).ConfigureAwait(false);
            }
            catch (TaskCanceledException)
            {
                break;
            }
        }

        // Resume unless user stopped.
        if (!pauseToken.IsCancellationRequested)
        {
            _pausedForSensitivePage = false;
            _pausedPageType = null;
            UiBridge?.UpdateMonitorPaused(null, null);

            // If a timed scan expired during the pause, do not resume.
            if (_multiScanUntilUtc is DateTime until && DateTime.UtcNow >= until)
            {
                _multiScanUntilUtc = null;
                _runningEvent.Reset();
                return;
            }

            // If monitoring was explicitly stopped, do not resume.
            if (token.IsCancellationRequested)
                return;

            _runningEvent.Set();
        }
    }

    private void SetAiStatus(string status)
    {
        AiStatus = status;
        UiBridge?.UpdateAiStatus(status);
    }

    private static NotificationRequest BuildThreatNotification(ThreatCategory cat, string threatDescription)
    {
        if (cat == ThreatCategory.Unsure)
        {
            var clean = threatDescription;
            clean = clean.StartsWith("Unsure:", StringComparison.OrdinalIgnoreCase)
                ? clean[7..].Trim()
                : clean;

            return new NotificationRequest
            {
                Title = $"Unsure: {clean}",
                Message = $"Content appears uncertain - manual review recommended: {clean}",
                Duration = TimeSpan.FromSeconds(10)
            };
        }

        return new NotificationRequest
        {
            Title = $"{cat}: {threatDescription}",
            Message = $"Personalized threat detected: {threatDescription}",
            Duration = TimeSpan.FromSeconds(10)
        };
    }

    private bool ShouldNotify(string threatDescription, string windowTitle)
    {
        var now = DateTime.UtcNow;
        lock (_notifyLock)
        {
            if (_recentNotifications.TryGetValue(threatDescription, out var last))
            {
                if (now - last < NotificationCooldown)
                    return false;
            }

            if (!string.IsNullOrWhiteSpace(windowTitle))
            {
                if (!_windowThreatCache.TryGetValue(windowTitle, out var perWin))
                {
                    perWin = new Dictionary<string, DateTime>(StringComparer.OrdinalIgnoreCase);
                    _windowThreatCache[windowTitle] = perWin;
                }

                if (perWin.TryGetValue(threatDescription, out var lastWin))
                {
                    if (now - lastWin < TimeSpan.FromSeconds(30))
                        return false;
                }
            }

            return true;
        }
    }

    private void MarkNotified(string threatDescription, string windowTitle)
    {
        var now = DateTime.UtcNow;
        lock (_notifyLock)
        {
            _recentNotifications[threatDescription] = now;
            if (!string.IsNullOrWhiteSpace(windowTitle))
            {
                if (!_windowThreatCache.TryGetValue(windowTitle, out var perWin))
                {
                    perWin = new Dictionary<string, DateTime>(StringComparer.OrdinalIgnoreCase);
                    _windowThreatCache[windowTitle] = perWin;
                }
                perWin[threatDescription] = now;
            }
        }
    }

    private sealed class LocalKeywordDetector
    {
        public static List<string> AnalyzeText(string text, bool strictMode)
        {
            if (string.IsNullOrWhiteSpace(text))
                return [];

            var found = new List<string>();
            var textLower = text.ToLowerInvariant();

            foreach (var word in SecurelyDefaults.Keywords)
            {
                var wordLower = word.ToLowerInvariant();

                if (!textLower.Contains(wordLower, StringComparison.OrdinalIgnoreCase))
                    continue;

                if (wordLower.Contains(' '))
                {
                    if (textLower.Contains(wordLower, StringComparison.OrdinalIgnoreCase))
                        found.Add(word);
                    continue;
                }

                if (strictMode)
                {
                    // Strict mode (python): any occurrence (substring match).
                    found.Add(word);
                }
                else
                {
                    // Normal mode: word boundary match.
                    var pattern = $@"\b{System.Text.RegularExpressions.Regex.Escape(wordLower)}\b";
                    if (System.Text.RegularExpressions.Regex.IsMatch(textLower, pattern, System.Text.RegularExpressions.RegexOptions.IgnoreCase))
                        found.Add(word);
                }
            }

            return found.Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        }
    }

    private sealed class ThreatCategorizer
    {
        private static readonly string[] HighThreatKeywords =
        [
            "virus", "malware", "ransomware", "trojan", "spyware", "rootkit",
            "keylogger", "botnet", "backdoor", "exploit", "vulnerability",
            "infected", "compromised", "hacked", "breach", "attack",
            "malicious software", "malicious code", "harmful", "dangerous",
            "stealing", "steal", "theft", "fraud", "scam", "phishing",
            "credential harvesting", "password theft", "identity theft"
        ];

        private static readonly string[] SuspiciousKeywords =
        [
            "suspicious", "unusual", "unexpected", "strange", "odd",
            "questionable", "concerning", "warning", "alert", "caution",
            "potential threat", "possible", "might be", "could be",
            "unverified", "untrusted", "unknown source", "unfamiliar",
            "unusual activity", "suspicious email", "suspicious link",
            "suspicious website", "suspicious message", "suspicious attachment"
        ];

        private static readonly string[] UnsureKeywords =
        [
            "unclear", "ambiguous", "uncertain", "unidentified",
            "unknown", "unrecognized", "may be", "appears to be",
            "looks like", "seems", "possibly", "perhaps", "might",
            "could potentially", "needs review", "requires investigation",
            "manual review", "uncertain content"
        ];

        public static ThreatCategory CategorizeThreat(string threatDescription)
        {
            if (string.IsNullOrWhiteSpace(threatDescription))
                return ThreatCategory.Unsure;

            var descLower = threatDescription.ToLowerInvariant();
            if (descLower.StartsWith("unsure:", StringComparison.OrdinalIgnoreCase))
                return ThreatCategory.Unsure;

            foreach (var keyword in HighThreatKeywords)
                if (descLower.Contains(keyword, StringComparison.OrdinalIgnoreCase))
                    return ThreatCategory.ThreatDetected;

            foreach (var keyword in UnsureKeywords)
                if (descLower.Contains(keyword, StringComparison.OrdinalIgnoreCase))
                    return ThreatCategory.Unsure;

            foreach (var keyword in SuspiciousKeywords)
                if (descLower.Contains(keyword, StringComparison.OrdinalIgnoreCase))
                    return ThreatCategory.SuspiciousActivity;

            if (descLower.StartsWith("suspicious:", StringComparison.OrdinalIgnoreCase))
                return ThreatCategory.SuspiciousActivity;
            if (descLower.Contains("threat", StringComparison.OrdinalIgnoreCase) ||
                descLower.Contains("malicious", StringComparison.OrdinalIgnoreCase))
                return ThreatCategory.ThreatDetected;

            if (descLower.Contains("suspicious", StringComparison.OrdinalIgnoreCase))
                return ThreatCategory.SuspiciousActivity;

            return ThreatCategory.Unsure;
        }
    }
}

