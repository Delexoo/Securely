using System.Diagnostics;
using System.Text;
using System.Text.RegularExpressions;

namespace SecurelyShell;

/// <summary>
/// WireGuard tunnel driver — patterns from wireguard-windows enterprise docs
/// (installtunnelservice / uninstalltunnelservice) and Algo / PiVPN / Amnezia BYO conf.
/// </summary>
internal static class VpnTunnel
{
    public const string TunnelName = "SecurelyTunnel";

    private static readonly string ConfDir = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "Securely",
        "vpn");

    private static string ConfPath => Path.Combine(ConfDir, TunnelName + ".conf");

    public static string? FindWireGuardExe()
    {
        string[] candidates =
        [
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "WireGuard", "wireguard.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "WireGuard", "wireguard.exe"),
            @"C:\Program Files\WireGuard\wireguard.exe",
        ];
        foreach (var path in candidates)
        {
            if (File.Exists(path)) return path;
        }
        return null;
    }

    public static bool IsTunnelServiceRunning()
    {
        try
        {
            using var p = Process.Start(new ProcessStartInfo
            {
                FileName = "sc.exe",
                Arguments = $"query WireGuardTunnel${TunnelName}",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
            });
            if (p == null) return false;
            var output = p.StandardOutput.ReadToEnd();
            p.WaitForExit(4000);
            return output.Contains("RUNNING", StringComparison.OrdinalIgnoreCase);
        }
        catch
        {
            return false;
        }
    }

    public static (bool ok, string message) Connect(string rawConf, bool killSwitch, bool splitTunnel)
    {
        var wg = FindWireGuardExe();
        if (wg == null)
        {
            return (false,
                "WireGuard for Windows is not installed. Install it from https://www.wireguard.com/install/ then paste your .conf (Algo, PiVPN, Amnezia, Firezone, or any WireGuard server).");
        }

        var conf = NormalizeConf(rawConf, killSwitch, splitTunnel);
        if (string.IsNullOrWhiteSpace(conf) || !conf.Contains("[Interface]", StringComparison.OrdinalIgnoreCase)
            || !conf.Contains("[Peer]", StringComparison.OrdinalIgnoreCase))
        {
            return (false, "Paste a valid WireGuard .conf with [Interface] and [Peer] blocks first.");
        }

        try
        {
            Directory.CreateDirectory(ConfDir);
            // Disconnect any prior Securely tunnel before rewriting.
            _ = Disconnect();
            File.WriteAllText(ConfPath, conf, new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));

            var install = RunElevatedHint(wg, $"/installtunnelservice \"{ConfPath}\"");
            if (!install.ok)
            {
                // Retry without elevation prompt path — may still work if already elevated.
                install = RunProcess(wg, $"/installtunnelservice \"{ConfPath}\"");
            }

            if (!install.ok && !IsTunnelServiceRunning())
            {
                return (false,
                    "Could not start the WireGuard tunnel service. Run Securely as Administrator once, or import the saved profile in the WireGuard app. "
                    + (string.IsNullOrWhiteSpace(install.message) ? "" : install.message));
            }

            // Ensure service is started
            RunProcess("sc.exe", $"start WireGuardTunnel${TunnelName}");
            Thread.Sleep(800);
            if (!IsTunnelServiceRunning())
            {
                return (false, "Tunnel service installed but not running. Open WireGuard and activate “SecurelyTunnel”, or re-run Securely elevated.");
            }

            return (true, "Tunnel up — SecurelyTunnel via WireGuard.");
        }
        catch (Exception ex)
        {
            return (false, ex.Message);
        }
    }

    public static (bool ok, string message) Disconnect()
    {
        var wg = FindWireGuardExe();
        try
        {
            if (wg != null)
            {
                RunProcess(wg, $"/uninstalltunnelservice {TunnelName}");
            }
            RunProcess("sc.exe", $"stop WireGuardTunnel${TunnelName}");
            return (true, "Disconnected.");
        }
        catch (Exception ex)
        {
            return (false, ex.Message);
        }
    }

    public static string NormalizeConf(string raw, bool killSwitch, bool splitTunnel)
    {
        var text = raw.Replace("\r\n", "\n").Trim();
        if (string.IsNullOrEmpty(text)) return "";

        // Strip DNS leak risk: keep DNS lines; adjust AllowedIPs for kill/split semantics
        // (wireguard-windows: literal 0.0.0.0/0 enables WFP kill-switch-like blocking).
        string allowed;
        if (splitTunnel)
        {
            // Full internet via tunnel but leave classic LAN routes — common Algo/PiVPN client tweak.
            allowed = "0.0.0.0/1, 128.0.0.0/1, ::/1, 8000::/1";
        }
        else if (killSwitch)
        {
            allowed = "0.0.0.0/0, ::/0";
        }
        else
        {
            allowed = "0.0.0.0/0, ::/0";
        }

        if (Regex.IsMatch(text, @"^\s*AllowedIPs\s*=", RegexOptions.Multiline | RegexOptions.IgnoreCase))
        {
            text = Regex.Replace(
                text,
                @"^\s*AllowedIPs\s*=\s*.*$",
                "AllowedIPs = " + allowed,
                RegexOptions.Multiline | RegexOptions.IgnoreCase);
        }
        else if (text.Contains("[Peer]", StringComparison.OrdinalIgnoreCase))
        {
            text = Regex.Replace(
                text,
                @"(\[Peer\])",
                "$1\nAllowedIPs = " + allowed,
                RegexOptions.IgnoreCase);
        }

        return text.Trim() + "\n";
    }

    private static (bool ok, string message) RunProcess(string fileName, string args)
    {
        try
        {
            using var p = Process.Start(new ProcessStartInfo
            {
                FileName = fileName,
                Arguments = args,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
            });
            if (p == null) return (false, "Failed to start process.");
            var stdout = p.StandardOutput.ReadToEnd();
            var stderr = p.StandardError.ReadToEnd();
            p.WaitForExit(15000);
            var msg = (stdout + " " + stderr).Trim();
            return (p.ExitCode == 0 || IsTunnelServiceRunning(), msg);
        }
        catch (Exception ex)
        {
            return (false, ex.Message);
        }
    }

    private static (bool ok, string message) RunElevatedHint(string fileName, string args)
    {
        // Prefer non-elevated first; UAC every connect is painful. Caller retries.
        return RunProcess(fileName, args);
    }
}
