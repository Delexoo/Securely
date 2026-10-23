using System.Text.Json;

namespace SecurelyShell;

/// <summary>
/// Shared license file so dashboard + island WebViews see the same Stripe entitlement.
/// </summary>
internal static class LicenseStore
{
    private static readonly string PathFile = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "Securely",
        "license.json");

    public static object? Read()
    {
        try
        {
            if (!File.Exists(PathFile)) return null;
            using var doc = JsonDocument.Parse(File.ReadAllText(PathFile));
            var root = doc.RootElement;
            return new
            {
                email = root.TryGetProperty("email", out var e) ? e.GetString() ?? "" : "",
                active = root.TryGetProperty("active", out var a) && a.ValueKind == JsonValueKind.True,
                status = root.TryGetProperty("status", out var s) ? s.GetString() ?? "" : "",
                checkedAt = root.TryGetProperty("checkedAt", out var c) && c.TryGetInt64(out var n) ? n : 0L,
                sessionId = root.TryGetProperty("sessionId", out var sid) ? sid.GetString() ?? "" : "",
            };
        }
        catch
        {
            return null;
        }
    }

    public static void Write(string email, bool active, string status, string? sessionId = null)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(PathFile)!);
        var payload = new
        {
            email = (email ?? "").Trim().ToLowerInvariant(),
            active,
            status = string.IsNullOrWhiteSpace(status) ? (active ? "active" : "inactive") : status,
            checkedAt = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
            sessionId = sessionId ?? "",
        };
        File.WriteAllText(PathFile, JsonSerializer.Serialize(payload));
    }
}
