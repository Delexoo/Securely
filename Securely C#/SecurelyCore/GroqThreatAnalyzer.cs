using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace SecurelyCore;

public sealed class AiAnalysisOutcome
{
    public List<string> Threats { get; init; } = [];
    public SensitivePageType? AutoPausePageType { get; init; }
}

/// <summary>
/// Port of Securely.py's Groq-based analysis + all AI post-processing heuristics.
/// </summary>
public sealed class GroqThreatAnalyzer
{
    private static readonly string[] ModelsToTry =
    [
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile",
        "llama-3.3-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ];

    private readonly HttpClient _http;
    private readonly AuditLogger _logger;

    private readonly object _stateLock = new();
    private int _currentApiKeyIndex;
    private readonly Dictionary<int, DateTime> _apiCooldownUntil = new();
    private readonly Dictionary<int, int> _apiFailureCounts = new();

    private DateTime _aiRateLimitUntilUtc = DateTime.MinValue;
    private bool _aiInRateLimit;

    public GroqThreatAnalyzer(AuditLogger logger)
    {
        _logger = logger;
        _http = new HttpClient
        {
            Timeout = TimeSpan.FromSeconds(25)
        };
        _currentApiKeyIndex = 0;
        for (var i = 0; i < SecurelyDefaults.GroqApiKeys.Length; i++)
        {
            _apiFailureCounts[i] = 0;
            _apiCooldownUntil[i] = DateTime.MinValue;
        }
    }

    public void ResetApiState()
    {
        lock (_stateLock)
        {
            _currentApiKeyIndex = 0;
            _apiCooldownUntil.Clear();
            _apiFailureCounts.Clear();
            for (var i = 0; i < SecurelyDefaults.GroqApiKeys.Length; i++)
            {
                _apiFailureCounts[i] = 0;
                _apiCooldownUntil[i] = DateTime.MinValue;
            }

            _aiRateLimitUntilUtc = DateTime.MinValue;
            _aiInRateLimit = false;
        }
        _logger.LogInfo("Reset Groq API state.");
    }

    public IReadOnlyList<string> GetApiStatus()
    {
        var now = DateTime.UtcNow;
        var status = new List<string>();
        for (var idx = 0; idx < SecurelyDefaults.GroqApiKeys.Length; idx++)
        {
            var isCurrent = idx == _currentApiKeyIndex;
            var keyStatus = $"Key {idx + 1}" + (isCurrent ? " (Active)" : "");
            var cooldown = _apiCooldownUntil.TryGetValue(idx, out var until) ? until : DateTime.MinValue;
            var failures = _apiFailureCounts.TryGetValue(idx, out var f) ? f : 0;

            if (SecurelyDefaults.GroqApiKeys[idx] is null or "")
            {
                status.Add($"{keyStatus}: Invalid/Empty");
                continue;
            }

            if (cooldown > now)
            {
                var remaining = (int)(cooldown - now).TotalSeconds;
                status.Add(remaining > 3600 ? $"{keyStatus}: Cooldown ({remaining / 60}min remaining)" : $"{keyStatus}: Cooldown ({remaining}s remaining)");
            }
            else if (failures > 0)
            {
                status.Add($"{keyStatus}: {failures} failures");
            }
            else
            {
                status.Add($"{keyStatus}: Ready");
            }
        }

        return status;
    }

    public async Task<AiAnalysisOutcome> AnalyzeScreenWithAiAsync(
        string? imageBase64,
        string? detectedText,
        bool isQuickScan,
        string? windowTitle,
        bool notificationsEnabled,
        Action<NotificationRequest>? requestNotification,
        CancellationToken cancellationToken)
    {
        // Securely.py: cooldown gating for AI rate limit.
        var nowUtc = DateTime.UtcNow;
        lock (_stateLock)
        {
            if (_aiRateLimitUntilUtc > nowUtc)
            {
                _aiInRateLimit = true;
                return new AiAnalysisOutcome { Threats = [] };
            }

            if (_aiInRateLimit)
            {
                _aiInRateLimit = false;
            }
        }

        if (SecurelyDefaults.GroqApiKeys.Length == 0)
            return new AiAnalysisOutcome { Threats = [] };

        // Get key that isn't in cooldown.
        var apiKeyIndex = GetNextAvailableApiKeyIndex();
        if (apiKeyIndex is null)
            return new AiAnalysisOutcome { Threats = [] };

        var prompt = SecurelyDefaults.AiPrompt;

        // Securely.py: detected_text is the only input used by the Groq call.
        string textPrompt;
        if (!string.IsNullOrWhiteSpace(detectedText))
        {
            textPrompt = prompt + $"""

DETECTED TEXT FROM SCREEN (OCR):
{detectedText}

Analyze the above text for security threats. Look for suspicious indicators like phishing emails, suspicious sender addresses, urgency tactics, suspicious links, typosquatting, etc.
""";
        }
        else
        {
            textPrompt = prompt + """

WARNING: No text was detected from the screen (OCR may not be working or screen may contain only images).

Since no text was extracted, I cannot fully analyze the content. However, if this is an email or message window, you should manually check for:
- Suspicious sender email addresses
- Urgency language (act now, urgent, account suspended)
- Suspicious links or URLs
- Typosquatting or fake domains
- Requests for personal information

RESPOND WITH: UNSURE: No text detected - manual review recommended. Please check sender address, links, and content manually for suspicious indicators.
""";
        }

        var messages = new[]
        {
            new Dictionary<string, object?>
            {
                ["role"] = "user",
                ["content"] = textPrompt
            }
        };

        var lastError = string.Empty;
        var apiKey = SecurelyDefaults.GroqApiKeys[apiKeyIndex.Value];

        // Try models with the current key, falling back on model errors.
        foreach (var modelName in ModelsToTry)
        {
            cancellationToken.ThrowIfCancellationRequested();

            try
            {
                var requestBody = new
                {
                    model = modelName,
                    messages,
                    temperature = 0.3,
                    max_tokens = 2048
                };

                using var req = new HttpRequestMessage(HttpMethod.Post, "https://api.groq.com/openai/v1/chat/completions");
                req.Headers.Add("Authorization", $"Bearer {apiKey}");
                req.Content = new StringContent(JsonSerializer.Serialize(requestBody), Encoding.UTF8, "application/json");

                using var resp = await _http.SendAsync(req, cancellationToken).ConfigureAwait(false);
                var body = await resp.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);

                if (!resp.IsSuccessStatusCode)
                {
                    lastError = $"HTTP {(int)resp.StatusCode}: {body}";
                    HandleApiFailureOnStatus(apiKeyIndex.Value, resp.StatusCode, lastError);
                    // For model-not-found/access errors, try next model.
                    if (IsModelUnavailable(lastError))
                        continue;

                    break;
                }

                var textResponse = ExtractChatContent(body);
                if (string.IsNullOrWhiteSpace(textResponse))
                    textResponse = "UNSURE: Empty AI response";

                return ProcessAiResponse(
                    textResponse,
                    detectedText,
                    isQuickScan,
                    windowTitle,
                    notificationsEnabled,
                    requestNotification);
            }
            catch (OperationCanceledException)
            {
                throw;
            }
            catch (Exception ex)
            {
                lastError = ex.Message;
                HandleApiFailureOnException(apiKeyIndex.Value, ex);
                if (IsModelUnavailable(lastError))
                    continue;

                break;
            }
        }

        // All models failed with this key - set cooldown if required and return empty.
        lock (_stateLock)
        {
            if (!_apiCooldownUntil.TryGetValue(apiKeyIndex.Value, out var until) || until <= DateTime.UtcNow)
            {
                _apiCooldownUntil[apiKeyIndex.Value] = DateTime.UtcNow.AddSeconds(SecurelyDefaults.ApiCooldownSecondsOnFailure);
            }
        }

        return new AiAnalysisOutcome { Threats = [] };
    }

    private int? GetNextAvailableApiKeyIndex()
    {
        lock (_stateLock)
        {
            var now = DateTime.UtcNow;

            if (_currentApiKeyIndex < SecurelyDefaults.GroqApiKeys.Length &&
                _apiCooldownUntil.TryGetValue(_currentApiKeyIndex, out var currentUntil) &&
                currentUntil <= now)
            {
                return _currentApiKeyIndex;
            }

            for (var idx = 0; idx < SecurelyDefaults.GroqApiKeys.Length; idx++)
            {
                if (_apiCooldownUntil.TryGetValue(idx, out var until) && until <= now)
                {
                    _currentApiKeyIndex = idx;
                    return idx;
                }
            }
        }

        return null;
    }

    private void HandleApiFailureOnStatus(int apiKeyIndex, System.Net.HttpStatusCode statusCode, string error)
    {
        lock (_stateLock)
        {
            _apiFailureCounts[apiKeyIndex] = _apiFailureCounts.TryGetValue(apiKeyIndex, out var f) ? f + 1 : 1;

            var now = DateTime.UtcNow;
            if ((int)statusCode == 429)
            {
                _apiCooldownUntil[apiKeyIndex] = now.AddSeconds(65);
                _aiRateLimitUntilUtc = now.AddSeconds(65);
                _aiInRateLimit = true;
            }
            else if ((int)statusCode is 401 or 403)
            {
                _apiCooldownUntil[apiKeyIndex] = now.AddSeconds(3600);
            }
            else
            {
                _apiCooldownUntil[apiKeyIndex] = now.AddSeconds(SecurelyDefaults.ApiCooldownSecondsOnFailure);
            }
        }
    }

    private void HandleApiFailureOnException(int apiKeyIndex, Exception ex)
    {
        lock (_stateLock)
        {
            _apiFailureCounts[apiKeyIndex] = _apiFailureCounts.TryGetValue(apiKeyIndex, out var f) ? f + 1 : 1;
            _apiCooldownUntil[apiKeyIndex] = DateTime.UtcNow.AddSeconds(SecurelyDefaults.ApiCooldownSecondsOnFailure);
        }

        _logger.LogWarning($"Groq API exception (key {apiKeyIndex + 1}): {ex.Message}");
    }

    private static bool IsModelUnavailable(string errorText)
    {
        if (string.IsNullOrWhiteSpace(errorText)) return false;
        var e = errorText.ToLowerInvariant();
        return e.Contains("model_not_found", StringComparison.OrdinalIgnoreCase) ||
               e.Contains("404", StringComparison.OrdinalIgnoreCase) ||
               e.Contains("does not exist", StringComparison.OrdinalIgnoreCase) ||
               e.Contains("403", StringComparison.OrdinalIgnoreCase) ||
               e.Contains("access denied", StringComparison.OrdinalIgnoreCase) ||
               e.Contains("invalid model", StringComparison.OrdinalIgnoreCase);
    }

    private static string ExtractChatContent(string groqResponseJson)
    {
        using var doc = JsonDocument.Parse(groqResponseJson);
        if (!doc.RootElement.TryGetProperty("choices", out var choices) || choices.GetArrayLength() == 0)
            return string.Empty;
        var choice0 = choices[0];
        if (!choice0.TryGetProperty("message", out var msg))
            return string.Empty;
        if (!msg.TryGetProperty("content", out var content))
            return string.Empty;
        return content.GetString() ?? string.Empty;
    }

    /// <summary>
    /// Port of Securely.py's `process_ai_response`.
    /// </summary>
    public AiAnalysisOutcome ProcessAiResponse(
        string textResponse,
        string? detectedText,
        bool isQuickScan,
        string? windowTitle,
        bool notificationsEnabled,
        Action<NotificationRequest>? requestNotification)
    {
        var respUpper = (textResponse ?? string.Empty).ToUpperInvariant();

        var detectedTextNormalized = detectedText ?? string.Empty;

        var isPaymentPage = respUpper.Contains("LEGITIMATE_PAYMENT", StringComparison.OrdinalIgnoreCase) ||
                             IsPaymentPage(detectedTextNormalized);
        var isLoginPage = respUpper.Contains("LEGITIMATE_LOGIN", StringComparison.OrdinalIgnoreCase);

        if (isPaymentPage || isLoginPage)
        {
            var pageType = isPaymentPage ? SensitivePageType.Payment : SensitivePageType.Login;
            var isPage = LooksLikeLoginOrPaymentPage(detectedTextNormalized, windowTitle ?? string.Empty);

            if (isPage)
            {
                // Securely.py: if this was a quick scan, don't pause monitoring.
                if (isQuickScan)
                {
                    if (notificationsEnabled && requestNotification != null)
                    {
                        requestNotification(new NotificationRequest
                        {
                            Title = pageType == SensitivePageType.Payment ? "Payment Page Detected" : "Login Page Detected",
                            Message = $"Securely detected a {pageType} page during Quick Scan. Auto-pause only works during 24/7 monitoring or Scan for 15m.",
                            Duration = TimeSpan.FromSeconds(8)
                        });
                    }
                    return new AiAnalysisOutcome { Threats = [] };
                }

                // Non-quick scan: auto-pause.
                return new AiAnalysisOutcome
                {
                    Threats = [],
                    AutoPausePageType = pageType
                };
            }

            return new AiAnalysisOutcome { Threats = [] };
        }

        if (textResponse.StartsWith("SUSPICIOUS:", StringComparison.OrdinalIgnoreCase) ||
            textResponse.Contains("SUSPICIOUS", StringComparison.OrdinalIgnoreCase))
        {
            var threatDesc = textResponse.Replace("SUSPICIOUS:", "", StringComparison.OrdinalIgnoreCase).Trim();
            if (string.IsNullOrWhiteSpace(threatDesc)) threatDesc = textResponse.Trim();
            return new AiAnalysisOutcome
            {
                Threats = [threatDesc]
            };
        }

        if (textResponse.StartsWith("UNSURE:", StringComparison.OrdinalIgnoreCase) ||
            textResponse.Contains("UNSURE", StringComparison.OrdinalIgnoreCase))
        {
            var unsureDesc = textResponse.Replace("UNSURE:", "", StringComparison.OrdinalIgnoreCase)
                .Replace("unsure:", "", StringComparison.OrdinalIgnoreCase)
                .Trim();

            if (string.IsNullOrWhiteSpace(unsureDesc))
                unsureDesc = "Content appears uncertain - manual review recommended";

            return new AiAnalysisOutcome
            {
                Threats = [$"Unsure: {unsureDesc}"],
            };
        }

        // SAFE
        return new AiAnalysisOutcome { Threats = [] };
    }

    private static List<string> AnalyzeTextKeywords(string text, bool strictMode)
    {
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
            }
            else
            {
                if (strictMode)
                {
                    found.Add(word);
                }
                else
                {
                    // Word boundary match for accuracy
                    var pattern = $@"\b{Regex.Escape(wordLower)}\b";
                    if (Regex.IsMatch(textLower, pattern, RegexOptions.IgnoreCase))
                        found.Add(word);
                }
            }
        }

        return found;
    }

    // --- Heuristic helpers ported from Securely.py ---

    private static List<string> ExtractUrlsFromText(string text)
    {
        var urls = new List<string>();
        var urlPattern = new Regex(
            @"(https?://[^\s<>""'\)\]]+|https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?)",
            RegexOptions.IgnoreCase);

        var matches = urlPattern.Matches(text ?? string.Empty);
        foreach (Match m in matches)
        {
            var match = m.Value;
            if (string.IsNullOrWhiteSpace(match)) continue;

            var urlLower = match.ToLowerInvariant();
            if (urlLower.StartsWith("http://", StringComparison.OrdinalIgnoreCase))
            {
                var domainPart = urlLower.Replace("http://", "", StringComparison.OrdinalIgnoreCase).Split('/')[0];

                var commonHttpsDomains = new[]
                {
                    "google.com","facebook.com","amazon.com","microsoft.com","apple.com","twitter.com",
                    "x.com","youtube.com","github.com","paypal.com","ebay.com","netflix.com","linkedin.com",
                    "reddit.com","wikipedia.org","stackoverflow.com","politics1.com"
                };
                if (Array.Exists(commonHttpsDomains, d => domainPart.Contains(d, StringComparison.OrdinalIgnoreCase)))
                    continue; // likely OCR misread
            }

            urls.Add(match);
        }

        return urls;
    }

    private static List<string> ExtractDomainsFromText(string text)
    {
        var domains = new List<string>();
        var urlPattern = new Regex(@"(https?://)?([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}",
            RegexOptions.IgnoreCase);

        var matches = urlPattern.Matches(text ?? string.Empty);
        foreach (Match m in matches)
        {
            // We capture full match, not groups, for simplicity.
            var fullUrl = m.Value;
            var domainMatch = new Regex(@"([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}",
                RegexOptions.IgnoreCase).Match(fullUrl);
            if (!domainMatch.Success) continue;

            var domain = domainMatch.Value.ToLowerInvariant();
            if (domain.StartsWith("www.", StringComparison.OrdinalIgnoreCase))
                domain = domain[4..];
            domains.Add(domain);
        }

        return domains;
    }

    private static bool IsHttpUrl(string url)
    {
        if (string.IsNullOrWhiteSpace(url)) return false;
        var s = url.Trim().ToLowerInvariant();
        return s.StartsWith("http://", StringComparison.OrdinalIgnoreCase) && !s.StartsWith("https://", StringComparison.OrdinalIgnoreCase);
    }

    private static bool IsSuspiciousDomain(string domain, string windowTitle)
    {
        if (string.IsNullOrWhiteSpace(domain))
            return false;

        var domainLower = domain.ToLowerInvariant();

        var legitimateDomains = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "google.com","accounts.google.com","myaccount.google.com",
            "microsoft.com","login.microsoftonline.com","account.microsoft.com",
            "apple.com","appleid.apple.com","id.apple.com",
            "facebook.com","www.facebook.com","m.facebook.com",
            "amazon.com","pay.amazon.com",
            "paypal.com","www.paypal.com",
            "ebay.com","www.ebay.com",
            "netflix.com","www.netflix.com",
            "twitter.com","x.com",
            "linkedin.com","www.linkedin.com",
            "github.com","github.io",
            "dropbox.com","www.dropbox.com",
            "adobe.com","accounts.adobe.com",
            "yahoo.com","login.yahoo.com",
            "outlook.com","hotmail.com","live.com",
            "bankofamerica.com","chase.com","wellsfargo.com",
            "getpostman.com",
            "tebex.io","pay.tebex.io"
        };

        if (legitimateDomains.Contains(domainLower))
            return false;

        var suspiciousPatterns = new[]
        {
            @"g[o0]{2}gle",
            @"goog[e1]e",
            @"micr[o0]soft",
            @"faceb[o0]ok",
            @"amaz[o0]n",
            @"payp[a4]l",
            @"[a4]pple",
            @"yah[o0]o",
            @"[e3]bay"
        };
        foreach (var pattern in suspiciousPatterns)
        {
            if (Regex.IsMatch(domainLower, pattern, RegexOptions.IgnoreCase))
                return true;
        }

        var serviceNames = new[]
        {
            "google","microsoft","apple","facebook","amazon","paypal","ebay","netflix","twitter",
            "linkedin","github","adobe","yahoo","outlook","hotmail","bank","chase","wells","postman"
        };

        foreach (var service in serviceNames)
        {
            if (!domainLower.Contains(service, StringComparison.OrdinalIgnoreCase))
                continue;

            var isLegitimateSubdomain = Array.Exists(legitimateDomains.ToArray(),
                legit => domainLower.EndsWith("." + legit, StringComparison.OrdinalIgnoreCase) ||
                         domainLower.Equals(legit, StringComparison.OrdinalIgnoreCase));

            if (!isLegitimateSubdomain)
            {
                if (!string.IsNullOrWhiteSpace(windowTitle))
                {
                    var titleLower = windowTitle.ToLowerInvariant();
                    if (titleLower.Contains(service, StringComparison.OrdinalIgnoreCase) &&
                        domainLower.Contains(service, StringComparison.OrdinalIgnoreCase))
                        return true;
                }
            }
        }

        var suspiciousTlds = new[] { ".tk", ".ml", ".ga", ".cf", ".gq" };
        foreach (var tld in suspiciousTlds)
            if (domainLower.EndsWith(tld, StringComparison.OrdinalIgnoreCase))
                return true;

        // Domains with numbers in suspicious places (like g00gle)
        if (Regex.IsMatch(domainLower, @"[a-z][0-9]{2,}[a-z]", RegexOptions.IgnoreCase))
            return true;

        return false;
    }

    private static bool IsDevelopmentEnvironment(string detectedText, string windowTitle)
    {
        if (string.IsNullOrWhiteSpace(detectedText) && string.IsNullOrWhiteSpace(windowTitle))
            return false;

        var text = (detectedText ?? string.Empty).ToUpperInvariant();
        var title = (windowTitle ?? string.Empty).ToUpperInvariant();

        var devIndicators = new[]
        {
            "VISUAL STUDIO","VS CODE","VSCODE","CODE -","PYCHARM","INTELLIJ","ECLIPSE","SUBLIME","ATOM","VIM","EMACS","NOTEPAD++","JETBRAINS",
            "ANDROID STUDIO","XCODE","DEVELOPER","DEBUG","BREAKPOINT","CALL STACK","TERMINAL","CONSOLE",
            "GIT","GITHUB","BITBUCKET","GITLAB",
            "PYTHON","JAVASCRIPT","TYPESCRIPT","JAVA","C#",
            "FUNCTION","DEF ","CLASS ","IMPORT ","FROM ","RETURN ",
            "IF __NAME__","MAIN()","SYNTAX","INDENT","TAB",
            "SECURELY_CTK.PY",".PY",".JS",".TS",".JAVA",".CPP"
        };

        foreach (var indicator in devIndicators)
            if (title.Contains(indicator, StringComparison.OrdinalIgnoreCase))
                return true;

        var codePatterns = new[]
        {
            "DEF ","CLASS ","IMPORT ","FROM ","RETURN ","IF ","ELSE ","FUNCTION","VAR ","LET ","CONST ","PUBLIC ","PRIVATE ",
            "BREAKPOINT","CALL STACK","DEBUG CONSOLE","TERMINAL","SECURELY_CTK",".PY","PYTHON","JAVASCRIPT"
        };

        foreach (var pattern in codePatterns)
            if (text.Contains(pattern, StringComparison.OrdinalIgnoreCase))
                return true;

        return false;
    }

    private static bool IsPaymentPage(string detectedText)
    {
        if (string.IsNullOrWhiteSpace(detectedText))
            return false;

        var text = detectedText.ToUpperInvariant();

        var paymentKeywords = new[]
        {
            "CARD NUMBER","CREDIT CARD","DEBIT CARD","CVV","CVC",
            "EXPIRY DATE","EXPIRATION","EXP DATE","MM/YY","MM/YYYY",
            "BILLING ADDRESS","BILLING","ZIP CODE","POSTAL CODE",
            "PAYMENT METHOD","PAY NOW","CHECKOUT","PROCEED TO PAYMENT",
            "TOTAL PRICE","SUBTOTAL","ORDER TOTAL","PAYMENT INFORMATION"
        };

        var loginKeywords = new[]
        {
            "PASSWORD","USERNAME","SIGN IN","LOG IN","LOGIN",
            "FORGOT PASSWORD","RESET PASSWORD","ACCOUNT LOGIN"
        };

        var paymentCount = 0;
        foreach (var kw in paymentKeywords)
            if (text.Contains(kw, StringComparison.OrdinalIgnoreCase))
                paymentCount++;

        var loginCount = 0;
        foreach (var kw in loginKeywords)
            if (text.Contains(kw, StringComparison.OrdinalIgnoreCase))
                loginCount++;

        return paymentCount > 0 && paymentCount >= loginCount;
    }

    private static bool LooksLikeLoginOrPaymentPage(string detectedText, string windowTitle)
    {
        if (IsDevelopmentEnvironment(detectedText, windowTitle))
            return false;

        if (string.IsNullOrWhiteSpace(detectedText))
            return false;

        var text = detectedText.ToUpperInvariant();

        var loginKeywords = new[]
        {
            "PASSWORD","USERNAME","SIGN IN","LOG IN","LOGIN",
            "FORGOT PASSWORD","RESET PASSWORD","ACCOUNT LOGIN"
        };
        var paymentKeywords = new[]
        {
            "CARD NUMBER","CREDIT CARD","DEBIT CARD","CVV","CVC",
            "EXPIRY DATE","EXPIRATION","EXP DATE","MM/YY","MM/YYYY",
            "BILLING ADDRESS","BILLING","ZIP CODE","POSTAL CODE",
            "PAYMENT METHOD","PAY NOW","CHECKOUT","PROCEED TO PAYMENT",
            "TOTAL PRICE","SUBTOTAL","ORDER TOTAL","PAYMENT INFORMATION"
        };

        var foundLogin = 0;
        foreach (var kw in loginKeywords)
            if (text.Contains(kw, StringComparison.OrdinalIgnoreCase))
                foundLogin++;

        var foundPayment = 0;
        foreach (var kw in paymentKeywords)
            if (text.Contains(kw, StringComparison.OrdinalIgnoreCase))
                foundPayment++;

        var foundGeneric = new[] { "SECURE", "HTTPS", "SIGN", "ACCOUNT", "IDENTITY", "VERIFICATION" };
        var genericCount = 0;
        foreach (var kw in foundGeneric)
            if (text.Contains(kw, StringComparison.OrdinalIgnoreCase))
                genericCount++;

        var hasUrl = ExtractUrlsFromText(detectedText).Count > 0;

        if (foundLogin > 0 || foundPayment > 0)
        {
            if (foundLogin >= foundPayment) return true;
            return true;
        }

        if (genericCount >= 2 && hasUrl && (foundLogin > 0 || foundPayment > 0))
            return true;

        var totalKeywords = foundLogin + foundPayment + genericCount;
        if (totalKeywords >= 3 && (text.Contains("HTTPS", StringComparison.OrdinalIgnoreCase) ||
                                   text.Contains("HTTP", StringComparison.OrdinalIgnoreCase) ||
                                   text.Contains("SECURE", StringComparison.OrdinalIgnoreCase)))
            return true;

        return false;
    }
}

