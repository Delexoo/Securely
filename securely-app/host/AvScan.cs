using System.Diagnostics;
using System.Security.Cryptography;
using System.Text.Json;

namespace SecurelyShell;

/// <summary>
/// Companion AV helpers — Defender MpCmdRun + local SHA-256.
/// Inspired by open engines (ClamAV scan UX, KicomAV/Jackal static hash+signature flow)
/// without claiming primary AV status or shipping cracked vendor DBs.
/// </summary>
internal static class AvScan
{
    public static string? FindMpCmdRun()
    {
        string[] candidates =
        [
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Windows Defender", "MpCmdRun.exe"),
            @"C:\Program Files\Windows Defender\MpCmdRun.exe",
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Windows Defender", "MpCmdRun.exe"),
        ];
        foreach (var path in candidates)
        {
            if (File.Exists(path)) return path;
        }
        return null;
    }

    public static object DefenderStatus()
    {
        var mp = FindMpCmdRun();
        return new
        {
            installed = mp != null,
            path = mp ?? "",
            hint = mp != null
                ? "Windows Security / Defender is available — Securely complements it."
                : "Defender tools not found. Keep Windows Security enabled.",
        };
    }

    public static async Task<object> ScanPathsAsync(IEnumerable<string> paths, CancellationToken ct = default)
    {
        var list = paths.Where(p => !string.IsNullOrWhiteSpace(p) && File.Exists(p)).Take(12).ToList();
        var results = new List<object>();
        var mp = FindMpCmdRun();

        foreach (var path in list)
        {
            ct.ThrowIfCancellationRequested();
            string sha = "";
            try
            {
                await using var fs = File.OpenRead(path);
                var hash = await SHA256.HashDataAsync(fs, ct).ConfigureAwait(false);
                sha = Convert.ToHexString(hash).ToLowerInvariant();
            }
            catch (Exception ex)
            {
                results.Add(new { path, ok = false, error = ex.Message });
                continue;
            }

            var defender = "skipped";
            var threat = false;
            if (mp != null)
            {
                try
                {
                    using var p = Process.Start(new ProcessStartInfo
                    {
                        FileName = mp,
                        Arguments = $"-Scan -ScanType 3 -File \"{path}\"",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        CreateNoWindow = true,
                    });
                    if (p != null)
                    {
                        var output = await p.StandardOutput.ReadToEndAsync(ct).ConfigureAwait(false);
                        await p.WaitForExitAsync(ct).ConfigureAwait(false);
                        defender = p.ExitCode == 0 ? "clean" : $"exit {p.ExitCode}";
                        // MpCmdRun returns non-zero when threats found (typically 2).
                        threat = p.ExitCode == 2
                            || output.Contains("Threat", StringComparison.OrdinalIgnoreCase);
                        if (threat) defender = "threat";
                    }
                }
                catch (Exception ex)
                {
                    defender = "error: " + ex.Message;
                }
            }

            results.Add(new
            {
                path,
                ok = true,
                sha256 = sha,
                defender,
                threat,
                name = Path.GetFileName(path),
            });
        }

        return new { ok = true, count = results.Count, results };
    }

    public static string? PickFiles()
    {
        try
        {
            using var dlg = new OpenFileDialog
            {
                Title = "Securely — scan files",
                Multiselect = true,
                Filter = "All files|*.*|Executables|*.exe;*.dll;*.msi;*.scr|Scripts|*.ps1;*.js;*.vbs;*.bat",
            };
            if (dlg.ShowDialog() != DialogResult.OK) return null;
            return JsonSerializer.Serialize(dlg.FileNames);
        }
        catch
        {
            return null;
        }
    }
}
